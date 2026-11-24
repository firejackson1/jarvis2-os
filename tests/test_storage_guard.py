# SPDX-License-Identifier: Apache-2.0
"""Exercise selection/race handling without host block devices or mounts."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'ramboot/storage-guard.sh'
SHELL = os.environ.get('JARVIS_GUARD_TEST_SHELL', '/bin/sh')


class StorageGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='guard fixture ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sys = self.root / 'sys'
        self.dev = self.root / 'dev'
        self.work = self.root / 'work'
        for path in (self.sys, self.dev, self.work):
            path.mkdir()
        self.calls = self.root / 'calls'
        self.bb = self.root / 'safe commands'
        self.bb.write_text('''#!/bin/sh
case "$1" in cat|sort|cmp) exec "$@";;
  *) echo "forbidden host operation: $1" >&2; exit 99;;
esac
''')
        self.bb.chmod(0o755)

    def node(self, name, device, kind=None, removable='0'):
        node = self.sys / name
        node.mkdir(exist_ok=True)
        (node / 'dev').write_text(device + '\n')
        if kind is not None:
            (node / 'device').mkdir(exist_ok=True)
            (node / 'device/type').write_text(kind + '\n')
            (node / 'removable').write_text(removable + '\n')

    def mmc(self, base='mmcblk0', major=179):
        self.node(base, f'{major}:0', 'MMC')
        self.node(base + 'boot0', f'{major}:8')
        self.node(base + 'boot1', f'{major}:16')
        self.node(base + 'p1', f'{major}:1')

    def run_guard(self, fail='', mutation='', real_primitive=False):
        self.assertTrue(LIB.is_file(), 'Storage guard implementation is missing')
        self.calls.unlink(missing_ok=True)
        callback = '''
guard_protect_node() {
    printf '%s %s:%s\\n' "$1" "$2" "$3" >> "$CALLS"
    [ "$1" != "$FAIL_NODE" ] || return 1
    if [ "$1" = mmcblk0p1 ]; then
        case "$GUARD_MUTATION" in
          add) mkdir -p "$GUARD_SYSFS/mmcblk0p2"
               printf '179:2\\n' > "$GUARD_SYSFS/mmcblk0p2/dev";;
          renumber) printf '179:2\\n' > "$GUARD_SYSFS/mmcblk0p1/dev";;
          remove) rm "$GUARD_SYSFS/mmcblk0boot1/dev"
                  rmdir "$GUARD_SYSFS/mmcblk0boot1";;
        esac
    fi
}
'''
        script = '. "$GUARD_LIBRARY"\n'
        if not real_primitive:
            script += callback
        script += '\nguard_protect_storage\n'
        env = dict(os.environ, LC_ALL='C', GUARD_LIBRARY=str(LIB),
                   GUARD_SYSFS=str(self.sys), GUARD_DEVROOT=str(self.dev),
                   GUARD_WORKDIR=str(self.work), GUARD_BB=str(self.bb),
                   CALLS=str(self.calls), FAIL_NODE=fail,
                   GUARD_MUTATION=mutation)
        result = subprocess.run([SHELL, '-c', script], env=env,
                                capture_output=True, text=True, timeout=5)
        calls = self.calls.read_text().splitlines() if self.calls.exists() else []
        self.assertNotIn('forbidden host operation:', result.stderr)
        return result, calls

    def test_whole_boot_and_partitions_are_protected_but_other_disks_are_not(self):
        self.mmc()
        self.node('sda', '8:0')
        self.node('mmcblk1', '179:32', 'SD', '1')
        self.node('mmcblk01', '179:64', 'SD', '1')
        self.node('mmcblk0p1unrelated', '8:16')
        result, calls = self.run_guard()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['mmcblk0 179:0', 'mmcblk0boot0 179:8',
                                 'mmcblk0boot1 179:16', 'mmcblk0p1 179:1'])

    def test_no_internal_mmc_fails_without_protection_calls(self):
        self.node('mmcblk0', '179:0', 'SD', '1')
        result, calls = self.run_guard()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_ambiguous_internal_devices_fail_before_any_protection(self):
        self.mmc()
        self.mmc('mmcblk1', 180)
        result, calls = self.run_guard()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])

    def test_missing_boot_device_or_partition_fails_closed(self):
        for name in ('mmcblk0boot1', 'mmcblk0p1'):
            with self.subTest(name=name):
                self.mmc()
                node = self.sys / name
                (node / 'dev').unlink()
                node.rmdir()
                result, calls = self.run_guard()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])

    def test_invalid_or_duplicate_device_numbers_fail_before_protection(self):
        self.mmc()
        for device in ('179:1extra', ':1', '179:1:2', '999999999999:1', '179:0'):
            with self.subTest(device=device):
                (self.sys / 'mmcblk0p1/dev').write_text(device + '\n')
                result, calls = self.run_guard()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])

    def test_failed_protection_stops_without_reporting_success(self):
        self.mmc()
        result, calls = self.run_guard(fail='mmcblk0boot0')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, ['mmcblk0 179:0', 'mmcblk0boot0 179:8'])

    def test_late_partition_requires_a_new_complete_scan(self):
        self.mmc()
        result, _ = self.run_guard(mutation='add')
        self.assertNotEqual(result.returncode, 0)
        result, calls = self.run_guard()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('mmcblk0p2 179:2', calls)

    def test_removed_or_renumbered_node_invalidates_the_scan(self):
        for mutation in ('renumber', 'remove'):
            with self.subTest(mutation=mutation):
                self.mmc()
                result, _ = self.run_guard(mutation=mutation)
                self.assertNotEqual(result.returncode, 0)

    def test_snapshot_symlink_is_rejected_without_touching_its_target(self):
        self.mmc()
        target = self.root / 'untouched'
        target.write_text('keep this')
        (self.work / 'mmc-before').symlink_to(target)
        result, calls = self.run_guard()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
        self.assertEqual(target.read_text(), 'keep this')

    def test_real_primitive_rejects_existing_regular_file(self):
        self.mmc()
        (self.dev / 'mmcblk0').write_text('not a block device')
        result, _ = self.run_guard(real_primitive=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.dev / 'mmcblk0').read_text(), 'not a block device')

    def test_real_primitive_rejects_device_symlink(self):
        self.mmc()
        target = self.root / 'not a device'
        target.write_text('keep this')
        (self.dev / 'mmcblk0').symlink_to(target)
        result, _ = self.run_guard(real_primitive=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), 'keep this')

    def test_readonly_primitive_requires_successful_setter_and_exact_readback(self):
        self.bb.write_text('''#!/bin/sh
[ "$1" = blockdev ] || exit 99
printf '%s\\n' "$2" >> "$CALLS"
case "$2" in
  --setro) exit "$SET_STATUS";;
  --getro) printf '%s\\n' "$READBACK"; exit "$GET_STATUS";;
  *) exit 99;;
esac
''')
        for setter, getter, readback, success in (
                (0, 0, '1', True), (1, 0, '1', False),
                (0, 1, '1', False), (0, 0, '0', False),
                (0, 0, '1unexpected', False)):
            with self.subTest(setter=setter, getter=getter, readback=readback):
                self.calls.unlink(missing_ok=True)
                env = dict(os.environ, GUARD_LIBRARY=str(LIB), GUARD_BB=str(self.bb),
                           CALLS=str(self.calls), SET_STATUS=str(setter),
                           GET_STATUS=str(getter), READBACK=readback)
                result = subprocess.run(
                    [SHELL, '-c', '. "$GUARD_LIBRARY"; guard_set_readonly /unused/device'],
                    env=env, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode == 0, success, result.stderr)
                self.assertEqual(self.calls.read_text().splitlines(),
                                 ['--setro'] if setter else ['--setro', '--getro'])


if __name__ == '__main__':
    unittest.main()
