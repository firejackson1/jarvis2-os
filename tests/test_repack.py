import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FragmentTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('repack', ROOT / 'tools/repack.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_recovery_must_be_unique_and_correct_type(self):
        args = ['--header_version', '4', '--ramdisk_type', '1', '--ramdisk_name',
                'platform', '--vendor_ramdisk_fragment', '/tmp/platform',
                '--ramdisk_type', '2', '--ramdisk_name', 'recovery',
                '--vendor_ramdisk_fragment', '/tmp/recovery']
        self.assertEqual(Path('/tmp/recovery'), self.module.recovery_fragment(args))
        with self.assertRaises(ValueError):
            self.module.recovery_fragment(args + args[8:])
        bad = args.copy()
        bad[bad.index('2')] = '1'
        with self.assertRaises(ValueError):
            self.module.recovery_fragment(bad)

    @unittest.skipUnless(os.environ.get('JARVIS_ANDROID_TREE'), 'requires AOSP host mkbootimg tools')
    def test_real_v4_repack_preserves_platform_dtb_bootconfig(self):
        tree = Path(os.environ['JARVIS_ANDROID_TREE'])
        tools = tree / 'out/host/linux-x86/bin'
        with tempfile.TemporaryDirectory(prefix='jarvis recovery ') as tmp:
            p = Path(tmp)
            for name, data in [('platform', b'platform-fragment'), ('recovery', b'old-recovery'),
                               ('dtb', b'dtb-fixture'), ('bootconfig', b'fixture=true\n'),
                               ('new', b'new-recovery')]:
                (p / name).write_bytes(data)
            subprocess.run([str(tools / 'mkbootimg'), '--header_version', '4',
                            '--pagesize', '4096', '--dtb', str(p / 'dtb'),
                            '--vendor_bootconfig', str(p / 'bootconfig'),
                            '--ramdisk_type', '1', '--ramdisk_name', 'platform',
                            '--vendor_ramdisk_fragment', str(p / 'platform'),
                            '--ramdisk_type', '2', '--ramdisk_name', 'recovery',
                            '--vendor_ramdisk_fragment', str(p / 'recovery'),
                            '--vendor_boot', str(p / 'stock.img')], check=True)
            report = self.module.repack(tree, p / 'stock.img', p / 'new', p / 'output', 67108864)
            self.assertFalse(report['avb_signed'])
            self.assertTrue(report['protected_payloads_unchanged'])
            self.assertFalse(report['device_contacted'])
            with self.assertRaises(ValueError):
                self.module.repack(tree, p / 'stock.img', p / 'new', p / 'output', 67108864)
            with self.assertRaises(ValueError):
                self.module.repack(tree, p / 'stock.img', p / 'new', p / 'too-small', 100)
