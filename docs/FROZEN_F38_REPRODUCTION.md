# Frozen f38da52 source reproduction

The candidate's device source is
`f38da52af274a0e50c92a10cf279e62f44125358`. Later tools and documentation commits
do not describe a rebuild of its images. The development manifest's `main`
revision is for ongoing work; select the exact frozen commit for this recipe.
Use a fresh, dedicated Android checkout. These instructions describe source
assembly and offline compilation, not installation or hardware acceptance.

## Exact source closure

Populate the 1,430 projects from the frozen commit's
`manifests/lineage21-pinned.xml`. Clone the device repository at
`device/onn/jarvis2` and check out the full commit above. All 1,430 project HEADs
in the audited build workspace matched this manifest. Its five modified projects
are represented as follows:

| Project | Patch source |
|---|---|
| `packages/apps/TvSettings` | Frozen `patches/TvSettings/series` |
| `packages/modules/Bluetooth` | Frozen `patches/Bluetooth/series` |
| `packages/modules/adb` | Frozen `patches/Adb/series`, including its two new helper files |
| `build/make` | Frozen `patches/ReleaseTools/series` |
| `packages/apps/SetupWizard` | External source supplement's `patches/SetupWizard/series` |

The SetupWizard project HEAD is
`e58f07efee4ba3d69d6b4922d5bbf4707da6e033`. Its sole change adds the
`BLUETOOTH_CONNECT` manifest permission. The supplement records an existing build
input that was missing from the frozen device repository; it introduces no new
image behavior. The ten files in the other four projects reconstructed exactly
from their frozen public patches. The SetupWizard patch must likewise reconstruct
the existing manifest, including its unchanged upstream content.

The source supplement is this repository at commit
`225a2828d025ea9967d27ed2d0ee6455d555d395`. Obtain it through a separate checkout
of that exact commit, or a source-supplement archive with a published verified
checksum. Keep it outside the frozen Android device checkout; use only its
listed supplementary patch rather than advancing the product source. Apply each
series to its project in listed order, for example from the Android source root:

```sh
# Set this to the separately verified supplement directory outside this tree.
source_supplement=/path/to/verified/source-supplement
while IFS= read -r patch; do
  git -C packages/apps/SetupWizard apply \
    "$source_supplement/patches/SetupWizard/$patch"
done < "$source_supplement/patches/SetupWizard/series"
```

Do not advance or modify the frozen device checkout to obtain that patch. A new
source-supplement commit is not the product-source commit. Reconstructing these
already-used sources does not require rebuilding the existing candidate images.

## Required local inputs

The following assets are planned for a **private draft** release. They are not
promised as publicly downloadable yet. Hardware release gates and publication
authorization remain separate. Obtain verified local files; no private host path
or private record outside the supplied source bundle is part of this recipe.

| Expected asset | Bytes | SHA256 |
|---|---:|---|
| `LTvLauncher-2026.11.23-code8117-neutral-armeabi-v7a.apk` | 10024443 | `ac585d5a0bb3c13c2ea346d052d1fa5140a6bb35bbe90a20002f776f92c03347` |
| `jarvis2-bootanimation-87e2aa9.zip` | 13482326 | `87e2aa9ceda3fc1fdbf787dad06687eedc12efeca6a0046d3a76a68f6d03ad50` |
| `LTvLauncher-2026.11.23-code8117-neutral-corresponding-sources.tar.gz` | 474377768 | `aa26fe3cc3395559730983c7248e3d2d5243847f18e46c730bd9e2e6776b2966` |

The corresponding-source bundle supplies sanitized build records and metadata,
dependency sources, notices and recipes; private caches or private build records
are not required. Consult `docs/LAUNCHER_SOURCE_BUILD.md` and
`manifests/launcher-source-bundle.json` in the verified source delivery. Building
and signing a different launcher requires an explicitly reviewed hash/certificate
pin change; possession of source cannot reproduce the project's private signature.

Supply the eleven stock images locally, verify every entry in frozen
`stock-inputs.sha256`, and run `stage-stock.py` as documented in BUILD.md. Stock
firmware and Google APKs are not supplied or mirrored by these companion assets.
The staged kernel must match the kernel extracted from the pinned `boot.img`.

Copy the standalone launcher asset to a local input directory as
`LTvLauncher.apk`, retaining its verified bytes. Supply the pinned
`LTvLauncher-source.tar.gz` from the documented upstream source URL or a verified
local copy; the helper verifies both input hashes. Then run, with explicit local
file paths and without downloading a substitute APK:

The frozen helper expects `out/host/linux-x86/bin/zipalign` before launcher
staging, while the missing launcher prebuilt can prevent an initial Soong build.
Bootstrap only that tool from the pinned, checked-in SDK layout. Keep the SDK's
`lib64` directory intact for its `libc++.so` dependency. From the Android source
root, run this subshell before starting Soong:

```sh
(
  set -eu
  bootstrap_zipalign="$PWD/out/host/linux-x86/bin/zipalign"
  sdk_zipalign="$PWD/prebuilts/sdk/tools/linux/bin/zipalign"
  test -x "$sdk_zipalign"
  # Refuse to replace any existing tool or dangling symlink.
  test ! -e "$bootstrap_zipalign" && test ! -L "$bootstrap_zipalign"
  mkdir -p "$(dirname "$bootstrap_zipalign")"
  ln -s "$sdk_zipalign" "$bootstrap_zipalign"
  trap 'rm -f -- "$bootstrap_zipalign"' EXIT
  trap 'exit 1' HUP INT TERM
  python3 device/onn/jarvis2/tools/prepare-launcher.py /path/to/local/launcher-inputs "$PWD"
)
python3 device/onn/jarvis2/tools/prepare-boot-animation.py /path/to/local/jarvis2-bootanimation-87e2aa9.zip
```

The subshell removes the bootstrap link on success or failure. Do not run a
build while it exists: Ninja must never write through it into the checked-in
SDK. If the shell is forcibly killed, inspect and remove that exact temporary
link before building. An existing real host tool needs no bootstrap link;
verify its provenance and invoke the launcher helper directly instead.

The frozen helpers were exercised in a fresh sparse Android workspace containing
only links to the pinned SDK/JDK prebuilts and this temporary zipalign link.
The resulting APK, three native libraries, license and expanded notices matched
the frozen staged inputs byte-for-byte; the animation helper reproduced the
exact pinned archive too. This preparation check used no existing host output
or private build cache. It does not establish a clean full-ROM rebuild.

The later [selected feature receipt](../manifests/frozen-f38-feature-evidence.json)
binds 15 extracted payloads back to the exact signed target-files archive and
the final delivery filesystem prefixes. It records package versions, selected
source/bytecode observations and the remaining controls/Music update gaps.
It is not a new build, complete image privacy/AVB audit or hardware qualification.

The launcher helper extracts all three native libraries and notices from that
exact APK. The optional animation must be explicitly staged: omitting it selects
the upstream default and does not reproduce this candidate's artwork.

## Preserve the original build identity

From the Android source root, use the original values rather than the supplement
or current tools commit time:

```sh
test "$(git -C device/onn/jarvis2 rev-parse HEAD)" = f38da52af274a0e50c92a10cf279e62f44125358
export BUILD_NUMBER=jarvis2.f38da52af274
export BUILD_DATETIME=1795517392 SOURCE_DATE_EPOCH=1795517392
export BUILD_USERNAME=jarvis2 BUILD_HOSTNAME=builder LINEAGE_BUILDTYPE=UNOFFICIAL
source build/envsetup.sh
lunch lineage_jarvis2-ap2a-userdebug
m -j4 sign_target_files_apks target-files-package
```

The source supplement closes the source-state discrepancy; it does not prove a
byte-identical whole-ROM rebuild. Original release signatures require the original
private signing keys, which are never distributed. Recipients can use their own
keys with the documented signing process. Image extraction, package/signature
verification and complete AVB checks remain necessary for any newly built output;
none establishes hardware boot, recovery, rollback or installation safety.
