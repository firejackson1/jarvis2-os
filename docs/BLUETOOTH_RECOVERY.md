# Recovery Bluetooth investigation

Bluetooth pairing is not implemented or hardware-tested in this recovery.
D-pad key handling alone does not establish Bluetooth support.

## Controller and transport established from evidence

A retained Android runtime trace identifies `rtl8852bs`, selects the Realtek
vendor library, opens `/dev/ttyS1`, uses H5 and configures the controller/host
UART to 1500000 baud. Firmware initialization reports LMP subversion 0x8852,
HCI version/revision 0xb/0xb and firmware/config names `rtl8852bs_fw` and
`rtl8852bs_config`. This describes the observed working Android session; it is
not a live recovery initialization or pairing test.

The pinned stock vendor image contains those local extraction inputs:

| File | Bytes | SHA256 |
|---|---:|---|
| `rtl8852bs_fw` | 200474 | `280f92b49487986cc35afce4027fc55cf02eeea5aac742e3826b67efd23feb8b` |
| `rtl8852bs_config` | 68 | `6aefdce624c4248739bd5039f01cf9e5248b54a0e64bdfbef214cd78bbaf52c7` |

They are not copied into this repository or licensed by this document. The
initial UART baud and complete reset/power sequence still need validation.
The separate USB-driver analysis in LCARS_UI.md describes an alternative driver
in the image, not the transport selected in the retained runtime trace.

## Stock kernel constraints

The kernel's embedded IKCONFIG was extracted offline from the pinned stock boot
image, without executing the kernel. Relevant values:

- `CONFIG_BT=m`, `CONFIG_BT_LE=y`, `CONFIG_BT_HCIUART=m`;
- `CONFIG_BT_HCIUART_3WIRE` and `CONFIG_BT_HCIUART_RTL` are not set;
- `CONFIG_UHID=y`, `CONFIG_MODVERSIONS=y`, `CONFIG_MODULE_SIG_PROTECT=y`,
  `CONFIG_TRIM_UNUSED_KSYMS=y`; forced module signing is not set.

A generic HCI-UART/BlueZ command is therefore not an established working path.
Matching module ABI, symbol visibility and signing policy must not be assumed;
there is no authorization or plan here to replace the device kernel.

## Prefer reuse before another Bluetooth stack

The pinned Android 14 Bluetooth source provides `system/test/headless`, which
initializes `bluetoothInterface` without Android Java UI. Its native HID-host
implementation targets `/dev/uhid`, and `ParameterProvider` exposes explicit
configuration and snoop path overrides. Recovery's minui input reader also watches
`/dev/input` for newly created devices. These are source-level facilities, not a
working recovery integration.

Investigate this path first in the Android 17 checkout:

1. Build the upstream native headless target offline and inspect its dependencies.
2. Check compatibility with the stock 32-bit vendor HIDL Bluetooth service from a
   separate 32-bit process. A 64-bit client cannot directly load its 32-bit vendor
   libraries; cross-process compatibility and required loader/services remain
   unverified.
3. Keep controller setup, all stack configuration, bond data and snoop files in
   recovery RAM during bring-up; do not silently access Android's pairing store.
4. Add a bounded pairing controller with explicit discovery, selection, consent,
   failure and cancellation states. Verify HID events really reach recovery.
5. Test in RAM with USB keyboard/box-button fallback before any device write.

Do not substitute a simulated device discovery or successful callback for a
real pairing test. Keep the pairing UI unavailable until a functioning backend
reports actual controller state. Do not start a radio service in this source-only
investigation.

## References inspected

- Android Bluetooth source at
  [68c10e675632ac57b1d4d807c38dbd470b73e49e](https://github.com/LineageOS/android_packages_modules_Bluetooth/tree/68c10e675632ac57b1d4d807c38dbd470b73e49e/system/test/headless).
  Android 17 API/dependency compatibility must be checked separately.
- Radxa's Realtek driver reference at
  [72ef9b75374fdde945e0a19f6aba68e13d4d426d](https://github.com/radxa/rtkbt/tree/72ef9b75374fdde945e0a19f6aba68e13d4d426d),
  whose documentation includes RTL8852BS UART/H5 and whose attach source still
  requires the kernel HCI line discipline. Its GPL sources/firmware have not been
  imported into this Apache-licensed UI project or bundled for redistribution.
