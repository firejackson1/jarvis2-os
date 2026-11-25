#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record read-only Jarvis2 Recovery evidence in a private host directory."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'recovery_writer_contract', Path(__file__).with_name('install-candidate.py'))
WRITER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(WRITER)
PLAN = WRITER.PLAN
SECTOR = PLAN.SECTOR_SIZE
DEFAULT_PREFIX = 1024 * 1024
MAX_PREFIX = 16 * 1024 * 1024
ANDROID_PROCESSES = {
    'system_server', 'zygote', 'zygote64', 'surfaceflinger', 'fastbootd',
    'update_engine', 'update_engine_sideload', 'snapuserd', 'dd',
}
PATH_PROBE = (
    'if [ -L "$1" ]; then printf symlink; elif [ -d "$1" ]; then printf directory; '
    'elif [ ! -e "$1" ]; then printf absent; else printf unsupported; fi'
)


class InspectionADB(WRITER.ADB):
    def run(self, *args, binary=False):
        selector = [] if args[0] == 'devices' else ['-s', self.serial]
        try:
            result = subprocess.run([self.path, *selector, *args], capture_output=True,
                                    timeout=30, check=True)
        except subprocess.SubprocessError:
            raise ValueError(f'ADB {args[0]} failed or timed out') from None
        if result.stderr:
            raise ValueError('ADB reported diagnostics during a read-only check')
        return result.stdout if binary else result.stdout.decode('utf-8')


def shell(adb, *args):
    return adb.run('shell', shlex.join(args)).strip()


def device_state(adb, serial):
    rows = [line.split() for line in adb.run('devices', '-l').splitlines()]
    matching = [row for row in rows if row and row[0] == serial]
    usb = [token for row in matching for token in row[2:] if token.startswith('usb:') and token[4:]]
    if (len(matching) != 1 or len(matching[0]) < 3 or
        matching[0][1] not in ('device', 'recovery') or len(usb) != 1 or
        adb.run('get-serialno').strip() != serial):
        raise ValueError('Expected the exact USB ADB device and an authorized connection')
    product = shell(adb, 'getprop', 'ro.product.device')
    if product != 'jarvis2':
        raise ValueError('The selected USB device does not identify as Jarvis2')
    uid = PLAN.native_uint(shell(adb, 'id', '-u'))
    slot = shell(adb, 'getprop', 'ro.boot.slot_suffix')
    boot_completed = shell(adb, 'getprop', 'sys.boot_completed')
    processes = {Path(name.strip()).name for name in shell(adb, 'ps', '-A', '-o', 'NAME').splitlines()}
    recovery = (slot in ('_a', '_b') and boot_completed in ('', '0') and
                'recovery' in processes and not processes & ANDROID_PROCESSES)
    return {'serial': serial, 'product': product, 'slot': slot[1:] if slot in ('_a', '_b') else None,
            'adb_state': matching[0][1], 'usb': usb[0], 'uid': uid, 'idle_recovery': recovery}


def partition(adb, name):
    path = shell(adb, 'readlink', '-f', '/dev/block/by-name/' + name)
    if not re.fullmatch(r'/dev/block/[A-Za-z0-9_.-]+', path) or path.rsplit('/', 1)[1] in ('.', '..'):
        raise ValueError('Unexpected physical block path for ' + name)
    identity = shell(adb, 'stat', '-Lc', '%t:%T', path)
    if not re.fullmatch(r'[0-9a-fA-F]+:[0-9a-fA-F]+', identity):
        raise ValueError('Unexpected physical block identity for ' + name)
    major, minor = (int(value, 16) for value in identity.split(':'))
    record = {'path': path, 'major': major, 'minor': minor,
              'bytes': PLAN.native_uint(shell(adb, 'blockdev', '--getsize64', path))}
    WRITER.device(record, hashed=False)
    return record


def snapshot_state(adb, metadata):
    def unverified(reason):
        return {'status': 'unverified', 'reason': reason}

    mounts = []
    for line in shell(adb, 'cat', '/proc/self/mountinfo').splitlines():
        before, boundary, after = line.partition(' - ')
        left, right = before.split(), after.split()
        if not boundary or len(left) < 6 or len(right) != 3:
            return unverified('unexpected mountinfo format')
        if left[4] == '/metadata' or left[4].startswith('/metadata/'):
            mounts.append((left, right))
    if len(mounts) != 1 or mounts[0][0][4] != '/metadata':
        return unverified('metadata is absent or has stacked or nested mounts')
    (left, right), = mounts
    mount_options = set(left[5].split(','))
    options = mount_options | set(right[2].split(','))
    if (left[2] != f"{metadata['major']}:{metadata['minor']}" or left[3] != '/' or
        right[0] != 'f2fs' or not right[1].startswith('/dev/block/') or
        'ro' not in mount_options or 'rw' in options or
        not options & {'norecovery', 'disable_roll_forward'} or
        shell(adb, 'readlink', '-f', right[1]) != metadata['path']):
        return unverified('metadata mount is not the verified read-only F2FS partition')

    def path_state(path):
        return shell(adb, 'sh', '-c', PATH_PROBE, 'probe', path)

    ota = '/metadata/ota'
    kind = path_state(ota)
    if kind == 'absent':
        return {'status': 'clear', 'evidence': 'verified metadata with no OTA directory'}
    if kind != 'directory':
        return unverified('unexpected ota path')
    entries = shell(adb, 'find', ota, '-maxdepth', '1', '-mindepth', '1', '-print').splitlines()
    if not entries:
        return {'status': 'clear', 'evidence': 'verified metadata with an empty OTA directory'}
    snapshots = ota + '/snapshots'
    if (entries == [snapshots] and path_state(snapshots) == 'directory' and
        not shell(adb, 'find', snapshots, '-maxdepth', '1', '-mindepth', '1', '-print')):
        return {'status': 'clear', 'evidence': 'verified metadata with an empty snapshots directory'}
    return unverified('persisted OTA entries require independent review')


def inspect(serial, adb_path, adb_pin, lpdump, lpdump_pin, output, *,
            prefix_bytes=DEFAULT_PREFIX, transport=None, view_loader=PLAN.load_views):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', serial):
        raise ValueError('Expected a USB ADB serial')
    if type(prefix_bytes) is not int or not SECTOR <= prefix_bytes <= MAX_PREFIX or prefix_bytes % SECTOR:
        raise ValueError('Invalid bounded metadata prefix length')
    output = Path(os.path.abspath(output))
    if (output.is_relative_to(ROOT) or output.exists() or
        any(path.is_symlink() for path in (output, *output.parents))):
        raise ValueError('Choose a fresh private output directory outside the source tree')
    adb_path, lpdump = map(WRITER.regular, (adb_path, lpdump))
    for path, expected in ((adb_path, adb_pin), (lpdump, lpdump_pin)):
        WRITER.pin(expected)
        if WRITER.digest(path) != expected:
            raise ValueError('Host tool digest differs from the requested pin')
    adb = transport if transport is not None else InspectionADB(adb_path, serial)

    with TemporaryDirectory(prefix='jarvis2-inspection-', dir=output.parent) as temp:
        stage = Path(temp) / 'report'
        stage.mkdir(mode=0o700)
        state = device_state(adb, serial)
        result = {'format': 1, 'kind': 'jarvis2-recovery-inspection', 'device': state,
                  'tools': {'adb_sha256': adb_pin, 'lpdump_sha256': lpdump_pin},
                  'layout': None, 'snapshots': {'status': 'unverified', 'reason': 'idle root Recovery required'},
                  'installation_authorized': False}
        if state['idle_recovery'] and state['uid'] == 0:
            names = ('super', 'metadata', *sorted(PLAN.PHYSICAL))
            physical = {name: partition(adb, name) for name in names}
            if (len({(row['major'], row['minor']) for row in physical.values()}) != len(names) or
                len({row['path'] for row in physical.values()}) != len(names)):
                raise ValueError('Unexpected aliases in the inspected physical partitions')
            super_device = physical['super']
            if super_device['bytes'] < prefix_bytes:
                raise ValueError('Requested prefix exceeds the inspected block size')
            snapshots = snapshot_state(adb, physical['metadata'])

            def read_prefix():
                data = adb.run('exec-out', 'dd', 'if=' + super_device['path'], 'bs=512',
                               'count=' + str(prefix_bytes // SECTOR), 'status=none', binary=True)
                if len(data) != prefix_bytes:
                    raise ValueError('Short or mixed output from metadata prefix read')
                return data

            data = read_prefix()
            prefix = stage / 'super-prefix.img'
            prefix.write_bytes(data)
            sizes = {name: physical[name]['bytes'] for name in sorted(PLAN.PHYSICAL)}
            views = view_loader(str(lpdump), str(prefix), sizes)
            for view in views:
                layout = view['layout']
                backing = layout['block_devices'][0]
                required_bytes = 12288 + 2 * layout['metadata_slot_count'] * layout['metadata_max_size']
                if backing['size'] != super_device['bytes'] or not (
                    required_bytes <= prefix_bytes <= backing['first_logical_sector'] * SECTOR
                ):
                    raise ValueError('Prefix does not match native metadata and live backing geometry')
            if (device_state(adb, serial) != state or
                any(partition(adb, name) != row for name, row in physical.items()) or
                read_prefix() != data or snapshot_state(adb, physical['metadata']) != snapshots):
                raise ValueError('Recovery evidence changed during inspection')
            result['layout'] = {'views_match': views[0] == views[1], 'views': views,
                                'physical': physical,
                                'metadata_prefix': {'bytes': prefix_bytes, 'sha256': hashlib.sha256(data).hexdigest()}}
            result['snapshots'] = snapshots
        if WRITER.digest(adb_path) != adb_pin or WRITER.digest(lpdump) != lpdump_pin:
            raise ValueError('Pinned host tool changed during inspection')
        report = stage / 'inspection.json'
        report.write_text(json.dumps(result, indent=2) + '\n')
        prefix = stage / 'super-prefix.img'
        report.chmod(0o600)
        if prefix.exists():
            prefix.chmod(0o600)
        if output.exists() or output.is_symlink():
            raise ValueError('Output appeared during inspection')
        stage.rename(output)
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('serial', 'adb-sha256', 'lpdump-sha256'):
        parser.add_argument('--' + name, required=True)
    for name in ('adb', 'lpdump', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = inspect(args.serial, args.adb, args.adb_sha256, args.lpdump, args.lpdump_sha256, args.output)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Recovery inspection failed: {error}\n')
    print(json.dumps({'idle_root_recovery': result['device']['idle_recovery'] and result['device']['uid'] == 0,
                      'layout_views_match': result['layout']['views_match'] if result['layout'] else None,
                      'snapshot_status': result['snapshots']['status'],
                      'installation_authorized': False}, indent=2))


if __name__ == '__main__':
    main()
