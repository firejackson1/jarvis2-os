# SPDX-License-Identifier: Apache-2.0
"""Test RAM USB setup without mounting filesystems or creating device nodes."""
import os
from pathlib import Path
import select
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = os.environ.get('JARVIS_GUARD_TEST_SHELL', '/bin/sh')
LIB = ROOT / 'ramboot/usb-log.sh'


class UsbLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='usb log ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'state'
        self.work.mkdir()
        self.sys = self.root / 'sys'
        (self.sys / 'class/udc/fe350000.crgudc').mkdir(parents=True)
        tty = self.sys / 'class/tty/ttyGS0'
        tty.mkdir(parents=True)
        (tty / 'dev').write_text('246:0\n')
        self.bb = self.root / 'safe operations'
        self.bb.write_text('''#!/usr/bin/env python3
import os,sys,subprocess,time,shutil
from pathlib import Path
root=Path(os.environ['TESTROOT']).resolve()
cmd,*args=sys.argv[1:]
for arg in args:
 if arg.startswith('/') and not Path(arg).resolve().is_relative_to(root):
  sys.exit('forbidden host path')
with (root/'calls').open('a') as f: f.write(cmd+' '+repr(args)+'\\n')
if cmd=='mkdir':
 r=subprocess.run(['mkdir',*args]);
 if r.returncode: sys.exit(r.returncode)
 p=Path(args[-1])
 if p.name=='jarvis2_ram_log':
  for n in ('idVendor','idProduct','bcdUSB','bcdDevice','bDeviceClass','UDC'): (p/n).touch()
  for n in ('functions','configs','strings'): (p/n).mkdir()
 if p.name=='0x409':
  for n in ('serialnumber','manufacturer','product'): (p/n).touch()
 if p.name=='c.1':
  for n in ('MaxPower','bmAttributes'): (p/n).touch()
 if p.name=='acm.usb0': (p/'port_num').write_text(os.environ.get('ACM_PORT','0'))
elif cmd=='mount':
 if os.environ.get('FAIL_MOUNT') or os.environ.get('FAIL_MOUNT_FS')==args[1]: sys.exit(1)
 if args[1]=='configfs':
  g=Path(args[-1])/'usb_gadget'; g.mkdir()
  if os.environ.get('EXISTING_GADGET'): (g/'owner_gadget').mkdir()
 elif args[1]=='debugfs':
  mode=Path(args[-1])/'usb/amlogic/crg-drd-otg/mode'; mode.parent.mkdir(parents=True)
  mode.write_text(os.environ.get('USB_ROLE','notg-host')+'\\n')
 else: sys.exit('forbidden mount type')
elif cmd=='umount':
 if os.environ.get('FAIL_UMOUNT'): sys.exit(1)
 shutil.rmtree(Path(args[0])/'usb')
elif cmd=='cat' and Path(args[0]).name=='mode':
 p=Path(args[0])
 if p.read_text()=='device\\n' and not os.environ.get('FAIL_ROLE_SWITCH'):
  p.write_text('notg-device\\n')
  if not os.environ.get('FAIL_UDC_REGISTER'):
   name='unexpected' if os.environ.get('WRONG_UDC') else 'fe350000.crgudc'
   if os.environ.get('UDC_DELAY_READS'): (root/'udc-delay').write_text('0')
   else: (root/'sys/class/udc'/name).mkdir()
 os.execvp('cat',['cat',*args])
elif cmd=='ls' and Path(args[-1])==root/'sys/class/udc':
 p=root/'udc-delay'
 if p.exists():
  n=int(p.read_text())+1; p.write_text(str(n))
  if n>=int(os.environ['UDC_DELAY_READS']):
   (root/'sys/class/udc/fe350000.crgudc').mkdir(); p.unlink()
 os.execvp('ls',['ls',*args])
elif cmd=='mknod': Path(args[0]).write_text('substituted node '+':'.join(args[1:]))
elif cmd=='sleep': time.sleep(.02)
elif cmd=='stty':
 if os.environ.get('FAIL_STTY'): sys.exit(1)
elif cmd=='cat' and Path(args[0]).name=='startup.log':
 p=root/'log-attempts'; n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n))
 if n==1 and os.environ.get('FIRST_LOG_FAIL'): sys.exit(1)
 os.execvp('cat',['cat',*args])
elif cmd in ('cat','ls','ln','rmdir'): os.execvp(cmd,[cmd,*args])
else: sys.exit('forbidden host operation '+cmd)
''')
        self.bb.chmod(0o755)
        (self.work / 'startup.log').write_text('RAM startup fixture\n')
        self.env = dict(os.environ, TESTROOT=str(self.root), GUARD_BB=str(self.bb),
                        GUARD_WORKDIR=str(self.work), GUARD_SYSROOT=str(self.sys),
                        USB_LOG_LIBRARY=str(LIB), USB_LOG_TTY=str(self.work / 'ttyGS0'))

    def run_library(self, script, **extra):
        self.assertTrue(LIB.is_file(), 'USB diagnostic library is missing')
        result = subprocess.run([SHELL, '-c', '. "$USB_LOG_LIBRARY"\n' + script],
                                env={**self.env, **extra}, capture_output=True,
                                text=True, timeout=8)
        self.assertNotIn('forbidden host', result.stderr)
        return result

    def test_host_execution_is_refused_before_busybox(self):
        entry = ROOT / 'ramboot/usb-log-init'
        self.assertTrue(entry.is_file(), 'Diagnostic PID 1 entrypoint is missing')
        result = subprocess.run([SHELL, str(entry)], capture_output=True, text=True, timeout=3)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires PID 1', result.stderr)

    def test_creates_only_acm_and_binds_expected_controller(self):
        result = self.run_library('usb_log_setup')
        self.assertEqual(result.returncode, 0, result.stderr)
        g = self.work / 'config/usb_gadget/jarvis2_ram_log'
        self.assertEqual((g / 'UDC').read_text().strip(), 'fe350000.crgudc')
        self.assertEqual([p.name for p in (g / 'functions').iterdir()], ['acm.usb0'])
        self.assertEqual((g / 'configs/c.1/acm.usb0').resolve(), g / 'functions/acm.usb0')
        self.assertEqual((g / 'strings/0x409/serialnumber').read_text().strip(), 'RAM-DIAGNOSTIC')
        self.assertEqual((self.work / 'ttyGS0').read_text(), 'substituted node c:246:0')
        self.assertTrue((self.work / 'null').is_file(), 'Private null node is missing')
        self.assertEqual((self.work / 'null').read_text(), 'substituted node c:1:3')

    def test_preexisting_gadget_is_preserved_and_never_bound(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        result = self.run_library('usb_log_setup', EXISTING_GADGET='1')
        self.assertNotEqual(result.returncode, 0)
        g = self.work / 'config/usb_gadget'
        self.assertTrue((g / 'owner_gadget').is_dir())
        self.assertFalse((g / 'jarvis2_ram_log').exists())
        self.assertNotIn('debugfs', (self.root / 'calls').read_text())

    def test_acm_must_own_the_selected_tty(self):
        result = self.run_library('usb_log_setup', ACM_PORT='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / 'ttyGS0').exists())
        self.assertEqual((self.work / 'config/usb_gadget/jarvis2_ram_log/UDC').read_text(), '')

    def test_unexpected_or_additional_controller_is_rejected(self):
        controller = self.sys / 'class/udc/fe350000.crgudc'
        controller.rmdir()
        (controller.parent / 'another-controller').mkdir()
        result = self.run_library('usb_log_setup')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / 'config/usb_gadget/jarvis2_ram_log').exists())
        controller.mkdir()
        result = self.run_library('usb_log_require_udc')
        self.assertNotEqual(result.returncode, 0)

    def test_missing_udc_switches_known_host_role_and_cleans_private_debugfs(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        result = self.run_library('usb_log_setup')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.work / 'config/usb_gadget/jarvis2_ram_log/UDC').read_text().strip(),
                         'fe350000.crgudc')
        self.assertFalse((self.work / 'usb-debug').exists())
        self.assertIn('debugfs', (self.root / 'calls').read_text())

    def test_role_switch_failure_and_unknown_role_stop_and_clean_debugfs(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        for extra in ({'USB_ROLE': 'otg-host'}, {'FAIL_ROLE_SWITCH': '1'},
                      {'FAIL_MOUNT_FS': 'debugfs'}):
            with self.subTest(extra=extra):
                result = self.run_library('usb_log_require_udc', **extra)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.work / 'usb-debug').exists())
                self.assertFalse((self.work / 'config/usb_gadget/jarvis2_ram_log').exists())

    def test_preexisting_debug_path_is_preserved_and_not_mounted(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        debug = self.work / 'usb-debug'
        debug.mkdir()
        (debug / 'owner-file').write_text('keep')
        result = self.run_library('usb_log_require_udc')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((debug / 'owner-file').read_text(), 'keep')
        calls = self.root / 'calls'
        self.assertNotIn('mount', calls.read_text() if calls.exists() else '')

    def test_missing_udc_registration_is_bounded_and_unexpected_udc_stops(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        result = self.run_library('usb_log_require_udc', FAIL_UDC_REGISTER='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / 'usb-debug').exists())
        self.assertEqual((self.root / 'calls').read_text().count('sleep '), 4)
        result = self.run_library('usb_log_require_udc', WRONG_UDC='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / 'usb-debug').exists())

    def test_delayed_udc_registration_succeeds_after_bounded_wait(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        result = self.run_library('usb_log_setup', UDC_DELAY_READS='3')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.work / 'usb-debug').exists())
        self.assertEqual((self.root / 'calls').read_text().count('sleep '), 2)
        self.assertEqual((self.work / 'config/usb_gadget/jarvis2_ram_log/UDC').read_text().strip(),
                         'fe350000.crgudc')

    def test_debugfs_cleanup_failure_prevents_gadget_creation(self):
        (self.sys / 'class/udc/fe350000.crgudc').rmdir()
        result = self.run_library('usb_log_setup', FAIL_UMOUNT='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.work / 'usb-debug').exists())
        self.assertFalse((self.work / 'config/usb_gadget/jarvis2_ram_log').exists())

    def test_mount_failure_and_preexisting_mount_path_stop(self):
        result = self.run_library('usb_log_setup', FAIL_MOUNT='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.work / 'config/usb_gadget').exists())
        result = self.run_library('usb_log_setup')
        self.assertNotEqual(result.returncode, 0)

    def test_bad_tty_device_number_prevents_node_and_binding(self):
        dev = self.sys / 'class/tty/ttyGS0/dev'
        for bad in ('246', '246:0:1', '246:', ':0', '246:1;reboot', '999999999999:0', '0246:0'):
            with self.subTest(dev=bad):
                dev.write_text(bad)
                # Each attempt needs a fresh private configfs view.
                work = self.root / ('bad-' + str(len(list(self.root.glob('bad-*')))))
                work.mkdir()
                result = self.run_library('usb_log_setup', GUARD_WORKDIR=str(work))
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((work / 'ttyGS0').exists())
                self.assertEqual((work / 'config/usb_gadget/jarvis2_ram_log/UDC').read_text(), '')

    def test_writer_does_not_block_parent_without_a_host_reader(self):
        self.assertTrue(LIB.is_file(), 'USB diagnostic library is missing')
        tty = self.work / 'ttyGS0'
        os.mkfifo(tty)
        (self.work / 'null').touch()
        process = subprocess.Popen([SHELL, '-c', '. "$USB_LOG_LIBRARY"\n'
                                    'usb_log_start_writer\nprintf "parent continued\\n"\n'
                                    'wait "$USB_LOG_WRITER"'],
                                   env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        try:
            ready, _, _ = select.select([process.stdout], [], [], 3)
            self.assertTrue(ready, 'Parent blocked waiting for a USB host')
            self.assertEqual(process.stdout.readline(), 'parent continued\n')
        finally:
            os.killpg(process.pid, signal.SIGTERM)
            _, errors = process.communicate(timeout=3)
            self.assertNotIn('forbidden host', errors)

    def test_writer_streams_log_and_retries_a_closed_connection(self):
        self.assertTrue(LIB.is_file(), 'USB diagnostic library is missing')
        target = self.work / 'ttyGS0'
        target.touch()
        (self.work / 'null').touch()
        process = subprocess.Popen([SHELL, '-c', '. "$USB_LOG_LIBRARY"\n'
                                    'usb_log_start_writer\nwait "$USB_LOG_WRITER"'],
                                   env={**self.env, 'FIRST_LOG_FAIL': '1'},
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=True)
        try:
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                if target.read_text() == 'RAM startup fixture\n':
                    break
                time.sleep(.02)
            self.assertEqual(target.read_text(), 'RAM startup fixture\n')
            self.assertGreaterEqual(int((self.root / 'log-attempts').read_text()), 2)
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline and int((self.root / 'log-attempts').read_text()) < 3:
                time.sleep(.02)
            self.assertGreaterEqual(int((self.root / 'log-attempts').read_text()), 3,
                                    'Idle log never reopened for a later host connection')
            calls = (self.root / 'calls').read_text().splitlines()
            stty = next(i for i, line in enumerate(calls) if line.startswith('stty '))
            sent = next(i for i, line in enumerate(calls) if line.startswith('cat ') and 'startup.log' in line)
            self.assertLess(stty, sent)
        finally:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=3)
