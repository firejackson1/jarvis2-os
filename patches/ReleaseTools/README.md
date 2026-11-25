# Release build identity and OTA trust

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

For explicitly numbered builds, the second patch makes common partition
properties depend on both Soong identity files. It also tracks the date for
global system buildinfo. The existing incremental behavior for unnumbered
builds is preserved. This prevents the stale `system_ext` and `product`
identity observed in the private neutral r2 artifact. To replay the original
Android rules after applying the series, run:

```sh
python3 tools/test-build-properties.py /path/to/android/build/make \
  /path/to/android/prebuilts/build-tools/linux-x86/bin
```

The native fixture runs the extracted Make rules through the pinned Kati and
Ninja, including the real `buildinfo.sh`. It checks a fresh build, an
incremental change to each identity file, and the unchanged and unnumbered
build cases. Run the separate final-image identity check for release evidence.
