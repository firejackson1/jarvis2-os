import hashlib,importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('image_contents',ROOT/'tools/inspect-image-contents.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ImageContentsTests(unittest.TestCase):
 def fixture(self,root):
  required=[
   ('system','system/apex/com.android.btservices.apex'),
   ('system_ext','priv-app/Jarvis2RemoteSettings/Jarvis2RemoteSettings.apk'),
   ('system_ext','app/Jarvis2TvControlsOverlay/Jarvis2TvControlsOverlay.apk'),
   ('system_ext','priv-app/TvSettingsTwoPanel/TvSettingsTwoPanel.apk'),
   ('product','app/Jarvis2LtvLauncher/Jarvis2LtvLauncher.apk')]
  for part,path in required:
   p=root/part/path;p.parent.mkdir(parents=True);p.write_bytes(b'fixture apk')
  allowlist=root/'system_ext/etc/permissions/privapp-permissions-jarvis2-remote.xml'
  allowlist.parent.mkdir(parents=True)
  allowlist.write_text('<permissions><privapp-permissions package="app.jarvis2.remote"><permission name="android.permission.BLUETOOTH_PRIVILEGED"/><permission name="android.permission.MODIFY_AUDIO_ROUTING"/><permission name="android.permission.MEDIA_CONTENT_CONTROL"/></privapp-permissions></permissions>')
  return required
 def test_extensionless_allowlist_is_not_a_loadable_permission_file(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   xml=root/'system_ext/etc/permissions/privapp-permissions-jarvis2-remote.xml'
   xml.rename(xml.with_name('jarvis2_remote_privapp_permissions'))
   errors=module.inspect_trees(root,{'launcher_sha256':hashlib.sha256(b'fixture apk').hexdigest()})
   self.assertTrue(any('remote privilege allowlist' in e for e in errors))
 def test_allowlist_must_grant_remote_routing_permission(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   xml=root/'system_ext/etc/permissions/privapp-permissions-jarvis2-remote.xml'
   xml.write_text('<permissions><privapp-permissions package="another.app"><permission name="android.permission.MODIFY_AUDIO_ROUTING"/></privapp-permissions></permissions>')
   errors=module.inspect_trees(root,{'launcher_sha256':hashlib.sha256(b'fixture apk').hexdigest()})
   self.assertTrue(any('remote privilege allowlist' in e for e in errors))
 def test_missing_required_apps_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   errors=module.inspect_trees(Path(d),{'launcher_sha256':hashlib.sha256(b'fixture apk').hexdigest()})
   self.assertTrue(any('Missing required package' in e for e in errors))
 def test_actual_tree_debug_trust_and_phone_packages_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   key=root/'system/system/etc/security/adb_keys';key.parent.mkdir(parents=True);key.write_text('public trust fixture')
   phone=root/'system_ext/priv-app/Settings/Settings.apk';phone.parent.mkdir(parents=True);phone.write_bytes(b'fixture')
   errors=module.inspect_trees(root,{'launcher_sha256':hashlib.sha256(b'fixture apk').hexdigest()})
   self.assertTrue(any('debug trust' in e for e in errors));self.assertTrue(any('handset' in e for e in errors))
 def test_launcher_payload_must_match_verified_upstream(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   errors=module.inspect_trees(root,{'launcher_sha256':'0'*64})
   self.assertTrue(any('launcher checksum' in e for e in errors))
 def test_complete_fixture_passes_only_scoped_content_checks(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   self.assertEqual([],module.inspect_trees(root,{'launcher_sha256':hashlib.sha256(b'fixture apk').hexdigest()}))

 def test_official_updater_is_forbidden_in_release_image(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   path=root/'system_ext/priv-app/Updater/Updater.apk'
   path.parent.mkdir(parents=True);path.write_bytes(b'updater fixture')
   errors=module.inspect_trees(root,{'launcher_sha256':hashlib.sha256(b'fixture apk').hexdigest()})
   self.assertTrue(any('official OTA client' in error for error in errors))
