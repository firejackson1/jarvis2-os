#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Derive a reviewed LCARS vendor_boot from a local stock image and plug-in."""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from build_stock_lcars import ROOT, STOCK_VENDOR_BOOT, compress_replacement, unpack_stock_recovery
from repack import digest, repack


AVBTOOL_PROJECT = 'LineageOS/android_external_avb'
AVBTOOL_REVISION = 'f18dc828607cce4bc2266f1b6c1369425f3fbcf9'
AVBTOOL_SHA256 = 'f8e82d9eb64093972cc2e04fbcec5c86a10cb2cac9f871c7a55490bb3b6f48eb'
# Stock build 15640252 records the vendor_boot hash in the signed parent vbmeta.
VENDOR_BOOT_BYTES = 67108864
VENDOR_BOOT_SALT = '9c36d1cb9303ad93fda0f340d31b24ccf8892ee3a1d9198bb6b94acf0772d625'
VENDOR_BOOT_FINGERPRINT = 'onn/jarvis2/jarvis2:14/URO3.260203.035.A1/15640252:user/release-keys'


def require_digest(path, expected):
    if not re.fullmatch('[a-f0-9]{64}', expected) or not path.is_file() or digest(path) != expected:
        raise ValueError(f'SHA-256 mismatch or missing required file: {path.name}')


def materialize(kit, stock, plugin, plugin_sha256, image_sha256, output):
    kit, stock, plugin, output = (path.resolve() for path in (kit, stock, plugin, output))
    if output.exists() or any(output.is_relative_to(path) for path in (ROOT, kit)):
        raise ValueError('Use a fresh output directory outside the source and tool kit')
    if not re.fullmatch('[a-f0-9]{64}', image_sha256):
        raise ValueError('A reviewed final image SHA-256 is required')
    require_digest(stock, STOCK_VENDOR_BOOT)
    require_digest(plugin, plugin_sha256)
    host = kit / 'out/host/linux-x86/bin'
    pins = json.loads((ROOT / 'fixture-tool-pins.json').read_text())['files']
    for pin in pins.values():
        require_digest(host / pin['destination'], pin['sha256'])
    avbtool = kit / 'external/avb/avbtool.py'
    require_digest(avbtool, AVBTOOL_SHA256)
    lz4 = shutil.which('lz4')
    if not lz4:
        raise ValueError('An installed lz4 command is required')

    with TemporaryDirectory(prefix='jarvis2-lcars-materialize-') as scratch:
        work = Path(scratch)
        cpio = unpack_stock_recovery(host, stock, work, lz4)
        fragment, untouched = compress_replacement(cpio, plugin.read_bytes(), work, lz4)
        require_digest(stock, STOCK_VENDOR_BOOT)
        unsigned = work / 'unsigned'
        repack(kit, stock, fragment, unsigned, VENDOR_BOOT_BYTES)
        image = work / 'vendor_boot.img'
        (unsigned / 'vendor_boot-unsigned.img').rename(image)
        tool = [sys.executable, avbtool]
        subprocess.run([*tool, 'add_hash_footer', '--image', image, '--partition_name', 'vendor_boot',
                        '--partition_size', str(VENDOR_BOOT_BYTES), '--algorithm', 'NONE',
                        '--hash_algorithm', 'sha256', '--salt', VENDOR_BOOT_SALT,
                        '--internal_release_string', 'avbtool 1.2.0', '--prop',
                        'com.android.build.vendor_boot.fingerprint:' + VENDOR_BOOT_FINGERPRINT],
                       check=True)
        subprocess.run([*tool, 'verify_image', '--image', image], check=True, capture_output=True)
        require_digest(image, image_sha256)
        require_digest(plugin, plugin_sha256)
        output.mkdir(mode=0o700)
        shutil.copyfile(image, output / image.name)
        require_digest(output / image.name, image_sha256)
    report = {'image': image.name, 'bytes': VENDOR_BOOT_BYTES, 'sha256': image_sha256,
              'stock_vendor_boot_sha256': STOCK_VENDOR_BOOT, 'plugin_sha256': plugin_sha256,
              'unchanged_recovery_records': untouched, 'leaf_verified': True,
              'parent_vbmeta_verified': False, 'device_contacted': False}
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-kit', type=Path, required=True)
    parser.add_argument('--stock-vendor-boot', type=Path, required=True)
    parser.add_argument('--plugin', type=Path, required=True)
    parser.add_argument('--plugin-sha256', required=True)
    parser.add_argument('--expected-image-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = materialize(args.tool_kit, args.stock_vendor_boot, args.plugin, args.plugin_sha256,
                             args.expected_image_sha256, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Materialization failed: {error}\n')
    print(json.dumps(result, indent=2))
