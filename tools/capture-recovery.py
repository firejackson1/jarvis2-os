#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Back up the seven LCARS rollback images from an already qualified Recovery session."""

import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory


spec = importlib.util.spec_from_file_location(
    'recovery_inspector', Path(__file__).with_name('inspect-recovery.py'))
INSPECT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(INSPECT)
WRITER = INSPECT.WRITER
PLAN = INSPECT.PLAN
SECTOR = PLAN.SECTOR_SIZE
CHUNK = 8 * 1024 * 1024
LOGICAL_TARGETS = ('system', 'system_ext', 'product')
PHYSICAL_TARGETS = ('init_boot', 'vendor_boot', 'vbmeta_system', 'vbmeta')


def physical_inventory(adb, layout_physical):
    names = ('super', *WRITER.REQUIRED_PHYSICAL)
    records = {name: INSPECT.partition(adb, name) for name in names}
    if any(records[name] != row for name, row in layout_physical.items()):
        raise ValueError('Physical identity changed after layout inspection')
    if (len({(row['major'], row['minor']) for row in records.values()}) != len(names) or
        len({row['path'] for row in records.values()}) != len(names)):
        raise ValueError('Physical partition aliases are forbidden')
    ranges = {}
    parents = set()
    for name, record in records.items():
        sysfs = f"/sys/dev/block/{record['major']}:{record['minor']}"
        resolved = Path(INSPECT.shell(adb, 'readlink', '-f', sysfs))
        if not resolved.is_relative_to('/sys/devices') or resolved.name != Path(record['path']).name:
            raise ValueError('Physical block path differs from its sysfs identity')
        parents.add(resolved.parent)
        start = PLAN.native_uint(INSPECT.shell(adb, 'cat', sysfs + '/start'))
        size = PLAN.native_uint(INSPECT.shell(adb, 'cat', sysfs + '/size'))
        if size * SECTOR != record['bytes']:
            raise ValueError('Physical partition size differs from sysfs geometry')
        ranges[name] = (start, start + size)
    ordered = sorted(ranges.values())
    if len(parents) != 1 or any(right[0] < left[1] for left, right in zip(ordered, ordered[1:])):
        raise ValueError('Physical partitions overlap or have different backing disks')
    return records, (next(iter(parents)), ranges)


def device_hash(adb, path):
    fields = INSPECT.shell(adb, 'sha256sum', path).split()
    if len(fields) != 2 or fields[1] != path:
        raise ValueError('Unexpected partition hash output')
    WRITER.pin(fields[0])
    return fields[0]


def read_ranges(adb, path, ranges, destination=None):
    digest = hashlib.sha256()
    with destination.open('xb') if destination else nullcontext() as output:
        for offset, length in ranges:
            for start in range(offset, offset + length, CHUNK):
                size = min(CHUNK, offset + length - start)
                data = adb.run('exec-out', 'dd', 'if=' + path, 'bs=1048576',
                               'iflag=skip_bytes,count_bytes', 'skip=' + str(start),
                               'count=' + str(size), 'status=none', binary=True)
                if len(data) != size:
                    raise ValueError('Short or mixed partition payload read')
                digest.update(data)
                if output is not None:
                    output.write(data)
    return digest.hexdigest()


def sync(path, mode, *, directory=False):
    path.chmod(mode)
    fd = os.open(path, os.O_RDONLY | (os.O_DIRECTORY if directory else 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def capture(serial, slot, adb_path, adb_pin, lpdump, lpdump_pin, dmctl, dmctl_pin, output,
            *, transport=None, view_loader=PLAN.load_views):
    if slot not in ('a', 'b'):
        raise ValueError('An explicit target slot is required')
    WRITER.pin(dmctl_pin)
    if not re.fullmatch(r'/(tmp|sbin|system/bin)/[A-Za-z0-9_.-]+', dmctl):
        raise ValueError('Expected an independently reviewed Recovery dmctl path')
    output = Path(os.path.abspath(output))
    if (output.is_relative_to(INSPECT.ROOT) or output.exists() or
        any(path.is_symlink() for path in (output, *output.parents))):
        raise ValueError('Choose a fresh private output directory outside the source checkout')
    adb = transport if transport is not None else INSPECT.InspectionADB(WRITER.regular(adb_path), serial)

    with TemporaryDirectory(prefix='jarvis2-capture-', dir=output.parent) as temp:
        scratch = Path(temp)

        def inspect(name):
            return INSPECT.inspect(serial, adb_path, adb_pin, lpdump, lpdump_pin, scratch / name,
                                   transport=adb, view_loader=view_loader)

        initial = inspect('before')
        layout = initial['layout']
        if initial['snapshots']['status'] != 'clear':
            raise ValueError('Clear snapshot evidence from idle root Recovery is required')
        if not layout or not layout['views_match']:
            raise ValueError('Matching native metadata views are required')
        view = layout['views'][0]
        PLAN.validate_layout(view)
        if any(view['sizes'].get(part + '_' + slot, 0) <= 0 for part in PLAN.FOUNDATION):
            raise ValueError('Selected slot lacks an allocated OS foundation')
        physical, geometry = physical_inventory(adb, layout['physical'])
        if device_hash(adb, dmctl) != dmctl_pin:
            raise ValueError('Recovery dmctl hash differs from its pin')

        super_device = physical.pop('super')
        suffix = '_' + slot
        targets = {part + suffix: part + '.img' for part in (*LOGICAL_TARGETS, *PHYSICAL_TARGETS)}
        sizes = {part: physical[part]['bytes'] if part in physical else view['sizes'][part] for part in targets}
        if any(size <= 0 or size % 4096 for size in sizes.values()):
            raise ValueError('Rollback image sizes must match the writer block alignment')
        if shutil.disk_usage(scratch).free < sum(sizes.values()):
            raise ValueError('The output filesystem has insufficient space for all seven restore files')
        stage = scratch / 'result'
        saved = stage / 'old-images'
        saved.mkdir(parents=True, mode=0o700)
        shutil.copyfile(scratch / 'before/super-prefix.img', stage / 'super-prefix.img')

        digest_physical = {name: device_hash(adb, row['path']) for name, row in physical.items()}
        for part in PHYSICAL_TARGETS:
            name = part + suffix
            actual = read_ranges(adb, physical[name]['path'], [(0, sizes[name])], saved / targets[name])
            if actual != digest_physical[name]:
                raise ValueError('Captured physical image changed while reading')

        ranges = {
            name: [(extent['target_data'] * SECTOR, extent['num_sectors'] * SECTOR) for extent in extents]
            for name, extents in view['layout']['partitions'].items() if extents
        }
        logical = {}
        for name, regions in ranges.items():
            filename = targets.get(name)
            logical[name] = read_ranges(adb, super_device['path'], regions, saved / filename if filename else None)
        old_files = {filename: {'bytes': sizes[part],
                               'sha256': digest_physical[part] if part in physical else logical[part]}
                     for part, filename in targets.items()}
        WRITER.image_files(saved, old_files)

        if inspect('mid') != initial or physical_inventory(adb, layout['physical']) != (
            {**physical, 'super': super_device}, geometry
        ):
            raise ValueError('Recovery state or physical layout changed during capture')
        for name, regions in ranges.items():
            if read_ranges(adb, super_device['path'], regions) != logical[name]:
                raise ValueError('A logical partition changed between capture and readback')
        if (any(device_hash(adb, row['path']) != digest_physical[name] for name, row in physical.items()) or
            device_hash(adb, dmctl) != dmctl_pin or inspect('after') != initial or
            physical_inventory(adb, layout['physical']) != ({**physical, 'super': super_device}, geometry)):
            raise ValueError('Recovery state or protected partition bytes changed during readback')

        metadata_prefix = layout['metadata_prefix']
        capture_data = {'format': 1, 'serial': serial, 'current_slot': initial['device']['slot'],
                        'super': super_device, 'physical': {
                            name: {**row, 'sha256': digest_physical[name]} for name, row in physical.items()
                        }, 'metadata_prefix': metadata_prefix, 'logical_sha256': logical,
                        'old_files': old_files, 'dmctl': {'path': dmctl, 'sha256': dmctl_pin}}
        capture_file = stage / 'capture.json'
        capture_file.write_text(json.dumps(capture_data, indent=2, sort_keys=True) + '\n')
        receipt = {'format': 1, 'kind': 'jarvis2-rollback-capture', 'target_slot': slot,
                   'capture_sha256': WRITER.digest(capture_file), 'restore_files': len(old_files),
                   'protected_physical_hashes': len(physical), 'logical_hashes': len(logical),
                   'adb_sha256': adb_pin, 'lpdump_sha256': lpdump_pin, 'installation_authorized': False}
        (stage / 'capture-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        for path in (*saved.iterdir(), capture_file, stage / 'super-prefix.img', stage / 'capture-receipt.json'):
            sync(path, 0o600)
        sync(saved, 0o700, directory=True)
        sync(stage, 0o700, directory=True)
        if output.exists() or output.is_symlink():
            raise ValueError('Output appeared during backup')
        stage.rename(output)
        fd = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return receipt


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slot', choices=('a', 'b'), required=True)
    for name in ('serial', 'adb-sha256', 'lpdump-sha256', 'dmctl', 'dmctl-sha256'):
        parser.add_argument('--' + name, required=True)
    for name in ('adb', 'lpdump', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = capture(args.serial, args.slot, args.adb, args.adb_sha256, args.lpdump,
                          args.lpdump_sha256, args.dmctl, args.dmctl_sha256, args.output)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Recovery capture failed: {error}\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
