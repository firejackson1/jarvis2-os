<!-- SPDX-License-Identifier: Apache-2.0 -->
# Recovery raw writer — offline development only

`tools/install-candidate.py` is **unqualified development code**. It has been
exercised only with file-backed fake ADB devices. Do not run it against hardware
without a separate reviewed qualification and explicit installation approval.
No installation, slot change, wipe, recovery entry or publication is authorized
by this document. Public candidate packaging does not establish installation safety.

The tool defaults to dry-run. Dry-run performs recovery checks and may create
read-only RAM device-mapper tables and a durable host journal; it does not write
persistent device blocks. `--execute` is the only path to persistent target writes.
It never invokes fastboot, a logical resize, liblp writer, snapshot cancellation,
a filesystem mount, reboot, slot activation or wipe. It never provisions an empty
slot. Existing complete foundations for an explicit `--slot a` or `--slot b` are
required; an allocated other slot is not described as a verified bootable fallback.

## Prepare a verified LCARS ZIP locally

The host preflight takes the LCARS archive, the archive SHA-256 and the
expected AVB root public-key-blob SHA-256 from trusted release evidence. Use
Linux with Python 3.11 or later, Git, OpenSSL and `lz4`. Supply locally obtained
stock reference images from the pinned 15640252 profile, a Git checkout
containing the archive's Recovery source commit, and the prepared portable
tool kit. [Stock OTA extraction](STOCK_FOUNDATION.md) ·
[Portable LCARS kit](https://github.com/firejackson1/jarvis2-os/blob/708e088ed57eb83805753d9213717965a3c61e2c/docs/STOCK_LCARS.md#recreate-the-recovery-image-from-a-plug-in)

```sh
python3 tools/prepare-lcars-install.py \
  --archive /private/download/candidate.zip \
  --archive-sha256 <trusted-archive-sha256> \
  --root-public-key-sha256 <trusted-AVB-root-public-key-blob-sha256> \
  --stock-images /private/extracted-stock/images \
  --recovery-source /path/to/recovery-git-checkout \
  --tool-kit /private/prepared-tool-kit \
  --output /private/fresh-preflight
```

The preflight checks all archive members and the stock hashes, then exports
the pinned recipe from Git. It rebuilds `vendor_boot.img`, stages the matching
stock `init_boot.img`, and verifies the exact stock AVB graph, zero flags,
parent and child keys, and all required image bindings. The root must explicitly
bind the locally rebuilt Recovery file. Only after these checks does the tool
save the five `images/` members, the two `transition-images/` members and
verification reports. For LCARS format 3 it also copies the verified Recovery
notice archive to the output and records its digest. The tool defaults to
rejecting temporary-key archives.
`--allow-offline-rehearsal` allows host testing and retains its rehearsal label.

These files are inputs to the capture-bound procedure below. They do not
establish the current slot, layout, rollback backups or device authorization.
Obtain a fresh verified capture and exact restore set before preparing any
writer proof or performing an authorized device trial.

### Check a saved layout and restore files

Add these options to the same local preflight command:

```sh
--fit-slot a \
--fit-inputs /private/saved-capture \
--fit-capture-sha256 <trusted-capture-json-sha256> \
--fit-lpdump /tools/host/bin/lpdump \
--fit-lpdump-sha256 <trusted-lpdump-executable-sha256>
```

Keep `capture.json`, `super-prefix.img` and the seven files in `old-images/`
inside the private capture directory. Use the reviewed native `lpdump` with
its matching shared libraries. For the explicit target slot, preflight checks
both saved LP views, the allocated layout, each candidate and restore size,
each saved restore hash and every untouched stock-reference hash. It also checks
that the target extents start beyond the captured metadata prefix. A mismatch
stops preflight before it stages output.

The `saved_capture_fit` record binds the results to the capture, metadata and
tool hashes. This is an offline receipt for the saved state. Recovery transport,
capture freshness and device authorization are separate checks.

## Supported contract and prerequisites

A separate operator must qualify recovery transport and stage a reviewed native
`dmctl` executable in recovery RAM or a supported existing location. Its exact
path/hash is pinned by the capture. The writer does not stage that executable,
enter recovery or mount metadata. Cached ABI/dependency inspection alone does not
prove the helper executes in recovery; that remains an independent prerequisite.

Every preflight and write boundary requires the exact USB serial in `adb devices
-l` with explicit `device` or `recovery` state and a USB transport, matching `get-serialno`, UID0, the captured current slot,
a recovery process, no completed Android boot and no Android/update/snapuserd
processes. An existing process reported as `dd` also blocks all operations,
including resume and restore: a device-side writer may survive a lost USB shell.
The tool never kills it. Wait for independently verified writer quiescence before
retrying; absence of a host ADB command is not evidence that device I/O stopped.
The exact recovery `ps -A -o NAME` behavior must be qualified to expose the native
writer as `dd`. Busybox/wrapper forms reported under another name are unsupported
by this narrow guard and remain an explicit operator quiescence prerequisite.
No vendor-adbd child-termination behavior or generic process exclusion is assumed.
Explicit target slot is separate from current slot; no activation is
performed even when a complete inactive slot is selected.

`/metadata` must already be mounted from its verified physical partition as
F2FS, read-only, with `norecovery` or `disable_roll_forward` explicitly visible in
mountinfo. Unmounted, writable, wrong backing, unknown filesystem/options or
rollforward-enabled state fails closed. The metadata mount root must be `/`;
subdirectory binds and any nested mounts under `/metadata` are rejected because
they can hide persisted snapshot state. The writer does not attempt to repair
or obtain this state. Normal Android mounts metadata writable; observations there
are not a substitute for this recovery prerequisite.

Only these persisted OTA shapes are accepted under that verified mount:

- `/metadata/ota` absent;
- an empty real `/metadata/ota` directory;
- a real `/metadata/ota` directory containing only a real empty `snapshots/` directory.

Any state/lock/indicator file, symlink, snapshot content or unknown shape is
rejected. Missing state on this verified filesystem means None according to the
pinned snapshot implementation; a missing path on an unmounted filesystem proves
nothing. Fastbootd's HAL-only `snapshot-update-status:none` is not substituted
for persisted-state verification. No arbitrary protobuf state parser is provided.

The operator-pinned host ADB and native lpdump binaries must be supplied with
SHA256 pins. Native lpdump parses a fresh bounded super prefix read through
exec-out, with exact length/hash checks; mixed stderr or a partial capture fails.
The existing slot planner validates both native JSON/text views, complete target
allocation, sector geometry, linear extent bounds/overlaps and exact image budgets.
The live super identity/capacity must match those views. All target extents must
also lie beyond the entire captured protected prefix.

The live by-name resolution, major/minor, size and sysfs partition extents of
super and protected physical partitions are checked. Only disjoint partitions
on one verified parent disk are supported. Existing known linear maps matching
the fresh LP tables may remain; aliases of target partitions are checked by
major/minor against mountinfo. Unknown, nonlinear, verity, COW or snapshot maps
fail closed in this first increment. Normal verity maps need additional recovery
qualification rather than an invented capture-only validation. Existing foreign
maps are never deleted. Only matching operation-specific `j2i_...` linear maps
may be recreated writable; all map tables are cross-checked against the planner.

## Private capture and externally reviewed installation proof

There is deliberately no automatic capture-authoring or approval API. Assemble
and independently authenticate the evidence in a separate read-only procedure;
keep real serials and runtime captures private. Capture is JSON with these fields:

| Field | Required content |
|---|---|
| `format` | Literal integer1 |
| `serial`, `current_slot` | Exact USB identity and observed `a` or `b` |
| `super` | `path`, integer `major`, `minor`, `bytes` |
| `physical` | Complete inventory listed below; each record adds `sha256` to the super record shape |
| `metadata_prefix` | Exact `bytes` and `sha256`; sector-aligned, at most16MiB, covering both LP views and their backups |
| `logical_sha256` | Full hashes for every allocated logical partition in the native LP views; zero-extent entries omitted |
| `old_files` | Exactly five or seven restore-image records, each containing positive integer `bytes` and lowercase `sha256` |
| `dmctl` | Qualified recovery executable `path` and SHA256 |

The physical inventory is both A and B for `bootloader`, `boot`, `init_boot`, `vendor_boot`,
`dtbo`, `oem`, `odm_ext`, `vbmeta`, `vbmeta_system`, plus shared `misc` and `metadata`. Every record
is a real physical partition path and exact full hash/size, not a symlink or an
inferred slot alias. Capture after the recovery and read-only metadata state are
established: older Android-time metadata/misc hashes may legitimately differ and
must not be silently accepted. Preserve a complete independently verified restore
set externally; this tool only consumes the five/seven images it is allowed to write.
Bootloader partitions are protected by identity/size/geometry/hash checks only;
bootloader write or restore images are never accepted. On this model `dt_a` and
`dt_b` both alias `/dev/dtb`, a character/pseudodevice rather than distinct GPT
block partitions. These aliases are explicitly untargeted and outside this block
writer inventory. No DTB command, pseudo-device write or restore API is provided.

Candidate proof JSON must be externally reviewed and pinned by the caller, with:

```text
passed: true
avb_offline_verified: true
foundation_compatible: true
capture_sha256: <trusted exact capture file hash>
target_slot: a | b
files: {system.img, system_ext.img, product.img, vbmeta_system.img, vbmeta.img}
```

Each file record contains exactly `bytes` and `sha256`. These declarations require
independent AVB, reference/foundation, intended content/metadata and signing-key
review. The writer validates the proof pin and actual bytes; it does not turn
self-authored booleans into authenticated project trust or hardware acceptance.
The general packaging receipt alone is not this capture-bound installation proof.

Local old/new directories must contain exactly their declared regular raw files,
without symlink ancestry. Lengths/hashes must match; sparse input is rejected.
Write sizes must be unchanged and multiples of4096. Old restore bytes must match
the captured target hashes and freshly verified live old state before a new run.

The five-image owner-compatible route preserves existing bootstrap/recovery.
A stock-compatible public candidate installed over custom bootstrap requires an
explicit separately pinned transition proof for `init_boot.img` and
`vendor_boot.img`, separate transition images, and both old images in the restore
set. That proof must bind the same capture/slot **and exact candidate proof hash**
using `candidate_proof_sha256`, and literally declare `passed`,
`foundation_compatible` and `recovery_transition_reviewed` true. This seven-target
route changes target-slot recovery; the old custom recovery transport does not
qualify the replacement stock recovery or its USB restoration route.

## Command interface for later qualification

Inspect `python3 tools/install-candidate.py --help` locally. Required arguments
are capture/path pin, candidate-proof/path pin, explicit slot, new and old image
directories, fresh host journal path, pinned ADB and lpdump paths/hashes. Optional
transition proof/pin/images must be supplied together. No hardware command recipe
is approved here. Qualify the exact tools and operator prerequisites first.

The host journal must be outside the repository and image inputs, on durable
storage, not in device userdata or recovery RAM. It is private, mode0600, with
capture/proof/transition/slot bindings, append records and file/directory fsync.
A fresh run refuses an existing journal; use explicit `--resume` for that same
operation, including after a successful dry-run.

Long RAM transfers and full hashes precede a fresh identity/mount/map/staging
boundary check. Ambiguous stacked mounts are refused. Immediately before each
persistent write the journal records `before_write`; after complete
fsync and full-target hash readback it records `verified`. Recovery `/tmp` and each staging destination must be under a writable
rootfs/ramfs/tmpfs mount, with no symlink redirection; regular RAM leftovers may
be replaced on resume, while other object types fail closed. Data is RAM-staged,
hashed, then written with explicit4096-byte block count bounded to the exact
partition size. The sequence is three userspaces, optional two bootstrap files,
then vbmeta_system and vbmeta. Protected prefix, physical partitions and every
non-target allocated logical partition are checked before writes and at completion.
No automatic boot follows success or failure.

Resume hashes every target and classifies it as old, new or partial. Completed
new targets are retained; old targets are written as needed. Partial bytes are
accepted only when the **last per-target event** is a bound pending `before_write`;
a historical attempt followed by `verified` cannot authorize later corruption.
Every target is reclassified at write boundaries, not only at initial preflight. Explicit
`--resume --restore --execute` instead writes the pinned old set, without first
finishing installation. Both old/new inputs and proofs remain required. Changed
proof/capture, protected state, journal binding or unknown target data fails
closed. A malformed/truncated journal is not repaired automatically; preserve it
and obtain an independently reviewed recovery plan rather than inventing progress.

## Evidence and interruption limits

Run only the file-backed host qualification now:

```sh
python3 -m unittest discover -s tests -p test_candidate_install.py -v
```

Tests exercise the production command flow through a fake ADB implementation,
including a completed write followed by a partial write/disconnect, a pending
resume/restore refused while a surviving `dd` is present, quiescent resume,
direct restore, seven-target transitions, complete inactive-slot support,
empty-slot refusal, known linear maps, mounted aliases, protected B/metadata,
changed proofs and invalid recovery/snapshot state. Native lpdump is replaced by
validated synthetic views in this harness; its parser has its own regression
suite. A/B fixtures contain distinct per-partition bytes, and tests inspect actual
write ranges and protected B logical bytes as well as physical partitions/prefix.
This is not actual recovery ABI, USB, persistence or power-cut qualification.
A quiescent, trusted recovery is required; these checks do not provide kernel-atomic
exclusion against another privileged process changing mounts/maps/files concurrently.

The five/seven writes are not atomic. Vbmeta last provides no power-loss guarantee.
A loss before recovery is re-entered may leave a nonbootable/mixed set; B may be
empty, boot retry/fallback behavior may intervene, and changing bootstrap may
remove the previously working recovery. Re-entry, recovery root USB, read-only
metadata setup, journal durability across real host power loss and interrupted
hardware restore must be qualified independently. If prerequisites no longer
hold, the writer stops; it does not boot, repair LP metadata, switch to B or wipe.
