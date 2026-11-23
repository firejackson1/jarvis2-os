#!/usr/bin/env python3
"""Re-sign an offline APEX after changing only bytes in an existing ext4 file.
Uses the ORIGINAL APEX keys, verified against its public key and outer certificate.
No device operations, filesystem layout changes or inode metadata edits.
"""
import hashlib,os,re,shutil,subprocess,sys,zipfile
from pathlib import Path
w,s,original=map(Path,sys.argv[1:4]);tools=s/'out/host/linux-x86/bin';apexkey=s/'packages/modules/Bluetooth/apex'

def run(args):
 try:return subprocess.check_output(list(map(str,args)),stderr=subprocess.STDOUT,text=True)
 except subprocess.CalledProcessError as e:
  print(e.output,flush=True);raise
def sha(b):return hashlib.sha256(b).hexdigest()
payload=w/'candidate-apex_payload.img'
with zipfile.ZipFile(original) as z:
 stock=z.read('apex_payload.img');public=z.read('apex_pubkey');cert=z.read('META-INF/CERT.RSA')
payload.write_bytes(stock)
(w/'outer-cert.rsa').write_bytes(cert)
run(['openssl','pkcs7','-inform','DER','-in',w/'outer-cert.rsa','-print_certs','-out',w/'outer-cert.pem'])
assert run(['openssl','x509','-in',w/'outer-cert.pem','-noout','-fingerprint','-sha256'])==run(['openssl','x509','-in',apexkey/'com.android.btservices.x509.pem','-noout','-fingerprint','-sha256'])
run([tools/'avbtool','extract_public_key','--key',apexkey/'com.android.btservices.pem','--output',w/'apex-test.pub'])
assert (w/'apex-test.pub').read_bytes()==public
old=(w/'stock-libbluetooth_jni.so').read_bytes();new=(w/'candidate-libbluetooth_jni.so').read_bytes()
assert len(old)==len(new)
changed=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
assert changed and min(changed)>=0x67392c and max(changed)<0x673964
# Resolve the file's logical data blocks without assuming contiguous allocation.
raw=bytearray(stock);blocks={}
for offset in changed:
 logical=offset//4096
 if logical not in blocks:
  answer=run(['debugfs','-R','bmap /lib/libbluetooth_jni.so '+str(logical),payload])
  blocks[logical]=int(answer.strip().splitlines()[-1]);assert blocks[logical]>0
 physical=blocks[logical]*4096+offset%4096
 assert raw[physical]==old[offset]
 raw[physical]=new[offset]
payload.write_bytes(raw)
assert len([i for i,(a,b) in enumerate(zip(stock,raw)) if a!=b])==len(changed)
run(['debugfs','-R','dump /lib/libbluetooth_jni.so '+str(w/'apex-verified-lib.so'),payload])
assert (w/'apex-verified-lib.so').read_bytes()==new
(w/'apex-fsck.log').write_text(run(['e2fsck','-f','-n',payload]))
run([tools/'avbtool','add_hashtree_footer','--image',payload,
 '--algorithm','SHA256_RSA4096','--key',apexkey/'com.android.btservices.pem','--hash_algorithm','sha256',
 '--salt','9bce517bfb77944e2e57413a20eecc7054e7ab6d0f6f7598f1856e0d3ffb79be',
 '--do_not_generate_fec','--prop','apex.key:com.android.btservices'])
run([tools/'avbtool','resize_image','--image',payload,'--partition_size',len(stock)])
(w/'apex-avb-verify.log').write_text(run([tools/'avbtool','verify_image','--image',payload,'--key',apexkey/'com.android.btservices.pem']))
unsigned=w/'btservices-unsigned.apex'
with zipfile.ZipFile(original) as z,zipfile.ZipFile(unsigned,'w') as out:
 for info in z.infolist():
  if info.filename.startswith('META-INF/'):continue
  out.writestr(info,payload.read_bytes() if info.filename=='apex_payload.img' else z.read(info.filename))
result=w/'com.android.btservices.apex';jdk=s/'prebuilts/jdk/jdk17/linux-x86/bin'
run([jdk/'java','-Djava.library.path='+str(s/'out/host/linux-x86/lib64'),'-jar',s/'out/host/linux-x86/framework/signapk.jar',
 '-a','4096',apexkey/'com.android.btservices.x509.pem',apexkey/'com.android.btservices.pk8',unsigned,result])
env=dict(os.environ,PATH=str(jdk)+':'+os.environ['PATH'])
verify=subprocess.check_output([str(jdk/'java'),'-jar',str(s/'prebuilts/sdk/tools/linux/lib/apksigner.jar'),'verify','--verbose','--print-certs',str(result)],stderr=subprocess.STDOUT,text=True,env=env)
(w/'apex-apk-verify.log').write_text(verify)
with zipfile.ZipFile(original) as a,zipfile.ZipFile(result) as b:
 for name in a.namelist():
  if name=='apex_payload.img' or name.startswith('META-INF/'):continue
  assert a.read(name)==b.read(name),name
print('APEX verified: native file bytes only; ext4 metadata unchanged; original AVB/outer signing keys, signatures and all other ZIP entries preserved')
print(sha(result.read_bytes()),result)
