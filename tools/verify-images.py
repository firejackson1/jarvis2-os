#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record offline image fit and packaging checks; no partition/device operations."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def check(output,limits,avbtool):
    result={'format':1,'unofficial':True,'boot_tested':False,'flashed':False,'files':{},'errors':[]}
    for part,budget in limits.items():
        image=output/(part+'.img')
        if not image.is_file():result['errors'].append('Missing '+image.name);continue
        maximum=int(subprocess.check_output([str(avbtool),'add_hashtree_footer','--partition_size',str(budget),'--hash_algorithm','sha256','--calc_max_image_size'],text=True).strip())
        h=hashlib.sha256()
        with image.open('rb') as f:
            while data:=f.read(1024*1024):h.update(data)
            f.seek(-64,2);signed=f.read(4)==b'AVBf'
        size=image.stat().st_size
        fits=size<=budget if signed else size<=maximum
        result['files'][image.name]={'bytes':size,'partition_budget':budget,'unsigned_payload_max':maximum,'sha256':h.hexdigest(),'has_avb_footer':signed,'fits':fits}
        if not fits:result['errors'].append(part+' exceeds the reference slot-A budget')
    forbidden=['product/priv-app/TVLauncherNoGMS','product/priv-app/TVRecommendationsNoGMS','system_ext/priv-app/Settings','system_ext/priv-app/SystemUI']
    for name in forbidden:
        if (output/name).exists():result['errors'].append('Unwanted staged package: '+name)
    for part in ['root','system','system_ext','product']:
        for key in (output/part).rglob('adb_keys'):
            result['errors'].append('Pre-authorized debug key file: '+str(key.relative_to(output)))
    manifest=output/'jarvis2-image-verification.json';manifest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if result['errors']:raise SystemExit(1)
    print('Offline packaging/size checks passed; AVB chain signing and device tests remain required.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('limits',type=Path);p.add_argument('avbtool',type=Path)
    a=p.parse_args();check(a.output.resolve(),json.loads(a.limits.read_text()),a.avbtool.resolve())
