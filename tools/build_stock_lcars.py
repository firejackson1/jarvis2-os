#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the unsigned ARM32 LCARS prototype against pinned local stock inputs."""

import argparse
import json
from pathlib import Path
import stat
import subprocess
from tempfile import TemporaryDirectory

from prepare_ramdisk import AUDIT, original, record, replace_payload
from repack import digest, recovery_fragment, repack


ROOT = Path(__file__).resolve().parents[1]
STOCK_VENDOR_BOOT = 'c017791c8e52678595a03b902237dcb15a4e8adeb3d35fdb2232838750e4233a'
STOCK_HEADERS = {
    'recovery_ui/include/recovery_ui/device.h':
        'd689b8e785984975575bf7a7df93bf741e4c2a6b92d4b4e3dcb4953294b67bc2',
    'recovery_ui/include/recovery_ui/screen_ui.h':
        'd909a9a09bd73f264d12e8e940a879885e45aad09afc244728f364cc0ec9489f',
    'recovery_ui/include/recovery_ui/ui.h':
        'd32a581f061bb96af6a985b0fded1c8a290dfaf8f4ae2ead09258e132390146f',
    'otautil/include/otautil/boot_state.h':
        '64a001dcffbeb048835fc860a953e7042f8fe3f1017e5f351ad4fcfe3a38684c',
}
EXTENSION = 'system/lib/librecovery_ui_ext.so'
STOCK_ALIAS = 'system/lib/librecovery_ui_onn_stock.so'
LINK_LIBS = ('recovery_ui', 'dl', 'c++', 'c', 'm')


def add_extension(data, plugin):
    before = AUDIT.parse_cpio(data)
    if EXTENSION not in before or STOCK_ALIAS in before:
        raise ValueError('Expected the original unmodified Recovery extension')
    extension = original(before[EXTENSION])
    if not stat.S_ISREG(extension['mode']) or extension['nlink'] != 1:
        raise ValueError('Expected a regular, unshared stock extension')
    for payload in (extension['data'], plugin):
        elf = AUDIT.elf_info(payload)
        if not elf or (elf['machine'], elf['bits'], elf['elf_type']) != ('ARM', 32, 3):
            raise ValueError('Both Recovery extensions must be ARM32 shared libraries')

    raw = record(data, before[EXTENSION])
    header = bytearray(raw[:110])
    name = STOCK_ALIAS.encode() + b'\0'
    trailer = max(original(entry)['record_span'][1] for entry in before.values())
    trailer_header = data[trailer:trailer + 110]
    name_size = int(trailer_header[94:102], 16)
    trailer_name = data[trailer + 110:trailer + 110 + name_size]
    if trailer_name != b'TRAILER!!!\0':
        raise ValueError('Expected the stock archive trailer')
    max_inode = max(original(entry)['ino'] for entry in before.values())
    inode = max(max_inode, int(trailer_header[6:14], 16)) + 1
    header[6:14] = f'{inode:08x}'.encode()
    header[94:102] = f'{len(name):08x}'.encode()
    alias = bytes(header) + name
    alias += b'\0' * (-len(alias) % 4) + extension['data']
    alias += b'\0' * (-len(alias) % 4)

    start, end = extension['record_span']
    trailer_end = (trailer + 110 + name_size + 3) & ~3
    result = data[:start] + replace_payload(raw, plugin) + alias + data[end:trailer_end]
    result += b'\0' * (-len(result) % 512)

    after = AUDIT.parse_cpio(result)
    if set(after) != set(before) | {STOCK_ALIAS}:
        raise ValueError('Unexpected archive inventory change')
    if after[EXTENSION]['data'] != plugin or after[STOCK_ALIAS]['data'] != extension['data']:
        raise ValueError('Archive does not contain both expected extensions')
    for path in before.keys() - {EXTENSION}:
        if record(data, before[path]) != record(result, after[path]):
            raise ValueError(f'Unexpected change to {path}')
    return result, len(before) - 1


def compile_extension(android, aosp, work, cpio):
    entries = AUDIT.parse_cpio(cpio)
    libraries = work / 'stock-libs'
    libraries.mkdir()
    for library in LINK_LIBS:
        name = f'lib{library}.so'
        entry = AUDIT.resolve(entries, 'system/lib/' + name)
        if not entry or not stat.S_ISREG(entry['mode']):
            raise ValueError(f'Missing stock ARM32 library {name}')
        (libraries / name).write_bytes(entry['data'])

    toolchain = android / 'prebuilts/clang/host/linux-x86/clang-r510928/bin'
    clang = toolchain / 'clang++'
    sys_headers = [
        'external/libcxx/include', 'bionic/libc/include', 'bionic/libc/kernel/uapi',
        'bionic/libc/kernel/uapi/asm-arm', 'bionic/libc/kernel/android/uapi',
    ]
    obj = work / 'stock_lcars.o'
    cmd = [clang, '--target=armv7a-linux-androideabi34', '-march=armv7-a', '-mthumb',
           '-std=c++17', '-fPIC', '-fno-exceptions', '-fno-rtti', '-Wall', '-Wextra',
           '-Werror', '-Wno-unused-parameter', '-nostdinc++']
    for directory in sys_headers:
        cmd += ['-isystem', android / directory]
    cmd += ['-I', aosp / 'recovery_ui/include', '-Wno-inconsistent-missing-override',
            '-I', aosp / 'otautil/include', '-I', ROOT, '-O2', '-fvisibility=hidden',
            '-c', ROOT / 'recovery/stock_lcars.cpp', '-o', obj]
    subprocess.run(cmd, check=True)
    resources = Path(subprocess.check_output([clang, '--print-resource-dir'], text=True).strip())
    library = work / Path(EXTENSION).name
    subprocess.run([toolchain / 'ld.lld', '-m', 'armelf_linux_eabi', '-shared', '-soname', library.name,
                    '--no-undefined', '--as-needed', '-z', 'relro', '-z', 'now', '-o', library,
                    obj, '-L', libraries, *[f'-l{name}' for name in LINK_LIBS],
                    resources / 'lib/linux/libclang_rt.builtins-arm-android.a'], check=True)
    return library


def build(android, aosp, stock, output):
    android, aosp, stock, output = (path.resolve() for path in (android, aosp, stock, output))
    if output.exists() or any(output.is_relative_to(root) for root in (android, aosp, ROOT)):
        raise ValueError('Use a fresh output directory outside the source checkouts')
    if not stock.is_file() or digest(stock) != STOCK_VENDOR_BOOT:
        raise ValueError('Stock vendor_boot SHA256 does not match the supported firmware')
    for path, expected in STOCK_HEADERS.items():
        if digest(aosp / path) != expected:
            raise ValueError(f'AOSP Recovery header differs from the pinned input: {path}')

    host = android / 'out/host/linux-x86/bin'
    with TemporaryDirectory(prefix='jarvis2-stock-lcars-') as scratch:
        work = Path(scratch)
        raw = subprocess.check_output([host / 'unpack_bootimg', '--boot_img', stock, '--out',
                                       work / 'stock', '--format', 'mkbootimg', '-0'])
        if not raw.endswith(b'\0'):
            raise ValueError('Unexpected unpack_bootimg output')
        stock_fragment = recovery_fragment(raw[:-1].decode().split('\0'))
        cpio = subprocess.check_output([host / 'lz4', '-q', '-d', '-c', stock_fragment])
        plugin = compile_extension(android, aosp, work, cpio)
        updated, untouched = add_extension(cpio, plugin.read_bytes())
        archive = work / 'stock-lcars.cpio'
        archive.write_bytes(updated)
        fragment = work / 'stock-lcars.cpio.lz4'
        subprocess.run([host / 'lz4', '-q', '-l', '-12', archive, fragment], check=True)
        if subprocess.check_output([host / 'lz4', '-q', '-d', '-c', fragment]) != updated:
            raise ValueError('Compressed recovery archive failed readback')
        if digest(stock) != STOCK_VENDOR_BOOT:
            raise ValueError('Stock vendor_boot changed during the build')
        report = repack(android, stock, fragment, output, 67108864)
        (output / plugin.name).write_bytes(plugin.read_bytes())
        report.update({'prototype': 'stock-arm32-lcars', 'stock_vendor_boot_sha256': STOCK_VENDOR_BOOT,
                       'unchanged_recovery_records': untouched, 'plugin_sha256': digest(plugin)})
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--android-tree', type=Path, required=True)
    parser.add_argument('--aosp-recovery', type=Path, required=True)
    parser.add_argument('--stock-vendor-boot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build(args.android_tree, args.aosp_recovery, args.stock_vendor_boot, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Build failed: {error}\n')
    print(json.dumps(result, indent=2))
