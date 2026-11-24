# Developer preview validation limits

No public binary preview is available yet. This is the release-preparation
matrix, not a promise that every listed feature will work after a clean install.
The development device has existing data and separately installed Google apps.

| Area | Evidence | Still required |
|---|---|---|
| Model/architecture | 2026 onn 4K Pro jarvis2; ARM32 Android 14 on stock ARM64 kernel | Other models and 64-bit Android are unsupported |
| Home and remote | Owner verified home, focus and Select on a private slot-A build | Fresh pairing/defaults, repeated reboot and alternate-launcher tests |
| Settings controls | f38 system_ext companion and required grants verified live; enabling its disabled key service restored owner-verified Bluetooth hold and widget double-press after clean setup | First-run activation without ADB/AI, repeated binding/reboot and all custom actions |
| AirPods | Owner verified removal pause and reinsertion resume | Final-image reconnect, competing sessions and other models |
| Audio | Private HDMI/Bluetooth and dual-output tests | Receiver-based lossless passthrough proof; multi-headphone support is not established |
| Sleep | A workaround stopped speaker clicking; a deeper wake test failed | Genuine suspend/wake fix and repeated hardware cycles |
| Networking/USB | Development connections worked; USB detection has been intermittent | Final-image Wi-Fi/Ethernet reconnect, USB host/device and hub matrix |
| Google apps | Play sign-in worked; VLC and YouTube TV installed after landscape feature correction | Separate supported installation route for EROFS; no certification or app-catalog guarantee |
| Smart Home | Provider configuration/shortcuts and a brief built-in microphone test | Actual assistant conversation and independent remote microphone validation |
| Release signing | Encrypted key backup verified; exact corrected `f38da52` package/APEX, system OTA certificate, filesystem and complete stock-template AVB checks passed | Hardware acceptance, stock recovery trust and migration tests |
| Installation/recovery | Native read-only seven-target dry-run passed for corrected f38; existing recovery helper and Android A roundtrip passed | Replacement stock recovery transport, actual installation/restore and clean setup |

Slot B is not a proven fallback. Current captured logical partitions for B have
no allocated foundation; earlier stock-fastboot operations modified shared LP
metadata. Do not assume a partition suffix isolates the other slot, and do not
restore old snapshot/COW metadata blindly. User data is shared between slots.
See [slot installation](SLOT_INSTALLATION.md) and [restore evidence](RESTORE_PLAN.md).

Production-key preserved-data upgrades from development-key builds are not
supported. See [release signing](RELEASE_SIGNING.md). No document here authorizes
a wipe or installation on the owner's development device.

After a clean reset, remote side-panel shortcuts require the **Jarvis2 Remote
Settings** accessibility service to be enabled. The app can already be present
in the ROM while this service is off; reinstalling the ROM is not the remedy.
Enable its service in Android Accessibility settings. This normal-user setup
route still needs a recorded navigation test and clearer onboarding before
public release. See [the integration ledger](PERSISTENT_FEATURES.md).

For reproducible bugs, open an issue in this project's repository using the
Developer preview bug template. Report the exact build, firmware base, steps and
redacted evidence. This unofficial project is independent of LineageOS and does
not provide LineageOS official support. Hardware or fresh-install results not
recorded above remain unverified.


The corrected candidate uses stock init_boot/vendor_boot. Offline inspection of
its stock recovery shows `ro.secure=1`, `ro.adb.secure=1`, `ro.debuggable=0`;
the tested development recovery uses the opposite values and a different adbd
SELinux launch label. Its adbd binary matches stock, but those configuration
differences mean the successful development-recovery root shell does not qualify
a root restoration shell in the replacement recovery. Stock recovery runtime
transport and the before-recovery failure path still require verification.
