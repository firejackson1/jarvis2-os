#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""UNQUALIFIED OFFLINE DEVELOPMENT installer; default dry-run, no boot/slot/wipe.

Do not run on hardware without a separately approved qualification. Execution
requires --execute and operator-pinned current capture/candidate proof/old images.
Only complete existing foundations and RAM linear maps are supported. No LP,
fastboot, snapshot cancellation or metadata mount operation exists in this tool.
"""
import argparse,hashlib,importlib.util,json,os,re,shlex,stat,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('candidate_slot_plan',Path(__file__).with_name('slot-install-plan.py'));PLAN=importlib.util.module_from_spec(spec);spec.loader.exec_module(PLAN)
REQUIRED_PHYSICAL=tuple(p+'_'+s for p in ['bootloader','boot','init_boot','vendor_boot','dtbo','oem','odm_ext','vbmeta','vbmeta_system'] for s in 'ab')+('misc','metadata')


def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def regular(path):
 path=Path(os.path.abspath(path))
 if any(p.is_symlink() for p in [path,*path.parents]) or not path.is_file():raise ValueError('Unsafe local file path')
 return path


def unique(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError('Duplicate JSON key')
  result[key]=value
 return result


def pin(value):
 if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid SHA256 pin')


def pinned(path,expected):
 pin(expected);path=regular(path)
 if path.stat().st_size>2*1024*1024 or digest(path)!=expected:raise ValueError('Pinned capture/proof changed')
 return json.loads(path.read_bytes(),object_pairs_hook=unique)


def record(value):
 if not isinstance(value,dict) or set(value)!={'bytes','sha256'} or type(value['bytes']) is not int or value['bytes']<=0:raise ValueError('Invalid exact image record')
 pin(value['sha256'])


def device(value,hashed=True):
 keys={'path','major','minor','bytes'}|({'sha256'} if hashed else set())
 if not isinstance(value,dict) or set(value)!=keys or not isinstance(value['path'],str) or not re.fullmatch('/dev/block/[A-Za-z0-9_.-]+',value['path']):raise ValueError('Invalid physical identity')
 if any(type(value[k]) is not int or value[k]<0 for k in ['major','minor','bytes']) or not value['bytes'] or value['bytes']%512:raise ValueError('Invalid physical size/identity')
 if hashed:pin(value['sha256'])


def image_files(folder,records):
 folder=Path(folder)
 if folder.is_symlink() or not folder.is_dir() or {p.name for p in folder.iterdir()}!=set(records):raise ValueError('Image directory must contain exactly the declared regular raw files')
 for name,info in records.items():
  if not re.fullmatch(r'(system|system_ext|product|vbmeta|vbmeta_system|init_boot|vendor_boot)\.img',name):raise ValueError('Unknown image identity')
  record(info);path=regular(folder/name)
  if path.stat().st_size!=info['bytes'] or digest(path)!=info['sha256']:raise ValueError('Pinned image bytes differ')
  with path.open('rb') as f:
   if f.read(4)==b'\x3a\xff\x26\xed':raise ValueError('Sparse images unsupported')


class ADB:
 def __init__(self,path,serial):self.path=str(path);self.serial=serial
 def run(self,*args,binary=False):
  command=[self.path]+([] if args and args[0]=='devices' else ['-s',self.serial])+list(args)
  result=subprocess.run(command,capture_output=True,check=True)
  return result.stdout if binary else result.stdout.decode('utf-8',errors='strict')


class Journal:
 def __init__(self,path,header,resume):
  self.path=Path(os.path.abspath(path));self.records=[]
  if any(p.is_symlink() for p in [self.path,*self.path.parents]) or ROOT==self.path or ROOT in self.path.parents:raise ValueError('Unsafe journal path')
  if resume:
   regular(self.path)
   if self.path.stat().st_size>4*1024*1024:raise ValueError('Journal too large')
   self.records=[json.loads(line,object_pairs_hook=unique) for line in self.path.read_text().splitlines()]
   if not self.records or self.records[0]!=header:raise ValueError('Journal input binding differs')
   if any(not isinstance(r,dict) or r.get('event') not in ['header','before_write','verified','operation_complete'] for r in self.records):raise ValueError('Unknown journal record')
  else:
   fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);os.close(fd);self.append(header)
 def append(self,value):
  with os.fdopen(os.open(self.path,os.O_WRONLY|os.O_APPEND|os.O_NOFOLLOW),'ab') as f:f.write((json.dumps(value,sort_keys=True)+'\n').encode());f.flush();os.fsync(f.fileno())
  fd=os.open(self.path.parent,os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd)
  finally:os.close(fd)
  self.records.append(value)


def parse_table(text,name,super_identity):
 lines=text.strip().splitlines()
 if not lines or lines[0]!='Targets in the device-mapper table for '+name+':':raise ValueError('Unknown dmctl table format')
 result=[]
 for line in lines[1:]:
  match=re.fullmatch(r'([0-9]+)-([0-9]+): linear, ([^ ]+) ([0-9]+)',line)
  if not match:raise ValueError('Unsupported nonlinear/verity/COW or unknown DM table')
  start,end,backing,offset=match.groups();identity=str(super_identity['major'])+':'+str(super_identity['minor'])
  if backing not in (super_identity['path'],identity) or int(end)<=int(start):raise ValueError('DM backing identity/range mismatch')
  result.append((int(start),int(end)-int(start),int(offset)))
 if not result:raise ValueError('Empty DM table')
 return result


def install(args,transport=None,view_loader=None):
 capture=pinned(args.capture,args.capture_sha256);proof=pinned(args.candidate_proof,args.candidate_proof_sha256)
 if capture.get('format')!=1 or type(capture.get('format')) is not int or capture.get('current_slot') not in ('a','b') or not re.fullmatch('[A-Za-z0-9_-]{1,128}',capture.get('serial','')):raise ValueError('Invalid capture identity')
 if args.slot not in ('a','b') or proof.get('target_slot')!=args.slot or proof.get('capture_sha256')!=args.capture_sha256 or any(proof.get(k) is not True for k in ['passed','avb_offline_verified','foundation_compatible']):raise ValueError('Candidate proof must bind slot/current capture and reviewed AVB/foundation')
 expected={p+'.img' for p in PLAN.PARTS}
 if not isinstance(proof.get('files'),dict) or set(proof['files'])!=expected:raise ValueError('Expected five candidate images')
 if set(capture.get('physical',{}))!=set(REQUIRED_PHYSICAL):raise ValueError('Complete protected physical inventory required')
 device(capture['super'],False)
 for item in capture['physical'].values():device(item)
 devices=[capture['super'],*capture['physical'].values()]
 if len({p['path'] for p in devices})!=len(devices) or len({(p['major'],p['minor']) for p in devices})!=len(devices):raise ValueError('Physical aliases are forbidden')
 physical=capture['physical'];prefix=capture['metadata_prefix'];record(prefix)
 if prefix['bytes']%512 or prefix['bytes']>16*1024*1024 or prefix['bytes']>capture['super']['bytes']:raise ValueError('Invalid bounded metadata prefix')
 dmctl=capture['dmctl'];pin(dmctl['sha256'])
 if not re.fullmatch(r'/(tmp|sbin|system/bin)/[A-Za-z0-9_.-]+',dmctl['path']):raise ValueError('Unsupported operator-staged dmctl path')
 transition=getattr(args,'transition_proof',None);transition_pin=getattr(args,'transition_proof_sha256',None);extra={}
 if any(bool(x) for x in [transition,transition_pin,getattr(args,'transition_images',None)]):
  if not all([transition,transition_pin,args.transition_images]):raise ValueError('Explicit pinned transition proof/images required together')
  t=pinned(transition,transition_pin)
  if any(t.get(k) is not True for k in ['passed','foundation_compatible','recovery_transition_reviewed']) or t.get('target_slot')!=args.slot or t.get('capture_sha256')!=args.capture_sha256 or t.get('candidate_proof_sha256')!=args.candidate_proof_sha256 or set(t.get('files',{}))!={'init_boot.img','vendor_boot.img'}:raise ValueError('Invalid explicit bootstrap transition proof')
  extra=t['files'];image_files(args.transition_images,extra)
 all_new=dict(proof['files'],**extra);old=capture.get('old_files')
 if not isinstance(old,dict) or set(old)!=set(all_new):raise ValueError('Complete pinned old restore images required')
 image_files(args.images,proof['files']);image_files(args.old_images,old)
 for name in all_new:
  record(all_new[name]);record(old[name])
  if all_new[name]['bytes']%4096 or all_new[name]['bytes']!=old[name]['bytes']:raise ValueError('Exact sizes must stay unchanged')
  part=name[:-4]+'_'+args.slot
  if part in physical and old[name]!={k:physical[part][k] for k in ['bytes','sha256']}:raise ValueError('Restore image differs from captured physical image')
 if args.restore and not args.resume:raise ValueError('Restore requires explicit resume of the bound journal')
 if transport is None:
  for path,value in [(args.adb,args.adb_sha256),(args.lpdump,args.lpdump_sha256)]:pin(value);regular(path)
  if digest(args.adb)!=args.adb_sha256 or digest(args.lpdump)!=args.lpdump_sha256:raise ValueError('Host tool pin mismatch')
  transport=ADB(args.adb,capture['serial'])
 adb=transport
 def shell(*tokens):return adb.run('shell',shlex.join(str(t) for t in tokens)).strip()
 def size(path):
  result=shell('blockdev','--getsize64',path)
  if not re.fullmatch('[0-9]+',result):raise ValueError('Unknown block size response')
  return int(result)
 def identity(path):
  result=shell('stat','-Lc','%t:%T',path)
  if not re.fullmatch('[0-9a-fA-F]+:[0-9a-fA-F]+',result):raise ValueError('Unknown physical stat response')
  return tuple(int(n,16) for n in result.split(':'))
 def remote_hash(path):
  value=shell('sha256sum',path).split()[0];pin(value);return value
 def path_state(path):return shell('sh','-c','if [ -L "$1" ]; then printf symlink; elif [ -d "$1" ]; then printf directory; elif [ -f "$1" ]; then printf file; elif [ ! -e "$1" ]; then printf absent; else printf unsupported; fi','probe',path)
 def require_ram(path,mounts):
  choices=[mt for mt in mounts if path==mt[1] or path.startswith(mt[1].rstrip('/')+'/')]
  if not choices:raise ValueError('RAM staging mount is unknown')
  deepest=max(len(mt[1]) for mt in choices);matches=[mt for mt in choices if len(mt[1])==deepest]
  if len(matches)!=1:raise ValueError('Ambiguous stacked staging mounts')
  chosen=matches[0]
  if chosen[3] not in ('tmpfs','ramfs','rootfs') or 'rw' not in chosen[2]:raise ValueError('Staging must be writable RAM, not persistent storage')
 def read_prefix():
  data=adb.run('exec-out','dd','if='+capture['super']['path'],'bs=512','count='+str(prefix['bytes']//512),'status=none',binary=True)
  if len(data)!=prefix['bytes'] or hashlib.sha256(data).hexdigest()!=prefix['sha256']:raise ValueError('Protected metadata prefix differs')
  return data
 def basic_guard():
  lines=adb.run('devices','-l').splitlines();matches=[l.split() for l in lines if l.split() and l.split()[0]==capture['serial']]
  if len(matches)!=1 or matches[0][1] not in ('device','recovery') or not any(x.startswith('usb:') for x in matches[0][2:]) or adb.run('get-serialno').strip()!=capture['serial']:raise ValueError('Exact USB identity required')
  if shell('id','-u')!='0' or shell('getprop','ro.boot.slot_suffix')!='_'+capture['current_slot'] or shell('getprop','sys.boot_completed') not in ('','0'):raise ValueError('Root recovery/current slot required')
  processes={Path(x.strip()).name for x in shell('ps','-A','-o','NAME').splitlines()}
  if 'dd' in processes:raise ValueError('Existing dd process: wait for independently verified writer quiescence; no automatic kill')
  if 'recovery' not in processes or processes&{'system_server','zygote','zygote64','surfaceflinger','fastbootd','update_engine','update_engine_sideload','snapuserd'}:raise ValueError('Recovery only; Android/update services must be stopped')
  ranges=[];parents=set()
  for name,item in dict(physical,super=capture['super']).items():
   if shell('readlink','-f','/dev/block/by-name/'+name)!=item['path'] or identity(item['path'])!=(item['major'],item['minor']) or size(item['path'])!=item['bytes']:raise ValueError('Live physical identity/size differs: '+name)
   sys='/sys/dev/block/'+str(item['major'])+':'+str(item['minor']);resolved=shell('readlink','-f',sys)
   if not resolved.startswith('/sys/devices/') or Path(resolved).name!=Path(item['path']).name:raise ValueError('Physical partition sysfs identity differs')
   parents.add(str(Path(resolved).parent));start=shell('cat',sys+'/start');count=shell('cat',sys+'/size')
   if not re.fullmatch('[0-9]+',start) or not re.fullmatch('[0-9]+',count) or int(count)*512!=item['bytes']:raise ValueError('Unknown physical partition sector geometry')
   ranges.append((int(start),int(start)+int(count)))
  if len(parents)!=1 or any(b[0]<a[1] for a,b in zip(sorted(ranges),sorted(ranges)[1:])):raise ValueError('Physical partitions overlap or use unsupported parent disks')
  if remote_hash(dmctl['path'])!=dmctl['sha256']:raise ValueError('Recovery dmctl tool pin mismatch')
  mounts=[]
  for line in shell('cat','/proc/self/mountinfo').splitlines():
   fields=line.split();sep=fields.index('-');mounts.append((fields[2],fields[4],set(fields[5].split(',')),fields[sep+1],fields[sep+2],set(fields[sep+3].split(',')),fields[3]))
  if shell('readlink','-f','/tmp')!='/tmp' or path_state('/tmp')!='directory':raise ValueError('Recovery /tmp must be a real RAM directory')
  require_ram('/tmp',mounts)
  metas=[m for m in mounts if m[1]=='/metadata'];meta=physical['metadata'];mid=str(meta['major'])+':'+str(meta['minor'])
  if any(mt[1].startswith('/metadata/') for mt in mounts):raise ValueError('Nested metadata mounts can hide snapshot state')
  if len(metas)!=1 or metas[0][6]!='/' or metas[0][0]!=mid or metas[0][3]!='f2fs' or 'ro' not in metas[0][2] or 'rw' in metas[0][2]|metas[0][5] or not ({'norecovery','disable_roll_forward'}&(metas[0][2]|metas[0][5])):raise ValueError('Metadata must already be verified f2fs read-only with rollforward disabled')
  if shell('readlink','-f',metas[0][4])!=meta['path']:raise ValueError('Metadata mount backing differs')
  # Only these exact directory shapes are supported; no protobuf/unknown state parsing.
  ota=path_state('/metadata/ota')
  entries=shell('find','/metadata/ota','-mindepth','1','-print').splitlines() if ota=='directory' else []
  if ota not in ('absent','directory') or entries not in ([],['/metadata/ota/snapshots']):raise ValueError('Persisted snapshot state must be absent, with at most empty snapshots directory')
  if entries and path_state('/metadata/ota/snapshots')!='directory':raise ValueError('Snapshot directory must be a real empty directory')
  read_prefix();return mounts
 mounts=basic_guard()
 with tempfile.TemporaryDirectory(prefix='jarvis2-plan-') as work:
  metadata=Path(work)/'super-prefix.img';metadata.write_bytes(read_prefix());physical_sizes={p:physical[p]['bytes'] for p in PLAN.PHYSICAL}
  views=(view_loader or PLAN.load_views)(str(args.lpdump),str(metadata),physical_sizes)
 manifest={'avb_offline_verified':True,'files':proof['files']};result=PLAN.plan(args.slot,manifest,views);PLAN.validate_images(Path(args.images),result)
 layout=views[0]['layout'];superdev=layout['block_devices'][0]
 if superdev['size']!=capture['super']['bytes'] or prefix['bytes']<12288+2*layout['metadata_max_size']*layout['metadata_slot_count']:raise ValueError('Fresh metadata geometry does not match live backing/prefix')
 for part in ['system','system_ext','product']:
  if any(e['target_data']*512<prefix['bytes'] for e in layout['partitions'][part+'_'+args.slot]):raise ValueError('Target overlaps protected captured prefix')
 logical={n:e for n,e in layout['partitions'].items() if e}
 if set(capture.get('logical_sha256',{}))!=set(logical):raise ValueError('Complete allocated logical hash inventory required')
 for value in capture['logical_sha256'].values():pin(value)
 for part in ['system','system_ext','product']:
  name=part+'_'+args.slot
  if old[part+'.img']['sha256']!=capture['logical_sha256'][name]:raise ValueError('Restore image differs from captured logical image')
 journal_path=Path(args.journal).absolute()
 for folder in [args.images,args.old_images]+([args.transition_images] if extra else []):
  if Path(folder).resolve()==journal_path or Path(folder).resolve() in journal_path.parents:raise ValueError('Journal must stay outside image inputs')
 header={'event':'header','format':1,'capture_sha256':args.capture_sha256,'candidate_proof_sha256':args.candidate_proof_sha256,'transition_proof_sha256':transition_pin,'slot':args.slot}
 journal=Journal(args.journal,header,args.resume)
 for r in journal.records[1:]:
  if r['event'] in ('before_write','verified'):
   name=r.get('partition','')[:-2]+'.img'
   if name not in all_new or r.get('partition')!=name[:-4]+'_'+args.slot or r.get('sha256') not in (all_new[name]['sha256'],old[name]['sha256']):raise ValueError('Journal target/hash is outside pinned operation')
  elif r['event']!='operation_complete' or r.get('set') not in ('old','new'):raise ValueError('Malformed journal state')
 tag='j2i_'+args.capture_sha256[:8]+args.candidate_proof_sha256[:8]+'_';tables={n:[(e['logical_sector'],e['num_sectors'],e['target_data']) for e in extents] for n,extents in logical.items()};maps={}
 def table(name):return parse_table(shell(dmctl['path'],'table',name),name,capture['super'])
 def mapped_path(name):
  path=shell(dmctl['path'],'getpath',name)
  if not re.fullmatch('/dev/block/dm-[0-9]+',path):raise ValueError('Unknown RAM mapping path')
  return path
 def inspect_maps(mounts):
  target_ids={(physical[p+'_'+args.slot]['major'],physical[p+'_'+args.slot]['minor']) for p in ['vbmeta','vbmeta_system']+(['init_boot','vendor_boot'] if extra else [])};target_ids.add((capture['super']['major'],capture['super']['minor']))
  for sysdev in shell('find','/sys/block','-maxdepth','1','-name','dm-*','-print').splitlines():
   if not re.fullmatch('/sys/block/dm-[0-9]+',sysdev):raise ValueError('Unknown sysfs mapper identity')
   name=shell('cat',sysdev+'/dm/name');part=name[len(tag):] if name.startswith(tag) else name
   if part not in tables or table(name)!=tables[part]:raise ValueError('Unknown/foreign/nonlinear DM table')
   path=mapped_path(name)
   if size(path)!=views[0]['sizes'][part]:raise ValueError('RAM mapping size differs')
   if name.startswith(tag):maps[part]=path
   if part in [p+'_'+args.slot for p in ['system','system_ext','product']]:target_ids.add(identity(path))
  if any(tuple(int(x) for x in mt[0].split(':')) in target_ids for mt in mounts):raise ValueError('Target or mounted alias is in use')
 inspect_maps(mounts)
 for part,entries in tables.items():
  name=tag+part
  existing=[shell('cat',p+'/dm/name') for p in shell('find','/sys/block','-maxdepth','1','-name','dm-*','-print').splitlines()]
  if name not in existing:
   cmd=[dmctl['path'],'create',name,'-ro']
   for start,count,offset in entries:cmd+=['linear',str(start),str(count),capture['super']['path'],str(offset)]
   shell(*cmd)
  if table(name)!=entries:raise ValueError('RAM-only table differs from validated extents')
  maps[part]=mapped_path(name)
 def target(part):return maps[part] if part in maps else physical[part]['path']
 changed={p[:-4]+'_'+args.slot for p in all_new}
 def protected_guard():
  inspect_maps(basic_guard())
  for part in maps:
   name=tag+part
   if table(name)!=tables[part]:raise ValueError('Owned map changed or disappeared')
   maps[part]=mapped_path(name)
   if size(maps[part])!=views[0]['sizes'][part]:raise ValueError('Owned map size changed')
  for name,item in physical.items():
   if name not in changed and remote_hash(item['path'])!=item['sha256']:raise ValueError('Protected physical partition changed: '+name)
  for name,path in maps.items():
   if name not in changed and remote_hash(path)!=capture['logical_sha256'][name]:raise ValueError('Protected logical partition changed: '+name)
 def classify(part,actual):
  name=part[:-2]+'.img';kind='old' if actual==old[name]['sha256'] else 'new' if actual==all_new[name]['sha256'] else 'partial'
  last=next((r['event'] for r in reversed(journal.records) if r.get('partition')==part),None)
  if kind=='partial' and (not args.resume or last!='before_write'):raise ValueError('Unexpected target corruption without a pending write')
  return kind
 def classify_all(initial=False):
  states={}
  for name in all_new:
   part=name[:-4]+'_'+args.slot;states[part]=classify(part,remote_hash(target(part)))
   if initial and not args.resume and states[part]!='old':raise ValueError('New run must match captured old state')
  return states
 protected_guard();classifications=classify_all(initial=True)
 desired=old if args.restore else all_new
 order=['system','system_ext','product']+(['init_boot','vendor_boot'] if extra else [])+['vbmeta_system','vbmeta']
 if args.execute:
  for base in order:
   name=base+'.img';part=base+'_'+args.slot;dest=target(part);wanted=desired[name]
   protected_guard();pinned(args.capture,args.capture_sha256);pinned(args.candidate_proof,args.candidate_proof_sha256)
   if transition:pinned(transition,transition_pin)
   classify_all()
   if remote_hash(target(part))==wanted['sha256']:continue
   if part in maps:
    mapname=tag+part
    if table(mapname)!=tables[part]:raise ValueError('RAM table changed')
    shell(dmctl['path'],'delete',mapname);cmd=[dmctl['path'],'create',mapname]
    for start,count,offset in tables[part]:cmd+=['linear',str(start),str(count),capture['super']['path'],str(offset)]
    shell(*cmd);maps[part]=mapped_path(mapname);dest=maps[part]
    if table(mapname)!=tables[part]:raise ValueError('Writable RAM table changed')
   source=Path(args.old_images if args.restore else args.transition_images if base in ['init_boot','vendor_boot'] else args.images)/name
   if digest(regular(source))!=wanted['sha256'] or size(dest)!=wanted['bytes']:raise ValueError('Write source/target changed')
   staged='/tmp/'+tag+part+'.img';require_ram(staged,basic_guard());state=path_state(staged)
   if state not in ('file','absent'):raise ValueError('Unsafe RAM staging destination')
   if state=='file':shell('rm',staged)
   adb.run('push',str(source),staged)
   if remote_hash(staged)!=wanted['sha256']:raise ValueError('Staged RAM image differs')
   # The long transfer precedes the final safety boundary and durable write intent.
   protected_guard();classify_all();pinned(args.capture,args.capture_sha256);pinned(args.candidate_proof,args.candidate_proof_sha256)
   if transition:pinned(transition,transition_pin)
   require_ram(staged,basic_guard())
   if path_state(staged)!='file' or remote_hash(staged)!=wanted['sha256']:raise ValueError('RAM staging source changed after transfer')
   if part in maps:
    if table(tag+part)!=tables[part]:raise ValueError('Post-transfer owned map table changed')
    fresh=mapped_path(tag+part)
    if fresh!=maps[part]:raise ValueError('Post-transfer mapper path changed')
    dest=fresh
   else:
    item=physical[part];dest=item['path']
    if shell('readlink','-f','/dev/block/by-name/'+part)!=dest or identity(dest)!=(item['major'],item['minor']):raise ValueError('Post-transfer physical target changed')
   if size(dest)!=wanted['bytes']:raise ValueError('Post-transfer target size changed')
   actual=remote_hash(dest);classify(part,actual)
   if actual==wanted['sha256']:continue
   # Hashing can take time: repeat cheap live guards after the final long read.
   boundary=basic_guard();inspect_maps(boundary);require_ram(staged,boundary)
   if path_state(staged)!='file':raise ValueError('Staging path changed at write boundary')
   if part in maps:
    if table(tag+part)!=tables[part] or mapped_path(tag+part)!=dest:raise ValueError('Mapper changed at write boundary')
   elif shell('readlink','-f','/dev/block/by-name/'+part)!=dest or identity(dest)!=(physical[part]['major'],physical[part]['minor']):raise ValueError('Physical target changed at write boundary')
   if size(dest)!=wanted['bytes']:raise ValueError('Target size changed at write boundary')
   journal.append({'event':'before_write','partition':part,'operation':'restore' if args.restore else 'install','sha256':wanted['sha256'],'bytes':wanted['bytes']})
   shell('dd','if='+staged,'of='+dest,'bs=4096','count='+str(wanted['bytes']//4096),'conv=fsync');shell('rm',staged)
   if remote_hash(dest)!=wanted['sha256']:raise ValueError('Full readback mismatch')
   journal.append({'event':'verified','partition':part,'sha256':wanted['sha256']})
  protected_guard()
  for name,item in desired.items():
   if remote_hash(target(name[:-4]+'_'+args.slot))!=item['sha256']:raise ValueError('Mixed set: final readback differs')
  journal.append({'event':'operation_complete','set':'old' if args.restore else 'new'})
 pinned(args.capture,args.capture_sha256);pinned(args.candidate_proof,args.candidate_proof_sha256)
 if transition:pinned(transition,transition_pin)
 return {'executed':bool(args.execute),'classifications':classifications,'final_set':('old' if args.restore else 'new') if args.execute else 'not_written','target_slot':args.slot,'hardware_qualified':False,'power_loss_before_recovery_proven':False,'interruption_restore_hardware_proven':False,'boot_requested':False,'slot_switch_requested':False,'wipe_requested':False,'metadata_writer_used':False}


def main():
 os.umask(0o077);p=argparse.ArgumentParser(description=__doc__)
 for name in ['capture','candidate-proof','images','old-images','journal','adb','lpdump']:p.add_argument('--'+name,type=Path,required=True)
 for name in ['capture-sha256','candidate-proof-sha256','adb-sha256','lpdump-sha256']:p.add_argument('--'+name,required=True)
 p.add_argument('--slot',choices=['a','b'],required=True)
 for name in ['transition-proof','transition-images']:p.add_argument('--'+name,type=Path)
 p.add_argument('--transition-proof-sha256')
 for name in ['execute','resume','restore']:p.add_argument('--'+name,action='store_true')
 print(json.dumps(install(p.parse_args()),indent=2))

if __name__=='__main__':main()
