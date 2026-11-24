"""Compile the actual patched adbd policy for Android and host behavior."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "patches/Adb/0001-explicit-port-disables-android-network-fallback.patch"


class AdbListenerPolicyTests(unittest.TestCase):
    def test_android_opt_in_and_unchanged_host_fallback(self):
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler, "A C++17 compiler is required")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            subprocess.run([
                "git", "-C", directory, "apply", "--include=daemon/listener_policy.h", str(PATCH)
            ], check=True)
            (work / "check.cpp").write_text(r'''
#include "daemon/listener_policy.h"
#include <cstdio>
struct Case { const char* port; bool usb; int android_port; int host_port; };
int main() {
    const Case cases[] = {
        {"", false, 5555, 5555}, {"", true, 0, 0},
        {"-1", false, 0, 5555}, {"-1", true, 0, 0},
        {"0", false, 0, 5555}, {"0", true, 0, 0},
        {"5556", false, 5556, 5556}, {"5556", true, 5556, 5556},
        {" 5557suffix", false, 5557, 5557},
        {"invalid", false, 0, 5555}, {"invalid", true, 0, 0},
    };
    for (const auto& c : cases) {
#ifdef __ANDROID__
        const int expected = c.android_port;
#else
        const int expected = c.host_port;
#endif
        const int actual = AdbTcpListenPort(c.port, c.usb, 5555);
        if (actual != expected) {
            std::fprintf(stderr, "port=%s usb=%d expected=%d actual=%d\n",
                         c.port, c.usb, expected, actual);
            return 1;
        }
    }
}
''')
            for mode in ("android", "host"):
                with self.subTest(mode=mode):
                    binary = work / mode
                    flags = ["-D__ANDROID__"] if mode == "android" else []
                    subprocess.run([
                        compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", *flags,
                        str(work / "check.cpp"), "-o", str(binary)
                    ], check=True)
                    result = subprocess.run([str(binary)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
