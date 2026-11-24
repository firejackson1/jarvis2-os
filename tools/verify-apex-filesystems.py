#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compare supported ext4 APEX filesystems using caller-supplied AOSP debugfs.

No signing, private-key reads or device operations. Match the exact archives to a
prior package-verification report. A trusted report SHA256 pin is required to
inherit its caller-pinned public-key trust statement; otherwise the scope is
internal consistency only. Run with external 1GiB RAM/3GiB swap/one-CPU
limits. Timestamps, inode flags/layout and hardlink topology remain unverified.
"""
import argparse,hashlib,importlib.util,io,json,os,re,stat,struct,subprocess,tempfile,time,traceback,zipfile
from pathlib import Path


_PACKAGE_SPEC=importlib.util.spec_from_file_location('jarvis2_public_packages',Path(__file__).with_name('verify-signed-packages.py'))
_PACKAGES=importlib.util.module_from_spec(_PACKAGE_SPEC)
_PACKAGE_SPEC.loader.exec_module(_PACKAGES)

def validate_package_proof(data,trusted_sha256=None):
 if trusted_sha256 is not None and (not re.fullmatch(r'[0-9a-fA-F]{64}',trusted_sha256) or hashlib.sha256(data).hexdigest()!=trusted_sha256.lower()):
  raise ValueError('Trusted package-proof SHA256 pin mismatch or malformed pin')
 proof=_PACKAGES.load_json_unique(data)
 if not isinstance(proof,dict) or proof.get('status')!='passed' or not isinstance(proof.get('archive_sha256'),dict) or set(proof['archive_sha256'])!={'original','signed'} or not isinstance(proof.get('embedded_apks'),list):
  raise ValueError('Malformed or unsuccessful prior package proof')
 for digest in proof['archive_sha256'].values():
  if not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{64}',digest):raise ValueError('Malformed prior archive digest')
 paths=set()
 for item in proof['embedded_apks']:
  if not isinstance(item,dict) or not isinstance(item.get('path'),str) or item['path'] in paths or item.get('signature_verified') is not True or item.get('nonsignature_entry_content_unchanged') is not True:
   raise ValueError('Malformed or duplicate embedded APK proof')
  paths.add(item['path'])
  for field in ('sha256','expected_certificate_sha256'):
   if item.get(field) is None and field=='expected_certificate_sha256':continue
   if not isinstance(item.get(field),str) or not re.fullmatch(r'[0-9a-f]{64}',item[field]):raise ValueError('Malformed embedded APK digest')
 trust={'mode':'internal-consistency-only','caller_inventory_pin_verified':False,'prior_package_report_pin_verified':trusted_sha256 is not None,'hardware_root_of_trust_verified':False}
 claimed=proof.get('public_inventory_trust',{})
 if trusted_sha256 is not None and isinstance(claimed,dict) and claimed.get('mode')=='caller-pinned-public-inventory' and claimed.get('caller_inventory_pin_verified') is True:
  if not isinstance(claimed.get('inventory_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',claimed['inventory_sha256']):raise ValueError('Malformed prior inventory anchor')
  trust.update(mode=claimed['mode'],caller_inventory_pin_verified=True,inventory_sha256=claimed['inventory_sha256'])
 return proof,trust

def sha_file(path):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):raise ValueError('Expected regular file')
  return hashlib.file_digest(f,'sha256').hexdigest()

def parse_ls(text,parent):
 entries={}
 for line in text.splitlines():
  if not line:continue
  fields=line.split('/')
  if len(fields)!=8 or fields[0] or fields[-1]:raise ValueError('Unexpected native ls format')
  _,inode,mode,uid,gid,name,size,_=fields
  # Native ext4 ls exposes unused all-zero directory slots, not paths.
  if line=='/0/000000/0/0//0/':continue
  if not all(re.fullmatch(r'[0-9]+',v) for v in [inode,uid,gid]) or not re.fullmatch(r'[0-7]+',mode):raise ValueError('Malformed native inode metadata')
  if int(inode)==0:raise ValueError('Inconsistent unused directory slot')
  if name=='..':continue
  if name=='.':
   if parent!='.':continue
   path='.'
  else:
   if not name or name in ('.','..') or '\\' in name or any(ord(c)<32 for c in name):raise ValueError('Unsafe inode name')
   path=name if parent=='.' else parent+'/'+name
  if path in entries:raise ValueError('Duplicate native path')
  bits=int(mode,8);kind={stat.S_IFDIR:'directory',stat.S_IFREG:'file',stat.S_IFLNK:'symlink'}.get(stat.S_IFMT(bits))
  if kind is None:raise ValueError('Unsupported native inode type')
  if kind!='directory' and not re.fullmatch(r'[0-9]+',size):raise ValueError('Malformed inode size')
  entries[path]={'inode':int(inode),'type':kind,'mode':stat.S_IMODE(bits),'uid':int(uid),'gid':int(gid),'size':int(size) if size else None}
 return entries

def walk_extracted(root):
 result={};pending=[root]
 while pending:
  directory=pending.pop()
  for entry in os.scandir(directory):
   path=Path(entry.path);relative=path.relative_to(root).as_posix();info=entry.stat(follow_symlinks=False)
   if stat.S_ISLNK(info.st_mode):result[relative]={'type':'symlink','link_target':os.readlink(path)}
   elif stat.S_ISDIR(info.st_mode):result[relative]={'type':'directory'};pending.append(path)
   elif stat.S_ISREG(info.st_mode):result[relative]={'type':'file','sha256':sha_file(path),'size':info.st_size}
   else:raise ValueError('Unsupported extracted inode type')
 result['.']={'type':'directory'}
 return result


def main():
 os.umask(0o077)
 parser=argparse.ArgumentParser(description=__doc__)
 for flag in ['original','signed','package-proof','debugfs','report-dir']:parser.add_argument('--'+flag,type=Path,required=True)
 parser.add_argument('--trusted-package-proof-sha256')
 args=parser.parse_args();args.report_dir.mkdir(mode=0o700,exist_ok=False)
 for name in ['tmp','logs','snapshots']:(args.report_dir/name).mkdir(mode=0o700)
 env=dict(os.environ,TMPDIR=str(args.report_dir/'tmp'))
 report={'status':'running','scope':'All 31 original/signed ext4 APEX filesystem paths,regular bytes,linktargets,modes,UID/GID and raw extended attributes; only 21 prior-verified embedded APK byte changes allowed.','apexes':[],'symlinks_followed':False,'authoritative_metadata_source':'Pinned debugfs ls -l -p and ea_list/ea_get by inode on raw payload images, independent of host extraction ownership/xattrs.','unverified_metadata':['timestamps (atime/mtime/ctime/crtime)','inode numbers/generation/layout/block placement and hardlink topology','directory byte encoding/allocated size and filesystem superblock UUID/features','inode flags/project identifiers; not asserted unchanged'],'limitations':['Does not establish final ROM raw-image AVB, hardware acceptance, installation, rollback or OTA completeness.','Bounded known-artifact verifier; not a universal untrusted-archive schema suite.']}
 def save():
  temp=args.report_dir/'report.tmp';temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(args.report_dir/'report.json')
 def run(command,label):
  r=subprocess.run([str(x) for x in command],capture_output=True,text=True,env=env)
  (args.report_dir/'logs'/label).write_text(r.stdout+r.stderr)
  errors=[line for line in r.stderr.splitlines() if line and not re.fullmatch(r'debugfs [0-9].*',line)]
  if r.returncode or errors:raise RuntimeError('Native filesystem read error; '+label+': '+r.stderr[-500:])
  return r.stdout
 def payload(archive,name,dest):
  data=archive.read(name)
  if name.endswith('.capex'):
   with zipfile.ZipFile(io.BytesIO(data)) as z:data=z.read('original_apex')
  with zipfile.ZipFile(io.BytesIO(data)) as z,dest.open('wb') as writer,z.open('apex_payload.img') as reader:
   while chunk:=reader.read(1048576):writer.write(chunk)
  with dest.open('rb') as f:f.seek(1080);magic=f.read(2)
  if magic!=b'\x53\xef':raise ValueError('Only the inspected ext4 payload format is supported')
 def snapshot(image,folder,label):
  entries={};pending=[('.',2)];visited=set()
  while pending:
   parent,inode=pending.pop()
   if inode in visited:raise ValueError('Directory inode cycle/alias')
   visited.add(inode)
   found=parse_ls(run([args.debugfs,'-R','ls -l -p <'+str(inode)+'>',image],label+'-ls-'+str(inode)+'.txt'),parent)
   for path,item in found.items():
    if path in entries:raise ValueError('Duplicate payload path')
    entries[path]=item
    if item['type']=='directory' and path!=parent:pending.append((path,item['inode']))
  if '.' not in entries:raise ValueError('Missing root inode')
  inode_paths={}
  for path,item in entries.items():inode_paths.setdefault(item['inode'],[]).append(path)
  command_file=folder/'list-xattrs.txt';command_file.write_text(''.join('ea_list <'+str(i)+'>\n' for i in sorted(inode_paths)))
  text=run([args.debugfs,'-f',command_file,image],label+'-xattrs-list.txt')
  attrs={};current=None
  for line in text.splitlines():
   marker=re.fullmatch(r'debugfs: ea_list <([0-9]+)>',line)
   if marker:
    current=int(marker[1])
    if current in attrs:raise ValueError('Duplicate xattr command output')
    attrs[current]={};continue
   if not line or line=='Extended attributes:':continue
   match=re.fullmatch(r'  ([A-Za-z0-9_.-]+) \(([0-9]+)\)(?: =.*)?',line)
   if not match or current is None or match[1] in attrs[current]:raise ValueError('Unexpected native xattr listing')
   attrs[current][match[1]]=int(match[2])
  if set(attrs)!=set(inode_paths):raise ValueError('Missing authoritative xattr results')
  xattr_dir=folder/'xattrs';xattr_dir.mkdir();commands=[];outputs=[]
  for inode,values in sorted(attrs.items()):
   for index,(name,size) in enumerate(sorted(values.items())):
    output=xattr_dir/(str(inode)+'-'+str(index));commands.append('ea_get -f '+str(output)+' <'+str(inode)+'> '+name+'\n');outputs.append((inode,name,size,output))
  if commands:
   command_file=folder/'get-xattrs.txt';command_file.write_text(''.join(commands));run([args.debugfs,'-f',command_file,image],label+'-xattrs-get.txt')
  for item in entries.values():item['xattrs']={}
  for inode,name,size,path in outputs:
   data=path.read_bytes()
   if len(data)!=size:raise ValueError('Missing/truncated native xattr value')
   for target in inode_paths[inode]:entries[target]['xattrs'][name]={'bytes':size,'sha256':hashlib.sha256(data).hexdigest()}
  tree=folder/'tree';tree.mkdir()
  run([args.debugfs,'-R','rdump ./ '+str(tree),image],label+'-rdump.txt')
  extracted=walk_extracted(tree)
  if set(extracted)!=set(entries):raise ValueError('Extracted/native exact path sets differ')
  for path,item in entries.items():
   actual=extracted[path]
   if item['type']!=actual['type']:raise ValueError('Extracted/native inode types differ')
   if item['type']=='file' and item['size']!=actual['size']:raise ValueError('Extracted/native regular file sizes differ')
   if item['type']=='symlink' and len(os.fsencode(actual['link_target']))!=item['size']:raise ValueError('Extracted/native symlink size differs')
   item.update({key:value for key,value in actual.items() if key not in ('type','size')})
  return entries
 try:
  save();proof,trust=validate_package_proof(args.package_proof.read_bytes(),args.trusted_package_proof_sha256)
  report['public_inventory_trust']=trust
  hashes={'original':sha_file(args.original),'signed':sha_file(args.signed)}
  if hashes!=proof['archive_sha256']:raise ValueError('Package proof is for different archives')
  report['archive_sha256']=hashes;report['prior_package_proof_sha256']=sha_file(args.package_proof);report['debugfs_sha256']=sha_file(args.debugfs)
  embedded={item['path']:item for item in proof['embedded_apks']}
  with zipfile.ZipFile(args.original) as original,zipfile.ZipFile(args.signed) as signed:
   names=sorted(n for n in original.namelist() if n.endswith(('.apex','.capex')))
   if names!=sorted(n for n in signed.namelist() if n.endswith(('.apex','.capex'))):raise ValueError('APEX entry identities differ')
   for name in names:
    identity=Path(name).name;differences=[];allowed=[]
    with tempfile.TemporaryDirectory(dir=args.report_dir/'tmp') as temp:
     folder=Path(temp);old_dir=folder/'original';new_dir=folder/'signed';old_dir.mkdir();new_dir.mkdir()
     old_image=old_dir/'payload.img';new_image=new_dir/'payload.img';payload(original,name,old_image);payload(signed,name,new_image)
     old=snapshot(old_image,old_dir,identity+'-original');new=snapshot(new_image,new_dir,identity+'-signed')
     for kind,contents in [('original',old),('signed',new)]:(args.report_dir/'snapshots'/(identity+'-'+kind+'.json')).write_text(json.dumps(contents,indent=2)+'\n')
     if set(old)!=set(new):differences.append({'kind':'path_set','removed':sorted(set(old)-set(new)),'added':sorted(set(new)-set(old))})
     for path in sorted(set(old)&set(new)):
      before,after=old[path],new[path]
      for field in ['type','mode','uid','gid','xattrs']:
       if before[field]!=after[field]:differences.append({'path':path,'field':field,'original':before[field],'signed':after[field]})
      if before['type']=='symlink' and after['type']=='symlink' and before['link_target']!=after['link_target']:differences.append({'path':path,'field':'link_target','original':before['link_target'],'signed':after['link_target']})
      if before['type']=='file' and after['type']=='file' and before['sha256']!=after['sha256']:
       prior=embedded.get(name+'!/'+path)
       if not prior or prior.get('preserved_in_shim') or prior.get('expected_certificate_sha256') is None or prior['sha256']!=after['sha256'] or not prior['nonsignature_entry_content_unchanged']:
        differences.append({'path':path,'field':'file_bytes','original':before['sha256'],'signed':after['sha256']})
       else:allowed.append({'path':path,'original_sha256':before['sha256'],'signed_sha256':after['sha256'],'prior_intended_certificate_sha256':prior['expected_certificate_sha256']})
     result={'path':name,'native_path_count':len(old),'regular_files':sum(x['type']=='file' for x in old.values()),'symlinks':sum(x['type']=='symlink' for x in old.values()),'native_xattr_count':sum(len(x['xattrs']) for x in old.values()),'selinux_labeled_paths':sum('security.selinux' in x['xattrs'] for x in old.values()),'allowed_embedded_apk_byte_changes':allowed,'differences':differences,'passed':not differences}
     report['apexes'].append(result);save();print(identity+': '+('PASS' if not differences else 'DIFFERENCES')+' paths='+str(len(old))+' allowedAPKchanges='+str(len(allowed))+' unexpected='+str(len(differences)),flush=True)
  report['counts']={'apexes':len(report['apexes']),'paths':sum(x['native_path_count'] for x in report['apexes']),'regular_files':sum(x['regular_files'] for x in report['apexes']),'symlinks':sum(x['symlinks'] for x in report['apexes']),'native_xattrs':sum(x['native_xattr_count'] for x in report['apexes']),'selinux_labeled_paths':sum(x['selinux_labeled_paths'] for x in report['apexes']),'allowed_apk_changes':sum(len(x['allowed_embedded_apk_byte_changes']) for x in report['apexes']),'unexpected_differences':sum(len(x['differences']) for x in report['apexes'])}
  if report['counts']['apexes']!=31 or report['counts']['allowed_apk_changes']!=21:raise ValueError('Unexpected APEX/allowed APK change inventory')
  report['status']='passed' if not report['counts']['unexpected_differences'] else 'failed';save();print(json.dumps(report['counts']),flush=True)
  return 0 if report['status']=='passed' else 1
 except BaseException as error:
  report.update(status='failed',error=str(error),traceback=traceback.format_exc());save();raise

if __name__=='__main__':raise SystemExit(main())
