"""Fresh serialized admission for the authorized default sequence regression."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

slot=open('/home/server/openrx-local/v1/locks/execution.lock','a+')
fcntl.flock(slot,fcntl.LOCK_EX|fcntl.LOCK_NB)
cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
expected={'cpu.max':'600000 100000','memory.max':'7516192768','memory.swap.max':'2147483648','pids.max':'128'}
actual={n:(cg/n).read_text().strip() for n in expected}
assert actual==expected,(actual,expected)
ancestors={str(a):{n:(a/n).read_text().strip() for n in expected if (a/n).exists()} for a in [cg,*cg.parents] if str(a).startswith('/sys/fs/cgroup')}
for a,limits in ancestors.items():
    for n,v in limits.items():
        if n=='cpu.max':assert v.split()[0]=='max' or int(v.split()[0])/int(v.split()[1])>=6,(a,n,v)
        else:assert v=='max' or int(v)>=int(expected[n]),(a,n,v)
mem={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines()}
assert mem['MemAvailable']>=7516192768+1073741824
affinity=sorted(os.sched_getaffinity(0));assert len(affinity)>=6
receipt={'at_epoch':time.time(),'actual_kernel_limits':actual,'ancestors':ancestors,'affinity':affinity,
         'MemAvailable':mem['MemAvailable'],'SwapFree':mem['SwapFree'],'global_nonblocking_lock':True,
         'workers':1,'reason':'Authorized PR70 default native program sequence regression and real mapped integration; unchanged test_program_sequence.py --synthesize, no --full-v2. One serial worker, six CPUs/600%,7GiB RAM/2GiB swap/Tasks128. Related actual default divsqrt whole-backend synthesis peak8053063680bytes plus593715200bytes swap, no OOM. Current roughly9.1GB MemAvailable supports7GiB RAM plus fresh1GiB OS reserve;2GiB swap accommodates related measured working set and older installed Yosys0.9 mapping. Constraints reflect current available headroom, not the smaller cache/component job. Memory pressure is reported honestly and not assumed zero. No unrelated workload or full-pipeline performance measurement.'}
dest=Path(sys.argv[1]);dest.write_text(json.dumps(receipt,indent=2)+'\n')
os.set_inheritable(slot.fileno(),True)
env=dict(os.environ,OPENRX_RESOURCE_LOCK_FD=str(slot.fileno()),PYTHONDONTWRITEBYTECODE='1')
start=time.monotonic()
result=subprocess.run(sys.argv[2:],env=env,pass_fds=(slot.fileno(),))
# The lock remains held while checking the service's owned descendant drain.
remaining=[int(p) for p in (cg/'cgroup.procs').read_text().split() if int(p)!=os.getpid()]
receipt['owned_descendants_after_payload']=remaining
receipt['returncode']=result.returncode
receipt['wall_seconds']=time.monotonic()-start
receipt['kernel_final']={n:(cg/n).read_text().strip() for n in ['cpu.stat','memory.peak','memory.events','memory.swap.peak','pids.current'] if (cg/n).exists()}
dest.write_text(json.dumps(receipt,indent=2)+'\n')
assert not remaining,'owned service descendants must drain before slot release'
sys.exit(result.returncode)
