# adbd network default policy

Apply `series` to `packages/modules/adb` at
`8f1f33d623ca6cffd6c415b43b317fd274660601`.

Android product's `service.adb.tcp.port=-1` overrides the stock vendor default.
The patch prevents adbd from reopening TCP 5555 when USB is absent and the port
is explicitly disabled. An unset port retains upstream fallback; positive ports,
USB behavior, authentication and host adbd behavior stay intact. Existing
`service.adb.listen_addrs` precedence is unchanged.

The pure helper is exercised by both upstream `adb_test` / `adbd_test` GTests
and the repository's lightweight C++ compilation test. No device is required
for the latter. Product builds must verify the final adbd payload and product
property; host checks do not establish runtime port state.

The mandatory `Jarvis2LtvLauncher` module overrides `Updater` using Android's
existing package replacement mechanism, removing official automatic and manual
update checks. This exclusion is coupled to that launcher remaining mandatory;
changing launcher packaging requires retaining the Updater exclusion elsewhere.
This does not change recovery or establish recovery trust in new release keys.
