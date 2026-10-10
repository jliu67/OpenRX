"""Separate bounded single-worker build recovery; preserves prior attempt."""
from pathlib import Path
import subprocess,json,hashlib,datetime,fcntl,sys,os
ROOT=Path('${OPENRX_LOCAL_ROOT}')
E=ROOT/'migrations/20261009/build-attempt-03'
E.mkdir()
S=ROOT/'builds/gem5-rebuild-03/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9'
R=ROOT/'checkouts/execution-6f54052'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
def require(condition,message):
 if not condition:raise ValueError(message)
def newjson(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
lock=(ROOT/'locks/execution.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX)
require(sha(ROOT/'artifacts/gem5-source-c8222cc.tar.gz')=='0f4102a3ece810342b0a0124d44f9cb6a5b0aba08b436998b5e5069ab35bdba3','source archive drift')
inventory=json.loads((ROOT/'migrations/20261009/source-inventory.json').read_text())
changed=[item['path'] for item in inventory['files'] if sha(S/item['path'])!=item['sha256']]
require(not changed,('copied source drift',changed))
subprocess.run(['dpkg-query','-W'],stdout=(E/'toolchain-packages.txt').open('x'),check=True)
for name,cmd in [('gcc-version',['gcc','--version']),('python-version',['python3','--version']),('scons-version',['scons','--version'])]:
 subprocess.run(cmd,stdout=(E/(name+'.txt')).open('x'),stderr=subprocess.STDOUT,check=True)
config=S/'build/RISCV/gem5.build/config'
configsha=sha(config)
sys.path.insert(0,str(R))
from simulator.gem5.bundle import check_config
check_config(config.read_text())
require(configsha=='f839a59b33a593a63c3f5bef53bfac468df0619fcc46c3583c76b08b2d08564c',('HOST CONFIG DRIFT',configsha))
require(b''.join(line for line in config.read_bytes().splitlines(keepends=True) if line not in [b'HAVE_PNG=y\n',b'HAVE_HDF5=y\n',b'HAVE_PROTOBUF=y\n'])==(R/'docs/validation/m3-fs/build-20261008/canonical-config').read_bytes(),'canonical scientific config differs')
with (E/'canonical-config').open('xb') as f:f.write(config.read_bytes());f.flush();os.fsync(f.fileno())
command=['scons','build/RISCV/gem5.opt','-j1','--limit-ld-memory-usage','--without-tcmalloc']
newjson(E/'build-command.json',{'argv':command,'source_archive_sha256':sha(ROOT/'artifacts/gem5-source-c8222cc.tar.gz'),'source_commit':'c8222cc67a399bfc01e8658dd14b30d5bfd634f9','config_sha256':configsha,'project_commit':'6f54052a2be04b6967f65d6645e9a531270721d7','start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_path':str(S),'recovery':'separate full copy of preserved attempt02 partial build; incremental SCons recompilation; no scientific checkpoint resume; no wall timeout','budget':{'MemoryMax':'8G','MemorySwapMax':'2G','CPUQuota':'100%'}})
rc=subprocess.run(command,cwd=S).returncode
changed=[item['path'] for item in inventory['files'] if sha(S/item['path'])!=item['sha256']]
result={'returncode':rc,'source_changed':changed,'config_sha256_after':sha(config),'completion_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scientific_validation':'not performed'}
if rc==0:
 binary=S/'build/RISCV/gem5.opt'
 result.update(binary_sha256=sha(binary),binary_bytes=binary.stat().st_size)
 for name,cmd in [('build-info',[str(binary),'--build-info']),('loader',['ldd',str(binary)])]:
  with (E/(name+'.log')).open('x') as out:
   result[name+'_exit']=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT).returncode
   out.flush();os.fsync(out.fileno())
newjson(E/'build-result.json',result)
require(rc==0 and not changed and result['config_sha256_after']==configsha,result)
print('BUILD VERIFIED',json.dumps(result),flush=True)
