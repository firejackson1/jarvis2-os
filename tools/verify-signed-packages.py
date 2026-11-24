#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify the supported Jarvis2 signed-package rehearsal using public materials.

No signing, private-key reads or device operations. A caller-provided inventory
SHA256 pin anchors expected key identities; without one, checks establish only
internal consistency. Final raw-image AVB, hardware trust and OTA completeness
remain separate. Run with external 1GiB RAM / 3GiB swap / one-CPU limits; JVM heap
is limited to 256MiB. Supply matching pinned AOSP host tools and JDK via CLI.
The original ZIP and role-map policy require a caller-trusted baseline; the
public-key inventory pin does not authenticate either artifact or policy.
"""
import argparse,hashlib,importlib.util,io,json,os,re,shutil,stat,struct,subprocess,tempfile,time,traceback,zipfile
from pathlib import Path

_PREPARER_SPEC=importlib.util.spec_from_file_location('jarvis2_signing_metadata',Path(__file__).with_name('prepare-signing-metadata.py'))
_PREPARER=importlib.util.module_from_spec(_PREPARER_SPEC)
_PREPARER_SPEC.loader.exec_module(_PREPARER)

def sha(data):return hashlib.sha256(data).hexdigest()

def file_sha(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):raise ValueError('Expected regular file')
  return hashlib.file_digest(f,'sha256').hexdigest()

def public_file(root,base,suffix):
 if suffix not in ('.public.pem','.x509.pem','.avbpubkey') or not valid_relative(base):
  raise ValueError('Only canonical relative exported public paths/formats are allowed')
 root=Path(root).resolve();path=root/(base+suffix)
 current=root
 for component in (base+suffix).split('/'):
  current=current/component
  if current.is_symlink():raise ValueError('Public material symlinks are unsupported')
 if not path.is_file() or not path.resolve().is_relative_to(root):raise ValueError('Invalid exported public material path')
 return path

def valid_relative(value):
 return isinstance(value,str) and bool(value) and not value.startswith('/') and all(part not in ('','.','..') and re.fullmatch(r'[A-Za-z0-9_.+-]+',part) for part in value.split('/'))

def rows(data,apex=False):
 return _PREPARER.parse_metadata(data,apex=apex)

def load_json_unique(data):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('Duplicate JSON field: '+key)
   result[key]=value
  return result
 return json.loads(data,object_pairs_hook=pairs)

def validate_inventory(data,role_map,trusted_sha256=None):
 digest=hashlib.sha256(data).hexdigest()
 if trusted_sha256 is not None:
  if not re.fullmatch(r'[0-9a-fA-F]{64}',trusted_sha256) or trusted_sha256.lower()!=digest:
   raise ValueError('Trusted public inventory SHA256 pin mismatch or malformed pin')
 def bindings(document,inventory):
  if not isinstance(document,dict) or type(document.get('format')) is not int or document['format']!=1 or not isinstance(document.get('keys'),list) or not document['keys']:
   raise ValueError('Invalid public inventory/role-map schema')
  result={}
  for item in document['keys']:
   if not isinstance(item,dict):raise ValueError('Invalid public key entry')
   allowed={'role','identity','key_base'}|({'public_spki_sha256','certificate_sha256'} if inventory else set())
   if set(item)-allowed or not {'role','identity','key_base'}.issubset(item):raise ValueError('Unexpected public key entry fields')
   role=item['role'];identity=item['identity'];base=item['key_base']
   if not isinstance(role,str) or role not in {'apk','apex-payload','apex-container','image-avb'} or not valid_relative(identity) or not valid_relative(base):raise ValueError('Invalid public key role/identity/path')
   if role.startswith('apex-') and ('/' in identity or not identity.endswith('.apex')):raise ValueError('Invalid APEX role identity')
   if not inventory and role=='image-avb':raise ValueError('Role map contains only package signing roles')
   key=(role,identity)
   if key in result:raise ValueError('Duplicate public key role identity')
   if inventory:
    required={'public_spki_sha256'}|({'certificate_sha256'} if role in ('apk','apex-container') else set())
    if not required.issubset(item):raise ValueError('Missing public fingerprint')
    for field in ('public_spki_sha256','certificate_sha256'):
     if field in item and (not isinstance(item[field],str) or not re.fullmatch(r'[0-9a-fA-F]{64}',item[field])):raise ValueError('Malformed public fingerprint')
   result[key]=item
  return result
 expected=bindings(role_map,False);inventory=load_json_unique(data);actual=bindings(inventory,True)
 if not set(expected).issubset(actual) or any(actual[key]['key_base']!=item['key_base'] for key,item in expected.items()):raise ValueError('Public role mapping differs from inventory')
 extras=set(actual)-set(expected)
 if len(extras)>1 or any(role!='image-avb' for role,_ in extras):raise ValueError('Unexpected unmapped public inventory roles')
 trust={'mode':'caller-pinned-public-inventory' if trusted_sha256 is not None else 'internal-consistency-only','caller_inventory_pin_verified':trusted_sha256 is not None,'inventory_sha256':digest,'hardware_root_of_trust_verified':False}
 return inventory,trust

def is_jar_signature(name):
 # JAR signing metadata is reserved only at the top level of META-INF.
 # LICENSE/NOTICE/services and nested lookalikes remain compared verbatim.
 return re.fullmatch(r'META-INF/(?:MANIFEST\.MF|[A-Z0-9_-]+\.(?:SF|RSA|DSA|EC)|SIG-[A-Z0-9_-]+(?:\.[A-Z0-9]{1,3})?)',name,re.I|re.ASCII) is not None

def apk_content(data):
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  names=z.namelist()
  if len(set(names))!=len(names):raise ValueError('APK duplicate entries')
  return {n:sha(z.read(n)) for n in names if not is_jar_signature(n)}

def embedded_payload_key(path):
 size=path.stat().st_size
 with path.open('rb') as f:
  f.seek(-64,2);footer=struct.unpack('>4sIIQQQ28s',f.read(64))
  if footer[0]!=b'AVBf':raise ValueError('Missing payload AVB footer')
  offset,length=footer[4:6]
  if offset+length>size-64 or length<256:raise ValueError('Payload vbmeta bounds invalid')
  f.seek(offset);header=f.read(256)
  if header[:4]!=b'AVB0':raise ValueError('Missing payload vbmeta header')
  auth,aux=struct.unpack_from('>QQ',header,12);algorithm=struct.unpack_from('>I',header,28)[0]
  key_offset,key_size=struct.unpack_from('>QQ',header,64);flags=struct.unpack_from('>I',header,120)[0]
  if not algorithm or flags or not key_size or key_offset+key_size>aux or 256+auth+aux>length:raise ValueError('Unsigned/disabled/malformed payload vbmeta')
  f.seek(offset+256+auth+key_offset);key=f.read(key_size)
  if len(key)!=key_size:raise ValueError('Truncated embedded payload key')
 return key,algorithm

def require_payload_content_verification(output,path):
 pattern=r'^.*: Successfully verified (?:sha256|sha512) (?:hashtree|hash) of '+re.escape(str(path))+r' for image of [1-9][0-9]* bytes$'
 if not re.search(pattern,output,re.M):raise ValueError('Native AVB output lacks payload content hash/hashtree verification')

def verification_environment(jdk,host,soong_host,tmpdir):
 return dict(os.environ,JAVA_HOME=str(jdk),PATH=str(jdk/'bin')+':'+str(soong_host/'bin')+':'+str(host/'bin')+':'+os.environ['PATH'],TMPDIR=str(tmpdir))

def main():
 os.umask(0o077)
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--signed',type=Path,required=True)
 parser.add_argument('--original',type=Path,required=True)
 parser.add_argument('--public-materials',type=Path,required=True)
 parser.add_argument('--role-map',type=Path,required=True)
 parser.add_argument('--trusted-public-inventory-sha256')
 parser.add_argument('--host',type=Path,required=True)
 parser.add_argument('--soong-host',type=Path,required=True)
 parser.add_argument('--jdk',type=Path,required=True)
 parser.add_argument('--report-dir',type=Path,required=True)
 a=parser.parse_args()
 a.report_dir.mkdir(mode=0o700,exist_ok=False)
 (a.report_dir/'logs').mkdir(mode=0o700)
 (a.report_dir/'tmp').mkdir(mode=0o700)
 env=verification_environment(a.jdk,a.host,a.soong_host,a.report_dir/'tmp')
 report={'status':'running','full_target_files_complete':False,'dropped_stock_reference_images':['vendor.img','odm.img','system_dlkm.img','vendor_dlkm.img','odm_dlkm.img'],'reference_image_requirement':'Preserve and independently verify unchanged original reference inputs; signed package rehearsal is not a complete OTA/full-image artifact.','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'signed_archive':str(a.signed),'original_archive':str(a.original),'public_materials':str(a.public_materials),'android_verification_api':34,'public_keys':[],'standalone_apks':[],'apexes':[],'embedded_apks':[],'preserved':[],'content_comparison_exclusion':'Only top-level JAR MANIFEST.MF, .SF/.RSA/.DSA/.EC, and reserved SIG-* signing artifacts; all other META-INF entries compared.', 'limitations':['Caller must authenticate the original baseline and role-map policy independently; a public-key inventory pin authenticates neither artifact nor policy.','Bounded known-artifact verifier with focused content tests; not a universal untrusted-input schema validation suite.','No blanket file exclusions apply to native APK signature or APEX payload AVB verification. APEX integrity/intended signer verification does not establish equality of every non-APK payload filesystem file or its metadata to the original.','Package/APEX verification only; final raw image AVB chain, hardware trust, installation, restore and OTA trust are NOT established.']}
 def save():
  p=a.report_dir/'report.tmp'
  p.write_text(json.dumps(report,indent=2)+'\n');p.replace(a.report_dir/'report.json')
 def run(args,label=None,input=None):
  r=subprocess.run([str(x) for x in args],input=input,capture_output=True,env=env)
  if label:(a.report_dir/'logs'/label).write_bytes(r.stdout+r.stderr)
  if r.returncode:raise RuntimeError('Verification tool failed: '+str(args[0])+'; log='+str(label)+'; '+r.stderr.decode(errors='replace')[-1000:])
  return r.stdout
 def verify_apk(path,expected,label,original_bytes=None):
  output=run([a.soong_host/'bin/apksigner','-JXmx256M','-JXX:ActiveProcessorCount=1','verify','--verbose','--print-certs','--min-sdk-version','34','--max-sdk-version','34',path],label).decode()
  certs=re.findall(r'^Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-fA-F]+)$',output,re.M)
  if not certs or (expected is not None and certs!=[expected]):raise ValueError('Unexpected signer certificate: '+str(path)+' '+str(certs))
  data=path.read_bytes()
  if original_bytes is not None and apk_content(data)!=apk_content(original_bytes):raise ValueError('Unsigned APK ZIP content changed: '+str(path))
  return {'sha256':sha(data),'signer_certificate_sha256':certs,'signature_verified':True,'nonsignature_entry_content_unchanged':original_bytes is not None}
 def unpack_apex(data,compressed,folder,prefix):
  path=folder/(prefix+('.capex' if compressed else '.apex'));path.write_bytes(data)
  if compressed:
   with zipfile.ZipFile(io.BytesIO(data)) as z:inner=z.read('original_apex')
   inner_path=folder/(prefix+'.apex');inner_path.write_bytes(inner)
  else:inner=data;inner_path=path
  with zipfile.ZipFile(io.BytesIO(inner)) as z:
   manifest=z.read('apex_manifest.pb');pubkey=z.read('apex_pubkey')
  return path,inner_path,inner,manifest,pubkey
 def payload_apks(path,label):
  text=run([a.host/'bin/deapexer','--debugfs_path',a.host/'bin/debugfs_static','--fsckerofs_path',a.host/'bin/fsck.erofs','list',path],label).decode()
  found=[]
  for entry in text.split():
   if not entry.endswith('.apk'):continue
   name=entry.removeprefix('./')
   if name.startswith('/') or '..' in name.split('/') or name in found:raise ValueError('Unsafe/duplicate payload APK path')
   found.append(name)
  return sorted(found)
 def extract(path,dest,label):
  run([a.host/'bin/deapexer','--debugfs_path',a.host/'bin/debugfs_static','--fsckerofs_path',a.host/'bin/fsck.erofs','extract',path,dest],label)
 try:
  save()
  role_map=load_json_unique(a.role_map.read_bytes())
  inventory_path=a.public_materials/'inventory.json'
  if inventory_path.is_symlink() or not inventory_path.is_file():raise ValueError('Public inventory must be a regular file')
  inventory,trust=validate_inventory(inventory_path.read_bytes(),role_map,a.trusted_public_inventory_sha256)
  report['public_inventory_trust']=trust
  roles={(item['role'],item['identity']):item['key_base'] for item in role_map['keys']}
  if len(roles)!=77:raise ValueError('Supported Jarvis2 layout requires 77 package signing roles')
  keys={}
  for item in inventory['keys']:
   identity=(item['role'],item['identity'])
   if identity in keys:raise ValueError('Duplicate public inventory identity')
   base=item['key_base'];pem=public_file(a.public_materials,base,'.public.pem')
   spki=sha(run(['openssl','pkey','-pubin','-in',pem,'-outform','DER']))
   if spki!=item['public_spki_sha256'].lower():raise ValueError('Exported SPKI inventory mismatch')
   if 'certificate_sha256' in item:
    cert=public_file(a.public_materials,base,'.x509.pem');der=run(['openssl','x509','-in',cert,'-outform','DER'])
    pub=run(['openssl','x509','-in',cert,'-pubkey','-noout'])
    certspki=sha(run(['openssl','pkey','-pubin','-outform','DER'],input=pub))
    if sha(der)!=item['certificate_sha256'].lower() or certspki!=spki:raise ValueError('Exported certificate/SPKI mismatch')
   if item['role'] in ('apex-payload','image-avb'):
    expected=public_file(a.public_materials,base,'.avbpubkey')
    derived=run([a.host/'bin/avbtool','extract_public_key','--key',pem,'--output','/dev/stdout'])
    if derived!=expected.read_bytes():raise ValueError('Exported AVB public key differs from SPKI')
   keys[identity]=item;report['public_keys'].append({'role':item['role'],'identity':item['identity'],'public_spki_sha256':spki,'verified':True})
  if len(keys) not in (77,78):raise ValueError('Unexpected public key inventory count')
  report['archive_sha256']={'original':file_sha(a.original),'signed':file_sha(a.signed)}
  with zipfile.ZipFile(a.original) as original,zipfile.ZipFile(a.signed) as signed:
   _PREPARER.validate_archive(original);_PREPARER.validate_archive(signed)
   old_names,new_names=set(original.namelist()),set(signed.namelist())
   allowed_removed={'IMAGES/','IMAGES/vendor.img','IMAGES/odm.img','IMAGES/system_dlkm.img','IMAGES/vendor_dlkm.img','IMAGES/odm_dlkm.img'}
   removed,added=old_names-new_names,new_names-old_names
   report['archive_entry_differential']={'removed':sorted(removed),'added':sorted(added),'allowed_removed':sorted(allowed_removed),'explanation':'Pinned signer skips all IMAGES/ and these 5 prebuilt-only foundation partitions lack trees/build flags for regeneration; package audit only, target-files completeness NOT established.'}
   if len(new_names)!=len(signed.namelist()) or added or removed!=allowed_removed:raise ValueError('Unexpected signed archive entry differential')
   package=lambda n:n.endswith(('.apk','.apk.gz','.apex','.capex'))
   if {n for n in old_names if package(n)}!={n for n in new_names if package(n)}:raise ValueError('Package identities changed')
   apk_rows=rows(original.read('META/apkcerts.txt'));apex_rows=rows(original.read('META/apexkeys.txt'),apex=True)
   def expected_apk(partition,name):
    row=apk_rows[(partition,name)]
    if row['certificate']=='PRESIGNED':return None
    source=row['certificate'].removesuffix('.x509.pem');item=keys[('apk',source)]
    mapped=roles[('apk',source)]
    if mapped!=item['key_base']:raise ValueError('APK plan/public mapping differs')
    return item['certificate_sha256'].lower()
   for name in signed.namelist():
    if not name.endswith('.apk'):continue
    partition=name.split('/')[0].lower();basename=Path(name).name;expected=expected_apk(partition,basename)
    with tempfile.TemporaryDirectory(dir=a.report_dir/'tmp') as temp:
     path=Path(temp)/basename;data=signed.read(name);path.write_bytes(data);old=original.read(name)
     result=verify_apk(path,expected,'apk-'+basename+'.txt',old)
     if expected is None:
      if data!=old:raise ValueError('PRESIGNED standalone changed')
      report['preserved'].append({'path':name,'sha256':sha(data),'byte_identical':True})
     result.update(path=name,expected_certificate_sha256=expected);report['standalone_apks'].append(result);save()
    print('Verified standalone '+name,flush=True)
   for name in signed.namelist():
    if not name.endswith(('.apex','.capex')):continue
    partition=name.split('/')[0].lower();identity=Path(name).name.replace('.capex','.apex');presigned=apex_rows[(partition,identity)]['container_certificate']=='PRESIGNED'
    result={'path':name,'identity':identity,'presigned':presigned}
    with tempfile.TemporaryDirectory(dir=a.report_dir/'tmp') as temp:
     folder=Path(temp);data=signed.read(name);old=original.read(name)
     outer,inner,inner_data,manifest,pubkey=unpack_apex(data,name.endswith('.capex'),folder,'signed')
     _,old_inner,_,old_manifest,_=unpack_apex(old,name.endswith('.capex'),folder,'original')
     if manifest!=old_manifest:raise ValueError('APEX manifest changed')
     if presigned:
      if data!=old:raise ValueError('PRESIGNED APEX changed')
      expected=None;report['preserved'].append({'path':name,'sha256':sha(data),'byte_identical':True})
     else:
      item=keys[('apex-container',identity)];payload=keys[('apex-payload',identity)];expected=item['certificate_sha256'].lower()
      if roles[('apex-container',identity)]!=item['key_base']:raise ValueError('APEX container plan/public mapping differs')
      if roles[('apex-payload',identity)]!=payload['key_base']:raise ValueError('APEX payload plan/public mapping differs')
     result['outer_container']=verify_apk(outer,expected,'apex-'+identity+'-outer.txt')
     if outer!=inner:result['inner_container']=verify_apk(inner,expected,'apex-'+identity+'-inner.txt')
     if not presigned:
      with zipfile.ZipFile(io.BytesIO(inner_data)) as z:
       payload_path=folder/'apex_payload.img'
       with z.open('apex_payload.img') as reader,payload_path.open('wb') as writer:shutil.copyfileobj(reader,writer,1048576)
      embedded,algorithm=embedded_payload_key(payload_path);intended=public_file(a.public_materials,payload['key_base'],'.avbpubkey').read_bytes()
      if embedded!=intended or pubkey!=intended:raise ValueError('APEX payload embedded/ZIP/intended public keys differ')
      payload_output=run([a.host/'bin/avbtool','verify_image','--image',payload_path,'--key',public_file(a.public_materials,payload['key_base'],'.public.pem')],'apex-'+identity+'-payload.txt').decode()
      require_payload_content_verification(payload_output,payload_path)
      result.update(payload_signature_and_hashtree_verified=True,payload_embedded_key_sha256=sha(embedded),payload_algorithm=algorithm,zip_pubkey_matches_intended=True)
     paths=payload_apks(inner,'apex-'+identity+'-list.txt');old_paths=payload_apks(old_inner,'apex-'+identity+'-original-list.txt')
     if paths!=old_paths:raise ValueError('Embedded APK paths changed')
     if paths:
      new_dir=folder/'new';old_dir=folder/'old';extract(inner,new_dir,'apex-'+identity+'-extract.txt');extract(old_inner,old_dir,'apex-'+identity+'-original-extract.txt')
      for path in paths:
       current=new_dir/path;previous=old_dir/path
       if current.is_symlink() or previous.is_symlink() or not current.resolve().is_relative_to(new_dir.resolve()):raise ValueError('Unsafe embedded APK')
       old_apk=previous.read_bytes();expected=None if presigned else expected_apk(partition,Path(path).name)
       verified=verify_apk(current,expected,'embedded-'+Path(path).name+'.txt',old_apk)
       if presigned and current.read_bytes()!=old_apk:raise ValueError('PRESIGNED shim embedded APK changed')
       verified.update(path=name+'!/'+path,expected_certificate_sha256=expected,preserved_in_shim=presigned);report['embedded_apks'].append(verified)
     result['embedded_apk_count']=len(paths);report['apexes'].append(result);save()
    print('Verified APEX '+identity,flush=True)
  counts={'public_keys':len(report['public_keys']),'standalone_apks':len(report['standalone_apks']),'standalone_resigned':sum(r['expected_certificate_sha256'] is not None for r in report['standalone_apks']),'apexes':len(report['apexes']),'apex_payloads_verified':sum(r.get('payload_signature_and_hashtree_verified',False) for r in report['apexes']),'embedded_apks':len(report['embedded_apks']),'embedded_resigned':sum(not r['preserved_in_shim'] for r in report['embedded_apks']),'embedded_shim_preserved':sum(r['preserved_in_shim'] for r in report['embedded_apks'])}
  if counts!={'public_keys':len(inventory['keys']),'standalone_apks':104,'standalone_resigned':103,'apexes':31,'apex_payloads_verified':30,'embedded_apks':23,'embedded_resigned':21,'embedded_shim_preserved':2}:raise ValueError('Package inventory count mismatch: '+str(counts))
  report.update(status='passed',counts=counts,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));save();print(json.dumps(counts),flush=True)
 except BaseException as error:
  report.update(status='failed',error=str(error),traceback=traceback.format_exc());save();raise

if __name__=="__main__":main()
