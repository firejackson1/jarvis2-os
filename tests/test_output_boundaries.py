import importlib.util,subprocess,tempfile,unittest,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('patch_verify',ROOT/'tools/verify-patches.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class OutputBoundaryTests(unittest.TestCase):
 def test_app_output_in_other_repo_directory_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'android';src.mkdir();keys=Path(d)/'keys';keys.mkdir();target=Path(d)/'target.apk';target.write_bytes(b'fixture')
   out=ROOT/'tools'/('must-not-be-created-'+uuid.uuid4().hex)
   r=subprocess.run([ROOT/'tools/build-apps.sh',src,target,keys,out],capture_output=True,text=True)
   self.assertEqual(2,r.returncode);self.assertIn('Output must be outside',r.stderr);self.assertFalse(out.exists())
 def test_patch_output_in_android_tree_is_rejected_before_git_access(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'android';src.mkdir();out=src/'output'
   with self.assertRaisesRegex(ValueError,'outside'):
    module.verify(src,out)
   self.assertFalse(out.exists())
