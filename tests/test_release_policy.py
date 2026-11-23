"""Public tree must not grant the developer's existing ADB identity access."""
import pathlib
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
class ReleasePolicyTests(unittest.TestCase):
    def test_no_pre_authorized_adb_keys(self):
        device = ROOT
        self.assertFalse(list(device.rglob('*.pub')))
        for f in device.rglob('*.mk'):
            self.assertNotIn('PRODUCT_ADB_KEYS', f.read_text(), str(f))
    def test_public_product_requires_adb_authorization(self):
        product = (ROOT / 'device.mk').read_text()
        self.assertNotIn('ro.adb.secure=0', product)
        self.assertNotIn('service.adb.tcp.port=', product)
        self.assertNotIn('persist.adb.tcp.port=', product)
