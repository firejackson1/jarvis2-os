# Persistent integration ledger

Updated 2026-11-24. These are separate evidence levels. A working live RAM patch
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

| Feature | Reproducible source/build state | Remaining release evidence |
| --- | --- | --- |
| Controls, widgets, button editor, Smart Home shortcuts | Controls 1.0/code 1 APK verified in f38 system_ext and signed archive; live package previously resolved to that privileged path | After clean setup the key service was disabled; enabling it restored owner-verified Bluetooth hold and widget double-press. The 1.1 onboarding candidate is not in f38; normal-user setup and other feature tests remain open |
| TV Settings categories | Static RRO payload verified in the extracted f38 image and signed archive | Fresh overlay activation and navigation |
| Native AirPods Settings row | Java source patch compiled in TvSettingsTwoPanel | Rebuilt APK and fresh-install behavior |
| AACP basic-mode compatibility | Native Bluetooth patch compiled into APEX | Final APEX contents, signing and real reconnect/pause/resume |
| Open launcher choice | Pinned project-signed GPL launcher APK verified in f38 product and signed archive | Complete native-library/source correspondence, Home-role and clean reboot checks |
| Custom animation | Exact pinned archive verified in f38 product and signed archive; all descriptor parts use interruptible `p` playback | Repeat visual/boot timing test after further integration; descriptor inspection alone is not a timing measurement |
| Audio policy engine libraries | All four declared libraries verified in f38 system and signed archive | Matching vendor policy engine and real output behavior |
| Audio HAL, policy and config | Earlier development used live RAM mounts; private legacy staging tools exist | Do not treat those runtime experiments as inclusion in the clean f38 images. Licensed, reproducible integration and actual audio testing remain required |
| Lossless/DTS changes | Unlicensed DTS replacement excluded from new Git | Do not bundle or claim this replacement without a verified license route |
| USB/ADB | Authenticated USB defaults in product source | Fresh USB role changes, recovery and fastbootd; no personal ADB keys |
| Remote Power/Mic customization | App routing works with live F11/F10 keylayout aliases | Framework-native fail-safe required before persisting aliases |
| Sleep/wake | Earlier workaround prevented clicking but genuine wake failed. The clean trial had a 60-second idle timeout; a later live keep-awake setting prevents automatic sleep while powered | The live setting is not baked into f38 and does not fix intentional suspend. True suspend, box-button/remote wake and repeated-cycle validation remain open |
| Lock screen and notifications | Product TV SystemUI, default lock-screen property | Clean-user behavior, no handset SystemUI and remote Settings behavior |
| Recovery, installation and rollback | f38 retained stock bootstrap recovery. The separate ARM64 LCARS ramdisk rebuilt byte-identically; its first RAM launch stalled at the logo and Android returned after power-cycle | No new recovery was installed. Successful RAM operation, recovery-owned Bluetooth, complete AVB integration and normal-user install/restore tests remain required |
| Music session cleanup | Current f38 APK has a one-instruction, empty onDestroy; later source patch and a signed standalone candidate are available, with [offline evidence](../manifests/music-cleanup-candidate.json) | Integrate the cleanup in a new image, then test Android lifecycle, Bluetooth browsing and playback |

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
private signed app build passed; it is not installed or included in the frozen
f38 image. Visual, disabled-state and normal-user activation tests remain open.
Offline signature verification found the 1.1 candidate and frozen app use the
same project certificate. A DEX class inventory found no missing application
classes apart from generated resource classes; the candidate adds one UI lambda.
These scoped checks support an update test but do not prove it installs or works.

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
