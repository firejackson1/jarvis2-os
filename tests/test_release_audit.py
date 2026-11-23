import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('release_audit',Path(__file__).resolve().parents[1]/'tools/release_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
class AuditTests(unittest.TestCase):
 def test_private_material_rejected_without_echoing_it(self):
  examples=[('key.pem',b'dummy','forbidden-artifact'),('a.txt',b'-----BEGIN '+b'PRIVATE KEY-----','private-key'),('a.txt',':'.join(['ab']*6).encode(),'device-address'),('a.txt',('10'+'.9.8.7').encode(),'private-address'),('a.txt',b'JUSA'+b'123456789','device-serial'),('a.txt',b'PRODUCT_ADB_KEYS := owner.pub','trusted-adb-key'),('a.txt',b'/home/'+b'jedi/project','owner-path'),('image.img',b'\0binary','binary-content')]
  for name,data,issue in examples:
   with self.subTest(issue=issue):self.assertIn(issue,audit.check_file(Path(name),data))
 def test_documentation_and_public_urls_allowed(self):
  self.assertEqual([],audit.check_file(Path('README.md'),b'https://github.com/LineageOS/android\nhttps://ha.example.org\n192.0.2.10'))
