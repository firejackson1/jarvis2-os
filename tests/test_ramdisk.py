import importlib.util
from pathlib import Path
import stat
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


def archive(entries, crc=False):
    result = bytearray()
    for entry in [*entries, ('TRAILER!!!', 0, b'')]:
        name, mode, data, *metadata = entry
        attributes = metadata[0] if metadata else {}
        name = name.encode() + b'\0'
        fields = [1, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name),
                  sum(data) & 0xffffffff if crc else 0]
        for index, value in attributes.items():
            fields[index] = value
        result += (b'070702' if crc else b'070701') + ''.join(f'{v:08x}' for v in fields).encode() + name
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

    def test_hardlinked_executable_payload_can_appear_first_or_last(self):
        for payload_first in (True, False):
            with self.subTest(payload_first=payload_first):
                payload = elf(64, 183)
                entries = self.audit.parse_cpio(archive([
                    ('init', stat.S_IFREG | 0o755, payload if payload_first else b'',
                     {0: 12, 4: 2, 7: 8, 8: 1}),
                    ('system/bin/init', stat.S_IFREG | 0o755, b'' if payload_first else payload,
                     {0: 12, 4: 2, 7: 8, 8: 1}),
                    ('system/bin/recovery', stat.S_IFREG | 0o755, payload),
                ]))
                report = self.audit.audit_layers([entries], expected_recovery_arch='arm64')
                self.assertEqual(report['required']['init']['machine'], 'AArch64')
                self.assertEqual(entries['init']['data'], entries['system/bin/init']['data'])
                self.assertEqual(entries['init']['ino'], 12)
                self.assertEqual(entries['init']['nlink'], 2)
                self.assertEqual(entries['init']['dev'], [8, 1])

    def test_later_nonempty_hardlink_payload_updates_all_aliases(self):
        entries = self.audit.parse_cpio(archive([
            ('first', stat.S_IFREG | 0o755, b'old', {0: 25, 4: 3}),
            ('second', stat.S_IFREG | 0o644, b'new', {0: 25, 4: 3, 2: 7}),
            ('third', stat.S_IFREG | 0o640, b'', {0: 25, 4: 3, 2: 9}),
        ]))
        for entry in entries.values():
            self.assertEqual(entry['data'], b'new')
            self.assertEqual(entry['mode'], stat.S_IFREG | 0o640)
            self.assertEqual(entry['uid'], 9)

    def test_hardlink_identity_includes_device_and_is_scoped_to_one_archive(self):
        first = self.audit.parse_cpio(archive([
            ('a', stat.S_IFREG | 0o644, b'one', {0: 12, 4: 2, 7: 8}),
            ('b', stat.S_IFREG | 0o644, b'two', {0: 12, 4: 2, 7: 9}),
            ('c', stat.S_IFREG | 0o644, b'three', {0: 12, 4: 1, 7: 8}),
        ]))
        second = self.audit.parse_cpio(archive([
            ('d', stat.S_IFREG | 0o644, b'', {0: 12, 4: 2, 7: 8}),
        ]))
        self.assertEqual([first[n]['data'] for n in ('a', 'b', 'c')],
                         [b'one', b'two', b'three'])
        self.assertEqual(second['d']['data'], b'')

    def test_regular_overlay_updates_existing_aliases_but_symlink_replaces_one_name(self):
        base = self.audit.parse_cpio(archive([
            ('init', stat.S_IFREG | 0o755, elf(64, 183), {0: 12, 4: 2}),
            ('system/bin/init', stat.S_IFREG | 0o755, b'', {0: 12, 4: 2}),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/other', stat.S_IFREG | 0o755, elf(32, 40)),
        ]))
        regular = self.audit.parse_cpio(archive([
            ('system/bin/init', stat.S_IFREG | 0o755, elf(32, 40)),
        ]))
        report = self.audit.audit_layers([base, regular], expected_recovery_arch='arm64')
        self.assertEqual(report['required']['init']['machine'], 'ARM')
        symlink = self.audit.parse_cpio(archive([
            ('system/bin/init', stat.S_IFLNK | 0o777, b'/system/bin/other'),
        ]))
        report = self.audit.audit_layers([base, symlink], expected_recovery_arch='arm64')
        self.assertEqual(report['required']['init']['machine'], 'AArch64')
        self.assertEqual(base['init']['data'], elf(64, 183), 'An audit must not mutate inputs')

    def test_incoming_hardlink_can_replace_one_old_alias_without_changing_the_other(self):
        base = self.audit.parse_cpio(archive([
            ('init', stat.S_IFREG | 0o755, elf(64, 183), {0: 12, 4: 2}),
            ('system/bin/init', stat.S_IFREG | 0o755, b'', {0: 12, 4: 2}),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
        ]))
        overlay = self.audit.parse_cpio(archive([
            ('new-init', stat.S_IFREG | 0o755, b'', {0: 42, 4: 2}),
            ('system/bin/init', stat.S_IFREG | 0o755, elf(32, 40), {0: 42, 4: 2}),
        ]))
        report = self.audit.audit_layers([base, overlay], expected_recovery_arch='arm64')
        self.assertEqual(report['required']['init']['machine'], 'AArch64')

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

    def test_required_entrypoints_must_be_executable_regular_files(self):
        for mode in (stat.S_IFREG | 0o644, stat.S_IFDIR | 0o755):
            with self.subTest(mode=mode):
                entries = self.audit.parse_cpio(archive([
                    ('init', mode, elf(64, 183)),
                    ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
                ]))
                with self.assertRaises(ValueError):
                    self.audit.audit_layers([entries])

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

    def test_overwritten_credentials_still_embedded_in_the_image_are_flagged(self):
        original = self.audit.parse_cpio(archive([
            ('init', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
            ('hidden', stat.S_IFREG | 0o600,
             b'-----BEGIN ' + b'PRIVATE KEY-----\nfixture'),
            ('adb_keys', stat.S_IFLNK | 0o777, b'/not-an-owner-key'),
        ]))
        overlay = self.audit.parse_cpio(archive([
            ('hidden', stat.S_IFREG | 0o644, b'public fixture'),
        ]))
        for layers in ([original, overlay], iter([original, overlay])):
            with self.subTest(layers=type(layers).__name__):
                report = self.audit.audit_layers(layers)
                self.assertEqual(set(report['blocked_artifacts']), {'hidden', 'adb_keys'})
                self.assertEqual(report['blocked_archive_artifacts'],
                                 [{'layer': 0, 'path': 'adb_keys'}, {'layer': 0, 'path': 'hidden'}])

    def test_overwritten_payload_in_a_hardlink_group_is_still_scanned(self):
        entries = self.audit.parse_cpio(archive([
            ('init', stat.S_IFREG | 0o755, elf(64, 183)),
            ('system/bin/recovery', stat.S_IFREG | 0o755, elf(64, 183)),
            ('first', stat.S_IFREG | 0o600,
             b'-----BEGIN ' + b'PRIVATE KEY-----\nfixture', {0: 17, 4: 2}),
            ('last', stat.S_IFREG | 0o644, b'public fixture', {0: 17, 4: 2}),
        ]))
        self.assertEqual(entries['first']['data'], b'public fixture')
        report = self.audit.audit_layers([entries])
        self.assertEqual(report['blocked_artifacts'], ['first'])
