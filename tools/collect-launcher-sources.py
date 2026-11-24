#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Collect locked hosted launcher dependencies; SDK/legal review remain separate."""
import argparse,concurrent.futures,hashlib,json,re,tarfile,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    return h.hexdigest()
def collect_one(name,info,output,download=False):
    version=str(info['version']);source=info['source']
    if not re.fullmatch(r'[a-z_][a-z0-9_]*',name) or not re.fullmatch(r'[0-9A-Za-z.+_-]+',version):
        raise ValueError('Invalid dependency name or version')
    if source=='sdk':return {'name':name,'version':version,'source':'sdk','collected':False}
    if source!='hosted':raise ValueError('Unsupported dependency source: '+source)
    desc=info['description'];expected=desc['sha256']
    if desc.get('url')!='https://pub.dev' or not re.fullmatch(r'[0-9a-f]{64}',expected):
        raise ValueError('Unsupported archive host or checksum')
    filename=name+'-'+version+'.tar.gz';archive=output/filename
    if archive.is_symlink():raise ValueError('Archive must not be a symlink')
    url='https://pub.dev/api/archives/'+filename
    if not archive.exists():
        if not download:raise FileNotFoundError('Missing source archive: '+filename)
        partial=archive.with_suffix('.gz.partial')
        # Exclusive creation prevents accidental reuse or following a partial symlink.
        try:
            with partial.open('xb') as f:
                request=urllib.request.Request(url,headers={'User-Agent':'Jarvis2-Corresponding-Source'})
                with urllib.request.urlopen(request,timeout=60) as response:
                    size=0
                    while chunk:=response.read(1024*1024):
                        size+=len(chunk)
                        if size>64*1024*1024:raise ValueError('Source archive size limit exceeded')
                        f.write(chunk)
            if digest(partial)!=expected:raise ValueError('Locked source checksum mismatch: '+name)
            partial.replace(archive)
        finally:
            # Only remove a partial created by this invocation.
            if 'f' in locals():partial.unlink(missing_ok=True)
    actual=digest(archive)
    if actual!=expected:raise ValueError('Locked source checksum mismatch: '+name)
    return {'name':name,'version':version,'source':source,'collected':True,
            'sha256':actual,'bytes':archive.stat().st_size,'url':url,'file':filename}
def framework_material(inputs,manifest):
    spec=manifest.get('framework_source')
    if not spec:return {}
    archive=inputs/spec['name']
    if not archive.is_file():return {}
    if digest(archive)!=spec['sha256']:raise ValueError('Framework source checksum mismatch')
    result={}
    with tarfile.open(archive) as tf:
        for name in spec['packages']:
            path='packages/'+name
            member=tf.getmember(spec['prefix']+'/'+path+'/pubspec.yaml')
            if not member.isfile():raise ValueError('Missing SDK package source: '+name)
            result[name]={'collected':True,'archive':spec['name'],'archive_sha256':spec['sha256'],
                          'source_commit':spec['source_commit'],'path':path}
    return result

def sdk_material(inputs,manifest):
    result=framework_material(inputs,manifest)
    spec=manifest.get('sky_engine_source')
    if not spec:return result
    revision=spec['engine_revision']
    if revision!=manifest.get('framework_source',{}).get('engine_revision'):
        raise ValueError('Sky engine revision mismatch')
    archive=inputs/spec['name']
    if archive.is_symlink():raise ValueError('Sky engine archive must not be a symlink')
    if not archive.is_file():return result
    if digest(archive)!=spec['sha256']:raise ValueError('Sky engine source checksum mismatch')
    with zipfile.ZipFile(archive) as z:
        names=set()
        for member in z.infolist():
            name=member.filename
            if (name.startswith('/') or '\\' in name or
                any(part in ('.','..','') for part in name.rstrip('/').split('/')) or
                (name.split('/')[0]!='sky_engine' and name!='LICENSE.zip_old_location.md') or name in names or
                (member.external_attr>>16)&0o170000==0o120000):
                raise ValueError('Unsafe sky engine ZIP member: '+name)
            names.add(name)
        for name in ('sky_engine/pubspec.yaml','sky_engine/LICENSE','sky_engine/lib/ui/ui.dart'):
            if name not in names or not 0<z.getinfo(name).file_size<=4*1024*1024:
                raise ValueError('Missing or invalid sky engine package member: '+name)
        marker=z.read('sky_engine/pubspec.yaml').decode('utf-8')
        if not re.search(r'^name: sky_engine\s*$',marker,re.M) or not re.search(
                r'^version: '+re.escape(spec['version'])+r'\s*$',marker,re.M):
            raise ValueError('Sky engine package identity mismatch')
    result['sky_engine']={'collected':True,'archive':spec['name'],
        'archive_sha256':spec['sha256'],'engine_revision':revision,'path':'sky_engine',
        'version':spec['version'],'material_kind':'generated_sdk_package',
        'engine_dependency_closure_complete':False}
    return result

def collect(inputs,download=False):
    inputs=inputs.resolve()
    if inputs==ROOT or ROOT in inputs.parents:raise ValueError('Inputs must be outside the source repository')
    manifest=json.loads((ROOT/'manifests/launcher-inputs.json').read_text())
    archive=inputs/'LTvLauncher-source.tar.gz'
    expected=next(a['sha256'] for a in manifest['artifacts'] if a['name']==archive.name)
    if digest(archive)!=expected:raise ValueError('Pinned launcher source checksum mismatch')
    import yaml
    with tarfile.open(archive) as tf:
        member='LtvLauncher-'+manifest['source_commit']+'/pubspec.lock'
        info=tf.getmember(member)
        if not info.isfile() or info.size>1024*1024:raise ValueError('Invalid source lockfile')
        packages=yaml.safe_load(tf.extractfile(info))['packages']
    output=inputs/'dependency-sources';output.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda item:collect_one(item[0],item[1],output,download),sorted(packages.items())))
    framework=sdk_material(inputs,manifest)
    for item in results:
        if item['source']=='sdk' and item['name'] in framework:item.update(framework[item['name']])
    report={'format':1,'source_commit':manifest['source_commit'],'dependencies':results,
            'complete_corresponding_source':False,'license_review_complete':False,
            'engine_dependency_closure_complete':False}
    (inputs/'dependency-source-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified hosted archives:',sum(item['source']=='hosted' and item['collected'] for item in results))
    print('SDK packages with verified source material:',len(framework))
    print('SDK dependencies requiring separate material:',sum(item['source']=='sdk' and not item['collected'] for item in results))
    print('Dependency collection does not establish complete source/license compliance.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('inputs',type=Path)
    p.add_argument('--download',action='store_true',help='explicitly permit missing hosted source downloads')
    a=p.parse_args();collect(a.inputs,a.download)
