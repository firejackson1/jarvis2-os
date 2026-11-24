# First complete ARM64 recovery ramdisk

The full platform target completed successfully. This is a compiled diagnostic
fragment, not a boot-tested, signed or installable vendor_boot image. No device
partition was changed by this build or its inspection.

## Frozen inputs

- Device source: `9c77952c1e547bbc1bcdc33f370420df1f470cfb`.
- Device archive SHA256: `30d0c0afddc9f87d85646c87f90b896c021b1f053d61eb33286bbd99d26bc39c`.
- Public 1,240-project manifest SHA256: `115070912ccef056511bf6f783514399e9e13b6f9154a278ca8a0b87db571ae8`.
- Recovery revision: `1cdebe4061372e9abb5dc738002ad6c707f7c534`.
- Recovery header patches from `902329becd609f039f6c95fbd722fd1c906d49ad`:
  `<algorithm>` in `PublicVolume.cpp` and `<vector>` in `VolumeManager.h`.
- The README's protobuf, Skia, Highway and XMP patches were also applied.

The public manifest retains the frozen project revisions and copy/link rules;
only its fetch URL and unused remote metadata were normalized for public use.
After applying the patches in a separate checkout, the successful build used:

```sh
export GOCACHE="$PWD/out/go-cache-v4"
export SOONG_INCREMENTAL_ANALYSIS=false PYTHONDONTWRITEBYTECODE=1
export BUILD_NUMBER=jarvis2recovery.9c77952
export BUILD_DATETIME=1795527218 SOURCE_DATE_EPOCH=1795527218
export BUILD_USERNAME=jarvis2 BUILD_HOSTNAME=builder
export LINEAGE_BUILDTYPE=UNOFFICIAL
source build/envsetup.sh
lunch lineage_jarvis2_recovery trunk_staging userdebug
m -j8 -k0 out/target/product/jarvis2_recovery/ramdisk-recovery.img
```

All compiler and product checks remained enabled. `-k0` collects independent
failures; it does not make a failing build pass. The exact failed compilations
passed after their header fixes, followed by the full target. This was a resumed
build. A subsequent independent empty-output build completed successfully.

The independent rebuild used the same frozen sources, build
number and epoch. A private mount namespace binds an empty output directory at
the original `out` path, including a new Go cache, so original outputs remain
intact and path names do not change. A fresh audit matched all 1,240 project
revisions with exactly the five expected patched projects. Both resulting LZ4
ramdisks were independently hashed and match the 14,718,863-byte SHA256 below.
The original output was retained. This establishes byte identity for these two
builds, not runtime compatibility or reproducibility on arbitrary hosts.

## Output and inspection

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| LZ4 ramdisk | 14,718,863 | `55604c2612018e1f84062ee1022d36b4a9b3122a4ea0b2a04e9ccd7827c86286` |
| Decoded newc archive | 32,401,152 | `de1c94c471ce1c8ec87ebdcf166e52444d8f6aa260ca18a18ccc776cf027bc4e` |

The archive has 417 entries and 88 AArch64 ELF files. Init, recovery and adbd are
ELF64/AArch64. The custom UI is in `system/lib64/librecovery_ui_ext.so`, rather
than the main executable. It exports `make_device` and contains both Jarvis2
device/UI vtables, matching the pinned recovery loader's factory contract.
Runtime loading and display behavior remain unqualified: the first complete
RAM candidate was accepted by Fastboot but remained at the boot logo without
ADB or a visible menu. See the [hardware attempt](RAM_BOOT_CONTAINER.md#first-hardware-attempt).

An offline inventory found candidate files for every listed `DT_NEEDED` library
and interpreter in usual recovery search locations. This does not prove linker
namespace/version behavior or execution. The policy and file-context files
exist; their runtime correctness remains unverified.

## Holds before installation

- The strict audit flags `adb_keys`, an unresolved symlink to
  `/product/etc/security/adb_keys`, not an embedded key blob. Its trust-path
  behavior needs deliberate treatment; the finding is not waived.
- The generated fstab still has the prototype read-only ext4 metadata entry.
  The initial RAM test must not mount Android storage.
- Review the complete init/import graph, controlled recovery arguments and
  authentication behavior.
- Assemble the separately tested PID 1 guard and bind its runtime/kernel/module
  hashes and complete physical partition inventory to the private RAM image.
- Bluetooth pairing is not implemented. Evdev handling is not a radio backend.
- AVB integration and successful RAM recovery operation remain unverified.
  Android returned after discarding the failed RAM attempt by power-cycle;
  the recovery's own reboot action has not been tested. No binary release is
  authorized here.

A separate [diagnostic derivation](DIAGNOSTIC_FRAGMENT.md) now removes the
reviewed unresolved trust placeholder, replaces the metadata fstab entry with a
RAM-only entry, and controls the init import and Recovery arguments. It passed
the strict archive audit with untouched records byte-identical. The original
build above remains unchanged. The derived fragment still needs the guard and
hardware overlay; those were subsequently assembled for the first RAM attempt.

The separate [guarded CPIO assembly](GUARDED_RAMDISK.md) now supplies that overlay
privately, including verified ordered storage/hardware module inputs and the
historical complete partition-number manifest. A header-only review initially
held packaging because the ramdisk exceeded the prior declared address spacing.
The subsequent
[placement review and actual legacy-v2 packaging](RAM_BOOT_CONTAINER.md) found
vendor-source relocation and produced a private candidate retaining the proven
reference fields. This corrects the header-only inference; exact stock behavior
and a successful device boot remain unverified.

Keep the original artifact and private audit receipts. This fragment is not a
replacement for the working installed recovery.
