import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('image_verify',ROOT/'tools/verify-images.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ImageChecksTests(unittest.TestCase):
 def test_missing_staging_roots_cannot_pass_packaging_checks(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'staging'):
    module.check(Path(d),{},Path('/unused/avbtool'))
