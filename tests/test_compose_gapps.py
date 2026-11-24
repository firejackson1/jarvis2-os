# SPDX-License-Identifier: Apache-2.0
import hashlib,importlib.util,json,os,tempfile,unittest
from types import SimpleNamespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('compose_gapps',ROOT/'tools/compose-gapps.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class ComposerBoundaryTests(unittest.TestCase):
 def test_output_cannot_be_in_repository_or_input_trees(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);source=root/'input';source.mkdir()
   for output in [ROOT/'forbidden-output',source/'output']:
    with self.subTest(output=output),self.assertRaises(ValueError):m.check_output(output,[source])
   m.check_output(root/'fresh',[source]);(root/'existing').mkdir()
   with self.assertRaises(FileExistsError):m.check_output(root/'existing',[source])
 def test_staging_destination_never_traverses_symlinks(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);outside=root/'outside';outside.mkdir();tree=root/'tree';tree.mkdir();(tree/'link').symlink_to(outside,target_is_directory=True)
   for name in ['../escape','link/escape','/absolute']:
    with self.subTest(name=name),self.assertRaises(ValueError):m.destination(tree,name)
   self.assertFalse((outside/'escape').exists())
 def test_content_walk_does_not_follow_symlinks_and_detects_bytes(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);tree=root/'tree';tree.mkdir();other=root/'other';other.mkdir();(other/'hidden').write_bytes(b'outside');(tree/'link').symlink_to(other,target_is_directory=True);(tree/'file').write_bytes(b'before')
   before=m.content_snapshot(tree);self.assertNotIn('link/hidden',before);self.assertEqual('symlink',before['link']['type'])
   (tree/'file').write_bytes(b'after');self.assertNotEqual(before,m.content_snapshot(tree))
 def test_content_comparison_allows_only_exact_recipe_additions(self):
  before={'':{'type':'directory'},'old':{'type':'file','bytes':1,'sha256':'0'*64}}
  after=dict(before,new={'type':'file','bytes':2,'sha256':'1'*64},folder={'type':'directory'})
  expected={'new':{'bytes':2,'sha256':'1'*64}}
  m.verify_content(before,after,expected,{'new','folder'})
  for changed in [dict(after,old={'type':'file','bytes':1,'sha256':'2'*64}),dict(after,extra={'type':'file','bytes':1,'sha256':'3'*64}),dict(after,new={'type':'file','bytes':2,'sha256':'4'*64})]:
   with self.subTest(changed=changed),self.assertRaises(ValueError):m.verify_content(before,changed,expected,{'new','folder'})
 def test_root_rekey_requires_explicit_permission_and_output_pin(self):
  m.validate_root_policy('a'*64,'a'*64,'a'*64,False)
  with self.assertRaises(ValueError):m.validate_root_policy('a'*64,'b'*64,'b'*64,False)
  with self.assertRaises(ValueError):m.validate_root_policy('a'*64,'b'*64,'c'*64,True)
  m.validate_root_policy('a'*64,'b'*64,'b'*64,True)
 def test_policy_pin_mismatch_fails_before_using_policy(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'policy.json';path.write_text('{}')
   with self.assertRaises(ValueError):m.pinned_json(path,'0'*64)
   self.assertEqual({},m.pinned_json(path,m.PROFILE.digest(path)))
 def test_non4096_avb_tree_geometry_is_rejected(self):
  m.require_tree_geometry(SimpleNamespace(data_block_size=4096,hash_block_size=4096))
  for data,hashed in [(512,4096),(4096,512),(8192,8192)]:
   with self.subTest(data=data,hashed=hashed),self.assertRaises(ValueError):m.require_tree_geometry(SimpleNamespace(data_block_size=data,hash_block_size=hashed))
 def test_prefix_digest_rejects_truncation_instead_of_looping(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'image.img';path.write_bytes(b'abc')
   self.assertEqual(hashlib.sha256(b'abc').hexdigest(),m.prefix_digest(path,3))
   with self.assertRaises(ValueError):m.prefix_digest(path,4)
 def test_all_five_baseline_hashes_include_both_vbmeta_inputs(self):
  with tempfile.TemporaryDirectory() as temp:
   images={name:Path(temp)/(name+'.img') for name in ['system','system_ext','product','vbmeta','vbmeta_system']}
   for path in images.values():path.write_bytes(b'unchanged')
   expected={name:m.PROFILE.digest(path) for name,path in images.items()};m.verify_input_hashes(images,expected)
   for name in ['vbmeta','vbmeta_system']:
    images[name].write_bytes(b'changed')
    with self.subTest(name=name),self.assertRaises(ValueError):m.verify_input_hashes(images,expected)
    images[name].write_bytes(b'unchanged')
 def test_presigned_google_hash_recipe_remains_valid(self):
  recipe=json.loads((ROOT/'manifests/gapps-recipe.json').read_text());m.PROFILE.validate_recipe(recipe)
  self.assertEqual(27,len(recipe['entries']))

if __name__=='__main__':unittest.main()
