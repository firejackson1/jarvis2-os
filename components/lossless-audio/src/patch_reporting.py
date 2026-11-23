#!/usr/bin/env python3
"""Exact-build Thumb patch: report DTS-HD and TrueHD/MAT1 independently.
Input is the reproducible upstream US patch1+2 output. No device writes.
"""
import hashlib, importlib.util, struct, sys
from pathlib import Path

def patch(work):
    work=Path(work)
    spec=importlib.util.spec_from_file_location('upstream',work/'upstream/patch_hal.py')
    ph=importlib.util.module_from_spec(spec);spec.loader.exec_module(ph)
    src=work/'candidate/audio.primary.amlogic.upstream.so'
    data=bytearray(src.read_bytes())
    assert hashlib.sha256(data).hexdigest()=='5a9b8238a36f332eaa11a43130a210b7b26f68b388c5fc590f29c90bf8032b79'
    obj=(work/'tools/reporting.o').read_bytes()
    # ELF32 .text section, independent of tool output formatting.
    shoff=struct.unpack_from('<I',obj,32)[0];size,num,names=struct.unpack_from('<HHH',obj,46)
    sections=[struct.unpack_from('<10I',obj,shoff+i*size) for i in range(num)]
    ns=sections[names];strings=obj[ns[4]:ns[4]+ns[5]]
    text=next(s for s in sections if strings[s[0]:].split(b'\0')[0]==b'.text')
    code=obj[text[4]:text[4]+text[5]]
    assert len(code)==40
    assert data[0x7ab24:0x7ab2a]==bytes.fromhex('05464ff48071')
    data[0x7ab24:0x7ab2a]=code[:6]
    # r5 now points 0xc0 bytes into the cap structure; adjust Atmos flag read.
    assert data[0x7ab4e:0x7ab52]==bytes.fromhex('95f8c400')
    data[0x7ab4e:0x7ab52]=ph.encode_thumb2_ldrb_w(0,5,4)
    B=0x8ab92;pool=0x8acbc;table=0x48982
    block=bytearray(code[6:])
    block[16:18]=ph.encode_thumb_ldr_pc(1,B+16,pool)
    block[28:32]=ph.encode_thumb2_blx(B+28,0x12b5e0)
    block[32:34]=ph.encode_thumb_b(B+32,0x8a9c0)
    data[B-0x10000:B-0x10000+34]=block
    struct.pack_into('<I',data,pool-0x10000,(table-(B+18+4))&0xffffffff)
    old=b'[%s:%d] out:%p out devices:%#x cur_out_devices:%#x format:%s(%#x) digital_mode(%s) sink cap:%s(%#x)'
    assert data[table:table+len(old)]==old
    entries=[b'',b'dtshd;',b'truehd;',b'dtshd;truehd;']
    payload=b''.join(s+b'\0'*(16-len(s)) for s in entries)
    data[table:table+len(payload)]=payload
    out=work/'candidate/audio.primary.amlogic.so';out.write_bytes(data)
    print(hashlib.sha256(data).hexdigest(),out)

if __name__=='__main__':patch(sys.argv[1])
