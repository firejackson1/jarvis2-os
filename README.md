# Jarvis2 OS — unofficial development sources

An **unofficial LineageOS 21 / Android 14** TV build for the 2026 onn 4K Pro
(`jarvis2`). This project is independent of LineageOS, onn, Google and Amlogic.

**Not a public ROM release yet. Candidate ZIPs are raw images, not OTA installers.**
The experimental [recovery raw writer](docs/CANDIDATE_INSTALLATION.md) is under
offline qualification; do not execute it on hardware without a reviewed test plan.
The first private source build has booted slot A with existing data; Home and
remote navigation were human-verified and image readback matched. Advanced
integration, clean-install behavior and restoration remain open gates. Shared
Virtual A/B metadata needs special handling; B is not a verified fallback.

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

Clone this repository as `device/onn/jarvis2` in the Android checkout.
Run `./tools/test-host.sh` with Python 3, Git, a C++17 compiler, JDK 11 or newer and the system
Brotli decoder library (`libbrotli1` on Debian/Ubuntu). Read
[Build](docs/BUILD.md), [Licensing](docs/LICENSING.md),
[Release checklist](docs/RELEASE_CHECKLIST.md),
[Slot installation status](docs/SLOT_INSTALLATION.md),
[Optional Google apps](docs/GOOGLE_APPS.md),
[Local GApps composition](docs/GAPPS_COMPOSITION.md),
[Release signing](docs/RELEASE_SIGNING.md),
[Raw image AVB assembly](docs/AVB_IMAGE_ASSEMBLY.md),
[Offline candidate packaging](docs/CANDIDATE_PACKAGING.md),
[Experimental recovery writer](docs/CANDIDATE_INSTALLATION.md),
[Known issues and validation limits](docs/KNOWN_ISSUES.md) and
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
