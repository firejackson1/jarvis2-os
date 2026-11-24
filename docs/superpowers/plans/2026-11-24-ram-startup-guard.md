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

Ruling: the native fragment also needs display/input drivers after MMC protection.
Use the remaining dependency closure of the saved `amlogic-input` and `aml_drm`
modules, in stock recovery load order: ten modules. Verify their complete ordered
hash manifest before loading any of them, then recheck storage protection before
Android init. This preserves the original 27-module pre-MMC sequence; it does not
load camera/watchdog modules or run the stock hardware script's closed services.
Loading kernel drivers is not claimed free of all device side effects; block
protection and hardware verification remain required.

Assembly uses a separate deterministic newc overlay after the preserved native
CPIO. Place BusyBox at canonical `system/bin/busybox`, its existing inspected musl
closure at root `lib`, and all modules under `ramboot/modules`, not `/lib/modules`.
The pinned first-stage init skips automatic module loading when `/lib/modules`
is absent and recognizes recovery by `/system/bin/recovery`. The owned USB profile
sets configfs/controller before `fs` and selects ADB at `boot`; generic upstream
rules own the gadget. Controller `fe350000.crgudc` is supported by the retained
working recovery properties and matching DTB; do not copy the stale stock role
path `ffe09000.usb-role-switch`. No new authentication property is introduced.

The offline assembler must bind every private input by SHA256, reject path/type
collisions in the effective overlay, check both module sequences against stock
dependencies, audit the combined CPIO and preserve its base bytes exactly.
Its report must leave runtime dependency/SELinux/hardware qualification open.

Executed checkpoint: the private native guarded CPIO is assembled, 60,512,820
bytes, SHA256 `4155440d652f8a2691a416ad4293839394321d35f1ec3888b599e52fea3b8c26`.
The complete source suite passed 56 Python tests, three native executables and
pinned-header syntax; 28 guard tests passed under the actual ARM64 BusyBox/QEMU.
Safe substitutes were used for all privileged operations. The new assembler and
hardware workflow gates were reproduced failing first. Actual stock module
dependencies satisfy the two ordered lists. Private inputs/report and the
unmodified base bytes were verified. No hardware action or flash occurred.

Ruling: the earlier legacy-v2 header's declared ramdisk-to-DTB gap is only
15,728,640 bytes; the new gzip payload is 20,299,793 bytes. Do not copy that load
layout into a candidate hardware launch. Check actual bootloader relocation and
nonoverlapping RAM regions first. A valid CPIO and total download-size check alone
do not establish a valid boot-container memory layout.

Follow-up ruling from source inspection: the related S7D vendor implementation
uses `boot/amlimage-android.c`, selected by `CONFIG_AMLOGIC_MODIFY`, rather than
the generic parser. For legacy images its ramdisk reader returns the source
offset inside the downloaded image; the header's ramdisk address is printed but
is not that reader's destination. `boot_ramdisk_high` subsequently uses LMB and
`initrd_high`. Two CRC-valid saved stock environment records agree on
`initrd_high=1f800000`. The prior header-only spacing observation is therefore a
potential overlap under direct loading, not proof of a stock failure. The
related source is not binary-equivalent proof of the onn's packed stock BL33.

Next offline package step: retain the proven reference image's v2 fields and
exact kernel/DTB, replace only its ramdisk using pinned AOSP tools, and set
explicit `rdinit=/ramboot-init panic=0`. Bind all inputs and verify the unpacked
output and download budget. Do not invent a new fixed destination based on the
header-only concern. Keep relocation, runtime FDT fixups, startup and hardware
qualification open in the resulting private candidate report. No boot command
belongs in this packaging tool.

Executed checkpoint: the private legacy-v2 candidate is 41,138,176 bytes,
SHA256 `d2fb4d1a5b24685ba8ca1c994ddb83d5e7a47d32387f8af6e03338b772cf198b`.
Two AOSP packing runs produced identical bytes; extracted kernel/DTB and guarded
CPIO match exact inputs. The only intentionally changed recognized header field
is command line (`panic=0`). Five new real-AOSP fixture tests first failed before
the packer existed, then passed, including rejection and budget cleanup; a report
regression reproduced an overly broad unchanged-header claim and now explicitly
identifies the command-line exception. Complete suite: 61 Python tests plus three
native executables and pinned-header syntax. No device action occurred.

Operational ruling: use the currently freed build memory for an independent
native recovery rebuild in an empty output directory bound at the same path
inside a private mount namespace. This avoids changing embedded output-path
strings and preserves the original output tree. A fresh all-project audit passed
with exactly the five expected patched projects. Use an owned 8 GiB swap file,
24 GiB memory-high/28 GiB maximum/16 GiB swap maximum, a 12 GiB filesystem reserve
and the existing 64 GiB thin-pool reserve. Scope the return watcher to the exact
build invocation; after it exits, reclaim only this task's verified swap and
restore Bazzite. This is an active reproduction check, not a completed result.

Resource follow-up: active Soong graph analysis filled nearly all initial swap
without an OOM. Preserve the same running build; add a second owned 8 GiB swap
file, raise memory-high to 26 GiB and swap maximum to 24 GiB, retaining the
28 GiB memory maximum and both storage reserves. Replace only the return watcher
with a version that reclaims both identity-bound task files before Bazzite starts.
Verify the replacement watcher is live against the unchanged build invocation.
