#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract offline EROFS images and inspect packaging; does not certify AVB or boot."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARTS=('system','system_ext','product')
REQUIRED=('Jarvis2RemoteSettings.apk','Jarvis2TvControlsOverlay.apk',
          'TvSettingsTwoPanel.apk','Jarvis2LtvLauncher.apk','com.android.btservices.apex')
FORBIDDEN={'TVLauncherNoGMS.apk':'unlicensed Google launcher',
           'TVRecommendationsNoGMS.apk':'unlicensed Google recommendations',
           'Settings.apk':'handset Settings','SystemUI.apk':'handset SystemUI'}
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()
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
    return errors

def inspect_images(images,work,fsck):
    images=images.resolve();work=work.resolve()
    if any(work==base or base in work.parents for base in (images,ROOT.resolve())):
        raise ValueError('Extraction output must be outside input directories')
    if work.exists():raise ValueError('Extraction output must be fresh')
    for part in PARTS:
        if not (images/(part+'.img')).is_file():raise FileNotFoundError(part+'.img')
    manifest=json.loads((ROOT/'manifests/launcher-inputs.json').read_text())
    expected=next(a['sha256'] for a in manifest['artifacts'] if a['name']=='LTvLauncher.apk')
    work.mkdir(parents=True)
    files={}
    for part in PARTS:
        image=images/(part+'.img');before=sha(image)
        with (work/(part+'-fsck.log')).open('w') as log:
            subprocess.run([str(fsck),'--no-preserve','--extract='+str(work/part),str(image)],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        if sha(image)!=before:raise ValueError('Input image changed during extraction: '+part)
        files[image.name]={'sha256':before,'bytes':image.stat().st_size}
    errors=inspect_trees(work,{'launcher_sha256':expected})
    report={'format':1,'unofficial':True,'image_files':files,'errors':errors,
            'scope':'EROFS integrity, required/forbidden package filenames, launcher payload hash, debug trust filenames',
            'avb_chain_verified':False,'boot_tested':False,'complete_privacy_audit':False,'flashed':False}
    (work/'image-content-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)
    print('Scoped extracted-image checks passed; complete privacy, AVB and hardware validation remain required.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('images',type=Path);p.add_argument('output',type=Path);p.add_argument('fsck_erofs',type=Path)
    a=p.parse_args();inspect_images(a.images,a.output,a.fsck_erofs.resolve())
