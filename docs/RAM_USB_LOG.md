# One-way USB RAM startup log

Status: offline diagnostic candidate, not hardware-qualified recovery. The
ordinary full-recovery RAM test stalled without a retained log. This separate
mode tests the USB/runtime path and reports relevant boot flags. It does not
start the recovery menu or establish where the earlier image actually failed.

The exact retained kernel's embedded configuration enables USB_F_ACM,
USB_U_SERIAL, USB_CONFIGFS_ACM and CONFIGFS_FS as built-ins. Configuration follows
the [Linux 5.15 configfs gadget interface](https://www.kernel.org/doc/html/v5.15/usb/gadget_configfs.html).
The [ACM function's port_num](https://github.com/torvalds/linux/blob/v5.15/drivers/usb/gadget/function/f_acm.c)
binds the selected tty to the created function. These upstream references do
not qualify the onn's UDC, PHY, endpoint resources or vendor-specific behavior.

## What runs

- A separate PID 1 entrypoint checks a RAM root, the exact kernel release and
  board identity. Ordinary host execution is refused before invoking BusyBox.
- Only the 25 reviewed modules through amlogic-usb are loaded, after complete
  ordered hash/dependency validation. cqhci, amlogic-mmc and the later display/
  input/storage sequence are absent from this overlay.
- After verifying an empty gadget configuration, this mode checks for its UDC.
  If none exists, it uses a private RAM debugfs mount and the verified vendor
  role control to request device mode. Only the observed notg-host role is
  accepted for switching; the resulting role and exact UDC must be verified.
  The private debugfs view is removed before constructing the ACM gadget.
- A private configfs view refuses any existing gadget or an unexpected UDC.
  One ACM function must own port zero. Its tty major/minor come from sysfs;
  the device node is created only in private RAM state.
- An owned background writer sets raw/no-echo mode and replays the small RAM log
  every two seconds, reopening the port between finite snapshots. Duplicate
  snapshots are intentional so an idle reconnect can retrieve the log.
  The parent never waits for a serial host. Failed opens/writes are retried in
  the child, whose stdin is a private RAM null node. There is no command reader,
  shell, ADB, network or storage function.
- PID 1 waits on success or failure without requesting a reboot. It never
  calls Android init and never accesses Android block nodes or filesystems.

The ordinary recovery assembler remains the default and keeps its stricter
force-normal/resume rejection and storage-protection handoff. The log-only mode
can report these flags because it has no Android-init handoff. Its output is
not a recovery image suitable for installation.

## Offline assembly

Use the same checksum-bound BusyBox, musl loader, platform-module CPIO, kernel
release and prepared ARM64 diagnostic base as the guarded recovery experiment.
The mode does not require a partition inventory. All generated artifacts stay
outside source control.

```sh
python3 tools/assemble_ramdisk.py \
  --diagnostic-cpio /private/prepared/diagnostic.cpio \
  --expected-input-sha256 EXACT_BASE_SHA256 \
  --inputs /private/inputs.json --mode usb-log-only \
  --output /private/new-usb-log-output
```

The existing legacy-v2 packer can wrap a deterministically compressed result
with the pinned reference's unchanged kernel/DTB. Its `boot_tested` and runtime
qualification fields stay false. Development gadget IDs and generic strings
are for private bring-up; an assigned public product identity is not claimed.

## Limits and next hardware check

Host fixtures substitute all privileged setup operations. ARM64 QEMU checks can
exercise the actual shell/applications but cannot validate USB enumeration.
If startup stops before the USB module prefix/gadget bind, its log stays in RAM
and USB cannot report it. There is no claim of diagnostics before that point.

A future authorized RAM test needs a directly connected USB host and a verified
way back to Android. The host should expose a CDC ACM serial port; opening that
port should produce the generic startup log and boot-mode flags. No serial
keystroke is a supported command. A missing port or log is a failed diagnostic
test, not permission to flash or disable the normal recovery guard.

## Executed offline evidence, 2026-11-24

Source `c99f07ffbb158d78077c7abcd357747076bf26cd` was cloned from a verified Git
bundle into a fresh private native build directory. The source stayed clean.
Two separate assemblies and deterministic gzip outputs were byte-identical:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Diagnostic CPIO | 38,305,944 | `538a02f93ff66650222e503c89fa7114f9975d25ed94a6f8238cc0429fdbb676` |
| Gzip ramdisk | 14,682,765 | `79ea82a183fdf69aef0709fec470749b1f6fc14547551f82fc7900f5cc2784e7` |
| Unsigned legacy-v2 RAM image | 35,520,512 | `dadf373afe1f285c5c032d283bc0a414f7bf1fca93bd5970c64566e4c4d45c95` |

Round-trip packaging verified unchanged kernel/DTB bytes and the 128 MiB offline
download budget. A current device-reported budget is still a launch preflight.
The previous full recovery image and guarded CPIO hashes remained unchanged.
The bounded job finished successfully in 13.6 seconds; the desktop VM remained
running. No image was signed, booted or flashed.

Local host tests: 74 tests ran with six missing-native-tool skips. On the native
build host all 74 ran without skips. Three C++ behavior suites and recovery-header
syntax checks also passed. Actual ARM64 BusyBox shell checks passed 39 tests with
privileged operations substituted. A test-owned PTY separately verified the
actual ARM64 stty clears echo, canonical input and output postprocessing.

Independent source review identified an idle reconnect gap in tail-follow mode.
The exact BusyBox binary reproduced it after its output reader closed without
new log data. Failing idle-reopen/private-null tests were then made green by
finite snapshots and explicit child stdin. This review and these fixtures do
not qualify the real UDC, USB reconnect or normal recovery boot.

## USB role finding and correction, 2026-11-24

Read-only live Android checks found an empty UDC class, an xHCI child under
the dual-role controller and an unbound gadget despite `sys.usb.config=mtp,adb`.
The vendor USB parameter was false; the DT controller type was 1. This is a
kernel role issue before ADB authorization, rather than evidence of a bad cable.

The retained amlogic-usb.ko is 1,576,016 bytes, SHA256
`f077029f83dab546f13882e4e7aaf344f71d2597277119003894f4ba4eabbd98`.
Its build-ID note matched the loaded note (SHA256
`d1ba3d73ebbe9c6186bafda0c7d443e32c3a51c64a8e9af78e04012dba96fb44`).
This binds the loaded build ID to the retained analysis input; it is not a
new full-file hash of a loaded kernel module.

LLVM disassembly of that module establishes:

- get_otg_mode reads force_device_mode; the module has the otg_device parameter.
- The probe's branch at 0x9274 selects gadget initialization when that flag is
  true, or when controller type is 2. False plus type 1 selects host setup.
- A built-in debugfs mode handler selects host/device without unloading the
  module. The driver remove callback simply returns zero, so unbind/rebind was
  deliberately avoided rather than assumed safe.

A bounded runtime test changed only that existing mode control from notg-host
to notg-device. USB ADB immediately appeared on the actual computer over the
already-connected cable and the UDC reported configured. Restored notg-host and
removed the private debugfs mount. Android stayed awake on slot A with Ethernet
ADB; no module reload, sleep request, reboot, flash, slot switch or wipe occurred.
This qualifies that runtime switch on the current Android session. It does not
qualify the separate diagnostic image, Fastboot, or a persistent automatic policy.

An initial offline approach passed a module insertion parameter. Further
inspection found init_module calls __module_init_hook before usb_main_init;
the related [GKI module hook](https://github.com/khadas/common_drivers/blob/3a11a86a02e759fc57fc79410215f7c0c3a0d8e0/drivers/gki_tool/gki_module.c#L64)
replays boot-argument setup callbacks. That can overwrite the parameter before
the probe, so that approach was withdrawn before building an image.

Instead, the diagnostic now uses the runtime role control only when no UDC is
registered. It rejects unexpected controllers, unknown roles, existing gadget
configuration or a preexisting private debug path. It verifies the changed role,
waits at most four one-second intervals for the exact controller, and cleans its
owned debugfs view on success or failure. All module hashes still validate
before insertion; the shared loader and default recovery entrypoint are unchanged.
The first candidate's RAM launch arguments remain unknown; this is a correction
for an identified role-selection failure mode, not proof of its earlier stall.

## Corrected build and first hardware result

Built source `54163ad8cff91bf9a7814982f15b060b1e3f54db` from a clean private
clone. Two empty output directories produced identical CPIO and gzip bytes;
the legacy-v2 packer verified unchanged kernel/DTB and a matching round trip.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Corrected CPIO | 38,307,376 | `c7920e3ee437d69430440820970d8d40c509bc32823452bc5f91633c28e651c2` |
| Gzip ramdisk | 14,682,939 | `15fa2801559976e8f6c0c4e838afde8d472ebee0b1ef7167daa3a8bb556d69b9` |
| Unsigned RAM image | 35,520,512 | `1f8ee62040f622f2cc25af62fc7f61bf3f14efc90f779fe3e7e67eb4f203c138` |

The bounded native job completed in 15.932 seconds, with 344.2 MiB peak memory
and no swap; the desktop VM stayed running. All 80 native host tests ran without
skips, plus three C++ suites and pinned recovery-header checks. Local tests ran
80 cases with six missing-native-tool skips. Prior full-recovery and first USB
diagnostic artifacts remained byte-unchanged. The default loader and both
entrypoints are unchanged from the preceding source.
The final ARM64 BusyBox shell ran all 45 startup/storage/USB guard tests under
QEMU with privileged operations substituted. Independent source review found
no blocking issue; added delayed-registration and cleanup-failure checks from
its feedback. These are not kernel, controller or serial-transfer tests.

With the owner present for a return check, read-only Android preflight reported
boot completion and slot A. Captured complete hashes of boot_a, vendor_boot_a,
dtbo_a, vbmeta_a and vbmeta_system_a; no vbmeta_vendor_a node existed. bootctl
was absent, so bootable/successful/retry metadata was not obtained. snapshotctl
reported state none but also missing-state-file warnings; this is not proof of
a healthy merge or a fully qualified installation preflight.

Verified the bootloader device/model, selected slot A, unlocked state,
is-userspace no and the 128 MiB download budget. Rehashed the image immediately
before Fastboot boot; transfer and boot returned OKAY in 8.696 seconds.

The exact generic USB gadget enumerated at high speed with two CDC ACM
interfaces and an ACM tty. That establishes startup through gadget bind for
this image, not full Recovery startup. A 12-second reader received zero bytes;
a second 12-second read with explicit carrier/read settings and DTR/RTS also
received zero bytes. No serial command or application payload was sent. The
host modem manager was inactive and no competing tty reader was found.
The log writer/data-transfer stage and the actual reported boot flags remain
unverified; enumeration alone is not a successful log capture.

Power-cycled using the owner's mapped outlet, verified power restored ON, and
requested the normal network-ADB re-enable flow. Android return and after-test
partition comparisons are pending. No flash, wipe, slot change or saved
bootloader setting was requested. Do not call this recovery ready.
