#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Download checksum-pinned Python image tools into a fresh local directory."""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from materialize_stock_lcars import AVBTOOL_PROJECT, AVBTOOL_REVISION, AVBTOOL_SHA256, ROOT


def download(project, revision, source, expected):
    url = f'https://raw.githubusercontent.com/{project}/{revision}/{source}'
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f'Tool source does not match its pin: {source}')
    return data


def prepare(kit):
    if kit.exists() or kit.resolve().is_relative_to(ROOT):
        raise ValueError('Use a fresh tool-kit directory outside the source checkout')
    pins = json.loads((ROOT / 'fixture-tool-pins.json').read_text())
    files = {
        'out/host/linux-x86/bin/' + pin['destination']:
            download(pins['repository'], pins['revision'], source, pin['sha256'])
        for source, pin in pins['files'].items()
    }
    files['external/avb/avbtool.py'] = download(AVBTOOL_PROJECT, AVBTOOL_REVISION,
                                               'avbtool.py', AVBTOOL_SHA256)
    kit.mkdir(mode=0o700)
    for name, contents in files.items():
        path = kit / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        path.chmod(0o755)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool_kit', type=Path)
    args = parser.parse_args()
    try:
        prepare(args.tool_kit)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Tool kit preparation failed: {error}\n')
    print(f'Verified tool sources saved to {args.tool_kit}')
