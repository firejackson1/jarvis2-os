#!/usr/bin/env python3
"""Stage slot-local overrides in extracted, offline EROFS trees. Never follow OEM links."""
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys

PERMISSIONS_XML=b'''<permissions>
<feature name="app.jarvis2.audio.lossless" version="1"/>
<privapp-permissions package="app.jarvis2.remote">
<permission name="android.permission.BLUETOOTH_PRIVILEGED"/>
<permission name="android.permission.MODIFY_AUDIO_ROUTING"/>
</privapp-permissions></permissions>\n'''

def snapshot(root):
    result={}
    paths=[root]
    for directory,dirs,files in os.walk(root,followlinks=False):
        paths.extend(Path(directory)/name for name in dirs+files)
    for path in paths:
        s=path.lstat()
        entry={'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,
               'xattrs':{name:base64.b64encode(os.getxattr(path,name,follow_symlinks=False)).decode()
                         for name in os.listxattr(path,follow_symlinks=False)}}
        if stat.S_ISLNK(s.st_mode):entry['link']=os.readlink(path)
        elif stat.S_ISREG(s.st_mode):entry['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        result[str(path.relative_to(root))]=entry
    return result

def put(root,relative,data,label=None):
    path=root/relative
    # A symlink in a parent could escape the staging tree. Only a final-file link may be replaced.
    for parent in path.parents:
        if parent==root:break
        if parent.is_symlink():raise ValueError('Symlink parent: '+str(parent))
    existed=path.exists() or path.is_symlink()
    if path.is_symlink():
        path.unlink()
        existed=False
    missing=[]
    parent=path.parent
    while not parent.exists():missing.append(parent);parent=parent.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o755)
        os.chown(directory,0,0)
        os.setxattr(directory,'security.selinux',b'u:object_r:system_file:s0\0')
    path.write_bytes(data)
    if not existed:
        path.chmod(0o644);os.chown(path,0,0)
    if label:os.setxattr(path,'security.selinux',(label+'\0').encode())

def patch_codec(data):
    expected='a8d99a85c38e78a7850ae25aa0f29b5f8545d1cf7011f5d73e496b9e1e0e324a'
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Wrong codec module')
    if b'~Module signature appended~' in data[-40:]:raise ValueError('Refusing to modify a signed module')
    shoff=struct.unpack_from('<Q',data,0x28)[0]
    size,count,strings=struct.unpack_from('<HHH',data,0x3a)
    headers=[struct.unpack_from('<IIQQQQIIQQ',data,shoff+i*size) for i in range(count)]
    names=headers[strings][4]
    section=next(h for h in headers if data[names+h[0]:].split(b'\0',1)[0]==b'.data')
    changed=bytearray(data)
    for offset,maximum in [(0x140,8),(0x170,16)]:
        start=section[4]+offset
        if struct.unpack_from('<Q',data,start)[0]!=0x1000000445:raise ValueError('Codec format layout mismatch')
        if struct.unpack_from('<I',data,start+8)[0]!=0x7fe:raise ValueError('Unexpected codec rate mask')
        if struct.unpack_from('<II',data,start+20)!=(2,maximum):raise ValueError('Codec channel layout mismatch')
        struct.pack_into('<I',changed,start+8,0x1ffe)
    diff=[i for i,(a,b) in enumerate(zip(data,changed)) if a!=b]
    assert diff==[section[4]+0x149,section[4]+0x179],diff
    return bytes(changed)

def stage(work,source,apk):
    rom=work/'rom';candidate=work/'candidate'
    journal=work/'rom-before.json'
    if journal.exists():raise FileExistsError('Already staged; extract clean trees before rebuilding')
    before={p:snapshot(rom/p) for p in ('vendor','odm','vendor_dlkm','system')}
    journal.write_text(json.dumps(before,sort_keys=True))
    put(rom/'vendor','lib/hw/audio.primary.amlogic.so',(candidate/'audio.primary.amlogic.so').read_bytes())
    put(rom/'vendor','lib/libamladecs.so',(candidate/'libamladecs.so').read_bytes())
    put(rom/'vendor','etc/aml_audio_config.json',(candidate/'aml_audio_config.json').read_bytes())
    put(rom/'odm','lib/libHwAudio_dtshd.so',(candidate/'libHwAudio_dtshd.so').read_bytes())
    put(rom/'odm','etc/audio_policy_configuration.xml',(candidate/'audio_policy_configuration.xml').read_bytes(),
        'u:object_r:vendor_configs_file:s0')
    prop=(rom/'vendor/build.prop').read_text()
    assert prop.count('ro.vendor.platform.is.forceddp=true')==1
    prop=prop.replace('ro.vendor.platform.is.forceddp=true','ro.vendor.platform.is.forceddp=false')
    assert 'ro.vendor.platform.is.aml_truehd_passthrough=' not in prop
    prop+='\n# Jarvis2 slot-local lossless audio support\nro.vendor.platform.is.aml_truehd_passthrough=true\nro.vendor.jarvis2.lossless_support=1\n'
    put(rom/'vendor','build.prop',prop.encode())
    module=rom/'vendor_dlkm/lib/modules/amlogic-snd-codec-t9015.ko'
    put(rom/'vendor_dlkm','lib/modules/amlogic-snd-codec-t9015.ko',patch_codec(module.read_bytes()))
    libs=['libaudiopolicyengineconfigurable.so','libpolicy-subsystem.so','libparameter.so','libremote-processor.so']
    for lib in libs:
        put(rom/'system','system/lib/'+lib,(source/'out/target/product/jarvis2/system/lib'/lib).read_bytes(),
            'u:object_r:system_lib_file:s0')
    put(rom/'system','system/priv-app/Jarvis2RemoteSettings/Jarvis2RemoteSettings.apk',apk.read_bytes(),
        'u:object_r:system_file:s0')
    put(rom/'system','system/etc/permissions/privapp-permissions-jarvis2.xml',PERMISSIONS_XML,
        'u:object_r:system_file:s0')
    allowed={
        'vendor':{'lib/hw/audio.primary.amlogic.so','lib/libamladecs.so','etc/aml_audio_config.json','build.prop'},
        'odm':{'lib/libHwAudio_dtshd.so','etc/audio_policy_configuration.xml'},
        'vendor_dlkm':{'lib/modules/amlogic-snd-codec-t9015.ko'},
        'system':{'system/lib/'+name for name in libs}|{
            'system/priv-app/Jarvis2RemoteSettings','system/priv-app/Jarvis2RemoteSettings/Jarvis2RemoteSettings.apk',
            'system/etc/permissions/privapp-permissions-jarvis2.xml'}
    }
    after={p:snapshot(rom/p) for p in before}
    report={}
    for partition,entries in before.items():
        changed={name for name,value in entries.items() if after[partition].get(name)!=value}
        added=set(after[partition])-set(entries)
        assert changed|added<=allowed[partition],(partition,changed|added-allowed[partition])
        assert not set(entries)-set(after[partition]),'Unexpected deletion'
        report[partition]={'changed':sorted(changed),'added':sorted(added),'preserved':len(entries)-len(changed)}
    (work/'rom-staged.json').write_text(json.dumps(after,sort_keys=True))
    (work/'rom-changes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':stage(*(Path(arg) for arg in sys.argv[1:4]))
