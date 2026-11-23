#!/usr/bin/env python3
"""Add only the onn key-layout change to the new offline product tree."""
import hashlib,json,sys
from pathlib import Path
from stage_rom import put,snapshot
w=Path(sys.argv[1]);root=w/'rom/product';journal=w/'rom-before.json';staged=w/'rom-staged.json'
before=json.loads(journal.read_text());old=json.loads(staged.read_text())
if 'product' not in before:
 before['product']=snapshot(root);journal.write_text(json.dumps(before,sort_keys=True))
name='usr/keylayout/Vendor_0957_Product_0031.kl'
assert before['product'][name]['sha256']=='bb06fa90babbd0b949ee991c2066ed784919d468fa94a97d8e93e77221d2956e'
content=(w/'candidate/onn-controls.kl').read_bytes()
assert hashlib.sha256(content).hexdigest()=='dce07a69969f12a71276c13f4f6afd4901a70c5eac8658c5e86f30ef325bd4dc'
put(root,name,content)
now=snapshot(root);changed={k for k in before['product'] if now.get(k)!=before['product'][k]}
assert changed=={name} and now.keys()==before['product'].keys()
if old.get('product')!=now:
 image=w/'images-candidate/product.img'
 if image.exists():image.unlink()
old['product']=now;staged.write_text(json.dumps(old,sort_keys=True))
print('Product staged: only Power/Mic aliases; owners, modes and SELinux labels preserved')
