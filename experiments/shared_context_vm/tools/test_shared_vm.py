"""Portable source/entry-point checks; native RTL runs require admitted assets."""
import hashlib,json,os,pwd,subprocess,sys,tempfile,unittest
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
 def test_configured_uncapped_failure_exits_cleanly_before_commands(self):
  with tempfile.TemporaryDirectory()as tmp:
   tmp=Path(tmp);assets=tmp/'assets';assets.mkdir();lock=tmp/'test-only-lock';lock.touch();s=lock.stat()
   env={'HOME':pwd.getpwuid(os.getuid()).pw_dir,'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid())}
   argv=[sys.executable,str(ROOT/'tools/run_shared_vm.py'),'--suite','iterations20','--fixtures',str(assets),'--native-dir',str(assets),'--verilator-root',str(assets),'--output',str(tmp/'output'),'--lock',str(lock),'--lock-identity',str(os.major(s.st_dev)),str(os.minor(s.st_dev)),str(s.st_ino),'--unit','codex-openrx-test-no-scope.scope','build']
   p=subprocess.run(argv,capture_output=True,text=True,env=env,timeout=5)
   self.assertEqual(p.returncode,1);self.assertEqual(p.stderr,'');self.assertEqual(json.loads(p.stdout)['status'],'FAILED_FIRST_FAILURE_NO_RETRY');self.assertIsNone(json.loads(p.stdout)['result'])
   self.assertFalse((tmp/'output/actual-build').exists())
if __name__=='__main__':unittest.main()
