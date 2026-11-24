"""Exercise real Brotli extraction and reject malformed or unsafe destinations."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/extract-webview-credits.py"
HTML = b"<html><title>Credits</title>" + b"Copyright license\n" * 101 + b"</html>"
# Brotli-compressed HTML above; test execution only needs the decoder library.
BROTLI = bytes.fromhex(
    "1b3c07004427e73739c8773969415ac1061cb8344ea38cb8100d133991969c8e5149"
    "b0e9ca76cd5f1aac1ccdbbb0a011af13"
)


def pack(payload):
    return (struct.pack("<IB3xHH", 5, 1, 1, 0)
            + struct.pack("<HIHI", 41071, 24, 0, 24 + len(payload)) + payload)


def compressed(payload=BROTLI, size=len(HTML)):
    return b"\x1e\x9b" + size.to_bytes(6, "little") + payload


class WebviewCreditsTests(unittest.TestCase):
    def invoke(self, data, existing=None, duplicate=False):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            apk, output = work / "webview.apk", work / "credits.html"
            with zipfile.ZipFile(apk, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("assets/resources.pak+com.android.webview+", data)
                if duplicate:
                    archive.writestr("assets/resources.pak", data)
            if existing is not None:
                output.write_bytes(existing)
            result = subprocess.run([sys.executable, str(TOOL), str(apk), str(output)],
                                    capture_output=True, text=True)
            return result, output.read_bytes() if output.exists() else None

    def assert_rejected(self, data, message, **kwargs):
        result, output = self.invoke(data, **kwargs)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIsNone(output)

    def test_extracts_actual_brotli_bytes_and_reports_hash(self):
        result, output = self.invoke(pack(compressed()))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, HTML)
        self.assertEqual(json.loads(result.stdout), {
            "resource_id": 41071, "bytes": len(HTML),
            "sha256": hashlib.sha256(HTML).hexdigest()})

    def test_existing_output_is_never_overwritten(self):
        result, output = self.invoke(pack(compressed()), existing=b"keep")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, b"keep")
        self.assertNotIn("Traceback", result.stderr)

    def test_truncated_header_rejected_cleanly(self):
        self.assert_rejected(b"\x05\x00", "header")

    def test_truncated_entry_table_rejected(self):
        self.assert_rejected(struct.pack("<IB3xHH", 5, 1, 10, 0), "table")

    def test_offsets_cannot_point_into_table_or_beyond_data(self):
        data = bytearray(pack(compressed()))
        for offset in (0, len(data) + 1):
            with self.subTest(offset=offset):
                struct.pack_into("<I", data, 14, offset)
                self.assert_rejected(bytes(data), "offset")

    def test_brotli_declared_length_must_match_actual(self):
        self.assert_rejected(pack(compressed(size=len(HTML) + 1)), "length")

    def test_brotli_allocation_is_bounded(self):
        self.assert_rejected(pack(compressed(size=16 * 1024 * 1024 + 1)), "budget")

    def test_zip_member_unpacked_size_is_bounded(self):
        self.assert_rejected(b"x" * (8 * 1024 * 1024 + 1), "8MiB")

    def test_duplicate_pak_entries_are_rejected(self):
        self.assert_rejected(pack(compressed()), "one resources.pak", duplicate=True)

    def test_corrupt_brotli_rejected_without_output(self):
        self.assert_rejected(pack(compressed(payload=b"invalid")), "Brotli")


if __name__ == "__main__":
    unittest.main()
