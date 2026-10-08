import datetime,hashlib,json,os,pathlib,subprocess,time
p=pathlib.Path('/tmp/openrx-gem5-source/link-recovery-20261008')
s=pathlib.Path('/tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9')
env=dict(os.environ)
env.update(PATH='/tmp/openrx-gem5-source/apt-root/usr/bin:'+env['PATH'],PYTHONPATH='/tmp/openrx-gem5-source/python-build-deps',PYTHON_CONFIG='/tmp/openrx-gem5-source/bin/python3-config',LD_LIBRARY_PATH='/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu')
args=['timeout','600','python3','-m','SCons','build/RISCV/gem5.opt','-j6','--without-tcmalloc','--limit-ld-memory-usage']
config=s/'build/RISCV/gem5.build/config'
before=json.loads((p/'object-metadata-before.json').read_text())
assert before['config_sha256']==hashlib.sha256(config.read_bytes()).hexdigest()
for obj,info in before.items():
 if obj=='config_sha256':continue
 f=pathlib.Path(obj)
 assert f.stat().st_size==info['size_bytes'] and f.stat().st_mtime_ns==info['mtime_ns'],obj
assert '[     CXX]' not in (p/'dry-run-confirmed.log').read_text()
start=datetime.datetime.now(datetime.timezone.utc)
def mem():
 c=pathlib.Path('/sys/fs/cgroup')
 stat={k:int(v) for k,v in (x.split() for x in (c/'memory.stat').read_text().splitlines())}
 return {'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'memory_current_bytes':int((c/'memory.current').read_text()),'memory_stat':{k:stat[k] for k in ('anon','file','inactive_file','active_file')},'memory_events':{k:int(v) for k,v in (x.split() for x in (c/'memory.events').read_text().splitlines())}}
provenance={'schema':'openrx-gem5-link-recovery-v1','source_revision':'c8222cc67a399bfc01e8658dd14b30d5bfd634f9','source_archive_sha256':'0f4102a3ece810342b0a0124d44f9cb6a5b0aba08b436998b5e5069ab35bdba3','source_directory':str(s),'canonical_config_before_sha256':before['config_sha256'],'started_utc':start.isoformat(),'deadline_utc':(start+datetime.timedelta(seconds=600)).isoformat(),'command_argv':args,'command_environment':{k:env[k] for k in ('PATH','PYTHONPATH','PYTHON_CONFIG','LD_LIBRARY_PATH')},'link_option_difference':'--limit-ld-memory-usage; upstream adds -Wl,--no-keep-memory; no source/Kconfig change','status':'running','timeout_seconds':600,'jobs':6,'memory_limit_bytes':int(pathlib.Path('/sys/fs/cgroup/memory.max').read_text()),'cpu_quota':pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_before':mem(),'binary_preflight_executed':False,'guest_boot_executed':False}
(p/'recovery-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(p/'canonical-config-before').write_bytes(config.read_bytes())
print(json.dumps({'started_utc':provenance['started_utc'],'deadline_utc':provenance['deadline_utc'],'mode':'supported reduced-memory link retry'}),flush=True)
log=open(p/'recovery.log','w')
proc=subprocess.Popen(args,cwd=s,env=env,stdout=log,stderr=subprocess.STDOUT)
while True:
 observation=mem();observation['processes']=[]
 for f in pathlib.Path('/proc').glob('[0-9]*/status'):
  try:
   status={a:b.strip() for a,b in (line.split(':',1) for line in f.read_text().splitlines() if ':' in line)}
   if status.get('Name') not in ('ld','ld.bfd','collect2','cc1plus'):continue
   raw=(f.parent/'stat').read_text().rsplit(') ',1)[1].split()
   observation['processes'].append({'pid':int(f.parent.name),'name':status['Name'],'rss_kib':int(status.get('VmRSS','0 kB').split()[0]),'cpu_user_seconds':int(raw[11])/100,'cpu_system_seconds':int(raw[12])/100,'cmdline':(f.parent/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')[:500]})
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 with (p/'resource-observations.jsonl').open('a') as out:out.write(json.dumps(observation)+'\n')
 print(json.dumps({'checkpoint_utc':observation['recorded_utc'],'anon_gib':round(observation['memory_stat']['anon']/2**30,3),'oom_kill':observation['memory_events']['oom_kill'],'linkers':observation['processes']}),flush=True)
 try:
  code=proc.wait(timeout=30);break
 except subprocess.TimeoutExpired:pass
log.close();end=datetime.datetime.now(datetime.timezone.utc)
(p/'recovery-exit-code.txt').write_text(str(code)+'\n')
provenance.update(ended_utc=end.isoformat(),elapsed_seconds=(end-start).total_seconds(),returncode=code,status='target-build-success-pending-identity-verification' if code==0 else 'failed',canonical_config_after_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),memory_after=mem())
(p/'recovery-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({'returncode':code,'ended_utc':end.isoformat(),'elapsed_seconds':provenance['elapsed_seconds']}),flush=True)
raise SystemExit(code)
