# SPDX-License-Identifier: Apache-2.0
import hashlib,importlib.util,json,os,tempfile,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'tools/verify-apex-filesystems.py';s=importlib.util.spec_from_file_location('fsverify',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FilesystemProofTests(unittest.TestCase):
 def test_native_unused_directory_slots_are_not_live_paths(self):
  text='/2/040755/1000/1000/.//\n/2/040755/1000/1000/..//\n/0/000000/0/0//0/\n/0/000000/0/0//0/\n'
  self.assertEqual({'.'},set(m.parse_ls(text,'.')))
 def test_nonzero_or_named_empty_slots_fail_closed(self):
  for row in ['/1/000000/0/0//0/','/0/100644/0/0/name/0/','/0/000000/1/0//0/']:
   with self.subTest(row=row),self.assertRaises(ValueError):m.parse_ls(row,'.')
 def test_walk_never_follows_directory_or_file_symlinks(self):
  with tempfile.TemporaryDirectory() as temp:
   parent=Path(temp);tree=parent/'tree';tree.mkdir();outside=parent/'outside';outside.mkdir();(outside/'secret').write_text('not traversed')
   (tree/'directory-link').symlink_to(outside,target_is_directory=True);(tree/'file-link').symlink_to(outside/'secret');(tree/'file').write_bytes(b'actual')
   result=m.walk_extracted(tree)
   self.assertEqual({'.','directory-link','file-link','file'},set(result))
   self.assertEqual('symlink',result['directory-link']['type']);self.assertNotIn('sha256',result['file-link'])
 def test_unpinned_prior_report_cannot_transfer_a_trust_claim(self):
  proof={'status':'passed','archive_sha256':{'original':'0'*64,'signed':'1'*64},'embedded_apks':[],
         'public_inventory_trust':{'mode':'caller-pinned-public-inventory','caller_inventory_pin_verified':True,'inventory_sha256':'2'*64,'hardware_root_of_trust_verified':False}}
  data=json.dumps(proof).encode()
  _,trust=m.validate_package_proof(data)
  self.assertEqual('internal-consistency-only',trust['mode']);self.assertFalse(trust['caller_inventory_pin_verified'])
  _,trust=m.validate_package_proof(data,hashlib.sha256(data).hexdigest())
  self.assertTrue(trust['caller_inventory_pin_verified']);self.assertTrue(trust['prior_package_report_pin_verified'])
  with self.assertRaises(ValueError):m.validate_package_proof(data,'0'*64)
if __name__=='__main__':unittest.main()
