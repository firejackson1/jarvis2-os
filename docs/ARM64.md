# ARM64 migration assessment

The owner requested moving toward 64-bit Android while porting recovery.
This source tree now targets ARM64 recovery. The installed device has not been
converted or flashed by this side conversation.

## Evidence from saved images

- The saved vendor_boot v4 ramdisks contain ARM32 native init and recovery.
- Their ELF inventory contains 118 ARM32 userspace objects and 52 AArch64 kernel
  module objects. Kernel module architecture must not be counted as userspace support.
- Read-only inspection of the saved vendor and ODM images found no `/lib64`.
- Read-only inspection of saved OEM and ODM-ext images found no `/lib64`,
  `/vendor/lib64` or `/odm/lib64` directories.

This identifies a standard 64-bit vendor-library packaging gap; it is not an
exhaustive claim that no usable 64-bit binary exists elsewhere. No image was
mounted writable or used to change a device during inspection.

## Same-SoC reference

The ODROID-C5 device tree explicitly supports an Android 64-bit build selected
by `ANDROID_BUILD_TYPE=64`, with ARM64 primary and ARM32 secondary architecture.
It identifies S905X5M/S7D and kernel 5.15. Its graphics build includes Amlogic
gralloc and hardware-composer projects.

Pinned primary reference:
[ODROID-C5 BoardConfig](https://github.com/codewalkerster/android_device_hardkernel_odroidc5/blob/680084ee8cdd26cfb6accfbaa2cfa4cfdf40962f/BoardConfig.mk).
This is an Android 14 hardware/build reference, not an Android 17 Jarvis2 port
or proof that its proprietary binaries match our kernel. Its bootloader, DTB and
board-specific power/storage configuration must not be copied onto Jarvis2.

## Migration order

1. Compile and boot ARM64 diagnostic recovery while retaining the Jarvis2 kernel,
   DTB and normal-boot fragments. Minui's framebuffer/DRM paths do not depend on
   Android's proprietary EGL stack; actual display behavior still needs testing.
2. Inventory the C5 reference's 64-bit GPU/EGL/mapper implementation and compare
   its userspace/kernel driver interfaces with Jarvis2. Verify provenance and
   redistribution rights before bundling any binaries.
3. Build a 64-bit Android userspace, preserving a 32-bit compatibility runtime
   where needed. Binderized 32-bit HAL processes may remain usable; libraries
   loaded into a 64-bit process need compatible 64-bit implementations.
4. Validate graphics/composition first, then media, audio and DRM independently.
   Working software rendering or a boot animation is not accelerated-TV validation.
5. Audit VINTF, vendor API compatibility, SELinux, AVB and shared-userdata upgrade/
   rollback behavior before an installation trial. This work does not authorize
   a wipe, slot switch, bootloader replacement or slot B write.

## Current compile evidence

The recovery UI produced an ELF64/AArch64 relocatable object using LineageOS 24
headers. A copied Android 14 compiler/Bionic header set was used locally to avoid
competing with the main build. The object is not linked and is not a recovery
image; the complete Android 17 build and hardware checks remain outstanding.
