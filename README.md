# Jarvis2 recovery bring-up for Android 17

Separate experimental source tree for LineageOS 24 recovery on the onn Jarvis2
(S905X5M). This tree has not produced or booted a complete Android 17 recovery.
It does not change the existing ROM project or device partitions.

## Approach

The earlier [Jarvis2 recovery](https://github.com/firejackson1/jarvis2-recovery)
patches the OEM Android 14 recovery binary/ramdisk. Repacking that image alone
would not make it Android 17. This port instead builds new recovery userspace
from LineageOS 24. The target is now ARM64, following the owner's request to
move toward 64-bit Android. The existing recovery was independently confirmed
ARM32; its 64-bit kernel modules do not make its userspace 64-bit.

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

## Architecture and ramdisk checks

`tools/cross-check.py` compiles an AArch64 object by default and rejects the wrong
ELF class/machine. It can also check ARM32 with `--arch arm`. An executed local
check used a copied Android 14 compiler/Bionic header set with the exact LineageOS
24 recovery interfaces. That checks source/target ABI compilation, not linking
against a complete Android 17 platform. The generated report records this limit.

```sh
python3 tools/cross-check.py --clang /private/clang/bin/clang-18 \
  --cxx-headers /private/clang/include/c++/v1 \
  --bionic /private/bionic/libc --arch arm64 \
  --headers-origin 'Describe the actual compiler/platform inputs' \
  --output out/fresh-arm64-check
```

`tools/audit-ramdisk.py` reads raw/gzip newc archives without extracting paths or
executing programs. Supply separate archives in the kernel's overlay order;
decode LZ4 archives with a trusted host tool first. It checks native entrypoints,
identifies kernel versus userspace ELF architectures, flags private keys/owner
ADB trust files and records policy/init-script inventory. It rejects unsafe paths,
duplicates, truncation and symlink loops. Runtime dependency linking, SELinux
correctness and startup-write behavior remain separate verification tasks.

```sh
python3 tools/audit-ramdisk.py --cpio /private/platform.cpio \
  --cpio /private/recovery.cpio --expected-recovery-arch arm64 \
  --output out/fresh-ramdisk-report.json
```

The 64-bit Android migration has additional vendor-library requirements, recorded
in [ARM64 assessment](docs/ARM64.md). A 64-bit recovery does not convert the
installed Android system by itself.

## Android build checkpoint — not yet validated

Use a **separate** LineageOS 24 checkout and the recorded upstream revisions.
Do not replace or resync the working LineageOS 21 checkout. Place this tree at
`device/onn/jarvis2_recovery`, select the release configuration supported by that
checkout, and build the ramdisk target:

```sh
source build/envsetup.sh
export GOCACHE="$PWD/out/recovery-go-cache"
lunch lineage_jarvis2_recovery trunk_staging userdebug
m out/target/product/jarvis2_recovery/ramdisk-recovery.img
```

The product and dependency graph still require a full Android 17 build test.
No boot/kernel/DTB image is to be installed from this prototype configuration.
The kernel is intentionally not rebuilt here. The minimal recovery fstab omits
userdata and formattable entries; storage, encryption and update operations
will need deliberate integration after the diagnostic build boots.

The pinned checkout passed the actual `lunch` configuration step after selecting
`core_64_bit_only.mk` before `core_minimal.mk` and enabling the vendor_boot
resource rules. The explicit target above still requests only the recovery
ramdisk; enabling those rules does not produce an installable vendor_boot image.
An isolated Go cache also avoided a stale standard-library index in a cache
shared with an older platform build. No global Go setting or older checkout was
changed. Product configuration success is not a completed recovery link.

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

The [RAM startup audit](docs/RAM_STARTUP_AUDIT.md) records the pinned upstream
BCB, logging and userdata-key paths that run without selecting a destructive
menu action. It also records the prototype metadata fstab mismatch and the
remaining early write-guard requirements. It is not a completed RAM boot test.

## License

New source in this tree is Apache-2.0. Upstream headers are downloaded only into
the ignored cache and retain their upstream notices. OEM inputs are not licensed
or redistributed by this project.

## LCARS interface and remote pairing work

The native LCARS renderer and input-selection tests are implemented; see
[LCARS UI](docs/LCARS_UI.md). Actual radio identification and the remaining
recovery-owned Bluetooth service work are recorded in
[Bluetooth investigation](docs/BLUETOOTH_RECOVERY.md). This is experimental
source, not a downloadable recovery image or a claim that pairing works.

The recovery branch's GitHub workflow also runs the synthetic v4 packing test
without a private Android build checkout. It downloads only the three
checksum-pinned Python fixture tools recorded in `fixture-tool-pins.json`.
Those source tools exercise container packing; they do not compile Android,
validate a recovery binary or establish boot safety.
