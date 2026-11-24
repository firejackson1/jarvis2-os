<!-- SPDX-License-Identifier: Apache-2.0 -->
# Offline vanilla image assembly

`tools/assemble-avb-images.py` wraps three caller-verified raw EROFS files in the
AVB policy of an authenticated coherent baseline, then signs its two parent
vbmeta images with explicitly supplied user keys. It does not rebuild filesystems,
copy Google files, install, flash, select slots, alter LP metadata or query devices.

Authenticate the baseline, all unchanged references, new payloads and host tools
independently. A root-key pin checks the operator's expected AVB public-key blob;
it does not authenticate payload intent or establish hardware acceptance. The
caller must verify the new filesystem contents, APK/APEX signatures, metadata,
provenance and compatibility before assembly. These checks are not inferred from
EROFS structure or a successful AVB signature.

## Inputs and supported layout

Supply exact-size baseline `system.img`, `system_ext.img`, `product.img`,
`vbmeta.img` and `vbmeta_system.img`, plus every unchanged image referenced by its
AVB graph. All paths must be regular files without symlink ancestry; hardlinked
or otherwise aliased input identities are rejected. Baseline leaves need valid
raw EROFS geometry and unsigned AVB footers. New inputs must be raw single-device
4KiB EROFS files whose lengths exactly equal their filesystem block geometry.
Sparse images, existing AVB footers, trailing bytes and unsupported features are
rejected. Native `fsck.erofs` checks each new payload.

The supported baseline binds product from root vbmeta and system/system_ext from
its root-bound vbmeta_system child. Parents use SHA256_RSA2048 or SHA256_RSA4096;
verification-disable flags and public-key metadata are unsupported. Leaves use
SHA256/SHA512, 4KiB data/hash blocks and dm-verity version1. Duplicate or ambiguous
changed-image descriptor roles fail closed. Other references are kept unchanged.

Exact partition budgets come from baseline file lengths. Assembly preserves leaf
salts, hash algorithms, FEC policy, properties, rollback indices, parent algorithms,
flags, rollback locations, release strings and unchanged descriptors/chain keys.
Only the three userspace hashtrees and the intended vbmeta_system public key are
replaced. The root key defaults to preservation; `--allow-root-key-change` permits
an explicit new output-root pin but does not enroll it in hardware.

Use the matching Android host `fsck.erofs`, `avbtool`, OpenSSL runtime and pinned
AVB Python source in this layout:

```text
external/avb/avbtool.py
out/host/linux-x86/bin/fsck.erofs
out/host/linux-x86/bin/avbtool
```

Preserve FEC/runtime dependencies if required by the baseline. Authenticate host
binaries as well as source; hashes are recorded in the result. The reviewed AVB
source pin is in `manifests/avb-test-tool.json`. Keep the composer and its companion
profile, audit, package-verifier and signing-metadata helpers beside this tool.
They are reused without changing composer behavior or running Google assembly.
Python bytecode writes are disabled while importing the AVB source.

## Run

Use explicit user-owned RSA keys outside the repository and output. The tool
never generates, searches for or copies private keys. Supply noninteractive key
access through an operator-managed private workspace; do not expose passphrases
in commands or logs. Never supply project private keys.

```sh
python3 tools/assemble-avb-images.py \
  --base-images /inputs/authenticated-baseline \
  --payloads /inputs/verified-raw-erofs \
  --references /inputs/unchanged-references \
  --tool-tree /tools/android-layout \
  --avbtool-source-sha256 <trusted-avbtool-python-sha256> \
  --root-key /private/user-keys/root.pem \
  --system-key /private/user-keys/vbmeta_system.pem \
  --baseline-root-sha256 <trusted-baseline-avb-public-blob-sha256> \
  --output-root-sha256 <intended-output-avb-public-blob-sha256> \
  --output /work/fresh-assembled-images
```

Root pins are SHA256 of **AVB-format public-key blobs**, not PEM/SPKI/certificate
fingerprints. The payload directory contains exactly the three named inputs used
by this layout; unrelated files are not consumed. Output must be fresh and outside
the repository/tool bundle and every input directory.

Review `assembly.json`, both full AVB audit reports and tool logs. A successful
result contains five exact-size files in `images/`. The baseline audit precedes
private-key use and signing. Every raw payload prefix is hashed before/after the
footer append; all baseline, unchanged reference and new payload input hashes are
rechecked after the final audit. Failed/partial outputs are not release artifacts.

## Evidence and limits

A bounded native rehearsal used freshly built tiny vanilla EROFS payloads,
a synthetic coherent baseline and synthetic references, with disposable fixture
keys only. Two complete runs passed baseline/final audits and produced identical
five-image hashes. No real firmware, Google payload or project key was involved.
Run native work under 1GiB physical memory, 3GiB swap and one CPU limits.

Repeat on the authenticated final release inputs before packaging. Successful
offline assembly does not prove hardware root acceptance, rollback compatibility,
OTA/recovery trust, complete target-files, slot allocation, boot, migration,
interruption handling or restore. Those report claims remain false/unverified.
