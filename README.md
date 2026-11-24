# Jarvis2 recovery bring-up for Android 17

Separate experimental source tree for LineageOS 24 recovery on the onn Jarvis2
(S905X5M). This tree has not produced or booted a complete Android 17 recovery.
It does not change the existing ROM project or device partitions.

## Approach

The earlier [Jarvis2 recovery](https://github.com/firejackson1/jarvis2-recovery)
patches the OEM Android 14 recovery binary/ramdisk. Repacking that image alone
would not make it Android 17. This port instead builds new recovery userspace
from LineageOS 24, initially using ARM32 to match the existing recovery stack.

Keep the working stock kernel, DTB, bootconfig and all normal-boot vendor ramdisk
fragments. Replace only the named recovery fragment of header-v4 vendor_boot,
then verify the resulting AVB chain separately before considering a device test.
There is no standalone recovery partition on this device.

No signing key, owner ADB identity, OEM image or firmware is stored in Git.
Upstream recovery ADB and SELinux policies remain in effect; the Android 14
permissive policy patch is not blindly copied forward.

## What is implemented

- Recovery-only device configuration, intended at `device/onn/jarvis2_recovery`.
- LineageOS 24 recovery UI module: tap the physical power button to advance;
  hold it to select. A hidden menu is revealed first. Other keys delegate to
  upstream handling. Translated key events preserve each individual selection.
- Diagnostic-first menu, with wipe/update entries removed during bring-up and
  the normal data-wipe hook rejecting a wipe. This is not a security boundary:
  root ADB or fastboot can independently perform writes.
- Offline vendor_boot repacking with AOSP tools. It validates a unique recovery
  fragment, preserves recognized header fields and protected payloads, refuses
  existing output directories, verifies unchanged inputs and reserves AVB space.

The repacker produces an **unsigned** image, not a ready-to-install recovery.
It cannot establish the Android version or validity of a supplied ramdisk.
Its JSON report explicitly leaves signing and boot testing unverified.

## Host verification

```sh
python3 tools/test-host.py --fetch-headers
```

The UI syntax test uses checksum-verified headers from the exact recovery commit
in `upstream-pins.json`. Host-only Bionic attribute definitions are supplied;
the recovery class interfaces are not mocked. Button behavior is executed as a
native host test. Python tests cover fragment selection and duplicate/type errors.

To also execute synthetic v4 image round-trip tests using built AOSP tools:

```sh
JARVIS_ANDROID_TREE=/path/to/android python3 tools/test-host.py
```

Those fixtures test packaging only. A fixture ramdisk is not bootable.

## Android build checkpoint — not yet validated

Use a **separate** LineageOS 24 checkout and the recorded upstream revisions.
Do not replace or resync the working LineageOS 21 checkout. Place this tree at
`device/onn/jarvis2_recovery`, select the release configuration supported by that
checkout, and build the ramdisk target:

```sh
source build/envsetup.sh
lunch lineage_jarvis2_recovery-<release-config>-userdebug
m out/target/product/jarvis2_recovery/ramdisk-recovery.img
```

The product and dependency graph still require a full Android 17 build test.
No boot/kernel/DTB image is to be installed from this prototype configuration.
The kernel is intentionally not rebuilt here. The minimal recovery fstab omits
userdata and formattable entries; storage, encryption and update operations
will need deliberate integration after the diagnostic build boots.

## Offline packaging

```sh
python3 tools/repack.py --android-tree /path/to/android \
  --stock-vendor-boot /private/vendor_boot.img \
  --recovery-ramdisk /private/ramdisk-recovery.img \
  --output /private/fresh-output
```

The output includes a report and private unpacked inputs. Keep it outside public
artifacts: OEM bootconfig/ramdisks can contain device-specific information.
The tool has no ADB, fastboot, block-device write or slot-switch operation.

## Remaining gates

- [ ] Full Android 17 compilation and link, including init/adbd and ramdisk policy.
- [ ] Inspect the actual ramdisk for dependencies, file contexts and credentials.
- [ ] Integrate stock hardware input/display requirements; RGBX and DRM are provisional.
- [ ] Audit startup side effects before a RAM test: ordinary recovery can write
      bootloader messages, logs or metadata even without a menu action.
- [ ] Establish an explicitly authorized RAM launch and restore test plan.
- [ ] Verify TV output, physical button controls, USB ADB and reboot to Android.
- [ ] Integrate mounts, encryption and sideload only after diagnostic operation.
- [ ] Sign and verify the complete vendor_boot AVB chain before any installation.

No installation or slot B modification is authorized by these build instructions.

## License

New source in this tree is Apache-2.0. Upstream headers are downloaded only into
the ignored cache and retain their upstream notices. OEM inputs are not licensed
or redistributed by this project.
