# SPDX-License-Identifier: Apache-2.0
import copy,hashlib,importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('candidate_packaging',ROOT/'tools/package-candidate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
REV='a'*40

class CandidatePackagingTests(unittest.TestCase):
 def fixture(self,root):
  images=root/'images';meta=root/'metadata';images.mkdir();meta.mkdir();files={}
  for name in m.IMAGE_NAMES:
   path=images/name;path.write_bytes(('fixture '+name).encode());files[name]={'bytes':path.stat().st_size,'sha256':m.digest(path)}
  for name in m.METADATA_NAMES:
   path=meta/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(m.candidate_readme(REV) if name=='README.txt' else 'fixture metadata\n')
  proof=root/'proof.json';proof.write_text(json.dumps({'passed':True,'files':files}));return images,meta,proof
 def test_repeated_archive_bytes_and_member_metadata_match(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root);outputs=[]
   for name in ['one','two']:
    result=m.package(images,meta,proof,m.digest(proof),REV,root/name);self.assertTrue(result['all_members_read_back']);outputs.append(root/name/result['archive'])
   self.assertEqual(m.digest(outputs[0]),m.digest(outputs[1]))
   with zipfile.ZipFile(outputs[0]) as z:
    self.assertEqual(sorted(z.namelist()),z.namelist());self.assertEqual(20,len(z.namelist()));manifest=json.loads(z.read('manifest.json'));self.assertFalse(manifest['google_payload_included']);self.assertFalse(manifest['hardware_tested'])
    for i in z.infolist():self.assertEqual((2026,11,24,0,0,0),i.date_time);self.assertEqual(0o100644,i.external_attr>>16)
 def test_real_cli_accepts_reviewed_fixture_and_records_receipt(self):
  import subprocess,sys
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root)
   result=subprocess.run([sys.executable,str(ROOT/'tools/package-candidate.py'),'--images',str(images),'--metadata',str(meta),'--proof',str(proof),'--proof-sha256',m.digest(proof),'--source-revision',REV,'--output',str(root/'out')],check=True,capture_output=True,text=True)
   receipt=json.loads(result.stdout);self.assertTrue(receipt['passed']);self.assertFalse(receipt['public_release_ready']);self.assertEqual(receipt,json.loads((root/'out/verification.json').read_text()))
 def test_stale_proof_changed_image_rejected_before_output(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root);(images/'system.img').write_bytes(b'tampered');out=root/'out'
   with self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,out)
   self.assertFalse(out.exists())
 def test_proof_pin_false_like_bool_size_digest_and_identity_fail(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root);original=json.loads(proof.read_text())
   with self.assertRaises(ValueError):m.package(images,meta,proof,'0'*64,REV,root/'out')
   for mutate in [lambda d:d.update(passed='true'),lambda d:d.update(google_payload_included=0),lambda d:d.update(google_payload_included=True),lambda d:d['files']['system.img'].update(bytes=True),lambda d:d['files']['system.img'].update(sha256='z'*64),lambda d:d['files'].update({'../outside':{'bytes':1,'sha256':'a'*64}})]:
    d=copy.deepcopy(original);mutate(d);proof.write_text(json.dumps(d))
    with self.subTest(proof=d),self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,root/'out')
 def test_unknown_missing_and_symlink_sources_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root)
   for folder in [images,meta]:
    extra=folder/'unexpected';extra.write_text('unexpected')
    with self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,root/'out')
    extra.unlink()
   p=meta/'LICENSE';p.unlink();p.symlink_to(proof)
   with self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,root/'out')
   p.unlink()
   with self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,root/'out')
 def test_existing_output_and_output_inside_inputs_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root);out=root/'existing';out.mkdir()
   for target in [out,images/'output',meta/'output']:
    with self.subTest(output=target),self.assertRaises((ValueError,FileExistsError)):m.package(images,meta,proof,m.digest(proof),REV,target)
 def test_duplicate_json_and_wrong_readme_revision_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);images,meta,proof=self.fixture(root);data=proof.read_text();proof.write_text('{"passed":false,'+data[1:])
   with self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,root/'out')
   proof.write_text(data);(meta/'README.txt').write_text(m.candidate_readme('b'*40))
   with self.assertRaises(ValueError):m.package(images,meta,proof,m.digest(proof),REV,root/'out')

if __name__=='__main__':unittest.main()
