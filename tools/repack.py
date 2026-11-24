#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline v4 recovery-fragment replacement using AOSP's image tools."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


FILE_FLAGS = {'--dtb', '--vendor_bootconfig', '--vendor_ramdisk_fragment'}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pairs(args):
    if len(args) % 2:
        raise ValueError('Unexpected AOSP argument format')
    return list(zip(args[::2], args[1::2]))


def recovery_fragment(args):
    if ('--header_version', '4') not in pairs(args):
        raise ValueError('Only vendor_boot header v4 is supported')
    name = kind = None
    matches = []
    for flag, value in pairs(args):
        if flag == '--ramdisk_name':
            name = value
        elif flag == '--ramdisk_type':
            kind = value
        elif flag == '--vendor_ramdisk_fragment':
            if name == 'recovery':
                if kind != '2':
                    raise ValueError('Recovery fragment has an unexpected type')
                matches.append(Path(value))
            name = kind = None
    if len(matches) != 1:
        raise ValueError('Expected exactly one named recovery fragment')
    return matches[0]


def canonical(args):
    replacement = recovery_fragment(args)
    return [(flag, ('recovery-replacement' if Path(value) == replacement else digest(value))
             if flag in FILE_FLAGS else value) for flag, value in pairs(args)]


def repack(android_tree, stock, ramdisk, output, partition_size):
    tree, stock, ramdisk, output = map(lambda p: Path(p).resolve(),
                                      (android_tree, stock, ramdisk, output))
    if output.exists() or output.is_relative_to(tree):
        raise ValueError('Use a fresh output directory outside the Android checkout')
    if not stock.is_file() or not ramdisk.is_file() or partition_size <= 65536:
        raise ValueError('Regular image inputs and a valid partition budget are required')
    tools = tree / 'out/host/linux-x86/bin'
    for name in ('mkbootimg', 'unpack_bootimg'):
        if not (tools / name).is_file():
            raise ValueError('Missing built AOSP host tool: ' + name)
    initial = {str(p): digest(p) for p in (stock, ramdisk)}
    output.mkdir(parents=True)

    def unpack(image, destination):
        raw = subprocess.check_output([str(tools / 'unpack_bootimg'), '--boot_img',
                                       str(image), '--out', str(destination),
                                       '--format', 'mkbootimg', '-0'])
        if not raw.endswith(b'\0'):
            raise ValueError('AOSP tool did not return NUL-separated arguments')
        return [value.decode() for value in raw[:-1].split(b'\0')]

    before = unpack(stock, output / 'before')
    original = canonical(before)
    destination = recovery_fragment(before)
    shutil.copyfile(ramdisk, destination)
    image = output / 'vendor_boot-unsigned.img'
    subprocess.run([str(tools / 'mkbootimg'), *before, '--vendor_boot', str(image)], check=True)
    if image.stat().st_size > partition_size - 65536:
        image.unlink()
        raise ValueError('Repacked image leaves insufficient space for an AVB footer')
    after = unpack(image, output / 'after')
    if canonical(after) != original or digest(recovery_fragment(after)) != digest(ramdisk):
        image.unlink()
        raise ValueError('Protected fields/payloads changed or replacement did not match')
    if any(digest(p) != sha for p, sha in initial.items()):
        image.unlink()
        raise ValueError('An input changed during packaging')
    report = {'header_version': 4, 'protected_payloads_unchanged': True,
              'recognized_header_fields_unchanged': True, 'inputs_unchanged': True,
              'image_bytes': image.stat().st_size, 'partition_bytes': partition_size,
              'image_sha256': digest(image), 'ramdisk_sha256': digest(ramdisk),
              'avb_signed': False, 'boot_tested': False, 'device_contacted': False,
              'android17_binary_verified': False}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--android-tree', type=Path, required=True)
    parser.add_argument('--stock-vendor-boot', type=Path, required=True)
    parser.add_argument('--recovery-ramdisk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--partition-size', type=int, default=67108864)
    args = parser.parse_args()
    print(json.dumps(repack(args.android_tree, args.stock_vendor_boot, args.recovery_ramdisk,
                           args.output, args.partition_size), indent=2))
