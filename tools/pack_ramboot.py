#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline legacy-v2 RAM boot packaging; no ADB, Fastboot or device operations."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

spec = importlib.util.spec_from_file_location('recovery_repack', Path(__file__).with_name('repack.py'))
IMAGE = importlib.util.module_from_spec(spec)
previous_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(IMAGE)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting

CMDLINE = 'rdinit=/ramboot-init panic=0'
ALLOWED_FLAGS = {'--header_version', '--kernel', '--ramdisk', '--dtb', '--pagesize',
                 '--base', '--kernel_offset', '--ramdisk_offset', '--second_offset',
                 '--tags_offset', '--dtb_offset', '--board', '--cmdline',
                 '--os_version', '--os_patch_level'}


def require_hash(path, expected):
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('An exact lowercase SHA256 input binding is required')
    if IMAGE.digest(path) != expected:
        raise ValueError('Image input does not match expected SHA256')


def pack(android_tools, reference, ramdisk, output, bindings, max_download_bytes):
    android_tools, reference, ramdisk, output = map(lambda p: Path(p).resolve(),
                                                  (android_tools,reference,ramdisk,output))
    if output.exists() or output.is_relative_to(android_tools):
        raise ValueError('Choose a fresh private output directory outside the tools tree')
    if max_download_bytes <= 0:
        raise ValueError('A positive download budget is required')
    for path,key in ((reference,'reference_boot'),(ramdisk,'ramdisk')):
        if not path.is_file() or path.stat().st_size > max_download_bytes:
            raise ValueError('Bounded regular image inputs are required')
        require_hash(path,bindings[key])
    tools = {}
    for name in ('mkbootimg','unpack_bootimg'):
        path = android_tools/name
        if not path.is_file(): path = android_tools/(name+'.py')
        if not path.is_file(): raise ValueError('Missing AOSP image tool: '+name)
        tools[name] = path

    def command(name, *args):
        tool = tools[name]
        return ([sys.executable] if tool.suffix == '.py' else []) + [str(tool),*args]

    def unpack(path,destination):
        raw = subprocess.check_output(command('unpack_bootimg','--boot_img',str(path),
                                              '--out',str(destination),'--format','mkbootimg','-0'))
        if not raw.endswith(b'\0'):
            raise ValueError('AOSP tool did not return NUL-separated arguments')
        args = [v.decode() for v in raw[:-1].split(b'\0')]
        pairs = IMAGE.pairs(args)
        flags = [k for k,v in pairs]
        if len(set(flags)) != len(flags) or set(flags) - ALLOWED_FLAGS:
            raise ValueError('Unreviewed or duplicate legacy image fields')
        return dict(pairs)

    def protected(fields):
        return {k:IMAGE.digest(v) if k in ('--kernel','--dtb') else v
                for k,v in fields.items() if k not in ('--ramdisk','--cmdline')}

    output.mkdir(mode=0o700,parents=True)
    before = unpack(reference,output/'before')
    if before.get('--header_version') != '2' or before.get('--pagesize') != '0x00000800':
        raise ValueError('Only the reviewed legacy-v2, 2048-byte-page layout is supported')
    if before.get('--cmdline') != 'rdinit=/ramboot-init panic=5':
        raise ValueError('Reference image has an unreviewed init command line')
    for flag,key in (('--kernel','kernel'),('--dtb','dtb')):
        if flag not in before: raise ValueError('Reference lacks a required protected payload')
        require_hash(before[flag],bindings[key])
    original = protected(before)
    args = {**before,'--ramdisk':str(ramdisk),'--cmdline':CMDLINE}
    image = output/'ramboot-unsigned.img'
    try:
        subprocess.run(command('mkbootimg',*[item for pair in args.items() for item in pair],
                               '--output',str(image)),check=True)
        if image.stat().st_size > max_download_bytes:
            raise ValueError('Boot image exceeds the supplied download budget')
        after = unpack(image,output/'after')
        if (protected(after) != original or after.get('--cmdline') != CMDLINE
                or IMAGE.digest(after['--ramdisk']) != bindings['ramdisk']):
            raise ValueError('RAM image roundtrip changed protected fields or payloads')
        for path,key in ((reference,'reference_boot'),(ramdisk,'ramdisk')):
            require_hash(path,bindings[key])
    except Exception:
        image.unlink(missing_ok=True)
        raise
    report = {'header_version':2,'image_bytes':image.stat().st_size,
              'image_sha256':IMAGE.digest(image),'bindings':dict(bindings),
              'aosp_tools_sha256':{k:IMAGE.digest(v) for k,v in tools.items()},
              'max_download_bytes':max_download_bytes,'device_budget_currently_verified':False,
              'protected_payloads_unchanged':True,
              'recognized_header_fields_unchanged_except_cmdline':True,
              'changed_header_fields':['--cmdline'], 'replaced_payloads':['ramdisk'],
              'inputs_unchanged':True,'cmdline':CMDLINE,
              'bootloader_relocation_verified':False,'runtime_startup_qualified':False,
              'avb_signed':False,'boot_tested':False,'device_contacted':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--android-tools',type=Path,required=True)
    parser.add_argument('--reference-boot',type=Path,required=True)
    parser.add_argument('--ramdisk',type=Path,required=True)
    parser.add_argument('--bindings',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-download-bytes',type=int,default=128*1024*1024)
    args = parser.parse_args()
    print(json.dumps(pack(args.android_tools,args.reference_boot,args.ramdisk,args.output,
                           json.loads(args.bindings.read_text()),args.max_download_bytes),indent=2))
