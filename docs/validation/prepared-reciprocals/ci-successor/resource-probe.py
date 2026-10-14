"""Bounded metadata guard payload; no compiler, simulator or scientific run."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

out = Path(sys.argv[1])
out.mkdir(exist_ok=False)
source = Path(sys.argv[2])
slot = open('/home/server/openrx-local/v1/locks/execution.lock', 'a+')
fcntl.flock(slot, fcntl.LOCK_EX | fcntl.LOCK_NB)
cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
expected = {'cpu.max': '600000 100000', 'memory.max': '1073741824',
            'memory.swap.max': '134217728', 'pids.max': '64'}
actual = {n: (cg / n).read_text().strip() for n in expected}
assert actual == expected, actual
ancestors = {str(a): {n: (a / n).read_text().strip() for n in expected if (a / n).exists()}
             for a in [cg, *cg.parents] if str(a).startswith('/sys/fs/cgroup')}
for a, limits in ancestors.items():
    for n, v in limits.items():
        if n == 'cpu.max':
            assert v.split()[0] == 'max' or int(v.split()[0]) / int(v.split()[1]) >= 6, (a,n,v)
        else:
            assert v == 'max' or int(v) >= int(expected[n]), (a,n,v)
mem = {l.split(':')[0]: int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines()}
assert mem['MemAvailable'] >= 2*1024**3
affinity = sorted(os.sched_getaffinity(0))
assert len(affinity) >= 6
receipt = {'actual_kernel_limits': actual, 'ancestors': ancestors, 'affinity': affinity,
           'MemAvailable': mem['MemAvailable'], 'SwapFree': mem['SwapFree'], 'workers': 1,
           'at_epoch': time.time(), 'global_nonblocking_lock': True,
           'reason': 'Only bounded Python source/evidence guards and rejection tests. No build/simulator/native payload. Six CPUs available; sequential checks use one worker. 1 GiB RAM/128 MiB swap safely exceed small metadata input; fresh 1 GiB OS reserve.'}
(out/'resource.json').write_text(json.dumps(receipt, indent=2)+'\n')
commands = [
    [sys.executable,'-B','scripts/prepared_parent_bindings.py','--check-evidence','--output',str(out/'source-binding-report.json')],
    [sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_prepared_parent_bindings.py','-v'],
    [sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_reciprocal_cycle_model.py','-v'],
]
journal=[]
try:
    for i, cmd in enumerate(commands):
        start=time.time()
        r=subprocess.run(cmd,cwd=source,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        (out/f'{i:02d}.stdout').write_text(r.stdout)
        (out/f'{i:02d}.stderr').write_text(r.stderr)
        journal.append({'argv':cmd,'cwd':str(source),'returncode':r.returncode,'wall_seconds':time.time()-start})
        (out/'commands.json').write_text(json.dumps(journal,indent=2)+'\n')
        print(r.stdout+r.stderr,flush=True)
        assert r.returncode == 0, cmd
finally:
    receipt['kernel_final']={n:(cg/n).read_text().strip() for n in ['cpu.stat','memory.peak','memory.events','memory.swap.peak','pids.current'] if (cg/n).exists()}
    receipt['completed_commands']=len(journal)
    receipt['returncode']=0 if len(journal)==len(commands) and all(r['returncode']==0 for r in journal) else 1
    (out/'resource.json').write_text(json.dumps(receipt,indent=2)+'\n')
