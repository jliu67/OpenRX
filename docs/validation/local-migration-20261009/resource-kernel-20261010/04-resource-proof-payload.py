import json, os, pathlib, resource, sys, time
out=pathlib.Path(sys.argv[1]); out.mkdir()
allocation=bytearray(1024*1024)
records=[]
for i in range(3):
 relative=pathlib.Path('/proc/self/cgroup').read_text().strip().split('::',1)[1]
 base=pathlib.Path('/sys/fs/cgroup'); directory=base/relative.lstrip('/')
 groups=[]
 while True:
  names=('cpu.max','memory.max','memory.high','memory.swap.max','pids.max','cpuset.cpus.effective','cgroup.controllers','cgroup.subtree_control','memory.current','memory.peak','cpu.stat','pids.current')
  values={}
  for name in names:
   try: values[name]=(directory/name).read_text().strip()
   except FileNotFoundError: values[name]=None
  groups.append({'path':str(directory),'files':values})
  if directory==base: break
  directory=directory.parent
 records.append({'sample':i,'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),'groups':groups,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
 print('kernel witness sample',i,flush=True); time.sleep(2)
path=out/'kernel-witness.json'
with path.open('x') as f:
 json.dump({'scope':'tiny 1MiB resource proof; no scientific workload','records':records},f,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
