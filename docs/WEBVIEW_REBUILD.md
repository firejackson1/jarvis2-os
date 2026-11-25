# Rebuilding the Jarvis2 r2 WebView

Jarvis2 r2 uses the ARM32 LineageOS WebView prebuilt at version 157.0.8103.78
and version code 810307800, with package name `com.android.webview`. The
[preparation receipt](../manifests/webview-r2-rebuild.json) binds the Chromium
source, source patches, icon inputs and final APK readback.

The ARM ELF library is byte-identical to the one in the pinned LineageOS
prebuilt. All 641 non-signature payloads in the r2 APK match that prebuilt.
The prebuilt also includes the Crashpad trampoline, which the ARM APK import
omits by specifying the WebView library as its packaged JNI input.
[ARM prebuilt](https://github.com/LineageOS/android_external_chromium-webview_prebuilt_arm/tree/1c11dffe87310d3c81e2ad93b9f0a7e8c09adfc0) ·
[Android import rule](https://github.com/LineageOS/android_external_chromium-webview_patches/blob/544b12e3d42a02b4337f31819f6ba917187dcccf/os_pickup.mk)

## Source and dependency pins

Use a dedicated Linux x86-64 build workspace. The initial checkout verified
the Chromium tag commit `4b3d0dabb8250b6f152d2d85d79e7706e309d087`, tree
`1390557da6bf6cb630528eac294f338b887ad81a`, and `DEPS` SHA-256
`70f36c59069488921a7d83b5ad0dfb3d221211be2be966f28ed84ef6ceeb8daa`.
Chromium's DEPS pins depot_tools at `96b9c092c0cdaa9f1ec87b0af777ec85977dee91`
and FFmpeg at `5c85ff666b3434d9323b83437f910ad8431ab7c9`.
[Exact Chromium tag](https://chromium.googlesource.com/chromium/src/+/refs/tags/157.0.8103.78) ·
[Android build prerequisites](https://chromium.googlesource.com/chromium/src/+/main/docs/android_build_instructions.md)

~~~sh
set -eu
chromium=4b3d0dabb8250b6f152d2d85d79e7706e309d087
depot=96b9c092c0cdaa9f1ec87b0af777ec85977dee91
git init src
git -C src remote add origin https://chromium.googlesource.com/chromium/src.git
git -C src fetch --depth=1 --no-tags origin "$chromium"
git -C src checkout --detach FETCH_HEAD
test "$(git -C src rev-parse HEAD)" = "$chromium"
printf '%s  %s\n' \
  70f36c59069488921a7d83b5ad0dfb3d221211be2be966f28ed84ef6ceeb8daa \
  src/DEPS | sha256sum -c

git init depot_tools
git -C depot_tools remote add origin https://chromium.googlesource.com/chromium/tools/depot_tools.git
git -C depot_tools fetch --depth=1 --no-tags origin "$depot"
git -C depot_tools checkout --detach FETCH_HEAD
test "$(git -C depot_tools rev-parse HEAD)" = "$depot"
export PATH="$PWD/depot_tools:$PATH" DEPOT_TOOLS_UPDATE=0
cat > .gclient <<'CONFIG'
solutions = [{
    "name": "src",
    "url": "https://chromium.googlesource.com/chromium/src.git",
    "managed": False,
    "custom_deps": {},
    "custom_vars": {"checkout_pgo_profiles": True},
}]
target_os = ["android"]
CONFIG
gclient sync --nohooks --no-history --jobs=3 --revision "src@$chromium"
gclient revinfo -a > deps-revisions.txt
test "$(git -C src/third_party/ffmpeg rev-parse HEAD)" = \
  5c85ff666b3434d9323b83437f910ad8431ab7c9
~~~

Compare `deps-revisions.txt` with the
[304-entry dependency inventory](../manifests/webview-r2-deps.txt) from the
Linux x86-64 Android sync. It records Git revisions, resolved CIPD instances
and storage objects. Differences need review before reusing the build
receipt.

Install the documented host prerequisites in the build environment. The
verified graph used Debian 13 with Chromium's `build/install-build-deps.py
--android --no-prompt --no-syms --no-chromeos-fonts`. Debian provides the Linux
headers as the architecture-independent `linux-libc-dev` package. Verify
that package and the header files if Chromium's quick check reports only
`linux-libc-dev:i386` missing. Check the remaining prerequisites normally.

Run `depot_tools/ensure_bootstrap` to initialize the pinned tool wrappers,
then run `gclient runhooks` at the workspace root. The official build profile
needs the optimization files fetched by the PGO-enabled hooks, including
`src/chrome/android/profiles/afdo.prof`. Compare the downloaded files to the
[profile pins](../manifests/webview-r2-rebuild.json) before starting the build.

## Patch and icon inputs

All 13 patches from LineageOS revision
`544b12e3d42a02b4337f31819f6ba917187dcccf` passed sequential replay on the
exact source. The replay matched 100 present and 47 absent original paths
against Chromium's checked-out Git tree. Apply the series to a separate
rebuild tree after dependency sync. [LineageOS patches and build README](https://github.com/LineageOS/android_external_chromium-webview_patches/tree/544b12e3d42a02b4337f31819f6ba917187dcccf)

Run the following in that source tree with `patch_dir` set to the absolute
path to the verified LineageOS patch input directory.

~~~sh
set -eu
for patch in "$patch_dir"/[0-9]*.patch; do
  git apply --check "$patch"
  git apply "$patch"
done
for density in mdpi hdpi xhdpi xxhdpi xxxhdpi; do
  icon_dir="android_webview/nonembedded/java/res_icon/drawable-$density"
  mkdir -p "$icon_dir"
  cp "chrome/android/java/res_chromium_base/mipmap-$density/app_icon.png" \
    "$icon_dir/icon_webview.png"
done
~~~

The icon paths above replace the obsolete paths in the LineageOS README.
The first four source images match the r2 APK pixel for pixel after
normalizing RGB channels of fully transparent pixels. Keep all five source
images in place. GN's icon resource ZIP contains every one of them, and
all five ZIP entries match the pinned PNG bytes.

When linking `system_webview_apk`, Chromium's common resource filter
drops `drawable-xxxhdpi/icon_webview`. The generated ARM rule takes its
regular expression and exceptions from `base/android/resource_exclusions.gni`.
Replaying the generated rule on the icon resource ZIP and linking with the
pinned AAPT2 produced the same four density entries as the r2 APK. The
unfiltered control linked with all five. Two runs produced byte-identical
test APKs. [Icon filter receipt](../manifests/webview-r2-icon-filter.json) ·
[Pinned Chromium resource filter](https://chromium.googlesource.com/chromium/src/+/4b3d0dabb8250b6f152d2d85d79e7706e309d087/base/android/resource_exclusions.gni)

## ARM32 build and relink checks

Use the public `system_webview_apk` target. Start from the pinned LineageOS
README arguments with `target_cpu = "arm"`, `target_os = "android"` and
`android_default_version_code = "810307800"`. The README's
`enable_nacl = false` is obsolete in the pinned Chromium tree. Preserve the
README's other product arguments, including its codec settings, for the
matching build attempt. Validate the supplied arguments in the actual
graph with `gn gen out/JarvisWebView --fail-on-unused-args` before compiling.
[Chromium WebView build instructions](https://chromium.googlesource.com/chromium/src/+/main/android_webview/docs/build-instructions.md) ·
[Pinned LineageOS arguments](https://github.com/LineageOS/android_external_chromium-webview_patches/blob/544b12e3d42a02b4337f31819f6ba917187dcccf/README)

Use the [exact GN arguments](../manifests/webview-r2.args.gn) from the
validated build graph. With `recipe_dir` set to the absolute path of this
repository and the shell in the patched Chromium checkout, run:

~~~sh
mkdir -p out/JarvisWebView
cp "$recipe_dir/manifests/webview-r2.args.gn" out/JarvisWebView/args.gn
gn gen out/JarvisWebView --fail-on-unused-args
autoninja -C out/JarvisWebView -j 4 system_webview_apk
~~~

The graph passed with GN 2595. The PGO-enabled hook run supplied the profiles,
and offline Siso compilation started. The dependent relink job waits for a
successful exit of that build. It verifies the archived baseline hashes,
checks the rebuilt package manifest and compares each APK payload to r2
before running the diagnostic FFmpeg relink. The full source build and relink
results are pending.

The ARM32 linker response includes `libffmpeg_internal.a`. The archive
contains 254 compiled objects, with a direct input from the pinned
FFmpeg tree for each. Readback from the staged userspace source companion
matched all 247 C inputs and seven assembly inputs to the build checkout
and Git blobs, including file modes.

Capture the APK, ELF architecture/build ID and the full GN arguments and
dependency record when the target builds. Then repeat with a distinct
local FFmpeg source marker and check that the rebuilt ARM WebView library
carries the marker. Use the unchanged r2 APK and its source companion as
reference inputs.
