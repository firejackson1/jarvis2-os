# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest

from test_ramdisk import archive, elf
from test_startup_guard import MODULES, HARDWARE

ROOT = Path(__file__).resolve().parents[1]


class AssembleRamdiskTests(unittest.TestCase):
    def setUp(self):
        script = ROOT / 'tools/assemble_ramdisk.py'
        self.assertTrue(script.is_file(), 'Guarded ramdisk assembler is missing')
        spec = importlib.util.spec_from_file_location('assembler', script)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.temp = tempfile.TemporaryDirectory(prefix='ram assembly ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = {}
        self.add_input('busybox', elf(64, 183))
        self.add_input('musl_loader', elf(64, 183))
        self.add_input('mmc_partitions', b'1\n2\n3\n')
        self.add_input('platform_cpio', self.platform())
        self.inputs['kernel_release'] = '5.15.196-fixture'
        self.base = archive([
            ('bin', stat.S_IFLNK | 0o777, b'/system/bin'),
            ('system', stat.S_IFDIR | 0o755, b''),
            ('system/bin', stat.S_IFDIR | 0o755, b''),
            ('init', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/etc/init/hw/init.rc', stat.S_IFREG | 0o644,
             b'import /ramboot/init.hardware.rc\nservice recovery /system/bin/recovery --show_text\n'),
            ('system/etc/recovery.fstab', stat.S_IFREG | 0o644,
             b'ramdisk /tmp ramdisk defaults defaults\n'),
        ])

    def add_input(self, name, content):
        p = self.root / name
        p.write_bytes(content)
        self.inputs[name] = {'path': str(p), 'sha256': hashlib.sha256(content).hexdigest()}

    def platform(self, bad_dependency=False):
        names = MODULES + HARDWARE
        deps = ''.join('/lib/modules/' + n + ':' +
                       (' /lib/modules/' + HARDWARE[-1] if bad_dependency and n == MODULES[0]
                        else '') + '\n' for n in names).encode()
        return archive([
            *[('lib/modules/' + n, stat.S_IFREG | 0o644,
               elf(64, 183, kind=1)) for n in names],
            ('lib/modules/modules.dep', stat.S_IFREG | 0o644, deps),
        ])

    def assemble(self, base=None):
        base = self.base if base is None else base
        return self.tool.assemble(base, hashlib.sha256(base).hexdigest(), self.inputs)

    def test_overlay_preserves_base_and_places_runtime_behind_canonical_paths(self):
        result, report = self.assemble()
        self.assertTrue(result.startswith(self.base))
        overlay = self.tool.AUDIT.parse_cpio(result[len(self.base):])
        self.assertNotIn('bin', overlay)
        self.assertIn('system/bin/busybox', overlay)
        self.assertIn('ramboot-init', overlay)
        self.assertEqual(overlay['lib/libc.musl-aarch64.so.1']['data'],
                         b'ld-musl-aarch64.so.1')
        self.assertNotIn('lib/modules', overlay)
        self.assertIn(b'sys.usb.controller fe350000.crgudc',
                      overlay['ramboot/init.hardware.rc']['data'])
        self.assertEqual(report['storage_modules'], MODULES)
        self.assertEqual(report['hardware_modules'], HARDWARE)
        self.assertTrue(report['base_bytes_preserved'])
        self.assertFalse(report['boot_tested'])
        self.assertFalse(report['runtime_dependencies_verified'])
        again, _ = self.assemble()
        self.assertEqual(result, again)

    def test_changed_private_input_or_base_hash_is_rejected(self):
        (self.root / 'busybox').write_bytes(b'changed')
        with self.assertRaises(ValueError): self.assemble()
        with self.assertRaises(ValueError): self.tool.assemble(self.base, '0' * 64, self.inputs)

    def test_unaligned_base_is_rejected(self):
        with self.assertRaises(ValueError): self.assemble(self.base + b'\0')

    def test_mixed_architecture_init_is_rejected(self):
        parsed = self.tool.AUDIT.parse_cpio(self.base)
        base = archive([(n,e['mode'],elf(32,40) if n == 'init' else e['data'])
                        for n,e in parsed.items()])
        with self.assertRaises(ValueError): self.assemble(base)

    def test_wrong_architecture_and_invalid_partition_manifest_are_rejected(self):
        for name, content in (('busybox', elf(32, 40)), ('mmc_partitions', b'1\n1\n'),
                              ('mmc_partitions', b'01\n'), ('kernel_release', b'')):
            with self.subTest(name=name, content=content):
                if name == 'kernel_release':
                    self.inputs[name] = ''
                else:
                    self.add_input(name, content)
                with self.assertRaises(ValueError): self.assemble()
                self.add_input('busybox', elf(64, 183))
                self.add_input('mmc_partitions', b'1\n2\n3\n')

    def test_storage_dependency_on_later_hardware_is_rejected(self):
        self.add_input('platform_cpio', self.platform(bad_dependency=True))
        with self.assertRaises(ValueError): self.assemble()

    def test_existing_alias_or_payload_cannot_be_shadowed_by_overlay(self):
        for entry in (('lib', stat.S_IFLNK | 0o777, b'/system/lib64'),
                      ('ramboot-init', stat.S_IFREG | 0o755, b'existing'),
                      ('system/bin/busybox', stat.S_IFREG | 0o755, b'existing')):
            with self.subTest(path=entry[0]):
                # Insert a record in the base before its final trailer.
                parsed = self.tool.AUDIT.parse_cpio(self.base)
                base = archive([(n, e['mode'], e['data']) for n,e in parsed.items()] + [entry])
                with self.assertRaises(ValueError): self.assemble(base)


if __name__ == '__main__':
    unittest.main()
