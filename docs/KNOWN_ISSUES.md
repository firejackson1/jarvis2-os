# Developer preview validation limits

No public binary preview is available yet. This is the release-preparation
matrix, not a promise that every listed feature will work after a clean install.
The development device has existing data and separately installed Google apps.

| Area | Evidence | Still required |
|---|---|---|
| Model/architecture | 2026 onn 4K Pro jarvis2; ARM32 Android 14 on stock ARM64 kernel | Other models and 64-bit Android are unsupported |
| Home and remote | Owner verified home, focus and Select on a private slot-A build | Fresh pairing/defaults, repeated reboot and alternate-launcher tests |
| Settings controls | Tap/hold/double actions verified during development; native overlay compiles | Exact final-image behavior after clean setup |
| AirPods | Owner verified removal pause and reinsertion resume | Final-image reconnect, competing sessions and other models |
| Audio | Private HDMI/Bluetooth and dual-output tests | Receiver-based lossless passthrough proof; multi-headphone support is not established |
| Sleep | A workaround stopped speaker clicking; a deeper wake test failed | Genuine suspend/wake fix and repeated hardware cycles |
| Networking/USB | Development connections worked; USB detection has been intermittent | Final-image Wi-Fi/Ethernet reconnect, USB host/device and hub matrix |
| Google apps | Play sign-in worked; VLC and YouTube TV installed after landscape feature correction | Separate supported installation route for EROFS; no certification or app-catalog guarantee |
| Smart Home | Provider configuration/shortcuts and a brief built-in microphone test | Actual assistant conversation and independent remote microphone validation |
| Release signing | Tools built; independent key set has a tested backup | Signed-package verification, complete AVB assembly, hardware trust and migration tests |
| Installation/recovery | Earlier authorized slot-A image writes/readbacks and Android boot succeeded | Reusable interrupted-install restoration and clean-install instructions |

Slot B is not a proven fallback. Current captured logical partitions for B have
no allocated foundation; earlier stock-fastboot operations modified shared LP
metadata. Do not assume a partition suffix isolates the other slot, and do not
restore old snapshot/COW metadata blindly. User data is shared between slots.
See [slot installation](SLOT_INSTALLATION.md) and [restore evidence](RESTORE_PLAN.md).

Production-key preserved-data upgrades from development-key builds are not
supported. See [release signing](RELEASE_SIGNING.md). No document here authorizes
a wipe or installation on the owner's development device.

For reproducible bugs, open an issue in this project's repository using the
Developer preview bug template. Report the exact build, firmware base, steps and
redacted evidence. This unofficial project is independent of LineageOS and does
not provide LineageOS official support. Hardware or fresh-install results not
recorded above remain unverified.
