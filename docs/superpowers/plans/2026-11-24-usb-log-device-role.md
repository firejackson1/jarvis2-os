# USB log device-role correction

> Execute inline with superpowers:executing-plans under the owner's standing
> delegation. This task builds offline; it does not authorize a hardware reboot.

**Goal:** Ensure the one-way USB diagnostic registers its peripheral controller
even when the vendor module initially selects the host-only DT default.

**Design:** Keep the existing loader and default recovery byte-for-byte. In USB
log setup, first refuse any existing gadget configuration. If no UDC exists,
mount debugfs privately in RAM, require notg-host from the verified vendor mode
control, request device mode and verify notg-device plus the exact UDC within a
bounded wait. Remove the private debugfs view before building the ACM gadget.
Use shell and the existing Python unittest harness; add no dependencies.

**Ruling:** An initial insertion-parameter policy passed host tests, but exact
module init calls a GKI hook before USB initialization. Related hook source
replays boot arguments and may overwrite that parameter. Withdrew that approach
before commit/build; use the runtime control already proved on this device.

**Evidence:** Live Android requested mtp,adb but had no UDC and had an xHCI child
under the dual-role controller. Its parameter was false and DT controller-type
was 1. Retained module probe disassembly selects the host branch for that
combination and the gadget branch for force_device_mode true. Runtime debugfs
device mode exposed USB ADB on the same cable; the test restored host mode.
The module's loaded build-ID note matched the retained note. Complete loaded
file bytes and the failed RAM launch arguments have not been newly measured.

**Checks / task:**

- [x] Add a failing regression for absent-UDC recovery, private-mount cleanup
  and no mutation of an existing gadget/configuration or private path.
- [x] Implement the narrow runtime role selection; retain the default recovery
  loader and entrypoint, ordered module checks and one-way writer behavior.
- [ ] Run host tests and ARM64 BusyBox checks with privileged commands safely
  substituted. Review policy scope and negative paths.
- [ ] Build two fresh deterministic private diagnostic images; verify unchanged
  kernel, DTB, module bytes and previous candidates, and document exact evidence.
- [ ] Commit/publish source; leave hardware enumeration and recovery qualification
  open until a separately authorized test with a return path.
