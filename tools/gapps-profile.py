#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export/validate Google-free composition metadata and compare EROFS metadata.

No signing, keys, image rebuilding, updater execution, device queries or writes.
The recipe contains only paths/hashes/metadata, never Google payload bytes.
EROFS metadata is read directly from the pinned on-disk format (erofs_fs.h,
GPL-2.0-only OR Apache-2.0); native fsck is an additional CLI integrity gate.
Supported: single-device 4KiB EROFS, incompat bits 0x3, compact/extended inodes,
short inline/shared xattrs and flat directory/symlink data. Other layouts fail.
Regular compressed file contents, timestamps, inode placement and hardware AVB
trust are outside this incremental tool. Caller must authenticate base inputs.
Run native jobs with external 1GiB RAM/3GiB swap/one-CPU limits.
"""
import argparse,hashlib,json,os,re,shutil,stat,struct,subprocess,tempfile,uuid,zipfile
from pathlib import Path
from urllib.parse import urlsplit

PARTS=('system','system_ext','product')
LABEL='u:object_r:system_file:s0'
PREFIXES={1:'user.',2:'system.posix_acl_access',3:'system.posix_acl_default',4:'trusted.',5:'lustre.',6:'security.'}


def digest(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):raise ValueError('Expected regular input file')
  return hashlib.file_digest(f,'sha256').hexdigest()


def json_unique(data):
 def pairs(items):
  out={}
  for key,value in items:
   if key in out:raise ValueError('Duplicate JSON key')
   out[key]=value
  return out
 return json.loads(data,object_pairs_hook=pairs)


def safe_path(value,root=False):
 if root and value=='':return value
 if not isinstance(value,str) or not value or value.startswith('/') or '\\' in value or any(x in ('','.','..') for x in value.split('/')) or any(ord(c)<32 for c in value):raise ValueError('Noncanonical relative path')
 return value


def checked_file(root,name):
 safe_path(name);current=Path(root)
 for component in name.split('/'):
  current=current/component
  if current.is_symlink():raise ValueError('Metadata symlinks are unsupported')
 if not current.is_file():raise ValueError('Missing metadata file')
 return current


def sha256_value(value):
 if not isinstance(value,str) or not re.fullmatch(r'[0-9a-f]{64}',value):raise ValueError('Invalid SHA256')
 return value


def capability_mask(value):
 if not value:return 0
 if len(value)!=20:raise ValueError('Unsupported capability xattr length')
 magic,low,inherit_low,high,inherit_high=struct.unpack('<IIIII',value)
 if magic!=0x02000001 or inherit_low or inherit_high:raise ValueError('Capability xattr cannot be represented by canned fs_config')
 return low|(high<<32)


class ErofsMetadata:
 """Bounded metadata-only reader; never decompresses regular file payloads."""
 def __init__(self,path,max_entries=100000):
  fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);self.file=os.fdopen(fd,'rb');self.cache={};self.max_entries=max_entries
  try:
   if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('EROFS input must be a regular file')
   self.limit=os.fstat(fd).st_size;sb=self.read(1024,128)
   if struct.unpack_from('<I',sb)[0]!=0xe0f5e1e2 or sb[12]!=12 or sb[13] or struct.unpack_from('<I',sb,80)[0]&~3 or struct.unpack_from('<H',sb,86)[0] or sb[90] or sb[91]:raise ValueError('Unsupported EROFS superblock/features')
   self.block_size=4096;self.root_nid=struct.unpack_from('<H',sb,14)[0]
   self.blocks,self.meta_block,self.xattr_block=struct.unpack_from('<III',sb,36)
   if not self.blocks or self.blocks*self.block_size>self.limit:raise ValueError('Truncated EROFS filesystem')
   self.limit=self.blocks*self.block_size
   self.geometry={'block_size':4096,'filesystem_bytes':self.limit,'uuid':str(uuid.UUID(bytes=sb[48:64])),'build_epoch':struct.unpack_from('<Q',sb,24)[0],'build_nsec':struct.unpack_from('<I',sb,32)[0],'incompat_features':struct.unpack_from('<I',sb,80)[0]}
  except BaseException:self.file.close();raise
 def __enter__(self):return self
 def __exit__(self,*args):self.file.close()
 def read(self,offset,size):
  if type(offset) is not int or type(size) is not int or offset<0 or size<0 or offset+size>self.limit or size>64*1024*1024:raise ValueError('EROFS metadata bounds exceeded')
  self.file.seek(offset);data=self.file.read(size)
  if len(data)!=size:raise ValueError('Truncated EROFS metadata')
  return data
 def xattr_entry(self,offset,end):
  if offset+4>end:raise ValueError('Truncated xattr header')
  length,index,size=struct.unpack('<BBH',self.read(offset,4));total=(4+length+size+3)&~3
  if index not in PREFIXES or offset+total>end:raise ValueError('Unsupported or truncated xattr')
  name=self.read(offset+4,length)
  try:name=name.decode('ascii')
  except UnicodeDecodeError:raise ValueError('Invalid xattr name')
  if '\0' in name or '/' in name or (index in (2,3) and name):raise ValueError('Invalid xattr name')
  return PREFIXES[index]+name,self.read(offset+4+length,size),total
 def inode(self,nid):
  if nid in self.cache:return self.cache[nid]
  if len(self.cache)>=self.max_entries:raise ValueError('EROFS inode limit exceeded')
  offset=self.meta_block*4096+nid*32;head=self.read(offset,32);fmt,count,mode=struct.unpack_from('<HHH',head)
  if fmt&~15 or (fmt>>1)>3:raise ValueError('Unsupported inode layout')
  extended=fmt&1;header_size=64 if extended else 32
  if extended:
   head=self.read(offset,64);size=struct.unpack_from('<Q',head,8)[0];uid,gid=struct.unpack_from('<II',head,24)
  else:size=struct.unpack_from('<I',head,8)[0];uid,gid=struct.unpack_from('<HH',head,24)
  kind={stat.S_IFDIR:'directory',stat.S_IFREG:'file',stat.S_IFLNK:'symlink'}.get(stat.S_IFMT(mode))
  if kind is None:raise ValueError('Unsupported EROFS inode type')
  xsize=0 if not count else 12+4*(count-1);attributes={}
  if xsize:
   if xsize<=12:raise ValueError('Unsupported empty xattr body')
   body=self.read(offset+header_size,xsize);shared=body[4]
   if 12+shared*4>xsize:raise ValueError('Invalid shared xattr count')
   for i in range(shared):
    target=self.xattr_block*4096+struct.unpack_from('<I',body,12+i*4)[0]*4
    name,value,_=self.xattr_entry(target,self.limit)
    if name in attributes:raise ValueError('Duplicate xattr')
    attributes[name]=value.hex()
   cursor=offset+header_size+12+shared*4;end=offset+header_size+xsize
   while cursor<end:
    name,value,length=self.xattr_entry(cursor,end)
    if name in attributes:raise ValueError('Duplicate xattr')
    attributes[name]=value.hex();cursor+=length
  raw=bytes.fromhex(attributes.get('security.selinux',''))
  try:label=raw.rstrip(b'\0').decode('ascii') if raw else None
  except UnicodeDecodeError:raise ValueError('Invalid SELinux label')
  if label and (not re.fullmatch(r'[A-Za-z0-9_:.,-]+',label) or b'\0' in raw.rstrip(b'\0')):raise ValueError('Malformed SELinux label')
  value={'nid':nid,'offset':offset,'header_size':header_size,'xattr_size':xsize,'layout':fmt>>1,'raw_block':struct.unpack_from('<I',head,16)[0],
         'metadata':{'type':kind,'mode':stat.S_IMODE(mode),'uid':uid,'gid':gid,'size':size,'xattrs':attributes,'selinux_label':label,'capabilities':capability_mask(bytes.fromhex(attributes.get('security.capability','')))}}
  self.cache[nid]=value;return value
 def flat_data(self,inode):
  size=inode['metadata']['size'];layout=inode['layout']
  if layout not in (0,2) or size>64*1024*1024:raise ValueError('Unsupported/oversized directory or symlink layout')
  bulk=size if layout==0 or not size else ((size-1)//4096)*4096
  data=self.read(inode['raw_block']*4096,bulk) if bulk else b''
  if bulk<size:
   at=inode['offset']+inode['header_size']+inode['xattr_size'];tail=size-bulk
   if at%4096+tail>4096:raise ValueError('Inline directory data crosses block boundary')
   data+=self.read(at,tail)
  return data
 def directory(self,inode):
  data=self.flat_data(inode);out=[]
  for offset in range(0,len(data),4096):
   block=data[offset:offset+4096]
   if len(block)<12:raise ValueError('Truncated directory block')
   first=struct.unpack_from('<H',block,8)[0]
   if first<12 or first%12 or first>len(block):raise ValueError('Invalid directory name table')
   count=first//12
   for i in range(count):
    nid,start,hint,reserved=struct.unpack_from('<QHBB',block,i*12)
    end=struct.unpack_from('<H',block,(i+1)*12+8)[0] if i+1<count else len(block)
    if reserved or not first<=start<end<=len(block):raise ValueError('Invalid directory name offsets')
    raw=block[start:end];name_raw,_,padding=raw.partition(b'\0')
    if padding.strip(b'\0'):raise ValueError('Invalid directory padding')
    try:name=name_raw.decode('utf-8')
    except UnicodeDecodeError:raise ValueError('Non-UTF8 directory name')
    if name in ('.','..'):continue
    if '/' in name or not name or len(name_raw)>255:raise ValueError('Invalid directory filename')
    safe_path(name);out.append((name,nid,hint))
  return out
 def snapshot(self):
  result={};pending=[('',self.root_nid,2)];directories=set()
  while pending:
   path,nid,hint=pending.pop()
   if path in result or len(result)>=self.max_entries:raise ValueError('Duplicate path or metadata entry limit')
   inode=self.inode(nid);entry=dict(inode['metadata']);entry['xattrs']=dict(entry['xattrs'])
   if {1:'file',2:'directory',7:'symlink'}.get(hint)!=entry['type']:raise ValueError('Directory/inode type mismatch')
   if entry['type']=='directory':
    if nid in directories:raise ValueError('Directory inode cycle/alias')
    directories.add(nid)
    for name,child,kind in self.directory(inode):pending.append(((path+'/' if path else '')+name,child,kind))
    entry.pop('size')
   elif entry['type']=='symlink':entry['target']=self.flat_data(inode).decode('utf-8')
   result[path]=entry
  return dict(sorted(result.items()))


def compare_metadata(before,after,allowed_additions=None):
 allowed_additions=allowed_additions or {};changed=[];unexpected=[]
 for path in sorted(set(before)&set(after)):
  fields=[key for key in set(before[path])|set(after[path]) if before[path].get(key)!=after[path].get(key)]
  if fields:changed.append({'path':path,'fields':sorted(fields)})
 added=sorted(set(after)-set(before))
 for path in added:
  expected=allowed_additions.get(path)
  if expected is None or any(after[path].get(key)!=value for key,value in expected.items()):unexpected.append(path)
 removed=sorted(set(before)-set(after))
 return {'passed':not changed and not unexpected and not removed,'changed_existing':changed,'removed':removed,'added':added,'unexpected_added':unexpected,'regular_file_contents_verified':False}


def parse_fs_config(data):
 result={}
 for raw in data.decode('utf-8').splitlines():
  if not raw or raw.startswith('#'):continue
  line=('/'+raw if raw.startswith(' ') else raw).split()
  if len(line)<4:raise ValueError('Malformed fs_config row')
  path=line[0].removeprefix('/') if line[0]=='/' else line[0];safe_path(path,root=True)
  if path in result or not all(re.fullmatch(r'[0-9]+',x) for x in line[1:3]) or not re.fullmatch(r'[0-7]{1,4}',line[3]):raise ValueError('Duplicate or malformed fs_config row')
  fields={}
  for token in line[4:]:
   key,separator,value=token.partition('=')
   if not separator or key not in ('selabel','capabilities') or key in fields:raise ValueError('Invalid fs_config metadata')
   fields[key]=value
  caps=fields.get('capabilities','0')
  if not re.fullmatch(r'(?:0x[0-9a-fA-F]+|0|[1-9][0-9]*)',caps):raise ValueError('Invalid capability mask')
  caps=int(caps,0)
  if caps>=2**64 or any(int(x)>=2**32 for x in line[1:3]):raise ValueError('UID/GID or capability mask overflow')
  result[path]={'uid':int(line[1]),'gid':int(line[2]),'mode':int(line[3],8),'capabilities':caps}
 return result


def canned_config(snapshot,part):
 lines=[]
 for path,item in sorted(snapshot.items()):
  name=(part+'/' if part!='system' else '')+path if path else '/'
  lines.append(f'{name} {item["uid"]} {item["gid"]} {item["mode"]:o} capabilities=0x{item["capabilities"]:x}\n')
 return ''.join(lines).encode()


def validate_zip(z):
 names=set()
 for info in z.infolist():
  safe_path(info.filename.rstrip('/'))
  if info.filename in names or info.flag_bits&1:raise ValueError('Duplicate/encrypted ZIP entry')
  names.add(info.filename)
  if stat.S_IFMT(info.external_attr>>16) not in (0,stat.S_IFREG,stat.S_IFDIR):raise ValueError('Nonregular ZIP input entries are unsupported')


def validate_provenance(item):
 name=item.get('filename');safe_path(name)
 if '/' in name or not name.endswith('.zip') or type(item.get('bytes')) is not int or not 0<item['bytes']<=1024**3:raise ValueError('Invalid public ZIP provenance')
 url=item.get('url')
 if not isinstance(url,str):raise ValueError('Missing public upstream URL')
 parsed=urlsplit(url)
 if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Upstream URL must be public HTTPS without credentials/query')
 sha256_value(item['sha256'])

def export_recipe(archive,pin):
 validate_provenance(pin)
 if type(pin.get('format')) is not int or pin['format']!=1:raise ValueError('Unsupported GApps input manifest')
 if pin.get('architecture')!='arm' or pin.get('android_api')!=34 or pin.get('variant')!='ATV-minimal' or archive.stat().st_size!=pin['bytes'] or digest(archive)!=sha256_value(pin['sha256']):raise ValueError('Wrong GApps input identity')
 entries=[]
 with zipfile.ZipFile(archive) as z:
  validate_zip(z)
  if z.read('build.prop')!=b'arch=arm\nversion=34\nversion_nice=14.0.0\n':raise ValueError('Wrong GApps package metadata')
  for info in z.infolist():
   path=info.filename
   if info.is_dir() or not path.startswith('system/') or path.startswith('system/addon.d/'):continue
   pieces=path.split('/')
   if info.file_size>512*1024*1024:raise ValueError('Oversized Google payload entry')
   if len(pieces)<3 or pieces[1] not in PARTS:raise ValueError('Unsupported Google payload path')
   part=pieces[1];relative='/'.join(pieces[2:]);safe_path(relative)
   if part=='system':relative='system/'+relative
   with z.open(info) as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
   entries.append({'zip_path':path,'partition':part,'image_path':relative,'bytes':info.file_size,'sha256':sha,'uid':0,'gid':0,'mode':0o644,'capabilities':0,'selinux_label':LABEL})
 result={'format':1,'kind':'local-gapps-composition-recipe','android_api':34,'architecture':'arm','variant':'ATV-minimal','source_revision':pin.get('source_revision'),'input':{key:pin[key] for key in ('filename','bytes','sha256','url')},'entries':sorted(entries,key=lambda x:x['zip_path']),'directory_metadata':{'uid':0,'gid':0,'mode':0o755,'capabilities':0,'selinux_label':LABEL},'google_payload_bytes_included':False,'ordinary_erofs_sideload_supported':False,'google_signatures_verified_by_this_export':False,'redistribution_permission_inferred':False}
 validate_recipe(result);return result


def validate_recipe(recipe):
 if not isinstance(recipe,dict) or set(recipe)!={'format','kind','android_api','architecture','variant','source_revision','input','entries','directory_metadata','google_payload_bytes_included','ordinary_erofs_sideload_supported','google_signatures_verified_by_this_export','redistribution_permission_inferred'}:raise ValueError('Unexpected recipe fields')
 if recipe['kind']!='local-gapps-composition-recipe' or recipe['variant']!='ATV-minimal' or any(recipe[key] is not False for key in ['google_payload_bytes_included','ordinary_erofs_sideload_supported','google_signatures_verified_by_this_export','redistribution_permission_inferred']):raise ValueError('Invalid recipe scope flags')
 if not isinstance(recipe['input'],dict) or set(recipe['input'])!={'filename','bytes','sha256','url'}:raise ValueError('Invalid ZIP provenance fields')
 validate_provenance(recipe['input'])
 if recipe['source_revision'] is not None and not re.fullmatch(r'[0-9a-f]{40}',recipe['source_revision']):raise ValueError('Invalid upstream source revision')
 if recipe['directory_metadata']!={'uid':0,'gid':0,'mode':0o755,'capabilities':0,'selinux_label':LABEL} or any(type(recipe['directory_metadata'].get(key)) is not int for key in ('uid','gid','mode','capabilities')):raise ValueError('Invalid directory metadata')
 if not isinstance(recipe,dict) or type(recipe.get('format')) is not int or recipe['format']!=1 or recipe.get('android_api')!=34 or recipe.get('architecture')!='arm' or not isinstance(recipe.get('entries'),list) or len(recipe['entries'])!=27:raise ValueError('Unsupported recipe schema or entry count')
 sha256_value(recipe['input']['sha256']);seen=set();destinations=set()
 for entry in recipe['entries']:
  if not isinstance(entry,dict) or set(entry)!={'zip_path','partition','image_path','bytes','sha256','uid','gid','mode','capabilities','selinux_label'}:raise ValueError('Unexpected Google file fields')
  safe_path(entry['zip_path']);safe_path(entry['image_path']);part=entry['partition']
  if part not in PARTS or entry['zip_path'] in seen or (part,entry['image_path']) in destinations:raise ValueError('Invalid/duplicate recipe destination')
  expected='system/'+part+'/'+(entry['image_path'].removeprefix('system/') if part=='system' else entry['image_path'])
  if entry['zip_path']!=expected or (part=='system' and not entry['image_path'].startswith('system/')):raise ValueError('Recipe path mapping mismatch')
  sha256_value(entry['sha256'])
  if type(entry['bytes']) is not int or entry['bytes']<=0 or any(type(entry.get(key)) is not int for key in ('uid','gid','mode','capabilities')) or (entry['uid'],entry['gid'],entry['mode'],entry['capabilities'],entry['selinux_label'])!=(0,0,0o644,0,LABEL):raise ValueError('Unexpected Google file metadata')
  seen.add(entry['zip_path']);destinations.add((part,entry['image_path']))
 return True


def export_profile(target_files,output,limits,fsck=None,base_images=None,source_revision=None):
 if set(limits)!=set(PARTS) or any(type(x) is not int or not 0<x<=3355443200 for x in limits.values()):raise ValueError('Provide exact positive partition byte budgets')
 if source_revision is not None and not re.fullmatch(r'[0-9a-f]{7,64}',source_revision):raise ValueError('Source revision must be a commit ID, not a path')
 target_files=Path(target_files);output=Path(output)
 if target_files.is_symlink():raise ValueError('Target-files must not be a symlink')
 output.mkdir(mode=0o700);(output/'metadata').mkdir();(output/'logs').mkdir()
 profile={'format':1,'kind':'gapps-composition-profile','android_api':34,'architecture':'arm','source':{'target_files_sha256':digest(target_files),'source_revision':source_revision,'base_images_supplied_separately':base_images is not None},'metadata_method':{'reader_source_sha256':digest(Path(__file__)),'native_fsck_sha256':digest(Path(shutil.which(str(fsck)) or fsck).resolve()) if fsck else None,'regular_file_contents_verified':False},'owner_device_capture_used':False,'composition_ready':False,'image_avb_assembled':False,'hardware_trust_verified':False,'google_payload_included':False,'partitions':{},'limitations':['Caller must authenticate target-files, base images and this profile independently.','Metadata-only increment: no Google copy, image rebuild, AVB assembly or regular-file content equality is established.','Rebuilding must preserve all recorded raw xattrs; canned fs_config applies UID/GID/mode/caps, not SELinux labels.']}
 with zipfile.ZipFile(target_files) as z:
  # Target-files can contain ordinary filesystem symlinks; critical members below cannot.
  if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate target-files ZIP members')
  def member(name,maximum):
   info=z.getinfo(name)
   if info.file_size>maximum or info.flag_bits&1 or stat.S_IFMT(info.external_attr>>16) not in (0,stat.S_IFREG):raise ValueError('Invalid release metadata member')
   return z.read(info)
  misc={}
  for line in member('META/misc_info.txt',1048576).decode().splitlines():
   if not line.strip() or line.startswith('#'):continue
   key,separator,value=line.partition('=')
   if not separator or key in misc or not re.fullmatch(r'[a-zA-Z0-9_]+',key):raise ValueError('Malformed misc metadata')
   misc[key]=value
  compressor=misc.get('erofs_default_compressor','lz4hc,12');cluster=misc.get('erofs_pcluster_size','65536')
  if not re.fullmatch(r'lz4hc,[0-9]+|lz4|none',compressor) or not re.fullmatch(r'[0-9]+',cluster):raise ValueError('Unsupported EROFS build settings')
  if not 4096<=int(cluster)<=1048576 or int(cluster)&(int(cluster)-1):raise ValueError('Unsupported physical cluster size')
  profile['build_settings']={'compressor':compressor,'pcluster_size':int(cluster),'settings_source':'META/misc_info.txt (filtered; key paths excluded)'}
  contexts=member('META/file_contexts.bin',16*1024*1024)
  if not contexts:raise ValueError('Missing compiled file contexts')
  (output/'metadata/file_contexts.bin').write_bytes(contexts)
  profile['file_contexts']={'file':'metadata/file_contexts.bin','sha256':hashlib.sha256(contexts).hexdigest(),'source_member':'META/file_contexts.bin'}
  for part in PARTS:
   if misc.get(part+'_fs_type')!='erofs':raise ValueError('Profile requires three EROFS partitions')
   name='filesystem_config.txt' if part=='system' else part+'_filesystem_config.txt'
   source_config=member('META/'+name,16*1024*1024);parse_fs_config(source_config)
   source_path='metadata/'+part+'.source_fs_config.txt';(output/source_path).write_bytes(source_config)
   with tempfile.TemporaryDirectory(prefix='image-',dir=output) as temporary:
    if base_images is None:
     info=z.getinfo('IMAGES/'+part+'.img')
     if info.file_size>limits[part] or info.flag_bits&1 or stat.S_IFMT(info.external_attr>>16) not in (0,stat.S_IFREG):raise ValueError('Invalid/oversized base image')
     image=Path(temporary)/(part+'.img')
     with z.open(info) as reader,image.open('wb') as writer:shutil.copyfileobj(reader,writer,1048576)
    else:image=checked_file(base_images,part+'.img')
    if image.stat().st_size>limits[part]:raise ValueError('Base image exceeds partition budget')
    if fsck:
     with (output/'logs'/(part+'-fsck.log')).open('wb') as log:subprocess.run([str(fsck),str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
    with ErofsMetadata(image) as reader:snapshot=reader.snapshot();geometry=reader.geometry
    validate_snapshot(snapshot)
    if any(not item['selinux_label'] for item in snapshot.values()):raise ValueError('Every base path needs an authoritative SELinux label')
    if any(Path(path).name in ('adb_keys','default_adb_keys','adbkey','adbkey.pub') for path in snapshot):raise ValueError('Refuse pre-authorized debug trust baseline')
    metadata_file='metadata/'+part+'.metadata.json';(output/metadata_file).write_text(json.dumps(snapshot,indent=2)+'\n')
    config_file='metadata/'+part+'.fs_config';(output/config_file).write_bytes(canned_config(snapshot,part))
    profile['partitions'][part]={'image_sha256':digest(image),'image_bytes':image.stat().st_size,'partition_bytes':limits[part],'mount_point':'/' if part=='system' else part,'erofs':geometry,'metadata':{'file':metadata_file,'sha256':digest(output/metadata_file)},'fs_config':{'file':config_file,'sha256':digest(output/config_file)},'source_fs_config':{'file':source_path,'sha256':digest(output/source_path),'source_member':'META/'+name},'native_fsck_verified':bool(fsck),'metadata_entries':len(snapshot)}
 (output/'profile.json').write_text(json.dumps(profile,indent=2)+'\n');validate_profile(output)
 return profile


def validate_snapshot(snapshot):
 if not isinstance(snapshot,dict) or '' not in snapshot or len(snapshot)>100000:raise ValueError('Invalid metadata snapshot')
 for path,item in snapshot.items():
  safe_path(path,root=True)
  if not isinstance(item,dict) or item.get('type') not in ('directory','file','symlink'):raise ValueError('Invalid metadata inode type')
  expected={'type','mode','uid','gid','xattrs','selinux_label','capabilities'}|({'size'} if item['type']!='directory' else set())|({'target'} if item['type']=='symlink' else set())
  if set(item)!=expected or any(type(item[key]) is not int or not 0<=item[key]<2**32 for key in ('uid','gid')) or type(item['mode']) is not int or not 0<=item['mode']<=0o7777 or type(item['capabilities']) is not int or not 0<=item['capabilities']<2**64:raise ValueError('Invalid inode metadata schema')
  if item['type']!='directory' and (type(item['size']) is not int or not 0<=item['size']<2**64):raise ValueError('Invalid inode size')
  if item['type']=='symlink' and (not isinstance(item['target'],str) or '\0' in item['target'] or len(item['target'].encode())!=item['size']):raise ValueError('Invalid symlink target')
  if not isinstance(item['xattrs'],dict) or set(item['xattrs'])-{'security.selinux','security.capability'}:raise ValueError('Profile rebuild supports only SELinux/capability xattrs')
  for name,value in item['xattrs'].items():
   if not re.fullmatch(r'[A-Za-z0-9_.-]+',name) or not isinstance(value,str) or len(value)%2 or not re.fullmatch(r'[0-9a-f]*',value):raise ValueError('Invalid raw xattr encoding')
  raw=bytes.fromhex(item['xattrs'].get('security.selinux',''));label=raw.rstrip(b'\0').decode('ascii') if raw else None
  if label!=item['selinux_label'] or capability_mask(bytes.fromhex(item['xattrs'].get('security.capability','')))!=item['capabilities']:raise ValueError('Semantic metadata differs from raw xattrs')
 return True

def validate_profile(root):
 root=Path(root);profile=json_unique(checked_file(root,'profile.json').read_bytes())
 if not isinstance(profile,dict) or set(profile)!={'format','kind','android_api','architecture','source','metadata_method','owner_device_capture_used','composition_ready','image_avb_assembled','hardware_trust_verified','google_payload_included','partitions','limitations','build_settings','file_contexts'}:raise ValueError('Unexpected composition profile fields')
 if profile['android_api']!=34 or profile['architecture']!='arm' or any(profile[key] is not False for key in ['owner_device_capture_used','composition_ready','image_avb_assembled','hardware_trust_verified','google_payload_included']):raise ValueError('Invalid profile scope flags')
 if set(profile['source'])!={'target_files_sha256','source_revision','base_images_supplied_separately'} or (profile['source']['source_revision'] is not None and not re.fullmatch(r'[0-9a-f]{7,64}',profile['source']['source_revision'])) or type(profile['source']['base_images_supplied_separately']) is not bool:raise ValueError('Invalid/sensitive profile provenance')
 if type(profile.get('format')) is not int or profile['format']!=1 or profile.get('kind')!='gapps-composition-profile' or set(profile.get('partitions',{}))!=set(PARTS) or profile.get('composition_ready') is not False:raise ValueError('Unsupported composition profile schema')
 sha256_value(profile['source']['target_files_sha256'])
 method=profile['metadata_method']
 if not isinstance(method,dict) or set(method)!={'reader_source_sha256','native_fsck_sha256','regular_file_contents_verified'} or method['regular_file_contents_verified'] is not False:raise ValueError('Invalid metadata method provenance')
 sha256_value(method['reader_source_sha256'])
 if method['native_fsck_sha256'] is not None:sha256_value(method['native_fsck_sha256'])
 settings=profile['build_settings']
 if not isinstance(settings,dict) or set(settings)!={'compressor','pcluster_size','settings_source'} or not isinstance(settings['compressor'],str) or not re.fullmatch(r'lz4hc,[0-9]+|lz4|none',settings['compressor']) or type(settings['pcluster_size']) is not int or not 4096<=settings['pcluster_size']<=1048576 or settings['pcluster_size']&(settings['pcluster_size']-1) or settings['settings_source']!='META/misc_info.txt (filtered; key paths excluded)':raise ValueError('Invalid/sensitive EROFS build settings')
 if not isinstance(profile['file_contexts'],dict) or set(profile['file_contexts'])!={'file','sha256','source_member'} or profile['file_contexts']['file']!='metadata/file_contexts.bin' or profile['file_contexts']['source_member']!='META/file_contexts.bin':raise ValueError('Unexpected file-context provenance')
 for part,item in profile['partitions'].items():
  if not isinstance(item,dict) or set(item)!={'image_sha256','image_bytes','partition_bytes','mount_point','erofs','metadata','fs_config','source_fs_config','native_fsck_verified','metadata_entries'}:raise ValueError('Unexpected partition profile fields')
  for key,expected in [('metadata','metadata/'+part+'.metadata.json'),('fs_config','metadata/'+part+'.fs_config'),('source_fs_config','metadata/'+part+'.source_fs_config.txt')]:
   fields={'file','sha256'}|({'source_member'} if key=='source_fs_config' else set())
   if not isinstance(item[key],dict) or set(item[key])!=fields or item[key]['file']!=expected:raise ValueError('Unexpected metadata sidecar path/fields')
  expected_member='META/'+('filesystem_config.txt' if part=='system' else part+'_filesystem_config.txt')
  if item['source_fs_config']['source_member']!=expected_member:raise ValueError('Invalid filesystem config provenance')
  if item['mount_point']!=('/' if part=='system' else part) or type(item['native_fsck_verified']) is not bool:raise ValueError('Invalid partition profile')
 for item in [profile['file_contexts']]+[r[key] for r in profile['partitions'].values() for key in ['metadata','fs_config','source_fs_config']]:
  if digest(checked_file(root,item['file']))!=sha256_value(item['sha256']):raise ValueError('Composition metadata hash mismatch')
 for part,item in profile['partitions'].items():
  sha256_value(item['image_sha256'])
  if type(item['image_bytes']) is not int or type(item['partition_bytes']) is not int or not 0<item['image_bytes']<=item['partition_bytes']:raise ValueError('Invalid base image budget')
  geometry=item['erofs']
  if not isinstance(geometry,dict) or set(geometry)!={'block_size','filesystem_bytes','uuid','build_epoch','build_nsec','incompat_features'} or geometry['block_size']!=4096 or any(type(geometry[key]) is not int or geometry[key]<0 for key in ['filesystem_bytes','build_epoch','build_nsec','incompat_features']) or not 0<geometry['filesystem_bytes']<=item['image_bytes'] or geometry['build_nsec']>=1000000000 or geometry['incompat_features']&~3:raise ValueError('Invalid EROFS geometry')
  uuid.UUID(geometry['uuid'])
  snapshot=json_unique(checked_file(root,item['metadata']['file']).read_bytes())
  validate_snapshot(snapshot)
  if type(item['metadata_entries']) is not int or item['metadata_entries']!=len(snapshot):raise ValueError('Metadata entry count mismatch')
  if canned_config(snapshot,part)!=checked_file(root,item['fs_config']['file']).read_bytes():raise ValueError('Canned metadata differs from authoritative snapshot')
  parse_fs_config(checked_file(root,item['source_fs_config']['file']).read_bytes())
 return {'passed':True,'composition_ready':False,'regular_file_contents_verified':False,'native_fsck_verified_at_export':all(p['native_fsck_verified'] for p in profile['partitions'].values()),'image_files_rechecked_by_validation':False,'compiled_context_rebuild_equivalence_proved':False}


def recipe_additions(recipe,part,before):
 validate_recipe(recipe);out={}
 for entry in recipe['entries']:
  if entry['partition']!=part:continue
  path=entry['image_path']
  if path in before:raise ValueError('Google destination already exists')
  out[path]={'type':'file','uid':entry['uid'],'gid':entry['gid'],'mode':entry['mode'],'size':entry['bytes'],'capabilities':entry['capabilities'],'selinux_label':entry['selinux_label'],'xattrs':{'security.selinux':entry['selinux_label'].encode().hex()}}
  parent=Path(path).parent
  while str(parent)!='.':
   name=parent.as_posix()
   if name not in before:out[name]={'type':'directory','uid':0,'gid':0,'mode':0o755,'capabilities':0,'selinux_label':LABEL,'xattrs':{'security.selinux':LABEL.encode().hex()}}
   parent=parent.parent
 return out


def main():
 os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
 recipe=commands.add_parser('export-recipe');recipe.add_argument('--gapps',type=Path,required=True);recipe.add_argument('--input-manifest',type=Path,required=True)
 export=commands.add_parser('export');export.add_argument('--target-files',type=Path,required=True);export.add_argument('--output',type=Path,required=True);export.add_argument('--partition-limits',type=Path,required=True);export.add_argument('--fsck-erofs',type=Path,required=True);export.add_argument('--base-images',type=Path);export.add_argument('--source-revision')
 check=commands.add_parser('validate');check.add_argument('--profile',type=Path,required=True)
 compare=commands.add_parser('compare');compare.add_argument('--before',type=Path,required=True);compare.add_argument('--after',type=Path,required=True);compare.add_argument('--fsck-erofs',type=Path,required=True);compare.add_argument('--recipe',type=Path);compare.add_argument('--partition',choices=PARTS)
 args=parser.parse_args()
 if args.command=='export-recipe':result=export_recipe(args.gapps,json_unique(args.input_manifest.read_bytes()))
 elif args.command=='export':result=export_profile(args.target_files,args.output,json_unique(args.partition_limits.read_bytes()),args.fsck_erofs,args.base_images,args.source_revision)
 elif args.command=='validate':result=validate_profile(args.profile)
 else:
  snapshots=[]
  for path in [args.before,args.after]:
   subprocess.run([str(args.fsck_erofs),str(path)],check=True,stdout=subprocess.DEVNULL)
   with ErofsMetadata(path) as reader:snapshots.append(reader.snapshot())
  allowed=None
  if args.recipe:
   if args.partition is None:parser.error('--recipe requires --partition')
   allowed=recipe_additions(json_unique(args.recipe.read_bytes()),args.partition,snapshots[0])
  result=compare_metadata(*snapshots,allowed);result['native_fsck_integrity_verified']=True
 print(json.dumps(result,indent=2))
 if result.get('passed') is False:raise SystemExit(1)

if __name__=='__main__':main()
