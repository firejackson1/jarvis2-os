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
