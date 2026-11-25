# SPDX-License-Identifier: Apache-2.0
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

import test_candidate_install as fixtures


ROOT = Path(__file__).resolve().parents[1]


class RecoveryFixture(fixtures.FakeADB):
    product = 'jarvis2'
    power_mode = 'recovery'
    uid = '0'
    usb = 'usb:1-2'
    corrupt_prefix = False

    def run(self, *args, binary=False):
        special = {
            ('devices', '-l'): f'List of devices attached\n{self.serial} recovery {self.usb}\n',
            ('shell', 'getprop ro.product.device'): self.product,
            ('shell', 'ps -A -o NAME'): f'NAME\nadbd\n{self.power_mode}\n',
            ('shell', 'id -u'): self.uid,
            ('shell', 'find /metadata/ota/snapshots -maxdepth 1 -mindepth 1 -print'): '',
        }
        if args in special:
            self.commands.append(args)
            return special[args]
        if args[0] == 'exec-out' and self.corrupt_prefix and sum(
            cmd[0] == 'exec-out' for cmd in self.commands
        ):
            return b'a' + super().run(*args, binary=binary)[1:]
        return super().run(*args, binary=binary)


class RecoveryInspectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            'recovery_inspection', ROOT / 'tools/inspect-recovery.py')
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        _, fixture, self.views = fixtures.InstallerTests().fixture(self.root)
        device = self.root / 'fixture'
        device.mkdir()
        self.adb = RecoveryFixture(device, fixture.capture, self.views)
        self.adb_path = self.root / 'adb'
        self.lpdump = self.root / 'lpdump'
        self.output = self.root / 'inspection'
        for path in (self.adb_path, self.lpdump):
            path.write_bytes(path.name.encode())

    def inspect(self, *, adb_pin=None, **options):
        return self.tool.inspect(
            self.adb.serial, self.adb_path, adb_pin or self.tool.WRITER.digest(self.adb_path),
            self.lpdump, self.tool.WRITER.digest(self.lpdump), self.output,
            transport=self.adb, view_loader=lambda *args: copy.deepcopy(self.views), **options,
        )

    def test_qualified_fixture_records_both_views_without_write_commands(self):
        result = self.inspect()
        self.assertTrue(result['layout']['views_match'])
        self.assertEqual('clear', result['snapshots']['status'])
        self.assertEqual(1048576, (self.output / 'super-prefix.img').stat().st_size)
        self.assertFalse(result['installation_authorized'])
        self.assertEqual({'inspection.json', 'super-prefix.img'}, {p.name for p in self.output.iterdir()})
        for command in self.adb.commands:
            self.assertIn(command[0], ('devices', 'get-serialno', 'shell', 'exec-out'))
            if command[0] == 'exec-out':
                self.assertEqual(command[1], 'dd')
                self.assertFalse(any(token.startswith('of=') for token in command))
            if command[0] == 'shell':
                self.assertIn(command[1].split()[0], ('getprop', 'id', 'ps', 'readlink', 'stat',
                                                      'blockdev', 'cat', 'sh', 'find'))
        self.assertFalse(self.adb.maps or self.adb.writes)

    def test_snapshots_remain_unverified_when_the_mount_or_state_is_ambiguous(self):
        for attribute, value in (('metadata_mounted', False), ('nested_metadata', True),
                                 ('no_replay', False), ('snapshot', True)):
            with self.subTest(attribute=attribute):
                previous = getattr(self.adb, attribute)
                setattr(self.adb, attribute, value)
                self.output = self.root / attribute
                result = self.inspect()
                self.assertEqual('unverified', result['snapshots']['status'])
                self.assertTrue(result['layout']['views_match'])
                setattr(self.adb, attribute, previous)

    def test_unprivileged_or_non_recovery_is_reported_without_partition_reads(self):
        for attribute, value in (('uid', '2000'), ('power_mode', 'system_server')):
            with self.subTest(attribute=attribute):
                previous = getattr(self.adb, attribute)
                setattr(self.adb, attribute, value)
                self.output = self.root / attribute
                result = self.inspect()
                self.assertEqual('unverified', result['snapshots']['status'])
                self.assertIsNone(result['layout'])
                setattr(self.adb, attribute, previous)
        self.assertFalse(any(command[0] == 'exec-out' for command in self.adb.commands))

    def test_wrong_product_or_unpinned_usb_is_rejected(self):
        self.adb.usb = 'transport_id:4'
        with self.assertRaisesRegex(ValueError, 'USB'):
            self.inspect()
        self.adb.usb = 'usb:1-2'
        self.adb.product = 'other'
        with self.assertRaisesRegex(ValueError, 'Jarvis2'):
            self.inspect()
        self.assertFalse(self.output.exists())
        self.assertFalse(any(command[0] == 'exec-out' for command in self.adb.commands))

    def test_changed_prefix_discards_output(self):
        self.adb.corrupt_prefix = True
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.inspect()
        self.assertFalse(self.output.exists())

    def test_different_metadata_views_are_recorded_separately(self):
        self.views[1]['canonical'] = 'different slot view'
        self.assertFalse(self.inspect()['layout']['views_match'])

    def test_pins_and_capture_limit_are_checked_before_usb(self):
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.inspect(adb_pin='0' * 64)
        with self.assertRaisesRegex(ValueError, 'prefix'):
            self.inspect(prefix_bytes=17 * 1024 * 1024)
        self.assertEqual([], self.adb.commands)
        self.assertFalse(self.output.exists())
