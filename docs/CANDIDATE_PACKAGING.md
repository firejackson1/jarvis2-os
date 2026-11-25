<!-- SPDX-License-Identifier: Apache-2.0 -->
# Offline vanilla candidate packaging

`tools/package-candidate.py` makes a deterministic developer-preview ZIP from
five independently reviewed vanilla images and a small explicit metadata set.
It can also carry the project-built LCARS Recovery plug-in and its exact
local image binding.
It never signs, rebuilds, flashes, selects slots, installs or runs payload code.
It has no private-key inputs or Google-containing packaging mode. Python3.11+
with its standard zlib support is required.

The older `1ac457e` candidate is **held — do not install** after a privileged-permission allowlist
bug was found. Its successful historical packaging checks do not make it public
ready. Replacement product source `f38da52` is being rebuilt; authenticate and
review its final images independently before packaging. This document authorizes
no installation, publication or change to a working device.

## Authenticate and stage inputs

Supply a reviewed proof JSON and its SHA256 obtained through a trusted channel.
A hash calculated from an otherwise untrusted proof does not authenticate it.
The proof must have literal `passed:true` and exactly these five `files` records:

```json
{
  "passed": true,
  "files": {
    "product.img": {"bytes": 541949952, "sha256": "<64 lowercase hex>"},
    "system.img": {"bytes": 483131392, "sha256": "<64 lowercase hex>"},
    "system_ext.img": {"bytes": 96161792, "sha256": "<64 lowercase hex>"},
    "vbmeta.img": {"bytes": 2097152, "sha256": "<64 lowercase hex>"},
    "vbmeta_system.img": {"bytes": 2097152, "sha256": "<64 lowercase hex>"}
  }
}
```

The sizes above describe the current layout, not a device measurement. The
packager checks actual sizes/hashes against the supplied proof; it does not
supply those checksums or independently repeat AVB/property/package audits.
Additional proof evidence fields are retained outside the ZIP and not treated as
certifications. Duplicate JSON keys, malformed records and an explicitly declared
Google-containing proof are rejected. The caller must independently establish
vanilla content, source identity, stock compatibility and intended metadata.
`google_payload_included:false` is that caller-audited vanilla prerequisite; it
is not a cryptographic package-content scan performed by this packager.

The image directory must contain exactly those five regular files. Create a
fresh separate metadata directory with only:

```text
LICENSE
README.txt
docs/BUILD.md
docs/KNOWN_ISSUES.md
docs/LAUNCHER_SOURCE_BUILD.md
docs/LICENSING.md
docs/RESTORE_PLAN.md
docs/SLOT_INSTALLATION.md
docs/USERSPACE_NOTICES.md
manifests/avb-stock-15640252-profile.json
manifests/avb-userspace-property-policy.json
manifests/launcher-source-bundle.json
manifests/lineage21-pinned.xml
manifests/userspace-notices.json
```

Use the exact reviewed source revision for these source files. The following
local staging example reads committed Git blobs and writes only to fresh external
staging. Replace all placeholders, including the tool checkout and full40-hex
product-source commit. Packaging tools may come from a later reviewed tools
revision; record that revision separately from the product source.

```sh
python3 - <<'PY'
import importlib.util, subprocess
from pathlib import Path
repo = Path('/path/to/source-repository')
tool = Path('/path/to/tool-checkout/tools/package-candidate.py')
revision = '<full-40-hex-product-source-commit>'
staging = Path('/outside/source/fresh-candidate-metadata')
spec = importlib.util.spec_from_file_location('packager', tool)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
staging.mkdir(mode=0o700)
for name in m.METADATA_NAMES:
    target = staging / name
    target.parent.mkdir(parents=True, exist_ok=True)
    data = m.candidate_readme(revision).encode() if name == 'README.txt' else subprocess.run(
        ['git', '-C', str(repo), 'show', revision + ':' + name],
        check=True, capture_output=True).stdout
    target.write_bytes(data)
PY
```

The README must exactly equal the tool's canonical preview text for the supplied
revision. It is included in the metadata whitelist and checked before any output
is created. The tool rejects unknown/missing input files, unexpected directories,
symlinks including ancestor paths, and metadata files larger than8MiB. No source
correspondence claim is inferred merely from the caller's revision string.

## Include locally assembled LCARS Recovery

For an independently audited LCARS image set, the proof still lists the five
ROM images in `files`. Its `recovery` object also pins the complete
`source_revision` of the Recovery recipe, `plugin_sha256`,
`stock_vendor_boot_sha256` and `vendor_boot_sha256`. The latter is the digest of
the complete 64 MiB file with the AVB hash footer. Independently verify the
selected `vbmeta.img` against that derived file and the other images before
creating the proof. Set `rehearsal_only:true` for a temporary-key rehearsal.

Stage the reviewed plug-in at `recovery/librecovery_ui_ext.so` in the metadata
directory. For the reviewed ARM32 build, pin `notices_sha256` in the same
proof object and place the archive at
`recovery/jarvis2-lcars-arm32-notices.tar.gz`. The packager checks the notice
archive, plug-in and source revision against
[the notice provenance manifest](../manifests/lcars-notice-provenance.json).
Generate the README with
`candidate_readme(revision, reviewed['recovery'], reviewed.get('rehearsal_only', False))`,
where `reviewed` is the parsed authenticated proof. The packager checks the
plug-in's hash and writes the exact Recovery inputs and output hash into the
manifest. Format 3 includes the notice archive. Format 2 covers earlier LCARS
packages that deliver notices separately. The recipient obtains the pinned
stock image separately and reconstructs `vendor_boot` with the source recipe
recorded in the README. The packager verifies members and pins. Parent AVB
verification is a separate step.

## Package and check

Keep output fresh, outside the repository/tool checkout and both input trees:

```sh
python3 tools/package-candidate.py \
  --images /outside/source/reviewed-five-images \
  --metadata /outside/source/fresh-candidate-metadata \
  --proof /outside/source/reviewed-image-proof.json \
  --proof-sha256 <trusted-proof-sha256> \
  --source-revision <full-40-hex-product-source-commit> \
  --output /outside/source/fresh-candidate-package
```

A successful output has the ZIP, its generated `manifest.json`, and a separate
`verification.json` receipt. The base ZIP has 20 entries. LCARS format 2 adds
the plug-in. LCARS format 3 adds the plug-in and the notice archive. The manifest
binds the proof pin and actual member hashes and sizes. Rehearsal archives use
the `offline-rehearsal.zip` suffix and
an explicit label in the README and manifest. Existing outputs are never overwritten.

ZIP entry names are sorted, timestamps fixed at2026-11-24T00:00:00, Unix modes
0644, compression DEFLATE level6 and writes streamed with ZIP64 support. All
members are streamed back and compared with the reviewed inputs, then inputs
and the proof are hashed again. Failed/partial output must not be promoted.
Repeated runs with identical inputs and Python/zlib tooling produce identical
ZIP bytes; the receipt records Python/zlib versions. Different zlib versions may
change compressed bytes, so preserve tool versions for exact archive reproduction.
Host tests verify two independent outputs and reject stale proofs before output.

The packager always leaves hardware readiness, OTA/installability, source
correspondence and release approval unverified/false. A successful receipt is a
packaging check, not a substitute for the independent image audits.

## Separate companion assets

The ROM ZIP does not include the launcher's corresponding source archive,
supplemental readable notice packet or public verification materials. Deliver
those separately with a reviewed release-asset receipt containing filenames,
bytes and SHA256. The launcher whitelist and source index included inside the ROM
ZIP identify their contents; they are not the companion archives themselves.

The following are verified **historical staged companion candidates**, not a
promise of public availability or approval for the replacement build. Revalidate
their correspondence to the final images and deliver them together with any
future developer preview; the ROM archive alone is incomplete delivery.

| Companion file | Bytes | SHA256 |
|---|---:|---|
| `LTvLauncher-2026.11.23-code8117-neutral-corresponding-sources.tar.gz` | 474377768 | `aa26fe3cc3395559730983c7248e3d2d5243847f18e46c730bd9e2e6776b2966` |
| `supplemental-userspace-notices.tar.gz` | 904561 | `d59e01f2ca73a72e7eefeb23fb24a8f4f0fd03f2335b9eb7372f61d2e4d69878` |
| `jarvis2-release-v1-public-signing-materials.zip` | 183211 | `5909b7d5d9d64856d9558682088349a3d78a19a444f6875edefaa2547900f4c8` |

The LCARS notice archive travels inside format 3 packages. Use the separately
reviewed notice companion with earlier format 2 packages. Two private builds
of `jarvis2-lcars-arm32-notices.tar.gz` produced 31,772 bytes
with SHA-256 `5028c4d642211bfe2e153f4854f34757f474107a28a13eab7c59509ef234de30`.
Use the plug-in and member hashes from the
[LCARS notice manifest](../manifests/lcars-notice-provenance.json).

Also record the new ROM ZIP receipt, product-source revision, packaging-tool
revision/hash, trusted image-proof pin, and any refreshed companion hashes.
Public verification keys are not private keys and do not establish hardware trust.
Private local GApps compositions remain separate; never relabel or feed them to
this vanilla packaging route. No Google redistribution permission is inferred.

## Verify the complete download set

Place every release asset, `release-asset-receipt.json` and `SHA256SUMS.txt`
in one fresh directory. Obtain the trusted receipt digest from the reviewed
release record, then run:

```sh
python3 tools/verify-release-assets.py /path/to/downloaded-assets \
  --receipt-sha256 <trusted-release-asset-receipt-sha256>
```

The verifier checks the exact set, sizes, and hashes. The checksum list must
cover each payload and the receipt. The JSON result can be compared with the
hosting service's asset records to catch an incomplete or stale draft upload.
Keep license review, signature trust and device qualification as separate
release checks.
