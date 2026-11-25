# Persistent integration ledger

Updated 2026-11-25. These are separate evidence levels. A working live RAM patch
or installed app update does not establish behavior after a fresh ROM install.
The installed engineering trial uses frozen product source
`f38da52af274a0e50c92a10cf279e62f44125358`; its source, signing and image audit
receipts are recorded in DEVELOPMENT.md. Later recovery and device-setting
changes do not retroactively change those images.

The [frozen vanilla feature receipt](../manifests/frozen-f38-feature-evidence.json)
now binds 15 selected APK/APEX/library/artwork/keylayout files to the exact
signed target-files archive. Their extracted filesystem data also matches the
corresponding prefixes of the final delivery images. This is selected packaging
evidence, not an installed-device inventory, a fresh complete AVB/privacy audit
or qualification of every listed feature.

## Release candidate inclusion

The current product build is pinned at
`cb9334ee26ccd80d9f5e5d9276905440b93eaeba`. Its build namespace passed the
source verifier for all eight patches across six series and twelve affected
files. The pin includes Controls 1.1, the Music service cleanup, TV pairing and
Settings changes, the AACP fallback, the ADB reconnect change and the OTA
key-tooling patch. The native build produced the fresh `jarvis2.cb9334ee26cc`
target-files archive. Verified its embedded build identity and Controls 1.1,
the rebuilt Music APK and ART files, and the pinned launcher and animation.
The [current candidate receipt](../manifests/current-cb9334-inclusion.json)
ties the patch report and product commit to the production-key signed archive
and five final image hashes. All three
[complete EROFS filesystems match that archive](BUILD.md#inspect-the-generated-images-themselves).
All 21 selected members matched on readback, including Controls, Music and its
ART files, TV Settings, SetupWizard, TV SystemUI, Bluetooth and ADB APEX,
launcher, animation, four audio policy libraries, two keylayouts and the
privilege allowlist. The signing tool installed the pinned project OTA
certificate in the archive and final system image. The receipt also pins the
separately built LCARS plug-in, notices, derived `vendor_boot` and AVB chain.
Clean-install, recovery transport, rollback and artifact review remain open.

The [neutral r2 release inventory](../manifests/neutral-r2-release-coverage.json)
records the exact eight patch files and their six source series, all 21 tracked
files read from the ROM ZIP, and the independent LCARS source pin. The staged
product source archive matches all 200 files in the build commit. The r2 ZIP
updates the embedded [Known Issues page](KNOWN_ISSUES.md) and preserves all five
images, the LCARS plug-in and its notices byte for byte. The inventory
accompanies the private download set.

| Release change | Where to find it in neutral r2 |
| --- | --- |
| Settings tap and hold, left widget panel, button editor, Home chooser and Smart Home provider settings | Controls 1.1 in `system_ext`. The TV Settings overlay exposes the settings entries. Shortcut handling requires Accessibility consent. |
| Onn remote pairing, remotes and accessories, native AirPods entry | Patched TV Settings and SetupWizard in `system_ext`. The onn keylayout is present in `system` and `product`. |
| AirPods pause/resume, Bluetooth and sound panels, HDMI plus Bluetooth routing, automatic delay estimate and manual adjustment | Controls 1.1 in `system_ext`, AACP compatibility in the Bluetooth APEX and four audio policy libraries in `system`. The 50 ms AirPods calibration from testing is a per-device preference. |
| TV Home, lock-screen default and notification UI | LTvLauncher in `product`, TV SystemUI in `system_ext`, and `ro.lockscreen.disable.default=true` in `system`. The Home chooser discovers additional launchers after installation. |
| Authenticated USB ADB and explicit network port behavior | `ro.adb.secure=1`, `persist.sys.usb.config=mtp,adb` and the rebuilt ADB APEX in `system`. Network debugging is opt-in. |
| Music cleanup, neutral boot animation and OTA trust | Rebuilt Music APK and matching ART files and the neutral boot animation in `product`. The updated OTA certificate bundle is in `system`. |
| LCARS Recovery | ARM32 plug-in, notices and a pinned source archive. The host preflight reconstructs `vendor_boot` locally from the matching stock OTA. Installed HDMI, USB ADB, Fastbootd and physical rollback await hardware tests. |

The private Google-app rehearsal preserves the same 21 tracked feature files
and LCARS plug-in. It uses disposable AVB keys for offline testing. The
vanilla r2 package is the public-preview candidate.

### Features still in development

- **Recovery and bootloader:** The SanDisk desktop and missing-drive fallback
  worked in the ARM64 RAM Recovery. Installed USB Linux needs a validated USB
  handoff and enforcing policy. Recovery Bluetooth input and booting straight
  from USB at power-on remain open.
- **Suspend and power:** The speaker-click traces and temporary workaround
  are recorded in the suspend investigation. Genuine wake and native Power
  and Assistant/Mic remapping still need a fail-safe and device tests.
- **Audio and Smart Home:** TrueHD/DTS passthrough, simultaneous Bluetooth
  headsets, remote microphone capture, voice satellite operation and
  Matter/Thread commissioning remain open.
- **Optional apps and artwork:** FLauncher and Bridge Console TV were
  development-device installs. The public-preview animation is the neutral
  four-dot design. The branded animation remains in the private variant.

## Feature evidence

| Feature | Reproducible source/build state | Remaining release evidence |
| --- | --- | --- |
| Controls, widgets, button editor, Smart Home shortcuts | Controls 1.1/code 2 is in the current signed `system_ext`, with shortcut onboarding and required privileges | Android Accessibility consent is required. On the earlier clean setup, enabling the service restored owner-verified Bluetooth hold and widget double-press. Current-image onboarding, Xbox input and a real Smart Home provider conversation remain open |
| AirPods, Bluetooth and audio controls | The current Controls APK includes the icon panels, AirPods wear pause/resume, HDMI plus Bluetooth routing, automatic delay estimation and manual per-device calibration | Recheck fresh pairing, pause/resume and audio sync. A prior AirPods calibration is user data. Two simultaneous Bluetooth headsets are unverified |
| TV Settings categories | Static RRO payload verified in the extracted f38 image and signed archive | Fresh overlay activation and navigation |
| Native AirPods Settings row | The signed TvSettingsTwoPanel APK in the private rehearsal contains the row and calls its update method from the accessories screen | Clean-user navigation with paired AirPods |
| Remote pairing during initial setup | The signed TV Settings APK contains the onn Back-and-Home instructions and the signed SetupWizard requests `BLUETOOTH_CONNECT`. Both APKs matched the exact rehearsal image | Fresh setup and remote reconnect on hardware |
| AACP basic-mode compatibility | Native Bluetooth patch compiled into the APEX. The final r2 APEX matched the signed target-files payload. | Real reconnect/pause/resume on the exact r2 build |
| Open launcher choice | Pinned project-signed GPL launcher APK verified in f38 product and signed archive | Complete native-library/source correspondence, Home-role and clean reboot checks |
| Boot animation | Exact neutral archive verified in r2 product. All descriptor parts use interruptible `p` playback. | Check the neutral artwork on HDMI and measure boot timing |
| Audio policy engine libraries | All four declared libraries verified in f38 system and signed archive | Matching vendor policy engine and real output behavior |
| Audio HAL, policy and config | Earlier development used live RAM mounts; private legacy staging tools exist | Do not treat those runtime experiments as inclusion in the clean f38 images. Licensed, reproducible integration and actual audio testing remain required |
| Lossless/DTS changes | Unlicensed DTS replacement excluded from new Git | Do not bundle or claim this replacement without a verified license route |
| USB/ADB | Authenticated USB defaults in product source | Fresh USB role changes, recovery and fastbootd; no personal ADB keys |
| Remote Power/Mic customization | App routing works with live F11/F10 keylayout aliases | Framework-native fail-safe required before persisting aliases |
| Sleep/wake | Earlier workaround prevented clicking but genuine wake failed. The clean trial had a 60-second idle timeout; a later live keep-awake setting prevents automatic sleep while powered | The live setting is not baked into f38 and does not fix intentional suspend. True suspend, box-button/remote wake and repeated-cycle validation remain open |
| Lock screen and notifications | Product TV SystemUI, default lock-screen property | Clean-user behavior, no handset SystemUI and remote Settings behavior |
| Recovery, installation and rollback | f38 retained stock bootstrap recovery. A later ARM64 RAM build showed the custom menu on HDMI. The owner confirmed the box button moves focus, Reboot system now returns to Android, and Boot Linux from USB starts the SanDisk desktop | Installed Recovery still needs authenticated ADB, Fastbootd and boot-control integration, AVB and a normal-user install/restore test. See [installed Recovery audit](#installed-recovery-audit) |
| Music session cleanup | The current source-built APK and both matching ART files are in the final signed product image. The [f38 rehearsal](../manifests/f38-app-integration-rehearsal.json) used a separately built cleanup APK | Verify Android service lifecycle, Bluetooth browsing and playback on the current image |

## Clean-install remote-service activation gap

The side-menu code was present after the shared-data reset, but
`accessibility_enabled` was zero and no key service was enabled. The installed
package was `/system_ext/priv-app/Jarvis2RemoteSettings/Jarvis2RemoteSettings.apk`.
Its injection, audio-routing, media-control and privileged Bluetooth permissions
were granted. Enabling `app.jarvis2.remote/.Keys` for the current user made it
bind without crashed or pending services. The owner then verified both Settings
hold for Bluetooth and double-press for the left widget panel.

This proves that missing activation explained this incident; it does not prove
automatic setup or every control works on a new user. Release onboarding must
provide a visible way to enable the service through Android Accessibility
settings, document the required access, and verify it without ADB or an AI.
Do not import an owner's accessibility-service list or preferences into an image.

Controls version 1.1 (version code 2) now adds enabled/disabled status and an
Enable/Manage remote shortcuts button to the controller-settings source. It
matches this app's exact service component, remains visible without a controller,
refreshes on return and opens Android's own Accessibility page for consent. The
private signed app build passed. The current signed ROM contains Controls 1.1,
and the frozen f38 image still contains 1.0. Visual, disabled-state and
normal-user activation tests remain open.
Offline signature verification found the 1.1 candidate and frozen app use the
same project certificate. A DEX class inventory found no missing application
classes apart from generated resource classes; the candidate adds one UI lambda.
These scoped checks support an update test but do not prove it installs or works.


## Private image integration rehearsal

The [two-app image receipt](../manifests/f38-app-integration-rehearsal.json)
records Controls 1.1 and the Music media-session cleanup inside newly assembled
vanilla images derived from frozen f38. Both APKs carry the expected certificate
and embedded DEX. The rebuild removes the older APKs' four stale precompiled
ART files. Every other file payload and native filesystem metadata entry in the
two rebuilt filesystems matched the baseline. The system image matched byte
for byte. The full AVB chain passed offline verification, and two assembly runs
produced identical hashes for all five final images.

All eight tracked patch files across six series apply to their pinned upstream
revisions. The original f38 source tree matches 11 of the 12 resulting files.
The Music source change is the one absent from that tree. A clean release build
must apply the current Music series and compile Controls 1.1 from source with
matching ART precompilation. This rehearsal leaves the frozen release artifact
and its installation evidence separate. Normal-user Controls activation, Music
lifecycle and playback, production recovery integration and final hardware
qualification remain open.

## Installed Recovery audit

The five-option menu was tested through a RAM boot. The owner confirmed the
Linux desktop after selecting Boot Linux from USB with the SanDisk directly
attached. That build included a permissive SELinux domain for the USB Linux
experiment and stopped recovery ADB to hand the USB controller to Linux. Keep
those RAM-specific settings out of the installed preview until a production
policy and USB handoff have been verified. An earlier no-drive run logged a
45-second timeout and kept Recovery running.

The offline installed-image experiment used the earlier reproducible ARM64
ramdisk as a baseline. Replacing the named recovery fragment preserved the
stock platform ramdisk, device tree and boot configuration. The unsigned
26,707,968-byte result fits the 67,108,864-byte reference partition. The modeled
boot layout keeps the stock 32-bit first-stage `init`. Stock Recovery contains
32-bit `recovery`, `adbd` and `fastbootd`. The replacement supplies 64-bit
`recovery`, `adbd` and their linker. Its init configuration declares Fastbootd,
but the baseline archive lacks the executable.

The pinned Fastbootd implementation needs a usable boot-control HAL for A/B
slot variables. Stock Recovery declares both the boot-control and vendor
Fastboot HALs as AIDL services. In the stock archive their ELF dependencies
resolve to 21 and 30 ARM32 paths respectively, including their executables and
linker. All those paths are absent from the ARM64 repack. This offline check
establishes file coverage. Working Binder registration, linker namespaces,
USB enumeration, recovery-owned remote support, return to Android and stock
restoration still require verification. The repack was unsigned and remained
off-device.

### Stock-compatible ARM32 LCARS prototype

Stock Recovery loads a UI extension factory. A separate ARM32 build uses
that entry point and keeps the stock Recovery binary, Fastbootd, AIDL services
and initialization scripts. The factory's first prototype used `ResetUI()`.
An isolated ARM emulator exposed a vendor compatibility issue: Amlogic's
`GetUI()` reads a different member from the one `ResetUI()` updates. The
revised extension owns the original device without changing its UI object and
delegates menu and key handling through a new device adapter.

The revised factory built against pinned AOSP Android 14 headers and the
exact stock libraries. Its `ScreenRecoveryUI` vtable size and all 69
comparable symbol slots matched the stock library. In an isolated Bionic
loader test, both factory libraries loaded separately. The revised adapter
returned all four stock menu labels and matched seven stock key codes with
the menu visible and hidden. These are headless construction and dispatch
checks. HDMI, physical controls, Fastbootd mode, USB authorization, Bluetooth
pairing and boot/restore still require hardware verification.

The unsigned 27,183,104-byte vendor-boot repack fits the 67,108,864-byte
partition. It replaces the factory plug-in, adds the original plug-in under a
separate name and preserves 481 other recovery archive records byte for byte.
The platform fragment, device tree and boot configuration passed exact
comparison. A second compile and repack reproduced SHA-256
`30625d390c1fdd10e4465619bbbd9f66df0ec48652f716ba80371e850fd58862`.
[Pinned AOSP Recovery source](https://android.googlesource.com/platform/bootable/recovery/+/2e6ff7bc40063d38fc5478389a47c0fafba20bfd/)

## Remote alias blocker

Do not persist the live keylayout by itself. Native policy consumes POWER and
VOICE_ASSIST before accessibility, which motivated the aliases. Accessibility
failure passes F11/F10 through unchanged, and a foreground application may consume
a KCM fallback before native handling. The older initial image job predated the
replay correction. The frozen f38 APK now has bytecode-verified handling that
clears FLAG_FALLBACK for POWER/VOICE_ASSIST and sets it for other keys. That fix
is already included in f38; it does not implement interception of native keys
before accessibility or make the aliases safe to ship.

A framework bridge must scope the remote by vendor/product/scan code, permit
accessibility interception while interactive, and restore native policy before
application dispatch if the handler declines/times out. Screen-off handling and
press ownership through matching UP/cancellation require separate treatment.
Test absent/crashed/disabled services, timeouts, screen-off wake, app consumption,
removal and concurrent controllers. Current source does not implement that bridge;
shipping the aliases alone would risk losing basic Power/Mic behavior.
