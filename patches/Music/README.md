# Music media-session lifecycle

Apply the listed patch to `packages/apps/Music` at pinned revision
`c119d5a52f80289c7f939746ddc31c8bcee2a3ca` before a future ROM build. Rebuild
the `Music` module and resulting product image. Do not apply it to a dirty
checkout or reinterpret it as a modification of the frozen f38 candidate.

The original callback never releases the MediaSession created by onCreate.
The patch releases that resource, clears its reference and invokes superclass
cleanup. The host regression executes the actual patched callback body for
normal, repeated and absent-session cleanup; it also confirms that the original
callback fails. This is not a complete Android service/emulator test.

Private live diagnostics observed inactive Music sessions after the service
stopped. Background Bluetooth browsing can also recreate this service, so the
observed count change is not an isolated session-rate measurement. There is
no demonstrated causal connection to the separate suspend/speaker problem.

This source patch has not been installed on the test device. Final-image
lifecycle, browser reconnect and normal playback checks remain required.

The [standalone candidate receipt](../../manifests/music-cleanup-candidate.json)
records a private signed APK built from this patch. Signature verification
matches the frozen Music app's project certificate, all 181 non-signature
payload files survive signing unchanged, and DEX inspection confirms session
release, reference clearing and superclass cleanup. This is an offline update
candidate, not proof of Android installation, lifecycle behavior or integration
in a native Soong-built product image.
