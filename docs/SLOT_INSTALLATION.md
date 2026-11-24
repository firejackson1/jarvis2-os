# Explicit A/B installation support — in development

The release must allow an explicit `a` or `b` target; slot names do not designate
an Android-versus-custom-ROM format. Each target still needs a complete compatible
firmware foundation, sufficient allocated logical partitions and matching AVB
metadata. Android userdata is shared between slots.

## Important Virtual A/B metadata behavior

The first private A test used only five `_a` image flash commands. All five later
matched device readback, and unchanged boot/recovery/vendor partitions matched
their saved hashes. The system booted with SELinux enforcing; the owner verified
Home and remote navigation.

However, ordinary fastboot automatically sent same-size logical resize commands.
The pinned fastbootd implementation's `PartitionBuilder::Write()` calls
`UpdateAllPartitionMetadata()`, which updates both boot-slot metadata views.
`FlashHandler()` also calls `CancelPartitionSnapshot()` for logical partitions.
Therefore selecting an `_a` image name alone does not prove that B's shared
metadata was untouched. Complete pre-test metadata views were not captured for
that test, so previous claims of untouched shared metadata were too broad.
No B image flash command was sent; B is not a verified fallback.

Current read-only dumps show allocated A logical partitions and empty B entries
in both metadata views. An older saved view includes B/snapshot-COW mappings;
that old snapshot view must not be restored blindly. The owner's current choice
is to keep B unchanged while support is developed. No B provisioning or slot
switch has been authorized.

## Read-only preflight tool

`tools/slot-install-plan.py` accepts an explicit target and never writes a device:

```sh
python3 tools/slot-install-plan.py --slot a \
  --manifest /private/test-set/manifest.json --images /private/test-set/images \
  --super-metadata /private/capture/super-metadata.img \
  --physical-sizes /private/capture/physical-sizes.json \
  --lpdump /path/to/built/host/bin/lpdump
```

The physical-sizes JSON must contain independently checked integer byte sizes for
vbmeta_a, vbmeta_system_a, vbmeta_b and vbmeta_system_b. The native lpdump verifies
and reads both metadata views; complete textual layout comparisons cover extents
and groups as well as sizes. The plan requires matching metadata views, a fully
allocated target foundation, offline-verified AVB metadata and exact image sizes.
It checks local image hashes and reports whether the other slot even has a
complete allocated foundation. This does not establish that it can boot.

Manifest booleans and integer sizes are checked strictly, and actual regular-file
length must match both the manifest and partition. Digests must be valid SHA-256;
Android sparse images are rejected because this scope requires exact-size raw
images. Tests cover misleading truthy values and short/long files even when
their hashes match a deceptive manifest.

The manifest's AVB field is still a claimed prerequisite, not authenticated
release trust or an independent chain audit. The pinned native JSON omits extent
ranges, so its text tables are parsed and cross-checked against JSON identities,
groups and sizes. For this model the planner accepts only one super backing
device, fixed 512-byte sectors and linear extents. It verifies logical continuity,
byte totals, alignment, backing capacity, the reserved metadata prefix and overlap
across every logical partition in both matching views. Unsupported layouts fail
closed. Live physical identity/capacity, snapshot state, capture freshness and an
authenticated baseline remain mandatory writer gates; do not execute the emitted
plan automatically.

The tool rejects unsigned raw build archives, implicit/all-slot targets,
unallocated foundations, differing metadata views and size mismatches. It does
not resize, flash, activate a slot or wipe data. Firmware compatibility, trusted
release keys and recovery transport remain separate gates.

Host regressions cover allocated A and B targets, a B-active/A-empty layout,
unsigned images, empty target foundations, mismatched sizes and differing views.
A real read-only run against the current device's captured metadata planned A
and correctly refused B. This is not a B installation or boot test.

## Remaining installer work

An empty inactive slot requires full foundation provisioning, not just the three
rebuilt userspace images and two vbmeta files. A tested provisioning path must
allocate the target's vendor/ODM/module partitions too, preserve every protected
extent, detect cross-view overlap and snapshot state, verify backups of both
metadata views and all required content, and prove recovery after interruption.
It must not silently copy one metadata view over a different protected view.

Either-slot release support remains incomplete until that path and the actual
writer are verified. Do not present this planning tool or the private raw ZIP as
a universal installer.

## Experimental raw writer checkpoint

[Recovery raw writer](CANDIDATE_INSTALLATION.md) documents the new offline-only
implementation and its explicit operator prerequisites. It uses validated RAM
linear maps and exact bounded writes; it does not invoke fastboot flashing,
resize, snapshot cancellation or an LP metadata writer. File-backed simulations
and independent code review passed; actual recovery execution remains unqualified.
It refuses an empty target foundation and performs no automatic activation/wipe.

For the pinned product `system/core` revision
`ec299bf6da55702b7b9675d60a0faf2815f0dc6d`, skipping a same-size host resize is
insufficient: fastbootd's logical flash path calls `CancelPartitionSnapshot()`,
which writes through `PartitionBuilder::Write()` and updates both LP metadata
views even when the UPDATED attribute was already clear. Debuggable flashing can
also trigger overlay/scratch cleanup. The installed custom recovery's exact
source binding is not established by this product-source inspection. Read-only
getvar success and snapshot status None do not qualify either write path.
