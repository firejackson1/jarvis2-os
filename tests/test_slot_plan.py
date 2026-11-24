import copy,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('slot_plan',ROOT/'tools/slot-install-plan.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class SlotPlanTests(unittest.TestCase):
 def fixtures(self):
  parts=['system','system_ext','product','vendor','odm','system_dlkm','vendor_dlkm','odm_dlkm']
  sizes={p+'_'+slot:4096 for p in parts for slot in 'ab'}
  sizes.update({p+'_'+slot:8192 for p in ['vbmeta','vbmeta_system'] for slot in 'ab'})
  view={'canonical':'identical metadata views','sizes':sizes}
  manifest={'avb_offline_verified':True,'files':{p+'.img':{'bytes':4096 if p in ['system','system_ext','product'] else 8192,'sha256':'0'*64} for p in ['system','system_ext','product','vbmeta_system','vbmeta']}}
  return manifest,[view,copy.deepcopy(view)]
 def test_either_explicit_slot_targets_only_that_slot(self):
  for slot in 'ab':
   with self.subTest(slot=slot):
    manifest,views=self.fixtures();plan=module.plan(slot,manifest,views)
    self.assertEqual(5,len(plan['writes']));self.assertTrue(all(x['partition'].endswith('_'+slot) for x in plan['writes']))
    self.assertFalse(plan['switch_slot']);self.assertFalse(plan['wipe_data']);self.assertFalse(plan['executed'])
 def test_differing_metadata_views_are_not_silently_overwritten(self):
  manifest,views=self.fixtures();views[1]['canonical']='different other-slot view'
  with self.assertRaisesRegex(ValueError,'metadata views'):module.plan('a',manifest,views)
 def test_unallocated_other_slot_needs_full_provisioning(self):
  manifest,views=self.fixtures()
  for v in views:v['sizes']['vendor_b']=0
  with self.assertRaisesRegex(ValueError,'foundation'):module.plan('b',manifest,views)
 def test_size_mismatch_never_requests_automatic_resize(self):
  manifest,views=self.fixtures()
  for v in views:v['sizes']['system_a']=8192
  with self.assertRaisesRegex(ValueError,'size'):module.plan('a',manifest,views)
 def test_unsigned_build_archive_is_rejected(self):
  manifest,views=self.fixtures();manifest['avb_offline_verified']=False
  with self.assertRaisesRegex(ValueError,'AVB'):module.plan('a',manifest,views)
 def test_implicit_or_all_slots_rejected(self):
  manifest,views=self.fixtures()
  for slot in ['all','current','',None]:
   with self.subTest(slot=slot),self.assertRaises(ValueError):module.plan(slot,manifest,views)
 def test_active_b_layout_with_empty_a_is_supported_without_claiming_backup(self):
  manifest,views=self.fixtures()
  for v in views:
   for name in list(v['sizes']):
    if name.endswith('_a') and not name.startswith('vbmeta'):v['sizes'][name]=0
  result=module.plan('b',manifest,views)
  self.assertTrue(all(x['partition'].endswith('_b') for x in result['writes']))
  self.assertFalse(result['other_slot_foundation_allocated'])
 def test_avb_requires_literal_true(self):
  for value in ['true',1,{},None]:
   manifest,views=self.fixtures();manifest['avb_offline_verified']=value
   with self.subTest(value=value),self.assertRaises(ValueError):module.plan('a',manifest,views)
 def test_manifest_rejects_invalid_sizes_and_digests(self):
  for field,value in [('bytes',True),('bytes','4096'),('bytes',4096.0),('sha256','z'*64),('sha256','0'*63),('sha256',None)]:
   manifest,views=self.fixtures();manifest['files']['system.img'][field]=value
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):module.plan('a',manifest,views)
 def test_partition_sizes_reject_bool_and_float(self):
  for value in [True,4096.0,'4096']:
   manifest,views=self.fixtures()
   for view in views:view['sizes']['system_a']=value
   with self.subTest(value=value),self.assertRaises(ValueError):module.plan('a',manifest,views)
 def image_fixture(self,folder):
  import hashlib
  manifest,views=self.fixtures()
  for name,info in manifest['files'].items():
   payload=b'r'*info['bytes'];(folder/name).write_bytes(payload)
   info['sha256']=hashlib.sha256(payload).hexdigest()
  return manifest,views
 def test_raw_image_validation_accepts_exact_files(self):
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp);manifest,views=self.image_fixture(folder)
   module.validate_images(folder,module.plan('a',manifest,views))
 def test_raw_image_validation_rejects_wrong_lengths_even_with_matching_hash(self):
  import hashlib,tempfile
  for length in [4095,4097]:
   with self.subTest(length=length),tempfile.TemporaryDirectory() as temp:
    folder=Path(temp);manifest,views=self.image_fixture(folder)
    payload=b'r'*length;(folder/'system.img').write_bytes(payload)
    manifest['files']['system.img']['sha256']=hashlib.sha256(payload).hexdigest()
    with self.assertRaisesRegex(ValueError,'size'):module.validate_images(folder,module.plan('a',manifest,views))
 def test_raw_image_validation_rejects_sparse_files(self):
  import hashlib,tempfile
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp);manifest,views=self.image_fixture(folder)
   payload=b'\x3a\xff\x26\xed'+b'r'*4092;(folder/'system.img').write_bytes(payload)
   manifest['files']['system.img']['sha256']=hashlib.sha256(payload).hexdigest()
   with self.assertRaisesRegex(ValueError,'[Ss]parse'):module.validate_images(folder,module.plan('a',manifest,views))
 def test_raw_image_validation_rejects_nonregular_file(self):
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp);manifest,views=self.image_fixture(folder)
   (folder/'system.img').unlink();(folder/'system.img').mkdir()
   with self.assertRaisesRegex(ValueError,'regular'):module.validate_images(folder,module.plan('a',manifest,views))
 def test_physical_sizes_reject_bool_before_lpdump(self):
  physical={part+'_'+slot:8192 for part in ['vbmeta','vbmeta_system'] for slot in 'ab'}
  physical['vbmeta_a']=True
  with self.assertRaisesRegex(ValueError,'sizes'):module.load_views('/not/run','/not/read',physical)
 def test_raw_image_validation_rejects_checksum_mismatch(self):
  import tempfile
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp);manifest,views=self.image_fixture(folder)
   (folder/'system.img').write_bytes(b'x'*4096)
   with self.assertRaisesRegex(ValueError,'checksum'):module.validate_images(folder,module.plan('a',manifest,views))
 def native_views(self,size):
  import json
  from unittest.mock import patch
  physical={part+'_'+slot:8192 for part in ['vbmeta','vbmeta_system'] for slot in 'ab'}
  outputs=[]
  for slot in [0,1]:
   outputs.extend([json.dumps({'partitions':[{'name':'system_a','size':size}]}),f'Slot {slot}:\nidentical layout\n'])
  with patch.object(module.subprocess,'check_output',side_effect=outputs):
   return module.load_views('/native/lpdump','/captured/metadata',physical)
 def test_native_json_uint64_decimal_strings_are_normalized(self):
  for value in ['4096','0',4096,0]:
   with self.subTest(value=value):
    views=self.native_views(value)
    self.assertEqual(int(value),views[0]['sizes']['system_a'])
    self.assertIs(type(views[0]['sizes']['system_a']),int)
    self.assertEqual(views[0]['canonical'],views[1]['canonical'])
 def test_native_json_rejects_noncanonical_sizes(self):
  for value in [True,False,4096.0,-1,'-1','+1',' 1','1 ','1.0','1e3','','01','00','1x',None]:
   with self.subTest(value=value),self.assertRaises(ValueError):self.native_views(value)
