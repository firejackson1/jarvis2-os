# Sleep and speaker-mute investigation

Status: reproduced and narrowed on the engineering trial, not fixed or qualified
for public release. No ROM image or kernel module was installed during these
experiments. A powered keep-awake setting avoids idle sleep but does not repair
intentional suspend/wake.

## Bind observations to the running driver

Filesystem hashes for the Ethernet MAC/platform and sound-card modules matched
the retained analysis inputs. All five loaded module GNU build-ID notes also
matched. The early power and PHY-debug modules were unavailable as ordinary
files after Android switched root, so their full live file bytes were not
hashed. Build-ID matches alone are not a full live-code integrity proof.

| Module | Analysis file SHA256 |
| --- | --- |
| dwmac-meson8b | `b0a7a68a3d1bd703751e6401c6c650a5c7f2d35aabafa58eba10db12423dbe7d` |
| stmmac | `a620296ca5836faa2a05095850acd02e8a0b2d1b2fd3eda88beb9b2415dab0b5` |
| amlogic-snd-soc | `887defc17c1cf7772185ebacecb39344c32abba2c53282bed1bb6a3e384d0bc9` |
| amlogic-phy-debug | `3835e6760d4216c1fb7e8dab585caf0e5cbd3f64c04f9d6b2b81ceb8a0eb2a78` |
| amlogic-pm | `97b9c8bb793bdc1648f230d31c4692c3ce52b96ae025804420acec53d7d32af7` |

LLVM disassembly, with ELF relocations, was used. The REA artifact opener
recognized the ELF, but no deep-analysis provider was configured. Its attempted
decompilations failed; no recovered C or whole-bootloader decompilation is claimed.

## Separate wake handling from amplifier behavior

The vendor PHY-debug module owns `/sys/class/ethernet/wol`; it is not merely the
standard ethtool setting. Its store callback parses a hexadecimal integer and
assigns the vendor flag (or the external-PHY flag on that hardware branch).
It does not make an arbitrary value such as `2` a documented magic-packet mode.

The shipped MAC/platform instructions separately check that vendor flag and
PHY link state during suspend. On resume they can keep the Ethernet device
awake for 5,000 ms. Standard ethtool state is not a sufficient description of
that path: the platform resume code clears its recorded `wolopts`.

The related [vendor wake-reason definitions](https://github.com/khadas/common_drivers/blob/3a11a86a02e759fc57fc79410215f7c0c3a0d8e0/include/linux/amlogic/pm.h)
name value 10 as Ethernet PHY wake, and the shipped platform instructions compare
the saved resume method with 10. A CEC-prefixed log printing `0xa` does not by
itself prove a CEC trigger, the initiating IRQ, or the exact packet responsible.
The old test that disabled vendor Ethernet wake also failed to wake normally;
do not ship that as a fix or repeat it without a verified recovery path.

The sound-card suspend callback asserts its mute state. Its resume callback
clears that state and schedules GPIO work; the worker can unmute the speaker
even while Android remains asleep. The separate user mixer mute flag suppresses
that unmute. The running driver also repeats control-registration/GPIO-request
operations and logs duplicate-control/request errors during these cycles.
Those errors alone do not identify the initiating wake source.

## Controlled traces

Two isolated tracefs instances used the `boot` clock and existing power/GPIO
tracepoints. Each observation lasted 30 host-wall-clock seconds without host
polling. There were no added kprobes or sleep/wake commands. All four CPU buffers
reported zero overruns, commit overruns and dropped events in both captures.
The instances were removed and the original global `nop`/tracing-off state was
unchanged afterward. The trace controls were temporary RAM state.

On this kernel, the speaker pin was independently identified from the live GPIO
controller base (428) plus the device-tree offset (33), with active-low polarity.
That made it GPIO 461 in these captures; this number is not a portable firmware
constant and must not be used for direct pin writes on other builds.

| Observation | Suspend entries | Speaker GPIO result |
| --- | ---: | --- |
| Original mixer state, mute Off | 5 | Each cycle wrote mute low, then the card worker wrote unmute high |
| Temporary `SPK mute` On | 5 | Suspend writes stayed low; no card-worker unmute appeared |

The mixer experiment ended by restoring Off; its only high write was the
deliberate restore. The original state and successful restore were read back.
The standard TinyALSA tool was built from clean source
`2ed34d52a7a7b83dba0d1c27d777f8eb70b3f3e9`, matched against the installed
library, staged temporarily and removed after the test. No active playback
session was present in the saved preflight. No tone or microphone recording was
used, and no person verified the sound during this experiment.

This demonstrates how to suppress the observed unwanted unmute without holding
the CPU awake. It does not demonstrate an audible fix, repair the repeated
wakeups or justify permanently muting the speaker. A real fix must preserve
normal audio and intentional wake, including valid playback while the display
is off. GPIO traces do not substitute for listening and repeated wake tests.

## Remaining work

- Identify the wake trigger, including PHY/link transitions and offload behavior;
  do not infer it solely from the firmware code or wake-source event count.
- Integrate correct amplifier lifetime with the audio/power path, rather than
  forcing a permanent user mute or a permanent wake lock.
- Test remote/box-button wake, Ethernet recovery, playback and repeated cycles,
  with a verified way to power-cycle if needed.
- Build the final ROM and verify that its actual images contain the fix. These
  private diagnostics did not change the frozen candidate.
