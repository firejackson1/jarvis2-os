# Music service session cleanup

The bundled Music service creates a MediaSession in onCreate and has an empty
onDestroy. Inactive sessions remained after a live start/stop test; concurrent
Bluetooth browsing prevents attributing every new session to that one command.
The missing release is independently visible in the pinned source.

Use the normal MediaSession release API and call the superclass cleanup. Clear
the field so repeated cleanup is harmless. Removing Music or restarting its
process would avoid this lifecycle rather than fix it and can disrupt clients.

Keep this as a small offline platform patch against the pinned Music revision.
Do not change the installed app, user state, power state, either slot, or frozen
images. The owner delegated continuing fixes and opted out of further routine
design questions. This patch is not a claimed sleep or speaker-click fix.

Verify the actual patched callback with a host lifecycle regression, compile the
complete changed class against SDK 34 and the matching app classpath, and run
the repository host suite. Record exact source and compile evidence. A final
ROM rebuild and on-device lifecycle test remain separate qualification steps.
