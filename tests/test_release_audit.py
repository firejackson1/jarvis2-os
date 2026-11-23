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

class GitCandidateTests(unittest.TestCase):
 def test_deleted_working_file_is_not_a_read_failure(self):
  import tempfile,subprocess
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);subprocess.run(['git','init','-q',d],check=True)
   f=root/'a.txt';f.write_text('public text')
   subprocess.run(['git','-C',d,'add','a.txt'],check=True);f.unlink()
   self.assertEqual([],audit.audit(root))
 def test_index_audit_checks_staged_content_not_worktree(self):
  import tempfile,subprocess
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);subprocess.run(['git','init','-q',d],check=True)
   f=root/'a.txt';f.write_bytes(b'-----BEGIN '+b'PRIVATE KEY-----')
   subprocess.run(['git','-C',d,'add','a.txt'],check=True);f.write_text('public text')
   self.assertIn(('a.txt','private-key'),audit.audit(root,staged=True))

class HistoricalAuditTests(unittest.TestCase):
 def test_adb_trust_filename_rejected_even_without_private_key_header(self):
  self.assertIn('forbidden-artifact',audit.check_file(Path('adb_keys'),b'base64_public_debug_identity'))
 def test_removed_secret_is_still_detected_in_history(self):
  import tempfile,subprocess
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   def git(*args):return subprocess.run(['git','-C',d,*args],check=True,stdout=subprocess.DEVNULL)
   git('init','-q');git('config','user.name','Test Author');git('config','user.email','test@example.org')
   f=root/'old.txt';f.write_bytes(b'-----BEGIN '+b'PRIVATE KEY-----')
   git('add','.');git('commit','-qm','initial fixture');f.unlink();git('add','-u');git('commit','-qm','remove fixture')
   self.assertTrue(any(issue=='private-key' for _,issue in audit.audit(root,history=True)))
