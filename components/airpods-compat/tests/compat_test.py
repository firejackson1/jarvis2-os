import struct,sys,itertools
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
b=open(sys.argv[1],'rb').read();u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0,0x900000)
phoff=struct.unpack_from('<I',b,28)[0];ps,pn=struct.unpack_from('<HH',b,42)
for i in range(pn):
 t,off,va,_,fs,ms,flags,align=struct.unpack_from('<8I',b,phoff+i*ps)
 if t==1:u.mem_write(va,b[off:off+fs])
C=0xa00000;L=C+0x1000;R=C+0x2000;u.mem_map(C,0x3000)
u.mem_write(C+0x30,struct.pack('<I',L));u.mem_write(C+0x3c,struct.pack('<I',R))
count=0
for feature,mode,psm in itertools.product((0,8),(0,3),(0x1001,0x11,0x13,0x19,0x27,0x1003)):
 u.mem_write(L+0x34,bytes([feature]));u.mem_write(R+0x40,bytes([mode]));u.mem_write(R+4,struct.pack('<H',psm));u.reg_write(UC_ARM_REG_R4,C)
 u.emu_start(0x674919,0x674966,count=100)
 expected=bool(feature or mode!=3 or psm==0x1001)
 assert bool(u.reg_read(UC_ARM_REG_R5))==expected,(feature,mode,psm)
 assert u.mem_read(R+0x40,1)==bytes([0 if not feature and mode==3 else mode])
 count+=1
print('PASS',count,'actual Thumb cases: only AACP PSM0x1001 gains compatibility; HID/AVDTP/other PSM decisions and mode updates unchanged')
