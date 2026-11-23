# Building offline

This repository is an integration layer for a LineageOS 21 Android checkout,
not the full Android tree. Never run these instructions against a source tree
whose uncommitted changes you have not preserved. Use a dedicated checkout.
No build script here performs ADB, fastboot, a flash, a slot switch or a wipe.

## Host tests

Python 3, Git and JDK 11+ are required:

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
4. Apply patches/TvSettings in order and build the candidate TvSettingsTwoPanel.
5. Build the companion/overlay against that APK. Stage the generated overlay at
   overlays/TvControls/prebuilts/Jarvis2TvControlsOverlay.apk (ignored by Git).
6. Inherit device/onn/jarvis2/tv-controls.mk after the existing device
   configuration. Apps/overlays are already inside the device project and
   visible to Soong. No full product integration/build has been certified yet;
   follow the release ledger.
7. The preinstalled overlay is static and scoped to ro.lineage.device=jarvis2;
   fresh-image behavior still needs verification. It does not require an owner-
   specific cmd overlay enable command in the released product.
8. Before public binaries: build from a clean/pinned source state; assemble
   complete matching AVB chains using private release keys; check actual slot
   capacities and metadata; record corresponding sources/license obligations;
   test fresh boot, recovery entry and rollback using an authorized test plan.

Do not use the older experimental image set as an installer for this source
snapshot. It predates newer Settings, widget, voice and launcher changes.
