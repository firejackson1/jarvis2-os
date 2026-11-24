<!-- SPDX-License-Identifier: Apache-2.0 -->
# Offline vanilla image assembly

`tools/assemble-avb-images.py` wraps three caller-verified raw EROFS files in the
AVB policy of an authenticated coherent baseline or stock templates, then signs its two parent
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
The three userspace hashtrees and intended vbmeta_system public key are
replaced; an explicit property policy also updates exactly nine userspace properties. The root key defaults to preservation; `--allow-root-key-change` permits
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
result contains five exact-size files in `images/`. The baseline audit, or stock-template signature/reference verification described
below, precedes private-key use and signing. Every raw payload prefix is hashed before/after the
footer append; all baseline, unchanged reference and new payload input hashes are
rechecked after the final audit. Failed/partial outputs are not release artifacts.

## Public stock-template mode

This mode requires **no private owner capture and no old stock system, system_ext
or product files**. Supply the original stock root and child templates as
`vbmeta.img` and `vbmeta_system.img` in a separate input directory, all eleven
stock reference images, and the three new raw EROFS payloads. Use:

```sh
python3 tools/assemble-avb-images.py \
  --stock-templates /inputs/stock-vbmeta-templates \
  --stock-profile manifests/avb-stock-15640252-profile.json \
  --stock-profile-sha256 <trusted-stock-profile-sha256> \
  --userspace-policy manifests/avb-userspace-property-policy.json \
  --userspace-policy-sha256 <trusted-property-policy-sha256> \
  --payloads /inputs/verified-raw-erofs \
  --references /inputs/stock-15640252-images \
  --tool-tree /tools/android-layout \
  --avbtool-source-sha256 <trusted-avbtool-python-sha256> \
  --root-key /private/user-keys/root.pem \
  --system-key /private/user-keys/vbmeta_system.pem \
  --baseline-root-sha256 <trusted-stock-avb-public-blob-sha256> \
  --output-root-sha256 <intended-output-avb-public-blob-sha256> \
  --allow-root-key-change \
  --output /work/fresh-stock-compatible-images
```

The reviewed stock profile contains metadata only: exact template and eleven
reference hashes/sizes, output budgets, explicit unbound references and a fresh
leaf release string. Stock template files have a signed vbmeta block followed by
zero padding to 2MiB; independently obtained stock inputs must match the complete
profile pins. No firmware or signed template bytes are shipped in this repository.
The templates originate from stock build15640252, not the private custom recovery.
The profile's stock root public-key-blob SHA256 is
`17361044c25d76ae666a73c8e0249833d447c913980388fa667f21d037b72ec7`.
A separately reviewed layout/profile is needed for different inputs or budgets.

The stock profile outputs system483131392, system_ext96161792,
product541949952 and two2097152-byte vbmeta images. These are explicit supported
layout budgets, not a measurement or allocation of the caller's device.

Stock-template verification checks both signatures, the root pin, child key
bindings, and unchanged reference descriptors before any signing. Every one of
the eleven reference files must match its complete-file pin. Exactly ten are
AVB-covered; `odm_ext` is explicitly pinned but absent from the original signed
graph. The verifier neither invents a binding nor describes those bytes as
AVB-authenticated. Any unexpected unused, missing or misdeclared reference fails.

Only the three replaced hashtrees are skipped during input-template checking.
`replaced_baseline_leaf_bytes_verified:false` records this deliberately limited
proof. New leaf footer policy is explicit: algorithm NONE, flags0, rollback0,
location0 and the profile's reviewed release string. Hash algorithms, salts,
geometry and FEC policy come from the signed stock parent descriptors; no old
leaf header/bytes are assumed. Parent security headers, rollback and chain
locations, stock bootstrap properties and unchanged descriptor/key bytes remain
unchanged. The final full AVB auditor checks the complete newly assembled graph.

## Dynamic userspace properties

Stock mode requires the pinned `avb-userspace-property-policy.json`. Coherent
baseline mode accepts the same `--userspace-policy` and SHA256 arguments; without
them its original property-preservation behavior is unchanged. Use the explicit
policy whenever a new payload changes build identity or security patch.

The assembler extracts each supplied raw payload with native fsck.erofs into a
private temporary directory and reads only its canonical build.prop:
`system/system/build.prop`, `system_ext/etc/build.prop` and
`product/etc/build.prop` relative to the respective image roots. Fingerprints and
releases come from `ro.<partition>.build.fingerprint` and
`ro.<partition>.build.version.release`. All three AVB security-patch values
explicitly come from **system** `ro.build.version.security_patch`; no absent
partition-specific value is invented. Dates and fingerprints are never hardcoded.
Malformed/duplicate properties, missing sources, symlink paths and unexpected
policy schema fail closed.

Exactly fingerprint, os_version and security_patch are applied to all three new
leaf footers and their owning root/child descriptors. Missing allowed properties
are added; duplicate/misplaced allowed keys fail. Every other property and
bootstrap descriptor is preserved. The report records the nine selected values
and policy pin. This checks build-property coherence, not the broader correctness
of applications, filesystem metadata, security patch contents or declared dates.

## Evidence and limits

A bounded native rehearsal used freshly built tiny vanilla EROFS payloads,
a synthetic coherent baseline and synthetic references, with disposable fixture
keys only. Two complete runs passed baseline/final audits and produced identical
five-image hashes. A separate stock-template rehearsal exercises the dynamic
nine-property policy and coherent-baseline policy mode, while an actual stock
template/reference verification is read-only. No real firmware signing, Google
payload or project key is involved in these proofs.
Run native work under 1GiB physical memory, 3GiB swap and one CPU limits.

Repeat on the authenticated final release inputs before packaging. Successful
offline assembly does not prove hardware root acceptance, rollback compatibility,
OTA/recovery trust, complete target-files, slot allocation, boot, migration,
interruption handling or restore. Those report claims remain false/unverified.
