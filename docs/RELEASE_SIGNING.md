# Unofficial release signing

Production signing is an offline packaging step. It does not establish that the
bootloader trusts a key, that a slot is bootable, or that existing user data can
be retained. No signing command is an installation instruction.

## Key policy

Use independent project-controlled keys for platform/shared/media/network/module
APKs, APEX containers, APEX payloads and image AVB. Keep third-party PRESIGNED
packages unchanged where the pinned input calls for that. Do not substitute
public Android development keys or copy the owner's personal device trust.

Back up the complete key set with authenticated encryption and keep the unlock
secret separately. Verify restoration and every archived file before using the
keys. Record public certificate/key fingerprints, input hashes and signing-tool
revisions with the candidate. Private keys, unlock secrets and backup archives
must never enter Git, release assets, logs or bug reports.

The first private release key set has a verified encrypted backup, but has not
signed a release or been tested for hardware acceptance. Key backup verification
alone does not complete the release-signing checklist.

## Input and output checks

1. Start with target-files from the exact intended source and product outputs.
   A prior target-files archive is not updated by rebuilding a separate APK.
2. Inventory actual shipped APKs and APEX payloads. Deduplicate identical signing
   metadata; reject conflicting identities, missing metadata and ambiguous keys.
   Preserve package bytes when preparing metadata. This is preparation, not
   signature verification.
3. Sign every selected APK, APEX container and APEX payload with its designated
   key. Preserve explicitly allowed third-party signatures. Verify the effective
   Android 14 signer and each APEX payload key independently afterward.
4. Rebuild filesystems from the signed packages and inspect extracted images,
   including ownership/modes, privilege allowlists, defaults and notices. Compare
   their exact lengths with the live target layout without modifying it.
5. Assemble and audit the complete AVB chain, including parent-child key bindings,
   flags and rollback indices. Record the root public-key hash separately.
6. Create final checksums only after packaging is complete. Hardware trust, fresh
   boot, recovery and interrupted-install restoration remain separate gates.

A successful target-files signing run is not a configured OTA. The existing
captured archive lacks META/ab_partitions.txt and is not an A/B OTA installer.
See [SLOT_INSTALLATION.md](SLOT_INSTALLATION.md) for current installation limits.

## Existing-data migration

A build signed with unrelated release keys is not a supported dirty upgrade from
our development-key build. User data is shared between slots. Switching slots
cannot isolate package databases, settings or APEX module data.

APK signing lineage may support some migrations, but retaining old development
key capabilities can also retain unwanted trust. APEX payload trust is separate
from APK/container signatures. Updated packages in userdata may shadow factory
packages. No automatic migration or wipe is authorized by this document.

Until a coherent migration is independently qualified, label the production-key
preview as requiring fresh data and preserved-data upgrades as unsupported. A
fresh-data hardware test still requires a separately authorized device/data
plan; do not use the owner's current installation as disposable test data.

Primary references:

- https://source.android.com/docs/core/ota/sign_builds
- https://source.android.com/docs/security/features/apksigning/v3
- https://developer.android.com/tools/apksigner
- https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android14-release/services/core/java/com/android/server/pm/PackageManagerServiceUtils.java
- https://android.googlesource.com/platform/system/apex/+/refs/heads/android14-release/apexd/apex_file_repository.cpp

## Prepare shipped-package metadata

```sh
python3 tools/prepare-signing-metadata.py \
  --input /outside/source/original-target-files.zip \
  --output /outside/source/new-prepared-target-files.zip \
  --deapexer /path/to/android/out/host/linux-x86/bin/deapexer \
  --debugfs /path/to/android/out/host/linux-x86/bin/debugfs_static \
  --fsckerofs /path/to/android/out/host/linux-x86/bin/fsck.erofs
```

This creates a separate ZIP and refuses to overwrite an output. It discovers
embedded APKs through the pinned native APEX inspection tools and filters
META/apkcerts.txt and META/apexkeys.txt. It also supplies an absent
avb_avbtool=avbtool in META/misc_info.txt: the pinned APEX signer requires the
tool lookup even when image AVB is configured separately. It preserves valid
existing values, rejects malformed/duplicate misc keys and reports the exact
metadata entries changed. This does not enable AVB or alter verification flags.
It does not sign, read private keys,
validate package signatures, rebuild images, or contact a device. An unchanged
ZIP entry means its uncompressed content is identical; ZIP compression bytes
can differ. The output is private preparation material, not a public ROM ZIP.

Integration against the preserved earlier target-files archive found 104
standalone APKs, 23 embedded APKs and 31 APEX packages. All 6,138 nonmetadata
entries matched their original content hashes. The pinned signing tool accepted
127 APK metadata identities and 31 APEX metadata entries, including the preserved
launcher and CTS shim. Repeat this check against every new target-files build;
these counts do not inventory a future build automatically.

## Independently verify packages and APEX filesystems

Use the original trusted build archive, its signed output, matching pinned host
executables and a **public-only** key export. That export contains inventory.json,
public certificates, public PEMs and AVB public-key blobs, never private keys.
The inventory hash must come from your independently trusted release/build
record. A key-inventory pin does not authenticate the original archive or role
policy: establish those inputs separately.

```sh
python3 tools/verify-signed-packages.py \
  --original /outside/source/original-target-files.zip \
  --signed /outside/source/signed-target-files.zip \
  --public-materials /outside/source/public-key-export \
  --role-map manifests/signing-role-map.json \
  --trusted-public-inventory-sha256 TRUSTED_INVENTORY_SHA256 \
  --host /path/to/android/out/host/linux-x86 \
  --soong-host /path/to/android/out/soong/host/linux-x86 \
  --jdk /path/to/android/prebuilts/jdk/jdk17/linux-x86 \
  --report-dir /outside/source/new-package-report
```

It checks intended API-34 APK certificates, APEX container/payload signatures,
embedded payload keys and content hashes/hashtrees, preserved packages and
non-signature APK entry contents, including licenses and services metadata.
Only reserved top-level JAR signing files are excluded from that comparison.
The supplied JDK takes precedence over an inherited JAVA_HOME.

After verifying and preserving that report, compute its SHA-256 and use it as
PACKAGE_REPORT_SHA256 below. Do not treat an untrusted downloaded report's own
hash as independent trust.

```sh
python3 tools/verify-apex-filesystems.py \
  --original /outside/source/original-target-files.zip \
  --signed /outside/source/signed-target-files.zip \
  --package-proof /outside/source/new-package-report/report.json \
  --trusted-package-proof-sha256 PACKAGE_REPORT_SHA256 \
  --debugfs /path/to/android/out/host/linux-x86/bin/debugfs_static \
  --report-dir /outside/source/new-filesystem-report
```

This compares paths, ordinary file contents, symlink targets, modes, UID/GID and
raw extended attributes from the ext4 payload images, without following symlinks.
Only embedded APK changes already covered by the package proof are allowed.
Timestamps, inode flags/layout and hardlink topology remain outside the proof.
Both tools label unpinned inputs as internal consistency only, and neither proves
hardware acceptance, raw-image AVB, installation or restoration. They implement
the current bounded Jarvis2 artifact layout, not a universal untrusted-image API.

The supported rehearsal profile explicitly records the five prebuilt vendor/ODM/
module reference images dropped by the pinned signing tool; unexpected archive
changes fail. Its output is not a complete target-files/OTA artifact. Preserve
unchanged reference inputs for subsequent complete-chain/image validation.

Both promoted commands were executed against the private rehearsal under 1 GiB
RAM, 3 GiB swap and one CPU. The package command also passed with an invalid
inherited JAVA_HOME. No private key or device operation was required.
