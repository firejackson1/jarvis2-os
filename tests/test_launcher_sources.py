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
 def test_leading_underscore_is_valid_for_dart_package(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);data=b'dart internal package';(out/'_internal-1.0.0.tar.gz').write_bytes(data)
   info={'source':'hosted','version':'1.0.0','description':{'sha256':hashlib.sha256(data).hexdigest(),'url':'https://pub.dev'}}
   self.assertTrue(module.collect_one('_internal',info,out,False)['collected'])
 def sdk_fixture(self,root):
  import io,tarfile
  archive=root/'framework.tar.gz'
  with tarfile.open(archive,'w:gz') as t:
   data=b'name: flutter\n';info=tarfile.TarInfo('framework-fixture/packages/flutter/pubspec.yaml');info.size=len(data);t.addfile(info,io.BytesIO(data))
  return {'framework_source':{'name':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'prefix':'framework-fixture','source_commit':'fixture','packages':['flutter']}}
 def test_sdk_package_is_covered_only_by_verified_archive_member(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.sdk_fixture(root)
   result=module.sdk_material(root,manifest)
   self.assertEqual('packages/flutter',result['flutter']['path']);self.assertTrue(result['flutter']['collected'])
   self.assertNotIn('sky_engine',result)
 def test_changed_sdk_archive_cannot_be_claimed_collected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.sdk_fixture(root);(root/'framework.tar.gz').write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'checksum'):module.sdk_material(root,manifest)
 def test_missing_sdk_archive_remains_uncollected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.sdk_fixture(root);(root/'framework.tar.gz').unlink()
   self.assertEqual({},module.sdk_material(root,manifest))

 def sky_fixture(self,root,omit=None,extra=None):
  import zipfile
  archive=root/'sky.zip'
  members={'sky_engine/pubspec.yaml':b'name: sky_engine\nversion: 0.0.99\n','LICENSE.zip_old_location.md':b'License moved into sky_engine', 'sky_engine/LICENSE':b'L'*1690268,'sky_engine/lib/ui/ui.dart':b'library dart.ui;'}
  if omit:members.pop(omit)
  if extra:members[extra]=b'unsafe'
  with zipfile.ZipFile(archive,'w') as z:
   for name,data in members.items():z.writestr(name,data)
  manifest=self.sdk_fixture(root);manifest['framework_source']['engine_revision']='a'*40
  manifest['sky_engine_source']={'name':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'engine_revision':'a'*40,'version':'0.0.99'}
  return manifest
 def test_generated_sky_package_is_verified_separately_from_engine_closure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.sky_fixture(root);result=module.sdk_material(root,manifest)['sky_engine']
   self.assertTrue(result['collected']);self.assertEqual('sky_engine',result['path'])
   self.assertEqual('generated_sdk_package',result['material_kind']);self.assertFalse(result['engine_dependency_closure_complete'])
 def test_sky_checksum_and_revision_mismatch_are_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.sky_fixture(root);manifest['sky_engine_source']['engine_revision']='b'*40
   with self.assertRaisesRegex(ValueError,'revision'):module.sdk_material(root,manifest)
   manifest['sky_engine_source']['engine_revision']='a'*40;manifest['sky_engine_source']['sha256']='0'*64
   with self.assertRaisesRegex(ValueError,'checksum'):module.sdk_material(root,manifest)
 def test_sky_requires_package_license_and_generated_ui_members(self):
  for missing in ['sky_engine/pubspec.yaml','sky_engine/LICENSE','sky_engine/lib/ui/ui.dart']:
   with self.subTest(missing=missing),tempfile.TemporaryDirectory() as d:
    root=Path(d);manifest=self.sky_fixture(root,omit=missing)
    with self.assertRaisesRegex(ValueError,'Missing'):module.sdk_material(root,manifest)
 def test_sky_rejects_unsafe_zip_members(self):
  for unsafe in ['../escape','/escape','sky_engine/../escape',r'sky_engine\escape']:
   with self.subTest(unsafe=unsafe),tempfile.TemporaryDirectory() as d:
    root=Path(d);manifest=self.sky_fixture(root,extra=unsafe)
    with self.assertRaisesRegex(ValueError,'Unsafe'):module.sdk_material(root,manifest)
 def test_missing_sky_archive_remains_uncollected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);manifest=self.sky_fixture(root);(root/'sky.zip').unlink()
   self.assertNotIn('sky_engine',module.sdk_material(root,manifest))

 def test_sky_package_identity_must_match(self):
  import zipfile
  for marker in [b'name: other\nversion: 0.0.99\n',b'name: sky_engine\nversion: 1.0.0\n']:
   with self.subTest(marker=marker),tempfile.TemporaryDirectory() as d:
    root=Path(d);manifest=self.sky_fixture(root)
    with zipfile.ZipFile(root/'sky.zip','w') as z:
     z.writestr('sky_engine/pubspec.yaml',marker);z.writestr('sky_engine/LICENSE',b'license');z.writestr('sky_engine/lib/ui/ui.dart',b'library dart.ui;')
    manifest['sky_engine_source']['sha256']=hashlib.sha256((root/'sky.zip').read_bytes()).hexdigest()
    with self.assertRaisesRegex(ValueError,'identity'):module.sdk_material(root,manifest)
