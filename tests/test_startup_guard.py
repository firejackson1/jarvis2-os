# SPDX-License-Identifier: Apache-2.0
"""Exercise startup failure gates without loading modules or mounting anything."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'ramboot/startup-guard.sh'
SHELL = os.environ.get('JARVIS_GUARD_TEST_SHELL', '/bin/sh')
MODULES = '''amlogic-gkitool.ko amlogic-debug-iotrace.ko amlogic-uart.ko
amlogic-hwspinlock.ko amlogic-debug.ko amlogic-secmon.ko amlogic-cpuinfo.ko
page_trace.ko amlogic-memory-debug.ko aml_cma.ko clk-scmi.ko amlogic-clk.ko
amlogic-clk-soc-s7d.ko amlogic-aoclk-soc-t5w.ko amlogic-gpio.ko
amlogic-pinctrl-soc-s7d.ko amlogic-mailbox.ko amlogic-pwm.ko pwm-regulator.ko
gpio-regulator.ko amlogic-reset.ko amlogic-power.ko amlogic-cpufreq.ko
amlogic-thermal.ko amlogic-usb.ko cqhci.ko amlogic-mmc.ko'''.split()
HARDWARE = '''amlogic-efuse-unifykey.ko tee.ko amlogic-tee.ko videobuf-core.ko
dvb-core.ko amlogic-pm.ko amlogic-input.ko amlogic-dvb.ko aml_media.ko aml_drm.ko'''.split()


class StartupGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='startup guard ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = self.root / 'calls'
        self.manifest = self.root / 'modules.sha256'
        for module in MODULES + HARDWARE:
            (self.root / module).write_bytes(b'fixture module ' + module.encode())
        self.manifest.write_text(''.join(
            hashlib.sha256((self.root / name).read_bytes()).hexdigest() + '  ' + name + '\n'
            for name in MODULES))
        self.hardware_manifest = self.root / 'hardware.sha256'
        self.hardware_manifest.write_text(''.join(
            hashlib.sha256((self.root / name).read_bytes()).hexdigest() + '  ' + name + '\n'
            for name in HARDWARE))
        self.proc = self.root / 'proc'
        self.sys = self.root / 'sys'
        self.proc.mkdir()
        (self.sys / 'firmware/devicetree/base').mkdir(parents=True)
        (self.proc / 'cmdline').write_text('rdinit=/ramboot-init')
        (self.proc / 'bootconfig').write_text('')
        (self.sys / 'firmware/devicetree/base/compatible').write_bytes(b's7d_s905x5m_bm201-3g\0')
        (self.root / 'kernel.release').write_text('fixture-release\n')
        self.bb = self.root / 'safe commands'
        self.bb.write_text('''#!/bin/sh
case "$1" in
  sha256sum|cat|cmp) exec "$@";;
  insmod) printf '%s\\n' "${2##*/}" >> "$CALLS"
          [ "${2##*/}" != "$FAIL_MODULE" ];;
  uname) printf '%s\\n' "$KERNEL_RELEASE";;
  stat) printf '%s\\n' "$FILESYSTEM";;
  mount) printf 'mount:%s\\n' "$3" >> "$CALLS"; [ "$3" != "$FAIL_MOUNT_FS" ];;
  umount) printf 'umount:%s\\n' "${2##*/}" >> "$CALLS"; [ "$2" != "$FAIL_UMOUNT" ];;
  sleep) printf 'sleep\\n' >> "$CALLS";;
  *) echo "forbidden host operation: $1" >&2; exit 99;;
esac
''')
        self.bb.chmod(0o755)

    def run_library(self, script, **extra):
        self.assertTrue(LIB.is_file(), 'Startup guard implementation is missing')
        env = dict(os.environ, GUARD_LIBRARY=str(LIB), GUARD_BB=str(self.bb),
                   GUARD_MODULE_DIR=str(self.root), GUARD_MODULE_MANIFEST=str(self.manifest),
                   GUARD_HARDWARE_MANIFEST=str(self.hardware_manifest),
                   GUARD_RUNTIME=str(self.root), GUARD_WORKDIR=str(self.root),
                   GUARD_PROCROOT=str(self.proc), GUARD_SYSROOT=str(self.sys),
                   KERNEL_RELEASE='fixture-release', FILESYSTEM='tmpfs',
                   FAIL_MOUNT_FS='', FAIL_UMOUNT='', CALLS=str(self.calls), FAIL_MODULE='')
        env.update(extra)
        result = subprocess.run([SHELL, '-c', '. "$GUARD_LIBRARY"\n' + script],
                                env=env, capture_output=True, text=True, timeout=15)
        self.assertNotIn('forbidden host operation:', result.stderr)
        calls = self.calls.read_text().splitlines() if self.calls.exists() else []
        return result, calls

    def test_entrypoint_refuses_host_execution_before_using_busybox(self):
        init = ROOT / 'ramboot/init'
        self.assertTrue(init.is_file(), 'PID 1 entrypoint is missing')
        result = subprocess.run([SHELL, str(init)], capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires PID 1', result.stderr)

    def test_exact_reviewed_module_sequence_is_verified_before_loading(self):
        result, calls = self.run_library('guard_load_storage_modules')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, MODULES)

    def test_changed_missing_reordered_or_extra_module_prevents_all_loading(self):
        original = self.manifest.read_text()
        for change in ('hash', 'missing', 'reorder', 'extra', 'path'):
            with self.subTest(change=change):
                lines = original.splitlines()
                if change == 'hash':
                    lines[0] = '0' * 64 + '  ' + MODULES[0]
                elif change == 'missing':
                    lines.pop()
                elif change == 'reorder':
                    lines[0], lines[1] = lines[1], lines[0]
                elif change == 'extra':
                    lines.append(lines[-1])
                else:
                    lines[0] = lines[0].replace(MODULES[0], '../' + MODULES[0])
                self.manifest.write_text('\n'.join(lines) + '\n')
                result, calls = self.run_library('guard_load_storage_modules')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])

    def test_failed_module_load_stops_the_sequence(self):
        result, calls = self.run_library('guard_load_storage_modules', FAIL_MODULE=MODULES[1])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, MODULES[:2])

    def test_hardware_modules_have_a_separate_verified_sequence(self):
        result, calls = self.run_library('guard_load_hardware_modules')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, HARDWARE)
        self.calls.unlink()
        original = self.hardware_manifest.read_text()
        self.hardware_manifest.write_text(original.replace(HARDWARE[-1], '../' + HARDWARE[-1]))
        result, calls = self.run_library('guard_load_hardware_modules')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_missing_or_changed_hardware_input_prevents_all_hardware_loading(self):
        original = self.hardware_manifest.read_text()
        self.hardware_manifest.unlink()
        result, calls = self.run_library('guard_load_hardware_modules')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.hardware_manifest.write_text(original)
        (self.root / HARDWARE[-1]).write_bytes(b'changed module')
        result, calls = self.run_library('guard_load_hardware_modules')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_hardware_module_failure_stops_before_later_modules(self):
        result, calls = self.run_library('guard_load_hardware_modules', FAIL_MODULE=HARDWARE[1])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, HARDWARE[:2])

    def test_board_kernel_and_boot_mode_are_checked_before_modules(self):
        result, calls = self.run_library('guard_validate_boot')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, [])
        for path, invalid in (
                (self.root / 'kernel.release', b'other-kernel\n'),
                (self.sys / 'firmware/devicetree/base/compatible', b'other-board\0'),
                (self.proc / 'cmdline', b'androidboot.force_normal_boot=1'),
                (self.proc / 'bootconfig', b'androidboot.force_normal_boot = "1"'),
                (self.proc / 'bootconfig', b'androidboot.hibernation_resume_device = "x"')):
            with self.subTest(path=path.name, invalid=invalid):
                previous = path.read_bytes()
                path.write_bytes(invalid)
                result, calls = self.run_library('guard_validate_boot')
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                path.write_bytes(previous)

    def test_minimal_views_reject_non_ram_mountpoints_and_stop_on_mount_failure(self):
        for filesystem, failed, expected in (
                ('ext4', '', []), ('proc', '', []),
                ('tmpfs', 'proc', ['mount:proc']),
                ('ramfs', 'sysfs', ['mount:proc', 'mount:sysfs']),
                ('tmpfs', '', ['mount:proc', 'mount:sysfs'])):
            with self.subTest(filesystem=filesystem, failed=failed):
                self.calls.unlink(missing_ok=True)
                result, calls = self.run_library('guard_prepare_views',
                                                 FILESYSTEM=filesystem, FAIL_MOUNT_FS=failed)
                self.assertEqual(result.returncode == 0, filesystem == 'tmpfs' and not failed)
                self.assertEqual(calls, expected)

    def test_storage_wait_is_bounded_and_stops_as_soon_as_ready(self):
        script = '''
attempt=0
guard_protect_storage() {
    attempt=$((attempt + 1))
    printf 'attempt:%s\\n' "$attempt" >> "$CALLS"
    [ "$attempt" -ge "$READY_AFTER" ]
}
guard_wait_storage
'''
        for ready, attempts, success in ((1, 1, True), (3, 3, True), (11, 10, False)):
            with self.subTest(ready=ready):
                self.calls.unlink(missing_ok=True)
                result, calls = self.run_library(script, READY_AFTER=str(ready))
                self.assertEqual(result.returncode == 0, success, result.stderr)
                self.assertEqual([c for c in calls if c.startswith('attempt:')],
                                 ['attempt:' + str(n) for n in range(1, attempts + 1)])
                self.assertEqual(calls.count('sleep'), attempts - 1)

    def test_cleanup_failure_prevents_the_next_mount_cleanup(self):
        result, calls = self.run_library('guard_cleanup_views', FAIL_UMOUNT=str(self.sys))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, ['umount:sys'])

    def test_startup_failure_never_reaches_ready_state(self):
        for failed in ('views', 'board', 'modules', 'storage', 'hardware', 'recheck', 'cleanup'):
            with self.subTest(failed=failed):
                script = '''
record() { printf '%s\\n' "$1" >> "$CALLS"; [ "$1" != "$FAIL_STEP" ]; }
guard_prepare_views() { record views; }
guard_validate_boot() { record board; }
guard_load_storage_modules() { record modules; }
guard_wait_storage() { record storage; }
guard_load_hardware_modules() { record hardware; }
guard_protect_storage() { record recheck; }
guard_cleanup_views() { record cleanup; }
guard_startup && printf 'ready\\n' >> "$CALLS"
'''
                self.calls.unlink(missing_ok=True)
                result, calls = self.run_library(script, FAIL_STEP=failed)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('ready', calls)
                self.assertEqual(calls[-1], failed)

    def test_complete_startup_reaches_ready_only_after_all_gates(self):
        script = '''
record() { printf '%s\\n' "$1" >> "$CALLS"; }
guard_prepare_views() { record views; }
guard_validate_boot() { record board; }
guard_load_storage_modules() { record modules; }
guard_wait_storage() { record storage; }
guard_load_hardware_modules() { record hardware; }
guard_protect_storage() { record recheck; }
guard_cleanup_views() { record cleanup; }
guard_startup && printf 'ready\\n' >> "$CALLS"
'''
        result, calls = self.run_library(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['views', 'board', 'modules', 'storage', 'hardware',
                                 'recheck', 'cleanup', 'ready'])


if __name__ == '__main__':
    unittest.main()
