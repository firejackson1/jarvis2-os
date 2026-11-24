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
