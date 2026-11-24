#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--fetch-headers', action='store_true')
args = parser.parse_args()
pins = json.loads((root / 'upstream-pins.json').read_text())
cache = root / '.cache/headers/recovery_ui'
cache.mkdir(parents=True, exist_ok=True)
for name, expected in pins['headers_sha256'].items():
    path = cache / name
    if not path.is_file():
        if not args.fetch_headers:
            parser.error('Missing pinned header; rerun with --fetch-headers')
        url = ('https://raw.githubusercontent.com/LineageOS/android_bootable_recovery/'
               + pins['android_bootable_recovery'] + '/recovery_ui/include/recovery_ui/' + name)
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError('Downloaded header checksum mismatch: ' + name)
        path.write_bytes(content)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Cached header checksum mismatch: ' + name)
flags = ['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror']
subprocess.run(flags + ['-I.', 'tests/button_test.cpp', '-o', '.cache/button-test'],
               cwd=root, check=True)
subprocess.run([str(root / '.cache/button-test')], check=True)
for name in ('lcars_layout', 'lcars_menu'):
    binary = root / ('.cache/' + name + '-test')
    subprocess.run(flags + ['-include', 'tests/bionic_annotations.h', '-I.', '-I.cache/headers',
                           'tests/' + name + '_test.cpp', '-o', str(binary)], cwd=root, check=True)
    subprocess.run([str(binary)], check=True)

subprocess.run(flags + ['-fsyntax-only', '-include', 'tests/bionic_annotations.h',
                        '-I.cache/headers', 'recovery/recovery_ui.cpp'], cwd=root, check=True)
subprocess.run(['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-v'],
               cwd=root, check=True)
print('Button behavior and real LineageOS 24 recovery-header syntax checks passed.')
print('This is not an Android link, image build, AVB acceptance or hardware boot test.')
