# OTA trust replacement in release signing

Apply `series` to `build/make` at
`bc95152efc6a43f3b103b1848c946e9bf8d4e493`, then rebuild the matching host
`sign_target_files_apks` tool before using `--replace_ota_keys`.

The pinned Python 3 code reads `META/otakeys.txt` as bytes then uses a text regex,
which fails for a nonempty key list. Decode UTF-8 explicitly. Certificate ZIP
entries also need basenames: native `common.ZipWrite` otherwise retains the
supplied host path. These changes do not modify certificates or key selection.

`tools/test-ota-key-replacement.py --source /your/patched/sign_target_files_apks.py`
executes the two actual native functions in isolation with synthetic public-only
fixture bytes. Both explicit and empty key lists must generate system and
recovery trust ZIPs containing the mapped certificate under its basename, with
identical bytes. CI downloads the exact checksum-pinned source and applies the
patch before this check. This is not full signing, certificate validation, final
image verification, or hardware recovery trust proof. The current active Android
build inputs were not changed; patch/rebuild the host tool after it completes.
