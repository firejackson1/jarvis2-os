#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Produce a read-only A/B install plan; never flash, resize, activate or wipe."""
import argparse,hashlib,json,os,re,stat,subprocess
from pathlib import Path
PARTS=('system','system_ext','product','vbmeta_system','vbmeta')
FOUNDATION=('system','system_ext','product','vendor','odm','system_dlkm','vendor_dlkm','odm_dlkm')
SECTOR_SIZE=512
PHYSICAL={part+'_'+slot for part in ('vbmeta','vbmeta_system') for slot in ('a','b')}
def native_uint(value):
    if isinstance(value,str) and re.fullmatch(r'(0|[1-9][0-9]*)',value):value=int(value)
    if type(value) is not int or not 0<=value<2**64:
        raise ValueError('Native sizes must be nonnegative integers or canonical decimal strings')
    return value

def parse_layout(data,text):
    """Pinned native JSON omits extents: cross-check its text tables instead.

    Native liblp validates raw extent source indexes before lpdump emits names.
    This bounded format accepts only index zero on one unsuffixed super device.
    Captured declarations do not establish live physical identity or capacity.
    """
    def section(start,end):
        if text.count(start)!=1 or text.count(end)!=1:raise ValueError('Unexpected native layout tables')
        return text.split(start,1)[1].split(end,1)[0]
    def header(pattern):
        matches=re.findall(pattern,text,re.M)
        if len(matches)!=1:raise ValueError('Missing or duplicate native geometry field')
        return int(matches[0])
    devices=data.get('block_devices')
    if not isinstance(devices,list) or len(devices)!=1 or devices[0].get('name')!='super':
        raise ValueError('Only a single super backing device is supported')
    device=dict(devices[0])
    for key in ('size','block_size','alignment','alignment_offset'):
        device[key]=native_uint(device.get(key,0))
    body=section('Block device table:\n','Group table:\n')
    pattern=r'^  Partition name: ([A-Za-z0-9_]+)\n  First sector: ([0-9]+)\n  Size: ([0-9]+) bytes\n  Flags: ([^\n]*)\n'
    records=re.findall(pattern,body,re.M)
    if len(records)!=1 or re.sub(pattern,'',body,flags=re.M).replace('------------------------','').strip():
        raise ValueError('Unexpected native backing device table')
    name,first,size,flags=records[0]
    if name!=device['name'] or int(size)!=device['size'] or flags!='none':
        raise ValueError('Native backing device identities or sizes differ')
    device['first_logical_sector']=int(first)
    body=section('Partition table:\n','Super partition layout:\n')
    pattern=r'^  Name: ([A-Za-z0-9_]+)\n  Group: ([A-Za-z0-9_]+)\n  Attributes: [^\n]*\n  Extents:\n((?:    [^\n]*\n)*)'
    records=re.findall(pattern,body,re.M)
    if re.sub(pattern,'',body,flags=re.M).replace('------------------------','').strip():
        raise ValueError('Unexpected native partition extent table')
    json_parts={}
    for part in data['partitions']:
        name=part['name']
        if name in json_parts or name in PHYSICAL:raise ValueError('Duplicate or physical name in logical partition table')
        json_parts[name]=part
    partitions={}
    for name,group,extent_text in records:
        if name in partitions or name not in json_parts or json_parts[name].get('group_name')!=group:
            raise ValueError('Native partition identities or groups differ')
        extents=[]
        for line in extent_text.splitlines():
            match=re.fullmatch(r'    ([0-9]+) \.\. ([0-9]+) linear ([A-Za-z0-9_]+) ([0-9]+)',line)
            if not match:raise ValueError('Unsupported zero/nonlinear or malformed extent')
            start,end,source,offset=match.groups();start,end=int(start),int(end)
            if source!='super' or end<start:raise ValueError('Invalid extent source or sector range')
            extents.append({'logical_sector':start,'num_sectors':end-start+1,'target_type':'linear',
                            'target_source':0,'target_name':source,'target_data':int(offset)})
        partitions[name]=extents
    if set(partitions)!=set(json_parts):raise ValueError('Native JSON/text logical partitions differ')
    return {'sector_size':SECTOR_SIZE,'metadata_max_size':header(r'^Metadata max size: ([0-9]+) bytes$'),
            'metadata_slot_count':header(r'^Metadata slot count: ([0-9]+)$'),
            'block_devices':[device],'partitions':partitions}

def validate_layout(view):
    layout=view.get('layout')
    if not isinstance(layout,dict):raise ValueError('Validated native extent layout is required')
    if type(layout.get('sector_size')) is not int or layout['sector_size']!=SECTOR_SIZE:
        raise ValueError('LP extent sector size must be 512 bytes')
    devices=layout.get('block_devices')
    if not isinstance(devices,list) or len(devices)!=1 or devices[0].get('name')!='super':
        raise ValueError('Only a single super backing device is supported')
    device=devices[0]
    for key in ('size','block_size','alignment','alignment_offset','first_logical_sector'):
        if type(device.get(key)) is not int or not 0<=device[key]<2**64:
            raise ValueError('Invalid native device geometry: '+key)
    block=device['block_size'];alignment=device['alignment']
    if (block<SECTOR_SIZE or block%SECTOR_SIZE or block&(block-1) or
        alignment<SECTOR_SIZE or alignment%SECTOR_SIZE or device['alignment_offset']!=0 or
        not device['size'] or device['size']%block or
        device['first_logical_sector']*SECTOR_SIZE>device['size']):
        raise ValueError('Unsupported backing device size/block alignment geometry')
    for key in ('metadata_max_size','metadata_slot_count'):
        if type(layout.get(key)) is not int or layout[key]<=0:raise ValueError('Invalid metadata geometry')
    reserved=12288+2*layout['metadata_max_size']*layout['metadata_slot_count']
    if layout['metadata_max_size']%SECTOR_SIZE or device['first_logical_sector']*SECTOR_SIZE<reserved:
        raise ValueError('Metadata reserved prefix exceeds first logical sector')
    partitions=layout.get('partitions')
    if not isinstance(partitions,dict) or set(partitions)!=set(view['sizes'])-PHYSICAL:
        raise ValueError('Logical extent layout and partition sizes differ')
    intervals=[]
    for name,extents in partitions.items():
        if not re.fullmatch(r'[A-Za-z0-9_]+',name) or not isinstance(extents,list):
            raise ValueError('Malformed partition extent layout')
        logical=0
        for extent in extents:
            if not isinstance(extent,dict) or extent.get('target_type')!='linear':
                raise ValueError('Unsupported zero/nonlinear extent')
            for key in ('logical_sector','num_sectors','target_source','target_data'):
                if type(extent.get(key)) is not int or not 0<=extent[key]<2**64:
                    raise ValueError('Invalid extent sector or source index: '+key)
            if extent['target_source']!=0 or extent.get('target_name')!='super':
                raise ValueError('Extent backing device source index/name differs')
            count=extent['num_sectors'];offset=extent['target_data'];end=offset+count
            if not count or extent['logical_sector']!=logical:
                raise ValueError('Extent logical sector ranges must be positive and contiguous')
            if offset<device['first_logical_sector'] or end*SECTOR_SIZE>device['size']:
                raise ValueError('Extent bounds cross device capacity or protected metadata prefix')
            if count*SECTOR_SIZE%block or offset*SECTOR_SIZE%block or offset*SECTOR_SIZE%alignment:
                raise ValueError('Extent violates logical block/sector alignment')
            logical+=count
            intervals.append((offset,end,name))
        if logical*SECTOR_SIZE!=view['sizes'][name]:raise ValueError('Extent byte size differs from native partition size: '+name)
    intervals.sort()
    for previous,current in zip(intervals,intervals[1:]):
        if current[0]<previous[1]:raise ValueError('Logical partition extents overlap: '+previous[2]+' / '+current[2])

def plan(slot,manifest,views):
    if slot not in ('a','b'):raise ValueError('An explicit a or b target is required')
    if not isinstance(manifest,dict) or manifest.get('avb_offline_verified') is not True:raise ValueError('Complete offline AVB verification is required')
    if len(views)!=2 or views[0]['canonical']!=views[1]['canonical']:
        raise ValueError('Shared metadata views differ; stock fastbootd would overwrite the other view')
    files=manifest.get('files')
    if not isinstance(files,dict):raise ValueError('Manifest files must be an object')
    for part in PARTS:
        info=files.get(part+'.img')
        if not isinstance(info,dict) or type(info.get('bytes')) is not int or info['bytes']<=0:
            raise ValueError('Manifest image size must be a positive integer: '+part)
        if not isinstance(info.get('sha256'),str) or not re.fullmatch(r'[0-9a-fA-F]{64}',info['sha256']):
            raise ValueError('Invalid SHA256 digest: '+part)
    for view in views:
        if any(type(value) is not int or value<0 for value in view['sizes'].values()):
            raise ValueError('Partition sizes must be nonnegative integers')
    for view in views:validate_layout(view)
    if views[0]['layout']!=views[1]['layout']:raise ValueError('Native metadata extent layouts differ')
    sizes=views[0]['sizes']
    if any(sizes.get(part+'_'+slot,0)<=0 for part in FOUNDATION):
        raise ValueError('Target has an unallocated/incomplete logical OS foundation; full provisioning is required')
    writes=[]
    for part in PARTS:
        name=part+'_'+slot;info=manifest['files'][part+'.img']
        if info['bytes']<=0 or sizes.get(name)!=info['bytes']:
            raise ValueError('Partition/image size mismatch for '+name+'; automatic resize is forbidden')
        writes.append({'partition':name,'file':part+'.img','bytes':info['bytes'],'sha256':info['sha256'].lower()})
    other='b' if slot=='a' else 'a'
    return {'other_slot_foundation_allocated':all(sizes.get(part+'_'+other,0)>0 for part in FOUNDATION),'format':1,'target_slot':slot,'writes':writes,'switch_slot':False,'wipe_data':False,'executed':False,
            'shared_metadata_views_match':True,'linear_extent_layout_validated':True,'live_physical_identity_verified':False,
            'limitation':'Read-only plan. Firmware compatibility, recovery transport and release-signature trust require separate verification. Stock fastbootd may rewrite shared metadata even for same-size flashes.'}
def load_views(tool,metadata,physical):
    allowed=PHYSICAL
    if set(physical)!=allowed or any(type(v) is not int or v<=0 for v in physical.values()):
        raise ValueError('Provide verified sizes for both slots physical vbmeta partitions')
    views=[]
    for slot in (0,1):
        data=json.loads(subprocess.check_output([tool,'--slot',str(slot),'--json',metadata],text=True))
        text=subprocess.check_output([tool,'--slot',str(slot),metadata],text=True)
        lines=text.splitlines()
        if not lines or lines[0]!='Slot '+str(slot)+':':raise ValueError('Unexpected native metadata dump format')
        sizes={}
        for part in data['partitions']:
            name=part['name']
            if name in sizes or name in PHYSICAL:raise ValueError('Duplicate or physical name in logical partition table')
            sizes[name]=native_uint(part.get('size',0))
        layout=parse_layout(data,text)
        sizes.update(physical)
        view={'canonical':'\n'.join(lines[1:]),'sizes':sizes,'layout':layout}
        validate_layout(view)
        views.append(view)
    return views
def validate_images(images,result):
    """Check local raw files for a read-only plan; this establishes no AVB trust."""
    for item in result['writes']:
        path=images/item['file']
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('Image must be a regular file: '+item['file'])
        with path.open('rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode):raise ValueError('Image must be a regular file: '+item['file'])
            if info.st_size!=item['bytes']:raise ValueError('Image file size mismatch: '+item['file'])
            if f.read(4)==b'\x3a\xff\x26\xed':raise ValueError('Sparse images are unsupported: '+item['file'])
            f.seek(0)
            actual=hashlib.file_digest(f,'sha256').hexdigest()
        if actual!=item['sha256']:raise ValueError('Image checksum mismatch: '+item['file'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--slot',choices=('a','b'),required=True)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--images',type=Path,required=True)
    p.add_argument('--super-metadata',type=Path,required=True);p.add_argument('--physical-sizes',type=Path,required=True)
    p.add_argument('--lpdump',type=Path,required=True)
    a=p.parse_args();manifest=json.loads(a.manifest.read_text())
    views=load_views(str(a.lpdump),str(a.super_metadata),json.loads(a.physical_sizes.read_text()))
    result=plan(a.slot,manifest,views)
    validate_images(a.images,result)
    print(json.dumps(result,indent=2))
