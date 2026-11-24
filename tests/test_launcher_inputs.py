import hashlib,importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('launcher_inputs',ROOT/'tools/prepare-launcher.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class LauncherInputsTests(unittest.TestCase):
 def test_wrong_hash_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'input';p.write_bytes(b'changed input')
   with self.assertRaises(ValueError):module.verify_hash(p,hashlib.sha256(b'expected input').hexdigest())
 def test_matching_hash_is_accepted(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'input';p.write_bytes(b'expected input')
   module.verify_hash(p,hashlib.sha256(p.read_bytes()).hexdigest())
 def test_notices_are_preserved_for_android_license_packaging(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);inputs=root/'inputs';out=root/'stage';inputs.mkdir()
   expected={'LICENSE.txt':b'upstream copyleft terms','NOTICES.txt':b'third party notices'}
   for name,data in expected.items():(inputs/('LTvLauncher-'+name)).write_bytes(data)
   module.stage_notices(inputs,out)
   for name,data in expected.items():self.assertEqual(data,(out/name).read_bytes())

 def test_local_only_input_never_attempts_download(self):
  with tempfile.TemporaryDirectory() as d:
   from unittest.mock import patch
   with patch.object(module.urllib.request,'urlopen') as fetch:
    with self.assertRaisesRegex(FileNotFoundError,'controlled.*local|local.*controlled'):
     module.prepare(Path(d)/'inputs',Path(d)/'android',download=True)
    fetch.assert_not_called()
 def test_manifest_pins_controlled_source_candidate(self):
  import json
  manifest=json.loads((ROOT/'manifests/launcher-inputs.json').read_text())
  candidate=json.loads((ROOT/'manifests/launcher-source-bundle.json').read_text())
  apk=next(x for x in manifest['artifacts'] if x['name']=='LTvLauncher.apk')
  self.assertEqual(candidate['signed_apk_sha256'],apk['sha256'])
  self.assertIsNone(apk['url'])
  self.assertEqual('controlled-project-build',manifest['build_origin'])
