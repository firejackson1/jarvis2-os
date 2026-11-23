import hashlib,struct,sys
from pathlib import Path
w=Path(sys.argv[1]);b=bytearray((w/'stock-libbluetooth_jni.so').read_bytes())
assert hashlib.sha256(b).hexdigest()=='e4237df87e1ce303874cae04aef181d3dc09b6319a39199b92f70b4f736d6578'
# Confirm outer checks and exact failure-path endpoints. ARM32 CCB p_rcb+0x3c,
# RCB real_psm+4 and ertm_info.preferred_mode+0x40 match this binary and source.
assert b[0x673918:0x67392c]==bytes.fromhex('206b90f83400000720d4e06b90f8400003281bd1')
assert b[0x67395c:0x673966]==bytes.fromhex('e06b80f8405000e00125')
o=(w/'compat.o').read_bytes();off=struct.unpack_from('<I',o,32)[0];z,n,ni=struct.unpack_from('<HHH',o,46);h=[struct.unpack_from('<10I',o,off+i*z) for i in range(n)];s=h[ni];ns=o[s[4]:s[4]+s[5]];s=next(s for s in h if ns[s[0]:].split(b'\0')[0]==b'.text');code=bytearray(o[s[4]:s[4]+s[5]])
assert len(code)==24
start=0x67492c;end=0x674964
branch=(0x674966-(start+len(code)-2+4))//2
code[-2:]=struct.pack('<H',0xe000|(branch&0x7ff))
b[start-0x1000:end-0x1000]=code+bytes.fromhex('00bf')*((end-start-len(code))//2)
(w/'candidate-libbluetooth_jni.so').write_bytes(b)
print(hashlib.sha256(b).hexdigest())
