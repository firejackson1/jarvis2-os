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

## Verify source patches without modifying the Android tree

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
its pinned upstream hash, and rejects known ADB trust filenames. The JSON report
states this limited scope explicitly. It does not prove package behavior, native
patch contents, a complete privacy audit, release signatures or the AVB chain.
Run it after each image change; a staging-tree check cannot replace extraction.

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
