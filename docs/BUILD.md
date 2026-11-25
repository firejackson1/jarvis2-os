# Building offline

This repository is an integration layer for a LineageOS 21 Android checkout,
not the full Android tree. Never run these instructions against a source tree
whose uncommitted changes you have not preserved. Use a dedicated checkout.
No build script here performs ADB, fastboot, a flash, a slot switch or a wipe.

## Host tests

Python 3, Git, a C++17 compiler and JDK 11+ are required:

```sh
./tools/test-host.sh
```

Pure Java suites exercise wear/resume ownership, AACP parsing, button gestures,
audio-delay calculations, HDMI capability interpretation and server URI validation.
Python tests check release policy and the source privacy scanner. These tests do
not certify physical hardware, receiver passthrough, suspend or recovery behavior.

## Compile the TV controls app and Settings overlay

Prerequisites: a built LineageOS 21 tree with SDK34 public android.jar, its Java17
prebuilt, R8/D8, aapt2, signapk and native signapk dependencies. Supply the
**matching candidate TvSettings APK**; resource identifiers must match the
Settings build being packaged. Supply a private signing directory containing
platform.x509.pem and platform.pk8. Test keys are acceptable for private compile
verification only, never as production signing provenance.

```sh
./tools/build-apps.sh /path/to/android /path/to/TvSettingsTwoPanel.apk \
  /private/path/to/platform-signing /outside/source/new-build-output
```

The output must be a fresh directory. Both APK signatures are verified. The JSON
build manifest records source commit/dirty state, target Settings hash and APK
hashes. No private key is copied into the output or repository. This standalone
APK path uses the supplied keys; full Android builds instead apply the product's
platform signing configuration. They must agree for system privileges to work.

## Product integration

1. Populate a separate LineageOS 21 tree and its exact pinned manifest.
2. Clone this repository at device/onn/jarvis2 in that checkout. The root
   AndroidProducts.mk and BoardConfig.mk are then in the expected AOSP location.
3. Provide verified stock inputs locally using stage-stock.py; no stock firmware
   is distributed here. See stock-inputs.sha256. Distribution of any resulting
   stock kernel/vendor binaries requires an independently verified license route.
4. Apply `patches/TvSettings/series`, `patches/Bluetooth/series` and
   `patches/Adb/series` in their listed order to their pinned projects, then
   build `TvSettingsTwoPanel`, `com.android.btservices` and `com.android.adbd`.
   Also apply `patches/SetupWizard/series` to pinned `packages/apps/SetupWizard`
   and build `LineageSetupWizard`; see patches/SetupWizard/README.md.
   For new builds, apply `patches/Music/series` to pinned `packages/apps/Music`
   and rebuild `Music`; its service cleanup patch is not in the frozen f38
   images. See patches/Music/README.md for the remaining live checks.
   The ADB patch is required with the product negative-port default: unpatched
   adbd can otherwise fall back to network listening when USB is absent. See
   patches/Adb/README.md for scope and the mandatory launcher Updater exclusion.
   Release signing additionally requires `patches/ReleaseTools/series` on the
   pinned `build/make` project; rebuild `sign_target_files_apks` afterward.
5. Prepare the pinned LTvLauncher inputs as documented in LAUNCHERS.md.
6. lineage_jarvis2.mk inherits tv-controls.mk. Soong builds the Settings overlay
   directly from source with `TvSettingsTwoPanel` as its resource dependency;
   no staged overlay APK is required. The standalone APK command above remains
   useful for separate compile checks. When migrating an existing output tree
   from the old prebuilt module, run `m installclean` before rebuilding images
   to remove its old system_ext/app installation. The native overlay installs
   under system_ext/overlay; image inspection rejects duplicate packages.
7. The preinstalled overlay is static and scoped to ro.lineage.device=jarvis2;
   fresh-image behavior still needs verification. It does not require an owner-
   specific cmd overlay enable command in the released product.
8. Before public binaries: build from a clean/pinned source state; assemble
   complete matching AVB chains using private release keys; check actual slot
   capacities and metadata; record corresponding sources/license obligations;
   test fresh boot, recovery entry and rollback using an authorized test plan.

Do not use the older experimental image set as an installer for this source
snapshot. It predates newer Settings, widget, voice and launcher changes.

To reproduce the frozen `f38da52` source state, use
[its separate recipe](FROZEN_F38_REPRODUCTION.md). The newer SetupWizard source
supplement must stay outside that candidate's device checkout so its original
commit and build identity remain intact.

## Pin release build identity

Run from the Android source root after staging all reviewed inputs. Use the
exact device-source revision and its commit time, rather than an automatically
generated engineering username/time build number:

```sh
release_revision=$(git -C device/onn/jarvis2 rev-parse HEAD)
export BUILD_NUMBER="jarvis2.${release_revision:0:12}"
export BUILD_DATETIME=$(git -C device/onn/jarvis2 show -s --format=%ct "$release_revision")
export SOURCE_DATE_EPOCH="$BUILD_DATETIME"
export BUILD_USERNAME=jarvis2 BUILD_HOSTNAME=builder LINEAGE_BUILDTYPE=UNOFFICIAL
source build/envsetup.sh
lunch lineage_jarvis2-ap2a-userdebug
m -j4 sign_target_files_apks target-files-package
```

The pinned Soong frontend reads BUILD_NUMBER and BUILD_DATETIME explicitly.
Record these values, tool revisions and exact staged input hashes with the
artifact. Stable identity removes known host/time variability; it does not alone
prove byte-identical whole-ROM output. Inspect the resulting build.prop files,
and derive AVB userspace properties from those exact final payloads rather than
retaining stock or earlier-development fingerprints. Keep firmware properties
and security rollback counters separate from the new userspace build identity.

## Verify source patches without modifying the Android tree

Before the release build, verify that every tracked patch has been applied to
the pinned build checkout:

```sh
python3 tools/verify-release-patches.py /path/to/android
```

The check replays the six series in temporary directories and compares the
resulting files with the working tree. A nonzero exit means a patch result is
missing, differs, or cannot be verified. Run this as the Android build-tree
owner. The check covers source files. Verify the rebuilt images separately.

```sh
python3 tools/verify-patches.py /path/to/built/android /outside/source/new-patch-check
```

This checks the pinned TvSettings revision, obtains original files through Git,
applies the patch series to copies, and compiles the changed Java classes using
the matching existing Android build classpath. It is not a full APK/product build.
The Bluetooth patch is separately compiled/executed by host tests across 24
channel combinations; actual native-stack integration still requires a build.

## Inspect the generated images themselves

After image generation has completed, use the matching host `fsck.erofs` to
extract the three EROFS files into a fresh output directory outside the inputs:

```sh
python3 tools/inspect-image-contents.py /path/to/product-output \
  /outside/source/new-image-inspection /path/to/host/bin/fsck.erofs
```

This checks EROFS file decoding, hashes inputs before/after extraction, checks
required/forbidden package filenames, verifies that the launcher payload matches
its pinned controlled-build hash, and rejects known ADB trust filenames. The JSON report
states this limited scope explicitly. It does not prove package behavior, native
patch contents, a complete privacy audit, release signatures or the AVB chain.
Run it after each image change; a staging-tree check cannot replace extraction.

For release evidence, pass the independently authenticated signed target-files
archive and its trusted digest as well:

```sh
python3 tools/inspect-image-contents.py /path/to/final-images \
  /outside/source/new-release-inspection /path/to/host/bin/fsck.erofs \
  --signed-target-files /path/to/signed-target-files.zip \
  --signed-target-files-sha256 <trusted-signed-archive-sha256>
```

The report records the archive hash and the complete EROFS byte range and digest
for each image. `system`, `system_ext` and `product` must match their archive
members byte for byte within that range, including filesystem metadata. AVB
footers can differ, and the final chain and APK/APEX signatures still need
their independent audits. Keep this receipt with the release patch and
signing reports.

## Audit a complete AVB image set

All referenced image files must be present in one directory, named by the
unsuffixed AVB partition names. Use the pinned Android checkout's avbtool:

```sh
python3 tools/audit-avb-chain.py /outside/source/complete-image-set \
  /path/to/android /outside/source/new-avb-audit
```

The audit verifies every signed chain node and its leaf descriptors with upstream
avbtool, and separately compares each child embedded public key to its parent's
chain key. Unsigned chain nodes are rejected. It records flags/rollback indices
without altering them. An optional `--root-public-key-sha256` can compare the
AVB public-key blob against an independently established hash; without it the
result is internal consistency only. Even a matching operator pin does not prove
the physical bootloader accepts that key. No private key is needed or copied.

Run real signed-image regression fixtures on a built Android host with OpenSSL:

```sh
JARVIS2_ANDROID_SOURCE=/path/to/android python3 -m unittest discover -s tests -p test_avb_chain.py -v
```

These tests generate temporary RSA keys outside the repository and check a valid
chain, corrupted signature, valid-but-wrong child signer, unsigned root and wrong
root pin. They are explicitly skipped on hosts without the required build tools;
the ordinary host test suite does not silently stand in for them.

GitHub CI prepares a small fixture-tool layout from the exact pinned standalone
avbtool.py source and runs these signed-image cases as part of host checks. The
source SHA-256 is checked before execution; OpenSSL supplies fixture key generation.
This fixture layout is not a full Android build or evidence of ROM bootability.

## Custom Recovery source

The stock-compatible ARM32 LCARS prototype builds from a separate source
checkout pinned at `1409c21924d1040024c9521749248e05d7f78315`. Its offline recipe
uses the local LineageOS 21 tools, pinned AOSP Android 14 headers and the
original stock `vendor_boot`. It reproduced the prototype image and keeps the
stock Recovery and Fastbootd services. Signing and hardware qualification
remain separate. [Stock-compatible LCARS recipe](https://github.com/firejackson1/jarvis2-os/blob/1409c21924d1040024c9521749248e05d7f78315/docs/STOCK_LCARS.md)

Recipients can also rebuild the exact expected Recovery image from the
included LCARS plug-in and their local stock image. This route uses Python,
`lz4` and four checksum-pinned scripts. The local image hash and matching
parent `vbmeta` remain part of the release verification.
[Portable LCARS recipe](https://github.com/firejackson1/jarvis2-os/blob/708e088ed57eb83805753d9213717965a3c61e2c/docs/STOCK_LCARS.md#recreate-the-recovery-image-from-a-plug-in)

The ARM64 LCARS recovery port is source-only on
[`recovery17-lcars`](https://github.com/firejackson1/jarvis2-os/tree/recovery17-lcars),
with the earlier ARM64 source checkpoint at `650217efee5a79b05d923758993fd004d0489334`.
Its root is a separate recovery device tree intended for
`device/onn/jarvis2_recovery` in a separate LineageOS 24 / Android 17 checkout.
It is not the LineageOS 21 ROM device tree or a ready-to-flash image. Keep the
frozen ROM checkout intact when obtaining it. Follow that source's README and
upstream pins; a full link, ramdisk audit, AVB integration, Bluetooth backend,
RAM boot and restoration tests remain release gates.

The corrected f38 stock-recovery engineering trial does not satisfy the owner's
requirement for a public package containing this custom recovery. Do not publish
that trial as the final release or reuse its hardware results as proof for a
future recovery image.
