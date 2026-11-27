"""Portable source/entry-point checks; native RTL runs require admitted assets."""
import ast,hashlib,json,os,pwd,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
class Delivery(unittest.TestCase):
 def binding_context(self,tmp,suite='fetch18'):
  # Load only the real binding/case functions, never the CLI or host setup.
  tree=ast.parse((ROOT/'tools/run_shared_vm.py').read_text())
  functions={'require','pin','stack_flags','compile_sources','compilation_binding','check_build_binding','case'}
  constants={'COMPILE_OPTIONS','INCLUDE_DIRS'}
  nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in functions or isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in constants for t in n.targets)]
  meta=json.loads((ROOT/'fixtures/provenance.json').read_text())
  code=tmp/'code';fixtures=tmp/'fixtures';vr=tmp/'verilator';run=tmp/'run'
  for name in meta['experimental_files']:
   target=code/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
  fixtures.mkdir();(fixtures/'fixture.vh').write_text('unit fixture header\n')
  # Small benign providers exercise identity changes without native execution.
  meta['verilator_programs']={'bin/verilator':'unit','bin/verilator_bin':'unit'}
  meta['verilator_runtime_files']={'include/verilated.h':'unit'}
  for name in {**meta['verilator_programs'],**meta['verilator_runtime_files']}:
   target=vr/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('unit provider '+name)
  build=run/'actual-build';build.mkdir(parents=True);compat=build/'HardFloat-divSqrt-compile-view.v';compat.write_text('unit compile view\n')
  model=build/'model';model.write_bytes(b'unit fixture; must never execute')
  ns={'Path':Path,'hashlib':hashlib,'json':json,'struct':__import__('struct'),'CODE':code,'SRC':REPO,'F':fixtures,'VR':vr,'M':meta,'R':run,'suite':suite,'command':mock.Mock(side_effect=AssertionError('model launch forbidden in binding regression'))}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'real_runner_binding_functions','exec'),ns)
  receipt={'mode':'build','suite':suite,'status':'CONTEXTS_BUILD_PASS_PENDING_REVIEW','compilation_binding':ns['compilation_binding'](compat),'model':ns['pin'](model)}
  return ns,compat,receipt
 def assert_case_rejected(self,ns,receipt,message):
  (ns['R']/'actual-build/results.json').write_text(json.dumps(receipt))
  with self.assertRaisesRegex(ValueError,message):ns['case']()
  ns['command'].assert_not_called()
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
 def test_build_binding_is_explicit_and_relocatable(self):
  with tempfile.TemporaryDirectory()as tmp:
   tmp=Path(tmp);ns,compat,receipt=self.binding_context(tmp)
   ns['check_build_binding'](receipt,compat)
   for key in('CODE','F','VR'):
    other=tmp/('relocated-'+key);shutil.copytree(ns[key],other);ns[key]=other
   relocated=tmp/'relocated-view.v';shutil.copyfile(compat,relocated)
   self.assertEqual(ns['compilation_binding'](relocated),receipt['compilation_binding'])
   self.assertEqual(receipt['compilation_binding']['suite'],'fetch18')
   self.assertNotIn(str(tmp),json.dumps(receipt['compilation_binding']))
 def test_case_rejects_other_suite_or_legacy_build_before_launch(self):
  with tempfile.TemporaryDirectory()as tmp:
   ns,compat,receipt=self.binding_context(Path(tmp),'contexts16');ns['suite']='fetch18'
   self.assert_case_rejected(ns,receipt,'producing build suite')
   receipt['suite']='fetch18'
   self.assert_case_rejected(ns,receipt,'producing compilation inputs')
   receipt['compilation_binding']['suite']='fetch18'
   self.assert_case_rejected(ns,receipt,'producing compilation inputs')
   receipt.pop('suite');receipt.pop('compilation_binding')
   self.assert_case_rejected(ns,receipt,'producing build suite')
 def test_case_rejects_changed_build_inputs_before_launch(self):
  for change in('header','source','runtime','options','source_order','missing_binding'):
   with self.subTest(change=change),tempfile.TemporaryDirectory()as tmp:
    ns,compat,receipt=self.binding_context(Path(tmp))
    # Freeze the producing value just as JSON receipt serialization does.
    receipt=json.loads(json.dumps(receipt))
    if change=='header':(ns['F']/'fixture.vh').write_text('different header\n')
    elif change=='source':(ns['CODE']/'common/shared_fetch.v').write_text('different source\n')
    elif change=='runtime':(ns['VR']/'include/verilated.h').write_text('different runtime\n')
    elif change=='options':ns['COMPILE_OPTIONS']['cxx']='-std=c++17'
    elif change=='source_order':ns['M']['compile_files'].reverse()
    else:receipt.pop('compilation_binding')
    self.assert_case_rejected(ns,receipt,'producing compilation inputs')
 def test_case_keeps_frozen_executable_hash_check(self):
  with tempfile.TemporaryDirectory()as tmp:
   ns,compat,receipt=self.binding_context(Path(tmp))
   (ns['R']/'actual-build/model').write_bytes(b'changed executable')
   self.assert_case_rejected(ns,receipt,'frozen executable')
if __name__=='__main__':unittest.main()
