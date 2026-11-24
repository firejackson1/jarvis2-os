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
