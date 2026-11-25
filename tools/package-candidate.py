#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Package an authenticated vanilla developer preview, offline only.

Caller authenticates the image proof, source revision and metadata independently.
This tool checks bytes and packaging, not AVB, Google absence, signatures, source
correspondence, hardware readiness, installation or redistribution permission.
No device access, signing or private-key input. Separate source/notice delivery
is required; no Google-containing/private composition mode is supported.
"""
import argparse,hashlib,json,os,re,stat,sys,zipfile
from pathlib import Path
IMAGE_NAMES=tuple(p+'.img' for p in ['product','system','system_ext','vbmeta','vbmeta_system'])
METADATA_NAMES=('LICENSE','README.txt',*["docs/"+p+'.md' for p in ['BUILD','KNOWN_ISSUES','LAUNCHER_SOURCE_BUILD','LICENSING','RESTORE_PLAN','SLOT_INSTALLATION','USERSPACE_NOTICES']],*["manifests/"+p for p in ['avb-stock-15640252-profile.json','avb-userspace-property-policy.json','launcher-source-bundle.json','lineage21-pinned.xml','userspace-notices.json']])
RECOVERY_PLUGIN = 'recovery/librecovery_ui_ext.so'
RECOVERY_NOTICES = 'recovery/jarvis2-lcars-arm32-notices.tar.gz'
STOCK_VENDOR_BOOT = 'c017791c8e52678595a03b902237dcb15a4e8adeb3d35fdb2232838750e4233a'
ROOT=Path(__file__).resolve().parents[1]
STAMP=(2026,11,24,0,0,0)


def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def regular(path):
 path=Path(os.path.abspath(path))
 if any(p.is_symlink() for p in [path,*path.parents]) or not path.is_file():raise ValueError('Source must be a regular file without symlink ancestry')
 return path


def inventory(directory,expected):
 directory=Path(os.path.abspath(directory))
 if any(p.is_symlink() for p in [directory,*directory.parents]) or not directory.is_dir():raise ValueError('Input directory must exist without symlink ancestry')
 files={};pending=[directory];allowed_dirs={str(Path(n).parent) for n in expected}-{'.'}
 while pending:
  with os.scandir(pending.pop()) as entries:
   for entry in entries:
    path=Path(entry.path);name=path.relative_to(directory).as_posix();mode=entry.stat(follow_symlinks=False).st_mode
    if stat.S_ISDIR(mode) and name in allowed_dirs:pending.append(path)
    elif stat.S_ISREG(mode) and name in expected:files[name]=regular(path)
    else:raise ValueError('Unknown or nonregular input: '+name)
 if set(files)!=set(expected):raise ValueError('Missing required input files')
 return files


def unique_object(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError('Duplicate JSON key')
  result[key]=value
 return result


def sha256_value(value):
 if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid SHA256')


def reviewed_recovery(proof):
 if 'recovery' not in proof:
  return None
 recovery = proof['recovery']
 hash_fields = {'plugin_sha256', 'stock_vendor_boot_sha256', 'vendor_boot_sha256'}
 required = {'source_revision', *hash_fields}
 if not isinstance(recovery, dict) or set(recovery) not in (required, required | {'notices_sha256'}):
  raise ValueError('Expected an exact Recovery source and image binding')
 revision = recovery['source_revision']
 if not isinstance(revision, str) or not re.fullmatch('[0-9a-f]{40}', revision):
  raise ValueError('Expected an exact Recovery source revision')
 for field in hash_fields:
  sha256_value(recovery[field])
 if (recovery['stock_vendor_boot_sha256'] != STOCK_VENDOR_BOOT or
     recovery['vendor_boot_sha256'] == STOCK_VENDOR_BOOT):
  raise ValueError('Unknown stock foundation or missing custom Recovery binding')
 if 'notices_sha256' in recovery:
  sha256_value(recovery['notices_sha256'])
  provenance = json.loads((ROOT / 'manifests/lcars-notice-provenance.json').read_bytes(),
                          object_pairs_hook=unique_object)
  if (recovery['plugin_sha256'] != provenance['plugin_sha256'] or
      revision != provenance['source_revisions']['jarvis2'] or
      recovery['notices_sha256'] != provenance['companion_archive']['sha256']):
   raise ValueError('Recovery notice provenance differs from the reviewed plug-in and archive')
 return recovery


def candidate_readme(revision, recovery=None, rehearsal_only=False):
 foundation = ('Five candidate images require the exact separately obtained stock foundation\n'
               'pinned in manifests. Stock bootstrap differs from custom development recovery.\n')
 if recovery:
  foundation = f'''The locally built LCARS vendor_boot must match the hash in the manifest.
Use the included Recovery plug-in, the pinned recipe and your own stock image.
Recipe at https://github.com/firejackson1/jarvis2-os/blob/{recovery['source_revision']}/docs/STOCK_LCARS.md
'''
  if 'notices_sha256' in recovery:
   foundation += f'Recovery compiler-input notices are included at {RECOVERY_NOTICES}.\n'
 rehearsal = 'OFFLINE AVB REHEARSAL. The temporary trust key is for host testing only.\n' if rehearsal_only else ''
 return f'''Jarvis2 unofficial LineageOS-based developer preview: offline candidate
Source: {revision}

{rehearsal}NOT HARDWARE QUALIFIED. No installer is included. This is not an OTA or a
complete firmware/recovery backup. Do not use a generic ZIP installer.
{foundation}No Google payload or stock firmware foundation is included. The caller must
verify the vanilla input identity and the intended image contents separately.
Hardware key acceptance, boot, migration, recovery and restore remain unverified.
Shared userdata is not isolated between slots. No installation is authorized.

Corresponding launcher source, supplemental notices and public verification
materials are separate companion assets; obtain and verify their release receipt.
This archive alone is not a complete source/notice delivery or release approval.
'''


def package(images,metadata,proof,proof_sha256,source_revision,output):
 sha256_value(proof_sha256)
 if not isinstance(source_revision,str) or not re.fullmatch('[0-9a-f]{40}',source_revision):raise ValueError('Explicit full source commit required')
 images=Path(images);metadata=Path(metadata);proof=regular(proof);output=Path(os.path.abspath(output))
 if any(p.is_symlink() for p in [output,*output.parents]):raise ValueError('Output must not traverse symlinks')
 for base in [ROOT,images.absolute(),metadata.absolute()]:
  if output==base or base in output.parents:raise ValueError('Output must be outside repository and input directories')
 if output.exists():raise FileExistsError(output)
 if proof.stat().st_size>1048576 or digest(proof)!=proof_sha256:raise ValueError('Proof SHA256 pin mismatch or proof too large')
 reviewed=json.loads(proof.read_bytes(),object_pairs_hook=unique_object)
 if not isinstance(reviewed,dict) or reviewed.get('passed') is not True or reviewed.get('google_payload_included',False) is not False or not isinstance(reviewed.get('files'),dict) or set(reviewed['files'])!=set(IMAGE_NAMES):raise ValueError('Expected successful vanilla proof with exactly five image records')
 recovery = reviewed_recovery(reviewed)
 rehearsal_only = reviewed.get('rehearsal_only', False)
 if type(rehearsal_only) is not bool:
  raise ValueError('Rehearsal flag must be a boolean')
 metadata_names = (*METADATA_NAMES, RECOVERY_PLUGIN) if recovery else METADATA_NAMES
 has_notices = recovery is not None and 'notices_sha256' in recovery
 if has_notices:
  metadata_names += (RECOVERY_NOTICES,)
 image_files=inventory(images,IMAGE_NAMES);metadata_files=inventory(metadata,metadata_names)
 if any(p.stat().st_size>8*1024*1024 for p in metadata_files.values()):raise ValueError('Metadata exceeds bounded small-file scope')
 files={**{'images/'+n:p for n,p in image_files.items()},**metadata_files}
 records={n:{'bytes':p.stat().st_size,'sha256':digest(p)} for n,p in sorted(files.items())}
 for name in image_files:
  record=reviewed['files'][name]
  if not isinstance(record,dict) or set(record)!={'bytes','sha256'} or type(record['bytes']) is not int or record['bytes']<=0:raise ValueError('Malformed image proof record')
  sha256_value(record['sha256'])
  if records['images/'+name]!=record:raise ValueError('Actual image differs from reviewed proof: '+name)
 if recovery and records[RECOVERY_PLUGIN]['sha256'] != recovery['plugin_sha256']:
  raise ValueError('Recovery plug-in differs from reviewed proof')
 if has_notices and records[RECOVERY_NOTICES]['sha256'] != recovery['notices_sha256']:
  raise ValueError('Recovery notice archive differs from reviewed proof')
 if metadata_files['README.txt'].read_text()!=candidate_readme(source_revision,recovery,rehearsal_only):raise ValueError('README must match canonical developer-preview text and source revision')
 manifest={'format':1,'kind':'unofficial-offline-developer-preview','source_revision':source_revision,'image_proof_sha256':proof_sha256,'hardware_tested':False,'installable_ota':False,'installer_included':False,'google_payload_included':False,'stock_firmware_included':False,'source_correspondence_verified':False,'companion_assets_included':False,'files':records}
 if recovery:
  manifest.update(format=3 if has_notices else 2,
                  recovery={**recovery, 'plugin_member': RECOVERY_PLUGIN})
 if recovery or rehearsal_only:
  manifest['rehearsal_only'] = rehearsal_only
 manifest_bytes=(json.dumps(manifest,indent=2)+'\n').encode();output.mkdir(mode=0o700)
 suffix = '-offline-rehearsal.zip' if rehearsal_only else '-offline-candidate.zip'
 archive=output/('jarvis2-lineage-21-UNOFFICIAL-'+source_revision[:7]+('-lcars' if recovery else '')+suffix)
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for name in sorted([*files,'manifest.json']):
   info=zipfile.ZipInfo(name,date_time=STAMP);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;info.create_system=3
   info._compresslevel=6  # ZipInfo has no public compression-level field on Python 3.11.
   with z.open(info,'w',force_zip64=True) as dst:
    if name=='manifest.json':dst.write(manifest_bytes)
    else:
     with files[name].open('rb') as src:
      for chunk in iter(lambda:src.read(1048576),b''):dst.write(chunk)
 with zipfile.ZipFile(archive) as z:
  if z.namelist()!=sorted([*files,'manifest.json']) or z.read('manifest.json')!=manifest_bytes:raise ValueError('ZIP entry/manifest readback mismatch')
  for name,record in records.items():
   h=hashlib.sha256();length=0
   with z.open(name) as src:
    for chunk in iter(lambda:src.read(1048576),b''):h.update(chunk);length+=len(chunk)
   if length!=record['bytes'] or h.hexdigest()!=record['sha256']:raise ValueError('ZIP member differs from reviewed input: '+name)
 for name,path in files.items():
  if path.stat().st_size!=records[name]['bytes'] or digest(regular(path))!=records[name]['sha256']:raise ValueError('Input changed during packaging')
 if digest(regular(proof))!=proof_sha256:raise ValueError('Proof changed during packaging')
 receipt={'passed':True,'archive':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive),'all_members_read_back':True,'source_revision':source_revision,'image_proof_sha256':proof_sha256,'hardware_tested':False,'public_release_ready':False,'companion_assets_included':False,'python_version':sys.version.split()[0],'zlib_version':zipfile.zlib.ZLIB_VERSION,'zlib_runtime_version':zipfile.zlib.ZLIB_RUNTIME_VERSION}
 if recovery or rehearsal_only:
  receipt['rehearsal_only'] = rehearsal_only
 if has_notices:
  receipt['recovery_notices_sha256'] = recovery['notices_sha256']
 (output/'manifest.json').write_bytes(manifest_bytes);(output/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
 os.umask(0o077);p=argparse.ArgumentParser(description=__doc__)
 for flag in ['images','metadata','proof','output']:p.add_argument('--'+flag,type=Path,required=True)
 p.add_argument('--proof-sha256',required=True);p.add_argument('--source-revision',required=True);a=p.parse_args();print(json.dumps(package(a.images,a.metadata,a.proof,a.proof_sha256,a.source_revision,a.output),indent=2))

if __name__=='__main__':main()
