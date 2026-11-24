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
