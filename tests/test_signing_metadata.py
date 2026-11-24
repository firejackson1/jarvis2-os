import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('signing_metadata', ROOT / 'tools/prepare-signing-metadata.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def apk(name, partition='system', certificate='dev/key', compressed=None):
    row = f'name="{name}" certificate="{certificate}.x509.pem" private_key="{certificate}.pk8"'
    if certificate == 'PRESIGNED':
        row = f'name="{name}" certificate="PRESIGNED" private_key=""'
    if compressed:
        row += f' compressed="{compressed}"'
    return row + f' partition="{partition}"'


def apex(name='com.test.apex', partition='system', presigned=False):
    if presigned:
        return f'name="{name}" public_key="PRESIGNED" private_key="PRESIGNED" container_certificate="PRESIGNED" container_private_key="PRESIGNED" partition="{partition}"'
    return f'name="{name}" public_key="dev/module.avbpubkey" private_key="dev/module.pem" container_certificate="dev/module.x509.pem" container_private_key="dev/module.pk8" partition="{partition}"'


def apex_bytes():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        z.writestr('apex_payload.img', b'payload for native inspection')
        z.writestr('apex_manifest.pb', b'\x0a\x08com.test')
        z.writestr('apex_pubkey', b'public key')
    return stream.getvalue()


class SigningMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.input = Path(self.temp.name) / 'input.zip'
        self.output = Path(self.temp.name) / 'output.zip'

    def archive(self, apkrows=None, apexrows=None, entries=None):
        with zipfile.ZipFile(self.input, 'w') as z:
            z.writestr('META/apkcerts.txt', '\n'.join(apkrows or [apk('App.apk')]) + '\n')
            z.writestr('META/apexkeys.txt', '\n'.join(apexrows or []) + '\n')
            for name, data in (entries or {'SYSTEM/app/App/App.apk': b'unchanged apk'}).items():
                z.writestr(name, data)

    def prepare(self, listing=''):
        with patch.object(module.subprocess, 'check_output', return_value=listing) as runner:
            result = module.prepare(self.input, self.output, ('/native/deapexer', '/native/debugfs', '/native/fsck'))
        return result, runner

    def test_filters_unshipped_rows_and_preserves_package_bytes(self):
        self.archive([apk('App.apk'), apk('Missing.apk'), apk('App.apk')], [apex('unshipped.apex')])
        self.prepare()
        with zipfile.ZipFile(self.output) as z:
            self.assertEqual(apk('App.apk') + '\n', z.read('META/apkcerts.txt').decode())
            self.assertEqual(b'', z.read('META/apexkeys.txt'))
            self.assertEqual(b'unchanged apk', z.read('SYSTEM/app/App/App.apk'))

    def test_capex_and_embedded_apks_are_discovered_from_actual_archive(self):
        capex = io.BytesIO()
        with zipfile.ZipFile(capex, 'w') as z:
            z.writestr('original_apex', apex_bytes())
        self.archive([apk('Nested.apk'), apk('Nested.apk')], [apex(), apex('absent.apex')], {'SYSTEM/apex/com.test.capex': capex.getvalue()})
        _, runner = self.prepare('./\n./app/\n./app/Nested/\n./app/Nested/Nested.apk\n./etc/config\n')
        self.assertEqual(1, runner.call_count)
        self.assertEqual('/native/deapexer', runner.call_args.args[0][0])
        with zipfile.ZipFile(self.output) as z:
            self.assertEqual(apk('Nested.apk') + '\n', z.read('META/apkcerts.txt').decode())
            self.assertEqual(apex() + '\n', z.read('META/apexkeys.txt').decode())
            self.assertEqual(capex.getvalue(), z.read('SYSTEM/apex/com.test.capex'))

    def test_presigned_parent_and_embedded_test_keys_stay_presigned_or_unchanged(self):
        self.archive([apk('Google.apk', certificate='PRESIGNED'), apk('Nested.apk')], [apex(presigned=True)], {'PRODUCT/app/Google.apk': b'upstream package', 'SYSTEM/apex/com.test.apex': apex_bytes()})
        # Partition identity must match the actual archive, not metadata basename alone.
        with self.assertRaisesRegex(ValueError, 'metadata'):
            self.prepare('./app/Nested.apk')
        self.archive([apk('Google.apk', partition='product', certificate='PRESIGNED'), apk('Nested.apk')], [apex(presigned=True)], {'PRODUCT/app/Google.apk': b'upstream package', 'SYSTEM/apex/com.test.apex': apex_bytes()})
        self.prepare('./app/Nested.apk')
        with zipfile.ZipFile(self.output) as z:
            self.assertIn('certificate="PRESIGNED"', z.read('META/apkcerts.txt').decode())
            self.assertEqual(b'upstream package', z.read('PRODUCT/app/Google.apk'))
            self.assertEqual(apex_bytes(), z.read('SYSTEM/apex/com.test.apex'))

    def test_missing_metadata_fails_without_output(self):
        self.archive([apk('Wrong.apk')])
        with self.assertRaisesRegex(ValueError, 'metadata'):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_conflicting_partition_rows_rejected(self):
        self.archive([apk('App.apk'), apk('App.apk', certificate='other/key')])
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.prepare()

    def test_global_basename_certificate_conflict_rejected(self):
        self.archive([apk('App.apk'), apk('App.apk', partition='product', certificate='other/key')], entries={'SYSTEM/app/App.apk': b'a', 'PRODUCT/app/App.apk': b'b'})
        with self.assertRaisesRegex(ValueError, 'basename'):
            self.prepare()

    def test_malformed_metadata_and_duplicate_fields_rejected(self):
        for row in [apk('App.apk') + ' garbage', apk('App.apk') + ' partition="system"', 'name="App.apk"', apk('../App.apk')]:
            with self.subTest(row=row):
                self.archive([row])
                with self.assertRaises(ValueError):
                    self.prepare()

    def test_bad_archive_paths_and_symlinks_rejected(self):
        for name in ['SYSTEM/../App.apk', '/SYSTEM/App.apk', 'SYSTEM//app/App.apk']:
            with self.subTest(name=name):
                self.archive(entries={name: b'apk'})
                with self.assertRaises(ValueError):
                    self.prepare()
        self.archive()
        with zipfile.ZipFile(self.input, 'a') as z:
            info = zipfile.ZipInfo('SYSTEM/app/Link.apk')
            info.external_attr = 0o120777 << 16
            z.writestr(info, b'App.apk')
        with self.assertRaisesRegex(ValueError, 'regular'):
            self.prepare()

    def test_duplicate_archive_paths_rejected(self):
        self.archive()
        with zipfile.ZipFile(self.input, 'a') as z:
            with self.assertWarns(UserWarning):
                z.writestr('SYSTEM/app/App/App.apk', b'different')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.prepare()

    def test_embedded_paths_are_validated_and_require_metadata(self):
        for listing in ['../Nested.apk', './app/Missing.apk', './app/Nested.apk\n./app/Nested.apk']:
            with self.subTest(listing=listing):
                self.archive([apk('Nested.apk')], [apex()], {'SYSTEM/apex/com.test.apex': apex_bytes()})
                with self.assertRaises(ValueError):
                    self.prepare(listing)

    def test_refuses_overwriting_existing_output(self):
        self.archive()
        self.output.write_bytes(b'keep existing')
        with self.assertRaises(FileExistsError):
            self.prepare()
        self.assertEqual(b'keep existing', self.output.read_bytes())

    def test_compressed_apk_metadata_must_match_archive(self):
        self.archive([apk('App.apk')], entries={'SYSTEM/app/App.apk.gz': b'upstream gzip bytes'})
        with self.assertRaisesRegex(ValueError, 'compress'):
            self.prepare()
        self.archive([apk('App.apk', compressed='gz')], entries={'SYSTEM/app/App.apk.gz': b'upstream gzip bytes'})
        self.prepare()
        with zipfile.ZipFile(self.output) as z:
            self.assertEqual(b'upstream gzip bytes', z.read('SYSTEM/app/App.apk.gz'))

    def test_input_archive_symlink_is_rejected(self):
        self.archive()
        alias = self.input.with_name('alias.zip')
        alias.symlink_to(self.input)
        with self.assertRaisesRegex(ValueError, 'regular'):
            module.prepare(alias, self.output, ('unused', 'unused', 'unused'))

    def test_metadata_symlink_entry_is_rejected(self):
        with zipfile.ZipFile(self.input, 'w') as z:
            info = zipfile.ZipInfo('META/apkcerts.txt')
            info.external_attr = 0o120777 << 16
            z.writestr(info, apk('App.apk'))
            z.writestr('META/apexkeys.txt', '')
            z.writestr('SYSTEM/app/App.apk', b'apk')
        with self.assertRaisesRegex(ValueError, 'regular'):
            self.prepare()
