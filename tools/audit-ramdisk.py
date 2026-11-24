#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Inspect newc ramdisks without extracting files or executing their programs."""
import argparse
from collections import Counter, deque
import gzip
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct

LIMIT = 256 * 1024 * 1024


def parse_cpio(data):
    if len(data) > LIMIT:
        raise ValueError('Ramdisk exceeds the inspection size limit')
    entries, offset = {}, 0
    while offset + 110 <= len(data):
        magic = data[offset:offset + 6]
        if magic not in (b'070701', b'070702'):
            raise ValueError('Expected a newc/CRC archive header')
        try:
            fields = [int(data[offset + 6 + i * 8:offset + 14 + i * 8], 16) for i in range(13)]
        except ValueError as exc:
            raise ValueError('Malformed newc header') from exc
        mode, uid, gid, size, name_size = fields[1], fields[2], fields[3], fields[6], fields[11]
        start = offset + 110
        if not 1 <= name_size <= 4096 or start + name_size > len(data):
            raise ValueError('Invalid or truncated archive filename')
        raw_name = data[start:start + name_size]
        if not raw_name.endswith(b'\0') or b'\0' in raw_name[:-1]:
            raise ValueError('Invalid archive filename terminator')
        name = raw_name[:-1].decode()
        start = (start + name_size + 3) & ~3
        if start + size > len(data):
            raise ValueError('Truncated archive contents')
        payload = data[start:start + size]
        offset = (start + size + 3) & ~3
        if name == 'TRAILER!!!':
            if size or any(data[offset:]):
                raise ValueError('Unexpected data after archive trailer; supply layers separately')
            return entries
        if name.startswith('/') or '..' in PurePosixPath(name).parts or any(ord(c) < 32 for c in name):
            raise ValueError('Unsafe archive path')
        name = str(PurePosixPath(name))
        if name == '.':
            continue
        if name in entries:
            raise ValueError('Duplicate archive path: ' + name)
        if magic == b'070702' and sum(payload) & 0xffffffff != fields[12]:
            raise ValueError('CPIO checksum mismatch')
        entries[name] = {'mode': mode, 'uid': uid, 'gid': gid, 'data': payload}
    raise ValueError('Archive is truncated or lacks a trailer')


def resolve(entries, name):
    pending, resolved, links = deque(PurePosixPath(name).parts), [], 0
    while pending:
        part = pending.popleft()
        if part in ('', '.', '/'):
            continue
        if part == '..':
            if not resolved:
                raise ValueError('Symlink escapes the ramdisk root')
            resolved.pop()
            continue
        path = '/'.join([*resolved, part])
        entry = entries.get(path)
        if entry and stat.S_ISLNK(entry['mode']):
            links += 1
            if links > 40:
                raise ValueError('Ramdisk symlink loop')
            target = entry['data'].decode()
            if '\0' in target:
                raise ValueError('Invalid symlink target')
            if target.startswith('/'):
                resolved.clear()
            pending.extendleft(reversed(PurePosixPath(target).parts))
        else:
            resolved.append(part)
    return entries.get('/'.join(resolved))


def elf_info(data):
    if not data.startswith(b'\x7fELF'):
        return None
    if len(data) < 52 or data[4] not in (1, 2) or data[5] != 1:
        raise ValueError('Unsupported or truncated ELF header')
    bits = 32 if data[4] == 1 else 64
    if bits == 64 and len(data) < 64:
        raise ValueError('Truncated ELF64 header')
    kind, machine = struct.unpack_from('<HH', data, 16)
    return {'bits': bits, 'machine': {40: 'ARM', 183: 'AArch64', 62: 'x86_64'}.get(machine, str(machine)),
            'elf_type': kind}


def audit_layers(layers, expected_recovery_arch=None):
    entries, overwritten = {}, []
    for layer in layers:
        overwritten.extend(sorted(set(entries) & set(layer)))
        entries.update(layer)
    required = {}
    for name in ('init', 'system/bin/recovery'):
        entry = resolve(entries, name)
        info = elf_info(entry['data']) if entry else None
        if info is None or info['elf_type'] not in (2, 3):
            raise ValueError('Missing native executable in effective ramdisk: ' + name)
        required[name] = info
    if expected_recovery_arch:
        machine = {'arm': 'ARM', 'arm64': 'AArch64'}[expected_recovery_arch]
        if required['system/bin/recovery']['machine'] != machine:
            raise ValueError('Recovery executable does not match requested architecture')
    private_key = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----')
    blocked, elf_counts, executable_counts, init_scripts, policy_files = [], Counter(), Counter(), [], []
    for name, entry in entries.items():
        if not stat.S_ISREG(entry['mode']):
            continue
        payload = entry['data']
        if (PurePosixPath(name).name in ('adb_keys', 'default_adb_keys') or name.endswith('.pk8')
                or private_key.search(payload)):
            blocked.append(name)
        info = elf_info(payload)
        if info:
            elf_counts[info['machine'] + '/' + str(info['bits'])] += 1
            if info['elf_type'] in (2, 3):
                executable_counts[info['machine'] + '/' + str(info['bits'])] += 1
        if name.endswith('.rc'):
            init_scripts.append(name)
        if 'file_contexts' in name or name.endswith(('sepolicy', '.cil')):
            policy_files.append(name)
    return {'entries': len(entries), 'required': required, 'elf_counts': dict(elf_counts),
            'userspace_elf_counts': dict(executable_counts),
            'blocked_artifacts': sorted(blocked), 'overwritten_layer_entries': overwritten,
            'init_scripts': sorted(init_scripts), 'policy_files': sorted(policy_files),
            'boot_tested': False, 'linked_dependencies_verified': False,
            'startup_writes_reviewed': False, 'device_contacted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpio', type=Path, action='append', required=True,
                        help='Raw/gzip newc archive; repeated in kernel overlay order')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-recovery-arch', choices=('arm', 'arm64'))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh output report')
    layers = []
    for path in args.cpio:
        if not path.is_file() or path.stat().st_size > LIMIT:
            parser.error('Input is not a regular, bounded archive')
        with path.open('rb') as stream:
            compressed = stream.read(2) == b'\x1f\x8b'
        with (gzip.open(path, 'rb') if compressed else path.open('rb')) as stream:
            layers.append(parse_cpio(stream.read(LIMIT + 1)))
    report = audit_layers(layers, args.expected_recovery_arch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('required', 'elf_counts', 'blocked_artifacts')}, indent=2))
    if report['blocked_artifacts']:
        raise SystemExit(1)
