# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseAssetTests(unittest.TestCase):
    def verify(self, directory, pin):
        spec = importlib.util.spec_from_file_location('release_assets', ROOT/'tools/verify-release-assets.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        return verifier.verify(directory, pin)

    def fixture(self, directory):
        payload = b'fixture payload'
        digest = hashlib.sha256(payload).hexdigest()
        name = 'rom.zip'
        (directory/name).write_bytes(payload)
        receipt = {'format': 2, 'kind': 'unofficial-developer-preview-staging-receipt',
                   'product_source_revision': 'a'*40, 'packaging_tool_revision': 'b'*40,
                   'assets': [{'file': name, 'role': 'offline-candidate',
                               'bytes': len(payload), 'sha256': digest}]}
        receipt_path = directory/'release-asset-receipt.json'
        receipt_path.write_text(json.dumps(receipt))
        pin = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        (directory/'SHA256SUMS.txt').write_text(
            f'{digest}  {name}\n{pin}  release-asset-receipt.json\n')
        return pin

    def test_exact_release_files_and_both_metadata_members_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            pin = self.fixture(directory)
            report = self.verify(directory, pin)
            self.assertEqual(set(report['files']), {'rom.zip', 'release-asset-receipt.json', 'SHA256SUMS.txt'})
            self.assertEqual(report['files']['release-asset-receipt.json']['sha256'], pin)
            self.assertFalse(report['release_qualification_checked'])

    def test_rejects_extra_or_altered_asset_and_wrong_receipt_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            pin = self.fixture(directory)
            with self.assertRaisesRegex(ValueError, 'receipt SHA-256'):
                self.verify(directory, '0'*64)
            extra = directory/'unreviewed.zip'
            extra.touch()
            with self.assertRaisesRegex(ValueError, 'Unknown.*input'):
                self.verify(directory, pin)
            extra.unlink()
            (directory/'rom.zip').write_bytes(b'tampered bytes!')
            with self.assertRaisesRegex(ValueError, 'Asset bytes differ.*rom.zip'):
                self.verify(directory, pin)

    def test_rejects_checksum_list_that_omits_the_receipt_or_duplicates_an_asset(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            pin = self.fixture(directory)
            listing = directory/'SHA256SUMS.txt'
            line = listing.read_text().splitlines()[0] + '\n'
            for content in (line, line * 2):
                listing.write_text(content)
                with self.assertRaisesRegex(ValueError, 'Checksum list'):
                    self.verify(directory, pin)
