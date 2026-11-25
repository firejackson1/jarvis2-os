# Jarvis2 developer preview contents and validation

The current neutral developer-preview candidate targets the unlocked 2026 onn
4K Pro Jarvis2, US stock build 15640252. Android 14 userspace is ARM32 on a
64-bit stock kernel. The binary candidate remains private while installation,
recovery, rollback and distribution checks are pending.

## Included in the candidate

| Area | Offline-verified content | Hardware work still required |
| --- | --- | --- |
| Remote and widgets | Jarvis2 Controls 1.1 includes the button editor, Settings shortcuts and the left widget panel. TV Settings includes the onn Back + Home pairing instructions and the native AirPods entry. | Enable **Jarvis2 Remote Settings** in Android Accessibility to use the shortcuts. Verify onboarding without ADB, reconnects and the Xbox layout on a clean install. |
| Bluetooth and audio | Bluetooth panel, AirPods removal pause and reinsertion resume, AACP fallback, output selection, HDMI plus Bluetooth routing, automatic delay estimates and manual per-device adjustment. Four stock-compatible audio policy libraries are present. | Recheck output selection, AirPods reconnects and the dual-output delay. Multi-headphone support and lossless HDMI passthrough are unverified. |
| TV interface and launcher | TV SystemUI, TV Settings controls overlay, TV feature declarations, a default lock-screen disable property, native remote keylayouts and the bundled LTvLauncher. | Verify the lock screen, notifications, default Home and launcher switching after setup. FLauncher and Bridge Console TV were optional development-device installs. |
| Smart Home | Provider setup and shortcuts in TV Settings. A separate development-device test recorded briefly from the built-in microphone. | Verify a real provider conversation and remote microphone capture. Matter commissioning, Thread routing and voice satellite operation remain open. |
| USB and ADB | Authenticated USB defaults and a source patch for explicit network-listener port handling. | Verify host/device switching, hub behavior and reconnects. Network ADB is opt-in. |
| Music and boot artwork | Music releases its media session on destruction. The neutral preview has the original four-dot animation with interruptible playback. | Test Android service teardown and measure boot timing on the packaged preview. |
| LCARS Recovery | ARM32 UI extension, source and notices. Local reconstruction preserves the stock Fastbootd and boot-control services and verifies the signed binding of the Recovery image. | Verify the installed UI, USB ADB, Fastbootd, return to Android and physical restoration. The five-option Linux menu was tested separately in RAM. |

## Development changes still outside this candidate

- The speaker-click investigation and temporary keep-awake workaround are
  recorded. A production suspend/wake fix is still open.
- The native Power and Assistant/Mic remaps need a framework fallback before
  enabling them by default. The shipped keylayouts retain native behavior.
- The RAM Recovery build has booted Linux from the SanDisk. Installed Recovery
  USB boot, Recovery Bluetooth input and standalone power-on USB boot remain open.
- The experimental TrueHD/DTS HAL changes still need redistribution and
  receiver-based validation. The signed preview includes the four audio
  policy libraries listed above.
- Google apps are a separate local composition. The vanilla ZIP ships without
  them and makes no Play certification or catalog guarantee. The branded boot
  animation remains in a private variant. Personal apps and settings require
  their own installation or setup.

The [patch and feature ledger](https://github.com/firejackson1/jarvis2-os/blob/main/docs/PERSISTENT_FEATURES.md)
links the source patch checks and image readback. Use the ZIP manifest and
release receipt to identify the exact build.

## Installation and recovery limits

The ZIP is a raw-image package for offline validation. The LCARS image must be
reconstructed locally from the matching stock OTA. Signer continuity and a
file-backed install/rollback rehearsal passed. Key acceptance and restoration on
physical hardware still need verification for this exact payload.

The saved slot A layout fit all seven target and restore images. A saved slot B
view had no allocated logical foundation, so it cannot serve as a verified
fallback. Both slots share userdata and logical partition metadata. A read-only
live layout and snapshot check is required before qualifying a write plan.
Production-key upgrades from development-key builds are unsupported.

Report bugs in the [Jarvis2 project](https://github.com/firejackson1/jarvis2-os/issues)
with the build, firmware base, steps and redacted logs. This unofficial project
is independent of LineageOS and uses its own support channel.
