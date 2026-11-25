#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract offline EROFS images and inspect packaging; does not certify AVB or boot."""
import argparse,hashlib,importlib.util,json,re,stat,subprocess,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARTS=('system','system_ext','product')
REQUIRED=('Jarvis2RemoteSettings.apk','Jarvis2TvControlsOverlay.apk',
          'TvSettingsTwoPanel.apk','Jarvis2LtvLauncher.apk','com.android.btservices.apex')
FORBIDDEN={'Updater.apk':'unsupported official OTA client',
           'TVLauncherNoGMS.apk':'unlicensed Google launcher',
           'TVRecommendationsNoGMS.apk':'unlicensed Google recommendations',
           'Settings.apk':'handset Settings','SystemUI.apk':'handset SystemUI'}
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def prefix_sha256(stream, size):
    digest = hashlib.sha256()
    while size:
        block = stream.read(min(size, 1048576))
        if not block:
            raise ValueError('Truncated EROFS filesystem prefix')
        digest.update(block)
        size -= len(block)
    return digest.hexdigest()


def verify_archive_filesystems(images, target_files, target_files_sha256):
    if (target_files.is_symlink() or not target_files.is_file() or
        not re.fullmatch('[0-9a-f]{64}', target_files_sha256) or sha(target_files) != target_files_sha256):
        raise ValueError('Signed target-files archive SHA-256 or path differs from the reviewed input')

    spec = importlib.util.spec_from_file_location('image_contents_erofs', ROOT/'tools/gapps-profile.py')
    profiles = importlib.util.module_from_spec(spec)
    previous_setting = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(profiles)
    finally:
        sys.dont_write_bytecode = previous_setting
    filesystems = {}
    with zipfile.ZipFile(target_files) as archive:
        entries = archive.infolist()
        members = {entry.filename: entry for entry in entries}
        if len(members) != len(entries):
            raise ValueError('Duplicate signed target-files archive member')
        for partition in PARTS:
            name = partition + '.img'
            member = 'IMAGES/' + name
            entry = members.get(member)
            if (entry is None or entry.flag_bits & 1 or
                stat.S_IFMT(entry.external_attr >> 16) not in (0, stat.S_IFREG)):
                raise ValueError('Missing or invalid signed target-files image member: ' + member)
            with profiles.ErofsMetadata(images/name) as erofs:
                size = erofs.geometry['filesystem_bytes']
                erofs.file.seek(0)
                inspected = prefix_sha256(erofs.file, size)
            if entry.file_size < size:
                raise ValueError(name + ' is shorter than the final filesystem in the signed archive')
            with archive.open(entry) as source:
                if prefix_sha256(source, size) != inspected:
                    raise ValueError(name + ' filesystem bytes differ from the signed target-files archive')
            filesystems[name] = {'member': member, 'filesystem_bytes': size,
                                 'filesystem_sha256': inspected}
    if sha(target_files) != target_files_sha256:
        raise ValueError('Signed target-files archive changed during filesystem inspection')
    return {'target_files_sha256': target_files_sha256, 'filesystems': filesystems}


def inspect_trees(work,policy):
    errors=[];found={name:[] for name in REQUIRED}
    for part in PARTS:
        tree=work/part
        if not tree.is_dir():errors.append('Missing extracted tree: '+part);continue
        for path in tree.rglob('*'):
            # Do not follow filesystem symlinks outside the extracted partition.
            if path.is_symlink():continue
            name=path.name
            if name in {'adb_keys','default_adb_keys','adbkey','adbkey.pub'}:
                errors.append('Pre-authorized debug trust: '+str(path.relative_to(work)))
            if not path.is_file():continue
            if name in FORBIDDEN:errors.append(FORBIDDEN[name]+': '+str(path.relative_to(work)))
            if name in found:found[name].append(path)
    for name,paths in found.items():
        if not paths:errors.append('Missing required package: '+name)
        elif len(paths)!=1:errors.append('Duplicate required package: '+name)
    for path in found['Jarvis2LtvLauncher.apk']:
        if sha(path)!=policy['launcher_sha256']:errors.append('Pinned launcher checksum mismatch')
    allowlist=work/'system_ext/etc/permissions/privapp-permissions-jarvis2-remote.xml'
    try:
        if allowlist.is_symlink():raise ValueError('symlink')
        xml=ET.parse(allowlist).getroot()
        grants={p.get('name') for entry in xml.findall('privapp-permissions')
                if entry.get('package')=='app.jarvis2.remote' for p in entry.findall('permission')}
        required={'android.permission.BLUETOOTH_PRIVILEGED',
                  'android.permission.MODIFY_AUDIO_ROUTING','android.permission.MEDIA_CONTENT_CONTROL'}
        if xml.tag!='permissions' or not required<=grants:raise ValueError('missing grants')
    except (OSError,ET.ParseError,ValueError):
        errors.append('Missing or invalid remote privilege allowlist XML')
    return errors

def inspect_images(images,work,fsck,*,target_files=None,target_files_sha256=None):
    images=images.resolve();work=work.resolve()
    if any(work==base or base in work.parents for base in (images,ROOT.resolve())):
        raise ValueError('Extraction output must be outside input directories')
    if work.exists():raise ValueError('Extraction output must be fresh')
    if (target_files is None) != (target_files_sha256 is None):
        raise ValueError('Both signed target-files archive and its SHA-256 pin are required')
    files={}
    for part in PARTS:
        image=images/(part+'.img')
        if not image.is_file():raise FileNotFoundError(image.name)
        files[image.name]={'sha256':sha(image),'bytes':image.stat().st_size}
    binding = None
    if target_files is not None:
        binding = verify_archive_filesystems(images, target_files, target_files_sha256)
    manifest=json.loads((ROOT/'manifests/launcher-inputs.json').read_text())
    expected=next(a['sha256'] for a in manifest['artifacts'] if a['name']=='LTvLauncher.apk')
    work.mkdir(parents=True)
    for part in PARTS:
        image=images/(part+'.img')
        with (work/(part+'-fsck.log')).open('w') as log:
            subprocess.run([str(fsck),'--no-preserve','--extract='+str(work/part),str(image)],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
    for name, record in files.items():
        image=images/name
        if image.stat().st_size!=record['bytes'] or sha(image)!=record['sha256']:
            raise ValueError('Input image changed during inspection: '+name)
    if binding is not None and sha(target_files) != target_files_sha256:
        raise ValueError('Signed target-files archive changed during image inspection')
    errors=inspect_trees(work,{'launcher_sha256':expected})
    report={'format':1,'unofficial':True,'image_files':files,'errors':errors,
            'scope':'EROFS integrity, required/forbidden package filenames, launcher payload hash, debug trust filenames, remote privilege allowlist XML',
            'avb_chain_verified':False,'boot_tested':False,'complete_privacy_audit':False,'flashed':False}
    if binding is not None:
        report['signed_target_files_filesystem_binding'] = binding
    (work/'image-content-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)
    print('Scoped extracted-image checks passed; complete privacy, AVB and hardware validation remain required.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('images',type=Path);p.add_argument('output',type=Path);p.add_argument('fsck_erofs',type=Path)
    p.add_argument('--signed-target-files',type=Path)
    p.add_argument('--signed-target-files-sha256')
    a=p.parse_args()
    inspect_images(a.images,a.output,a.fsck_erofs.resolve(),target_files=a.signed_target_files,
                   target_files_sha256=a.signed_target_files_sha256)
