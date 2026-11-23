#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import hashlib,json,subprocess,sys
from pathlib import Path
root,target,out=map(Path,sys.argv[1:])
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
files={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.glob('Jarvis2*.apk')}
result={'format':1,'unofficial':True,'source_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
 'dirty':bool(subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True).strip()),
 'target_settings_sha256':sha(target),'files':files,'installed':False,'partition_writes':False}
(out/'build-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
