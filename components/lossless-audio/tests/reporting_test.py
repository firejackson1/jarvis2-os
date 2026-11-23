#!/usr/bin/env python3
"""Execute exact relocated Thumb bytes for every valid capability combination."""
import itertools,struct,sys
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
b=open(sys.argv[1],'rb').read();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
u.mem_map(0,0x300000)
phoff=struct.unpack_from('<I',b,28)[0];ps,pn=struct.unpack_from('<HH',b,42)
for i in range(pn):
 t,off,va,_,fs,ms,flags,align=struct.unpack_from('<8I',b,phoff+i*ps)
 if t==1:u.mem_write(va,b[off:off+fs])
D=0x3000000;C=0x4000000
u.mem_map(D,4096);u.mem_map(C,4096)
u.mem_write(0x12b5e0,bytes.fromhex('1eff2fe1')) # ARM bx lr, emulate libc body below.
seen=[]
def hook(u,addr,size,data):
 if addr==0x12b5e0:
  dest=u.reg_read(UC_ARM_REG_R0);src=u.reg_read(UC_ARM_REG_R1);limit=u.reg_read(UC_ARM_REG_R2)
  prefix=bytes(u.mem_read(dest,256)).split(b'\0')[0]
  suffix=bytes(u.mem_read(src,16)).split(b'\0')[0]
  assert len(prefix)+len(suffix)<limit==255
  u.mem_write(dest,prefix+suffix+b'\0');seen.append(suffix)
u.hook_add(UC_HOOK_CODE,hook)
for d,m,t in itertools.product((0,1),repeat=3):
 for prefix in (b'pcm;',b'pcm;ac3;',b'pcm;ac3;eac3;atmos;'):
  u.mem_write(D,prefix+b'\0'+b'\xa5'*(255-len(prefix)))
  for off,v in ((0x74,d),(0xd4,m),(0xed,t)):u.mem_write(C+off,bytes([v]))
  u.reg_write(UC_ARM_REG_R0,C)
  u.emu_start(0x8ab25,0x8ab2a,count=2)
  assert u.reg_read(UC_ARM_REG_R5)==C+0xc0
  u.reg_write(UC_ARM_REG_R4,D)
  u.emu_start(0x8ab93,0x8a9c0,count=100)
  expected=(b'dtshd;' if d else b'')+(b'truehd;' if m or t else b'')
  assert seen[-1]==expected,(d,m,t,seen[-1],expected)
  assert bytes(u.mem_read(D,256)).split(b'\0')[0]==prefix+expected
  assert bytes(u.mem_read(D+255,1))==b'\xa5'
print('PASS: 24 actual Thumb executions; independent DTS-HD, TrueHD-only and MAT+TrueHD; checked append and buffer guard')
