"""Finite owner-authorized migration validation. No activation or research."""
from pathlib import Path
import subprocess,json,time,hashlib,sys,shutil,re,datetime,os,stat
R=Path('${OPENRX_LOCAL_ROOT}'); E=R/'migrations/20261009'
S=R/'checkouts/execution-6f54052'
B=E/'build-attempt-03'
G=R/'builds/gem5-rebuild-03/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt'
RES=R/'artifacts/guest-resources-ranged-20261009'
# Bind the independently reviewed new runner/request before this service starts.
RUNNER=R/'releases/runner-v1-916b6b0d/local_execution.py'
RUNNER_SHA='916b6b0d33956c847350dc54124132020968aa5a6ff11576911141fa27460977'
SPEC=R/'requests/spec-issue-27-local-runtime-6f54052-attempt-02.json'
SPEC_SHA='b0117492ebcf3681fcd28d5b0ae04c7ede200a1deb341566890647d09fdf8ecd'
REQUEST_KEY='issue-27-local-runtime-6f54052-attempt-02'
SOURCE_COMMIT='6f54052a2be04b6967f65d6645e9a531270721d7'
CONFIG_SHA='f839a59b33a593a63c3f5bef53bfac468df0619fcc46c3583c76b08b2d08564c'
def require(condition,message):
 if not condition:raise ValueError(message)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def syncdir(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:os.close(fd)
def syncfile(p):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  require(stat.S_ISREG(os.fstat(fd).st_mode),'not regular: '+str(p))
  os.fsync(fd)
 finally:os.close(fd)
 syncdir(p.parent)
def newtext(p,text):
 with p.open('x') as out:out.write(text);out.flush();os.fsync(out.fileno())
 syncdir(p.parent)
def newjson(p,obj):newtext(p,json.dumps(obj,indent=2)+'\n')
def unit(name):
 r=subprocess.run(['systemctl','--user','show',name,'-p','ActiveState','-p','Result','-p','ExecMainStatus'],capture_output=True,text=True,check=True)
 return dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
def post(p):
 return subprocess.check_output(['gh','issue','comment','27','--repo','jliu67/OpenRX','--body-file',str(p)],text=True).strip()
def binding_checks():
 require(sha(RUNNER)==RUNNER_SHA,'runner drift')
 require(sha(SPEC)==SPEC_SHA,'owner request drift')
 spec=json.loads(SPEC.read_text())
 require(spec['runner_sha256']==RUNNER_SHA and spec['source_commit']==SOURCE_COMMIT and spec['request_key']==REQUEST_KEY,'owner request bindings')
 require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=S,text=True).strip()==SOURCE_COMMIT,'source commit drift')
 require(not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=S,text=True).strip(),'source worktree drift')
 require(sha(R/'artifacts/gem5-source-c8222cc.tar.gz')=='0f4102a3ece810342b0a0124d44f9cb6a5b0aba08b436998b5e5069ab35bdba3','upstream archive drift')
 require(sha(S/'simulator/gem5/resources.json')=='67c3838d04b617b3a4f34a874f84cc2c5517eca51c9049456bc6df19312404bb','resources manifest drift')
binding_checks()
print('WAITING for persistent single-worker build; no wall cutoff',flush=True)
while unit('openrx-migration-build03-20261009').get('ActiveState') in ['active','activating','deactivating']:time.sleep(30)
build_unit=unit('openrx-migration-build03-20261009')
require(build_unit['Result']=='success' and build_unit['ExecMainStatus']=='0','build service failed: '+str(build_unit))
build=json.loads((B/'build-result.json').read_text())
require(build['returncode']==0 and not build['source_changed'] and build['build-info_exit']==0 and build['loader_exit']==0,'build result rejected')
require(build['config_sha256_after']==CONFIG_SHA and sha(B/'canonical-config')==CONFIG_SHA,'canonical config drift')
require(sha(G)==build['binary_sha256'] and G.stat().st_size==build['binary_bytes'],'simulator drift')
require(sha(G.parents[0]/'gem5.build/config')==CONFIG_SHA,'actual generated config drift')
sys.path.insert(0,str(S))
from simulator.gem5.bundle import check_build_info,check_config
check_build_info((B/'build-info.log').read_text());check_config((B/'canonical-config').read_text())
P=R/'toolchains/ubuntu22-20261009/pinned-packages.json'
require(sha(P)=='c3948ff082235733e12ec2264a5c050936e4fef8547446c9389cf98036b86676','package pin manifest drift')
pins=json.loads(P.read_text())
require(len(pins['pins'])==41 and len(pins['archives'])==41,'package closure entry count drift')
for pin in pins['pins']:
 actual=subprocess.check_output(['dpkg-query','-W','-f=${Version}',pin['package']],text=True).strip()
 require(actual==pin['version'],'installed package drift: '+pin['package'])
for item in pins['archives']:
 f=P.parent/item['file']
 require(f.stat().st_size==item['bytes'] and sha(f)==item['sha256'],'package archive drift: '+item['file']);syncfile(f)
manifest=json.loads((S/'simulator/gem5/resources.json').read_text())
for item in manifest['resources']:
 f=RES/item['filename'];require(f.stat().st_size==item['bytes'] and sha(f)==item['sha256'],'guest resource drift: '+str(f));syncfile(f)
ELF=R/'artifacts/guest-20261008/openrx-runtime-probe'
require(sha(ELF)=='8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac','guest ELF drift');syncfile(ELF)
for f in [G,B/'build-result.json',B/'canonical-config',B/'build-info.log',B/'loader.log',P,RUNNER,SPEC,R/'artifacts/gem5-source-c8222cc.tar.gz']:syncfile(f)
for f in S.rglob('*'):
 require(not f.is_symlink(),'execution source contains symlink')
 if f.is_file():syncfile(f)
for d in sorted([S,*[f for f in S.rglob('*') if f.is_dir()]],key=lambda p:len(p.parts),reverse=True):syncdir(d)
syncdir(S.parent)
loader=subprocess.run(['ldd',str(G)],capture_output=True,text=True,check=True)
require('not found' not in loader.stdout,'host loader closure incomplete')
D=R/('toolchains/gem5-runtime-'+build['binary_sha256'][:12]);D.mkdir();(D/'lib').mkdir()
libs=[]
for line in loader.stdout.splitlines():
 m=re.match(r'\s*(\S+) => (/\S+) \(',line);direct=re.match(r'\s*(/\S+) \(',line)
 if not m and not direct:continue
 name,path=(m.group(1),m.group(2)) if m else (Path(direct.group(1)).name,direct.group(1))
 source=Path(path).resolve(strict=True);dest=D/'lib'/name
 with source.open('rb') as inp,dest.open('xb') as out:
  shutil.copyfileobj(inp,out,4*1024*1024);out.flush();os.fsync(out.fileno())
 require(sha(dest)==sha(source),'runtime library copy mismatch');dest.chmod(0o444);syncfile(dest)
 libs.append({'soname':name,'host_path':str(source),'bytes':source.stat().st_size,'sha256':sha(source),'pinned_copy':str(dest),'interpreter':bool(direct and not m)})
syncdir(D/'lib');syncdir(D);syncdir(D.parent)
env=os.environ.copy();env['LD_LIBRARY_PATH']=str(D/'lib')
pinned_loader=subprocess.run(['ldd',str(G)],env=env,capture_output=True,text=True,check=True)
require('not found' not in pinned_loader.stdout,'pinned loader closure incomplete')
observed=[]
for line in pinned_loader.stdout.splitlines():
 m=re.match(r'\s*(\S+) => (/\S+) \(',line);direct=re.match(r'\s*(/\S+) \(',line)
 if not m and not direct:continue
 name,path=(m.group(1),m.group(2)) if m else (Path(direct.group(1)).name,direct.group(1))
 candidates=[i for i in libs if i['soname']==name];require(len(candidates)==1,'unexpected pinned closure: '+name)
 source=Path(path).resolve(strict=True);require(sha(source)==candidates[0]['sha256'],'observed loader library drift: '+name)
 if m:require(source==(D/'lib'/name).resolve(),'library not using pinned profile: '+name)
 observed.append({'soname':name,'resolved_path':str(source),'sha256':sha(source)})
require(len(observed)==len(libs),'incomplete observed library closure')
info=subprocess.run([str(G),'--build-info'],env=env,capture_output=True,text=True,check=True)
check_build_info(info.stdout)
newtext(D/'pinned-build-info.log',info.stdout+info.stderr)
newjson(D/'runtime-libraries.json',{'libraries':libs,'host_ldd':loader.stdout,'pinned_ldd':pinned_loader.stdout,'observed_pinned_closure':observed,'binary_sha256':build['binary_sha256'],'core_package_manifest_sha256':sha(P),'installed_core_pins_verified':len(pins['pins']),'limitation':'Host ELF interpreter digest explicitly verified; Python standard library versions must match recorded pins; no complete offline/hermetic host rebuild claimed'})
binding_checks()
preflight={'state':'LOCAL_VALIDATING','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'build':build,'build_unit':build_unit,'build_result_sha256':sha(B/'build-result.json'),'original_binary_restored':False,'new_binary_pinned':True,'source_commit':SOURCE_COMMIT,'runner_sha256':sha(RUNNER),'request_key':REQUEST_KEY,'request_spec_sha256':sha(SPEC),'guest_resources_verified':True,'guest_runtime_sha256':sha(ELF),'runtime_library_profile_sha256':sha(D/'runtime-libraries.json'),'core_package_pins_verified':len(pins['pins']),'scientific_validation':'pending actual runtime; no full-scale workload authorized','remote_execution':'unavailable; fixed owner-authorized request only'}
newjson(E/'local-validation-preflight.json',preflight)
subprocess.run(['/usr/bin/python3',str(RUNNER),'--root',str(R),'state','--state','LOCAL_VALIDATING','--evidence',str(E/'local-validation-preflight.json'),'--reason','Completed pinned-source rebuild and guest/dependency/loader inputs verified; strict runtime smoke only'],check=True)
with (E/'state-events.jsonl').open('a') as out:
 out.write(json.dumps({'at':preflight['utc'],'state':'LOCAL_VALIDATING','evidence':str(E/'local-validation-preflight.json'),'sha256':sha(E/'local-validation-preflight.json'),'reason':'verified simulator and essential inputs; actual correctness remains pending'})+'\n');out.flush();os.fsync(out.fileno())
syncdir(E)
newtext(E/'local-validating-announcement.md','**LOCAL_VALIDATING — NOT ACTIVE.** Objective preflight verified the distinct pinned-source simulator rebuild, guest pins, exact41 core packages and actual pinned loader closure. New simulator SHA256 `'+build['binary_sha256']+'`; preflight SHA256 `'+sha(E/'local-validation-preflight.json')+'`; both host state journals bind that evidence. Strict runtime-only request `'+REQUEST_KEY+'` will execute through the accepted persistent runner. Independent guest review, safe-stop proof and cutover remain. No full-scale research or original simulator restoration is claimed.\n')
post(E/'local-validating-announcement.md')
binding_checks()
cmd=['/usr/bin/python3',str(RUNNER),'--root',str(R),'submit','--request-key',REQUEST_KEY,'--kind','validation','--validation-scope','guest-runtime-smoke','--cwd',str(S),'--input',str(G),'--input',str(ELF),'--input',str(RES/'opensbi'),'--input',str(RES/'vmlinux'),'--input',str(RES/'ubuntu.img'),'--input',str(D),'--input',str(SPEC),'--source',str(S),'--env','LD_LIBRARY_PATH='+str(D/'lib'),'--','/usr/bin/python3','simulator/gem5/run.py','--gem5',str(G),'--resources',str(RES),'--runtime-binary',str(ELF),'--output-dir','{execution_dir}/payload','--max-ticks','10000000000000','--stop-file','{execution_dir}/stop.request']
newjson(E/'runtime-submission-argv.json',{'argv':cmd})
submission=subprocess.run(cmd,capture_output=True,text=True,check=True)
result=json.loads(submission.stdout);ID=result['execution_id'];newjson(E/'runtime-execution-id.json',result)
print('RUNTIME execution',ID,flush=True)
newtext(E/'runtime-submitted.md','Runtime-only owner CLI submission: execution `'+ID+'`, request `'+REQUEST_KEY+'`, manifest SHA256 `'+sha(R/'executions'/ID/'manifest.json')+'`. Retained status/logs are host records; launch is no pass. Source6f54052 and runner SHA256 `'+RUNNER_SHA+'` are bound. Remote direct execution remains unavailable.\n')
post(E/'runtime-submitted.md')
while unit('openrx-'+ID+'.service').get('ActiveState') in ['active','activating','deactivating']:time.sleep(30)
subprocess.run(['/usr/bin/python3',str(RUNNER),'--root',str(R),'recover',ID],check=True)
subprocess.run(['/usr/bin/python3',str(RUNNER),'--root',str(R),'verify',ID],check=True)
payload=R/'executions'/ID/'payload/report.json'
report=json.loads(payload.read_text()) if payload.exists() else {'status':'missing','error':'scientific report unavailable'}
newjson(E/'runtime-capture-summary.json',{'execution_id':ID,'request_key':REQUEST_KEY,'runtime_status':report.get('status'),'runtime_validated':report.get('runtime_validated',False),'report_sha256':sha(payload) if payload.exists() else None,'receipt_sha256':sha(R/'executions'/ID/'receipt.json'),'scientific_acceptance':'candidate capture only; independent replay required','migration_complete':False})
newtext(E/'runtime-capture-post.md','**LOCAL_VALIDATING — NOT ACTIVE.** Runtime-only execution `'+ID+'` finished; retained scientific report status `'+str(report.get('status'))+'`, runtime validated `'+str(report.get('runtime_validated',False))+'`. Output receipt integrity verified; capture SHA256 `'+sha(E/'runtime-capture-summary.json')+'`. Independent guest/input/model review, actual simulator stop proof, final docs and reviewed merge remain. #16 and M1–M5 remain open.\n')
post(E/'runtime-capture-post.md')
print('FINITE MIGRATION VALIDATION CAPTURE COMPLETE; independent acceptance pending',flush=True)
