"""Run one isolated accepted experimental VM top in a reviewed capped host context.

External native fixtures and pinned Verilator sources are explicit inputs.
No dependency installs, native/fullhash replay, uncapped fallback or retries.
"""
import argparse,fcntl,gzip,hashlib,importlib.util,json,os,pwd,re,resource,shutil,signal,struct,subprocess,sys,tarfile,tempfile,time
from pathlib import Path
CODE=Path(__file__).resolve().parents[1];SRC=CODE.parents[1]
META=CODE/'fixtures/provenance.json';M=json.loads(META.read_text())
COMPILE_OPTIONS={'verilator':['--cc','--main','--exe','--timing','--top-module','tb_contexts','--output-split','10000','--output-split-cfuncs','1000','-Wno-fatal'],
 'cxx':'-std=c++20','link':'-pthread -ldl -Wl,-z,noexecstack',
 'make':['-j2','VM_DEFAULT_RULES=0','OPT_FAST=-Os','OPT_SLOW=-Os','OPT_GLOBAL=-Os','model'],
 'ordinary_mk':'include Vtb_contexts.mk\n%.o: %.cpp\n\t$(CXX) -Os $(CXXFLAGS) $(CPPFLAGS) -c -o $@ $<\n'}
INCLUDE_DIRS=['rtl/execute','rtl/execute/vendor/hardfloat','rtl/execute/vendor/hardfloat/8086-SSE','rtl/hash/vendor/blake2']
MATRIX={'contexts16':[(0,1,0,0),(1,1,0,0),(0,10,0,0),(1,10,0,0),(1,10,1,2)],
 'fetch18':[(0,1,1,0,0,0),(1,0,1,0,0,0),(1,1,1,0,0,0),(1,1,10,0,0,0),(1,1,10,1,2,0),(1,1,1,2,0,0)]+[(1,1,1,0,0,x)for x in(1,2,3,4)],
 'iterations20':[(0,0,1,0,0,0),(0,1,1,0,0,0),(1,0,1,0,0,0),(1,1,1,0,0,0),(0,1,10,0,0,0),(1,1,10,0,0,0)]}
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--suite',choices=MATRIX,required=True);p.add_argument('--list-cases',action='store_true')
for n in('output','fixtures','native-dir','verilator-root','kernel-guard','lock'):p.add_argument('--'+n,type=Path)
p.add_argument('--lock-identity',type=int,nargs=3);p.add_argument('--unit')
p.add_argument('mode',choices=('build','case'),nargs='?');p.add_argument('operands',type=int,nargs='*')
args=p.parse_args()
if args.kernel_guard is None:args.kernel_guard=CODE/'tools/kernel_guards.py'
if args.list_cases:print(json.dumps(MATRIX[args.suite]));raise SystemExit(0)
if not all(getattr(args,n)for n in('output','fixtures','native_dir','verilator_root','lock','lock_identity','unit'))or not args.mode:p.error('explicit paths, approved exclusion identity and current capped unit are required')
mode=args.mode;suite=args.suite;operands=tuple(args.operands)
if(mode=='build'and operands)or(mode=='case'and operands not in MATRIX[suite]):p.error('closed accepted operand matrix')
fetch,policy,rd,cancel,hold,fault=(0,0,0,0,0,0)if mode=='build'else((0,*operands,0)if suite=='contexts16'else operands)
R=args.output.resolve();R.mkdir(parents=True,exist_ok=True);F=args.fixtures.resolve(strict=True);G=args.native_dir.resolve(strict=True)
VR=args.verilator_root.resolve(strict=True)
HOME=pwd.getpwuid(os.getuid()).pw_dir
ENV={'HOME':HOME,'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','XDG_RUNTIME_DIR':'/run/user/'+str(os.getuid())}
NENV={'HOME':str(R/'absent-native-home'),'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C','VERILATOR_ROOT':str(VR)}
START=time.monotonic();CHILDREN=[];ROWS=[];LOCK=None
suffix='build'if mode=='build'else'case-'+'-'.join(map(str,operands))
OUT=R/('actual-'+suffix);UNIT=args.unit
if not re.fullmatch(r'codex-openrx-[a-z0-9-]+\.scope',UNIT):p.error('exact owned codex-openrx scope unit required')
def require(v,m):
 if not v:raise ValueError(m)
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,separators=(',',':'));f.write('\n')
def retained():return sum(p.stat().st_size for p in R.rglob('*')if p.is_file()and p.name not in('launch-stdout.txt','launch-stderr.txt'))
def budget(reserve=65536):
 require(retained()+reserve<=4194304,'complete experiment retained4MiB cap, final result reserve included')
 require(time.monotonic()-START<105,'active lifecycle bound')
def command(name,argv,cwd,seconds,allow_stderr=False):
 budget();row={'name':name,'argv':argv,'cwd':str(cwd),'returncode':None,'capture_complete':False};ROWS.append(row)
 p=subprocess.Popen(argv,cwd=cwd,env=NENV,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);CHILDREN.append(p)
 try:out,err=p.communicate(timeout=min(seconds,max(.1,105-(time.monotonic()-START))))
 except BaseException:
  try:os.killpg(p.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  try:
   out,err=p.communicate(timeout=5);row.update(returncode=p.returncode,capture_complete=True)
   (OUT/(name+'.stdout')).write_bytes(out);(OUT/(name+'.stderr')).write_bytes(err)
  except subprocess.TimeoutExpired:row['cleanup_capture_incomplete']=True
  raise
 row.update(returncode=p.returncode,capture_complete=True)
 require(len(out)+len(err)<=1048576,'complete child capture bound')
 for n,b in [('stdout',out),('stderr',err)]:
  path=OUT/(name+'.'+n+('.gz'if name=='component'and n=='stdout'else''))
  data=gzip.compress(b,mtime=0)if path.suffix=='.gz'else b
  if path.suffix=='.gz':require(gzip.decompress(data)==b,'lossless complete capture')
  with path.open('xb')as f:f.write(data)
  row[n]=pin(path)
  if path.suffix=='.gz':row['raw_stdout']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 budget();require(p.returncode==0,'first failure: '+name)
 if not allow_stderr:require(err==b'','compiler/runtime diagnostics must be empty')
 return out,err
def stack_flags(p):
 b=Path(p).read_bytes();require(b[:6]==b'\x7fELF\x02\x01','ELF64LE');h=struct.unpack_from('<16sHHIQQQIHHHHHH',b)
 ph=[struct.unpack_from('<IIQQQQQQ',b,h[5]+i*h[9])for i in range(h[10])];s=[x[1]for x in ph if x[0]==0x6474e551];require(s==[6],'explicit RW GNU_STACK, no PF_X');return s[0]
def compile_sources(compat):
 # This ordered list drives both compilation and the prelaunch identity check.
 files=[('hardfloat-compile-view',compat)if x=='@HARDFLOAT_VIEW'else('repo/'+x,SRC/x)for x in M['compile_files']]
 extra=['tests/contexts16/context_execute.v'if suite=='contexts16'else'common/context_execute.v','common/shared_fu.v']
 if suite!='contexts16':extra.append('common/shared_fetch.v')
 if suite=='iterations20':extra.append('common/iteration_shell.v')
 extra.append('tests/'+suite+'/tb_contexts.v')
 return files+[('experiment/'+x,CODE/x)for x in extra]
def compilation_binding(compat):
 def content(p):
  value=pin(p);return {'bytes':value['bytes'],'sha256':value['sha256']}
 return {'schema':'openrx.shared-context-vm.compilation.v1','suite':suite,
  'sources':[{'name':name,**content(path)}for name,path in compile_sources(compat)],
  'fixture_header':content(F/'fixture.vh'),
  'golden_closure':[{'name':x['path'],**content(SRC/x['path'])}for x in M['golden_files']],
  'compile_view_helper':content(SRC/'scripts/hardfloat_compile_view.py'),
  'verilator':[{'name':name,**content(VR/name)}for name in sorted({**M['verilator_programs'],**M['verilator_runtime_files']})],
  'include_order':['fixture']+INCLUDE_DIRS,'options':COMPILE_OPTIONS}
def check_build_binding(b,compat):
 require(b.get('mode')=='build'and b.get('status')=='CONTEXTS_BUILD_PASS_PENDING_REVIEW','one exact successful build')
 require(b.get('suite')==suite,'producing build suite mismatch or missing')
 require(b.get('compilation_binding')==compilation_binding(compat),'producing compilation inputs mismatch or missing')
def build():
 # Fresh derivation uses official HARDWARE_DATASET=0 elaboration. Every
 # unmodified HDL file is checked against accepted compiler-input hashes.
 for row in M['golden_files']:
  v=pin(SRC/row['path']);require(v['bytes']==row['bytes']and v['sha256']==row['sha256'],'golden source closure drift')
 require(pin(SRC/'scripts/hardfloat_compile_view.py')['sha256']==M['hardfloat_helper_sha256'],'accepted compile view helper')
 spec=importlib.util.spec_from_file_location('shared_vm_compile_view',SRC/'scripts/hardfloat_compile_view.py');view=importlib.util.module_from_spec(spec);spec.loader.exec_module(view)
 compat=view.prepare(SRC/'rtl/execute/vendor/hardfloat/divSqrtRecFN_small.v',OUT)
 result['compile_view']=pin(compat)
 binding=compilation_binding(compat)
 source_files=[str(path)for name,path in compile_sources(compat)]
 includes=['-I'+str(F)]+['-I'+str(SRC/x)for x in INCLUDE_DIRS]
 # Standard compiler scratch, not a retained evidence/mirror directory. Source
 # and final artifact are preserved before its ordinary lifecycle cleanup.
 with tempfile.TemporaryDirectory(prefix='openrx-precomputed06-',dir='/dev/shm')as tmp:
  work=Path(tmp);obj=work/'obj';obj.mkdir()
  argv=[str(VR/'bin/verilator'),*COMPILE_OPTIONS['verilator'],'--Mdir',str(obj),'-o','model',*includes,'-CFLAGS',COMPILE_OPTIONS['cxx'],'-LDFLAGS',COMPILE_OPTIONS['link'],*source_files]
  # Retain all frontend diagnostics under the original accepted -Wno-fatal
  # workflow. New errors are fatal; no warning text is filtered or discarded.
  command('verilate',argv,R,40,allow_stderr=True)
  # The upstream build creates91MiB PCH files, which do not fit the unchanged
  # per-file cap. Ordinary textual-header compilation changes no model source.
  rules=obj/'ordinary.mk';rules.write_text(COMPILE_OPTIONS['ordinary_mk'])
  # Compile the exact pinned Verilator runtime from source, using ordinary
  # textual headers within the same per-file/memory/time caps. No private .o
  # blobs, PCH files or model-specific objects are imported.
  command('compile-link',['/usr/bin/make','-C',str(obj),'-f','ordinary.mk',*COMPILE_OPTIONS['make']],R,95)
  model=obj/'model';require(model.is_file(),'final native executable');stack_flags(model)
  with model.open('rb')as f,(OUT/'model').open('xb')as g:
   for b in iter(lambda:f.read(1048576),b''):g.write(b)
  shutil.copymode(model,OUT/'model')
  generated=[p for p in obj.rglob('*')if p.is_file()and p.suffix in('.cpp','.h','.mk','.dat')]
  result['generated_sources']=[{'name':str(p.relative_to(obj)),**pin(p)}for p in generated]
  archive=OUT/'generated-sources.tar.gz'
  with tarfile.open(archive,'w:gz',compresslevel=6)as tar:
   for p in sorted(generated):tar.add(p,arcname=str(p.relative_to(obj)),recursive=False)
  expected={str(p.relative_to(obj)):pin(p)['sha256']for p in generated}
  with tarfile.open(archive,'r:gz')as tar:
   members=tar.getmembers();require(len(members)==len(expected),'complete source archive')
   for m in members:
    require(m.isfile()and m.name in expected and not m.name.startswith('/')and '..'not in Path(m.name).parts,'closed archive member');require(hashlib.sha256(tar.extractfile(m).read()).hexdigest()==expected[m.name],'lossless generated source roundtrip')
  result['generated_source_archive']=pin(archive);result['model']=pin(OUT/'model');budget()
 require(compilation_binding(compat)==binding,'post-build compilation input drift')
 result['compilation_binding']=binding;result['status']='CONTEXTS_BUILD_PASS_PENDING_REVIEW'
def case():
 buildroot=R/'actual-build';b=json.loads((buildroot/'results.json').read_text())
 check_build_binding(b,buildroot/'HardFloat-divSqrt-compile-view.v')
 require(pin(buildroot/'model')==b['model'],'frozen executable');stack_flags(buildroot/'model');budget(524288+65536)
 argv=[str(buildroot/'model'),'+POLICY='+str(policy),'+READ='+str(rd),'+CANCEL='+str(cancel),'+HOLD='+str(hold),'+FETCH='+str(fetch),'+FAULT='+str(fault),'+RCP='+str(F/'reciprocals.mem'),'+EVENTS='+str(F/'events.mem')]
 if suite=='iterations20':argv += ['+INITIAL'+str(i)+'='+str(G/('initial.hex'if i==0 else'final-'+str(i-1)+'.hex'))for i in range(4)]+['+PROGRAM='+str(F/'programs.mem')]
 else:argv += ['+INITIAL='+str(G/'initial.hex'),'+PROGRAM='+str(G/'program-0.mem')]
 out,err=command('component',argv,R,85)
 if fault:marker=('FETCH_REJECTION_PASS fault='+str(fault)).encode()
 elif suite=='iterations20':marker=b'ITERATIONS_NATIVE_PASS contexts=4 programs=0,1,2,3 steps=384,384,393,384 events=80,90,82,91 full_iteration_entry_dataset_XOR_AES_tail=1 shared_pool=1 credits_drained=1 complete_hash=0'
 else:marker=b'CONTEXTS_NATIVE_PASS contexts=4 steps_each=384 events_each=80 native_R_E_round_route_and_AES_F=1 shared_pool=1 credits_drained=1 complete_hash=0'
 require(out.count(marker)==1,'exact accepted suite closure')
 result['configuration']={'suite':suite,'operands':operands}
 result['status']='FETCH_REJECTION_PASS_PENDING_INDEPENDENT_REVIEW'if fault else'FETCH_NATIVE_COMPONENT_PASS_PENDING_INDEPENDENT_REVIEW'

result={'schema':'openrx.shared-fetch-component.actual.v1','mode':mode,'suite':suite,'status':'PREPARING','scientific_acceptance':False,'physical_acceptance':False,'physical_unknowns':117}
try:
 require(dict(os.environ)==ENV and os.getuid()!=0 and not OUT.exists(),'fresh clean ordinary test context');require(sorted(os.sched_getaffinity(0))==list(range(6)),'six eligible CPUs')
 LOCK=os.open(args.lock,os.O_RDWR|os.O_NOFOLLOW);st=os.fstat(LOCK);require([os.major(st.st_dev),os.minor(st.st_dev),st.st_ino]==args.lock_identity,'original global slot');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)
 guard=args.kernel_guard;require(pin(guard)['sha256']==M['guard_sha256'],'exact externally reviewed kernel guard')
 ns={'Path':Path,'os':os,'re':re,'now':lambda:'precomputed-native8','GIB':1073741824};exec(compile(guard.read_bytes(),str(guard),'exec'),ns)
 observed=ns['kernel_resources'](UNIT);require(observed is not None and not ns['kernel_resource_errors'](observed,{'kernel_memory_max_bytes':1073741824}),'kernel leaf/ancestor caps');result['kernel_limits']=observed;result['effective_limits']=ns['effective'](observed)
 available=int(next(x.split()[1]for x in Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:')))*1024;require(available>=2147483648,'host headroom')
 require(not[p for p in Path('/sys/fs/cgroup').rglob('codex-openrx-*')if p.is_dir()and p.name!=UNIT],'coexistence gate')
 resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
 OUT.mkdir()
 native_pins=json.loads((CODE/'fixtures/native-pins.json').read_text())
 inputs=[META,CODE/'fixtures/native-pins.json',Path(__file__),guard,F/'fixture.json',SRC/'scripts/hardfloat_compile_view.py',CODE/'tools/prepare_kernel.py',CODE/'tools/prepare_iterations.py']
 for row in M['golden_files']:
  v=pin(SRC/row['path']);require(v['bytes']==row['bytes']and v['sha256']==row['sha256'],'unchanged golden source closure');inputs.append(SRC/row['path'])
 for name,row in native_pins.items():
  v=pin(G/name);require(v['bytes']==row['bytes']and v['sha256']==row['sha256'],'immutable native input '+name);inputs.append(G/name)
 for name,h in M['experimental_files'].items():require(pin(CODE/name)['sha256']==h,'accepted exact experimental source');inputs.append(CODE/name)
 for name,h in M['fixtures'][suite].items():require(pin(F/name)['sha256']==h,'generated accepted fixture bytes');inputs.append(F/name)
 for name,h in M['verilator_programs'].items():require(pin(VR/name)['sha256']==h,'exact admitted Verilator');inputs.append(VR/name)
 for name,h in M['verilator_runtime_files'].items():require(pin(VR/name)['sha256']==h,'exact admitted runtime source');inputs.append(VR/name)
 result['input_pins']=[pin(x)for x in inputs]
 if mode=='build':build()
 else:case()
 for p in result['input_pins']:require(pin(p['path'])==p,'post-run input drift')
except BaseException as e:result.update(status='FAILED_FIRST_FAILURE_NO_RETRY',error={'type':type(e).__name__,'message':str(e)})
finally:
 result['commands']=ROWS;result['wall_seconds']=time.monotonic()-START;result['children']=[{'pid':p.pid,'returncode':p.poll()}for p in CHILDREN]
 if OUT.exists():
  own=Path('/sys/fs/cgroup')/next(x[3:]for x in Path('/proc/self/cgroup').read_text().splitlines()if x.startswith('0::')).lstrip('/');foreign=[]
  for p in [own/'cgroup.procs',*own.rglob('*/cgroup.procs')]:
   if p.exists():foreign.extend(int(x)for x in p.read_text().split()if int(x)!=os.getpid())
  result['slot_release_guard']={'children_reaped':all(p.poll()is not None for p in CHILDREN),'scope_only_owner':not foreign,'foreign_PIDs':foreign}
  if foreign or not all(p.poll()is not None for p in CHILDREN):result['status']='FAILED_UNVERIFIED_DRAIN_NO_FURTHER_ADMISSION'
  result['retained_experiment_bytes_before_result']=retained();result['files']=[pin(p)for p in sorted(OUT.rglob('*'))if p.is_file()]
  save(OUT/'results.json',result);require(retained()<=4194304,'complete experiment4MiB cap')
 if LOCK is not None:os.close(LOCK)
 print(json.dumps({'status':result['status'],'wall_seconds':result['wall_seconds'],'result':pin(OUT/'results.json')if(OUT/'results.json').exists()else None,'error':result.get('error')}))
if result['status']not in('CONTEXTS_BUILD_PASS_PENDING_REVIEW','FETCH_NATIVE_COMPONENT_PASS_PENDING_INDEPENDENT_REVIEW','FETCH_REJECTION_PASS_PENDING_INDEPENDENT_REVIEW','UNUSED_AREA_MODE'):sys.exit(1)
