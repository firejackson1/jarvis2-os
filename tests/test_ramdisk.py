import importlib.util
from pathlib import Path
import stat
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


def archive(entries):
    result = bytearray()
    for name, mode, data in [*entries, ('TRAILER!!!', 0, b'')]:
        name = name.encode() + b'\0'
        fields = [1, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name), 0]
        result += b'070701' + ''.join(f'{v:08x}' for v in fields).encode() + name
        result += b'\0' * (-len(result) % 4)
        result += data
        result += b'\0' * (-len(result) % 4)
    return bytes(result)


def elf(bits, machine):
    data = bytearray(64 if bits == 64 else 52)
    data[:7] = b'\x7fELF' + bytes([2 if bits == 64 else 1, 1, 1])
    struct.pack_into('<HH', data, 16, 3, machine)
    return bytes(data)


class RamdiskTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('audit', ROOT / 'tools/audit-ramdisk.py')
        self.audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.audit)

    def test_recovery_architecture_is_independent_of_android_app_abi(self):
        entries = self.audit.parse_cpio(archive([
            ('init', stat.S_IFLNK | 0o777, b'/system/bin/init'),
            ('system/bin/init', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
        ]))
        report = self.audit.audit_layers([entries])
        self.assertEqual(64, report['required']['system/bin/recovery']['bits'])
        self.assertEqual('AArch64', report['required']['init']['machine'])
        self.assertFalse(report['boot_tested'])
        self.audit.audit_layers([entries], expected_recovery_arch='arm64')
        with self.assertRaises(ValueError):
            self.audit.audit_layers([entries], expected_recovery_arch='arm')

    def test_archive_paths_cannot_escape_or_alias(self):
        for names in [('../escape',), ('/absolute',), ('init', './init')]:
            with self.assertRaises(ValueError):
                self.audit.parse_cpio(archive([(n, stat.S_IFREG | 0o644, b'x') for n in names]))

    def test_truncated_archives_and_symlink_loops_are_rejected(self):
        with self.assertRaises(ValueError):
            self.audit.parse_cpio(archive([('init', stat.S_IFREG | 0o755, b'x')])[:120])
        entries = self.audit.parse_cpio(archive([
            ('init', stat.S_IFLNK | 0o777, b'init'),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(32, 40)),
        ]))
        with self.assertRaises(ValueError):
            self.audit.audit_layers([entries])

    def test_private_keys_and_preauthorized_adb_files_are_flagged(self):
        entries = self.audit.parse_cpio(archive([
            ('init', stat.S_IFREG | 0o755, elf(32, 40)),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(32, 40)),
            ('adb_keys', stat.S_IFREG | 0o600, b'not-a-real-key'),
            # Synthetic marker only; no real private-key material.
            ('secret.pem', stat.S_IFREG | 0o600, b'-----BEGIN ' + b'PRIVATE KEY-----\nfixture'),
        ]))
        report = self.audit.audit_layers([entries])
        self.assertEqual({'adb_keys', 'secret.pem'}, set(report['blocked_artifacts']))
