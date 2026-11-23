# Voice assistant integration

Settings → Smart Home (main Settings menu).

Install an Android assistant app compatible with your build. Select it as the
provider and use Open assistant setup to sign in with your own server/account.
Home Assistant Companion full and minimal packages are detected when installed;
other apps advertising Android ACTION_ASSIST are also listed. Android default
assistant is supported. Configure Home Assistant's server and Assist pipeline
in Companion itself. No Companion APK is bundled or automatically downloaded.

Assign Configured voice assistant to any supported remote/controller gesture
through Remote & controller buttons. Existing bindings stay unchanged. If the
provider supports ACTION_ASSIST, the shortcut opens it; otherwise its launcher
opens. The optional server shortcut opens a browser for sign-in and is independent
of Companion setup. Clearing Jarvis2 preferences does not sign out another app.

Authentication, recording, wake words and conversational audio focus belong to
the selected provider. Jarvis2 does not collect passwords, tokens or microphone
audio, and does not start an always-listening service. The provider must supply
these features; selecting one does not make them work automatically on Android TV.
Use Sound output to access existing Jarvis2 output/sync controls. There is no
separate voice-only forced speaker route or media-pause policy in this version.
Remote hold is a launch gesture, not release-to-stop push-to-talk.

Verified: built-in mic captured one second of 16 kHz audio in the earlier test.
Not verified: provider sign-in/voice roundtrip, Android TV wake-word support,
remote microphone capture or remote speech playback. No personal server,
account, paired-device address or credentials are packaged. Runtime preferences
and accounts must not be included in a ROM release; app backup is disabled.
Existing per-device audio calibrations remain private app data and are preserved.
New devices start uncalibrated rather than inheriting an owner's measurement.
