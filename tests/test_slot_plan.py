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
  layout={'sector_size':512,'metadata_max_size':65536,'metadata_slot_count':3,
          'block_devices':[{'name':'super','size':2097152,'block_size':4096,'alignment':512,'alignment_offset':0,'first_logical_sector':2048}],
          'partitions':{name:[{'logical_sector':0,'num_sectors':8,'target_type':'linear','target_source':0,'target_name':'super','target_data':2048+8*i}] for i,name in enumerate(sizes) if not name.startswith('vbmeta')}}
  view={'canonical':'identical metadata views','sizes':sizes,'layout':layout}
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
  for v in views:
   v['sizes']['vendor_b']=0;v['layout']['partitions']['vendor_b']=[]
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
 def test_lcars_fit_checks_restore_hashes_and_untouched_stock_references(self):
  spec = importlib.util.spec_from_file_location('lcars_fit', ROOT/'tools/prepare-lcars-install.py')
  preflight = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(preflight)
  manifest, views = self.fixtures()
  candidate = {f'images/{name}': record for name, record in manifest['files'].items()}
  for partition in ('init_boot', 'vendor_boot'):
   candidate[f'transition-images/{partition}.img'] = {'sha256': 'c'*64, 'bytes': 4096}
  old = {Path(name).name: dict(record, sha256='b'*64) for name, record in candidate.items()}
  physical = {name[:-4]+'_a': record for name, record in old.items()
              if name.startswith(('vbmeta', 'init_boot', 'vendor_boot'))}
  physical['boot_a'] = {'bytes': 4096, 'sha256': 'd'*64}
  logical = {part+'_a': 'b'*64 for part in ('system', 'system_ext', 'product')}
  logical['vendor_a'] = 'e'*64
  capture = {'physical': physical, 'logical_sha256': logical, 'old_files': old,
             'super': {'bytes': 2097152}, 'metadata_prefix': {'bytes': 524288}}
  profile = {'references': {'boot': {'bytes': 4096, 'sha256': 'd'*64},
                            'vendor': {'bytes': 4096, 'sha256': 'e'*64},
                            'vendor_boot': {'bytes': 4096, 'sha256': 'f'*64}}}
  report = preflight.review_fit('a', candidate, capture, views, profile)
  self.assertEqual(report['restore_images_verified'], 7)
  self.assertEqual(report['untargeted_stock_references_verified'], ['boot', 'vendor'])
  self.assertFalse(report['installation_authorized'])
  logical['vendor_a'] = 'f'*64
  with self.assertRaisesRegex(ValueError, 'vendor_a.*stock foundation'):
   preflight.review_fit('a', candidate, capture, views, profile)
  logical['vendor_a'] = 'e'*64
  logical['product_a'] = 'f'*64
  with self.assertRaisesRegex(ValueError, 'product_a.*restore image'):
   preflight.review_fit('a', candidate, capture, views, profile)
  logical['product_a'] = 'b'*64
  capture['metadata_prefix']['bytes'] = 1052672
  with self.assertRaisesRegex(ValueError, 'captured metadata prefix'):
   preflight.review_fit('a', candidate, capture, views, profile)
 def test_active_b_layout_with_empty_a_is_supported_without_claiming_backup(self):
  manifest,views=self.fixtures()
  for v in views:
   for name in list(v['sizes']):
    if name.endswith('_a') and not name.startswith('vbmeta'):
     v['sizes'][name]=0;v['layout']['partitions'][name]=[]
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
 def native_views(self,size,transform=None):
  import json
  from unittest.mock import patch
  physical={part+'_'+slot:8192 for part in ['vbmeta','vbmeta_system'] for slot in 'ab'}
  outputs=[]
  for slot in [0,1]:
   data={'partitions':[{'name':'system_a','size':size,'group_name':'default'}],
         'block_devices':[{'name':'super','size':'2097152','block_size':'4096','alignment':'512'}]}
   allocated=size in ['4096',4096]
   extent='    0 .. 7 linear super 2048\n' if allocated else ''
   text=f'Slot {slot}:\nMetadata max size: 65536 bytes\nMetadata slot count: 3\nPartition table:\n------------------------\n  Name: system_a\n  Group: default\n  Attributes: readonly\n  Extents:\n{extent}------------------------\nSuper partition layout:\n------------------------\nBlock device table:\n------------------------\n  Partition name: super\n  First sector: 2048\n  Size: 2097152 bytes\n  Flags: none\n------------------------\nGroup table:\n'
   if transform is not None:data,text=transform(data,text)
   outputs.extend([json.dumps(data),text])
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

 def test_layout_is_required_not_inferred_from_positive_sizes(self):
  manifest,views=self.fixtures()
  for view in views:del view['layout']
  with self.assertRaisesRegex(ValueError,'layout'):module.plan('a',manifest,views)
 def test_extent_end_cannot_cross_capacity(self):
  manifest,views=self.fixtures()
  for view in views:view['layout']['partitions']['system_a'][0]['target_data']=4096
  with self.assertRaisesRegex(ValueError,'bounds'):module.plan('a',manifest,views)
 def test_extent_crossing_end_rejected_even_when_start_is_inside_device(self):
  manifest,views=self.fixtures()
  for view in views:
   view['layout']['partitions']['system_a'][0].update(target_data=4088,num_sectors=16)
   view['sizes']['system_a']=8192
  manifest['files']['system.img']['bytes']=8192
  with self.assertRaisesRegex(ValueError,'bounds'):module.plan('a',manifest,views)
 def test_target_cannot_overlap_other_slot_or_protected_foundation(self):
  for protected in ['system_b','vendor_a']:
   manifest,views=self.fixtures()
   for view in views:
    view['layout']['partitions']['system_a'][0]['target_data']=view['layout']['partitions'][protected][0]['target_data']
   with self.subTest(protected=protected),self.assertRaisesRegex(ValueError,'overlap'):module.plan('a',manifest,views)
 def test_target_cannot_enter_reserved_metadata_prefix(self):
  manifest,views=self.fixtures()
  for view in views:view['layout']['partitions']['system_a'][0]['target_data']=2040
  with self.assertRaisesRegex(ValueError,'bounds'):module.plan('a',manifest,views)
 def test_unsupported_types_and_source_indexes_are_rejected(self):
  for key,value in [('target_type','zero'),('target_type','striped'),('target_source',1),('target_source',True),('target_name','vendor'),('num_sectors',True),('num_sectors',0),('logical_sector',8)]:
   manifest,views=self.fixtures()
   for view in views:view['layout']['partitions']['system_a'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):module.plan('a',manifest,views)
 def test_single_super_identity_and_sector_geometry_are_required(self):
  for key,value in [('name','vendor'),('size',2097153),('block_size',513),('block_size',True),('first_logical_sector',0),('alignment_offset',512)]:
   manifest,views=self.fixtures()
   for view in views:view['layout']['block_devices'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):module.plan('a',manifest,views)
 def test_logical_block_alignment_and_extent_byte_totals_are_checked(self):
  for key,value in [('target_data',2049),('num_sectors',7)]:
   manifest,views=self.fixtures()
   for view in views:view['layout']['partitions']['system_a'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):module.plan('a',manifest,views)
 def test_multibacking_and_unexplained_layout_changes_are_rejected(self):
  manifest,views=self.fixtures()
  for view in views:view['layout']['block_devices'].append(copy.deepcopy(view['layout']['block_devices'][0]))
  with self.assertRaises(ValueError):module.plan('a',manifest,views)
  manifest,views=self.fixtures();views[1]['layout']['partitions']['system_a'][0]['target_data']=3000
  with self.assertRaises(ValueError):module.plan('a',manifest,views)
 def test_fragmented_adjacent_extents_and_1000_sector_odm_are_valid(self):
  manifest,views=self.fixtures()
  for view in views:
   view['layout']['partitions']['system_a']=[dict(view['layout']['partitions']['system_a'][0],num_sectors=8),dict(view['layout']['partitions']['system_a'][0],logical_sector=8,num_sectors=8,target_data=3000)]
   view['sizes']['system_a']=8192
   view['layout']['partitions']['odm_a'][0].update(num_sectors=1000,target_data=3072)
   view['sizes']['odm_a']=512000
  manifest['files']['system.img']['bytes']=8192
  self.assertEqual('a',module.plan('a',manifest,views)['target_slot'])

 def test_native_json_text_backing_identity_and_sizes_must_match(self):
  def wrong_device(data,text):
   data['block_devices'][0]['name']='vendor'
   return data,text
  transforms=[wrong_device,
              lambda data,text:(data,text.replace('Size: 2097152 bytes','Size: 2097664 bytes')),
              lambda data,text:(data,text.replace('linear super 2048','linear vendor 2048')),
              lambda data,text:(data,text.replace('0 .. 7 linear super 2048','0 .. 7 zero')),
              lambda data,text:(data,text.replace('0 .. 7 linear super 2048','0 .. 15 linear super 2048')),
              lambda data,text:(data,text.replace('0 .. 7 linear super 2048','0 .. 7 linear super 4096'))]
  for index,transform in enumerate(transforms):
   with self.subTest(case=index),self.assertRaises(ValueError):self.native_views('4096',transform)
 def test_native_parser_keeps_other_slot_protected_extents_in_overlap_checks(self):
  def overlap(data,text):
   data['partitions'].append({'name':'vendor_b','size':'4096','group_name':'default'})
   record='  Name: vendor_b\n  Group: default\n  Attributes: readonly\n  Extents:\n    0 .. 7 linear super 2048\n------------------------\n'
   return data,text.replace('Super partition layout:',record+'Super partition layout:')
  with self.assertRaisesRegex(ValueError,'overlap'):self.native_views('4096',overlap)
 def test_explicit_extent_sector_size_cannot_be_confused_with_block_size(self):
  manifest,views=self.fixtures()
  for view in views:view['layout']['sector_size']=4096
  with self.assertRaisesRegex(ValueError,'512'):module.plan('a',manifest,views)
