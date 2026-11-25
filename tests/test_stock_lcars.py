# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import stat
import sys
import unittest

from test_ramdisk import archive, elf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_stock_lcars import AUDIT, EXTENSION, STOCK_ALIAS, add_extension, record


class StockLcarsArchiveTests(unittest.TestCase):
    def test_factory_alias_preserves_payload_and_metadata(self):
        regular = stat.S_IFREG | 0o644
        original = elf(32, 40)
        source = archive([
            ('system/bin/fastbootd', regular, b'untouched'),
            (EXTENSION, regular, original, {0: 20, 2: 7, 3: 8, 5: 77}),
        ], crc=True)
        # The stock CPIO trailer has a higher inode than any file.
        inode_offset = source.rindex(b'070702') + 6
        source = source[:inode_offset] + b'00000063' + source[inode_offset + 8:]
        plugin = original + b'new bytes'
        result, untouched = add_extension(source, plugin)
        before = AUDIT.parse_cpio(source)
        after = AUDIT.parse_cpio(result)
        self.assertEqual(untouched, 1)
        self.assertEqual(record(source, before['system/bin/fastbootd']),
                         record(result, after['system/bin/fastbootd']))
        self.assertEqual(after[EXTENSION]['data'], plugin)
        self.assertEqual(after[STOCK_ALIAS]['data'], original)
        self.assertEqual(after[STOCK_ALIAS]['ino'], 100)
        for field in ('mode', 'uid', 'gid', 'nlink', 'mtime'):
            self.assertEqual(before[EXTENSION][field], after[STOCK_ALIAS][field])

    def test_arm64_replacement_is_rejected(self):
        source = archive([(EXTENSION, stat.S_IFREG | 0o644, elf(32, 40))])
        with self.assertRaisesRegex(ValueError, 'ARM32 shared libraries'):
            add_extension(source, elf(64, 183))
