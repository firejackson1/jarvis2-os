#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify all downloaded release assets against a reviewed staging receipt."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


RECEIPT = 'release-asset-receipt.json'
CHECKSUMS = 'SHA256SUMS.txt'
METADATA = {RECEIPT, CHECKSUMS}
NAME = r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}'

spec = importlib.util.spec_from_file_location('release_packaging', Path(__file__).with_name('package-candidate.py'))
PACK = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PACK)


def read_metadata(path):
    with PACK.regular(path).open('rb') as stream:
        data = stream.read(1048577)
    if len(data) > 1048576:
        raise ValueError('Release metadata exceeds one MiB')
    return data


def verify(directory, receipt_pin):
    PACK.sha256_value(receipt_pin)
    receipt_data = read_metadata(directory / RECEIPT)
    if hashlib.sha256(receipt_data).hexdigest() != receipt_pin:
        raise ValueError('Release receipt SHA-256 differs from the reviewed pin')
    receipt = json.loads(receipt_data, object_pairs_hook=PACK.unique_object)
    if (not isinstance(receipt, dict) or type(receipt.get('format')) is not int or
        receipt['format'] not in (1, 2) or
        receipt.get('kind') != 'unofficial-developer-preview-staging-receipt'):
        raise ValueError('Unsupported staging receipt')
    revisions = {key: receipt.get(key) for key in ('product_source_revision', 'packaging_tool_revision')}
    if any(not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value)
           for value in revisions.values()):
        raise ValueError('Staging receipt requires full source and tool revisions')
    if not isinstance(receipt.get('assets'), list) or not receipt['assets']:
        raise ValueError('Staging receipt requires an asset inventory')

    expected = {}
    for asset in receipt['assets']:
        if not isinstance(asset, dict) or set(asset) != {'file', 'bytes', 'sha256', 'role'}:
            raise ValueError('Invalid release asset entry')
        name = asset['file']
        if (not isinstance(name, str) or not re.fullmatch(NAME, name) or
            name in METADATA or name in expected or
            type(asset['bytes']) is not int or asset['bytes'] <= 0 or
            not isinstance(asset['role'], str) or not asset['role']):
            raise ValueError('Invalid or duplicate release asset: ' + str(name))
        PACK.sha256_value(asset['sha256'])
        expected[name] = {'bytes': asset['bytes'], 'sha256': asset['sha256']}

    paths = PACK.inventory(directory, set(expected) | METADATA)
    checksum_data = read_metadata(paths[CHECKSUMS])
    checksums = {}
    for line in checksum_data.decode('ascii').splitlines():
        record = re.fullmatch(r'([0-9a-f]{64})  (' + NAME + ')', line)
        if record is None or record[2] in checksums:
            raise ValueError('Checksum list has an invalid or duplicate entry')
        checksums[record[2]] = record[1]
    pins = {name: record['sha256'] for name, record in expected.items()}
    if checksums != {**pins, RECEIPT: receipt_pin}:
        raise ValueError('Checksum list must name the exact assets and reviewed receipt')

    for name, record in expected.items():
        path = paths[name]
        if path.stat().st_size != record['bytes'] or PACK.digest(path) != record['sha256']:
            raise ValueError('Asset bytes differ from their reviewed record: ' + name)
    if read_metadata(paths[RECEIPT]) != receipt_data or read_metadata(paths[CHECKSUMS]) != checksum_data:
        raise ValueError('Release metadata changed during verification')
    expected[RECEIPT] = {'bytes': len(receipt_data), 'sha256': receipt_pin}
    expected[CHECKSUMS] = {'bytes': len(checksum_data), 'sha256': hashlib.sha256(checksum_data).hexdigest()}
    return {**revisions, 'files': dict(sorted(expected.items())), 'release_qualification_checked': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--receipt-sha256', required=True)
    args = parser.parse_args()
    try:
        result = verify(args.directory, args.receipt_sha256)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Release asset verification failed: {error}\n')
    print(json.dumps(result, indent=2))
