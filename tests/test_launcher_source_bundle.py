import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile
import warnings

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/assemble-launcher-sources.py'


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        spec = importlib.util.spec_from_file_location('source_bundle', SCRIPT)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.data = b'Copyright contributor\nsource\n'
        (self.root / 'source.txt').write_bytes(self.data)
        self.manifest = {'format': 1, 'files': [self.entry('source.txt')]}

    def entry(self, path, destination=None):
        data = (self.root / path).read_bytes()
        return {'root': 'inputs', 'path': path, 'destination': destination or path,
                'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

    def assemble(self, name='bundle.tar.gz'):
        return self.tool.assemble(self.manifest, {'inputs': self.root}, self.root / name)

    def test_deterministic_preserves_exact_sources(self):
        a = self.assemble('a.tar.gz')
        (self.root / 'source.txt').touch()
        b = self.assemble('b.tar.gz')
        self.assertEqual(a, b)
        with tarfile.open(self.root / 'a.tar.gz') as archive:
            self.assertEqual(archive.extractfile('source.txt').read(), self.data)
            self.assertEqual(archive.getmember('source.txt').mtime, 0)
            self.assertEqual(archive.getnames(), ['SOURCE-BUNDLE.json', 'source.txt'])

    def test_tampered_source_fails_without_output(self):
        (self.root / 'source.txt').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'hash|size'):
            self.assemble()
        self.assertFalse((self.root / 'bundle.tar.gz').exists())

    def test_traversal_and_absolute_paths_rejected(self):
        for key in ('path', 'destination'):
            for bad in ('.', '../escape', '/absolute', 'a/../escape', 'a\\escape'):
                with self.subTest(key=key, bad=bad):
                    self.manifest['files'][0][key] = bad
                    with self.assertRaises(ValueError):
                        self.assemble()
            self.manifest['files'][0][key] = 'source.txt'

    def test_duplicate_destination_rejected(self):
        self.manifest['files'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.assemble()

    def test_file_directory_destination_collision_rejected(self):
        self.manifest['files'] = [self.entry('source.txt', 'a'),
                                  self.entry('source.txt', 'a/b')]
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.assemble()

    def test_symlink_escape_rejected(self):
        (self.root / 'link').symlink_to('/etc/passwd')
        self.manifest['files'][0]['path'] = 'link'
        with self.assertRaises(ValueError):
            self.assemble()

    def test_unsafe_nested_archive_rejected(self):
        p = self.root / 'bad.tar.gz'
        with tarfile.open(p, 'w:gz') as archive:
            member = tarfile.TarInfo('../escape')
            member.size = 1
            archive.addfile(member, io.BytesIO(b'x'))
        self.manifest['files'] = [dict(self.entry(p.name), archive='tar')]
        with self.assertRaises(ValueError):
            self.assemble()

    def test_external_source_link_requires_exact_declaration(self):
        p = self.root / 'source.tar.gz'
        with tarfile.open(p, 'w:gz') as archive:
            member = tarfile.TarInfo('test/sibling')
            member.type = tarfile.SYMTYPE
            member.linkname = '../../sibling/test'
            archive.addfile(member)
        entry = dict(self.entry(p.name), archive='tar')
        self.manifest['files'] = [entry]
        with self.assertRaises(ValueError):
            self.assemble()
        entry['external_source_links'] = {'test/sibling': '../../sibling/other'}
        with self.assertRaises(ValueError):
            self.assemble()
        entry['external_source_links'] = {'test/sibling': '../../sibling/test'}
        self.assemble()
        # The link remains metadata inside the unchanged source archive.
        self.assertFalse((self.root / 'sibling').exists())

    def test_same_size_hash_tampering_rejected(self):
        (self.root / 'source.txt').write_bytes(b'x' * len(self.data))
        with self.assertRaisesRegex(ValueError, 'hash'):
            self.assemble()

    def test_zip_duplicate_and_traversal_rejected(self):
        for names in [('a', 'a'), ('../escape',)]:
            with self.subTest(names=names):
                p = self.root / 'bad.zip'
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    with zipfile.ZipFile(p, 'w') as archive:
                        for name in names:
                            archive.writestr(name, 'source')
                self.manifest['files'] = [dict(self.entry(p.name), archive='zip')]
                with self.assertRaises(ValueError):
                    self.assemble()

    def test_existing_output_never_overwritten(self):
        output = self.root / 'bundle.tar.gz'
        output.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            self.assemble()
        self.assertEqual(output.read_bytes(), b'existing')

    def test_unlisted_files_excluded(self):
        (self.root / 'private-key').write_bytes(b'never bundle me')
        self.assemble()
        with tarfile.open(self.root / 'bundle.tar.gz') as archive:
            self.assertNotIn('private-key', archive.getnames())


if __name__ == '__main__':
    unittest.main()
