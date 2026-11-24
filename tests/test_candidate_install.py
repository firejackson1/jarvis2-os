# SPDX-License-Identifier: Apache-2.0
import copy,hashlib,importlib.util,json,shlex,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('installer',ROOT/'tools/install-candidate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def sha(data):return hashlib.sha256(data).hexdigest()
def payload(name,size=4096):
 data=(name+'|').encode();return (data*((size+len(data)-1)//len(data)))[:size]

class FakeADB:
 """File-backed physical devices and kernel linear maps, using the real command protocol."""
 def __init__(self,root,capture,views):
  self.root=root;self.capture=capture;self.views=views;self.commands=[];self.maps={};self.staged={};self.writes=[];self.fail_part=None;self.partial=False;self.foreign=False;self.mounted=False;self.snapshot=False;self.slot=capture['current_slot'];self.serial=capture['serial'];self.ro=True;self.no_replay=True;self.metadata_mounted=True;self.tmp_ram=True;self.stage_symlink=False;self.metadata_root="/";self.nested_metadata=False;self.on_push=None;self.on_write=None;self.on_hash=None;self.existing_dd=False;self.stacked_tmp=False;self.adb_state="device";self.ranges=[]
  self.devices={};self.ids={}
  for name,record in dict(capture['physical'],super=capture['super']).items():
   path=root/('device-'+name);path.write_bytes(b'\0'*record['bytes'] if name=='super' else payload('physical:'+name,record['bytes']));self.devices[record['path']]=path;self.ids[record['path']]=(record['major'],record['minor'])
  for name,extents in views[0]['layout']['partitions'].items():
   for e in extents:
    with self.devices[capture['super']['path']].open('r+b') as f:f.seek(e['target_data']*512);f.write(payload('logical:'+name,e['num_sectors']*512))
 def data(self,path):
  if path in self.devices:return self.devices[path].read_bytes()
  if path in self.staged:return self.staged[path]
  table=self.maps[next(n for n,x in self.maps.items() if x['path']==path)]['table'];out=b''
  for start,count,offset in table:
   with self.devices[self.capture['super']['path']].open('rb') as f:f.seek(offset*512);out+=f.read(count*512)
  return out
 def put(self,path,data):
  if path in self.devices:
   with self.devices[path].open('r+b') as f:f.write(data)
  else:
   table=self.maps[next(n for n,x in self.maps.items() if x['path']==path)]['table'];done=0
   for start,count,offset in table:
    chunk=data[done:done+count*512]
    with self.devices[self.capture['super']['path']].open('r+b') as f:f.seek(offset*512);f.write(chunk)
    done+=len(chunk)
 def run(self,*args,binary=False):
  self.commands.append(args)
  if args==('devices','-l'):return 'List of devices attached\n'+self.serial+' '+self.adb_state+' usb:1-2 product:fixture\n'
  if args==('get-serialno',):return self.serial+'\n'
  if args[0]=='push':
   self.staged[args[2]]=Path(args[1]).read_bytes()
   if self.on_push:self.on_push(args[2])
   return ''
  if args[0]=='exec-out':
   values=dict(x.split('=',1) for x in args[2:] if '=' in x);return self.data(values['if'])[:int(values['count'])*int(values['bs'])]
  assert args[0]=='shell',args
  a=shlex.split(args[1]);cmd=a[0]
  if cmd=='id':return '0\n'
  if cmd=='getprop':return {'sys.boot_completed':'0','ro.boot.slot_suffix':'_'+self.slot}[a[1]]+'\n'
  if cmd=='ps':return 'NAME\nrecovery\nadbd\n'+('dd\n' if self.existing_dd else '')
  if cmd=='readlink' and a[-1]=='/tmp':return '/tmp\n'
  if cmd=='readlink' and a[-1].startswith('/sys/dev/block/'):
   major,minor=map(int,a[-1].split('/')[-1].split(':'));return '/sys/devices/fixture/block/mmcblk0/'+Path(next(p for p,i in self.ids.items() if i==(major,minor))).name+'\n'
  if cmd=='readlink' and a[-1] in self.devices:return a[-1]+'\n'
  if cmd=='readlink':return self.capture['physical'][a[-1].split('/')[-1]]['path']+'\n' if a[-1].split('/')[-1] in self.capture['physical'] else self.capture['super']['path']+'\n'
  if cmd=='blockdev':return str(len(self.data(a[-1])))+'\n'
  if cmd=='stat':
   identity=self.ids[a[-1]] if a[-1] in self.ids else (253,int(a[-1].split('-')[-1]))
   return '%x:%x\n'%identity
  if cmd=='cat' and a[1].startswith('/sys/dev/block/'):
   major,minor=map(int,a[1].split('/')[-2].split(':'));path=next(p for p,i in self.ids.items() if i==(major,minor));return (str(len(self.data(path))//512) if a[1].endswith('/size') else str(minor*8192))+'\n'
  if cmd=='cat' and a[1]=='/proc/self/mountinfo':
   r=self.capture['physical']['metadata'];options='ro' if self.ro else 'rw';text=(f'1 0 {r["major"]}:{r["minor"]} {self.metadata_root} /metadata {options} - f2fs {r["path"]} {options}'+(',norecovery' if self.no_replay else '')+'\n') if self.metadata_mounted else ''
   text=('9 0 0:1 / / rw - '+('rootfs rootfs rw' if self.tmp_ram else 'ext4 /dev/block/root rw')+'\n')+text
   if self.stacked_tmp:text+='11 9 0:3 / /tmp rw - tmpfs tmpfs rw\n12 9 179:99 /private /tmp rw - ext4 /dev/block/private rw\n'
   if self.nested_metadata:text+='10 1 0:2 /clean /metadata/ota ro - tmpfs tmpfs ro\n'
   if self.mounted and self.maps:
    active=next((x['path'] for n,x in self.maps.items() if n.endswith('system_a')),next(iter(self.maps.values()))['path']);text+='2 0 253:'+active.split('-')[-1]+' / /system ro - erofs '+active+' ro\n'
   return text
  if cmd=='find' and a[1]=='/metadata/ota':return '/metadata/ota/snapshots\n'+('/metadata/ota/state\n' if self.snapshot else '')
  if cmd=='find' and a[1]=='/sys/block':return ''.join('/sys/block/'+x['path'].split('/')[-1]+'\n' for x in self.maps.values())
  if cmd=='cat' and a[1].startswith('/sys/block/'):
   dev=a[1].split('/')[3];return next(n+'\n' for n,x in self.maps.items() if x['path'].endswith('/'+dev))
  if cmd=='sh' and a[-2]=='probe':
   if a[-1].startswith('/tmp/j2i_'):return ('symlink' if self.stage_symlink else 'file' if a[-1] in self.staged else 'absent')+'\n'
   return 'directory\n'
  if cmd=='sha256sum':
   value=self.capture['dmctl']['sha256'] if a[1]==self.capture['dmctl']['path'] else sha(self.data(a[1]))
   if self.on_hash:self.on_hash(a[1])
   return value+'  '+a[1]+'\n'
  if cmd==self.capture['dmctl']['path']:
   op,name=a[1:3]
   if op=='create':
    tokens=a[3:];tokens=tokens[1:] if tokens[0]=='-ro' else tokens;table=[]
    while tokens:assert tokens[0]=='linear';table.append((int(tokens[1]),int(tokens[2]),int(tokens[4])));tokens=tokens[5:]
    self.maps[name]={'path':'/dev/block/dm-'+str(max([int(x['path'].split('-')[-1]) for x in self.maps.values()]+[-1])+1),'table':table};return ''
   if op=='getpath':return self.maps[name]['path']+'\n'
   if op=='delete':del self.maps[name];return ''
   if op=='table':return 'Targets in the device-mapper table for '+name+':\n'+''.join(f'{start}-{start+count}: linear, {self.capture["super"]["major"]}:{self.capture["super"]["minor"]} {offset}\n' for start,count,offset in self.maps[name]['table'])
  if cmd=='dd':
   values=dict(x.split('=',1) for x in a[1:]);dest=values['of']
   def note(length):
    if dest in self.devices:self.ranges.append((dest,0,length))
    else:
     remaining=length
     for start,count,offset in self.maps[next(n for n,x in self.maps.items() if x['path']==dest)]['table']:
      amount=min(remaining,count*512)
      if amount:self.ranges.append((self.capture['super']['path'],offset*512,offset*512+amount))
      remaining-=amount
   data=self.staged[values['if']][:int(values['bs'])*int(values['count'])];self.writes.append(values['of'])
   if self.fail_part and self.fail_part in values['if']:
    if self.partial:note(len(data)//2);self.put(values['of'],data[:len(data)//2])
    self.fail_part=None;raise RuntimeError('injected disconnect')
   note(len(data))
   self.put(values['of'],data)
   if self.on_write:self.on_write(values['of'])
   return ''
  if cmd=='rm':self.staged.pop(a[1],None);return ''
  raise AssertionError(args)

class InstallerTests(unittest.TestCase):
 def fixture(self,root,slot="a"):
  sizes={p+'_'+slot:4096 for p in m.PLAN.FOUNDATION for slot in 'ab'};sizes.update({p+'_'+slot:4096 for p in ['vbmeta','vbmeta_system'] for slot in 'ab'})
  parts={n:[{'logical_sector':0,'num_sectors':8,'target_type':'linear','target_source':0,'target_name':'super','target_data':2048+8*i}] for i,n in enumerate(sizes) if not n.startswith('vbmeta')}
  layout={'sector_size':512,'metadata_max_size':65536,'metadata_slot_count':2,'block_devices':[{'name':'super','size':2097152,'block_size':4096,'alignment':512,'alignment_offset':0,'first_logical_sector':2048}],'partitions':parts};view={'canonical':'fixture','sizes':sizes,'layout':layout};views=[view,copy.deepcopy(view)]
  record=lambda path,minor:{'path':path,'major':179,'minor':minor,'bytes':4096,'sha256':sha(b'\0'*4096)}
  capture={'format':1,'serial':'USBfixture','current_slot':'a','super':{'path':'/dev/block/mmcblk0p1','major':179,'minor':1,'bytes':2097152},'physical':{n:record('/dev/block/mmcblk0p'+str(i+2),i+2) for i,n in enumerate(m.REQUIRED_PHYSICAL)},'metadata_prefix':{'bytes':1048576,'sha256':sha(b'\0'*1048576)},'logical_sha256':{n:sha(payload('logical:'+n)) for n in parts},'old_files':{},'dmctl':{'path':'/tmp/fixture-dmctl','sha256':'d'*64}}
  for name,r in capture['physical'].items():r['sha256']=sha(payload('physical:'+name,r['bytes']))
  adb=FakeADB(root,capture,views);old=root/'old';new=root/'new';old.mkdir();new.mkdir();files={}
  for part in m.PLAN.PARTS:
   name=part+'.img';data=payload('logical:'+part+'_'+slot) if not part.startswith('vbmeta') else payload('physical:'+part+'_'+slot);(old/name).write_bytes(data);(new/name).write_bytes(payload('new:'+part));capture['old_files'][name]={'bytes':4096,'sha256':sha(data)};files[name]={'bytes':4096,'sha256':sha(payload('new:'+part))}
  cap=root/'capture.json';cap.write_text(json.dumps(capture));proof=root/'proof.json';proof.write_text(json.dumps({'passed':True,'avb_offline_verified':True,'foundation_compatible':True,'capture_sha256':m.digest(cap),'target_slot':slot,'files':files}))
  args=SimpleNamespace(capture=cap,capture_sha256=m.digest(cap),candidate_proof=proof,candidate_proof_sha256=m.digest(proof),slot=slot,images=new,old_images=old,journal=root/'journal.jsonl',execute=False,resume=False,restore=False,transition_proof=None,transition_proof_sha256=None,transition_images=None,lpdump=Path('/unused'))
  return args,adb,views
 def invoke(self,args,adb,views):return m.install(args,adb,lambda *unused:copy.deepcopy(views))
 def test_dry_run_actual_flow_has_no_persistent_writes(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));result=self.invoke(args,adb,views);self.assertEqual([],adb.writes);self.assertFalse(result['hardware_qualified']);self.assertEqual(5,len(result['classifications']));self.assertTrue(any(x[0]=='exec-out' for x in adb.commands))
 def test_partial_write_resume_and_restore_protect_other_slot_and_metadata(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));before={p:adb.data(r['path']) for p,r in adb.capture['physical'].items() if p.endswith('_b')};prefix=adb.data(adb.capture['super']['path'])[:1048576];protected_b={n:adb.data(adb.capture['super']['path'])[e[0]['target_data']*512:(e[0]['target_data']+e[0]['num_sectors'])*512] for n,e in views[0]['layout']['partitions'].items() if n.endswith('_b')}
   args.execute=True;adb.fail_part='system_ext';adb.partial=True
   with self.assertRaises(RuntimeError):self.invoke(args,adb,views)
   records=[json.loads(x) for x in args.journal.read_text().splitlines()];self.assertEqual('before_write',records[-1]['event']);args.resume=True
   result=self.invoke(args,adb,views);self.assertEqual('new',result['final_set']);args.restore=True;result=self.invoke(args,adb,views);self.assertEqual('old',result['final_set'])
   self.assertEqual(prefix,adb.data(adb.capture['super']['path'])[:1048576])
   for p,data in before.items():self.assertEqual(data,adb.data(adb.capture['physical'][p]['path']))
   for n,data in protected_b.items():
    e=views[0]['layout']['partitions'][n][0];self.assertEqual(data,adb.data(adb.capture['super']['path'])[e['target_data']*512:(e['target_data']+e['num_sectors'])*512])
   allowed=[(adb.capture['super']['path'],e[0]['target_data']*512,(e[0]['target_data']+e[0]['num_sectors'])*512) for n,e in views[0]['layout']['partitions'].items() if n in ['system_a','system_ext_a','product_a']]+[(adb.capture['physical'][n]['path'],0,4096) for n in ['vbmeta_a','vbmeta_system_a']]
   for device,start,end in adb.ranges:self.assertTrue(any(device==d and a<=start<=end<=b for d,a,b in allowed))
 def test_partial_operation_can_restore_without_finishing_install(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True;adb.fail_part='system_ext';adb.partial=True
   with self.assertRaises(RuntimeError):self.invoke(args,adb,views)
   args.resume=True;args.restore=True;result=self.invoke(args,adb,views);self.assertEqual('old',result['final_set'])
 def test_pending_resume_restore_refuses_surviving_dd_then_allows_quiescent_restore(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True;adb.fail_part='system_ext';adb.partial=True
   with self.assertRaises(RuntimeError):self.invoke(args,adb,views)
   pending=args.journal.read_bytes();before=len(adb.writes);args.resume=True;args.restore=True;adb.existing_dd=True
   with self.assertRaises(ValueError):self.invoke(args,adb,views)
   self.assertEqual(before,len(adb.writes));self.assertEqual(pending,args.journal.read_bytes())
   self.assertFalse(any(x[0]=='shell' and shlex.split(x[1])[0] in ['kill','killall','pkill'] for x in adb.commands))
   adb.existing_dd=False;result=self.invoke(args,adb,views);self.assertEqual('old',result['final_set'])
 def test_separately_pinned_seven_target_transition_and_restore(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);args,adb,views=self.fixture(root);folder=root/'transition';folder.mkdir();files={}
   for part in ['init_boot','vendor_boot']:
    name=part+'.img';data=adb.data(adb.capture['physical'][part+'_a']['path']);(folder/name).write_bytes(payload('transition:'+part));(args.old_images/name).write_bytes(data);adb.capture['old_files'][name]={'bytes':4096,'sha256':sha(data)};files[name]={'bytes':4096,'sha256':sha(payload('transition:'+part))}
   args.capture.write_text(json.dumps(adb.capture));args.capture_sha256=m.digest(args.capture);proof=json.loads(args.candidate_proof.read_text());proof['capture_sha256']=args.capture_sha256;args.candidate_proof.write_text(json.dumps(proof));args.candidate_proof_sha256=m.digest(args.candidate_proof)
   args.transition_images=folder;args.transition_proof=root/'transition.json';args.transition_proof.write_text(json.dumps({'passed':True,'foundation_compatible':True,'recovery_transition_reviewed':True,'target_slot':'a','capture_sha256':args.capture_sha256,'candidate_proof_sha256':args.candidate_proof_sha256,'files':files}));args.transition_proof_sha256=m.digest(args.transition_proof);args.execute=True
   approved=json.loads(args.transition_proof.read_text());bad=copy.deepcopy(approved);bad['candidate_proof_sha256']='f'*64;args.transition_proof.write_text(json.dumps(bad));args.transition_proof_sha256=m.digest(args.transition_proof)
   with self.assertRaises(ValueError):self.invoke(args,adb,views)
   self.assertFalse(adb.writes);args.transition_proof.write_text(json.dumps(approved));args.transition_proof_sha256=m.digest(args.transition_proof)
   result=self.invoke(args,adb,views);self.assertEqual(7,len(result['classifications']));self.assertEqual(7,len(adb.writes));self.assertEqual(payload('transition:vendor_boot'),adb.data(adb.capture['physical']['vendor_boot_a']['path']))
   args.resume=True;args.restore=True;self.invoke(args,adb,views);self.assertEqual(payload('physical:vendor_boot_a'),adb.data(adb.capture['physical']['vendor_boot_a']['path']))
 def test_bounded_dd_and_no_forbidden_persistent_apis(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True;self.invoke(args,adb,views)
   commands=[shlex.split(x[1]) for x in adb.commands if x[0]=='shell'];writes=[x for x in commands if x[0]=='dd'];self.assertEqual(5,len(writes))
   for command in writes:self.assertIn('count=1',command);self.assertIn('bs=4096',command);self.assertIn('conv=fsync',command)
   self.assertFalse(any(x[0] in ['fastboot','mount','bootctl','reboot'] or any('snapshot-update' in a or 'resize-logical' in a for a in x) for x in commands))
 def test_known_linear_map_preserved_and_mounted_alias_refused(self):
  for mounted in [False,True]:
   with self.subTest(mounted=mounted),tempfile.TemporaryDirectory() as t:
    args,adb,views=self.fixture(Path(t));e=views[0]['layout']['partitions']['system_a'][0];adb.maps['system_a']={'path':'/dev/block/dm-0','table':[(0,e['num_sectors'],e['target_data'])]};adb.mounted=mounted;args.execute=True
    if mounted:
     with self.assertRaises(ValueError):self.invoke(args,adb,views)
     self.assertFalse(adb.writes)
    else:
     self.invoke(args,adb,views);self.assertIn('system_a',adb.maps)
     deleted=[shlex.split(x[1])[2] for x in adb.commands if x[0]=='shell' and len(shlex.split(x[1]))>2 and shlex.split(x[1])[1]=='delete'];self.assertTrue(all(n.startswith('j2i_') for n in deleted))
 def test_explicit_complete_b_foundation_supported_without_slot_switch(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t),slot='b');args.execute=True
   before=adb.data(adb.capture['physical']['vbmeta_a']['path']);result=self.invoke(args,adb,views);self.assertEqual('b',result['target_slot']);self.assertFalse(result['slot_switch_requested']);self.assertEqual(before,adb.data(adb.capture['physical']['vbmeta_a']['path']))
 def test_resume_rejects_differently_pinned_proof_and_journal_input_tree(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True;adb.fail_part='system';adb.partial=True
   with self.assertRaises(RuntimeError):self.invoke(args,adb,views)
   before=len(adb.writes);args.resume=True;args.candidate_proof.write_text(json.dumps(json.loads(args.candidate_proof.read_text()),indent=2));args.candidate_proof_sha256=m.digest(args.candidate_proof)
   with self.assertRaises(ValueError):self.invoke(args,adb,views)
   self.assertEqual(before,len(adb.writes))
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.journal=args.old_images/'unsafe.jsonl'
   with self.assertRaises(ValueError):self.invoke(args,adb,views)

 def test_post_push_guards_refuse_mount_map_target_or_staging_changes(self):
  for fault in ['mount','map','target','staging_symlink','mount_after_final_hash']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    args,adb,views=self.fixture(Path(t));args.execute=True
    def mutate(path):
     name=next(n for n in adb.maps if n.endswith('system_a') and n.startswith('j2i_'))
     if fault=='mount_after_final_hash':
      counter=[0]
      def during_hash(device):
       if device==adb.maps[name]['path']:
        counter[0]+=1
        if counter[0]==2:adb.mounted=True
      adb.on_hash=during_hash
     if fault=='mount':adb.mounted=True
     if fault=='map':adb.maps[name]['table']=[(0,8,views[0]['layout']['partitions']['system_b'][0]['target_data'])]
     if fault=='target':adb.put(adb.maps[name]['path'],b'X'*4096)
     if fault=='staging_symlink':adb.stage_symlink=True
    adb.on_push=mutate
    with self.assertRaises((ValueError,RuntimeError)):self.invoke(args,adb,views)
    self.assertFalse(adb.writes)
    if args.journal.exists():self.assertFalse(any(json.loads(l)['event']=='before_write' for l in args.journal.read_text().splitlines()))
 def test_unknown_later_target_changed_during_previous_write_refused(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True
   def mutate(path):
    name=next(n for n in adb.maps if n.endswith('system_ext_a'));adb.put(adb.maps[name]['path'],b'X'*4096)
   adb.on_write=mutate
   with self.assertRaises(ValueError):self.invoke(args,adb,views)
   self.assertEqual(1,len(adb.writes))
 def test_historical_before_event_does_not_authorize_new_corruption(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True;self.invoke(args,adb,views);before=len(adb.writes);name=next(n for n in adb.maps if n.endswith('system_a'));adb.put(adb.maps[name]['path'],b'X'*4096);args.resume=True
   with self.assertRaises(ValueError):self.invoke(args,adb,views)
   self.assertEqual(before,len(adb.writes))

 def test_recovery_adb_banner_accepted_and_other_states_refused(self):
  for state in ['recovery','sideload','unauthorized','offline']:
   with self.subTest(state=state),tempfile.TemporaryDirectory() as t:
    args,adb,views=self.fixture(Path(t));adb.adb_state=state
    if state=='recovery':self.invoke(args,adb,views)
    else:
     with self.assertRaises(ValueError):self.invoke(args,adb,views)
    self.assertFalse(adb.writes)
 def test_unknown_dm_format_and_wrong_backing_are_rejected(self):
  identity={'path':'/dev/block/mmcblk0p1','major':179,'minor':1}
  for line in ['0-8: snapshot, 179:1 0','0-8: verity, anything','0-8: linear, 179:2 2048']:
   with self.subTest(line=line),self.assertRaises(ValueError):m.parse_table('Targets in the device-mapper table for name:\n'+line+'\n','name',identity)

 def test_bootloader_b_protected_and_bootloader_images_never_allowed(self):
  self.assertIn('bootloader_a',m.REQUIRED_PHYSICAL);self.assertIn('bootloader_b',m.REQUIRED_PHYSICAL)
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t));args.execute=True;adb.put(adb.capture['physical']['bootloader_b']['path'],b'X'*4096)
   with self.assertRaisesRegex(ValueError,'Protected physical'):self.invoke(args,adb,views)
   self.assertFalse(adb.writes)
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'bootloader.img').write_bytes(b'X'*4096)
   with self.assertRaises(ValueError):m.image_files(root,{'bootloader.img':{'bytes':4096,'sha256':sha(b'X'*4096)}})

 def test_refusals_before_any_persistent_write(self):
  for fault in ['serial','slot','snapshot','metadata_rw','mounted','proof','protected_b','prefix','metadata_unmounted','rollforward','tmp_persistent','stage_symlink','metadata_bind_root','hidden_ota_mount','stacked_tmp']:
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    args,adb,views=self.fixture(Path(t));args.execute=True
    if fault=='serial':adb.serial='wrong'
    if fault=='slot':adb.slot='b'
    if fault=='snapshot':adb.snapshot=True
    if fault=='metadata_rw':adb.ro=False
    if fault=='mounted':adb.mounted=True
    if fault=='proof':args.candidate_proof.write_text('{}')
    if fault=='stacked_tmp':adb.stacked_tmp=True
    if fault=='metadata_bind_root':adb.metadata_root='/clean-subdirectory'
    if fault=='hidden_ota_mount':adb.nested_metadata=True
    if fault=='tmp_persistent':adb.tmp_ram=False
    if fault=='stage_symlink':adb.stage_symlink=True
    if fault=='prefix':adb.put(adb.capture['super']['path'],b'X')
    if fault=='metadata_unmounted':adb.metadata_mounted=False
    if fault=='rollforward':adb.no_replay=False
    if fault=='protected_b':adb.put(adb.capture['physical']['vbmeta_b']['path'],b'X'*4096)
    with self.assertRaises((ValueError,RuntimeError)):self.invoke(args,adb,views)
    self.assertEqual([],adb.writes)
 def test_empty_b_foundation_is_never_provisioned(self):
  with tempfile.TemporaryDirectory() as t:
   args,adb,views=self.fixture(Path(t),slot='b')
   for v in views:v['sizes']['vendor_b']=0;v['layout']['partitions']['vendor_b']=[]
   with self.assertRaises(ValueError):self.invoke(args,adb,views)
   self.assertFalse(adb.writes)

if __name__=='__main__':unittest.main()
