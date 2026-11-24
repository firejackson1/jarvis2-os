"""Run the actual Music destroy callback with an observable owned resource.

Android framework plumbing is not emulated; full-class SDK compilation and a
real-device lifecycle check are separate gates.
"""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/MediaPlaybackService.java'
PATCH = ROOT / 'patches/Music/0001-release-media-session-on-destroy.patch'
RELATIVE = 'src/com/android/music/MediaPlaybackService.java'


class MusicSessionCleanupTests(unittest.TestCase):
    def test_patched_callback_releases_its_session_and_superclass(self):
        original = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         'f1c30950182cd36f08ff8dfede5ff9f31815ac77524f22c8081d7ec7b9a8bf14')
        projects = ET.parse(ROOT / 'manifests/lineage21-pinned.xml').getroot()
        revision = next(p.get('revision') for p in projects.findall('project')
                        if p.get('path') == 'packages/apps/Music')
        self.assertEqual(revision, 'c119d5a52f80289c7f939746ddc31c8bcee2a3ca')
        self.assertTrue(PATCH.is_file(), 'Music lifecycle patch is missing')
        with tempfile.TemporaryDirectory(prefix='music lifecycle ') as directory:
            work = Path(directory)
            source = work / RELATIVE
            source.parent.mkdir(parents=True)
            source.write_bytes(original)
            subprocess.run(['git', 'init', '-q', str(work)], check=True)
            subprocess.run(['git', '-C', str(work), 'apply', str(PATCH)], check=True)

            def exercise(text):
                # Compile the callback itself, preserving all its statements.
                start = text.index('public void onDestroy() {')
                end = text.index('\n    @Override', start)
                callback = text[start:end].strip()
                java = '''class Parent {
    int destroys;
    public void onDestroy() { destroys++; }
}
class OwnedSession {
    static int live;
    boolean released;
    OwnedSession() { live++; }
    void release() {
        if (released) throw new AssertionError("duplicate release");
        released = true;
        live--;
    }
}
public class Lifecycle extends Parent {
    OwnedSession mSession;
    CALLBACK
    public static void main(String[] args) {
        Lifecycle service = new Lifecycle();
        OwnedSession owned = new OwnedSession();
        service.mSession = owned;
        service.onDestroy();
        if (OwnedSession.live != 0 || !owned.released || service.mSession != null)
            throw new AssertionError("service leaked its owned session");
        if (service.destroys != 1) throw new AssertionError("super cleanup skipped");
        service.onDestroy();
        if (OwnedSession.live != 0 || service.destroys != 2)
            throw new AssertionError("repeated cleanup changed ownership");
        Lifecycle empty = new Lifecycle();
        empty.onDestroy();
        if (OwnedSession.live != 0 || empty.destroys != 1)
            throw new AssertionError("null-session cleanup skipped superclass");
    }
}
'''.replace('CALLBACK', callback)
                (work / 'Lifecycle.java').write_text(java)
                subprocess.run(['javac', '--release', '11', '-d', str(work),
                                str(work / 'Lifecycle.java')], check=True)
                return subprocess.run(['java', '-cp', str(work), 'Lifecycle'],
                                      capture_output=True, text=True, timeout=10)

            patched = exercise(source.read_text())
            self.assertEqual(patched.returncode, 0, patched.stderr)
            unpatched = exercise(original.decode())
            self.assertNotEqual(unpatched.returncode, 0)
            self.assertIn('service leaked its owned session', unpatched.stderr)
