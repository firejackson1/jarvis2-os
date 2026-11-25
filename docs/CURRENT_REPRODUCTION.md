# Reproduce the current Jarvis2 developer preview

Use device source `cb9334ee26ccd80d9f5e5d9276905440b93eaeba` for the
`jarvis2.cb9334ee26cc` build. The signing, image assembly, and packaging tools
used for the candidate are pinned separately at
`00d6300ed7a42d7153b6ca85e74b7766154fc8d0`. The
[candidate receipt](../manifests/current-cb9334-inclusion.json) records the
archive, image, and Recovery digests. These instructions cover offline builds.

## Source and inputs

1. Populate a dedicated Android checkout using the device commit's
   `manifests/lineage21-pinned.xml`. Its SHA-256 is
   `5260701a7c1d99f297bad23371118b9bac2f03bcabc82d5d3f9d80bebc4a44f7`.
   Place the device repository at `device/onn/jarvis2` and select the full
   device commit above. The current build audit matched all 1,430 upstream
   project revisions and saw only the twelve expected changed source paths
   across the six patched projects.
2. [Download and extract the exact stock OTA](STOCK_FOUNDATION.md). Stage its
   eleven local stock images against `stock-inputs.sha256`. With an
   EROFS-capable `fsck.erofs` on `PATH`, run
   `python3 device/onn/jarvis2/stage-stock.py /path/to/stock-images "$PWD"`
   from the Android root. The command verifies the input hashes, extracts the
   kernel from `boot.img`, and stages stock inputs in the fresh tree. Keep the
   matching [stock AVB templates](AVB_IMAGE_ASSEMBLY.md#public-stock-template-mode)
   for image assembly.
3. Stage the exact controlled launcher and custom boot animation. The existing
   [input staging commands](FROZEN_F38_REPRODUCTION.md#required-local-inputs)
   apply to the same pins and helpers. The launcher APK SHA-256 starts with
   `ac585d5a` and the animation SHA-256 starts with `87e2aa9c`. See the full
   hashes in the candidate receipt. Omitting the custom animation uses the
   upstream default and changes the image. The chosen animation remains a
   private input pending redistribution review.
   For a separate preview without the branded artwork, use the
   [original neutral animation](BOOT_ANIMATION.md#original-neutral-animation)
   and verify the resulting product image and AVB chain against its own receipt.

From the Android root, apply the six series to fresh projects. The current
device commit includes the SetupWizard and Music patches in-tree.

```bash
set -e
device="$PWD/device/onn/jarvis2"
test "$(git -C "$device" rev-parse HEAD)" = cb9334ee26ccd80d9f5e5d9276905440b93eaeba
while read -r series project; do
  patches="$device/patches/$series"
  while IFS= read -r patch; do
    git -C "$project" apply "$patches/$patch"
  done < "$patches/series"
done <<'JARVIS2_PATCH_PROJECTS'
Adb packages/modules/adb
Bluetooth packages/modules/Bluetooth
Music packages/apps/Music
ReleaseTools build/make
SetupWizard packages/apps/SetupWizard
TvSettings packages/apps/TvSettings
JARVIS2_PATCH_PROJECTS
python3 "$device/tools/verify-release-patches.py" "$PWD" > /outside/tree/patch-coverage.json
```

## Build, sign, and package

Use Bash from the Android root. The recorded native build used an incremental
output overlay and two jobs. Choose concurrency for the host's available memory.

```bash
export BUILD_NUMBER=jarvis2.cb9334ee26cc
export BUILD_DATETIME=1795575971 SOURCE_DATE_EPOCH=1795575971
export BUILD_USERNAME=jarvis2 BUILD_HOSTNAME=builder LINEAGE_BUILDTYPE=UNOFFICIAL
source build/envsetup.sh
lunch lineage_jarvis2-ap2a-userdebug
m -j2 sign_target_files_apks target-files-package
```

Read the actual `out/target/product/jarvis2/obj/PACKAGING/target_files_intermediates/lineage_jarvis2-target_files.zip`.
Check its embedded source identity and archive integrity. The original verifier
looked for a versioned name and reported a failure after a successful native
build. The recorded archive uses the fixed name above.

Follow [release signing](RELEASE_SIGNING.md) for package and OTA trust,
[AVB image assembly](AVB_IMAGE_ASSEMBLY.md) for the final chain, and
[candidate packaging](CANDIDATE_PACKAGING.md) for the verified artifact set.
Use the matching [ARM32 LCARS source and recipe](https://github.com/firejackson1/jarvis2-os/blob/708e088ed57eb83805753d9213717965a3c61e2c/docs/STOCK_LCARS.md).
Recipient-signed builds require their own keys and trust checks. The observed
build and source audit establish this candidate's input identity. A second
clean full-ROM rebuild and hardware qualification are still open.
