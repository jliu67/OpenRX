import json,pathlib,os,subprocess,sys,time,fcntl
slot=open("/home/server/openrx-local/v1/locks/execution.lock","a+")
fcntl.flock(slot,fcntl.LOCK_EX|fcntl.LOCK_NB)
cg=pathlib.Path('/sys/fs/cgroup')/pathlib.Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
actual={n:(cg/n).read_text().strip() for n in ['cpu.max','memory.max','memory.swap.max','pids.max']}
expected={'cpu.max':'600000 100000','memory.max':'2147483648','memory.swap.max':'536870912','pids.max':'128'}
assert actual==expected,(actual,expected)
ancestors={str(a):{n:(a/n).read_text().strip() for n in expected if (a/n).exists()} for a in [cg,*cg.parents] if str(a).startswith('/sys/fs/cgroup')}
for a,limits in ancestors.items():
 for n,v in limits.items():
  if n=='cpu.max':
   if v.split()[0]!='max':assert int(v.split()[0])/int(v.split()[1])>=6,(a,n,v)
  elif v!='max':assert int(v)>=int(expected[n]),(a,n,v)
mem={l.split(':')[0]:int(l.split()[1])*1024 for l in pathlib.Path('/proc/meminfo').read_text().splitlines()}
assert mem['MemAvailable']>=2147483648+1073741824,mem['MemAvailable']
affinity=sorted(os.sched_getaffinity(0));assert len(affinity)>=6,affinity
receipt={'at_epoch':time.time(),'actual_kernel_limits':actual,'ancestors':ancestors,'affinity':affinity,'MemAvailable':mem['MemAvailable'],'SwapFree':mem['SwapFree'],'workers':1,'reason':'Task64 final native register-file hashing validation: balanced524 native vectors per32/64 digest, held seed contracts, native connected cancellation/version restarts, four hardware-seeded8x4 chains and bounded new-stage mapping. Actual CPU600%,2GiB RAM,512MiB swap,Tasks128,six affinity,one worker,fresh1GiB reserve/global slot. Measured pilot peak167497728 bytes and prior bounded synth/compile peak610140160 bytes, one serial worker and only new hash32/hash64/seed mapping justify2GiB; no whole execution-core synthesis/full16K regeneration.'}
pathlib.Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n')
result=subprocess.run(sys.argv[2:])
receipt['returncode']=result.returncode
receipt['kernel_final']={n:(cg/n).read_text().strip() for n in ['cpu.stat','memory.peak','memory.events','memory.swap.peak','pids.current'] if (cg/n).exists()}
pathlib.Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n')
sys.exit(result.returncode)
