# Connecting developer tools

The public configuration requires normal host authorization and starts with
network ADB off. Rooted debugging is a separate choice. Neither root nor a
factory reset is needed to enable an ordinary debugging connection.

## Restore network ADB after a reboot

In this LineageOS TV Settings build, **ADB over network resets on reboot**.
Its switch changes `service.adb.tcp.port` to `5555` or `-1`; it does not save a
persistent network-listening preference. A box answering a ping while port 5555
is closed can be running Android with this switch off. Ping alone cannot prove
that Android has finished starting.

1. When Android Home is visible, open **Developer options → ADB over network**
   and turn it on. If greyed out, enable the main Android/USB debugging switch
   first. Read and accept the device's own debugging dialog if prompted.
2. Use the address shown below that switch. On your own computer, replace
   `DEVICE_IP` below with that address's IP portion:

   ```sh
   adb connect DEVICE_IP:5555
   adb devices -l
   ```

3. If Android asks to authorize the computer, check its fingerprint and approve
   your own computer. An `unauthorized` entry is a pending authorization, not a
   reason to import someone else's ADB keys or turn authentication off.

After connecting, a read-only boot check is:

```sh
adb -s DEVICE_IP:5555 shell getprop sys.boot_completed
```

`1` reports Android boot completion. An empty result, missing device or refused
connection does not. Check the TV screen as well. An ADB connection by itself
does not verify recovery, fastbootd, installation or rollback.

Turn network debugging off when finished. This guide does not add a persistent
listener or change a user's existing settings automatically.

## USB and recovery

For USB debugging, use the box's USB-A data connection and keep its separate
power connected. Run `adb devices -l` and authorize your own computer if asked.
If the computer lists no USB device at all, Android authorization has not yet
been reached. Check data connection, USB role and the host/controller owning
the port, especially when using a VM; do not treat it as an RSA-key failure.

Recovery and bootloader are different modes. `adb devices` can show recovery or
sideload while `fastboot devices` lists bootloader/fastbootd connections. Presence
in one mode does not establish a working shell or another mode's transport.
Neither command flashes, wipes or switches slots. Do not make those changes to
diagnose a missing debugging connection.

## Source reference and validation limits

The [pinned TV Settings development fragment](https://github.com/LineageOS/android_packages_apps_TvSettings/blob/26fd224082c96fa32e0bfe60b288093c6e7522f3/Settings/src/com/android/tv/settings/system/development/DevelopmentFragment.java)
implements the temporary property switch. Its XML makes the switch depend on
the main ADB switch; its English summary explicitly says it resets on reboot.
Those three files in the native build tree matched the pinned Git source.
The post-power-cycle network port was observed closed, but that boot's property
value, completed Home screen and this on-device re-enable flow have not yet been
verified. Do not interpret source behavior as a completed hardware test.
