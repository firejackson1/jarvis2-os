# Read-only RAM launch preparation

This implements the owner's RAM-only development constraint. It does not
authorize a reboot, flash, slot change or hardware launch. The new recovery has
not booted. The complete Android 17 ramdisk has built; its startup review,
guarded RAM assembly and hardware validation remain pending.

## Intent and constraints

Upstream Recovery can rewrite or clear the BCB before a menu selection. The
diagnostic image must protect internal storage before Android init starts,
avoid pending install commands, and keep its state in RAM. Hiding wipe actions
is insufficient. See `docs/RAM_STARTUP_AUDIT.md` for the inspected call paths.

The saved working device's DTB has root compatible string
`s7d_s905x5m_bm201-3g`. Its 83,220-byte DTB SHA256 is
`1542247558722727962aadeb648c855845cd1f9e5c391c70658650a0c92cca2d`.
These were read offline, not discovered by a new hardware test. Reject an
unexpected board before attempting storage protection.

Keep the known kernel, DTB and compatible modules. Do not rebuild or substitute
a kernel to make the guard work. No userdata, metadata or cache mount is needed
for this diagnostic boot. Bluetooth pairing state must also remain in RAM.

## Approaches and implementation choice

- A service in ordinary recovery init runs too late to cover first-stage init
  and earlier startup side effects; it cannot be the primary guard.
- A new static native PID 1 helper avoids an extra runtime, but introduces new
  privileged module-loading, device-node and mount code to qualify.
- Reusing the working RAM Linux prototype's utility runtime and module/storage
  sequence preserves a hardware-tested starting point. It still needs an
  interpreter/library audit and a new handoff to Android init.

Implementation choice delegated to the builder: start from the existing RAM
Linux prelude, retain only the required utility runtime, and hand off to the
actual new Android recovery init. Do not copy its SSH server, authorization
keys, networking setup or complete Linux root filesystem. The older prototype
does not establish that BusyBox is static; inspect its ELF interpreter and
dependencies before selecting runtime inputs.

## Required behavior

1. Refuse ordinary host execution. Validate PID 1 and a RAM-backed root before
   creating private RAM state. Mount only read-only proc/sys views needed to
   inspect the board and kernel, then validate their exact identities before
   loading modules or accessing storage. No Android filesystem is mounted.
2. Load only the reviewed, hashed, known-kernel module sequence needed to expose
   eMMC. No Android init/service may run before protection succeeds.
3. Identify internal MMC through sysfs device type and identity. Protect the
   whole device and all visible partitions and boot block devices, verify their
   read-only state, and detect nodes appearing during enumeration. Do not match
   an unrelated disk merely by a common name prefix. Require the complete
   expected physical partition set from a matching read-only preflight capture,
   not a subset inferred from backed-up images. Do not assume whole-device
   BLKROSET protects a partition appearing after the scan.
4. Missing devices, malformed metadata, module failure, failed read-only
   verification or an incomplete scan must prevent the Android-init handoff.
   A bounded wait is permitted for device discovery. No failure path writes BCB
   state or clears an Android recovery request.
5. Audit temporary mounts and their cleanup against the pinned first-stage
   init. Supply controlled recovery arguments and a diagnostic fstab that does
   not mount Android storage. Resolve the prototype metadata fstab mismatch.
6. Keep diagnostics in RAM and record the protection result. Root block flags
   protect normal block I/O; they are not a security boundary against a
   privileged process deliberately clearing them or issuing raw device commands.
7. Build a private RAM image only after inspecting the complete assembled
   ramdisk. Preserve CPIO hardlinks and overlay ordering, check the known
   Fastboot image size budget, and require a concrete authorized hardware test.

## Evidence required before claiming a working guard

Host tests must cover the internal/external distinction, aliases and boot
devices, missing nodes, partial protection, failed verification and a late
partition. They must never use host block devices or privileged mounts.

Offline evidence must bind kernel/DTB/modules/runtime/ramdisk hashes, demonstrate
the complete startup dependency and init-import graph, and show that no owner
keys were included. Hardware evidence must then show the early guard result,
display/input/ADB behavior, partition state before and after the RAM session,
and return to Android. A pending BCB request may survive a protected session;
the preflight and reboot test must account for that rather than clearing it
silently.

The guard belongs to the diagnostic RAM launch. An installed, update-capable
custom recovery needs separately reviewed write authorization and installation
behavior; permanently blocking all writes would not satisfy that requirement.
