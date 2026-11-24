# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
from pathlib import Path
import stat
import unittest

from test_ramdisk import archive, elf

ROOT = Path(__file__).resolve().parents[1]
INIT = 'system/etc/init/hw/init.rc'
FSTAB = 'system/etc/recovery.fstab'
SCRIPT = (b'import /init.recovery.${ro.hardware}.rc\n\n'
          b'service recovery /system/bin/recovery\n'
          b'    user root\n'
          b'service adbd /system/bin/adbd --device_banner=recovery\n')


class PrepareRamdiskTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'tools/prepare_ramdisk.py'
        self.assertTrue(path.is_file(), 'Diagnostic ramdisk preparer is missing')
        spec = importlib.util.spec_from_file_location('prepare', path)
        self.prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.prepare)

    def image(self, script=SCRIPT, adb_mode=stat.S_IFLNK | 0o644,
              adb_data=b'/product/etc/security/adb_keys', crc=False):
        return archive([
            ('init', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/adbd', stat.S_IFREG | 0o755, elf(64, 183)),
            ('prop.default', stat.S_IFREG | 0o644, b'ro.debuggable=1\n'),
            (INIT, stat.S_IFREG | 0o644, script),
            (FSTAB, stat.S_IFREG | 0o644, b'/dev/block/by-name/metadata /metadata ext4 ro wait\n'),
            ('adb_keys', adb_mode, adb_data),
            ('linked-first', stat.S_IFREG | 0o640, b'', {0: 90, 4: 2, 2: 7, 3: 8, 5: 123}),
            ('linked-last', stat.S_IFREG | 0o640, b'keep payload', {0: 90, 4: 2, 2: 7, 3: 8, 5: 123}),
        ], crc=crc)

    def test_only_reviewed_records_change_and_native_payloads_are_preserved(self):
        source = self.image()
        result, report = self.prepare.prepare(source, hashlib.sha256(source).hexdigest())
        before = self.prepare.AUDIT.parse_cpio(source)
        after = self.prepare.AUDIT.parse_cpio(result)
        self.assertNotIn('adb_keys', after)
        self.assertIn(b'service recovery /system/bin/recovery --show_text\n', after[INIT]['data'])
        self.assertIn(b'import /ramboot/init.hardware.rc\n', after[INIT]['data'])
        self.assertEqual(after[FSTAB]['data'], b'ramdisk /tmp ramdisk defaults defaults\n')
        for name in set(before) - {INIT, FSTAB, 'adb_keys'}:
            a, b = before[name]['archive']['record_span'], after[name]['archive']['record_span']
            self.assertEqual(source[a[0]:a[1]], result[b[0]:b[1]], name)
        for name in ('linked-first', 'linked-last'):
            self.assertEqual(after[name]['data'], b'keep payload')
            self.assertEqual(after[name]['uid'], 7)
            self.assertEqual(after[name]['gid'], 8)
            self.assertEqual(after[name]['mtime'], 123)
        self.assertFalse(report['boot_tested'])
        self.assertFalse(report['device_contacted'])
        self.assertTrue(report['untouched_records_identical'])
        self.assertTrue(report['requires_guard_and_hardware_overlay'])

    def test_input_digest_is_mandatory_and_must_match(self):
        for digest in ('', 'not-a-hash', '0' * 64):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                self.prepare.prepare(self.image(), digest)

    def test_owner_keys_and_unexpected_trust_links_are_not_silently_removed(self):
        for mode, data in ((stat.S_IFREG | 0o600, b'not-a-real-key'),
                           (stat.S_IFLNK | 0o777, b'/data/misc/adb/adb_keys')):
            source = self.image(adb_mode=mode, adb_data=data)
            with self.assertRaises(ValueError):
                self.prepare.prepare(source, hashlib.sha256(source).hexdigest())

    def test_unexpected_or_ambiguous_recovery_service_is_rejected(self):
        for script in (SCRIPT.replace(b'/system/bin/recovery\n', b'/system/bin/recovery --wipe_data\n'),
                       SCRIPT + b'service recovery /system/bin/recovery\n',
                       SCRIPT + b'service recovery /system/bin/recovery --wipe_data\n',
                       SCRIPT.replace(b'import /init.recovery.${ro.hardware}.rc\n', b'')):
            source = self.image(script=script)
            with self.assertRaises(ValueError):
                self.prepare.prepare(source, hashlib.sha256(source).hexdigest())

    def test_additional_hardware_imports_are_not_silently_retained(self):
        source = self.image(script=SCRIPT + b'import /vendor/etc/other.rc\n')
        with self.assertRaises(ValueError):
            self.prepare.prepare(source, hashlib.sha256(source).hexdigest())

    def test_crc_archive_checksums_are_updated_for_modified_records(self):
        source = self.image(crc=True)
        result, report = self.prepare.prepare(source, hashlib.sha256(source).hexdigest())
        self.assertEqual(result[:6], b'070702')
        self.assertEqual(self.prepare.AUDIT.parse_cpio(result)[FSTAB]['data'],
                         b'ramdisk /tmp ramdisk defaults defaults\n')
        self.assertTrue(report['untouched_records_identical'])

    def test_existing_adbd_configuration_is_not_modified(self):
        source = self.image()
        result, _ = self.prepare.prepare(source, hashlib.sha256(source).hexdigest())
        after = self.prepare.AUDIT.parse_cpio(result)
        self.assertIn(b'service adbd /system/bin/adbd --device_banner=recovery\n', after[INIT]['data'])
        self.assertEqual(after['prop.default']['data'], b'ro.debuggable=1\n')


if __name__ == '__main__':
    unittest.main()
