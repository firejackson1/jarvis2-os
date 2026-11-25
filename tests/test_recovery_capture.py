# SPDX-License-Identifier: Apache-2.0
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import test_candidate_install as fixtures
import test_recovery_inspection as inspection_fixtures


ROOT = Path(__file__).resolve().parents[1]


class CaptureFixture(inspection_fixtures.RecoveryFixture):
    truncate_payload = False
    change_on_readback = False
    range_reads = 0
    overlap_physical = False

    def run(self, *args, binary=False):
        if args[0] == 'exec-out' and 'iflag=skip_bytes,count_bytes' in args:
            self.commands.append(args)
            options = dict(arg.split('=', 1) for arg in args[2:])
            self.range_reads += 1
            self.assert_read_only(options)
            start = int(options['skip'])
            end = start + int(options['count'])
            data = self.data(options['if'])[start:end]
            if self.truncate_payload:
                return data[:-1]
            allocated = sum(bool(extents) for extents in self.views[0]['layout']['partitions'].values())
            if self.change_on_readback and self.range_reads > allocated + 4:
                return b'!' + data[1:]
            return data
        if self.overlap_physical and args[0] == 'shell' and args[1].endswith('/start'):
            return '2048\n'
        return super().run(*args, binary=binary)

    @staticmethod
    def assert_read_only(options):
        if set(options) != {'if', 'iflag', 'bs', 'skip', 'count', 'status'}:
            raise AssertionError('Unexpected block capture operation')


class RecoveryCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            'recovery_capture', ROOT / 'tools/capture-recovery.py')
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        _, original, self.views = fixtures.InstallerTests().fixture(self.root)
        device = self.root / 'fixture'
        device.mkdir()
        self.adb = CaptureFixture(device, original.capture, self.views)
        self.adb_path = self.root / 'adb'
        self.lpdump = self.root / 'lpdump'
        self.output = self.root / 'capture'
        for path in (self.adb_path, self.lpdump):
            path.write_bytes(path.name.encode())

    def capture(self, slot='a', dmctl_pin='d' * 64):
        return self.tool.capture(
            self.adb.serial, slot, self.adb_path, self.tool.WRITER.digest(self.adb_path),
            self.lpdump, self.tool.WRITER.digest(self.lpdump),
            self.adb.capture['dmctl']['path'], dmctl_pin, self.output,
            transport=self.adb, view_loader=lambda *args: copy.deepcopy(self.views),
        )

    def test_seven_restore_files_match_current_partitions_and_writer_contract(self):
        receipt = self.capture()
        self.assertFalse(receipt['installation_authorized'])
        capture = json.loads((self.output / 'capture.json').read_text())
        self.assertEqual(receipt['capture_sha256'], self.tool.WRITER.digest(self.output / 'capture.json'))
        self.assertEqual(set(self.tool.WRITER.REQUIRED_PHYSICAL), set(capture['physical']))
        self.assertEqual(self.adb.capture['logical_sha256'], capture['logical_sha256'])
        self.assertEqual(7, len(capture['old_files']))
        self.tool.WRITER.image_files(self.output / 'old-images', capture['old_files'])
        for name in ('system', 'system_ext', 'product'):
            self.assertEqual(fixtures.payload('logical:' + name + '_a'),
                             (self.output / 'old-images' / (name + '.img')).read_bytes())
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600
                            for p in self.output.rglob('*') if p.is_file()))
        self.assertFalse(self.adb.writes or self.adb.maps)
        self.assertFalse(any(cmd[0] == 'push' for cmd in self.adb.commands))

    def test_snapshot_or_device_geometry_failure_prevents_partition_payload_reads(self):
        self.adb.snapshot = True
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            self.capture()
        self.adb.snapshot = False
        self.adb.overlap_physical = True
        with self.assertRaisesRegex(ValueError, 'overlap'):
            self.capture()
        self.assertEqual(0, self.adb.range_reads)
        self.assertFalse(self.output.exists())

    def test_truncated_and_changed_full_payload_leave_no_result(self):
        self.adb.truncate_payload = True
        with self.assertRaisesRegex(ValueError, 'Short'):
            self.capture()
        self.adb.truncate_payload = False
        self.adb.range_reads = 0
        self.adb.change_on_readback = True
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.capture()
        self.assertFalse(self.output.exists())

    def test_extent_order_is_logical_order_even_when_physical_offsets_reverse(self):
        name = 'product_a'
        extent = self.views[0]['layout']['partitions'][name][0]
        head = {**extent, 'target_data': 4000}
        tail = {**extent, 'logical_sector': 8}
        for view in self.views:
            view['layout']['partitions'][name] = [head, tail]
            view['sizes'][name] = 8192
        super_path = self.adb.capture['super']['path']
        with self.adb.devices[super_path].open('r+b') as stream:
            stream.seek(extent['target_data'] * 512)
            stream.write(b'b' * 4096)
            stream.seek(head['target_data'] * 512)
            stream.write(b'a' * 4096)
        self.capture()
        self.assertEqual(b'a' * 4096 + b'b' * 4096,
                         (self.output / 'old-images/product.img').read_bytes())

    def test_dmctl_mismatch_prevents_payload_reads(self):
        with self.assertRaisesRegex(ValueError, 'dmctl'):
            self.capture(dmctl_pin='e' * 64)
        self.assertEqual(0, self.adb.range_reads)
        self.assertFalse(self.output.exists())
