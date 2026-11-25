# SPDX-License-Identifier: Apache-2.0
import hashlib,importlib.util,os,struct,subprocess,tempfile,unittest
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

class StockPolicyTests(unittest.TestCase):
 def test_profile_rejects_bool_sizes_extra_keys_and_wrong_digest(self):
  import copy
  profile={'format':1,'templates':{p:{'sha256':'a'*64,'bytes':65536} for p in ['vbmeta','vbmeta_system']},'references':{'boot':{'sha256':'b'*64,'bytes':131072}},'output_bytes':{p:33554432 for p in ['system','system_ext','product'] } | {'vbmeta':65536,'vbmeta_system':65536},'leaf_release_string':'fixture-reviewed','unbound_references':[]}
  m.validate_stock_profile(profile)
  for mutate in [lambda p:p['output_bytes'].update(system=True),lambda p:p['templates']['vbmeta'].update(sha256='z'*64),lambda p:p.update(extra=True),lambda p:p.update(unbound_references=['boot','boot']),lambda p:p.update(unbound_references=['unknown']),lambda p:p['references'].update({'../bad':{'sha256':'a'*64,'bytes':1}})]:
   bad=copy.deepcopy(profile);mutate(bad)
   with self.assertRaises(ValueError):m.validate_stock_profile(bad)
 def test_reference_coverage_accepts_only_explicit_unbound(self):
  m.validate_reference_coverage({'boot'},{'boot','unused'},['unused'])
  for used,refs,unbound in [({'boot'},{'boot','extra'},[]),({'boot'},{'boot'},['boot']),({'boot','unknown'},{'boot'},[])]:
   with self.subTest(used=used),self.assertRaises(ValueError):m.validate_reference_coverage(used,refs,unbound)
 def test_build_properties_duplicates_and_missing_source_fail_closed(self):
  self.assertEqual({'a':'b'},m.parse_build_properties('#comment\na=b\n'))
  for text in ['a=b\na=c\n','bad line','a=x\x00']:
   with self.assertRaises(ValueError):m.parse_build_properties(text)
  values={p:{'ro.'+p+'.build.fingerprint':'new/'+p+':release-keys','ro.'+p+'.build.version.release':'14'} for p in m.PARTS};values['system']['ro.build.version.security_patch']='2026-11-01'
  result=m.desired_properties(values);self.assertEqual(9,len(result));self.assertEqual(b'2026-11-01',result['com.android.build.product.security_patch'])
  del values['system_ext']['ro.system_ext.build.fingerprint']
  with self.assertRaises(ValueError):m.desired_properties(values)
 def test_rewrite_changes_only_allowed_properties_and_rejects_duplicates(self):
  from types import SimpleNamespace
  class Property:
   def __init__(self,key=None,value=None):self.key=key;self.value=value
  avb=SimpleNamespace(AvbPropertyDescriptor=Property)
  values={'com.android.build.system.'+k:v for k,v in [('fingerprint',b'new'),('os_version',b'14'),('security_patch',b'2026-11-01')]}
  original=[Property('bootstrap',b'unchanged'),Property('com.android.build.system.fingerprint',b'old')]
  new=m.rewrite_properties(original,values,{'system'},avb);self.assertEqual(b'unchanged',new[0].value);self.assertEqual(b'new',new[1].value);self.assertEqual(b'old',original[1].value);self.assertEqual(4,len(new))
  with self.assertRaises(ValueError):m.rewrite_properties(original+[original[1]],values,{'system'},avb)
  with self.assertRaises(ValueError):m.rewrite_properties(original,values,{'product'},avb)


@unittest.skipUnless(os.environ.get('JARVIS2_ANDROID_SOURCE'), 'requires pinned Android avbtool')
class RecoveryBindingTests(unittest.TestCase):
 def test_recovery_leaf_replaces_only_matching_stock_root_hash(self):
  android = Path(os.environ['JARVIS2_ANDROID_SOURCE'])
  avbtool = m.C.load_module('assembler_fixture_avb', android/'external/avb/avbtool.py')
  tool = android/'out/host/linux-x86/bin/avbtool'

  def make_leaf(path, payload, salt='aabb'):
   path.write_bytes(payload.ljust(4096, b'\0'))
   subprocess.run([tool, 'add_hash_footer', '--image', path, '--partition_name', 'vendor_boot',
                   '--partition_size', '131072', '--hash_algorithm', 'sha256', '--salt', salt,
                   '--prop', 'com.android.build.vendor_boot.fingerprint:stock',
                   '--algorithm', 'NONE'], check=True, capture_output=True)

  with tempfile.TemporaryDirectory() as temporary:
   root = Path(temporary)
   stock, replacement = root/'stock.img', root/'replacement.img'
   make_leaf(stock, b'original recovery')
   make_leaf(replacement, b'local LCARS recovery')
   image = avbtool.ImageHandler(str(stock), read_only=True)
   try:
    original = next(d for d in avbtool.Avb()._parse_image(image)[2]
                    if isinstance(d, avbtool.AvbHashDescriptor))
   finally:
    image._image.close()
   digest = m.PROFILE.digest(replacement)
   descriptor = m.recovery_hash_for_root(avbtool, [original], stock, replacement, digest)
   self.assertEqual(descriptor.partition_name, 'vendor_boot')
   expected_payload = b'local LCARS recovery'.ljust(4096, b'\0')
   self.assertEqual(descriptor.digest, hashlib.sha256(bytes.fromhex('aabb') + expected_payload).digest())
   self.assertNotEqual(descriptor.digest, original.digest)
   with self.assertRaisesRegex(ValueError, 'pin'):
    m.recovery_hash_for_root(avbtool, [original], stock, replacement, '0'*64)
   with self.assertRaisesRegex(ValueError, 'root'):
    m.recovery_hash_for_root(avbtool, [], stock, replacement, digest)
   make_leaf(replacement, b'local LCARS recovery', salt='ccdd')
   with self.assertRaisesRegex(ValueError, 'hash policy'):
    m.recovery_hash_for_root(avbtool, [original], stock, replacement, m.PROFILE.digest(replacement))
   make_leaf(replacement, b'local LCARS recovery')
   with replacement.open('r+b') as stream:
    stream.write(b'X')
   with self.assertRaisesRegex(ValueError, 'payload hash'):
    m.recovery_hash_for_root(avbtool, [original], stock, replacement, m.PROFILE.digest(replacement))

if __name__=='__main__':unittest.main()
