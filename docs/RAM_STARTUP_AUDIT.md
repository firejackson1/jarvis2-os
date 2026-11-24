# RAM startup audit

Status: source inspection only. The new Android 17 recovery has not been
RAM-booted or installed. Loading a boot image with `fastboot boot` does not make
the processes in that image read-only.

This review uses `LineageOS/android_bootable_recovery` at
`1cdebe4061372e9abb5dc738002ad6c707f7c534`, the recovery revision in
`upstream-pins.json`. Links below point to that exact revision.

## Automatic behavior before a menu selection

| Source path | Observed behavior | Requirement for the diagnostic RAM image |
| --- | --- | --- |
| [`recovery_main.cpp`, `get_args()`](https://github.com/LineageOS/android_bootable_recovery/blob/1cdebe4061372e9abb5dc738002ad6c707f7c534/recovery_main.cpp#L102) | Reads the boot-control message. If its command is `boot-recovery`, writes the arguments back to the BCB. With no explicit arguments, can import pending operations from the BCB or cache command file. | Do not inherit a pending install/wipe request. Make internal block devices read-only before Recovery or Android init starts. Verify both the whole device and its partitions. |
| [`recovery_main.cpp`, `copy_userdata_files()`](https://github.com/LineageOS/android_bootable_recovery/blob/1cdebe4061372e9abb5dc738002ad6c707f7c534/recovery_main.cpp#L203) | A non-user build attempts to mount `/data` and copy its ADB authorization keys into the recovery environment. | Exclude userdata from the diagnostic fstab and inspect the actual generated fstab, including any retained vendor fragments. Never import owner keys into a public image. |
| [`recovery.cpp`, `PromptAndWait()`](https://github.com/LineageOS/android_bootable_recovery/blob/1cdebe4061372e9abb5dc738002ad6c707f7c534/recovery.cpp#L490) | Calls `FinishRecovery()` before presenting the menu, not merely after a user asks to reboot. | Hiding destructive menu entries is insufficient. The write guard must already be active. |
| [`recovery.cpp`, `FinishRecovery()`](https://github.com/LineageOS/android_bootable_recovery/blob/1cdebe4061372e9abb5dc738002ad6c707f7c534/recovery.cpp#L133) | Clears the BCB; if cache exists, saves locale and removes the command file. Also invokes `copy_logs()`. | Reject internal block writes and exclude persistent cache mounts during the RAM test. A failed BCB clear must be reported; returning to Android needs a separate test because a pre-existing recovery request may remain. |
| [`recovery_utils/logging.cpp`, `copy_logs()`](https://github.com/LineageOS/android_bootable_recovery/blob/1cdebe4061372e9abb5dc738002ad6c707f7c534/recovery_utils/logging.cpp#L205) | When log saving is requested, writes pmsg; if cache exists, can rotate and copy recovery logs there. | Keep ordinary logs in tmpfs. Distinguish retained RAM/pstore diagnostics from internal Android filesystem writes. Audit the actual logging configuration and devices. |
| [`etc/init.rc`](https://github.com/LineageOS/android_bootable_recovery/blob/1cdebe4061372e9abb5dc738002ad6c707f7c534/etc/init.rc) | Imports `/init.recovery.${ro.hardware}.rc`, starts services and ueventd, and configures USB. `/tmp` is tmpfs, but imported device rules are outside this file. | Review every init import and first-stage configuration in the assembled image. Inspecting this one file does not prove startup is write-free. |

`--show_text` alone does not suppress all these behaviors. In particular, the
BCB update depends on the stored command, and the menu loop still calls
`FinishRecovery()`.

## Current device configuration gap

The current prototype `recovery/recovery.fstab` contains one read-only `ext4`
metadata entry. Earlier device evidence identified metadata as F2FS. That entry
is not a validated hardware configuration and must not be promoted as such.
The diagnostic launch should avoid mounting internal metadata altogether. A
future install-capable recovery will need the correct filesystem and snapshot
handling, independently reviewed and tested.

The queued first platform build intentionally retains its frozen source snapshot.
This finding does not silently change that job's inputs or turn a successful
compile into permission to boot it.

## Required launch design and evidence

1. Use a reviewed early bootstrap selected by the RAM image's init override.
   It must run before Android init, first-stage mounts, and recovery services.
   Retain the device's known kernel and compatible storage modules.
2. Discover the internal MMC device by its actual type, rather than assuming
   `/dev/mmcblk0`. Wait for its required nodes, set and verify block read-only
   status on the device and partitions, and fail closed if that cannot be done.
   Check special MMC boot devices and any aliases exposed by the actual kernel.
3. Control the diagnostic Recovery command line and fstab; do not replay pending
   BCB commands. Audit the finished ramdisk, imported init files, services,
   SELinux policy, module loading and block-node creation order.
4. Keep Bluetooth state and pairing keys in RAM for the initial test. Do not
   mount Android userdata to reuse its pairing database or ADB trust.
5. Record exact image/source hashes, a preflight state capture, write-guard
   output, display/input/ADB observations and post-test partition hashes. Test
   return to Android explicitly; neither a bootable menu nor a host unit test
   proves that path.
6. Obtain authorization for the concrete hardware test. No device reboot,
   partition write or slot change is part of this source audit.

The earlier Linux RAM prototype provides a useful MMC read-only implementation
to review, but its BusyBox init is not Android recovery init. Its successful boot
does not validate the new Android 17 service lifecycle. A block read-only flag
also is not a security boundary against a privileged process deliberately
clearing it; the test must contain no such operation.

## Remaining verification

The full platform link and generated ramdisk are still pending. Until they exist,
the complete init/import/fstab/module graph cannot be audited. This document
records concrete upstream write paths and launch requirements; it is not a
completed read-only startup qualification or a restore guarantee.
