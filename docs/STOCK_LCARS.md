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
