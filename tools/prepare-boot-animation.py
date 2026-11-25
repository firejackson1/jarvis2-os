#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare interruptible Jarvis2 boot artwork on the build host."""
import argparse,hashlib,io,json,shutil,struct,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED='87e2aa9ceda3fc1fdbf787dad06687eedc12efeca6a0046d3a76a68f6d03ad50'
def validate(path):
    with zipfile.ZipFile(path) as z:
        names=set(z.namelist())
        if len(names)!=len(z.infolist()):raise ValueError('Duplicate animation entry')
        for info in z.infolist():
            name=Path(info.filename)
            if name.is_absolute() or '..' in name.parts:raise ValueError('Unsafe animation entry')
            if info.compress_type!=zipfile.ZIP_STORED:raise ValueError('Animation entries must be stored uncompressed')
        lines=[line.split() for line in z.read('desc.txt').decode('utf-8').splitlines() if line.strip() and not line.lstrip().startswith('#')]
        if not lines or len(lines[0])!=3:raise ValueError('Invalid animation dimensions')
        dimensions=tuple(map(int,lines[0]))
        if any(v<=0 for v in dimensions):raise ValueError('Invalid animation dimensions')
        if len(lines)<2:raise ValueError('Missing animation parts')
        for fields in lines[1:]:
            if len(fields)!=4 or fields[0]!='p':raise ValueError('Only interruptible p parts are allowed; completion parts delay boot')
            if any(int(v)<0 for v in fields[1:3]):raise ValueError('Invalid repeat or pause')
            directory=fields[3]
            if '/' in directory or directory in ('.','..'):raise ValueError('Invalid part directory')
            frames=[name for name in names if name.startswith(directory+'/') and name.endswith('.png')]
            if not frames:raise ValueError('Missing part frames')
            for name in frames:
                with z.open(name) as frame:
                    if frame.read(8)!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid PNG frame')
    return dimensions

def prepare(path):
    if path.stat().st_size>32*1024*1024:raise ValueError('Animation size limit exceeded')
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=EXPECTED:raise ValueError('Expected the verified no-delay animation, not the completion-required original')
    dimensions=validate(path)
    output=ROOT/'prebuilts';output.mkdir(exist_ok=True)
    target=output/'bootanimation.zip'
    if target.is_symlink():raise ValueError('Unexpected animation output symlink')
    shutil.copyfile(path,target)
    (output/'bootanimation-provenance.json').write_text(json.dumps({'sha256':actual,'dimensions_fps':dimensions,'interruptible_parts_only':True,'installed':False,'redistribution_rights_reviewed':False},indent=2)+'\n')
    print('Exact no-delay animation staged locally. Artwork redistribution review and fresh-image boot test remain required.')


def png_chunk(kind, data):
    crc = zlib.crc32(kind + data)
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', crc)


def neutral_frame(width, height, active):
    stride = width + 1  # Each unfiltered PNG row starts with a zero filter byte.
    pixels = bytearray(stride * height)
    for dot in range(4):
        center = width // 2 - 15 + dot * 10
        shade = 224 if dot == active else 72
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    pixels[(height // 2 + dy) * stride + 1 + center + dx] = shade
    header = struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', header)
            + png_chunk(b'IDAT', zlib.compress(pixels, level=0)) + png_chunk(b'IEND', b''))


def generate_neutral(output):
    width, height, fps = 320, 180, 12
    entries = {'desc.txt': f'{width} {height} {fps}\np 0 0 pulse\n'.encode('ascii')}
    for active in range(4):
        frame = neutral_frame(width, height, active)
        for index in range(active * 3, active * 3 + 3):
            entries[f'pulse/{index:05d}.png'] = frame
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_STORED)
    with output.open('xb') as stream:
        stream.write(buffer.getvalue())
    print(hashlib.sha256(buffer.getbuffer()).hexdigest())


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    selection = p.add_mutually_exclusive_group(required=True)
    selection.add_argument('animation', type=Path, nargs='?', help='verified owner artwork to stage')
    selection.add_argument('--neutral', type=Path, metavar='OUTPUT', help='write original unbranded animation')
    a = p.parse_args()
    if a.neutral is not None:
        try:
            generate_neutral(a.neutral)
        except OSError as error:
            p.exit(1, f'Cannot write animation: {error}\n')
    else:
        prepare(a.animation.resolve())
