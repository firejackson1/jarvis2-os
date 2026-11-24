from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


class TvHardwareTests(unittest.TestCase):
    def test_landscape_apps_are_not_filtered_from_tv(self):
        root = Path(__file__).resolve().parents[1]
        permissions = ET.parse(root / 'android.software.leanback.xml').getroot()
        features = {node.get('name') for node in permissions.findall('feature')}
        # Landscape activities imply this Play requirement, even without touch.
        self.assertIn('android.hardware.screen.landscape', features)
