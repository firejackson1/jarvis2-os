#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compile the port's UI into an Android ARM object, without linking an image."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--clang', type=Path, required=True)
parser.add_argument('--cxx-headers', type=Path, required=True)
parser.add_argument('--bionic', type=Path, required=True, help='Bionic libc directory')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--headers-origin', required=True, help='Record the actual platform header origin')
parser.add_argument('--arch', choices=('arm64', 'arm'), default='arm64')
args = parser.parse_args()
compiler, cxx, bionic, output = [p.resolve() for p in
                               (args.clang, args.cxx_headers, args.bionic, args.output)]
if output.exists() or any(output.is_relative_to(p) for p in (cxx, bionic, compiler.parent)):
    parser.error('Use a fresh output directory outside compiler/header inputs')
pins = json.loads((root / 'upstream-pins.json').read_text())
for name, expected in pins['headers_sha256'].items():
    path = root / '.cache/headers/recovery_ui' / name
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Recovery interface header checksum mismatch: ' + name)
resource = Path(subprocess.check_output([str(compiler), '-print-resource-dir'], text=True).strip())
includes = [cxx, resource / 'include', bionic / 'include',
            bionic / ('kernel/uapi/asm-arm64' if args.arch == 'arm64' else 'kernel/uapi/asm-arm'), bionic / 'kernel/uapi',
            bionic / 'kernel/android/uapi', root / '.cache/headers']
if any(not p.is_dir() for p in includes):
    parser.error('A required include directory is missing')
output.mkdir(parents=True)
obj = output / ('recovery_ui.' + args.arch + '.o')
target = 'aarch64-linux-android34' if args.arch == 'arm64' else 'armv7a-linux-androideabi34'
arch_flags = ['-mno-outline-atomics'] if args.arch == 'arm64' else ['-mthumb', '-mfpu=neon', '-mfloat-abi=softfp']
command = [str(compiler), '--target=' + target, '-std=c++17',
           *arch_flags, '-fPIC', '-fno-exceptions',
           '-fno-rtti', '-Wall', '-Wextra', '-Werror', '-nostdinc', '-nostdinc++']
for path in includes:
    command += ['-isystem', str(path)]
command += ['-c', str(root / 'recovery/recovery_ui.cpp'), '-o', str(obj)]
subprocess.run(command, check=True)
header = obj.read_bytes()[:64]
elf_class = 2 if args.arch == 'arm64' else 1
if header[:7] != b'\x7fELF' + bytes([elf_class, 1, 1]):
    raise ValueError('Compiler did not produce the expected little-endian ELF class')
kind, machine = struct.unpack_from('<HH', header, 16)
flags = struct.unpack_from('<I', header, 48 if elf_class == 2 else 36)[0]
expected_machine = 183 if elf_class == 2 else 40
if (kind, machine) != (1, expected_machine):
    raise ValueError('Compiler produced the wrong object architecture or type')
if elf_class == 1 and (flags >> 24 != 5 or flags & 0x400):
    raise ValueError('Expected ARM EABI5 object without hard-float ABI')
with compiler.open('rb') as stream:
    compiler_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
report = {'artifact': obj.name, 'sha256': hashlib.sha256(obj.read_bytes()).hexdigest(),
          'class': 'ELF64' if elf_class == 2 else 'ELF32',
          'machine': 'AArch64' if elf_class == 2 else 'ARM', 'type': 'REL',
          'eabi_version': None if elf_class == 2 else 5,
          'recovery_interface_commit': pins['android_bootable_recovery'],
          'compiler_sha256': compiler_sha,
          'compiler_version': subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
          'platform_headers_origin': args.headers_origin, 'target_api': 34,
          'android17_full_build': False, 'linked': False, 'boot_tested': False}
(output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
