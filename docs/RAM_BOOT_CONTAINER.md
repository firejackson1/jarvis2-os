# Private RAM boot-container checkpoint

A complete legacy-v2 RAM candidate now packages the new guarded ARM64 recovery.
It was built and unpacked twice with identical bytes. The first authorized RAM
launch was accepted by Fastboot but did not reach Recovery. No flash, wipe or
slot-change command was issued. This is not a signed installable recovery or a
public binary release.

## Placement review and corrected inference

The earlier header-only review found that a 20.3 MB ramdisk would overlap the
DTB if placed directly at the header's old ramdisk address. That did **not**
establish how stock U-Boot actually places it.

The related S7D vendor tree at `2576f54b9e8068b8e1eef1756c6ca5933042c3a5`
(`https://git.odroid.com/yocto/uboot`) selects `boot/amlimage-android.c` when
`CONFIG_AMLOGIC_MODIFY` is enabled. Its legacy-v2 ramdisk reader returns the
offset inside the downloaded image; the header address is printed, not used as
that reader's destination. `boot/bootm.c` subsequently calls
`boot_ramdisk_high()` in `boot/image-board.c`, which allocates using LMB and
`initrd_high`. This differs from the direct-address assumption.

Two saved stock environment records, each with a valid 64 KiB CRC, agree on
`initrd_high=1f800000` and `bootm_size=c0000000`. The matching saved DTB has no
fixed enabled reservation overlapping the simple page-aligned allocation
prediction below that limit. Its framebuffer reservation starts at the limit.
The static DTB leaves RAM `reg` for bootloader fixup, and dynamic reservations
also exist. These checks support a candidate; they are not proof that the onn's
packed BL33 is binary-equivalent to this source, that its runtime environment
matches the saved capture, or that LMB chooses the predicted address.

The packer therefore retains the proven reference image's fields rather than
inventing a new fixed destination. Stock relocation, runtime FDT fixups and the
actual handoff remain hardware gates. The previous gap observation is retained
as a conditional concern, not described as a confirmed device failure.

## Exact package

| Input/output | SHA256 |
| --- | --- |
| Previously booted legacy-v2 reference | `a658e498917bf68f276b54117eb94004247e4c8e76035458fa2dba5b247d127f` |
| Unchanged stock kernel payload | `d9ef1096d33fe9f431f4d0cb54f5604a57f5f2fd41b2b86e7c9d499b1571dbae` |
| Unchanged stock DTB | `1542247558722727962aadeb648c855845cd1f9e5c391c70658650a0c92cca2d` |
| New guarded gzip ramdisk | `3a6f46222a6d5931905357ec1ff30d5d8d254a042948178d4daf4cd2286d4a35` |
| RAM boot image, 41,138,176 bytes | `d2fb4d1a5b24685ba8ca1c994ddb83d5e7a47d32387f8af6e03338b772cf198b` |

The only changed recognized header field is the command line:
`rdinit=/ramboot-init panic=0`. The prelude overrides ordinary init; a kernel
panic should retain diagnostics instead of the reference's five-second restart.
This does not claim that Android services or the stock bootloader can never
request a reboot. All other recognized fields and the kernel/DTB payloads match
after unpacking. The original reference's old ramdisk is absent from the result.

The executed packaging used AOSP mkbootimg revision
`4a27dd13adf9846e12d585d6fe99a375ebb58396`, pinned in `platform-manifest.xml`.
The tool-source hashes were:

- `mkbootimg.py`: `37d84b3d162e0bc62e36c1f4e1c63c85ea0caa9f29be023eb2f8efe006ad948c`.
- `unpack_bootimg.py`: `06b54dd9a07c5281778e29e234e76f6e3faee8bf0c904a5ef88fdee30eeed12e`.

The image fits the 128 MiB download budget, freshly verified in the first
hardware attempt below. Re-extracting its ramdisk reproduced the
guarded CPIO hash from `GUARDED_RAMDISK.md`, with no credential findings or base
record overwrites. The reference and unpacked input userspace stay private;
they can contain earlier development state and are not release assets.

## Offline packer

`tools/pack_ramboot.py` requires four lowercase SHA256 bindings in a private
JSON: `reference_boot`, `ramdisk`, `kernel`, `dtb`. It accepts only the reviewed
v2/page-size/init-command reference, rejects unreviewed fields, verifies a real
AOSP round trip, removes an output that fails verification/budget checks and
checks that original inputs remain unchanged. It has no device operations.

```sh
python3 tools/pack_ramboot.py \
  --android-tools /path/to/android/system/tools/mkbootimg \
  --reference-boot /private/proven-reference.img \
  --ramdisk /private/guarded.cpio.gz --bindings /private/bindings.json \
  --output /private/fresh-ramboot-output --max-download-bytes 134217728
```

The host suite passed 61 Python tests plus three native executable tests and
pinned-header syntax checks, including actual synthetic v2/v4 AOSP packing.
The executed candidate was independently repacked twice, with identical output.
That is packaging reproducibility. An independent empty-output platform rebuild
also completed with a byte-identical native ramdisk; see BUILD_CHECKPOINT.md.

## Additional startup inspection

The effective image contains only the reviewed main recovery init, owned USB
profile, recovery servicemanager definition and ueventd rules. The latter's
vendor/odm imports are absent RAM paths. Only the RAM-only recovery fstab is
present. The pinned fs_mgr selects that file in recovery; the pinned first-stage
init skips Android partition mounts in recovery mode. No default property
overrides `ro.boot.init_rc`. Bootloader-injected overrides still require checking.

An offline check found a candidate provider for every required strong dynamic
symbol and version across all 88 native ELF objects, following their recorded
dependency groups and linker exports. No distinct ambiguous library candidates
were found. The initial inspection script misparsed GNU readelf's multiword
OS-specific IFUNC type; correcting that parser resolved its false missing-libc
reports without changing any binary. This check does not qualify Android linker
namespaces, dlopen behavior, CPU-specific IFUNC execution or runtime SELinux.

## First hardware attempt

The owner authorized a RAM test and manually entered bootloader Fastboot.
Read-only queries identified the expected device/model, selected slot A,
unlocked state, `is-userspace: no`, and `max-download-size: 0x08000000`.
This bootloader returned “Variable not implemented” for both slots' successful,
unbootable and retry fields and for snapshot status, despite returning process
exit code zero. Those fields remain unknown; they were not treated as healthy
or as “no snapshot.” No fresh partition-hash baseline was obtained.

The exact image above was rehashed before `fastboot boot`. Transfer completed
in 10.044 seconds and Fastboot acknowledged boot. The owner then reported the
onn logo, with no recovery menu. USB disconnected and no ADB appeared. No UART
adapter was available on the host, so there is no startup trace proving kernel
entry, the guard stage, read-only protection or Android-init handoff. A visible
logo and a successful Fastboot acknowledgement do not establish those results.

The owner power-cycled with Reset released to discard the RAM image. Android
subsequently returned: authenticated network ADB reported boot completion and
slot suffix `_a`. Root debugging was available for read-only diagnostics, but
`/sys/fs/pstore` contained no retained files. The failure stage remains unknown.
No flashing, wipe, slot switch or saved environment change was requested.
No partition-integrity claim is made without qualified before/after reads.

## Hardware test requirements

Before requesting a launch, bind this exact image to a current read-only
preflight and explicit return plan:

1. Verify model/identity, current slot, successful-boot flags/retries, unlock state,
   snapshot/merge state and the actual USB transport/download budget. Stop on an
   unexpected state. Do not change a slot or cancel a snapshot.
2. Check current boot arguments for first-stage/init overrides. Verify retained
   current-slot restore files and their AVB relationships. Capture protected
   partition hashes in a quiescent environment where the available transport
   permits it; do not claim a baseline if root access or a hash read fails.
3. Record the current stock-Recovery root-shell failure as unresolved. Do not
   bypass it by touching slot B or flashing another helper. Identify the actual
   available read-only/return path before a launch.
4. With authorization for the reboot and RAM launch, keep UART recording, use
   the exact image, and look for the early guard marker/read-only result before
   accepting a visible menu as success. Test display/button/USB and return to
   Android separately; compare protected hashes afterward where qualified.
5. If the RAM image stalls, power-cycle with Reset released to discard it. The
   intended return is the already-selected Android slot, not a slot switch or
   restore flash. Do not promise that route without checking the current slot's
   state first. Remain available for a physical power-cycle during the test.

Normal bootloader boot-control bookkeeping may occur before the RAM guard runs;
the guard is not proof that the entire firmware boot chain performs zero writes.
No partition-writing command or persistent bootloader/environment modification
is part of this candidate test. A tested install-capable recovery and normal-user
installation/restore rehearsal are still required for the public ROM.
