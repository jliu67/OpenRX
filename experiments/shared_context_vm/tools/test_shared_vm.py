"""Portable source/entry-point checks; native RTL runs require admitted assets."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
class Delivery(unittest.TestCase):
 def test_accepted_source_closure(self):
  meta=json.loads((ROOT/'fixtures/provenance.json').read_text())
  for name,want in meta['experimental_files'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),want,name)
  for row in meta['golden_files']:self.assertEqual(hashlib.sha256((REPO/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])
  self.assertEqual(hashlib.sha256((ROOT/'tools/kernel_guards.py').read_bytes()).hexdigest(),meta['guard_sha256'])
 def test_all_three_closed_case_interfaces(self):
  for suite,count in [('contexts16',5),('fetch18',10),('iterations20',6)]:
   p=subprocess.run([sys.executable,str(ROOT/'tools/run_shared_vm.py'),'--suite',suite,'--list-cases'],capture_output=True,text=True,timeout=5)
   self.assertEqual(p.returncode,0,p.stderr);rows=json.loads(p.stdout);self.assertEqual(len(rows),count);self.assertEqual(len({tuple(r)for r in rows}),count)
 def test_execution_requires_explicit_host_context(self):
  p=subprocess.run([sys.executable,str(ROOT/'tools/run_shared_vm.py'),'--suite','fetch18','build'],capture_output=True,text=True,timeout=5)
  self.assertEqual(p.returncode,2);self.assertIn('approved exclusion identity',p.stderr)
 def test_missing_native_inputs_cannot_create_accepted_fixture(self):
  with tempfile.TemporaryDirectory()as tmp:
   tmp=Path(tmp);native=tmp/'native';native.mkdir()
   p=subprocess.run([sys.executable,str(ROOT/'tools/prepare_kernel.py'),'--native-dir',str(native),'--output',str(tmp/'out')],capture_output=True,timeout=5)
   self.assertNotEqual(p.returncode,0);self.assertFalse((tmp/'out/fixture.vh').exists())
if __name__=='__main__':unittest.main()
