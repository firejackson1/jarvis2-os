#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Derive a diagnostic CPIO fragment; never build, boot or flash a device image."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys

spec = importlib.util.spec_from_file_location('ramdisk_audit',
                                             Path(__file__).with_name('audit-ramdisk.py'))
AUDIT = importlib.util.module_from_spec(spec)
previous_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(AUDIT)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting

INIT = 'system/etc/init/hw/init.rc'
FSTAB = 'system/etc/recovery.fstab'
TRUST_LINK = 'adb_keys'
IMPORT = b'import /init.recovery.${ro.hardware}.rc\n'
RECOVERY = b'service recovery /system/bin/recovery\n'


def original(entry):
    return entry['archive']


def record(data, entry):
    start, end = original(entry)['record_span']
    return data[start:end]


def replace_payload(raw, payload):
    """Change only size/checksum/content; retain every other newc header field."""
    header = bytearray(raw[:110])
    namesize = int(header[94:102], 16)
    start = (110 + namesize + 3) & ~3
    header[54:62] = f'{len(payload):08x}'.encode()
    if header[:6] == b'070702':
        header[102:110] = f'{sum(payload) & 0xffffffff:08x}'.encode()
    return bytes(header) + raw[110:start] + payload + b'\0' * (-len(payload) % 4)


def prepare(data, expected_sha256):
    if not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('An exact lowercase SHA256 input binding is required')
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('Input CPIO does not match its expected digest')
    before = AUDIT.parse_cpio(data)
    source_report = AUDIT.audit_layers([before], expected_recovery_arch='arm64')
    if set(source_report['blocked_artifacts']) != {TRUST_LINK}:
        raise ValueError('Unexpected trust material or missing reviewed trust-link placeholder')
    link = original(before[TRUST_LINK])
    if (not stat.S_ISLNK(link['mode']) or link['nlink'] != 1
            or link['data'] != b'/product/etc/security/adb_keys'
            or AUDIT.resolve(before, TRUST_LINK) is not None):
        raise ValueError('Only the reviewed unresolved standard trust symlink may be removed')
    for name in (INIT, FSTAB):
        if name not in before:
            raise ValueError('Required diagnostic metadata is missing: ' + name)
        entry = original(before[name])
        if not stat.S_ISREG(entry['mode']) or entry['nlink'] != 1:
            raise ValueError('Diagnostic metadata must be an unshared regular file')
    script = original(before[INIT])['data']
    imports = [line for line in script.splitlines() if re.match(rb'\s*import(?:\s|$)', line)]
    services = [line for line in script.splitlines()
                if re.match(rb'\s*service\s+recovery(?:\s|$)', line)]
    if (script.count(IMPORT) != 1 or script.count(RECOVERY) != 1
            or imports != [IMPORT.rstrip(b'\n')] or services != [RECOVERY.rstrip(b'\n')]):
        raise ValueError('Init script does not have the exact reviewed import/service form')
    changes = {
        INIT: script.replace(IMPORT, b'import /ramboot/init.hardware.rc\n').replace(
            RECOVERY, b'service recovery /system/bin/recovery --show_text\n'),
        FSTAB: b'ramdisk /tmp ramdisk defaults defaults\n',
    }
    pieces, cursor = [], 0
    for name, entry in before.items():
        start, end = original(entry)['record_span']
        pieces.append(data[cursor:start])
        if name in changes:
            pieces.append(replace_payload(data[start:end], changes[name]))
        elif name != TRUST_LINK:
            pieces.append(data[start:end])
        cursor = end
    pieces.append(data[cursor:])  # Preserve the original trailer and final padding.
    result = b''.join(pieces)
    after = AUDIT.parse_cpio(result)
    report = AUDIT.audit_layers([after], expected_recovery_arch='arm64')
    if report['blocked_artifacts'] or set(after) != set(before) - {TRUST_LINK}:
        raise ValueError('Unexpected archive or trust material after preparation')
    if any(after[name]['data'] != payload for name, payload in changes.items()):
        raise ValueError('Diagnostic replacements did not survive archive parsing')
    for name in set(before) - set(changes) - {TRUST_LINK}:
        if record(data, before[name]) != record(result, after[name]):
            raise ValueError('An unreviewed archive record changed: ' + name)
    return result, {
        'input_sha256': expected_sha256, 'output_sha256': hashlib.sha256(result).hexdigest(),
        'output_bytes': len(result), 'changed_records': sorted(changes),
        'removed_records': [TRUST_LINK], 'untouched_records_identical': True,
        'blocked_artifacts_after': report['blocked_artifacts'],
        'requires_guard_and_hardware_overlay': True,
        'startup_qualified': False, 'boot_tested': False, 'device_contacted': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpio', type=Path, required=True)
    parser.add_argument('--expected-input-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh private output directory')
    if not args.cpio.is_file() or args.cpio.stat().st_size > AUDIT.LIMIT:
        parser.error('Input must be a bounded regular CPIO file')
    with args.cpio.open('rb') as stream:
        data = stream.read(AUDIT.LIMIT + 1)
    result, report = prepare(data, args.expected_input_sha256)
    args.output.mkdir(parents=True, mode=0o700)
    (args.output / 'diagnostic.cpio').write_bytes(result)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
