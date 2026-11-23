"""Real AVB regression fixtures; set JARVIS2_ANDROID_SOURCE to run tool integration."""
import hashlib,importlib.util,os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit_chain',ROOT/'tools/audit-avb-chain.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
SOURCE=os.environ.get('JARVIS2_ANDROID_SOURCE')
@unittest.skipUnless(SOURCE,'requires built Android avbtool and its source')
class AvbChainTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);cls.source=Path(SOURCE)
  cls.tool=cls.source/'out/host/linux-x86/bin/avbtool'
  for name in ('root','child','other'):
   key=cls.root/(name+'.pem')
   subprocess.run(['openssl','genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out',key],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   subprocess.run([cls.tool,'extract_public_key','--key',key,'--output',cls.root/(name+'.avbpubkey')],check=True)
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def fixture(self,base,child_signer='child'):
  base.mkdir()
  for name,key,extra in [('child',child_signer,[]),('vbmeta','root',['--chain_partition','child:1:'+str(self.root/'child.avbpubkey')])]:
   subprocess.run([self.tool,'make_vbmeta_image','--output',base/(name+'.img'),'--algorithm','SHA256_RSA2048','--key',self.root/(key+'.pem'),*extra],check=True)
 def test_valid_chain_checks_signatures_and_key_binding(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root/'images')
   report=module.audit(root/'images',self.source,root/'audit')
   self.assertTrue(report['parent_child_public_keys_match']);self.assertFalse(report['hardware_root_trust_verified'])
 def test_valid_but_wrong_child_signer_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root/'images','other')
   # Demonstrate the upstream follow option alone accepts this different key.
   subprocess.run([self.tool,'verify_image','--image',root/'images/vbmeta.img','--follow_chain_partitions'],check=True,stdout=subprocess.DEVNULL)
   with self.assertRaisesRegex(ValueError,'public key mismatch'):
    module.audit(root/'images',self.source,root/'audit')
 def test_corrupted_child_signature_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root/'images');p=root/'images/child.img'
   data=bytearray(p.read_bytes());data[256]^=1;p.write_bytes(data)
   with self.assertRaises(subprocess.CalledProcessError):module.audit(root/'images',self.source,root/'audit')
 def test_wrong_root_pin_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root/'images')
   with self.assertRaisesRegex(ValueError,'root key'):
    module.audit(root/'images',self.source,root/'audit','0'*64)
 def test_unsigned_root_is_not_reported_as_signed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);images=root/'images';images.mkdir()
   subprocess.run([self.tool,'make_vbmeta_image','--output',images/'vbmeta.img','--algorithm','NONE'],check=True)
   with self.assertRaisesRegex(ValueError,'signed'):
    module.audit(images,self.source,root/'audit')
