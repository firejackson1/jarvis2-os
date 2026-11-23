# Jarvis2 OS — unofficial development sources

An **unofficial LineageOS 21 / Android 14** TV build for the 2026 onn 4K Pro
(`jarvis2`). This project is independent of LineageOS, onn, Google and Amlogic.

**Not a public ROM release yet. No files in this repository are an installer.**
The working development device currently depends on RAM overlays and separately
installed applications. A booting device does not establish that a new image
contains all its fixes. Clean boot, installation and restoration remain gates.

## Current work

- ARM32 device configuration on the stock ARM64 kernel/hardware interface.
- TV remote/button mappings, left widgets, Bluetooth/AirPods pause and resume,
  sound-output controls and provider-based Smart Home setup.
- Main Settings categories and source patches for native Bluetooth integration.
- Offline build tools, source privacy checks and host tests.

Optional launcher choices are FLauncher, LTvLauncher and the owner's Bridge
Console TV. These APKs are not bundled here. Android TV Home is proprietary and
is not included as a publicly redistributable component.

## Development

Run `./tools/test-host.sh` with Python 3 and JDK 11 or newer. Read
[Build](docs/BUILD.md), [Licensing](docs/LICENSING.md),
[Release checklist](docs/RELEASE_CHECKLIST.md) and
[Development ledger](docs/DEVELOPMENT.md) before assembling images.

Private keys, pre-authorized debugging identities, owner settings, firmware,
DRM material and compiled vendor blobs must never enter this Git history.
The DTS replacement from the lossless-audio experiment is excluded because its
upstream snapshot does not provide an affirmative redistribution license.

## License

Original project code is Apache-2.0 unless a file states otherwise. Component
licenses and notices remain applicable; this is not a blanket relicensing of
LineageOS, Android, firmware, launchers or third-party code. See
[Licensing](docs/LICENSING.md).
