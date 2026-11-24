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

Partial implementation: `ramboot/storage-guard.sh` provides only internal MMC
enumeration, verified read-only block operations and a second inventory check.
Its initial host tests failed before the library existed; an additional test
failed before exact read-only readback handling was added. Tests use temporary
sysfs fixtures and safe command substitutes. Additional regression cases cover
removed/renumbered nodes and symlink rejection. The suite also runs under the
inspected ARM64 BusyBox shell through QEMU.

This library is not an executable PID 1 launcher and is not in the running
platform build. Board/PID/root validation, module loading, private RAM-backed
directory setup, bounded discovery and Android-init handoff are still missing.
The task remains incomplete until those parts and the generated ramdisk audit
are implemented and checked.

## Task 3: Package and qualify the RAM image

- [ ] Use the actual new recovery ramdisk and compatible verified kernel inputs.
- [ ] Preserve archive metadata/overlays, validate effective entrypoints and
      utility dependencies, and reject oversized or mismatched inputs.
- [ ] Bind the image and preflight/return procedure to exact hashes.
- [ ] Obtain authorization for that concrete RAM launch before any device action.
- [ ] Record actual display/input/ADB, storage protection and Android return
      evidence; keep public binary release held until its other gates pass.
