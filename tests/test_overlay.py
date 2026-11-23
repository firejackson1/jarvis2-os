from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
A='{http://schemas.android.com/apk/res/android}'
class OverlayTests(unittest.TestCase):
 def test_five_main_categories_and_no_top_level_airpods(self):
  for name in ['main_prefs','main_prefs_x','main_prefs_vendor']:
   root=ET.parse(ROOT/'overlays/TvControls/res/xml'/f'{name}.xml').getroot()
   group=next(n for n in root if n.get(A+'key')=='general_settings')
   entries={n.get(A+'key'):n for n in group if (n.get(A+'key')or'').startswith('jarvis_')}
   self.assertEqual({'jarvis_home','jarvis_controller_buttons','jarvis_voice','jarvis_widgets','jarvis_audio'},set(entries))
   self.assertEqual('Smart Home',entries['jarvis_voice'].get(A+'title'))
   self.assertTrue(entries['jarvis_voice'].get(A+'icon').endswith('/ic_home'))
 def test_release_overlay_enabled_without_owner_command(self):
  node=ET.parse(ROOT/'overlays/TvControls/AndroidManifest.xml').getroot().find('overlay')
  self.assertEqual('true',node.get(A+'isStatic'))
  self.assertEqual('jarvis2',node.get(A+'requiredSystemPropertyValue'))
