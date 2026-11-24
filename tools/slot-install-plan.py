#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Produce a read-only A/B install plan; never flash, resize, activate or wipe."""
import argparse,hashlib,json,subprocess
from pathlib import Path
PARTS=('system','system_ext','product','vbmeta_system','vbmeta')
FOUNDATION=('system','system_ext','product','vendor','odm','system_dlkm','vendor_dlkm','odm_dlkm')
def plan(slot,manifest,views):
    if slot not in ('a','b'):raise ValueError('An explicit a or b target is required')
    if not manifest.get('avb_offline_verified'):raise ValueError('Complete offline AVB verification is required')
    if len(views)!=2 or views[0]['canonical']!=views[1]['canonical']:
        raise ValueError('Shared metadata views differ; stock fastbootd would overwrite the other view')
    sizes=views[0]['sizes']
    if any(sizes.get(part+'_'+slot,0)<=0 for part in FOUNDATION):
        raise ValueError('Target has an unallocated/incomplete logical OS foundation; full provisioning is required')
    writes=[]
    for part in PARTS:
        name=part+'_'+slot;info=manifest['files'][part+'.img']
        if info['bytes']<=0 or sizes.get(name)!=info['bytes']:
            raise ValueError('Partition/image size mismatch for '+name+'; automatic resize is forbidden')
        writes.append({'partition':name,'file':part+'.img','bytes':info['bytes'],'sha256':info['sha256']})
    other='b' if slot=='a' else 'a'
    return {'other_slot_foundation_allocated':all(sizes.get(part+'_'+other,0)>0 for part in FOUNDATION),'format':1,'target_slot':slot,'writes':writes,'switch_slot':False,'wipe_data':False,'executed':False,
            'shared_metadata_views_match':True,
            'limitation':'Read-only plan. Firmware compatibility, recovery transport and release-signature trust require separate verification. Stock fastbootd may rewrite shared metadata even for same-size flashes.'}
def load_views(tool,metadata,physical):
    allowed={part+'_'+slot for part in ('vbmeta','vbmeta_system') for slot in ('a','b')}
    if set(physical)!=allowed or any(not isinstance(v,int) or v<=0 for v in physical.values()):
        raise ValueError('Provide verified sizes for both slots physical vbmeta partitions')
    views=[]
    for slot in (0,1):
        data=json.loads(subprocess.check_output([tool,'--slot',str(slot),'--json',metadata],text=True))
        text=subprocess.check_output([tool,'--slot',str(slot),metadata],text=True)
        lines=text.splitlines()
        if not lines or lines[0]!='Slot '+str(slot)+':':raise ValueError('Unexpected native metadata dump format')
        sizes={p['name']:int(p.get('size',0)) for p in data['partitions']};sizes.update(physical)
        views.append({'canonical':'\n'.join(lines[1:]),'sizes':sizes})
    return views
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--slot',choices=('a','b'),required=True)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--images',type=Path,required=True)
    p.add_argument('--super-metadata',type=Path,required=True);p.add_argument('--physical-sizes',type=Path,required=True)
    p.add_argument('--lpdump',type=Path,required=True)
    a=p.parse_args();manifest=json.loads(a.manifest.read_text())
    views=load_views(str(a.lpdump),str(a.super_metadata),json.loads(a.physical_sizes.read_text()))
    result=plan(a.slot,manifest,views)
    for item in result['writes']:
        with (a.images/item['file']).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=item['sha256']:raise ValueError('Image checksum mismatch: '+item['file'])
    print(json.dumps(result,indent=2))
