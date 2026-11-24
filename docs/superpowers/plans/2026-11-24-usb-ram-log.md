# USB RAM startup log implementation plan

> Execute inline using superpowers:executing-plans under standing owner
> delegation. Do not launch on hardware in this task.

**Goal:** Produce a private one-way USB serial image that exposes RAM startup
diagnostics without entering Android init or loading the internal-storage driver.

**Architecture:** Reuse the reviewed module hash loader and split identity from
boot-mode validation. A separate PID 1 entrypoint binds one configfs ACM gadget;
an owned background writer streams the RAM log. Add explicit assembly selection.

**Spec:** ../specs/2026-11-24-usb-ram-log.md

**Constraints:** Known kernel/DTB/runtime; RAM state only; no shell/input, Android
handoff, eMMC module, flash, slot, power or VM action. Host privileged operations
must be substituted in tests, never performed against real devices.

**Review focus:** Wrong identity, module mismatch, existing gadget/controller,
malformed tty device number, host absence/disconnect and accidental default-mode
changes must fail safely or preserve the ordinary guard behavior as specified.

### Task 1: Implement and test the diagnostic startup

Files: ramboot/{startup-guard.sh,usb-log-init,usb-log.sh},
tests/{test_startup_guard.py,test_usb_log.py}.

- [ ] Test identity-only acceptance of force-normal with unchanged ordinary
  rejection; test the exact USB-only module prefix. Observe RED, implement.
- [ ] Test gadget setup with safe filesystem/command substitutes: expected UDC,
  no preexisting gadget, one ACM function and validated tty node. Wrong identity,
  existing gadget, missing UDC, failed mount and malformed tty must stop. Observe
  RED, implement minimal shell code and keep PID 1 separate from the writer.
- [ ] Test ordinary-host execution refusal. Verify writer startup is asynchronous
  with a FIFO lacking a reader; test log streaming/retry with harmless files.
  Run existing startup tests and the full host suite; expect all executed tests
  green. Commit the startup/source tests.

### Task 2: Package and qualify offline

Files: tools/assemble_ramdisk.py, tests/test_assemble_ramdisk.py, README.md and
docs/RAM_USB_LOG.md.

- [ ] Add failing explicit-mode packaging tests: default mode unchanged,
  diagnostic entrypoint/libraries selected, only 25 USB prefix modules loaded,
  no storage/hardware manifests or handoff. Observe RED then implement selection.
- [ ] Run complete host suite and actual ARM64 BusyBox shell checks under QEMU
  with safe substitutes. Verify utility applets; no privileged host operations.
- [ ] Clone committed source into a fresh private native build directory. Build
  two deterministic diagnostic CPIOs, audit, gzip deterministically and wrap with
  the existing pinned legacy-v2 tools/reference. Verify unchanged kernel/DTB,
  input/source hashes, image size and default recovery candidate unchanged.
- [ ] Review source, document actual checks/limits, commit/publish source and
  record private job/artifact evidence. Leave hardware launch unqualified.
