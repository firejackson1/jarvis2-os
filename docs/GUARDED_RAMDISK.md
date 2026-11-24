# Guarded RAM recovery assembly

The actual native ARM64 recovery and reviewed diagnostic changes have now been
assembled with the early guard, utility runtime and stock hardware modules.
This is a private concatenated CPIO, not a launchable boot container. It has not
booted, changed device storage or passed runtime SELinux/linker qualification.

## Assembly inputs and behavior

`tools/assemble_ramdisk.py` appends a deterministic newc overlay after the entire
unchanged diagnostic CPIO. It never extracts/reconstructs that base archive.
All private files require exact SHA256 bindings. The tool rejects an unaligned
base, mixed-architecture init, wrong utility/module architectures, invalid
partition numbers, missing/reordered module dependencies and overlay collisions.
No device command or privileged module/mount/block operation runs on the host.

The overlay supplies:

- `/ramboot-init`, the PID 1 prelude, guard libraries and owned hardware init file.
- BusyBox at `/system/bin/busybox`, preserving the native `/bin` symlink.
- The inspected AArch64 musl interpreter and its libc symlink at root `/lib`.
- Exact kernel release and captured physical partition-number inputs.
- 27 pre-MMC modules and their ordered SHA256 manifest under `/ramboot`.
- Ten additional display/input dependency modules and a separate ordered manifest.

The ten additional modules follow stock recovery load order and dependency
metadata: `amlogic-efuse-unifykey`, `tee`, `amlogic-tee`, `videobuf-core`,
`dvb-core`, `amlogic-pm`, `amlogic-input`, `amlogic-dvb`, `aml_media`, `aml_drm`.
They load only after MMC protection succeeds. Every hardware-module hash is
checked before the first hardware load, and storage protection is checked again
before mount cleanup and Android-init handoff. A failure stops the handoff.
Kernel module initialization itself has not been qualified by a new hardware test.

No `/lib/modules` directory is introduced. The pinned first-stage init skips
automatic module loading when that directory is absent and identifies recovery
by the presence of `/system/bin/recovery`. The owned USB init profile sets
configfs and controller `fe350000.crgudc` during `early-init`, then selects ADB
at `boot`. Generic upstream recovery rules create and bind the gadget. It does
not import stock closed services, write unifykeys controls, create bootloader/DTB
aliases or change authentication properties. The retained Android 14 host init
verifier accepted this small profile; that is a syntax check, not Android 17
execution or actual USB validation.

## Reproduce offline

Create a private input JSON containing `kernel_release` as an exact string, and
each of `busybox`, `musl_loader`, `mmc_partitions`, `platform_cpio` as an object
with absolute `path` and lowercase `sha256` fields. The platform input is the
saved modules CPIO, not the old ARM32 recovery userspace. Do not include keys,
SSH services, Android userdata or an entire Linux root filesystem.

```sh
python3 tools/assemble_ramdisk.py \
  --diagnostic-cpio /private/diagnostic.cpio \
  --expected-input-sha256 EXACT_DIAGNOSTIC_SHA256 \
  --inputs /private/assembly-inputs.json \
  --output /private/fresh-guard-output
```

The result is `guarded.cpio` plus an input/source/architecture report. Utility
ELF architecture alone does not establish its dependency closure. The executed
assembly uses the separately inspected BusyBox/musl pair; their source and
redistribution obligations remain unresolved. No binary is committed or released.

## Executed artifact

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Guarded CPIO | 60,512,820 | `4155440d652f8a2691a416ad4293839394321d35f1ec3888b599e52fea3b8c26` |
| Overlay alone | — | `f2e04971b6f935d77002d1cc0f6321755c176f8a4d160fb5153b444be7187a2b` |
| gzip level 9, timestamp zero | 20,299,793 | `3a6f46222a6d5931905357ec1ff30d5d8d254a042948178d4daf4cd2286d4a35` |

The effective archive audit found 467 entries, 127 AArch64 ELFs, no overwritten
base records and no blocked credential artifacts. The original diagnostic bytes
remain the exact prefix. The policy format in the new native recovery is version
30, matching the retained stock policy format; kernel loading and access behavior
are still untested. Exact stock-kernel IKCONFIG extraction confirms configfs,
FunctionFS, USB HID and SELinux support; feature presence does not prove the
controller or UI works in this new userspace.

The expected partition file now comes from a retained full kernel enumeration
of physical partitions 1 through 31 and both MMC boot devices. Its associated
saved RAM image has the exact same kernel payload as the retained current-A boot
capture. An independent recent recovery inventory from the same device has the
same named physical-number set. This is historical evidence, not a fresh capture
or proof that the current GPT is unchanged. The guard still requires the exact
set and stable node identities at launch. Manifest SHA256:
`df63c2a139e620603fed9fb87b69b4cbcec41f4f0d3c65b7f48f544d86b7bddc`.

Host verification passed 56 Python tests, three native C++ executable tests and
pinned upstream-header syntax checks. All 28 guard tests also passed under the
actual inspected AArch64 BusyBox through QEMU, with safe substitutes for every
privileged operation. This does not test module insertion, block protection or
PID 1 on hardware.

## Boot-container memory layout hold

The earlier working legacy-v2 image declares ramdisk address `0x01000000`, DTB
address `0x01f00000` and kernel address `0x02080000`. Its space before the DTB is
15,728,640 bytes. This new compressed ramdisk is 20,299,793 bytes, so those
declared regions overlap if reused unchanged. Do not blindly reuse that layout.
This was a conditional direct-load concern, not a proven stock collision.
The [subsequent vendor-source and environment review](RAM_BOOT_CONTAINER.md)
found a legacy-image source-offset reader and LMB relocation. A complete private
candidate now retains the proven reference fields; exact stock relocation and
runtime FDT behavior remain unverified. The overall download-size limit is a
separate check.

Remaining gates include that container layout, the complete effective init/import
and linker/policy behavior, a current preflight/return plan, authorized RAM boot,
early guard evidence, HDMI/button/USB checks and before/after partition hashes.
An install-capable signed recovery remains separate work; the diagnostic guard
must not become a permanent substitute for installation and restore functions.
