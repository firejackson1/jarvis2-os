#!/usr/bin/env python3
"""Build and verify offline images against the saved slot A sizes. Contains no device writes."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from stage_rom import snapshot

def build(work,source,key):
    sys.path.insert(0,str(source/'external/avb'))
    import avbtool
    avb=avbtool.Avb()
    tools=source/'out/host/linux-x86/bin'
    env=dict(os.environ,PATH=str(tools)+':'+os.environ['PATH'])
    output=work/'images-candidate';output.mkdir(exist_ok=True)
    stock=work/'images-stock'
    staged=json.loads((work/'rom-staged.json').read_text())
    seed=hashlib.sha256((work/'rom-staged.json').read_bytes()).hexdigest()
    def parse(path):return avb._parse_image(avbtool.ImageHandler(str(path),read_only=True))
    def run(args,log):
        with (work/log).open('w') as f:
            subprocess.run([str(a) for a in args],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    def tree(path):
        return next(d for d in parse(path)[2] if isinstance(d,avbtool.AvbHashtreeDescriptor))
    for partition in ('vendor','odm','vendor_dlkm','system','product'):
        seed=hashlib.sha256(json.dumps(staged[partition],sort_keys=True).encode()).hexdigest()
        image=output/(partition+'.img')
        if image.is_symlink():raise ValueError('Unexpected output symlink')
        if not image.exists():
            cmd=[tools/'mkfs.erofs','--quiet','--preserve-mtime','-zlz4hc,12','-C65536',
                 '-L',partition,'-U',str(uuid.uuid5(uuid.NAMESPACE_URL,seed+partition)),image,work/'rom'/partition]
            run(cmd,'mkfs-'+partition+'.log')
            old_header=parse(stock/(partition+'.img'))[1]
            old=tree(stock/(partition+'.img'))
            cmd=[tools/'avbtool','add_hashtree_footer','--image',image,'--partition_name',partition,
                 '--partition_size',str((stock/(partition+'.img')).stat().st_size),
                 '--algorithm','NONE','--hash_algorithm',old.hash_algorithm,'--salt',old.salt.hex(),
                 '--rollback_index',str(old_header.rollback_index),'--flags',str(old_header.flags)]
            if old.fec_num_roots:cmd+=['--fec_num_roots',str(old.fec_num_roots)]
            else:cmd+=['--do_not_generate_fec']
            for desc in parse(stock/(partition+'.img'))[2]:
                if isinstance(desc,avbtool.AvbPropertyDescriptor):
                    cmd+=['--prop',desc.key+':'+desc.value.decode()]
            run(cmd,'footer-'+partition+'.log')
        run([tools/'avbtool','verify_image','--image',image],'verify-'+partition+'.log')
        extracted=work/'rom-verify'/partition
        if extracted.exists():shutil.rmtree(extracted)
        extracted.parent.mkdir(parents=True,exist_ok=True)
        run(['/usr/bin/fsck.erofs','--xattrs','--preserve','--extract='+str(extracted),image],
            'fsck-'+partition+'.log')
        rebuilt=snapshot(extracted)
        if rebuilt!=staged[partition]:
            diff=[p for p in set(rebuilt)|set(staged[partition]) if rebuilt.get(p)!=staged[partition].get(p)]
            (work/('metadata-diff-'+partition+'.json')).write_text(json.dumps(diff,indent=2))
            raise ValueError('EROFS metadata changed in '+partition+': '+str(diff[:12]))
        assert image.stat().st_size==(stock/(partition+'.img')).stat().st_size
        print(partition,'EROFS round trip, complete file metadata, AVB and partition size verified',flush=True)
    public=avbtool.RSAPublicKey(str(key)).encode()
    (output/'owner-public-key.avb').write_bytes(public)
    # Use the existing owner's parent key for the new child as well. Only that chain key changes.
    for partition,changed in [('vbmeta_system',{'system'}),('vbmeta',{'vendor','odm','vendor_dlkm','product'})]:
        _,header,old_descriptors,_=parse(stock/(partition+'.img'))
        descriptors=[]
        for old in old_descriptors:
            desc=copy.deepcopy(old)
            if isinstance(desc,avbtool.AvbHashtreeDescriptor) and desc.partition_name in changed:
                desc=tree(output/(desc.partition_name+'.img'))
            if isinstance(desc,avbtool.AvbChainPartitionDescriptor) and desc.partition_name=='vbmeta_system':
                desc.public_key=public
            descriptors.append(desc)
        bridge=work/(partition+'-bridge.img')
        bridge.write_bytes(avb._generate_vbmeta_blob(
            algorithm_name='NONE',key_path=None,public_key_metadata_path=None,descriptors=descriptors,
            chain_partitions_use_ab=None,chain_partitions_do_not_use_ab=None,
            rollback_index=header.rollback_index,flags=header.flags,
            rollback_index_location=header.rollback_index_location,props=None,props_from_file=None,
            kernel_cmdlines=None,setup_rootfs_from_kernel=None,ht_desc_to_setup=None,
            include_descriptors_from_image=None,signing_helper=None,signing_helper_with_files=None,
            release_string=None,append_to_release_string=None,
            required_libavb_version_minor=header.required_libavb_version_minor))
        run([tools/'avbtool','make_vbmeta_image','--output',output/(partition+'.img'),
             '--algorithm','SHA256_RSA4096','--key',key,'--include_descriptors_from_image',bridge,
             '--rollback_index',str(header.rollback_index),'--flags',str(header.flags),
             '--rollback_index_location',str(header.rollback_index_location),
             '--padding_size',str((stock/(partition+'.img')).stat().st_size)],'sign-'+partition+'.log')
        _,new_header,new_descriptors,_=parse(output/(partition+'.img'))
        assert new_header.rollback_index==header.rollback_index and new_header.flags==header.flags
        encoded={d.encode() for d in new_descriptors}
        assert encoded=={d.encode() for d in descriptors},'Unexpected AVB descriptor change'
        print(partition,'signature built, rollback/flags and every intended descriptor verified',flush=True)
    verify=work/'verify-tree';verify.mkdir(exist_ok=True)
    for file in stock.glob('*.img'):
        link=verify/file.name
        if link.exists() or link.is_symlink():link.unlink()
        link.symlink_to(output/file.name if (output/file.name).exists() else file)
    parent=parse(output/'vbmeta.img')[2]
    expected=[]
    for desc in parent:
        if isinstance(desc,avbtool.AvbChainPartitionDescriptor):
            path=work/(desc.partition_name+'-expected.avbpubkey')
            path.write_bytes(desc.public_key)
            expected+=['--expected_chain_partition',desc.partition_name+':'+str(desc.rollback_index_location)+':'+str(path)]
    run([tools/'avbtool','verify_image','--image',verify/'vbmeta.img','--key',key]+expected,
        'verify-vbmeta-complete.log')
    run([tools/'avbtool','verify_image','--image',verify/'vbmeta_system.img','--key',key],
        'verify-vbmeta_system-complete.log')
    manifest={'base_slot':'a','flashed':False,'slot_b_touched':False,
              'verified':'All root and child leaf hashes and expected chain keys; boot/OEM contents unchanged, not followed',
              'receiver_lossless_playback':'Not verified; current display has no lossless capability',
              'changed_chain_key':'vbmeta_system uses the same owner key as the existing parent',
              'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in output.glob('*.img')}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Parent AVB, child AVB, all referenced leaf hashes and chain keys verified offline',flush=True)

if __name__=='__main__':build(*(Path(arg) for arg in sys.argv[1:4]))
