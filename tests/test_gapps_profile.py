# SPDX-License-Identifier: Apache-2.0
import hashlib,importlib.util,io,json,stat,struct,tempfile,unittest,zipfile
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('gapps_profile',Path(__file__).resolve().parents[1]/'tools/gapps-profile.py')
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
LABEL=b'u:object_r:system_file:s0'

def attr(name,value,index=6):
 body=struct.pack('<BBH',len(name),index,len(value))+name+value
 return body+b'\0'*((-len(body))%4)

def image(label=LABEL,capability=1,shared=False,features=3):
 data=bytearray(4096);struct.pack_into('<III',data,1024,0xe0f5e1e2,0,0);data[1036]=12
 struct.pack_into('<H',data,1038,64);struct.pack_into('<Q',data,1040,2);struct.pack_into('<Q',data,1048,123456)
 struct.pack_into('<III',data,1060,1,0,0);struct.pack_into('<I',data,1104,features)
 caps=struct.pack('<IIIII',0x02000001,capability,0,0,0)
 def inode(nid,mode,size,xattrs,inline=b'',uid=0,gid=0,layout=2):
  off=nid*32;count=1+(len(xattrs)-12)//4 if xattrs else 0
  struct.pack_into('<HHHHIIIIHHI',data,off,layout<<1,count,mode,1,size,0,0,nid,uid,gid,0)
  data[off+32:off+32+len(xattrs)]=xattrs;data[off+32+len(xattrs):off+32+len(xattrs)+len(inline)]=inline
 root_xattrs=struct.pack('<IB7s',0,0,b'\0'*7)+attr(b'selinux',label)
 file_xattrs=struct.pack('<IB7s',0,0,b'\0'*7)+attr(b'selinux',label)+attr(b'capability',caps)
 if shared:
  data[1536:1536+len(attr(b'selinux',label))]=attr(b'selinux',label)
  root_xattrs=struct.pack('<IB7sI',0,1,b'\0'*7,384)
 names=b'...file';directory=struct.pack('<QHBB',64,36,2,0)+struct.pack('<QHBB',64,37,2,0)+struct.pack('<QHBB',80,39,1,0)+names
 inode(64,stat.S_IFDIR|0o755,len(directory),root_xattrs,directory)
 inode(80,stat.S_IFREG|0o644,1234,file_xattrs,uid=42,gid=43,layout=3)
 return bytes(data)

class ErofsMetadataTests(unittest.TestCase):
 def snapshot(self,data):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'image.img';path.write_bytes(data)
   with m.ErofsMetadata(path) as reader:return reader.snapshot()
 def test_inline_and_shared_labels_and_capabilities_are_authoritative(self):
  for shared in [False,True]:
   with self.subTest(shared=shared):
    entries=self.snapshot(image(shared=shared))
    self.assertEqual({'','file'},set(entries));self.assertEqual(LABEL.decode(),entries['file']['selinux_label'])
    self.assertEqual(1,entries['file']['capabilities']);self.assertEqual((42,43,0o644),(entries['file']['uid'],entries['file']['gid'],entries['file']['mode']))
    self.assertEqual(LABEL.hex(),entries['']['xattrs']['security.selinux'])
 def test_extended_inode_uses_full_width_ownership_and_size(self):
  data=bytearray(image());offset=80*32;count=struct.unpack_from('<H',data,offset+2)[0];length=12+4*(count-1);body=bytes(data[offset+32:offset+32+length])
  data[offset:offset+64+length]=b'\0'*(64+length)
  struct.pack_into('<HHHHQIIIIQII16s',data,offset,7,count,stat.S_IFREG|0o644,0,2**32+123,0,80,70000,80000,123456,0,1,b'\0'*16)
  data[offset+64:offset+64+length]=body;entry=self.snapshot(bytes(data))['file']
  self.assertEqual((70000,80000,2**32+123),(entry['uid'],entry['gid'],entry['size']));self.assertEqual(1,entry['capabilities'])
 def test_changed_label_and_capability_fail_metadata_comparison(self):
  before=self.snapshot(image())
  for changed in [image(label=b'u:object_r:unlabeled:s0'),image(capability=2)]:
   with self.subTest(changed=hashlib.sha256(changed).hexdigest()):
    report=m.compare_metadata(before,self.snapshot(changed));self.assertFalse(report['passed']);self.assertTrue(report['changed_existing'])
 def test_unchanged_metadata_does_not_claim_file_byte_equality(self):
  entries=self.snapshot(image());report=m.compare_metadata(entries,entries)
  self.assertTrue(report['passed']);self.assertFalse(report['regular_file_contents_verified'])
 def test_truncation_unsupported_features_and_bad_shared_ids_fail(self):
  broken=bytearray(image(shared=True));struct.pack_into('<I',broken,64*32+32+12,0xffffffff)
  for data in [image()[:1100],image(features=64),bytes(broken)]:
   with self.subTest(size=len(data)),self.assertRaises(ValueError):self.snapshot(data)
 def test_expected_added_paths_must_match_labels_capabilities_and_modes(self):
  before=self.snapshot(image());after=dict(before);after['extra']=dict(before['file'])
  self.assertFalse(m.compare_metadata(before,after)['passed'])
  allowed={'extra':dict(after['extra'])};self.assertTrue(m.compare_metadata(before,after,allowed)['passed'])
  after['extra']=dict(after['extra'],mode=0o600)
  self.assertFalse(m.compare_metadata(before,after,allowed)['passed'])

class ProfileTests(unittest.TestCase):
 def test_profile_export_is_sanitized_and_bound_to_supplied_build(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);archive=root/'target.zip';out=root/'profile'
   with zipfile.ZipFile(archive,'w') as z:
    z.writestr('META/misc_info.txt','system_fs_type=erofs\nsystem_ext_fs_type=erofs\nproduct_fs_type=erofs\nerofs_default_compressor=lz4hc,12\nerofs_pcluster_size=65536\navb_vbmeta_key_path=/private/project/key.pem\n')
    z.writestr('META/file_contexts.bin',b'public compiled contexts')
    for part in m.PARTS:
     z.writestr('IMAGES/'+part+'.img',image())
     name='filesystem_config.txt' if part=='system' else part+'_filesystem_config.txt'
     z.writestr('META/'+name,' 0 0 755 capabilities=0x0\n')
   result=m.export_profile(archive,out,{p:8192 for p in m.PARTS})
   self.assertFalse(result['composition_ready']);self.assertFalse(result['owner_device_capture_used'])
   self.assertNotIn('/private/project',json.dumps(result));self.assertTrue(m.validate_profile(out)['passed'])
   profile_file=out/'profile.json';saved=profile_file.read_bytes();malformed=json.loads(saved);malformed['private_key']='/private/project/key.pem';profile_file.write_text(json.dumps(malformed))
   with self.assertRaises(ValueError):m.validate_profile(out)
   profile_file.write_bytes(saved)
   context=out/'metadata/file_contexts.bin';context.write_bytes(b'tampered')
   with self.assertRaises(ValueError):m.validate_profile(out)
 def test_fs_config_root_and_capability_masks_are_validated(self):
  rows=m.parse_fs_config(b' 0 0 755 selabel=u:object_r:rootfs:s0 capabilities=0x0\nproduct/bin/test 0 2000 755 capabilities=0x1\n')
  self.assertIn('',rows);self.assertEqual(1,rows['product/bin/test']['capabilities'])
  for data in [b'../bad 0 0 644\n',b'x true 0 644\n',b'x 0 0 999\n',b'x 0 0 644\nx 0 1 644\n',b'x 4294967296 0 644\n']:
   with self.subTest(data=data),self.assertRaises(ValueError):m.parse_fs_config(data)

class RecipeTests(unittest.TestCase):
 def fixture(self,root,bad_path=None,symlink=False):
  archive=root/'gapps.zip'
  with zipfile.ZipFile(archive,'w') as z:
   z.writestr('build.prop',b'arch=arm\nversion=34\nversion_nice=14.0.0\n')
   for n in range(27):
    name=bad_path if n==0 and bad_path else 'system/product/app/App'+str(n)+'.apk'
    info=zipfile.ZipInfo(name);info.external_attr=(stat.S_IFLNK|0o777)<<16 if n==0 and symlink else (stat.S_IFREG|0o644)<<16
    z.writestr(info,b'synthetic public test payload')
  return archive,{'format':1,'architecture':'arm','android_api':34,'variant':'ATV-minimal','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'filename':'gapps.zip','url':'https://example.invalid/gapps.zip'}
 def test_recipe_has_hashes_and_metadata_but_no_payload_bytes(self):
  with tempfile.TemporaryDirectory() as temp:
   archive,pin=self.fixture(Path(temp));r=m.export_recipe(archive,pin)
   self.assertEqual(27,len(r['entries']));self.assertNotIn('synthetic public test payload',json.dumps(r));m.validate_recipe(r)
   r['entries'][0]['image_path']='../escape'
   with self.assertRaises(ValueError):m.validate_recipe(r)
 def test_committed_recipe_matches_the_pinned_input_manifest(self):
  root=Path(__file__).resolve().parents[1];recipe=json.loads((root/'manifests/gapps-recipe.json').read_text());pin=json.loads((root/'manifests/gapps-input.json').read_text())
  m.validate_recipe(recipe)
  self.assertEqual({key:pin[key] for key in ['filename','bytes','sha256','url']},recipe['input'])
  self.assertEqual(pin['source_revision'],recipe['source_revision'])
  self.assertEqual({'system':2,'system_ext':3,'product':22},{part:sum(entry['partition']==part for entry in recipe['entries']) for part in m.PARTS})
 def test_recipe_rejects_wrong_zip_identity_paths_and_symlinks(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)
   for path,link in [(None,False),('system/product/../escape',False),(None,True)]:
    archive,pin=self.fixture(root,path,link)
    if path is None and not link:pin['sha256']='0'*64
    with self.subTest(path=path,link=link),self.assertRaises(ValueError):m.export_recipe(archive,pin)

class MetadataBoundaryTests(unittest.TestCase):
 def test_recipe_rejects_payload_fields_and_private_provenance_paths(self):
  helper=RecipeTests()
  with tempfile.TemporaryDirectory() as temp:
   archive,pin=helper.fixture(Path(temp));recipe=m.export_recipe(archive,pin)
   for field,value in [('data','payload bytes'),('private_key','/private/key.pem')]:
    modified=json.loads(json.dumps(recipe));modified['entries'][0][field]=value
    with self.subTest(field=field),self.assertRaises(ValueError):m.validate_recipe(modified)
   pin['filename']='/private/owner/gapps.zip'
   with self.assertRaises(ValueError):m.export_recipe(archive,pin)
   pin['filename']='gapps.zip';pin['url']='https://user:password@example.invalid/gapps.zip'
   with self.assertRaises(ValueError):m.export_recipe(archive,pin)
if __name__=='__main__':unittest.main()
