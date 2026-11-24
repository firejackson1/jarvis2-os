# SPDX-License-Identifier: Apache-2.0
import importlib.util,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('assembler',ROOT/'tools/assemble-avb-images.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class RawPayloadTests(unittest.TestCase):
 def raw(self,path,blocks=1):
  data=bytearray(blocks*4096);struct.pack_into('<I',data,1024,0xe0f5e1e2);data[1036]=12;struct.pack_into('<I',data,1060,blocks);path.write_bytes(data);return path
 def test_raw_geometry_exact_length(self):
  with tempfile.TemporaryDirectory() as t:
   p=self.raw(Path(t)/'raw.img');self.assertEqual(4096,m.validate_raw(p)['filesystem_bytes'])
   for data in [p.read_bytes()[:-1],p.read_bytes()+b'\0'*4096]:
    p.write_bytes(data)
    with self.assertRaises(ValueError):m.validate_raw(p)
 def test_sparse_footer_and_wrong_formats_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'raw.img'
   for data in [b'\x3a\xff\x26\xed'+b'\0'*4092,b'AVB0'+b'\0'*4092,b'junk']:
    p.write_bytes(data)
    with self.subTest(magic=data[:4]),self.assertRaises(ValueError):m.validate_raw(p)
   self.raw(p);data=bytearray(p.read_bytes());data[-64:-60]=b'AVBf';p.write_bytes(data)
   with self.assertRaises(ValueError):m.validate_raw(p)
 def test_symlink_and_symlink_parent_inputs_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);folder=root/'real';folder.mkdir();self.raw(folder/'raw.img');(root/'alias').symlink_to(folder,target_is_directory=True);(root/'file').symlink_to(folder/'raw.img')
   for p in [root/'file',root/'alias/raw.img']:
    with self.subTest(path=p),self.assertRaises(ValueError):m.strict_file(p)
 def test_input_sets_cannot_alias_same_file(self):
  with tempfile.TemporaryDirectory() as t:
   p=self.raw(Path(t)/'raw.img');q=Path(t)/'hardlink.img';q.hardlink_to(p)
   with self.assertRaises(ValueError):m.distinct_files({'one':p,'two':q})
 def test_existing_output_and_input_tree_output_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);source=root/'source';source.mkdir()
   with self.assertRaises(ValueError):m.C.check_output(source/'out',[source])
   with self.assertRaises(FileExistsError):m.C.check_output(source,[])
 def test_footer_command_preserves_policy(self):
  from types import SimpleNamespace
  h=SimpleNamespace(rollback_index=7,flags=0,release_string='keep')
  tree=SimpleNamespace(hash_algorithm='sha512',salt=b'\xab',fec_num_roots=2)
  cmd=m.footer_command(Path('/tool'),Path('/image'),'system',100000,h,tree,[],object())
  for pair in [('--partition_size','100000'),('--salt','ab'),('--hash_algorithm','sha512'),('--rollback_index','7'),('--internal_release_string','keep'),('--fec_num_roots','2'),('--block_size','4096')]:self.assertEqual(pair[1],cmd[cmd.index(pair[0])+1])

if __name__=='__main__':unittest.main()
