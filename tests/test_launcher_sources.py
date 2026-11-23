import importlib.util,tempfile,unittest,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('launcher_sources',ROOT/'tools/collect-launcher-sources.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class LauncherSourceTests(unittest.TestCase):
 def test_cache_checksum_mismatch_fails_without_downloading(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);(out/'example-1.2.3.tar.gz').write_bytes(b'changed')
   info={'source':'hosted','version':'1.2.3','description':{'sha256':hashlib.sha256(b'original').hexdigest(),'url':'https://pub.dev'}}
   with self.assertRaisesRegex(ValueError,'checksum'):
    module.collect_one('example',info,out,download=False)
 def test_verified_cached_archive_is_recorded(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);data=b'source archive fixture';(out/'example-1.2.3.tar.gz').write_bytes(data)
   info={'source':'hosted','version':'1.2.3','description':{'sha256':hashlib.sha256(data).hexdigest(),'url':'https://pub.dev'}}
   result=module.collect_one('example',info,out,download=False)
   self.assertEqual(len(data),result['bytes']);self.assertEqual(info['description']['sha256'],result['sha256'])
 def test_unexpected_source_or_path_cannot_escape_archive_directory(self):
  with tempfile.TemporaryDirectory() as d:
   for name,info in [('../escape',{'source':'hosted','version':'1.0','description':{}}),('example',{'source':'git','version':'1.0'})]:
    with self.subTest(name=name),self.assertRaises(ValueError):module.collect_one(name,info,Path(d),False)
 def test_sdk_dependencies_are_explicitly_not_claimed_collected(self):
  with tempfile.TemporaryDirectory() as d:
   result=module.collect_one('flutter',{'source':'sdk','version':'0.0.0'},Path(d),False)
   self.assertFalse(result['collected']);self.assertEqual('sdk',result['source'])
