#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Append the private guard/runtime overlay to a diagnostic CPIO; no device access."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ramdisk_prepare', ROOT / 'tools/prepare_ramdisk.py')
PREPARE = importlib.util.module_from_spec(spec)
previous_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(PREPARE)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting
AUDIT = PREPARE.AUDIT


def checked(data, digest):
    if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('An exact lowercase SHA256 input binding is required')
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Private input does not match its expected SHA256')
    return data


def bounded_file(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > AUDIT.LIMIT:
        raise ValueError('Input must be a bounded regular file')
    with path.open('rb') as stream:
        data = stream.read(AUDIT.LIMIT + 1)
    if len(data) > AUDIT.LIMIT:
        raise ValueError('Input exceeds size limit')
    return data


def newc(entries):
    """Serialize only new overlay records; never flatten the original archive."""
    data = bytearray()
    for ino, (name, (mode, payload)) in enumerate(
            [*entries.items(), ('TRAILER!!!', (0, b''))], 1):
        encoded = name.encode() + b'\0'
        fields = [ino, mode, 0, 0, 2 if stat.S_ISDIR(mode) else 1, 0,
                  len(payload), 0, 0, 0, 0, len(encoded), 0]
        data += b'070701' + ''.join(f'{v:08x}' for v in fields).encode() + encoded
        data += b'\0' * (-len(data) % 4)
        data += payload
        data += b'\0' * (-len(data) % 4)
    return bytes(data)


def module_sequence(function):
    # Source-owned library defines functions only. Calling a sequence function
    # prints names; no mount, module or block utility is invoked here.
    result = subprocess.run(['/bin/sh', '-c', '. "$1"; ' + function, 'sequence',
                             str(ROOT / 'ramboot/startup-guard.sh')],
                            check=True, capture_output=True, text=True, timeout=5)
    names = result.stdout.splitlines()
    if not names or len(set(names)) != len(names) or any(
            not re.fullmatch(r'[A-Za-z0-9_-]+\.ko', n) for n in names):
        raise ValueError('Invalid source-owned module sequence')
    return names


def assemble(base, expected_sha256, inputs, *, mode='recovery'):
    if mode not in ('recovery', 'usb-log-only'):
        raise ValueError('Unknown RAM diagnostic mode')
    checked(base, expected_sha256)
    if len(base) % 4:
        raise ValueError('Base CPIO must end on a newc alignment boundary')
    parsed = AUDIT.parse_cpio(base)
    audit = AUDIT.audit_layers([parsed], expected_recovery_arch='arm64')
    if audit['required']['init']['machine'] != 'AArch64' or audit['required']['init']['bits'] != 64:
        raise ValueError('Diagnostic init must also be native ARM64')
    if audit['blocked_artifacts']:
        raise ValueError('Diagnostic fragment contains blocked trust material')
    if (parsed[PREPARE.FSTAB]['data'] != b'ramdisk /tmp ramdisk defaults defaults\n'
            or b'import /ramboot/init.hardware.rc\n' not in parsed[PREPARE.INIT]['data']
            or b'service recovery /system/bin/recovery --show_text\n'
            not in parsed[PREPARE.INIT]['data']):
        raise ValueError('Input is not the prepared diagnostic fragment')
    private = {}
    names = ['busybox', 'musl_loader', 'platform_cpio']
    if mode == 'recovery':
        names.append('mmc_partitions')
    for name in names:
        item = inputs[name]
        private[name] = checked(bounded_file(item['path']), item['sha256'])
    release = inputs['kernel_release']
    if not isinstance(release, str) or not re.fullmatch(r'[A-Za-z0-9_.+\-]{1,200}', release):
        raise ValueError('An exact kernel release is required')
    if mode == 'recovery':
        numbers = private['mmc_partitions'].decode('ascii').splitlines()
        if (not numbers or len(set(numbers)) != len(numbers)
                or any(not re.fullmatch('[1-9][0-9]{0,7}', n) for n in numbers)
                or not private['mmc_partitions'].endswith(b'\n')):
            raise ValueError('Invalid physical partition inventory')
    for name in ('busybox', 'musl_loader'):
        info = AUDIT.elf_info(private[name])
        if not info or (info['bits'], info['machine']) != (64, 'AArch64') or info['elf_type'] not in (2,3):
            raise ValueError('Utility runtime must contain native ARM64 executables')
    platform = AUDIT.parse_cpio(private['platform_cpio'])
    # This source fragment contains kernel modules, not a second userspace layer.
    dependencies = {}
    for line in platform['lib/modules/modules.dep']['data'].decode().splitlines():
        name, deps = line.split(':', 1)
        key = str(PurePosixPath(name).name)
        if key in dependencies:
            raise ValueError('Duplicate stock module dependency record')
        dependencies[key] = [PurePosixPath(d).name for d in deps.split()]
    usb = module_sequence('guard_usb_module_sequence') if mode == 'usb-log-only' else []
    storage = module_sequence('guard_module_sequence') if mode == 'recovery' else []
    hardware = module_sequence('guard_hardware_sequence') if mode == 'recovery' else []
    if set(storage) & set(hardware):
        raise ValueError('Storage and hardware sequences overlap')
    entries = {}

    def add(name, payload=b'', mode=stat.S_IFREG | 0o644):
        if name in parsed or name in entries:
            raise ValueError('Overlay would replace an existing record: ' + name)
        for parent in reversed(PurePosixPath(name).parents):
            if str(parent) == '.':
                continue
            key = str(parent)
            old = parsed.get(key)
            if old and not stat.S_ISDIR(old['mode']):
                raise ValueError('Overlay parent is an alias or non-directory: ' + key)
            if not old and key not in entries:
                entries[key] = (stat.S_IFDIR | 0o755, b'')
        entries[name] = (mode, payload)

    source_payloads = {
        'ramboot-init': 'usb-log-init' if mode == 'usb-log-only' else 'init',
        'ramboot/startup-guard.sh': 'startup-guard.sh',
        'ramboot/init.hardware.rc': 'init.hardware.rc',
    }
    if mode == 'usb-log-only':
        source_payloads['ramboot/usb-log.sh'] = 'usb-log.sh'
    else:
        source_payloads['ramboot/storage-guard.sh'] = 'storage-guard.sh'
    for dest, source in source_payloads.items():
        add(dest, (ROOT / 'ramboot' / source).read_bytes(),
            stat.S_IFREG | (0o755 if dest == 'ramboot-init' else 0o644))
    add('system/bin/busybox', private['busybox'], stat.S_IFREG | 0o755)
    add('lib/ld-musl-aarch64.so.1', private['musl_loader'], stat.S_IFREG | 0o755)
    add('lib/libc.musl-aarch64.so.1', b'ld-musl-aarch64.so.1', stat.S_IFLNK | 0o777)
    add('ramboot/kernel.release', release.encode() + b'\n')
    if mode == 'recovery':
        add('ramboot/mmc.partitions', private['mmc_partitions'])
    loaded = set()
    manifests = ((usb, 'usb-modules.sha256'),) if mode == 'usb-log-only' else (
        (storage, 'modules.sha256'), (hardware, 'hardware.sha256'))
    for sequence, manifest in manifests:
        lines = []
        for name in sequence:
            if name not in dependencies or not set(dependencies[name]) <= loaded:
                raise ValueError('Unmet module dependency before load: ' + name)
            e = platform['lib/modules/' + name]
            info = AUDIT.elf_info(e['data'])
            if (not stat.S_ISREG(e['mode']) or not info
                    or (info['bits'], info['machine'], info['elf_type']) != (64,'AArch64',1)):
                raise ValueError('Stock module is not an ARM64 relocatable file')
            add('ramboot/modules/' + name, e['data'])
            lines.append(hashlib.sha256(e['data']).hexdigest() + '  ' + name + '\n')
            loaded.add(name)
        add('ramboot/' + manifest, ''.join(lines).encode())
    overlay = newc(entries)
    result = base + overlay
    if len(result) > AUDIT.LIMIT:
        raise ValueError('Assembled ramdisk exceeds size limit')
    final = AUDIT.audit_layers([parsed, AUDIT.parse_cpio(overlay)], expected_recovery_arch='arm64')
    if final['blocked_artifacts'] or final['overwritten_layer_entries']:
        raise ValueError('Assembled ramdisk has trust material or overwrites')
    return result, {
        'base_sha256': expected_sha256, 'base_bytes_preserved': True,
        'output_sha256': hashlib.sha256(result).hexdigest(), 'output_bytes': len(result),
        'overlay_sha256': hashlib.sha256(overlay).hexdigest(),
        'private_inputs_sha256': {n: hashlib.sha256(p).hexdigest() for n,p in private.items()},
        'source_files_sha256': {dest: hashlib.sha256(entries[dest][1]).hexdigest()
                                for dest in source_payloads},
        'storage_modules': storage, 'hardware_modules': hardware,
        'usb_modules': usb, 'mode': mode, 'android_init_handoff': mode == 'recovery',
        'kernel_release': release, 'archive_audit': final,
        'runtime_dependencies_verified': False, 'selinux_qualified': False,
        'boot_tested': False, 'device_contacted': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diagnostic-cpio', type=Path, required=True)
    parser.add_argument('--expected-input-sha256', required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--mode', choices=('recovery', 'usb-log-only'), default='recovery')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh private output directory')
    result, report = assemble(bounded_file(args.diagnostic_cpio), args.expected_input_sha256,
                              json.loads(bounded_file(args.inputs)), mode=args.mode)
    args.output.mkdir(parents=True, mode=0o700)
    (args.output / 'guarded.cpio').write_bytes(result)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
