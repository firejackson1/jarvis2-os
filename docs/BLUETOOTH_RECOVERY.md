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

### Android 17 source check

The separate Android 17 checkout selects Bluetooth revision
`0a8ed94208f86cf0fc036b35841fac43ee84c770`. Its Git tree has no
`system/test/headless` subtree. The queued Android 14 `bt_headless` compile
experiment was therefore cancelled while still waiting for the recovery build;
it never built or ran a Bluetooth program. Do not repeat that obsolete target
as an Android 17 build instruction.

The current source still has `system/btif/src/bluetooth.cc`, the `libbtif`
static-library module, native HID-host code, and
`system/gd/hal/hci_backend_hidl.cc`. The latter references HIDL Bluetooth 1.0/1.1
interfaces, so upstream has not removed that transport interface. This is useful
source evidence for the separate vendor-service approach; it does not establish
service registration, ABI compatibility, SELinux permission or controller startup
in Recovery.

The current API also differs from the older headless example: lifecycle entry
points are standalone `bluetooth_init()`, `bluetooth_enable()`,
`bluetooth_disable()` and `bluetooth_cleanup()` functions. Initialization takes
OS callouts, the HCI instance name and an autonomous-repairing flag. Copying the
old interface-table initializer would not implement that lifecycle.

On Android, the current `ParameterProvider` has no config/snoop path override.
It uses `/data/misc/bluedroid/bt_config.conf` for the default HCI instance and
`/data/misc/bluetooth/logs` for snoop logs. Recovery must supply these directories
from verified RAM-backed storage before stack startup; mounting Android userdata
there to satisfy the paths would violate the initial bring-up design. The old
Android 14 override methods above are reference evidence only.

Continue this path in the Android 17 checkout:

1. Port a native host lifecycle against the current Bluetooth interfaces and
   link its actual dependency graph offline. The older headless code is a
   reference, not an available upstream target. Audit configuration paths,
   Android service dependencies and recovery variants before including a binary
   in the ramdisk. A compiled library alone is not the pairing backend.
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
- Android 17 Bluetooth
  [native interface](https://github.com/LineageOS/android_packages_modules_Bluetooth/blob/0a8ed94208f86cf0fc036b35841fac43ee84c770/system/btif/src/bluetooth.cc),
  [library build](https://github.com/LineageOS/android_packages_modules_Bluetooth/blob/0a8ed94208f86cf0fc036b35841fac43ee84c770/system/btif/Android.bp) and
  [HIDL transport backend](https://github.com/LineageOS/android_packages_modules_Bluetooth/blob/0a8ed94208f86cf0fc036b35841fac43ee84c770/system/gd/hal/hci_backend_hidl.cc)
  at `0a8ed94208f86cf0fc036b35841fac43ee84c770`.
- Radxa's Realtek driver reference at
  [72ef9b75374fdde945e0a19f6aba68e13d4d426d](https://github.com/radxa/rtkbt/tree/72ef9b75374fdde945e0a19f6aba68e13d4d426d),
  whose documentation includes RTL8852BS UART/H5 and whose attach source still
  requires the kernel HCI line discipline. Its GPL sources/firmware have not been
  imported into this Apache-licensed UI project or bundled for redistribution.
