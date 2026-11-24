# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get('JARVIS_ANDROID_TREE'), 'requires pinned AOSP host tools')
class PackRambootTests(unittest.TestCase):
    def setUp(self):
        script = ROOT / 'tools/pack_ramboot.py'
        self.assertTrue(script.is_file(), 'RAM boot-container packer is missing')
        spec = importlib.util.spec_from_file_location('pack_ramboot', script)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.temp = tempfile.TemporaryDirectory(prefix='RAM image with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tools = Path(os.environ['JARVIS_ANDROID_TREE']) / 'out/host/linux-x86/bin'
        self.kernel = self.root / 'kernel'; self.kernel.write_bytes(b'opaque fixture kernel')
        self.dtb = self.root / 'dtb'; self.dtb.write_bytes(b'opaque fixture dtb')
        self.old_rd = self.root / 'old-ramdisk'; self.old_rd.write_bytes(b'never copy old userspace')
        self.new_rd = self.root / 'new-ramdisk'; self.new_rd.write_bytes(b'checksum-bound new ramdisk')
        self.reference = self.root / 'reference.img'
        self.make_reference()
        self.bindings = {name:self.sha(path) for name,path in (
            ('reference_boot', self.reference), ('ramdisk', self.new_rd),
            ('kernel', self.kernel), ('dtb', self.dtb))}

    def sha(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def make_reference(self, version='2', cmdline='rdinit=/ramboot-init panic=5'):
        args = [str(self.tools/'mkbootimg'), '--header_version', version,
                        '--kernel',str(self.kernel),'--ramdisk',str(self.old_rd),
                        '--pagesize','2048','--base','0',
                        '--kernel_offset','0x02080000','--ramdisk_offset','0x01000000',
                        '--tags_offset','0x100','--dtb_offset','0x01f00000',
                        '--board','jarvis2','--cmdline',cmdline,'--output',str(self.reference)]
        if version == '2': args += ['--dtb',str(self.dtb)]
        subprocess.run(args, check=True,capture_output=True)

    def pack(self, budget=128*1024*1024):
        return self.tool.pack(self.tools,self.reference,self.new_rd,
                              self.root/'output',self.bindings,budget)

    def test_real_aosp_roundtrip_preserves_kernel_dtb_and_header_fields(self):
        report = self.pack()
        self.assertTrue(report['protected_payloads_unchanged'])
        self.assertTrue(report['recognized_header_fields_unchanged_except_cmdline'])
        self.assertEqual(report['changed_header_fields'],['--cmdline'])
        self.assertTrue(report['inputs_unchanged'])
        self.assertEqual(report['cmdline'], 'rdinit=/ramboot-init panic=0')
        self.assertFalse(report['boot_tested'])
        self.assertFalse(report['bootloader_relocation_verified'])
        self.assertFalse(report['device_contacted'])
        self.assertEqual((self.root/'output/after/ramdisk').read_bytes(),self.new_rd.read_bytes())
        self.assertEqual((self.root/'output/after/kernel').read_bytes(),self.kernel.read_bytes())
        self.assertEqual((self.root/'output/after/dtb').read_bytes(),self.dtb.read_bytes())

    def test_reference_or_ramdisk_hash_mismatch_cannot_produce_image(self):
        for name in ('reference_boot','ramdisk'):
            previous=self.bindings[name]; self.bindings[name]='0'*64
            with self.assertRaises(ValueError): self.pack()
            self.assertFalse((self.root/'output').exists())
            self.bindings[name]=previous

    def test_wrong_kernel_binding_rejects_before_creating_candidate(self):
        self.bindings['kernel']='0'*64
        with self.assertRaises(ValueError): self.pack()
        self.assertFalse((self.root/'output/ramboot-unsigned.img').exists())

    def test_unsupported_reference_version_or_init_command_is_rejected(self):
        for version,cmdline in (('1','rdinit=/ramboot-init panic=5'),
                               ('2','rdinit=/different-init panic=5')):
            with self.subTest(version=version):
                self.make_reference(version,cmdline)
                self.bindings['reference_boot']=self.sha(self.reference)
                out=self.root/'output'
                if out.exists():
                    import shutil
                    shutil.rmtree(out)
                with self.assertRaises(ValueError): self.pack()
                self.assertFalse((out/'ramboot-unsigned.img').exists())

    def test_download_budget_failure_removes_unqualified_image(self):
        self.new_rd.write_bytes(b'new ramdisk bytes' * 650)
        self.bindings['ramdisk']=self.sha(self.new_rd)
        with self.assertRaisesRegex(ValueError, 'exceeds the supplied download budget'):
            self.pack(budget=12500)
        self.assertTrue((self.root/'output/before/kernel').exists())
        self.assertFalse((self.root/'output/ramboot-unsigned.img').exists())


if __name__ == '__main__': unittest.main()
