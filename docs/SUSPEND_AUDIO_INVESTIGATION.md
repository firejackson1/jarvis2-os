# Suspend audio investigation

Status: unresolved; no driver fix is installed. Preserve the stock fallback and
keep experimental driver work outside released images until wake and audio are
verified together.

## Established observations

- The owner hears clicking and reports that it starts immediately when sleep
  is requested. That timing does not yet distinguish the first mute edge from
  the first rapid resume/unmute edge.
- Earlier traces bound the loaded vendor drivers to retained analysis inputs.
  The sound-card suspend path mutes the speaker; its resume worker subsequently
  unmutes it, even while the Android framework remains asleep. A temporary
  standard speaker-mute control prevented the worker's unmute writes without
  stopping repeated suspend/resume. The control was restored. That experiment
  had no independent audible confirmation.
- Disabling vendor Ethernet wake previously prevented normal wake and required
  a power cycle. It is not a qualified fix.

## ADB observer check, 2026-11-24

An established TCP ADB socket had a roughly one-second keepalive timer. The
retained ADB source defaults `ADB_TCP_KEEPALIVE_INTERVAL` to one second. Earlier
traces without intentional host polling still had this socket open, so they
did not exclude automatic ADB traffic as a contributor.

Used one owned tracefs instance with power suspend/wakeup-source events, the
boot clock and 128 KiB per CPU. Requested sleep for three 35-second host-clock
windows, waking the framework between them. Network wake remained enabled.

| Condition | Machine-suspend entries | Ethernet wake-source activations | Framework at collection |
| --- | ---: | ---: | --- |
| ADB connected, first run | 6 | 6 | Asleep |
| ADB disconnected | 3 | 3 | Awake after HDMI wake |
| ADB connected, second run | 6 | 6 | Asleep |

The disconnected run's entries occurred about 3.4, 10.3 and 16.4 seconds after
the start marker. Android logged an HDMI framework wake about 21 seconds into
that run, before the scheduled ADB reconnection. This confounds a comparison of
whole-window rates. It does **not** erase the three earlier cycles with the
ADB transport closed; an established ADB connection is not necessary for those
cycles. This test does not establish which Ethernet packet or hardware event
initiates them.

On the actual host peer, a non-promiscuous capture retained only the fixed
Ethernet/IPv4/TCP headers, at most 54 bytes per packet. The interval after TCP
close and before reconnect contained zero target TCP packets for 34.005
seconds. Matched the FIN/SYN to the phase's recorded disconnect/reconnect
times; an initial parser incorrectly included unrelated connection probes.
The erroneous summary was retained privately, then corrected against those
phase receipts. No application payload or raw runtime identity is published.

All trace buffers reported zero overruns, commit overruns and dropped events.
Removed the owned instance and verified global tracing remained off with the
nop tracer. Left Android awake on slot A with ADB connected. No partition
write, slot switch, reboot, wake-setting change or desktop interruption was
performed in this experiment.

## Driver path and next qualification

The related [Amlogic sound-card source published by Khadas](https://github.com/khadas/common_drivers/blob/3a11a86a02e759fc57fc79410215f7c0c3a0d8e0/sound/soc/amlogic/auge/card.c#L1014)
sets speaker mute during suspend and clears it during resume, then schedules a
GPIO worker. That worker path also re-registers the mixer control and requests
the GPIO. Its structure helps interpret the retained module's disassembly;
it is **not** verified corresponding source for the shipped module. Retained
reference file SHA256:
`2160fa12f2cfcb330f5c87bbf38604f94e9f25a8e76890f814eae94952e077c7`.

A real candidate needs to sequence amplifier mute against the speaker's audio
path, including background playback, instead of unmuting on every CPU resume.
Do not substitute permanent mute, disabled wake or a permanent suspend blocker.
Still required:

- Identify/qualify the board's amplifier and codec power sequence and obtain
  buildable vendor-driver source with verified correspondence.
- Distinguish the first suspend pop from subsequent resume pops without
  repeatedly sleeping the owner's box during offline work.
- Compile and inspect the candidate offline, then use a separately authorized
  RAM test with a working return path.
- Verify quiet sleep, remote/box/network wake, normal speaker playback,
  background audio, HDMI/Bluetooth routing and repeated cycles.

The separate exact GKI-core source match does not establish corresponding
source for these vendor modules. See [kernel provenance](KERNEL_SOURCE_PROVENANCE.md).
