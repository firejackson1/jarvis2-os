# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def pin(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WriterInputTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.prepared = self.root / 'preflight'
        self.capture = self.root / 'capture'
        self.capture.mkdir()
        (self.capture / 'capture.json').write_text('{}\n')
        self.capture_pin = pin(self.capture / 'capture.json')
        self.fit = {'target_slot': 'a', 'capture_sha256': self.capture_pin,
                    'candidate_images_fit': 7, 'restore_images_verified': 7,
                    'lpdump_sha256': '4' * 64}
        spec = importlib.util.spec_from_file_location('writer_input_test',
            ROOT / 'tools/stage-lcars-writer-inputs.py')
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)

    def make_files(self, rehearsal=False):
        files = {}
        for folder, names in (('images', ['system', 'system_ext', 'product', 'vbmeta', 'vbmeta_system']),
                              ('transition-images', ['init_boot', 'vendor_boot'])):
            directory = self.prepared / folder
            directory.mkdir(parents=True)
            for name in names:
                image = directory / (name + '.img')
                image.write_bytes(name.encode().ljust(4096, b'\0'))
                files[f'{folder}/{image.name}'] = {'bytes': 4096, 'sha256': pin(image)}
        self.receipt = {'format': 1, 'archive_sha256': '1' * 64, 'root_public_key_sha256': '2' * 64,
                        'rehearsal_only': rehearsal, 'avb_chain_verified': True,
                        'stock_profile_sha256': pin(ROOT / 'manifests/avb-stock-15640252-profile.json'),
                        'stock_reference_bytes_verified': True, 'device_contacted': False,
                        'installation_authorized': False, 'files': files, 'saved_capture_fit': self.fit}
        self.receipt_path = self.prepared / 'verification.json'
        self.receipt_path.write_text(json.dumps(self.receipt))
        self.approval = self.root / 'review.json'
        self.approval.write_text(json.dumps({
            'format': 1, 'kind': 'jarvis2-reviewed-lcars-transition', 'target_slot': 'a',
            'preflight_sha256': pin(self.receipt_path), 'capture_sha256': self.capture_pin,
        }))
        self.output = self.root / 'writer-inputs'

    def invoke(self, fit=None):
        with patch.object(self.tool.PREFLIGHT, 'verify_saved_fit', return_value=fit or self.fit):
            return self.tool.stage(self.prepared, pin(self.receipt_path), self.capture,
                                   self.approval, pin(self.approval), self.root / 'lpdump', self.output)

    def test_stages_the_exact_pair_and_leaves_device_authorization_false(self):
        self.make_files()
        status = self.invoke()
        first = self.output / 'candidate-proof.json'
        second = self.output / 'transition-proof.json'
        candidate, transition = [json.loads(path.read_text()) for path in (first, second)]
        self.assertEqual(set(candidate['files']), {'system.img', 'system_ext.img', 'product.img', 'vbmeta.img', 'vbmeta_system.img'})
        self.assertEqual(set(transition['files']), {'init_boot.img', 'vendor_boot.img'})
        self.assertEqual(transition['candidate_proof_sha256'], pin(first))
        self.assertEqual(transition['capture_sha256'], self.capture_pin)
        self.assertEqual(status['transition_proof_sha256'], pin(second))
        self.assertFalse(status['installation_authorized'])

    def test_changed_image_fails_before_outputs(self):
        self.make_files()
        (self.prepared / 'images/system.img').write_bytes(b'x' * 4096)
        with self.assertRaisesRegex(ValueError, 'image bytes differ'):
            self.invoke()
        self.assertFalse(self.output.exists())

    def test_review_for_a_different_capture_is_refused(self):
        self.make_files()
        approval = json.loads(self.approval.read_text())
        approval['capture_sha256'] = '3' * 64
        self.approval.write_text(json.dumps(approval))
        with self.assertRaisesRegex(ValueError, 'Capture|capture'):
            self.invoke()
        self.assertFalse(self.output.exists())

    def test_rehearsal_receipt_is_refused(self):
        self.make_files(rehearsal=True)
        with self.assertRaisesRegex(ValueError, 'production|rehearsal'):
            self.invoke()
        self.assertFalse(self.output.exists())

    def test_recomputed_layout_must_match_the_reviewed_fit(self):
        self.make_files()
        with self.assertRaisesRegex(ValueError, 'fit differs'):
            self.invoke({**self.fit, 'candidate_images_fit': 6})
        self.assertFalse(self.output.exists())
