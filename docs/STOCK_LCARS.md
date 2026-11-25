# Stock-compatible LCARS prototype

This recipe builds an offline ARM32 Recovery prototype for the onn Jarvis2.
The LCARS extension delegates vendor menu handling through the original stock
factory. The build keeps the stock Recovery executable, Fastbootd, boot-control
services and init files. It produces an unsigned development image.

## Inputs

- A pinned LineageOS 21 Jarvis2 Android checkout with the built host
  `mkbootimg`, `unpack_bootimg` and `lz4` tools. The builder uses the ARM32
  `clang-r510928` toolchain, libc++ and Bionic headers from that checkout.
  [ROM source setup](https://github.com/firejackson1/jarvis2-os/blob/main/docs/BUILD.md)
- The AOSP `bootable/recovery` checkout at
  `2e6ff7bc40063d38fc5478389a47c0fafba20bfd` for the Android 14 UI ABI.
  The builder verifies the four required headers by SHA-256.
  [Pinned AOSP source](https://android.googlesource.com/platform/bootable/recovery/+/2e6ff7bc40063d38fc5478389a47c0fafba20bfd/)
- A local copy of the stock `vendor_boot` whose SHA-256 is
  `c017791c8e52678595a03b902237dcb15a4e8adeb3d35fdb2232838750e4233a`.
  The release source does not carry vendor images or signing material.

## Build and verify

```sh
python3 tools/build_stock_lcars.py \
    --android-tree /path/to/lineage21 \
    --aosp-recovery /path/to/aosp-bootable-recovery \
    --stock-vendor-boot /path/to/stock/vendor_boot.img \
    --output /path/to/fresh/private-output
```

The source recipe reproduced both the plug-in and the 27,183,104-byte image.
Its report confirms 481 preserved recovery archive records and identical stock
platform ramdisk, device tree and boot configuration. The two modified paths
are `system/lib/librecovery_ui_ext.so` and the added stock factory alias.

| Output | SHA-256 |
| --- | --- |
| `librecovery_ui_ext.so` | `8d14f4ea2d191fce4424eab196690dc646080f82484d107bd89f77e340ca3f3c` |
| `vendor_boot-unsigned.img` | `30625d390c1fdd10e4465619bbbd9f66df0ec48652f716ba80371e850fd58862` |

The prior isolated ARM emulator test loaded both factories and compared the
four stock menu labels and seven key codes with both visibility states. The
prototype still needs a hardware boot, HDMI and input checks, authenticated
USB, Fastbootd, Bluetooth pairing, AVB integration and rollback verification.

## Recreate the Recovery image from a plug-in

On Linux with Python 3.11 or later and `lz4` installed, the source-only tool
kit can be prepared separately. It downloads four pinned scripts and verifies
their hashes before writing the kit. No Android checkout is needed for this
route. Supply the local stock `vendor_boot`, the reviewed plug-in and the two
SHA-256 values from the trusted distribution manifest.

```sh
python3 tools/prepare_stock_lcars_kit.py /path/to/fresh/tool-kit
python3 tools/materialize_stock_lcars.py \
    --tool-kit /path/to/tool-kit \
    --stock-vendor-boot /path/to/stock/vendor_boot.img \
    --plugin /path/to/recovery/librecovery_ui_ext.so \
    --plugin-sha256 <reviewed-plugin-sha256> \
    --expected-image-sha256 <reviewed-vendor-boot-sha256> \
    --output /path/to/fresh/private-output
```

The tool rebuilds the stock-format AVB hash footer and checks the resulting
64 MiB file against the exact manifest digest. It verifies the leaf's hash.
The matching signed parent `vbmeta` must be checked separately before any
hardware use. With the reviewed prototype plug-in, the portable tool kit and
Linux `lz4` 1.10.0 reproduced the private footer-wrapped image with SHA-256
`c9cc31121ee165b5cc45adc85af500589d34cf9cbb4a7b6bed499e3212c7d65e`.
The temporary root key from that AVB rehearsal is for offline testing only.
