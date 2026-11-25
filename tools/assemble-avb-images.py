#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assemble three caller-verified raw EROFS payloads into a pinned AVB baseline.

Offline only: no filesystem rebuild, install, slots or device access. Authenticate
baseline, references, new payloads and tools independently. Root pins do not
prove hardware acceptance. Payload content/metadata intent is NOT verified.
Requires companion composer/auditor helpers; only explicitly supplied user keys.
"""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,struct,subprocess,sys,tempfile,traceback
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('jarvis2_assembler_composer',Path(__file__).with_name('compose-gapps.py'))
C=importlib.util.module_from_spec(spec);old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
try:spec.loader.exec_module(C)
finally:sys.dont_write_bytecode=old
PROFILE=C.PROFILE;AUDIT=C.AUDIT;PARTS=C.PARTS;ROOT=C.ROOT


def strict_file(path):
 path=Path(os.path.abspath(path))
 if any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('Input path must not traverse symlinks')
 return C.regular(path)


def distinct_files(paths):
 seen=set()
 for path in paths.values():
  info=Path(path).stat();identity=(info.st_dev,info.st_ino)
  if identity in seen:raise ValueError('Ambiguous aliased input files')
  seen.add(identity)


def validate_raw(path):
 path=strict_file(path)
 with path.open('rb') as f:
  magic=f.read(4)
  if magic==b'\x3a\xff\x26\xed':raise ValueError('Android sparse input is unsupported')
  if path.stat().st_size>=64:
   f.seek(-64,2)
   if f.read(4)==b'AVBf':raise ValueError('Payload already has an AVB footer')
 with PROFILE.ErofsMetadata(path) as reader:geometry=reader.geometry
 if path.stat().st_size!=geometry['filesystem_bytes']:raise ValueError('Raw EROFS length must exactly match its block geometry; no trailing bytes/footer')
 return geometry


def footer_command(tool,target,part,budget,header,tree,descs,avbtool):
 command=[str(tool),'add_hashtree_footer','--image',str(target),'--partition_name',part,'--partition_size',str(budget),'--algorithm','NONE','--block_size','4096','--hash_algorithm',tree.hash_algorithm,'--salt',tree.salt.hex(),'--rollback_index',str(header.rollback_index),'--flags',str(header.flags),'--internal_release_string',header.release_string]
 command+=['--fec_num_roots',str(tree.fec_num_roots)] if tree.fec_num_roots else ['--do_not_generate_fec']
 for descriptor in descs:
  if isinstance(descriptor,avbtool.AvbPropertyDescriptor):command+=['--prop',descriptor.key+':'+descriptor.value.decode('utf-8')]
 return command


PROPERTY_POLICY={'format':1,'build_prop_paths':{'system':'system/build.prop','system_ext':'etc/build.prop','product':'etc/build.prop'},'fingerprint_source':'ro.{partition}.build.fingerprint','os_version_source':'ro.{partition}.build.version.release','security_patch_source':{'partition':'system','path':'system/build.prop','key':'ro.build.version.security_patch'}}


def validate_stock_profile(profile):
 if not isinstance(profile,dict) or set(profile)!={'format','templates','references','output_bytes','leaf_release_string','unbound_references'} or type(profile['format']) is not int or profile['format']!=1:raise ValueError('Unsupported stock profile schema')
 if not isinstance(profile['templates'],dict) or set(profile['templates'])!={'vbmeta','vbmeta_system'} or not isinstance(profile['references'],dict) or not profile['references']:raise ValueError('Missing stock templates/references')
 for name,item in list(profile['templates'].items())+list(profile['references'].items()):
  if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_]+',name) or not isinstance(item,dict) or set(item)!={'sha256','bytes'} or type(item['bytes']) is not int or item['bytes']<=0:raise ValueError('Invalid stock input identity')
  PROFILE.sha256_value(item['sha256'])
 if not isinstance(profile['unbound_references'],list) or any(not isinstance(n,str) for n in profile['unbound_references']) or len(profile['unbound_references'])!=len(set(profile['unbound_references'])) or not set(profile['unbound_references'])<=set(profile['references']):raise ValueError('Invalid explicit unbound references')
 if set(profile['references'])&set((*PARTS,'vbmeta','vbmeta_system')):raise ValueError('Stock references overlap changed images/templates')
 if not isinstance(profile['output_bytes'],dict) or set(profile['output_bytes'])!=set((*PARTS,'vbmeta','vbmeta_system')):raise ValueError('Missing explicit output budgets')
 for name,size in profile['output_bytes'].items():
  if type(size) is not int or size<=0 or size%4096 or (name.startswith('vbmeta') and size>16*1024*1024):raise ValueError('Invalid output budget')
 release=profile['leaf_release_string']
 if not isinstance(release,str) or not re.fullmatch(r'[ -~]{1,47}',release):raise ValueError('Invalid fresh leaf release string')


def parse_build_properties(text):
 result={}
 for line in text.splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  if '=' not in line or '\x00' in line:raise ValueError('Malformed canonical build.prop')
  key,value=line.split('=',1)
  if not re.fullmatch(r'[A-Za-z0-9_.-]+',key) or key in result:raise ValueError('Duplicate/malformed canonical property')
  result[key]=value
 return result


def desired_properties(values):
 result={}
 try:
  patch=values['system']['ro.build.version.security_patch']
  if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',patch):raise ValueError('Invalid global system security patch')
  for part in PARTS:
   for key,value in [('fingerprint',values[part]['ro.'+part+'.build.fingerprint']),('os_version',values[part]['ro.'+part+'.build.version.release']),('security_patch',patch)]:
    if not value or len(value)>1024 or any(ord(c)<32 or ord(c)>126 for c in value):raise ValueError('Invalid desired userspace property')
    result['com.android.build.'+part+'.'+key]=value.encode('ascii')
 except KeyError as e:raise ValueError('Missing canonical raw build property: '+str(e)) from None
 return result


def rewrite_properties(descriptors,values,parts,avbtool):
 result=[];seen=set()
 for descriptor in descriptors:
  value=copy.deepcopy(descriptor)
  if isinstance(value,avbtool.AvbPropertyDescriptor) and value.key in values:
   if value.key in seen or not any(value.key.startswith('com.android.build.'+part+'.') for part in parts):raise ValueError('Duplicate/misplaced userspace AVB property')
   seen.add(value.key);value.value=values[value.key]
  result.append(value)
 for key in sorted(values):
  if key not in seen and any(key.startswith('com.android.build.'+part+'.') for part in parts):
   value=avbtool.AvbPropertyDescriptor();value.key=key;value.value=values[key];result.append(value)
 return result


def validate_reference_coverage(used,references,unbound):
 unbound=set(unbound)
 if used&unbound or used|unbound!=set(references):raise ValueError('Stock profile reference set differs from signed graph and explicit unbound set')


def verify_stock_templates(images,templates,profile,avbtool,avb,root_pin):
 """Verify signed templates and every unchanged reference, excluding only 3 replacements."""
 validate_stock_profile(profile)
 for part,item in dict(profile['templates'],**profile['references']).items():
  path=strict_file(images[part])
  if path.stat().st_size!=item['bytes'] or PROFILE.digest(path)!=item['sha256']:raise ValueError('Stock template/reference pin mismatch')
 checked=set();active=set();leaves=set()
 def verify(part,expected=None):
  if part in active:raise ValueError('Stock AVB reference cycle')
  image=avbtool.ImageHandler(str(images[part]),read_only=True)
  try:
   footer,header,descs,_=avb._parse_image(image)
   if part in ('vbmeta','vbmeta_system') and footer is not None:raise ValueError('Stock templates must be bare vbmeta images')
   offset=footer.vbmeta_offset if footer else 0;image.seek(offset);blob=image.read(header.SIZE+header.authentication_data_block_size+header.auxiliary_data_block_size)
   start=header.SIZE+header.authentication_data_block_size+header.public_key_offset;public=blob[start:start+header.public_key_size]
   if header.flags or header.public_key_metadata_size or header.algorithm_type==0 or not avbtool.verify_vbmeta_signature(header,blob):raise ValueError('Invalid stock template/chain signature or flags')
   if expected is not None and public!=expected:raise ValueError('Stock parent/child key mismatch')
   if part=='vbmeta' and hashlib.sha256(public).hexdigest()!=root_pin:raise ValueError('Stock root key pin mismatch')
   if part in checked:return
   active.add(part)
   for descriptor in descs:
    if isinstance(descriptor,avbtool.AvbChainPartitionDescriptor):verify(descriptor.partition_name,descriptor.public_key)
    elif isinstance(descriptor,(avbtool.AvbHashDescriptor,avbtool.AvbHashtreeDescriptor)):
     if descriptor.partition_name in PARTS:continue
     if not descriptor.verify(str(images[descriptor.partition_name].parent),'.img',{},image,False):raise ValueError('Stock unchanged reference descriptor verification failed')
     leaves.add(descriptor.partition_name)
    elif not isinstance(descriptor,avbtool.AvbPropertyDescriptor):raise ValueError('Unsupported stock template descriptor')
   active.remove(part);checked.add(part)
  finally:image._image.close()
 verify('vbmeta')
 used=(checked|leaves)-{'vbmeta','vbmeta_system'}
 unbound=set(profile['unbound_references'])
 validate_reference_coverage(used,profile['references'],unbound)
 return {'template_signatures_verified':True,'parent_child_public_keys_match':True,'unchanged_reference_descriptors_verified':True,'avb_covered_references':sorted(used),'pinned_but_not_avb_covered_references':sorted(unbound),'full_reference_file_pins_verified':sorted(profile['references']),'operator_root_key_pin_checked':True,'replaced_baseline_leaf_bytes_verified':False,'hardware_root_trust_verified':False,'nodes':sorted(checked)}


def recovery_hash_for_root(avbtool, root_descriptors, stock, recovery, recovery_pin):
 """Check a locally reconstructed Recovery leaf before using its root binding."""
 PROFILE.sha256_value(recovery_pin)
 if recovery.stat().st_size != stock.stat().st_size or PROFILE.digest(recovery) != recovery_pin:
  raise ValueError('LCARS vendor_boot differs from the caller pin or stock partition size')
 root_hashes = [desc for desc in root_descriptors
                if isinstance(desc, avbtool.AvbHashDescriptor) and desc.partition_name == 'vendor_boot']
 if len(root_hashes) != 1:
  raise ValueError('Expected one root vendor_boot hash binding')

 avb = avbtool.Avb()

 def leaf(path):
  image = avbtool.ImageHandler(str(path), read_only=True)
  try:
   footer, header, descriptors, _ = avb._parse_image(image)
  finally:
   image._image.close()
  hashes = [desc for desc in descriptors if isinstance(desc, avbtool.AvbHashDescriptor)]
  if (footer is None or header.algorithm_type or header.flags or header.public_key_metadata_size or
      len(hashes) != 1 or hashes[0].partition_name != 'vendor_boot' or
      not 0 < footer.original_image_size == hashes[0].image_size <= footer.vbmeta_offset < path.stat().st_size or
      any(not isinstance(desc, avbtool.AvbPropertyDescriptor)
          for desc in descriptors if desc is not hashes[0])):
   raise ValueError('Unexpected vendor_boot footer, hash descriptor or security flags')
  properties = [desc.encode() for desc in descriptors if desc is not hashes[0]]
  security = (header.rollback_index, header.rollback_index_location, header.release_string,
              header.required_libavb_version_major, header.required_libavb_version_minor)
  return hashes[0], properties, security

 old_hash, old_props, old_security = leaf(stock)
 new_hash, new_props, new_security = leaf(recovery)
 if old_hash.encode() != root_hashes[0].encode():
  raise ValueError('Stock vendor_boot footer differs from the root hash binding')
 if old_props != new_props or old_security != new_security:
  raise ValueError('LCARS vendor_boot changed stock AVB properties or rollback policy')
 if (new_hash.hash_algorithm not in ('sha256', 'sha512') or not new_hash.digest or
     new_hash.digest == old_hash.digest or
     (new_hash.hash_algorithm, new_hash.salt, new_hash.flags) !=
     (old_hash.hash_algorithm, old_hash.salt, old_hash.flags)):
  raise ValueError('LCARS vendor_boot differs from the stock hash policy or repeats the stock digest')
 payload = hashlib.new(new_hash.hash_algorithm, new_hash.salt)
 with recovery.open('rb') as stream:
  remaining = new_hash.image_size
  while remaining:
   data = stream.read(min(remaining, 1048576))
   if not data:
    raise ValueError('Unexpected EOF while checking LCARS vendor_boot payload hash')
   payload.update(data)
   remaining -= len(data)
 if payload.digest() != new_hash.digest:
  raise ValueError('LCARS vendor_boot payload hash differs from its footer')
 return new_hash


def assemble(args):
 for pin in [args.baseline_root_sha256,args.output_root_sha256,args.avbtool_source_sha256]:PROFILE.sha256_value(pin)
 stock_mode=getattr(args,'stock_templates',None) is not None
 recovery_path=getattr(args,'lcars_vendor_boot',None)
 recovery_pin=getattr(args,'lcars_vendor_boot_sha256',None)
 if (recovery_path is None) != (recovery_pin is None) or (recovery_path is not None and not stock_mode):
  raise ValueError('LCARS vendor_boot and its SHA256 pin are both required in stock-template mode')
 if recovery_path is not None:
  recovery_path=strict_file(recovery_path)
 policy_path=getattr(args,'userspace_policy',None);policy_pin=getattr(args,'userspace_policy_sha256',None)
 if bool(policy_path)!=bool(policy_pin):raise ValueError('Userspace policy and SHA256 pin are both required')
 if stock_mode and not policy_path:raise ValueError('Stock-template mode requires explicit dynamic userspace policy')
 policy=None
 if policy_path:
  policy=C.pinned_json(strict_file(policy_path),policy_pin)
  if not isinstance(policy,dict) or type(policy.get('format')) is not int or policy!=PROPERTY_POLICY:raise ValueError('Unsupported dynamic userspace property policy')
 stock_profile=None
 if stock_mode:
  if not getattr(args,'stock_profile',None) or not getattr(args,'stock_profile_sha256',None):raise ValueError('Stock profile and SHA256 pin required')
  stock_profile=C.pinned_json(strict_file(args.stock_profile),args.stock_profile_sha256);validate_stock_profile(stock_profile)
 elif getattr(args,'stock_profile',None) or getattr(args,'stock_profile_sha256',None):raise ValueError('Stock profile requires stock-template mode')
 baseline_dir=args.stock_templates if stock_mode else args.base_images
 output=C.check_output(args.output,[baseline_dir,args.payloads,args.references,args.tool_tree]+([Path(policy_path).parent] if policy_path else [])+([args.stock_profile.parent] if stock_mode else []))
 keys=[strict_file(args.root_key),strict_file(args.system_key)]
 if any(ROOT.resolve()==p or ROOT.resolve() in p.parents or output==p or output in p.parents for p in keys):raise ValueError('User keys must stay outside repository/tool bundle and output')
 source=strict_file(args.tool_tree/'external/avb/avbtool.py')
 if PROFILE.digest(source)!=args.avbtool_source_sha256:raise ValueError('AVB Python source revision/hash differs')
 avbtool=C.load_module('jarvis2_assembler_pinned_avbtool',source);avb=avbtool.Avb()
 tools=args.tool_tree/'out/host/linux-x86/bin'
 required={name:C.regular((tools/name).resolve()) for name in ['fsck.erofs','avbtool']}
 env=dict(os.environ,PATH=str(tools)+':'+os.environ['PATH'])
 images={part:strict_file(baseline_dir/(part+'.img')) for part in (('vbmeta','vbmeta_system') if stock_mode else (*PARTS,'vbmeta','vbmeta_system'))}
 if stock_mode:
  for part in stock_profile['references']:images[part]=strict_file(args.references/(part+'.img'))
  for part,item in dict(stock_profile['templates'],**stock_profile['references']).items():
   if images[part].stat().st_size!=item['bytes'] or PROFILE.digest(images[part])!=item['sha256']:raise ValueError('Stock template/reference does not match pinned profile')
 payloads={part:strict_file(args.payloads/(part+'.img')) for part in PARTS}
 baseline_hashes={part:PROFILE.digest(path) for part,path in images.items()}
 payload_hashes={part:PROFILE.digest(path) for part,path in payloads.items()}
 payload_geometry={part:validate_raw(path) for part,path in payloads.items()}
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
 seen=set();active=set();reference_hashes={part:baseline_hashes[part] for part in stock_profile['references']} if stock_mode else {}
 def collect(part):
  if part in active:raise ValueError('AVB reference cycle')
  if part in seen:return
  if not re.fullmatch(r'[A-Za-z0-9_]+',part):raise ValueError('Unsafe AVB reference name')
  if part not in images:
   images[part]=strict_file(args.references/(part+'.img'));reference_hashes[part]=PROFILE.digest(images[part])
  active.add(part);_,header,descs,_=parse(images[part]);header_policy(header)
  for descriptor in descs:
   if isinstance(descriptor,(avbtool.AvbChainPartitionDescriptor,avbtool.AvbHashDescriptor,avbtool.AvbHashtreeDescriptor)):
    name=descriptor.partition_name
    if not re.fullmatch(r'[A-Za-z0-9_]+',name):raise ValueError('Unsafe AVB leaf name')
    if stock_mode and name in PARTS:continue
    if name not in images:
     if stock_mode:raise ValueError('Signed graph references an unlisted stock input')
     images[name]=strict_file(args.references/(name+'.img'));reference_hashes[name]=PROFILE.digest(images[name])
    if isinstance(descriptor,avbtool.AvbChainPartitionDescriptor):collect(name)
   elif not isinstance(descriptor,(avbtool.AvbPropertyDescriptor,avbtool.AvbKernelCmdlineDescriptor)):
    raise ValueError('Unsupported AVB descriptor type')
  named=[d.partition_name for d in descs if isinstance(d,(avbtool.AvbChainPartitionDescriptor,avbtool.AvbHashDescriptor,avbtool.AvbHashtreeDescriptor))]
  if len(named)!=len(set(named)):raise ValueError('Duplicate named AVB descriptor')
  for d in descs:
   if getattr(d,'partition_name',None) in PARTS and (part not in ('vbmeta','vbmeta_system') or not isinstance(d,avbtool.AvbHashtreeDescriptor)):raise ValueError('Ambiguous changed-image descriptor role')
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
 for part in (() if stock_mode else PARTS):
  footer,header,descs,_=parse(images[part]);trees=[d for d in descs if isinstance(d,avbtool.AvbHashtreeDescriptor)]
  if header.algorithm_type!=0 or header.rollback_index_location or header.flags or len(trees)!=1 or trees[0].partition_name!=part or trees[0].flags or trees[0].hash_algorithm not in ('sha256','sha512') or any(not isinstance(d,(avbtool.AvbHashtreeDescriptor,avbtool.AvbPropertyDescriptor)) for d in descs):raise ValueError('Unsupported leaf AVB footer policy')
  C.require_tree_geometry(trees[0])
  if footer is None or not 0<footer.original_image_size<=trees[0].image_size<images[part].stat().st_size:raise ValueError('Missing or invalid baseline raw-image footer geometry')
  with PROFILE.ErofsMetadata(images[part]) as reader:
   if reader.geometry['filesystem_bytes']!=footer.original_image_size:raise ValueError('Baseline EROFS/footer geometry mismatch')
  leaves[part]=(header,trees[0],descs)
 if stock_mode:
  for parent,parts in expected.items():
   for part in parts:
    tree=next(d for d in templates[parent][1] if isinstance(d,avbtool.AvbHashtreeDescriptor) and d.partition_name==part);C.require_tree_geometry(tree)
    if tree.flags or tree.hash_algorithm not in ('sha256','sha512'):raise ValueError('Unsupported stock replacement hashtree policy')
    leaves[part]=(SimpleNamespace(algorithm_type=0,flags=0,rollback_index=0,rollback_index_location=0,release_string=stock_profile['leaf_release_string']),tree,[])
 recovery_hash=None
 if recovery_path is not None:
  if 'vendor_boot' not in images:
   raise ValueError('Stock profile lacks the vendor_boot reference')
  recovery_hash=recovery_hash_for_root(avbtool,templates['vbmeta'][1],
                                      images['vendor_boot'],recovery_path,recovery_pin)
 input_files=[*images.values(),*payloads.values()]
 if recovery_path is not None:
  input_files.append(recovery_path)
 distinct_files({str(i):path for i,path in enumerate(input_files)})
 output.mkdir(mode=0o700);(output/'images').mkdir();(output/'logs').mkdir()
 report={'status':'running','format':1,'mode':'stock-templates' if stock_mode else 'coherent-baseline','replaced_baseline_leaf_bytes_verified':not stock_mode,'userspace_property_policy_sha256':policy_pin,'stock_profile_sha256':getattr(args,'stock_profile_sha256',None),'device_modified':False,'hardware_root_trust_verified':False,'restore_tested':False,'ota_installer':False,'full_target_files_complete':False,'payload_content_intent_verified':False,'payload_metadata_intent_verified':False,'baseline_root_sha256':args.baseline_root_sha256,'output_root_sha256':args.output_root_sha256,'root_key_changed':args.baseline_root_sha256!=args.output_root_sha256,'baseline_image_sha256':baseline_hashes,'unchanged_reference_image_sha256':reference_hashes,'payload_image_sha256':payload_hashes,'partitions':{},'files':{},'tool_hashes':{name:PROFILE.digest(path) for name,path in dict(required,avbtool_python=source).items()},'limitations':['Caller must independently authenticate baseline, references, payloads and tools.','EROFS structure is checked; intended changed content and metadata are caller responsibilities.','Output root pin is not hardware trust, OTA or installation qualification.']}
 if recovery_path is not None:
  report['unchanged_reference_image_sha256']={name:sha for name,sha in reference_hashes.items() if name!='vendor_boot'}
  report['lcars_vendor_boot']={'bytes':recovery_path.stat().st_size,'sha256':recovery_pin,
                              'stock_sha256':reference_hashes['vendor_boot']}
 redactions={str(keys[0]):'<user-root-key>',str(keys[1]):'<user-system-key>'}
 def redact(text):
  for path,label in redactions.items():text=text.replace(path,label)
  return text
 def save():
  tmp=output/'result.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');tmp.replace(output/'assembly.json')
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
  report['baseline_audit']=verify_stock_templates(images,templates,stock_profile,avbtool,avb,args.baseline_root_sha256) if stock_mode else audit(baseline,output/'baseline-audit',args.baseline_root_sha256)
  values={}
  if policy:
   props={}
   for part,path in payloads.items():
    with tempfile.TemporaryDirectory(prefix='properties-',dir=output) as work:
     run([required['fsck.erofs'],'--no-preserve','--extract='+work,path],'extract-properties-'+part+'.log')
     prop_path=strict_file(Path(work)/policy['build_prop_paths'][part])
     if prop_path.stat().st_size>1048576:raise ValueError('Canonical build.prop too large')
     props[part]=parse_build_properties(prop_path.read_text(encoding='utf-8'))
   values=desired_properties(props);report['desired_userspace_properties']={key:value.decode() for key,value in values.items()}
   for part,(header,tree,descs) in leaves.items():leaves[part]=(header,tree,rewrite_properties(descs,values,{part},avbtool))
   for part,(header,descs) in templates.items():templates[part]=(header,rewrite_properties(descs,values,expected[part],avbtool))
   save()
  root_public=avbtool.RSAPublicKey(str(keys[0])).encode();child_public=avbtool.RSAPublicKey(str(keys[1])).encode()
  root_sha=hashlib.sha256(root_public).hexdigest();C.validate_root_policy(args.baseline_root_sha256,root_sha,args.output_root_sha256,args.allow_root_key_change)
  report['system_public_key_sha256']=hashlib.sha256(child_public).hexdigest();save()
  for part in PARTS:
   target=output/'images'/(part+'.img');shutil.copyfile(payloads[part],target)
   run([required['fsck.erofs'],target],'fsck-'+part+'.log')
   raw_bytes=target.stat().st_size;raw_sha=PROFILE.digest(target);header,tree,descs=leaves[part];budget=stock_profile['output_bytes'][part] if stock_mode else images[part].stat().st_size
   run(footer_command(required['avbtool'],target,part,budget,header,tree,descs,avbtool),'footer-'+part+'.log')
   if C.prefix_digest(target,raw_bytes)!=raw_sha or target.stat().st_size!=budget:raise ValueError('AVB append changed payload bytes or exact image size')
   _,new_header,new_descs,_=parse(target)
   if (new_header.flags,new_header.rollback_index,new_header.rollback_index_location,new_header.release_string)!=(header.flags,header.rollback_index,header.rollback_index_location,header.release_string):raise ValueError('Leaf rollback/verification flags changed')
   if [d.encode() for d in descs if isinstance(d,avbtool.AvbPropertyDescriptor)]!=[d.encode() for d in new_descs if isinstance(d,avbtool.AvbPropertyDescriptor)]:raise ValueError('Leaf AVB properties changed')
   new_trees=[d for d in new_descs if isinstance(d,avbtool.AvbHashtreeDescriptor)]
   if len(new_trees)!=1:raise ValueError('Unexpected new hashtree count')
   new_tree=new_trees[0];C.require_tree_geometry(new_tree)
   fields=['salt','hash_algorithm','flags','fec_num_roots','data_block_size','hash_block_size','dm_verity_version','partition_name']
   if any(getattr(new_tree,key)!=getattr(tree,key) for key in fields):raise ValueError('Leaf AVB policy changed')
   report['partitions'][part]={'raw_bytes':raw_bytes,'raw_sha256':raw_sha,'erofs_geometry':payload_geometry[part],'exact_prefix_verified':True,'partition_bytes':budget};save()
  for part,changed,key in [('vbmeta_system',{'system','system_ext'},keys[1]),('vbmeta',{'product'},keys[0])]:
   header,descs=templates[part];new=[]
   for descriptor in descs:
    value=copy.deepcopy(descriptor)
    if isinstance(value,avbtool.AvbHashtreeDescriptor) and value.partition_name in changed:value=next(d for d in parse(output/'images'/(value.partition_name+'.img'))[2] if isinstance(d,avbtool.AvbHashtreeDescriptor))
    if (part=='vbmeta' and recovery_hash is not None and
        isinstance(value,avbtool.AvbHashDescriptor) and value.partition_name=='vendor_boot'):
     value=recovery_hash
    if part=='vbmeta' and isinstance(value,avbtool.AvbChainPartitionDescriptor) and value.partition_name=='vbmeta_system':value.public_key=child_public
    new.append(value)
   blob=avb._generate_vbmeta_blob(algorithm_name=algorithm(header),key_path=str(key),public_key_metadata_path=None,descriptors=new,chain_partitions_use_ab=None,chain_partitions_do_not_use_ab=None,rollback_index=header.rollback_index,flags=header.flags,rollback_index_location=header.rollback_index_location,props=None,props_from_file=None,kernel_cmdlines=None,setup_rootfs_from_kernel=None,ht_desc_to_setup=None,include_descriptors_from_image=None,signing_helper=None,signing_helper_with_files=None,release_string=header.release_string,append_to_release_string=None,required_libavb_version_minor=header.required_libavb_version_minor)
   size=stock_profile['output_bytes'][part] if stock_mode else images[part].stat().st_size
   if len(blob)>size:raise ValueError('Signed vbmeta exceeds baseline physical size')
   target=output/'images'/(part+'.img');target.write_bytes(blob+b'\0'*(size-len(blob)));_,actual,actual_descs,_=parse(target)
   if (actual.flags,actual.rollback_index,actual.rollback_index_location,actual.algorithm_type,actual.required_libavb_version_minor,actual.release_string)!=(header.flags,header.rollback_index,header.rollback_index_location,header.algorithm_type,header.required_libavb_version_minor,header.release_string) or [d.encode() for d in actual_descs]!=[d.encode() for d in new]:raise ValueError('Signed descriptor/rollback/flag preservation failed')
  final=output/'final-reference-tree';final.mkdir()
  final_images={**images,**{part:output/'images'/(part+'.img') for part in (*PARTS,'vbmeta','vbmeta_system')}}
  if recovery_path is not None:
   final_images['vendor_boot']=recovery_path
  for part,path in final_images.items():(final/(part+'.img')).symlink_to(path)
  report['final_audit']=audit(final,output/'final-audit',args.output_root_sha256)
  C.verify_input_hashes(images,dict(baseline_hashes,**reference_hashes))
  C.verify_input_hashes(payloads,payload_hashes)
  if recovery_path is not None:
   C.verify_input_hashes({'vendor_boot':recovery_path},{'vendor_boot':recovery_pin})
  if policy_path:C.pinned_json(strict_file(policy_path),policy_pin)
  if stock_mode:C.pinned_json(strict_file(args.stock_profile),args.stock_profile_sha256)
  report['files']={p.name:{'bytes':p.stat().st_size,'sha256':PROFILE.digest(p)} for p in sorted((output/'images').glob('*.img'))};report['status']='passed';save();return report
 except BaseException as error:
  report.update(status='failed',error=redact(str(error)),traceback=redact(traceback.format_exc()));save();raise RuntimeError(report['error']) from None


def main():
 os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
 group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--base-images',type=Path);group.add_argument('--stock-templates',type=Path)
 for flag in ['payloads','references','tool-tree','root-key','system-key','output']:parser.add_argument('--'+flag,type=Path,required=True)
 for flag in ['baseline-root-sha256','output-root-sha256','avbtool-source-sha256']:parser.add_argument('--'+flag,required=True)
 for flag in ['stock-profile','userspace-policy','lcars-vendor-boot']:parser.add_argument('--'+flag,type=Path)
 for flag in ['stock-profile-sha256','userspace-policy-sha256','lcars-vendor-boot-sha256']:parser.add_argument('--'+flag)
 parser.add_argument('--allow-root-key-change',action='store_true');args=parser.parse_args();result=assemble(args);print(json.dumps({'status':result['status'],'files':result['files'],'hardware_root_trust_verified':False},indent=2))

if __name__=='__main__':main()
