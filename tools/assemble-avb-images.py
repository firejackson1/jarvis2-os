#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assemble three caller-verified raw EROFS payloads into a pinned AVB baseline.

Offline only: no filesystem rebuild, install, slots or device access. Authenticate
baseline, references, new payloads and tools independently. Root pins do not
prove hardware acceptance. Payload content/metadata intent is NOT verified.
Requires companion composer/auditor helpers; only explicitly supplied user keys.
"""
import argparse,copy,hashlib,importlib.util,json,os,re,shutil,struct,subprocess,sys,traceback
from pathlib import Path
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


def assemble(args):
 for pin in [args.baseline_root_sha256,args.output_root_sha256,args.avbtool_source_sha256]:PROFILE.sha256_value(pin)
 output=C.check_output(args.output,[args.base_images,args.payloads,args.references,args.tool_tree])
 keys=[strict_file(args.root_key),strict_file(args.system_key)]
 if any(ROOT.resolve()==p or ROOT.resolve() in p.parents or output==p or output in p.parents for p in keys):raise ValueError('User keys must stay outside repository/tool bundle and output')
 source=strict_file(args.tool_tree/'external/avb/avbtool.py')
 if PROFILE.digest(source)!=args.avbtool_source_sha256:raise ValueError('AVB Python source revision/hash differs')
 avbtool=C.load_module('jarvis2_assembler_pinned_avbtool',source);avb=avbtool.Avb()
 tools=args.tool_tree/'out/host/linux-x86/bin'
 required={name:C.regular((tools/name).resolve()) for name in ['fsck.erofs','avbtool']}
 env=dict(os.environ,PATH=str(tools)+':'+os.environ['PATH'])
 images={part:strict_file(args.base_images/(part+'.img')) for part in (*PARTS,'vbmeta','vbmeta_system')}
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
 seen=set();active=set();reference_hashes={}
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
    if name not in images:images[name]=strict_file(args.references/(name+'.img'));reference_hashes[name]=PROFILE.digest(images[name])
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
 for part in PARTS:
  footer,header,descs,_=parse(images[part]);trees=[d for d in descs if isinstance(d,avbtool.AvbHashtreeDescriptor)]
  if header.algorithm_type!=0 or header.rollback_index_location or header.flags or len(trees)!=1 or trees[0].partition_name!=part or trees[0].flags or trees[0].hash_algorithm not in ('sha256','sha512') or any(not isinstance(d,(avbtool.AvbHashtreeDescriptor,avbtool.AvbPropertyDescriptor)) for d in descs):raise ValueError('Unsupported leaf AVB footer policy')
  C.require_tree_geometry(trees[0])
  if footer is None or not 0<footer.original_image_size<=trees[0].image_size<images[part].stat().st_size:raise ValueError('Missing or invalid baseline raw-image footer geometry')
  with PROFILE.ErofsMetadata(images[part]) as reader:
   if reader.geometry['filesystem_bytes']!=footer.original_image_size:raise ValueError('Baseline EROFS/footer geometry mismatch')
  leaves[part]=(header,trees[0],descs)
 distinct_files(dict(images,**{'payload_'+k:v for k,v in payloads.items()}))
 output.mkdir(mode=0o700);(output/'images').mkdir();(output/'logs').mkdir()
 report={'status':'running','format':1,'device_modified':False,'hardware_root_trust_verified':False,'restore_tested':False,'ota_installer':False,'full_target_files_complete':False,'payload_content_intent_verified':False,'payload_metadata_intent_verified':False,'baseline_root_sha256':args.baseline_root_sha256,'output_root_sha256':args.output_root_sha256,'root_key_changed':args.baseline_root_sha256!=args.output_root_sha256,'baseline_image_sha256':baseline_hashes,'unchanged_reference_image_sha256':reference_hashes,'payload_image_sha256':payload_hashes,'partitions':{},'files':{},'tool_hashes':{name:PROFILE.digest(path) for name,path in dict(required,avbtool_python=source).items()},'limitations':['Caller must independently authenticate baseline, references, payloads and tools.','EROFS structure is checked; intended changed content and metadata are caller responsibilities.','Output root pin is not hardware trust, OTA or installation qualification.']}
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
  report['baseline_audit']=audit(baseline,output/'baseline-audit',args.baseline_root_sha256)
  root_public=avbtool.RSAPublicKey(str(keys[0])).encode();child_public=avbtool.RSAPublicKey(str(keys[1])).encode()
  root_sha=hashlib.sha256(root_public).hexdigest();C.validate_root_policy(args.baseline_root_sha256,root_sha,args.output_root_sha256,args.allow_root_key_change)
  report['system_public_key_sha256']=hashlib.sha256(child_public).hexdigest();save()
  for part in PARTS:
   target=output/'images'/(part+'.img');shutil.copyfile(payloads[part],target)
   run([required['fsck.erofs'],target],'fsck-'+part+'.log')
   raw_bytes=target.stat().st_size;raw_sha=PROFILE.digest(target);header,tree,descs=leaves[part];budget=images[part].stat().st_size
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
  C.verify_input_hashes(images,dict(baseline_hashes,**reference_hashes))
  C.verify_input_hashes(payloads,payload_hashes)
  report['files']={p.name:{'bytes':p.stat().st_size,'sha256':PROFILE.digest(p)} for p in sorted((output/'images').glob('*.img'))};report['status']='passed';save();return report
 except BaseException as error:
  report.update(status='failed',error=redact(str(error)),traceback=redact(traceback.format_exc()));save();raise RuntimeError(report['error']) from None


def main():
 os.umask(0o077);parser=argparse.ArgumentParser(description=__doc__)
 for flag in ['base-images','payloads','references','tool-tree','root-key','system-key','output']:parser.add_argument('--'+flag,type=Path,required=True)
 for flag in ['baseline-root-sha256','output-root-sha256','avbtool-source-sha256']:parser.add_argument('--'+flag,required=True)
 parser.add_argument('--allow-root-key-change',action='store_true');args=parser.parse_args();result=assemble(args);print(json.dumps({'status':result['status'],'files':result['files'],'hardware_root_trust_verified':False},indent=2))

if __name__=='__main__':main()
