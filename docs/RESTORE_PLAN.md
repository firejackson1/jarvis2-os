# Restore evidence and remaining tests

Updated 2026-11-25. No installer or flash command is authorized by this document.
Do not change slot B, slot selection, userdata, bootloader or environment.

## Verified current development baseline

A read-only capture of the running slot A completed for sixteen partitions:
boot, vendor_boot, init_boot, dtbo, vbmeta, vbmeta_system, oem, odm_ext,
system, system_ext, product, vendor, odm, system_dlkm, vendor_dlkm, odm_dlkm.
Each file matched the block device's size and SHA-256 before and after capture.
The active slot was A at the start and end. No userdata was captured and no
partitions were written. The private raw backups and their hashes are not public
release material, and must not be confused with a stock OTA or a new candidate.

Offline verification of that captured baseline passed all signatures and leaf
hash/hashtree descriptors reachable from vbmeta through boot, oem and
vbmeta_system. Child embedded public keys were separately compared against their
parent chain descriptors. This additional check matters: the pinned avbtool's
`--follow_chain_partitions` path verifies child signatures but does not itself
compare child embedded keys against the parent's key bytes.

These results show the captured development chain is internally consistent.
They do not establish hardware root-of-trust acceptance for a new key, the
correctness of a new candidate, or the ability to restore through a failed boot.
The captured root key is existing development trust, not a production release key.

## Required before an installation request

1. Complete the new images and inspect their extracted contents, metadata and
   size against the intended device's actual slot-A layout.
2. Build and verify an explicit complete candidate AVB chain, including unchanged
   boot/recovery/OEM references and every changed leaf. Preserve relevant rollback
   indices/locations and flags; never disable verification merely to pass a check.
3. List the exact intended slot-A writes and their dependency/commit order. An
   interrupted multi-partition update can leave inconsistent descriptors even
   when every file was individually valid before the write.
4. Verify current recovery entry, USB ADB, bootloader fastboot and fastbootd on the
   exact connected computer/cable. Intermittent detection remains a real limit;
   having backup files alone does not provide a working transport.
5. Preserve recovery/boot and an independent route back to the flashing interface.
   Do not promise that leaving vendor_boot unchanged alone proves recovery remains
   reachable after an AVB failure before recovery starts.
6. Obtain authorization for the concrete candidate installation/hardware test,
   then test clean boot and rollback. Shared userdata means preserving slot-B
   partitions does not by itself prove stock slot B can still use the same data.

The known baseline capture is complete. Candidate verification, interruption
recovery and actual restoration remain open release gates.

Use the [read-only Recovery capture tool](CANDIDATE_INSTALLATION.md#back-up-an-existing-qualified-recovery-session)
to reproduce the seven-image backup in a qualified session. It rechecks the
session and reads the logical extents directly from super, leaving mappings
and partition contents untouched. A fresh device capture and a reachable
restore transport are separate requirements.

## Exact stock-based candidate checkpoint — 2026-11-24

The offline `1ac457e` candidate uses stock `init_boot` and `vendor_boot` references,
not the custom development bootstrap captured on the owner's slot A. Matching
its verified chain on that development device therefore requires seven target
partition changes: `system_a`, `system_ext_a`, `product_a`, `init_boot_a`,
`vendor_boot_a`, `vbmeta_system_a` and `vbmeta_a`. This is a dependency inventory,
not an executable write order or permission to install. The five-image offline
archive deliberately excludes stock firmware; users must obtain the exact pinned
stock foundation separately.

All sixteen saved development restore files have been independently rehashed
again; all seven proposed candidate partition lengths match the saved lengths.
These checks do not establish current device freshness or a working restore
transport. The stock bootstrap would replace slot A's custom recovery. Slot B
has not been established as a complete bootable fallback.

There is no atomic commit across these seven partitions. Writing parent AVB
metadata last reduces one inconsistent intermediate state, but does not make
power loss safe: old metadata can reject newly written leaves, and recovery can
fail before its USB interface is available. A full raw backup cannot fix that
without an independently reachable flashing interface. Do not turn this inventory
into a script until the live transport, snapshot state and interrupted-update
recovery path have been verified.

The package/APEX signing identity also changes from development keys. Existing
userdata compatibility is unproven; any clean-data test needs a separately
approved data plan because both slots share userdata. No wipe, slot switch,
resize, snapshot cancellation or shared metadata modification follows from
successful offline checks.

## LCARS archive and historical rollback fit

The local LCARS preflight produced all seven image inputs from the temporary-key
rehearsal archive and the pinned stock image set. The prepared image sizes and
the planned slot-A extents matched both saved LP views. The seven previous
restore files matched their full recorded physical and logical hashes. That
saved capture had no complete allocated slot-B foundation. A new device trial
still requires a fresh capture, an independently reachable restore transport,
and approval for the actual candidate. [Host preflight](CANDIDATE_INSTALLATION.md#prepare-a-verified-lcars-zip-locally)

The portable preflight can repeat the saved fit check with a pinned native
`lpdump`, the captured super prefix and the original seven restore files. It
records the exact input hashes and fails if any target overlaps the captured
metadata prefix or if the untouched stock foundation differs.
[Saved layout and restore-file check](CANDIDATE_INSTALLATION.md#check-a-saved-layout-and-restore-files)

## Stock rollback input rehearsal

The [Google-hosted full OTA](STOCK_FOUNDATION.md) can reproduce the stock
rollback inputs without a private capture. In addition to the reference files
and normalized templates in that guide, extract `system`, `system_ext`, and
`product` with full payload verification. The seven-image stock set consists
of those three images, `init_boot`, `vendor_boot`, `vbmeta_system`, and
`vbmeta`. Keep all other reference images for the AVB audit.

The exact extracted stock set passed all 13 AVB bindings and fit the seven
target sizes in the historical slot-A capture. The stock `vendor_boot`
contains stock Recovery. To return to a prior custom installation, retain
and verify the backup made from that specific device before writing. A live
capture, a working restore transport, and an authorized physical restore test
are still required.

## Exact neutral candidate rollback rehearsal

The [neutral candidate](../manifests/current-neutral-artwork.json) was tested
with the installer, native `lpdump`, the 4 MiB saved `super` metadata prefix,
and all seven historical restore files. The model used real content for the
target images and the saved logical extents. It supplied simulated physical
geometry, Recovery transport, and private protected partition bytes.

The dry run matched all seven captured targets and issued zero writes. The
model then stopped halfway through a `product_a` write. The actual installer
journal recorded a pending write, and the installer refused rollback while a
writer was still active. After the model reported the writer had stopped, the
installer restored the old files without completing the interrupted install.
A separate complete install and restore also passed full hash readback.

The saved `super` metadata prefix, 16 protected physical files and five
untargeted logical extents matched across the rehearsal. The recorded layout
had no allocated slot-B logical extents. A separate AVB audit reconstructed
all 13 bindings using the seven saved restore files and nine unchanged stock
references. These tests cover file-backed write boundaries and old-image
consistency. Physical recovery entry, USB availability after interruption,
eMMC power loss and an actual restore remain open.

### Interrupted writes on all seven r2 targets

The [r2 matrix receipt](../manifests/neutral-r2-rollback-matrix.json) covers the
exact staged operator installer, the updated r2 ZIP and the same saved slot-A
layout and restore files. After a dry run with zero persistent requests, the
fixture simulated a disconnect at a different target on each run. All three
userspace partitions, `init_boot_a`, `vendor_boot_a`, `vbmeta_system_a`, and
`vbmeta_a` were interrupted once. The chosen prefix in every case produced
a hash distinct from both complete images. The child verified-boot image
needed a 512-byte-aligned cut to create that mixed state.

The writer's journal showed completed earlier targets and a pending write for
the interrupted target. Later targets retained their original hashes. Each
restore attempt refused while a simulated `dd` was active, then restored all
seven original hashes directly after quiescence. All 56 modeled write requests
stayed within the target A ranges. The saved metadata prefix, 16 protected
physical fixtures and five untouched logical extents stayed byte-identical.
Re-entry to Recovery after an actual power loss, live USB availability and
physical restoration remain separate hardware gates.
