# LCARS recovery interface

Owner-selected direction: LCARS / Bridge Commander style, with Bluetooth remote
pairing requested. This source is an offline diagnostic bring-up, not a linked
or boot-tested recovery. It has not replaced the recovery on the device.

## Native interface implemented

- Amber rails, dark background, lavender focus tiles, visible selection and a
  development warning. The recovery's existing actions retain their indexes.
- Resolution-aware tiles and pagination; executable geometry tests cover 640x480,
  1280x720, 1920x1080 and 3840x2160.
- D-pad navigation flows through the upstream recovery selection loop. The
  highlight and selected-action return value stay synchronized. A physical-button
  tap traverses every item linearly, including the explicit submenu Back tile;
  holding selects. Keyboard Enter/OK/Select and Home/Back keys are handled.
- Overlong warning headers or insufficient screen space use the upstream menu,
  rather than dropping warnings to keep the new layout. Log/progress rendering
  without a menu also retains the upstream behavior.
- The existing diagnostic restrictions remain: this change enables no wipe,
  update, block write or Bluetooth service. RAM launch still needs a separately
  built image and an authorized hardware test.

## Bluetooth remote work still required

Receiving a D-pad event is not pairing support. Android's Bluetooth service is
not running in recovery, and pairing an Android remote does not prove recovery
can use it. The recovery needs controller discovery, driver/firmware startup,
its own Bluetooth host/pairing service and an HID-to-input path.

Offline stock-image inspection found multiple alternative radio drivers and
firmware configurations; this alone does not identify the actual controller.
The supplied `rtk_btusb.ko` exports a vendor character-device interface
(`alloc_chrdev_region`, `cdev_add`, `btchr_*`) and has no undefined
`hci_register_dev` symbol. Standard Linux HCI/BlueZ compatibility must therefore
be investigated rather than assumed. No firmware or pairing keys are copied
into this source tree. A later review of the retained Android trace identifies RTL8852BS on UART/H5;
see BLUETOOTH_RECOVERY.md. Recovery initialization and pairing remain unverified.

Planned pairing screen: discover, select, pair, report failures and return to the
menu. It must not report success from a simulated result. Keep single-button and
USB keyboard operation available throughout. Do not silently mount userdata or
import an owner's pairing database; recovery-owned pairing persistence and trust
need an explicit implementation and review.

## Validation so far

Run `python3 tools/test-host.py` for the three C++ suites, exact pinned recovery
interface syntax and Python ramdisk/packer tests. The six Python tests
all execute when the pinned source fixture tools or built AOSP host tools are supplied; the two new C++
suites execute drawing bounds, pagination, navigation, long-label and header
fallback checks. Host DrawInterface tests use a recording renderer, not HDMI.

An actual AArch64 ELF relocatable object compiled with Android 14 compiler/Bionic
inputs and pinned LineageOS 24 interface headers. SHA256:
`103681b674a7b54a74d881fb94a89b4e4e538399a4c80673214f1f6cb2a0137e`.
This checks compilation only. A full Android 17 link/build, HDMI, kernel input,
Bluetooth pairing, AVB and restoration remain unverified.
