# Prepare the Jarvis2 stock foundation locally

This preview uses the 2026 onn 4K Pro (`jarvis2`) US Android 14 firmware
`URO3.260203.035.A1`, incremental build `15640252`. Download the 911,005,562-byte
full OTA directly from Google. Use it as a source of local image files.
[Full Jarvis2 OTA](https://android.googleapis.com/packages/ota-api/package/7c8075293d8380cc8f77feb9c47be5ed9d307adb.zip)

The OTA SHA-256 is `7d8eeb206b0712db71fc0559ce66e1f9b9e97d7cd7dd9b821880c387d9aa70b2`.
The extraction below was tested on Linux x86-64 with `payload-dumper-go` 2.1.0.
The tested Linux amd64 archive SHA-256 is
`bbbb53a71955c69272afdef7bc7e83a1bb1770f453d0c21dcaf61a3ba0463c11`.
Keep the extractor's normal payload verification enabled.
[payload-dumper-go 2.1.0 release](https://github.com/ssut/payload-dumper-go/releases/tag/2.1.0)

Run from this repository with the downloaded OTA and verified extractor. The
command writes to a new host directory and extracts only the inputs used by the
preview.

```bash
set -euo pipefail
source_repo="$PWD"
ota=/path/to/downloaded/full-ota.zip
extractor=/path/to/verified/payload-dumper-go
work=$(mktemp -d)
printf '%s  %s\n' 7d8eeb206b0712db71fc0559ce66e1f9b9e97d7cd7dd9b821880c387d9aa70b2 "$ota" | sha256sum -c -
mkdir "$work/raw" "$work/templates"
"$extractor" -q -p boot,dtbo,init_boot,odm,odm_dlkm,odm_ext,oem,system_dlkm,vbmeta,vbmeta_system,vendor,vendor_boot,vendor_dlkm \
  -o "$work/raw" "$ota"
(cd "$work/raw" && sha256sum -c "$source_repo/stock-inputs.sha256")
test "$(wc -c < "$work/raw/vbmeta.img")" -eq 12288
test "$(wc -c < "$work/raw/vbmeta_system.img")" -eq 4096
for partition in vbmeta vbmeta_system; do
  cp "$work/raw/$partition.img" "$work/templates/$partition.img"
  truncate -s 2097152 "$work/templates/$partition.img"
done
(cd "$work/templates" && sha256sum -c <<'JARVIS2_TEMPLATE_HASHES'
a067d7e55a35d5d517af1e48a364b1b6dd483466fb499c36c1ac2cf5fba35d04  vbmeta.img
0d307c751d959322557a832471ddac47857c91ab9365d628238cc17a47babe83  vbmeta_system.img
JARVIS2_TEMPLATE_HASHES
)
printf 'Stock images: %s\nAVB templates: %s\n' "$work/raw" "$work/templates"
```

`raw` supplies `stage-stock.py`, the AVB assembler's `--references`, and the
LCARS host preflight's `--stock-images`. `templates` supplies the AVB assembler's
`--stock-templates`. The two template copies are zero-padded to the size pinned
by the stock AVB profile. The raw OTA images are preserved. Keep the files
local and use the [host preflight](CANDIDATE_INSTALLATION.md#prepare-a-verified-lcars-zip-locally)
before any separately authorized device test.

The downloaded stock files passed the stock AVB chain check and staged the
expected kernel. They also reproduced the exact LCARS preflight result for
the [neutral candidate](../manifests/current-neutral-artwork.json). The saved
slot-A layout and restore-file check used historical test data. It did not
measure the current device's layout or demonstrate a restore.
[Stock rollback input rehearsal](RESTORE_PLAN.md#stock-rollback-input-rehearsal)
