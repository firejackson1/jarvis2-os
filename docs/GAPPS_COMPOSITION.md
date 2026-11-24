<!-- SPDX-License-Identifier: Apache-2.0 -->
# Local optional Google composition

`tools/compose-gapps.py` produces a private local five-image candidate from an
exact vanilla-ROM baseline and the user-downloaded ZIP identified by
`manifests/gapps-recipe.json`. It does not run the Google recovery updater or
addon.d, install anything, change a slot, resize partitions, reboot or wipe data.
Ordinary recovery sideload into these EROFS images remains unsupported.

Google payloads are obtained from their upstream provider. Neither this source
repository nor its metadata recipe includes those payloads. Local composition
does not establish permission to redistribute the resulting Google-containing
images. See [GOOGLE_APPS.md](GOOGLE_APPS.md).

## Required inputs

Authenticate the baseline ROM, composition profile, recipe and host tools before
running the composer. Pins are checks against an operator's trusted choices;
computing a hash from an otherwise untrusted download does not authenticate it.

Supply:

- A profile exported by `gapps-profile.py` for the exact vanilla baseline, with
  its filesystem configs, compiled file contexts and authoritative metadata.
- The baseline `system.img`, `system_ext.img`, `product.img`, `vbmeta.img` and
  `vbmeta_system.img`. The three userspace files must already have exact-size
  AVB footers and match the profile hashes.
- Every unchanged image referenced by the baseline AVB graph, using unsuffixed
  names such as `boot.img` and `oem.img`. Obtain applicable firmware independently;
  it is not supplied by this tool.
- The exact upstream ZIP pinned by the reviewed recipe. All 27 payload entries
  are checked; no updater or arbitrary executable from the ZIP is run.
- Explicit user-owned root and vbmeta_system signing keys, outside the source
  repository and output. Never supply or distribute the project's private keys.
- A trusted baseline AVB root-key hash and the intended output root-key hash.
  These are SHA256 hashes of **AVB-format public-key blobs**, not PEM files or
  X.509/SPKI fingerprints.

The existing-root policy is the default. A publisher's public key cannot sign a
modified image. Using a different user-owned root requires
`--allow-root-key-change`, an explicit output-root pin, and independently
established hardware acceptance of that key. The flag does not enroll a key or
prove that the bootloader accepts it. The report always leaves hardware trust
unverified.

The supported baseline uses single-device 4KiB EROFS, three root-bound userspace
hashtrees, unsigned leaf footers covered by signed vbmeta/vbmeta_system, zero
verification-disable flags, and SHA256_RSA2048 or SHA256_RSA4096 parent nodes.
The data/hash blocks must both be 4096 bytes and dm-verity version must be1.
Public-key metadata and unsupported leaf descriptors/layouts are rejected.
Existing salts, hash algorithms, FEC policy, properties, rollback indices and
locations, parent algorithms, release strings and unchanged references are
retained. A metadata profile alone does not supply a complete AVB baseline.

## Host tools

Use Linux, Python3, OpenSSL, the matching Android `mkfs.erofs`, `fsck.erofs`,
`avbtool`, `apksigner` and its runtime files, and JDK17. Supply a tool tree with:

```text
external/avb/avbtool.py
out/host/linux-x86/bin/mkfs.erofs
out/host/linux-x86/bin/fsck.erofs
out/host/linux-x86/bin/avbtool
```

This can be the matching Android checkout or an audited host-tool bundle with
that layout; a full Android rebuild is not performed by composition. Preserve
required host runtime dependencies, including FEC support when the baseline uses
it. Authenticate binaries as well as the AVB Python source; tool hashes are
recorded for inspection. The source pin for the reviewed AVB module is recorded
in `manifests/avb-test-tool.json`.

Keep the companion profile, AVB audit, package verification and signing-metadata
Python tools together in `tools/`. The composer imports those helpers and
suppresses Python bytecode writes while loading the supplied AVB source. It sets
`JAVA_HOME` from `--jdk`; the JVM heap is limited to256MiB. Use an external resource
limit of1GiB physical memory,3GiB swap and one CPU for native rehearsals.

Key files must be usable by the local OpenSSL backend without interactive
password prompts. Unlock protected user keys into a private temporary workspace
before running; do not put passphrases in commands or logs. The tool does not
search for, generate, back up or copy private keys. Its result records public-key
hashes, not private-key bytes or paths.

## Run locally

Replace every placeholder with authenticated inputs. Keep output outside the
repository/tool bundle and all input trees; an existing output is never replaced.

```sh
python3 tools/compose-gapps.py \
  --profile /inputs/rom-profile \
  --profile-sha256 <trusted-profile-json-sha256> \
  --recipe manifests/gapps-recipe.json \
  --recipe-sha256 <reviewed-recipe-sha256> \
  --gapps /inputs/MindTheGapps-14.0.0-arm-ATV-minimal-20240523_192108.zip \
  --base-images /inputs/vanilla-images \
  --references /inputs/unchanged-avb-references \
  --tool-tree /tools/android-layout \
  --avbtool-source-sha256 <reviewed-avbtool-python-sha256> \
  --apksigner /tools/apksigner \
  --jdk /tools/jdk17 \
  --root-key /private/user-keys/root.pem \
  --system-key /private/user-keys/vbmeta_system.pem \
  --baseline-root-sha256 <trusted-baseline-avb-public-blob-sha256> \
  --output-root-sha256 <intended-output-avb-public-blob-sha256> \
  --output /work/fresh-local-composition
```

Review `composition.json` and the audit logs. A successful result contains five
exact-size images under `images/`, hashes, a complete offline AVB audit, unchanged
baseline/reference hashes, and per-partition content/metadata checks. Failed or
partial outputs are not candidates for installation.

The composer extracts one partition at a time, copies only the prescribed Google
files and absent parent directories, and refuses overwrites or symlink traversal.
It applies explicit canned ownership/modes/capabilities and matching SELinux
contexts, retaining the profile's UUID, build epoch and compression settings.
Rebuilt images must preserve every existing path's bytes/link targets and the
checked UID/GID/modes/raw xattrs. New files must match upstream bytes and verify
as Android14 APKs. No blanket META-INF exclusion is used for Google APK bytes.

The complete AVB auditor checks signatures, referenced contents and parent-bound
child public keys before and after composition. Final images preserve baseline
byte budgets; no device capacity or physical identity is queried. Timestamps,
hardlink topology and storage layout are not claimed unchanged merely because
content and the checked metadata match.

## Remaining qualification

Offline success is not an OTA, a hardware test, a migration plan or proof that
another slot is bootable. Installation still needs a compatible allocated
foundation, measured sizes, recovery and interruption/restore qualification, and
hardware acceptance of the selected key. The tool does not enable AVB bypasses.

Fresh-user Google defaults, retained-data permission behavior, Google device
certification and application compatibility require separate tests. No runtime
permission grants or userdata changes are automated. A synthetic AVB/filesystem
rehearsal cannot establish compatibility of the final release baseline.

## Native rehearsal scope

The reviewed composer completed two bounded Linux rehearsals using the pinned
upstream Google ZIP, synthetic EROFS baseline images and synthetic unchanged AVB
references. Only disposable fixture signing keys were used. All 27 Google files
and 16 APK signatures passed verification; existing content, symlink targets,
UID/GID/modes and raw SELinux/capability metadata survived. Both complete offline
AVB audits passed, and all five output image hashes matched between runs.

The native job completed within a 1GiB physical-memory cap, 3GiB swap cap and one
CPU; measured swap peak was 23.2MiB. This exercises the actual native pipeline,
but does not qualify a final release ROM, real firmware, hardware key acceptance,
OTA trust, installation, migration or restore. Repeat against the authenticated
final signed baseline before treating any composed candidate as release-tested.
