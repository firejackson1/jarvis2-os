# Diagnostic recovery fragment preparation

The native ARM64 recovery build is preserved unchanged. A separate offline
derivation prepares its CPIO for guarded RAM bring-up. Neither artifact has
booted; the derived fragment alone is not a complete boot image.

## Exact transformation

`tools/prepare_ramdisk.py` requires the exact lowercase SHA256 of its input.
The input must pass the ARM64 entrypoint audit with exactly one reviewed trust
finding: the unresolved `adb_keys` symlink to
`/product/etc/security/adb_keys`. A key file, different target, resolved target
or additional credential finding is rejected rather than silently removed.

Only these original records change:

| Record | Diagnostic change |
| --- | --- |
| `adb_keys` | Remove that unresolved standard placeholder symlink. |
| `system/etc/init/hw/init.rc` | Replace the single hardware import with `/ramboot/init.hardware.rc`; supply explicit `--show_text` to the single Recovery service. Unexpected imports or alternate/duplicate Recovery declarations are rejected. |
| `system/etc/recovery.fstab` | Replace the prototype metadata mount with `ramdisk /tmp ramdisk defaults defaults`. No Android filesystem entry remains in this file. |

Explicit service arguments prevent falling back to BCB/cache arguments when
Recovery has no command-line arguments. They do not prevent all BCB writes.
The early block guard remains mandatory; upstream Recovery can attempt to
update/clear the BCB and save logs before a menu action.

The tool edits original newc records without extracting/repacking the filesystem.
For modified regular files it updates size, payload, padding and the checksum
when the archive uses CRC newc. Other header metadata is preserved. Untouched
records, including original hard-link headers and payload placement, must remain
byte-identical. The original trailer and final padding are retained. The output
is reparsed and subjected to the strict credential/ARM64 audit again.

`prop.default`, native binaries, SELinux policy and the adbd service are unchanged.
Removing the placeholder is not proof of secure or functioning authentication;
the compiled upstream userdebug/unlocked behavior still needs runtime review.

## Executed artifact checks

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Original decoded native fragment | 32,401,152 | `de1c94c471ce1c8ec87ebdcf166e52444d8f6aa260ca18a18ccc776cf027bc4e` |
| Derived diagnostic fragment | 32,400,864 | `cae4c7f587a43a82d4dff32d194077cbc0b799527fb7cdae959b3038e3da38dc` |

The executed derivation reported exactly the changes above, byte-identical
untouched records and no remaining blocked credential artifacts. Inputs and
private source/tool receipts remain outside Git. Host tests cover digest
binding, unexpected trust material, ambiguous imports/services, CRC updates,
unchanged adbd/properties and preserved hard-link metadata/payloads. They do not
execute Android init or privileged operations.

## Remaining assembly and qualification

- Supply the reviewed `/ramboot/init.hardware.rc` rather than importing the
  stock hardware script wholesale. The latter also starts closed services and
  touches subsystems outside this diagnostic test.
- Add the guarded PID 1 runtime and its interpreter/library closure. Account for
  the native archive's `/bin` symlink to `/system/bin`; do not accidentally
  replace it with a directory when placing BusyBox.
- Bind the actual kernel release, DTB, ordered stock modules and complete
  physical partition inventory. The saved kernel release is
  `5.15.196-android14-11-g3d26c188ef7e-ab14657224`; the module vermagic release
  prefix is `5.15.196-android14-11-g570709ea67dc`. All 52 stock module objects
  contain a nonempty `__versions` section. This inventory proves neither symbol
  CRC compatibility nor signature acceptance. Do not force module loading or
  alter the kernel release to hide the difference.
- Review the complete effective import, fstab, dependency and policy graph after
  adding the overlay. Package within the proven RAM launch limits only then.
- Authorize and record the concrete hardware test, early protection evidence,
  display/input/ADB behavior, before/after partition hashes and Android return.

The derived archive is private diagnostic preparation. It is not the final
install-capable custom recovery, an AVB-signed image or public binary release.
The subsequently assembled [guarded CPIO](GUARDED_RAMDISK.md) retains those limits
and records the boot-container layout work still needed.
