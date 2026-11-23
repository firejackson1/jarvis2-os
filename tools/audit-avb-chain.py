#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify offline AVB descriptors, signatures and parent-bound child public keys."""
import argparse,hashlib,importlib.util,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def audit(images,source,output,root_key_sha256=None):
    images=images.resolve();source=source.resolve();output=output.resolve()
    if any(output==base or base in output.parents for base in (images,source,ROOT.resolve())):
        raise ValueError('Audit output must be outside input directories')
    if output.exists():raise ValueError('Audit output must be fresh')
    if root_key_sha256 is not None and not re.fullmatch(r'[0-9a-f]{64}',root_key_sha256):
        raise ValueError('Invalid expected root key SHA-256')
    spec=importlib.util.spec_from_file_location('jarvis2_upstream_avbtool',source/'external/avb/avbtool.py')
    avbtool=importlib.util.module_from_spec(spec);spec.loader.exec_module(avbtool)
    avb=avbtool.Avb();tool=source/'out/host/linux-x86/bin/avbtool'
    output.mkdir(parents=True);visited={};stack=set()
    def check(part,expected=None):
        if not re.fullmatch(r'[a-zA-Z0-9_]+',part):raise ValueError('Unsafe AVB partition name')
        if part in stack:raise ValueError('Cycle in AVB chain')
        image=avbtool.ImageHandler(str(images/(part+'.img')),read_only=True)
        try:
            footer,header,descriptors,_=avb._parse_image(image)
            offset=(footer.vbmeta_offset if footer else 0)+header.SIZE+header.authentication_data_block_size+header.public_key_offset
            image.seek(offset);key=image.read(header.public_key_size)
        finally:
            # The pinned upstream ImageHandler exposes no close/context manager.
            image._image.close()
        if not key or header.algorithm_type==0:raise ValueError('Chain node must be signed: '+part)
        if expected is not None and expected!=key:raise ValueError('Parent/child public key mismatch: '+part)
        digest=hashlib.sha256(key).hexdigest()
        if part=='vbmeta' and root_key_sha256 is not None and digest!=root_key_sha256:
            raise ValueError('Expected root key does not match')
        if part in visited:return
        stack.add(part);children=[]
        args=[str(tool),'verify_image','--image',str(images/(part+'.img'))]
        for desc in descriptors:
            if isinstance(desc,avbtool.AvbChainPartitionDescriptor):
                child=desc.partition_name
                if not re.fullmatch(r'[a-zA-Z0-9_]+',child):raise ValueError('Unsafe child image name')
                pub=output/(part+'-'+child+'.avbpubkey');pub.write_bytes(desc.public_key)
                args+=['--expected_chain_partition',child+':'+str(desc.rollback_index_location)+':'+str(pub)]
                children.append((child,desc.public_key))
        with (output/(part+'.log')).open('w') as log:
            subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
        for child,childkey in children:check(child,childkey)
        visited[part]={'key_sha256':digest,'rollback_index':header.rollback_index,
                       'flags':header.flags,'children':[child for child,_ in children]}
        stack.remove(part)
    check('vbmeta')
    report={'format':1,'signature_and_leaf_checks_passed':True,'parent_child_public_keys_match':True,
            'operator_root_key_pin_checked':root_key_sha256 is not None,
            'hardware_root_trust_verified':False,'restore_tested':False,'flashed':False,'nodes':visited}
    (output/'avb-chain-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Offline signatures, leaf descriptors and parent/child key bindings passed; hardware acceptance/restore untested.')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('images',type=Path)
    p.add_argument('android_tree',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--root-public-key-sha256',help='optional externally established AVB public-key-blob hash')
    a=p.parse_args();audit(a.images,a.android_tree,a.output,a.root_public_key_sha256)
