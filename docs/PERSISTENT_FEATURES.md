# Persistent integration ledger

Updated 2026-11-23. These are separate evidence levels. A working live RAM patch
or installed app update does not establish behavior after a fresh ROM install.
The full image job currently uses source e3ae5fb; later tool/artwork commits have
not been substituted into that running job.

| Feature | Reproducible source/build state | Remaining release evidence |
| --- | --- | --- |
| Controls, widgets, button editor, Smart Home shortcuts | Source app compiled as system_ext privileged package | Extracted image, privileges, fresh user setup and behavior |
| TV Settings categories | Static RRO rebuilt against candidate target | Extracted image, fresh overlay activation and navigation |
| Native AirPods Settings row | Java source patch compiled in TvSettingsTwoPanel | Rebuilt APK and fresh-install behavior |
| AACP basic-mode compatibility | Native Bluetooth patch compiled into APEX | Final APEX contents, signing and real reconnect/pause/resume |
| Open launcher choice | Pinned GPL launcher Make module built with original signature | Final APK/library paths, Home role and clean reboot |
| Custom animation | Optional local input fragment and validated no-delay archive | Refresh product image, inspect archive and repeat boot test |
| Audio policy engine libraries | Product packages declared and selected | Final library contents and matching vendor policy engine |
| Audio HAL, policy and config | Live RAM mounts still present; private legacy staging tools exist | Licensed, reproducible slot-local integration and actual audio testing |
| Lossless/DTS changes | Unlicensed DTS replacement excluded from new Git | Do not bundle or claim this replacement without a verified license route |
| USB/ADB | Authenticated USB defaults in product source | Fresh USB role changes, recovery and fastbootd; no personal ADB keys |
| Remote Power/Mic customization | App routing works with live F11/F10 keylayout aliases | Framework-native fail-safe required before persisting aliases |
| Sleep/wake | Earlier workaround prevents clicking but genuine wake failed | True suspend, box-button/remote wake and repeated-cycle validation |
| Lock screen and notifications | Product TV SystemUI, default lock-screen property | Clean-user behavior, no handset SystemUI and remote Settings behavior |
| Recovery, installation and rollback | Existing device recovery is not a release artifact | Exact complete AVB chain, authorized install and restore tests |

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
