# Userspace notices and source index

The assembled ROM keeps upstream embedded notices. Supplemental readable copies
and exact source/build references are indexed in
[userspace-notices.json](../manifests/userspace-notices.json). The index describes
an inspected baseline; check the final build's versions and resource hashes.
It does not cover unshipped stock kernel/vendor images or certify all licensing.

The small verbatim files under notices/userspace preserve rsync's additional
permission text, NTFS library terms/attribution and Chromium's license. Original
GNU license texts also appear in the combined image notices. An absent per-module
NOTICE association alone does not show that the full license text was missing.

WebView's full Credits document is already embedded in its Chromium
Brotli-compressed DataPack resource. To obtain a readable supplemental copy from
the exact final APK, on a host with Python 3 and system libbrotlidec:

```sh
python3 tools/extract-webview-credits.py /outside/source/webview.apk \
  /outside/source/new-webview-Credits.html
```

The output must be new. The helper bounds the ZIP member, DataPack tables and
Brotli expansion, and requires one Credits resource. Compare the printed digest
with the source index for the supported WebView version. It reads data without
running the APK or its ARM native library. A different version must be reviewed
and indexed rather than silently accepted as the current material.

For the inspected baseline, extraction reproduced 9,316,146 bytes with SHA-256
`62f3d14545ae237c97aa64876f9141fa4fd0ed9995666d4ac724b421ba15e2b3`.
The supplemental packet can carry that document compressed with gzip mtime=0,
alongside the verbatim notices and index. Generated Credits and archives stay
outside Git. They contain no SDK/tool caches, private build state or keys.

The index also identifies the Chromium tag, FFmpeg dependency revision, relevant
build flags and pinned WebView patches. Preserve these source/build references
when distributing the userspace images; do not describe a prebuilt-only source
repository as the complete preferred source of its native components.

## Selected native source materials for neutral r2

The additional staged source archive contains the exact trees of 18 native
Android projects and two WebView inputs. It groups filesystem tools such as
e2fsprogs, F2FS and NTFS, networking tools including iproute2, iptables, dnsmasq
and rsync, and other directly mapped components such as strace, nano and Vim.
The source index records each pinned commit, tree, source archive, build and
license file index, and files identified by Android's module inventory.

Each of the 16,085 native project archive members matches its Git blob and
mode. The 1,112 matched installed paths were read back from the neutral r2
filesystems. The r2 image NOTICE files and the embedded WebView Credits also
match their earlier pinned hashes. The raw zstd Git blobs preserve the original
source bytes for files whose archive export applies line-ending conversion.

The official Chromium FFmpeg source archive matches all 11,351 files in the
Git tree pinned by WebView's DEPS. The companion carries the verified FFmpeg
license files, 13 Lineage WebView patches and the WebView build recipe. See the
[Chromium FFmpeg source](https://chromium.googlesource.com/chromium/third_party/ffmpeg/+/5c85ff666b3434d9323b83437f910ad8431ab7c9)
and [LineageOS WebView build sources](https://github.com/LineageOS/android_external_chromium-webview_patches/tree/544b12e3d42a02b4337f31819f6ba917187dcccf).

The Chromium dependency sync and ARM32 graph validation passed. The full
WebView build and a modified-FFmpeg relink remain open. Coverage of the
remaining Android and APEX dependencies and distribution review for stock
inputs are separate gates. The neutral r2 ZIP carries five userspace/AVB
images and the LCARS plug-in. The stock kernel and vendor partitions are local
inputs outside that delivery archive.

The [WebView rebuild record](WEBVIEW_REBUILD.md) pins the Chromium checkout and
depot_tools and verifies the patch replay and ARM32 APK readback. It also
documents the corrected icon paths and the density difference between the
documented build and the shipped prebuilt.

## APEX source and license inventory for neutral r2

The [APEX source receipt](../manifests/neutral-r2-apex-sources.json) binds all
31 APEX and compressed APEX packages in the r2 filesystems to the signed
target-files members. For each package, the original build output matched
the unsigned target-files member byte for byte and selected one Soong
license metadata root.

Run the built `compliance_listshare` tool from the Android source root with
the receipt's `metadata_path` for one package. The receipt also records the
combined `compliance_dumpgraph -label_conditions` output hash and
`compliance_checkshare` result for all 31 roots. Soong's source-sharing
resolution returned 260 project paths, all with pins in the published
Lineage manifest. The dependency graph has direct source-sharing labels in
28 projects. The rest includes labels propagated through dependencies.
Some graph edges lead to host tools. Use the package payload and source
license terms when deciding what to distribute.

The VNDK v34 APEX contains 120 regular ARM shared libraries. Each matched
the pinned Android prebuilt snapshot byte for byte. The receipt maps them to
114 source module directories from the snapshot's own indexes. The current
Lineage manifest pins the VNDK prebuilt tree. The
[import history](#vndk-v34-import-history) identifies which earlier builds
introduced the library bytes in that tree.
[Original VNDK snapshot import](https://android.googlesource.com/platform/prebuilts/vndk/v34/+/912e0c51bc2557a8d4b396bad1b6e39fe4c0b358) ·
[AOSP snapshot generation](https://source.android.com/docs/core/architecture/vndk/snapshot-generate)

The tethering APEX's ARM Cronet library matched the source-built Soong
output byte for byte. The private source companion includes all 45,638
tracked files from the pinned Android Cronet checkout, including its
license and Soong build definitions. Every file or symlink matched its
Git object and mode. The library filename reports version 121.0.6103.2.
The checkout's older version label in `METADATA` does not identify the
shipped binary. The receipt pins the actual Git tree and library hash.

Complete corresponding-source delivery and redistribution review remain open.

### VNDK v34 import history

The [library-level receipt](../manifests/neutral-r2-vndk-history.json) matches
every r2 APEX library to its exact Git blob in Google's published VNDK
history. The comparison covers all eight commits through the current import,
including the initial empty tree. The build ID on the latest
commit applies to the snapshot as a whole. Most library bytes arrived earlier.

| Earliest import with the r2 bytes | ARM libraries | Identification |
| --- | ---: | --- |
| 10185551 | 115 | Includes the three libraries with explicit GPL-family metadata |
| 10357257 | 1 | `libui.so` |
| 10951026 | 4 | `libgui.so`, `libprocessgroup.so`, `libutils.so`, and `libziparchive.so` |

The generated ARM Blueprint assigns a named module license to 109 libraries.
`libexif.so`, `libnl.so` and `libxml2.so` have module-level rules that
include a GPL or LGPL identifier. The other 11 libraries use the snapshot's
combined default metadata. That combined list does not attribute each
individual license to a particular part of a library. The public raw CI
endpoints for all four historical builds, including the earlier 10085907
import, returned HTTP 404 for their manifests. The earliest published binary
import identifies the CI build to investigate. Rebuilding these binaries from
their precise original source revisions remains open.
[Google's build 10185551 import](https://android.googlesource.com/platform/prebuilts/vndk/v34/+/d9d6c32b19b2fc50fb952e8c44d8186a51f22a25) ·
[AOSP snapshot and source checks](https://source.android.com/docs/core/architecture/vndk/snapshot-generate#upload-vndk-snapshots)

The official Jarvis2 stock OTA contains `com.android.vndk.current.apex`.
All 120 library paths match the r2 APEX, including the library below
`lib/hw`. Only the ARM Clang UBSan runtime matches byte for byte. The other
119 libraries differ, so locally extracting this stock APEX cannot reproduce
the current r2 payload. ABI compatibility and installation behavior would
need separate evidence for any future replacement.

### Source candidates for three VNDK libraries

The [source candidate receipt](../manifests/neutral-r2-vndk-source-candidates.json)
compares the exported headers from the 10185551 import with the ones retained
in r2. All 281 headers match public Android 14 source trees by Git blob.
For each project, the Android 14 release, GSI and `android-14.0.0_r1` commits
share the same full Git tree. The receipt pins those trees, the library
digests and their ARM ELF build IDs.

| Project | Matching exported headers | Android 14 source commit |
| --- | ---: | --- |
| `libexif` | 20 | `c6eff752051d8b32c0c68e6107452949caa9d744` |
| `libnl` | 195 | `7523b7d9f2c3977a400d162670a8c0bc8eaa94b0` |
| `libxml2` | 66 | `9ec1e3881001ba9ba6da59154553f33a71c5c248` |

The r2 library's exported `xmlParserVersion` variable matches the combined
version macros in the candidate `libxml2` header. In comparison, the later
r67 `libxml2` tree differs in 35 exported headers. All 195 `libnl` headers
also match r67, where the build rule adds `lib/route/addr.c`. The r2
`libnl` symbol table lacks `rtnl_addr_alloc`. This is additional evidence
for reviewing the older source candidate and illustrates why matching
headers alone cannot identify the build inputs.

Three private candidate source archives reproduced byte for byte. Every
one of their 4,739 Git entries matched the original blob and mode. To
recreate an archive, clone the pinned project and use its commit from
the receipt with `git archive --prefix=<project>-<short-commit>/ <commit> | gzip -n`.
Use the first 12 characters of the commit in the archive prefix.
The original CI manifests, exact binary rebuilds and full distribution
review remain open.
[Android VNDK snapshot source documentation](https://source.android.com/docs/core/architecture/vndk/snapshot-generate#snapshot-files)

### VNDK modules using the snapshot default

The [module attribution receipt](../manifests/neutral-r2-vndk-default-license-sources.json)
maps all 11 default-rule libraries to their original module paths. The paths
agree in the Android build 10185551 import and the r2 snapshot. Each ARM ELF
also matches the exact signed r2 APEX filesystem inventory.

Ten of the libraries are versioned AIDL NDK modules. The Android 14 r1
candidates reproduce the latest frozen API hash in all ten directories using
the pinned AOSP hash script. The 119 generated C++ paths match the frozen
AIDL paths. All 119 C++ files and 357 exported headers have identical Git
blobs across both snapshot commits.
Six signed libraries also contain the expected interface hash string. The
four modules without an exported interface-hash method are checked through
the frozen source and snapshot file paths.
[AOSP Stable AIDL](https://source.android.com/docs/core/architecture/aidl/stable-aidl)

Nine frozen API directories also match the currently pinned ROM source.
The graphics common V4 directory differs in `BufferUsage.aidl` and its
hash list. The older AOSP source and both snapshot exports use
`VENDOR_MASK = -268435456`. The ROM's pinned source uses `4026531840`.
That difference identifies the older definition in r2's exported header.

Four AIDL declarations use the Android Apache 2.0 rule. The six hardware AIDL
declarations use the `hardware_interfaces_license` rule, which lists Apache
2.0 and NCSA in the project Blueprint. Both rules point to byte-identical
Apache 2.0 license text. Every one of the 11 paths links to that exact text
in the staged VNDK notice XML.

For `libstagefright_bufferqueue_helper.so`, all three exported headers match
the Android 14 r1 tree by Git blob and mode. Its two direct C++ source
candidates and the three headers carry Apache 2.0 headers. The candidate
Blueprint also references `libgui_bufferqueue_static` for the vendor
build. The r2 ELF defines BufferQueueProducer and GraphicBufferSource symbols
and has no shared dependency on `libgui.so`. The complete static
dependency license review, original CI manifest and exact binary rebuilds
remain open.

### APEX notice companion

The three installed partition notice archives contain 174 of the 229
distinct notice texts emitted by Soong for the 31 matched APEX roots. The
installed XML has no entry for 731 of the 734 paths in the generated APEX
index. In the VNDK subset, nine of 54 notice texts and the paths for all
120 ARM libraries lack exact matches in those partition archives.

The private r2 delivery adds `jarvis2-r2-apex-notices.tar.gz` with the
combined APEX notices and the VNDK notices as both text and XML. All five
archive entries matched their source hashes, and repeated packaging
produced identical bytes. The [notice receipt](../manifests/neutral-r2-apex-notices.json)
pins the archive and generated notices. Keep the companion alongside the
ROM ZIP. The installed partition notice files and ROM images retain their
original hashes.

To regenerate the combined documents, run the built AOSP
`out/host/linux-x86/bin/xmlnotice` and `textnotice` with
`-product Jarvis2 -title "Jarvis2 r2 APEX license notices"
-strip_prefix out/target/product/jarvis2/`. Pass the 31 hash-checked
`metadata_path` values from the APEX source receipt. For the VNDK-only
documents, use its single metadata path and title
`Jarvis2 VNDK v34 license notices`.

The notice companion fills the observed attribution gap in the staged
delivery. The [import history](#vndk-v34-import-history) records the
historical VNDK source manifest searches and their limits.
[Android CI artifact documentation](https://source.android.com/docs/setup/contribute/dashboard)
