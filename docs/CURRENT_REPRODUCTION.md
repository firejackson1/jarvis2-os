# Build the neutral Jarvis2 developer preview

Use device source `cb9334ee26ccd80d9f5e5d9276905440b93eaeba` for the
`jarvis2.cb9334ee26cc` build. The signing, image assembly, and packaging tools
used for the candidate are pinned separately at
`00d6300ed7a42d7153b6ca85e74b7766154fc8d0`. The
[neutral r2 receipt](../manifests/current-neutral-artwork.json) records the
release-candidate archive, image, and Recovery digests. These instructions
prepare source and build inputs for a neutral build with locally supplied keys.
The exact staged ZIP can be reproduced separately from the already signed
images and [pinned packaging inputs](CANDIDATE_PACKAGING.md#reproduce-the-staged-neutral-r2-zip).

## Source and inputs

Initialize Repo in a new Android source directory. This uses the manifest from
the exact product revision and Repo v2.73. Put Git LFS on `PATH` before
syncing. Git LFS 3.6.1 was tested. Repo's skip-smudge checkout still calls
the Git LFS executable, and the ARM WebView prebuilt needs a separate pull.

```bash
set -euo pipefail
repository=https://github.com/firejackson1/jarvis2-os.git
revision=cb9334ee26ccd80d9f5e5d9276905440b93eaeba
git lfs version
repo init -u "$repository" -b "$revision" -m manifests/lineage21-pinned.xml \
  --repo-url https://gerrit.googlesource.com/git-repo --repo-rev v2.73 --no-clone-bundle
test "$(git -C .repo/manifests rev-parse HEAD)" = "$revision"
printf '%s  %s\n' \
  5260701a7c1d99f297bad23371118b9bac2f03bcabc82d5d3f9d80bebc4a44f7 \
  .repo/manifests/manifests/lineage21-pinned.xml | sha256sum -c -
repo sync -c -j4 --no-interleaved --no-manifest-update --no-tags --fail-fast
webview=external/chromium-webview/prebuilt/arm
test "$(git -C "$webview" rev-parse HEAD)" = 1c11dffe87310d3c81e2ad93b9f0a7e8c09adfc0
git -C "$webview" lfs install --local --skip-repo --skip-smudge
git -C "$webview" lfs pull --include=webview.apk --exclude=
test "$(stat -c %s "$webview/webview.apk")" -eq 98528166
printf '%s  %s\n' f7ccf01cf3ec8555fd4500ddc7512430cb2cd3cadd1806a166be2092d25c7298 \
  "$webview/webview.apk" | sha256sum -c -
git clone --no-checkout "$repository" device/onn/jarvis2
git -C device/onn/jarvis2 checkout --detach "$revision"
```

The [builder preflight](../manifests/neutral-r2-builder-preflight.json) verifies
the public initialization and all 1,430 listed paths. The rehearsal synced
Lineage's vendor source and Music against their exact pins. The earlier native
build audit checked all 1,430 project revisions and the twelve patched files.
One clean sync stopped while initializing the ARM WebView worktree when Git
LFS was missing. Adding the executable let the same checkout finish at the
pinned commit. Pulling through the repository-local filter replaced the
133-byte pointer with the APK at the SHA-256 above.

1. [Download and extract the exact stock OTA](STOCK_FOUNDATION.md). With an
   EROFS-capable `fsck.erofs` on `PATH`, stage the extracted images from the
   Android root with
   `python3 device/onn/jarvis2/stage-stock.py /path/to/stock-raw "$PWD"`.
   Keep the padded [stock AVB templates](AVB_IMAGE_ASSEMBLY.md#public-stock-template-mode)
   for image assembly.
2. Put the controlled ARM32 launcher APK in a local directory as
   `LTvLauncher.apk`. Also supply `LTvLauncher-source.tar.gz` from the pinned
   URL in [launcher-inputs.json](../manifests/launcher-inputs.json). Both input
   hashes and the certificate are checked by the helper. The exact signed APK
   is staged in the private release set pending asset publication.
3. Generate the original neutral animation from verified source. The exact
   stage commands for the launcher and animation follow.

```bash
set -euo pipefail
device="$PWD/device/onn/jarvis2"
launcher_inputs=/path/to/local/launcher-inputs
(
  bootstrap="$PWD/out/host/linux-x86/bin/zipalign"
  sdk_zipalign="$PWD/prebuilts/sdk/tools/linux/bin/zipalign"
  test -x "$sdk_zipalign"
  test ! -e "$bootstrap"
  test ! -L "$bootstrap"
  mkdir -p "$(dirname "$bootstrap")"
  ln -s "$sdk_zipalign" "$bootstrap"
  trap 'rm -f -- "$bootstrap"' EXIT
  python3 "$device/tools/prepare-launcher.py" "$launcher_inputs" "$PWD"
)
generator_dir=$(mktemp -d)
git -C "$device" show \
  932294a6f92c3091c7b30d8f76748ffc6dea52e7:tools/prepare-boot-animation.py \
  > "$generator_dir/prepare-boot-animation.py"
mkdir -p "$device/prebuilts"
python3 "$generator_dir/prepare-boot-animation.py" --neutral "$device/prebuilts/bootanimation.zip"
printf '%s  %s\n' ea74502097a5e61134f25e92ac313f2154f80aea4972bae5cec1d4252bb2b375 \
  "$device/prebuilts/bootanimation.zip" | sha256sum -c -
```

The temporary bootstrap link is removed after staging. When a verified native
host `zipalign` already exists, invoke the launcher helper directly. Leave
the SDK's matching `lib64` directory available. The fresh host rehearsal
matched the launcher and generated animation to the r2 product filesystem.

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

Use Bash from the Android root with a fresh output tree. The recorded native
r2 build used an incremental overlay that retained earlier `product` and
`system_ext` build properties. The clean build must generate all three
userspace partitions with the intended identity. Choose concurrency for the
host's available memory.

The eight patches at the revision above reproduce the original r2 build
inputs. The clean baseline uses that exact pin. The successor build is queued
at product revision `148a63dfe989245d725b7a56e660e35faa5c9998`, with build
number `jarvis2.148a63dfe989` and UTC epoch `1795601128`. Its upstream
manifest is identical. It adds the ninth patch, which refreshes all partition
build properties when a numbered build's identity inputs change. The queued
rebuild preserves a verified copy of the baseline archive before it changes
the build number and date, so the real build exercises the incremental fix.
For a fresh build of that revision, substitute those three pins in the checkout,
patch and build commands. [Release build patches](../patches/ReleaseTools/README.md)

```bash
export BUILD_NUMBER=jarvis2.cb9334ee26cc
export BUILD_DATETIME=1795575971 SOURCE_DATE_EPOCH=1795575971
export BUILD_USERNAME=jarvis2 BUILD_HOSTNAME=builder LINEAGE_BUILDTYPE=UNOFFICIAL
export LC_ALL=C TZ=UTC
source build/envsetup.sh
lunch lineage_jarvis2-ap2a-userdebug
m -j2 sign_target_files_apks target-files-package
```

UTC is the clean build convention. The archived r2 properties used HST in
their displayed dates. The [byte-exact archive repack](CANDIDATE_PACKAGING.md#reproduce-the-staged-neutral-r2-zip)
uses the preserved signed images, including their original properties.

Read the actual `out/target/product/jarvis2/obj/PACKAGING/target_files_intermediates/lineage_jarvis2-target_files.zip`.
Check archive integrity and the expected build number, UTC epoch and fingerprint
in `SYSTEM/build.prop`, `SYSTEM_EXT/etc/build.prop` and
`PRODUCT/etc/build.prop`. Use the [image inspector](BUILD.md#inspect-the-generated-images-themselves)
with both expected identity arguments for the generated images and again
after signing. The original verifier looked only at the system identity.
The legacy r2 asset is retained for offline evidence and must be replaced
before release. [Identity receipt](../manifests/neutral-r2-build-identity.json)

Before signing the successor, extract the three `IMAGES/*.img` members from
its verified target-files archive. Read out the actual EROFS filesystems and
compare the three canonical build property files and all 21 tracked feature
files to the archive's `SYSTEM`, `SYSTEM_EXT` and `PRODUCT` entries. The
scheduled check also compares the feature and image digests to the build
receipt. A controlled test passed with matching image and archive files and
rejected a changed landscape declaration in the archive. The old unsigned and signed r2 builds
contain the same six stale identity fields, so the error was present before
signing. [Image readback controls](../manifests/successor-image-readback-controls.json)

Follow [release signing](RELEASE_SIGNING.md) for package and OTA trust,
[AVB image assembly](AVB_IMAGE_ASSEMBLY.md) for the final chain, and
[candidate packaging](CANDIDATE_PACKAGING.md) for the verified artifact set.
Use the matching [ARM32 LCARS source and recipe](https://github.com/firejackson1/jarvis2-os/blob/708e088ed57eb83805753d9213717965a3c61e2c/docs/STOCK_LCARS.md).

The staged r2 package was made by replacing the artwork in the previously
signed product filesystem, rebuilding EROFS, and reassembling the AVB chain.
This guide feeds the same neutral artwork into the build from the start.
Locally signed images need their own AVB, package-signature, filesystem
and hardware trust checks. The preflight verifies the inputs for this
route. A clean full-ROM build from those inputs and its hardware tests
remain open.
