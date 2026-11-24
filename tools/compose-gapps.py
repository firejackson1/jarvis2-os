#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compose local Google additions into a pinned EROFS/AVB baseline, never flash.

Caller must authenticate all baseline images, profile, recipe and host tools.
Profile/recipe/root pins make those choices explicit; they do not prove hardware
acceptance. Only explicitly supplied user RSA key files are used, never copied.
Requires the pinned AVB source API and companion audit/profile tools. Outputs
must be outside the repository/tool bundle and inputs. No Google updater runs.
Run with external 1GiB RAM/3GiB swap/one-CPU limits; Java heap is capped 256MiB.
"""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys,tempfile,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load_module(name,path):
 old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
 try:
  spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 finally:sys.dont_write_bytecode=old


PROFILE=load_module('jarvis2_composer_profile',Path(__file__).with_name('gapps-profile.py'))
AUDIT=load_module('jarvis2_composer_audit',Path(__file__).with_name('audit-avb-chain.py'))
PACKAGES=load_module('jarvis2_composer_packages',Path(__file__).with_name('verify-signed-packages.py'))
PARTS=PROFILE.PARTS


def check_output(output,input_directories):
 output=Path(output).resolve()
 if any(output==base or base in output.parents for base in [ROOT.resolve()]+[Path(p).resolve() for p in input_directories]):raise ValueError('Output must be outside repository/tool bundle and input trees')
 if output.exists():raise FileExistsError(output)
 return output


def regular(path):
 path=Path(path)
 if path.is_symlink() or not path.is_file():raise ValueError('Input must be a regular file, not a symlink')
 return path.resolve()


def pinned_json(path,pin):
 PROFILE.sha256_value(pin)
 if PROFILE.digest(regular(path))!=pin:raise ValueError('Caller policy/profile SHA256 pin mismatch')
 return PROFILE.json_unique(Path(path).read_bytes())


def destination(root,relative):
 PROFILE.safe_path(relative);current=Path(root)
 for component in relative.split('/')[:-1]:
  current=current/component
  if current.is_symlink() or (current.exists() and not current.is_dir()):raise ValueError('Unsafe Google ancestor path')
  if not current.exists():current.mkdir(mode=0o755)
 result=current/relative.split('/')[-1]
 if result.is_symlink() or result.exists():raise ValueError('Google destination already exists')
 return result


def content_snapshot(root):
 root=Path(root);result={'':{'type':'directory'}};pending=[root]
 while pending:
  folder=pending.pop()
  for entry in os.scandir(folder):
   path=Path(entry.path);relative=path.relative_to(root).as_posix();info=entry.stat(follow_symlinks=False)
   if stat.S_ISDIR(info.st_mode):result[relative]={'type':'directory'};pending.append(path)
   elif stat.S_ISLNK(info.st_mode):result[relative]={'type':'symlink','target':os.readlink(path)}
   elif stat.S_ISREG(info.st_mode):result[relative]={'type':'file','bytes':info.st_size,'sha256':PROFILE.digest(path)}
   else:raise ValueError('Unsupported staged file type')
 return result


def verify_content(before,after,expected_files,allowed_added):
 if any(after.get(path)!=value for path,value in before.items()):raise ValueError('Existing file contents/link targets changed')
 if set(after)-set(before)!=set(allowed_added):raise ValueError('Unexpected/missing added filesystem paths')
 for path,item in expected_files.items():
  if after.get(path)!={'type':'file','bytes':item['bytes'],'sha256':item['sha256']}:raise ValueError('Google input bytes changed')


def validate_root_policy(baseline,new,expected,allow_change):
 for pin in [baseline,new,expected]:PROFILE.sha256_value(pin)
 if new!=expected:raise ValueError('Supplied root key differs from caller output root pin')
 if baseline!=new and not allow_change:raise ValueError('Root key change requires explicit --allow-root-key-change')


def require_tree_geometry(tree):
 if (tree.data_block_size,tree.hash_block_size)!=(4096,4096) or getattr(tree,'dm_verity_version',1)!=1:raise ValueError('Only 4096-byte AVB data/hash block geometry is supported')

def prefix_digest(path,length):
 remaining=length;result=hashlib.sha256()
 with Path(path).open('rb') as f:
  while remaining:
   wanted=min(1048576,remaining);data=f.read(wanted)
   if len(data)!=wanted:raise ValueError('Unexpected EOF while checking filesystem prefix')
   result.update(data);remaining-=len(data)
 return result.hexdigest()

def verify_input_hashes(images,expected):
 for part,sha in expected.items():
  if PROFILE.digest(images[part])!=sha:raise ValueError('Baseline/reference input changed during composition: '+part)

def compose(args):
 for pin in [args.baseline_root_sha256,args.output_root_sha256,args.avbtool_source_sha256]:PROFILE.sha256_value(pin)
 profile=pinned_json(args.profile/'profile.json',args.profile_sha256);PROFILE.validate_profile(args.profile)
 recipe=pinned_json(args.recipe,args.recipe_sha256);PROFILE.validate_recipe(recipe)
 pin=dict(recipe['input'],format=1,architecture='arm',android_api=34,variant='ATV-minimal',source_revision=recipe['source_revision'])
 if PROFILE.export_recipe(regular(args.gapps),pin)!=recipe:raise ValueError('Google input does not exactly match the caller recipe')
 output=check_output(args.output,[args.profile,args.base_images,args.references,args.tool_tree])
 keys=[regular(args.root_key),regular(args.system_key)]
 if any(ROOT.resolve()==p or ROOT.resolve() in p.parents or output==p or output in p.parents for p in keys):raise ValueError('User keys must stay outside repository/tool bundle and output')
 source=regular(args.tool_tree/'external/avb/avbtool.py')
 if PROFILE.digest(source)!=args.avbtool_source_sha256:raise ValueError('AVB Python source revision/hash differs')
 avbtool=load_module('jarvis2_composer_pinned_avbtool',source);avb=avbtool.Avb()
 tools=args.tool_tree/'out/host/linux-x86/bin'
 required={name:regular((tools/name).resolve()) for name in ['mkfs.erofs','fsck.erofs','avbtool']}
 apksigner=regular(args.apksigner.resolve());java=regular((args.jdk/'bin/java').resolve())
 env=dict(os.environ,JAVA_HOME=str(args.jdk),PATH=str(args.jdk/'bin')+':'+str(tools)+':'+os.environ['PATH'])
 images={part:regular(args.base_images/(part+'.img')) for part in (*PARTS,'vbmeta','vbmeta_system')}
 baseline_hashes={part:PROFILE.digest(path) for part,path in images.items()}
 for part in PARTS:
  item=profile['partitions'][part]
  if baseline_hashes[part]!=item['image_sha256'] or images[part].stat().st_size!=item['partition_bytes']:raise ValueError('Baseline image hash/exact partition size differs from profile')
  with PROFILE.ErofsMetadata(images[part]) as reader:actual=reader.snapshot()
  wanted=PROFILE.json_unique(PROFILE.checked_file(args.profile,item['metadata']['file']).read_bytes())
  if not PROFILE.compare_metadata(wanted,actual)['passed']:raise ValueError('Baseline native metadata differs from profile')
 for name in ['vbmeta','vbmeta_system']:
  if not 0<images[name].stat().st_size<=16*1024*1024:raise ValueError('Unsupported vbmeta image size')
 def parse(path):
  image=avbtool.ImageHandler(str(path),read_only=True)
  try:return avb._parse_image(image)
  finally:image._image.close()
 def algorithm(header):
  for name,value in avbtool.ALGORITHMS.items():
   if value.algorithm_type==header.algorithm_type and name in ('SHA256_RSA2048','SHA256_RSA4096'):return name
  raise ValueError('Unsupported signed vbmeta algorithm')
 def header_policy(header):
  if header.flags or header.public_key_metadata_size:raise ValueError('Disabled verification or unsupported vbmeta flags/public-key metadata')
 # Validate descriptor paths before the existing auditor resolves any references.
 seen=set();active=set();reference_hashes={}
 def collect(part):
  if part in active:raise ValueError('AVB reference cycle')
  if part in seen:return
  if not re.fullmatch(r'[A-Za-z0-9_]+',part):raise ValueError('Unsafe AVB reference name')
  if part not in images:
   images[part]=regular(args.references/(part+'.img'));reference_hashes[part]=PROFILE.digest(images[part])
  active.add(part);_,header,descs,_=parse(images[part]);header_policy(header)
  for descriptor in descs:
   if isinstance(descriptor,(avbtool.AvbChainPartitionDescriptor,avbtool.AvbHashDescriptor,avbtool.AvbHashtreeDescriptor)):
    name=descriptor.partition_name
    if not re.fullmatch(r'[A-Za-z0-9_]+',name):raise ValueError('Unsafe AVB leaf name')
    if name not in images:images[name]=regular(args.references/(name+'.img'));reference_hashes[name]=PROFILE.digest(images[name])
    if isinstance(descriptor,avbtool.AvbChainPartitionDescriptor):collect(name)
   elif not isinstance(descriptor,(avbtool.AvbPropertyDescriptor,avbtool.AvbKernelCmdlineDescriptor)):
    raise ValueError('Unsupported AVB descriptor type')
  active.remove(part);seen.add(part)
 collect('vbmeta')
 templates={}
 for name in ['vbmeta','vbmeta_system']:
  _,header,descs,_=parse(images[name]);algorithm(header);header_policy(header);templates[name]=(header,descs)
 expected={'vbmeta':{'product'},'vbmeta_system':{'system','system_ext'}}
 for name,(_,descs) in templates.items():
  owned=[d.partition_name for d in descs if isinstance(d,avbtool.AvbHashtreeDescriptor) and d.partition_name in PARTS]
  if len(owned)!=len(expected[name]) or set(owned)!=expected[name]:raise ValueError('Unsupported userspace AVB descriptor ownership')
 chains=[d for d in templates['vbmeta'][1] if isinstance(d,avbtool.AvbChainPartitionDescriptor) and d.partition_name=='vbmeta_system']
 if len(chains)!=1:raise ValueError('Exactly one root-bound vbmeta_system child is required')
 leaves={}
 for part in PARTS:
  _,header,descs,_=parse(images[part]);trees=[d for d in descs if isinstance(d,avbtool.AvbHashtreeDescriptor)]
  if header.algorithm_type!=0 or header.rollback_index_location or header.flags or len(trees)!=1 or trees[0].partition_name!=part or trees[0].flags or trees[0].hash_algorithm not in ('sha256','sha512') or any(not isinstance(d,(avbtool.AvbHashtreeDescriptor,avbtool.AvbPropertyDescriptor)) for d in descs):raise ValueError('Unsupported leaf AVB footer policy')
  require_tree_geometry(trees[0]);leaves[part]=(header,trees[0],descs)
 output.mkdir(mode=0o700);(output/'images').mkdir();(output/'logs').mkdir()
 report={'status':'running','format':1,'google_payload_included':True,'private_local_output':True,'redistribution_permission_inferred':False,'device_modified':False,'hardware_root_trust_verified':False,'restore_tested':False,'ota_installer':False,'full_target_files_complete':False,'profile_sha256':args.profile_sha256,'recipe_sha256':args.recipe_sha256,'baseline_root_sha256':args.baseline_root_sha256,'output_root_sha256':args.output_root_sha256,'root_key_changed':args.baseline_root_sha256!=args.output_root_sha256,'baseline_image_sha256':baseline_hashes,'unchanged_reference_image_sha256':reference_hashes,'partitions':{},'files':{},'tool_hashes':{name:PROFILE.digest(path) for name,path in dict(required,apksigner=apksigner,java=java,avbtool_python=source).items()},'limitations':['Caller must authenticate original artifacts, profile, recipe and tools independently.','Filesystem checks cover exact paths/content/symlink targets, UID/GID/modes/labels/caps/raw xattrs; timestamps and storage/hardlink layout are not asserted unchanged.','Output key pin is an operator choice, not hardware acceptance or a supported migration/wipe/install route.']}
 redactions={str(keys[0]):'<user-root-key>',str(keys[1]):'<user-system-key>'}
 def redact(text):
  for path,label in redactions.items():text=text.replace(path,label)
  return text
 def save():
  tmp=output/'result.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(output/'composition.json')
 def run(command,label):
  process=subprocess.run([str(x) for x in command],capture_output=True,env=env)
  (output/'logs'/label).write_text(redact((process.stdout+process.stderr).decode(errors='replace')))
  if process.returncode:raise RuntimeError('Host tool failed; see '+label)
  return process.stdout
 def audit(tree,directory,pin):
  old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
  try:return AUDIT.audit(tree,args.tool_tree,directory,pin)
  finally:sys.dont_write_bytecode=old
 try:
  save()
  # Trusted baseline audit precedes key use, staging and signing.
  baseline=output/'baseline-reference-tree';baseline.mkdir()
  for part,path in images.items():(baseline/(part+'.img')).symlink_to(path)
  report['baseline_audit']=audit(baseline,output/'baseline-audit',args.baseline_root_sha256)
  root_public=avbtool.RSAPublicKey(str(keys[0])).encode();child_public=avbtool.RSAPublicKey(str(keys[1])).encode()
  root_sha=hashlib.sha256(root_public).hexdigest();validate_root_policy(args.baseline_root_sha256,root_sha,args.output_root_sha256,args.allow_root_key_change)
  report['system_public_key_sha256']=hashlib.sha256(child_public).hexdigest();save()
  import zipfile
  with zipfile.ZipFile(args.gapps) as archive:
   for part in PARTS:
    with tempfile.TemporaryDirectory(prefix='compose-',dir=output) as temporary:
     work=Path(temporary);staging=work/'staging';run([required['fsck.erofs'],'--no-preserve','--extract='+str(staging),images[part]],'extract-'+part+'.log')
     before=content_snapshot(staging)
     with PROFILE.ErofsMetadata(images[part]) as reader:native_before=reader.snapshot()
     allowed=PROFILE.recipe_additions(recipe,part,native_before);merged=dict(native_before,**allowed)
     selected=[entry for entry in recipe['entries'] if entry['partition']==part]
     for entry in selected:
      path=destination(staging,entry['image_path'])
      with archive.open(entry['zip_path']) as src,path.open('xb') as dst:shutil.copyfileobj(src,dst,1048576)
      if PROFILE.digest(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:raise ValueError('Pinned Google file bytes differ')
      if path.suffix=='.apk':run([apksigner,'-JXmx256M','-JXX:ActiveProcessorCount=1','verify','--verbose','--print-certs','--min-sdk-version','34','--max-sdk-version','34',path],'google-'+path.name+'.log')
     verify_content(before,content_snapshot(staging),{entry['image_path']:entry for entry in selected},set(allowed))
     config=work/'fs_config';config.write_bytes(PROFILE.canned_config(merged,part));item=profile['partitions'][part];settings=profile['build_settings'];target=output/'images'/(part+'.img')
     command=[required['mkfs.erofs'],'-b4096','-C'+str(settings['pcluster_size']),'--mount-point='+item['mount_point'],'--fs-config-file='+str(config),'--file-contexts='+str(PROFILE.checked_file(args.profile,profile['file_contexts']['file'])),'-T'+str(item['erofs']['build_epoch']),'-U'+item['erofs']['uuid']]
     if settings['compressor']!='none':command+=['-z'+settings['compressor']]
     run(command+[target,staging],'mkfs-'+part+'.log');run([required['fsck.erofs'],target],'fsck-'+part+'.log')
     with PROFILE.ErofsMetadata(target) as reader:native_after=reader.snapshot()
     metadata=PROFILE.compare_metadata(native_before,native_after,allowed)
     if not metadata['passed']:raise ValueError('Rebuilt EROFS metadata differs')
     extracted=work/'rebuilt';run([required['fsck.erofs'],'--no-preserve','--extract='+str(extracted),target],'verify-extract-'+part+'.log')
     verify_content(before,content_snapshot(extracted),{entry['image_path']:entry for entry in selected},set(allowed))
     raw_bytes=target.stat().st_size;raw_sha=PROFILE.digest(target);header,tree,descs=leaves[part]
     command=[required['avbtool'],'add_hashtree_footer','--image',target,'--partition_name',part,'--partition_size',str(item['partition_bytes']),'--algorithm','NONE','--block_size','4096','--hash_algorithm',tree.hash_algorithm,'--salt',tree.salt.hex(),'--rollback_index',str(header.rollback_index),'--flags',str(header.flags),'--internal_release_string',header.release_string]
     command+=['--fec_num_roots',str(tree.fec_num_roots)] if tree.fec_num_roots else ['--do_not_generate_fec']
     for descriptor in descs:
      if isinstance(descriptor,avbtool.AvbPropertyDescriptor):command+=['--prop',descriptor.key+':'+descriptor.value.decode('utf-8')]
     run(command,'footer-'+part+'.log')
     if prefix_digest(target,raw_bytes)!=raw_sha or target.stat().st_size!=item['partition_bytes']:raise ValueError('AVB append changed filesystem bytes or exact image size')
     _,new_header,new_descs,_=parse(target)
     if (new_header.flags,new_header.rollback_index,new_header.rollback_index_location,new_header.release_string)!=(header.flags,header.rollback_index,header.rollback_index_location,header.release_string):raise ValueError('Leaf rollback/verification flags changed')
     old_props=[d.encode() for d in descs if isinstance(d,avbtool.AvbPropertyDescriptor)];new_props=[d.encode() for d in new_descs if isinstance(d,avbtool.AvbPropertyDescriptor)]
     if old_props!=new_props:raise ValueError('Leaf AVB properties changed')
     new_tree=next(d for d in new_descs if isinstance(d,avbtool.AvbHashtreeDescriptor))
     if (new_tree.salt,new_tree.hash_algorithm,new_tree.flags,new_tree.fec_num_roots,new_tree.data_block_size,new_tree.hash_block_size)!=(tree.salt,tree.hash_algorithm,tree.flags,tree.fec_num_roots,tree.data_block_size,tree.hash_block_size):raise ValueError('Leaf AVB salt/hash/FEC policy changed')
     report['partitions'][part]={'native_metadata':metadata,'existing_content_entries_verified':len(before),'google_files_added':len(selected),'google_apk_signatures_verified':sum(x['image_path'].endswith('.apk') for x in selected),'all_existing_and_added_file_bytes_verified':True,'unsigned_erofs_bytes':raw_bytes,'unsigned_erofs_sha256':raw_sha,'salt':tree.salt.hex(),'rollback_index':header.rollback_index};save()
  for part,changed,key in [('vbmeta_system',{'system','system_ext'},keys[1]),('vbmeta',{'product'},keys[0])]:
   header,descs=templates[part];new=[]
   for descriptor in descs:
    value=copy.deepcopy(descriptor)
    if isinstance(value,avbtool.AvbHashtreeDescriptor) and value.partition_name in changed:value=next(d for d in parse(output/'images'/(value.partition_name+'.img'))[2] if isinstance(d,avbtool.AvbHashtreeDescriptor))
    if part=='vbmeta' and isinstance(value,avbtool.AvbChainPartitionDescriptor) and value.partition_name=='vbmeta_system':value.public_key=child_public
    new.append(value)
   blob=avb._generate_vbmeta_blob(algorithm_name=algorithm(header),key_path=str(key),public_key_metadata_path=None,descriptors=new,chain_partitions_use_ab=None,chain_partitions_do_not_use_ab=None,rollback_index=header.rollback_index,flags=header.flags,rollback_index_location=header.rollback_index_location,props=None,props_from_file=None,kernel_cmdlines=None,setup_rootfs_from_kernel=None,ht_desc_to_setup=None,include_descriptors_from_image=None,signing_helper=None,signing_helper_with_files=None,release_string=header.release_string,append_to_release_string=None,required_libavb_version_minor=header.required_libavb_version_minor)
   size=images[part].stat().st_size
   if len(blob)>size:raise ValueError('Signed vbmeta exceeds baseline physical size')
   target=output/'images'/(part+'.img');target.write_bytes(blob+b'\0'*(size-len(blob)));_,actual,actual_descs,_=parse(target)
   if (actual.flags,actual.rollback_index,actual.rollback_index_location,actual.algorithm_type,actual.required_libavb_version_minor,actual.release_string)!=(header.flags,header.rollback_index,header.rollback_index_location,header.algorithm_type,header.required_libavb_version_minor,header.release_string) or [d.encode() for d in actual_descs]!=[d.encode() for d in new]:raise ValueError('Signed descriptor/rollback/flag preservation failed')
  final=output/'final-reference-tree';final.mkdir()
  for part,path in images.items():(final/(part+'.img')).symlink_to((output/'images'/(part+'.img')) if part in (*PARTS,'vbmeta','vbmeta_system') else path)
  report['final_audit']=audit(final,output/'final-audit',args.output_root_sha256)
  verify_input_hashes(images,dict(baseline_hashes,**reference_hashes))
  report['files']={p.name:{'bytes':p.stat().st_size,'sha256':PROFILE.digest(p)} for p in sorted((output/'images').glob('*.img'))};report['status']='passed';save();return report
 except BaseException as error:
  report.update(status='failed',error=redact(str(error)),traceback=redact(traceback.format_exc()));save();raise RuntimeError(report['error']) from None


def main():
 os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
 for flag in ['profile','recipe','gapps','base-images','references','tool-tree','apksigner','jdk','root-key','system-key','output']:parser.add_argument('--'+flag,type=Path,required=True)
 for flag in ['profile-sha256','recipe-sha256','baseline-root-sha256','output-root-sha256','avbtool-source-sha256']:parser.add_argument('--'+flag,required=True)
 parser.add_argument('--allow-root-key-change',action='store_true');args=parser.parse_args();result=compose(args);print(json.dumps({'status':result['status'],'files':result['files'],'hardware_root_trust_verified':False},indent=2))

if __name__=='__main__':main()
