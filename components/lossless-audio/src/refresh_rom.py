#!/usr/bin/env python3
"""Refresh only reviewed files in an already staged offline tree."""
import json,sys
from pathlib import Path
from stage_rom import put,snapshot,PERMISSIONS_XML
OVERLAY_CONFIG=b'<config><overlay package="app.jarvis2.controls.overlay" enabled="true" mutable="true"/></config>\n'
w,apk=map(Path,sys.argv[1:3]);old=json.loads((w/'rom-staged.json').read_text())
updates={
 'vendor':{'lib/hw/audio.primary.amlogic.so':(w/'candidate/audio.primary.amlogic.so').read_bytes()},
 'odm':{'etc/audio_policy_configuration.xml':(w/'candidate/audio_policy_configuration.xml').read_bytes()},
 'system':{'system/overlay/Jarvis2TvControlsOverlay.apk':(w/'candidate/Jarvis2TvControlsOverlay.apk').read_bytes(),
           'system/overlay/config/config.xml':OVERLAY_CONFIG,
           'system/apex/com.android.btservices.apex':(w.parent/'jarvis2-ear-detection/com.android.btservices.apex').read_bytes(),
           'system/priv-app/Jarvis2RemoteSettings/Jarvis2RemoteSettings.apk':apk.read_bytes(),
           'system/etc/permissions/privapp-permissions-jarvis2.xml':PERMISSIONS_XML}}
for part,files in updates.items():
 for name,data in files.items():put(w/'rom'/part,name,data)
 now=snapshot(w/'rom'/part)
 changed={k for k in old[part] if now.get(k)!=old[part][k]}
 assert changed<=files.keys(),(part,changed)
 added=set(now)-set(old[part])
 allowed_additions=set(files)
 for name in files:
  allowed_additions.update(str(p) for p in Path(name).parents if str(p) not in old[part])
 assert added<=allowed_additions,(part,added)
 assert not set(old[part])-set(now)
 changed.update(added)
 if changed:
  image=w/'images-candidate'/(part+'.img')
  if image.exists():image.unlink()
 old[part]=now
 print(part,sorted(changed))
(w/'rom-staged.json').write_text(json.dumps(old,sort_keys=True))
