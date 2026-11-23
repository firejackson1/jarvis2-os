import importlib.util,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('boot_art',ROOT/'tools/prepare-boot-animation.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class BootArtTests(unittest.TestCase):
 def animation(self,path,kind='p',compression=zipfile.ZIP_STORED):
  with zipfile.ZipFile(path,'w',compression=compression) as z:
   z.writestr('desc.txt',f'1920 1080 60\n{kind} 0 0 loop\n')
   z.writestr('loop/00000.png',b'\x89PNG\r\n\x1a\nfixture')
 def test_completion_required_parts_are_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'animation.zip';self.animation(p,'c')
   with self.assertRaisesRegex(ValueError,'delay'):module.validate(p)
 def test_compressed_frames_are_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'animation.zip';self.animation(p,compression=zipfile.ZIP_DEFLATED)
   with self.assertRaisesRegex(ValueError,'stored'):module.validate(p)
 def test_interruptible_animation_is_accepted(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'animation.zip';self.animation(p)
   self.assertEqual((1920,1080,60),module.validate(p))
