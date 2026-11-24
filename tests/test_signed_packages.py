"""Focused content-comparison regressions; not a universal verifier schema suite."""
# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SOURCE=Path(__file__).resolve().parents[1]/'tools/verify-signed-packages.py'
spec=importlib.util.spec_from_file_location('signed_packages',SOURCE)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
content=module.apk_content

def archive(entries):
 output=io.BytesIO()
 with zipfile.ZipFile(output,'w') as z:
  for name,data in entries.items():z.writestr(name,data)
 return output.getvalue()

class ContentComparisonTests(unittest.TestCase):
 def test_jar_signing_artifact_changes_are_expected(self):
  for name in ['META-INF/MANIFEST.MF','META-INF/CERT.SF','META-INF/CERT.RSA','META-INF/CERT.DSA','META-INF/CERT.EC','META-INF/SIG-CUSTOM','META-INF/SIG-CUSTOM.A1']:
   with self.subTest(name=name):
    before={'classes.dex':b'code',name:b'old signature'}
    after=dict(before);after[name]=b'new signature'
    self.assertEqual(content(archive(before)),content(archive(after)))
 def test_notice_license_services_and_nested_signature_names_are_compared(self):
  for name in ['META-INF/LICENSE','META-INF/LICENSE.txt','META-INF/NOTICE','META-INF/NOTICE.txt','META-INF/services/com.example.Service','META-INF/versions/9/NOTICE','META-INF/nested/CERT.SF','META-INF/nested/CERT.RSA','META-INF/CERT.SF.txt','META-INF/MANIFEST.MF.backup','assets/META-INF/CERT.RSA']:
   with self.subTest(name=name):
    before={'classes.dex':b'code',name:b'original metadata'}
    after=dict(before);after[name]=b'tampered metadata'
    self.assertNotEqual(content(archive(before)),content(archive(after)))
 def test_metadata_addition_and_removal_are_detected(self):
  for name in ['META-INF/LICENSE','META-INF/services/Service']:
   with self.subTest(name=name):
    self.assertNotEqual(content(archive({'classes.dex':b'code'})),content(archive({'classes.dex':b'code',name:b'metadata'})))
 def test_regular_payload_changes_are_detected(self):
  self.assertNotEqual(content(archive({'AndroidManifest.xml':b'old'})),content(archive({'AndroidManifest.xml':b'new'})))


class PublicBoundaryTests(unittest.TestCase):
 def test_public_material_paths_cannot_escape_or_follow_symlinks(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'keys').mkdir();(root/'keys/key.public.pem').write_text('public')
   self.assertEqual(root/'keys/key.public.pem',module.public_file(root,'keys/key','.public.pem'))
   (root/'link').symlink_to(root/'keys',target_is_directory=True)
   for base in ['../keys/key','/keys/key','keys/../keys/key','link/key']:
    with self.subTest(base=base),self.assertRaises(ValueError):module.public_file(root,base,'.public.pem')
   with self.assertRaises(ValueError):module.public_file(root,'keys/key','.pk8')
 def test_inventory_pin_is_optional_and_explicit(self):
  data=b'{"format":1,"keys":[{"role":"apk","identity":"dev/key","key_base":"keys/release","public_spki_sha256":"'+b'0'*64+b'","certificate_sha256":"'+b'1'*64+b'"}]}'
  rolemap={'format':1,'keys':[{'role':'apk','identity':'dev/key','key_base':'keys/release'}]}
  _,trust=module.validate_inventory(data,rolemap)
  self.assertEqual('internal-consistency-only',trust['mode']);self.assertFalse(trust['caller_inventory_pin_verified'])
  _,trust=module.validate_inventory(data,rolemap,hashlib.sha256(data).hexdigest())
  self.assertEqual('caller-pinned-public-inventory',trust['mode']);self.assertTrue(trust['caller_inventory_pin_verified'])
  for pin in ['0'*64,'bad']:
   with self.subTest(pin=pin),self.assertRaises(ValueError):module.validate_inventory(data,rolemap,pin)
 def test_inventory_conflicts_private_paths_and_bad_digests_are_rejected(self):
  row={'role':'apk','identity':'dev/key','key_base':'keys/release','public_spki_sha256':'0'*64,'certificate_sha256':'1'*64}
  rolemap={'format':1,'keys':[{k:row[k] for k in ['role','identity','key_base']}]}
  mutations=[dict(row,key_base='../private/key'),dict(row,public_spki_sha256='invalid'),dict(row,private_key='private.pem'),dict(row,role='unknown')]
  for entry in mutations:
   with self.subTest(entry=entry),self.assertRaises(ValueError):module.validate_inventory(json.dumps({'format':1,'keys':[entry]}).encode(),rolemap)
  with self.assertRaises(ValueError):module.validate_inventory(json.dumps({'format':1,'keys':[row,row]}).encode(),rolemap)
 def test_requested_jdk_overrides_inherited_java_home_without_clearing_environment(self):
  with patch.dict(module.os.environ,{'JAVA_HOME':'/invalid','JARVIS2_KEEP_TEST':'preserved'}):
   env=module.verification_environment(Path('/requested-jdk'),Path('/host'),Path('/soong-host'),Path('/temporary'))
   self.assertEqual('/requested-jdk',env['JAVA_HOME'])
   self.assertEqual('preserved',env['JARVIS2_KEEP_TEST'])
   self.assertTrue(env['PATH'].startswith('/requested-jdk/bin:'))
   self.assertEqual('/invalid',module.os.environ['JAVA_HOME'])
 def test_duplicate_json_fields_are_rejected(self):
  with self.assertRaisesRegex(ValueError,'Duplicate JSON field'):
   module.load_json_unique(b'{"format":1,"format":1,"keys":[]}')
 def test_metadata_parser_rejects_malformed_fields_and_conflicts(self):
  good='name="App.apk" certificate="dev/key.x509.pem" private_key="dev/key.pk8" partition="system"'
  for text in [good+' garbage',good+' partition="system"',good+'\n'+good.replace('dev/key','other/key')]:
   with self.subTest(text=text),self.assertRaises(ValueError):module.rows(text.encode())

class PayloadOutputTests(unittest.TestCase):
 def test_vbmeta_signature_alone_cannot_claim_payload_content_verified(self):
  path=Path('/temporary/payload.img')
  with self.assertRaises(ValueError):module.require_payload_content_verification('vbmeta: Successfully verified footer and signed vbmeta struct',path)
  module.require_payload_content_verification(': Successfully verified sha256 hashtree of /temporary/payload.img for image of 4096 bytes\n',path)
  with self.assertRaises(ValueError):module.require_payload_content_verification(': Successfully verified sha256 hash of /different/payload.img for image of 4096 bytes\n',path)

if __name__=='__main__':unittest.main()
