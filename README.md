# Jarvis2 recovery bring-up for Android 17

Separate experimental source tree for LineageOS 24 recovery on the onn Jarvis2
(S905X5M). The first full ARM64 recovery ramdisk now builds. It has not booted
or been installed. This work does not change device partitions.

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

The inspector retains newc inode/device/link metadata and original entry data,
resolves regular-file hard links in either payload order and tracks shared-file
updates across archive layers. Credential scanning includes every original
payload, even if later entries replace it. Required native entrypoints must be
executable regular files. Keep the original CPIO byte streams for packaging;
the effective-file report is not an archive serializer or a full kernel
filesystem emulator.

Hard-link behavior follows the kernel's
[initramfs format](https://www.kernel.org/doc/Documentation/early-userspace/buffer-format.txt)
and the Linux 5.15
[unpacker](https://github.com/torvalds/linux/blob/v5.15/init/initramfs.c).
Synthetic tests cover link identity, payload placement, metadata updates,
ordinary-file overlays and replacing a single alias with a new link or symlink.

```sh
python3 tools/audit-ramdisk.py --cpio /private/platform.cpio \
  --cpio /private/recovery.cpio --expected-recovery-arch arm64 \
  --output out/fresh-ramdisk-report.json
```

The 64-bit Android migration has additional vendor-library requirements, recorded
in [ARM64 assessment](docs/ARM64.md). A 64-bit recovery does not convert the
installed Android system by itself.

## Android build checkpoint — linked, not boot-tested

Use a **separate** LineageOS 24 checkout and the recorded upstream revisions.
Do not replace or resync the working LineageOS 21 checkout. Place this tree at
`device/onn/jarvis2_recovery`, select the release configuration supported by that
checkout, and build the ramdisk target:

`platform-manifest.xml` freezes all 1,240 platform project revisions from the
audited checkout. It can be selected with `repo init -m platform-manifest.xml`
when this recovery source repository and an exact source revision are used as
the manifest repository. Its GitHub fetch URL is absolute and the unused private
remote was removed; project revisions, paths and link/copy rules are unchanged.
The device tree itself is supplied separately at the path above. Do not use a
moving `lineage-24.0` branch as a substitute for this manifest when reproducing
the build.

```sh
git -C prebuilts/misc apply \
  "$PWD/device/onn/jarvis2_recovery/patches/prebuilts-misc-protobuf-namespace.patch"
git -C external/skia apply \
  "$PWD/device/onn/jarvis2_recovery/patches/skia-skcms-vendor.patch"
git -C external/google-highway apply \
  "$PWD/device/onn/jarvis2_recovery/patches/highway-vendor.patch"
git -C external/XMP-Toolkit-SDK apply \
  "$PWD/device/onn/jarvis2_recovery/patches/xmp-vendor.patch"
git -C bootable/recovery apply \
  "$PWD/device/onn/jarvis2_recovery/patches/recovery-publicvolume-algorithm.patch"
git -C bootable/recovery apply \
  "$PWD/device/onn/jarvis2_recovery/patches/recovery-volumemanager-vector.patch"
source build/envsetup.sh
export GOCACHE="$PWD/out/recovery-go-cache"
lunch lineage_jarvis2_recovery trunk_staging userdebug
m out/target/product/jarvis2_recovery/ramdisk-recovery.img
```

The pinned product now passes full Soong analysis, Make rule generation and the
complete requested ramdisk build. See the
[build checkpoint](docs/BUILD_CHECKPOINT.md) for exact source/artifact hashes,
actual ELF inspection and the remaining authentication/startup holds.
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

Apply the patch once after a clean sync. The frozen AOSP `prebuilts/misc`
revision `be7c3a630b5dc5eb3260035d77a81b2f322754f8` and Lineage compat revision
`0dec3d5ab188c36125930cdaa9a57a225f298fea` both define the protobuf 21.12 vendor
compatibility modules. The patch gives only the legacy ARM32 AOSP package its
own Soong namespace; it preserves both definitions and their license records.
The ARM64-capable Lineage definitions remain in the global namespace. No binary
is replaced, and the legacy namespace is not exported to this recovery product.

The pinned Lineage `libjxl` exposes a vendor variant, but AOSP's `libskia_skcms`
and `libhwy` dependencies do not. Their patches add those variants;
Skia's generator is updated with its generated build file. They do not disable
JPEG XL or remove its dependency checks. The base revisions are Skia
`508606366e71a3daa933a4e08bc49b84e387ec18` and Google Highway
`94b90ab8cb9df9b3719a64751ea2fcb62caa3391`.
Lineage's DNG SDK also needs vendor variants of `xmp_toolkit_sdk` and its private
`zuid_md5` dependency. `xmp-vendor.patch` adds both against XMP revision
`45acb237cd13c19708f963247c732250cd43a4a5`. The remaining direct dependencies
in this image-library chain already declare vendor availability.

The recovery product also includes `lineage_sdk_common.mk`, as Lineage's own
common product does. The inherited media product places `org.lineageos.platform`
on the system-server classpath; omitting its matching packages causes the Make
dexpreopt consistency check to fail before the requested ramdisk can compile.
The check remains enabled. These product dependencies do not mean that a full
normal-boot Android system is included in the recovery ramdisk.

The pinned recovery's `volume_manager/PublicVolume.cpp` uses `std::replace`
without its `<algorithm>` header. `recovery-publicvolume-algorithm.patch` adds
that include against recovery revision `1cdebe4061372e9abb5dc738002ad6c707f7c534`.
The actual ARM64 recovery compile of that source now passes, followed by the
full ramdisk target. Image packaging and startup verification gates still apply.

`recovery-volumemanager-vector.patch` likewise makes `VolumeManager.h` include
the `<vector>` type used in its public declarations. The new libc++ headers
do not supply these standard-library declarations indirectly. Both patches
retain the original interfaces and compiler diagnostics.

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

- [x] Full Android 17 compilation and link, including init/adbd and generated policy.
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

`ramboot/init` is a diagnostic PID 1 prelude, intended for
`rdinit=/ramboot-init` in a separately assembled RAM image. It refuses ordinary
host execution, checks the RAM root, creates private RAM state, mounts only
read-only proc/sys views and checks the board and exact kernel release before
loading any module. It verifies every hash and name in the reviewed 27-module
sequence before the first load. The storage library checks internal MMC, its
boot devices and partitions, requires read-only readback and rejects a changing
inventory. Discovery is bounded; any failed gate prevents Android-init handoff.
The temporary proc/sys mounts must be removed before `/init` starts.

`/ramboot/mmc.partitions` must contain the complete physical partition inventory
captured read-only from the matching device/GPT: one canonical positive decimal
partition number per line, with no blanks, comments or duplicates. The guard
requires exactly that set before attempting protection. A partial list of backed-up
partitions is insufficient; do not infer missing entries. Bind this file to the
private image/preflight receipt. Whole-device read-only status alone is not used
as proof that a partition appearing later is protected.

This prelude is assembled in a private CPIO and legacy-v2 boot container, but
has no successful hardware qualification. Its BusyBox/musl closure, kernel-release input and hashed
stock modules are supplied privately and bound to that recovery ramdisk.
Unsupported force-normal-boot or
hibernation arguments stop the prelude. Failures leave it waiting with RAM logs
and a UART/kernel-log stage marker; there is no automatic reboot or persistent
BCB change. The storage poll is bounded; kernel module loading itself has no
userspace timeout. The first complete RAM launch stayed at the boot logo without
ADB; its startup stage is unknown. Do not
source its function libraries on a host with real privileged utilities.

`tools/prepare_ramdisk.py` derives the diagnostic fragment from a checksum-bound
native ARM64 newc archive. It changes only the reviewed init import, explicit
Recovery arguments and RAM-only fstab, and removes the unresolved standard
ADB-key placeholder symlink. All other records, including binaries, policy,
properties and hard-link metadata, remain byte-identical. It does not waive the
credential audit or change adbd authentication settings. See the
[diagnostic preparation record](docs/DIAGNOSTIC_FRAGMENT.md) for the exact
changes, executed artifact checks and remaining assembly requirements.

```sh
python3 tools/prepare_ramdisk.py --cpio /private/recovery.cpio \
  --expected-input-sha256 EXACT_INPUT_SHA256 \
  --output /private/fresh-diagnostic-output
```

The resulting fragment still requires the early guard, its private verified
inputs and the owned hardware init profile. `tools/assemble_ramdisk.py` now
assembles that overlay offline; the [guarded ramdisk record](docs/GUARDED_RAMDISK.md)
documents inputs, artifact hashes and verification. The separate
[RAM boot-container checkpoint](docs/RAM_BOOT_CONTAINER.md) records the executed
legacy-v2 packaging and the corrected placement analysis. Neither CPIO alone is
a launchable boot image; the private complete candidate has not reached Recovery.

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
