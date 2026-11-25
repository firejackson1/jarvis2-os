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
