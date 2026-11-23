#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare pinned licensed launcher inputs, never install anything on a device."""
import argparse,gzip,hashlib,json,re,shutil,struct,subprocess,tarfile,urllib.request,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def verify_hash(path,expected):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Input checksum mismatch: '+path.name)

def prepare(inputs,source,download=False):
    manifest=json.loads((ROOT/'manifests/launcher-inputs.json').read_text())
    inputs.mkdir(parents=True,exist_ok=True)
    for item in manifest['artifacts']:
        p=inputs/item['name']
        if not p.exists():
            if not download:raise FileNotFoundError('Provide '+p.name+' or explicitly pass --download')
            req=urllib.request.Request(item['url'],headers={'User-Agent':'Jarvis2-Source-Preparation'})
            tmp=p.with_suffix(p.suffix+'.partial')
            try:
                with urllib.request.urlopen(req,timeout=60) as response,tmp.open('wb') as f:
                    total=0
                    while chunk:=response.read(1024*1024):
                        total+=len(chunk)
                        if total>100*1024*1024:raise ValueError('Input size limit exceeded')
                        f.write(chunk)
                verify_hash(tmp,item['sha256']);tmp.replace(p)
            finally:tmp.unlink(missing_ok=True)
        verify_hash(p,item['sha256'])
    apk=inputs/'LTvLauncher.apk'
    java=source/'prebuilts/jdk/jdk17/linux-x86/bin/java'
    signer=source/'prebuilts/sdk/tools/linux/lib/apksigner.jar'
    signature=subprocess.check_output([java,'-jar',signer,'verify','--print-certs',apk],text=True)
    actual=re.search(r'Signer #1 certificate SHA-256 digest: (\w+)',signature).group(1)
    if actual!=manifest['certificate_sha256']:raise ValueError('Launcher signer mismatch')
    subprocess.run([source/'out/host/linux-x86/bin/zipalign','-c','-p','4',apk],check=True)
    with tarfile.open(inputs/'LTvLauncher-source.tar.gz') as tf:
        names=tf.getnames();prefix='LtvLauncher-'+manifest['source_commit']+'/'
        for name in ['LICENSE','pubspec.lock','android/app/build.gradle','.github/workflows/release.yml']:
            if prefix+name not in names:raise ValueError('Missing exact-source material: '+name)
        (inputs/'LTvLauncher-LICENSE.txt').write_bytes(tf.extractfile(prefix+'LICENSE').read())
    output=ROOT/'apps/Launcher/prebuilts';output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(apk) as z:
        libraries={Path(i.filename).name:i for i in z.infolist() if i.filename.startswith('lib/armeabi-v7a/') and i.filename.endswith('.so')}
        if set(libraries)!=set(manifest['native_libraries']):raise ValueError('Unexpected native-library set')
        for name,item in libraries.items():
            data=z.read(item)
            if data[:4]!=b'\x7fELF' or data[4]!=1 or struct.unpack_from('<H',data,18)[0]!=40:raise ValueError('Expected ARM32 library: '+name)
            (output/name).write_bytes(data)
        compressed=z.read('assets/flutter_assets/NOTICES.Z')
        try:notices=gzip.decompress(compressed)
        except gzip.BadGzipFile:notices=zlib.decompress(compressed)
        (inputs/'LTvLauncher-NOTICES.txt').write_bytes(notices)
    shutil.copyfile(apk,output/'LTvLauncher.apk')
    (inputs/'launcher-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Pinned APK signature, hash, ZIP alignment, ARM32 libraries and source material verified; no device operation.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('inputs',type=Path);parser.add_argument('android_tree',type=Path);parser.add_argument('--download',action='store_true')
    args=parser.parse_args();prepare(args.inputs.resolve(),args.android_tree.resolve(),args.download)
