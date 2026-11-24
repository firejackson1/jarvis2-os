# Persistent integration ledger

Updated 2026-11-24. These are separate evidence levels. A working live RAM patch
or installed app update does not establish behavior after a fresh ROM install.
The installed engineering trial uses frozen product source
`f38da52af274a0e50c92a10cf279e62f44125358`; its source, signing and image audit
receipts are recorded in DEVELOPMENT.md. Later recovery and device-setting
changes do not retroactively change those images.

| Feature | Reproducible source/build state | Remaining release evidence |
| --- | --- | --- |
| Controls, widgets, button editor, Smart Home shortcuts | Source app integrated in the f38 system_ext image; live package resolves to its privileged system_ext path | After clean setup the key service was disabled; enabling it restored owner-verified Bluetooth hold and widget double-press. Complete first-run onboarding and other feature tests remain open |
| TV Settings categories | Static RRO rebuilt against candidate target | Extracted image, fresh overlay activation and navigation |
| Native AirPods Settings row | Java source patch compiled in TvSettingsTwoPanel | Rebuilt APK and fresh-install behavior |
| AACP basic-mode compatibility | Native Bluetooth patch compiled into APEX | Final APEX contents, signing and real reconnect/pause/resume |
| Open launcher choice | Pinned GPL launcher Make module built with original signature | Final APK/library paths, Home role and clean reboot |
| Custom animation | Optional local input fragment and validated no-delay archive | Refresh product image, inspect archive and repeat boot test |
| Audio policy engine libraries | Product packages declared and selected | Final library contents and matching vendor policy engine |
| Audio HAL, policy and config | Earlier development used live RAM mounts; private legacy staging tools exist | Do not treat those runtime experiments as inclusion in the clean f38 images. Licensed, reproducible integration and actual audio testing remain required |
| Lossless/DTS changes | Unlicensed DTS replacement excluded from new Git | Do not bundle or claim this replacement without a verified license route |
| USB/ADB | Authenticated USB defaults in product source | Fresh USB role changes, recovery and fastbootd; no personal ADB keys |
| Remote Power/Mic customization | App routing works with live F11/F10 keylayout aliases | Framework-native fail-safe required before persisting aliases |
| Sleep/wake | Earlier workaround prevented clicking but genuine wake failed. The clean trial had a 60-second idle timeout; a later live keep-awake setting prevents automatic sleep while powered | The live setting is not baked into f38 and does not fix intentional suspend. True suspend, box-button/remote wake and repeated-cycle validation remain open |
| Lock screen and notifications | Product TV SystemUI, default lock-screen property | Clean-user behavior, no handset SystemUI and remote Settings behavior |
| Recovery, installation and rollback | f38 retained stock bootstrap recovery. The separate ARM64 LCARS ramdisk rebuilt byte-identically; its first RAM launch stalled at the logo and Android returned after power-cycle | No new recovery was installed. Successful RAM operation, recovery-owned Bluetooth, complete AVB integration and normal-user install/restore tests remain required |

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

## Remote alias blocker

Do not persist the live keylayout by itself. Native policy consumes POWER and
VOICE_ASSIST before accessibility, which motivated the aliases. Accessibility
failure passes F11/F10 through unchanged, and a foreground application may consume
a KCM fallback before native handling. The first image build also uses the old replay flags, which skip native Power
gesture detection. Later app source clears FLAG_FALLBACK for POWER/VOICE_ASSIST;
that app compiled offline but is not installed or in the first image job.

A framework bridge must scope the remote by vendor/product/scan code, permit
accessibility interception while interactive, and restore native policy before
application dispatch if the handler declines/times out. Screen-off handling and
press ownership through matching UP/cancellation require separate treatment.
Test absent/crashed/disabled services, timeouts, screen-off wake, app consumption,
removal and concurrent controllers. Current source does not implement that bridge;
shipping the aliases alone would risk losing basic Power/Mic behavior.
