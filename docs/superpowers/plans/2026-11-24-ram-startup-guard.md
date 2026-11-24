# RAM startup guard implementation plan

> Execute inline with `superpowers:executing-plans`. No sub-agents. Keep the
> existing platform build and frozen source inputs intact while it is running.

**Goal:** Prepare and verify an early internal-storage guard before a concrete
RAM boot test of the new custom recovery.

**Spec:** `docs/superpowers/specs/2026-11-24-ram-startup-guard.md`.

**Architecture:** Reuse the proven RAM Linux utility/module prelude, reduce its
runtime inputs, then hand off to the new Android init after verified block
protection. Inspect the complete generated ramdisk before packaging it.

## Global constraints

- No device action, partition write, slot change or desktop interruption.
- Keep owner keys, stock binaries and runtime inputs outside Git.
- Do not treat a source check, host mock or packed image as hardware validation.
- Do not silently replace the new recovery with the earlier Linux shell image.

## Review focus

- No helper runs after a failed or incomplete storage scan.
- The whole eMMC device, boot devices and late partitions are covered.
- Utility ELF interpreters and libraries do not require Android storage mounts.
- Temporary mount handling does not bypass or break the intended Android init.
- BCB and logging behavior cannot resume a pending install during the RAM test.

## Task 1: Bind the actual launch inputs

- [x] Inspect the saved DTB offline and record its exact board compatible value.
- [x] Inventory the saved vendor ramdisk's module paths, ELF architectures and
      hashes against the previously working pre-MMC module sequence.
- [x] Inspect the earlier utility runtime's ELF interpreter/library closure.
- [ ] Inspect the newly built Android ramdisk's init, fstab, imports and policy.

Expected: a private input receipt, no extracted binaries in the source tree,
and unresolved dependencies stated explicitly. The earlier ARM32 init and
new ARM64 recovery must not be assumed interchangeable.

The offline receipt identifies 27 pre-MMC modules in the saved vendor ramdisk,
all AArch64 relocatable ELF objects. Their uniform vermagic is
`5.15.196-android14-11-g570709ea67dc SMP preempt mod_unload modversions aarch64`.
This is an input inventory, not a module ABI/signature/load test. No module was
executed or copied into the public source tree.

The earlier BusyBox is dynamically linked AArch64, not static. Its interpreter
is `/lib/ld-musl-aarch64.so.1`; its only needed library,
`libc.musl-aarch64.so.1`, is a symlink to that loader. The loader has no further
`DT_NEEDED` entries. Required applets and shell syntax were checked with
unprivileged QEMU AArch64 execution. This establishes the inspected utility
closure, not the ability to load modules, set block flags or start Android init.
Private runtime hashes are recorded outside Git; binary redistribution and
corresponding source obligations remain uncleared.

## Task 2: Implement and test the guard

- [ ] Add a failing host test for each failure class in the spec before changing
      the reused guard. Use temporary fixtures and safe command substitutes;
      never invoke host block, module-loading or mount operations.
- [ ] Retain only the bootstrap utility commands and known module sequence.
- [ ] Add board/root/PID checks, complete node verification and a fail-closed
      handoff. Keep diagnostic state in RAM.
- [ ] Run the complete host suite and a separate review against the spec.

Expected: tests fail for the actual missing behavior, then pass with the guard;
no hardware-safe claim or new image installation is implied.

`ramboot/storage-guard.sh` provides internal MMC
enumeration, verified read-only block operations and a second inventory check.
Its initial host tests failed before the library existed; an additional test
failed before exact read-only readback handling was added. Tests use temporary
sysfs fixtures and safe command substitutes. Additional regression cases cover
removed/renumbered nodes and symlink rejection. The suite also runs under the
inspected ARM64 BusyBox shell through QEMU.

`ramboot/init` now provides the PID 1 entrypoint and private RAM state setup;
`startup-guard.sh` supplies minimal proc/sys views, board/kernel checks, the
reviewed hashed module sequence, bounded storage discovery and mount cleanup.
All hashes and ordered names are checked before the first `insmod`. No later
gate or Android handoff is reached after a failure. Ordinary host execution is
rejected before using BusyBox; failure in PID 1 waits with RAM diagnostics.
An EXIT trap also prevents a failed Android-init exec from simply exiting PID 1.

Ruling: board identity needs sysfs to be visible. Only read-only proc/sys views
are mounted after PID/RAM-root checks and before board/kernel checks. Module
loading and storage access remain behind the identity checks. The pinned
Android first stage mounts proc/sys itself, so the prelude unmounts its views
before handoff. This is a source-based preparation, not a hardware validation.

Ten startup tests cover host refusal, ordered hash verification, missing/changed/
reordered/extra module inputs, load failure, board/kernel/boot-mode rejection,
mount failures, bounded discovery, cleanup failure and success/failure workflow
gates. They use safe command substitutes and also pass under the inspected
ARM64 BusyBox shell through QEMU. No host module or mount operation is executed.

The prelude is not included in the frozen platform build or an assembled RAM
image yet. Its exact kernel-release input, proc/bootconfig behavior, init
dependency closure, diagnostic arguments/fstab and complete ramdisk still need
binding and inspection. Kernel module loading is not itself time-bounded.
Task completion and hardware safety remain unproven until those checks pass.

Additional source finding: whole-device BLKROSET is not proof of disk-wide
protection for a future partition. The guard therefore requires a complete
preflight partition-number set and refuses incomplete/unexpected discovery
before any protection call. Three added test cases first reproduced missing,
partial, malformed, duplicate and symlinked inventory acceptance, then passed
after the gate was added. The manifest must come from a matching complete
read-only capture; the retained installer backup inventory covers only a subset
and must not be promoted into this input by guessing.

## Task 3: Package and qualify the RAM image

Preparation: the archive inspector now retains original entry payloads and
newc link identity, resolves regular-file hard links and models ordinary-file
updates versus link replacement across layers. Credential checks inspect all
input payloads, including data overwritten by another entry or layer. Host
tests passed after reproducing the missing behavior first. A regression audit
of the saved older ARM32 archives preserved their entrypoint/ELF/init/policy
inventory; this is not an audit of the pending Android 17 output. Original CPIO
byte streams must remain intact when packaging; the report is not a serializer.

Offline checkpoint: the full native ARM64 build completed. A checksum-bound
diagnostic CPIO derivative changes only the reviewed init import/arguments,
RAM-only fstab and unresolved standard ADB trust symlink. Original record spans
allow surgical edits; all untouched records remain byte-identical. Seven new
host tests reproduced the missing preparer and ambiguous import/service gates
before passing; the complete suite passed 46 Python tests plus three native C++
executables and pinned-header syntax checks. The actual derivative's strict
credential audit is clean; it is not a complete guarded image. See
`docs/DIAGNOSTIC_FRAGMENT.md` for hashes and open assembly requirements.

The stock boot container now binds the actual kernel release independently of
module vermagic. Their release prefixes differ. All 52 retained stock modules
contain version-check sections; actual symbol compatibility/signature acceptance
is still unproven. No kernel or module was altered to hide this mismatch.

- [ ] Use the actual new recovery ramdisk and compatible verified kernel inputs.
- [ ] Preserve archive metadata/overlays, validate effective entrypoints and
      utility dependencies, and reject oversized or mismatched inputs.
- [ ] Bind the image and preflight/return procedure to exact hashes.
- [ ] Obtain authorization for that concrete RAM launch before any device action.
- [ ] Record actual display/input/ADB, storage protection and Android return
      evidence; keep public binary release held until its other gates pass.
