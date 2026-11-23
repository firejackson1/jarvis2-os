# Restore evidence and remaining tests

Updated 2026-11-23. No installer or flash command is authorized by this document.
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
