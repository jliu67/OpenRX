"""Run only affected combined regressions inside the immutable admitted runner."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode=True
source=Path(sys.argv[1]).resolve()
execution=Path(sys.argv[2]).resolve()
assert source.is_dir() and not (source/'.git').exists()
assert execution.is_dir() and source!=execution and source not in execution.parents
manifest=json.loads((execution/'manifest.json').read_text())
assert manifest['migration_state']=='LOCAL_ACTIVE' and manifest['kind']=='simulation'
assert manifest['resources']['MemoryMax']=='4294967296'
assert manifest['resources']['MemorySwapMax']=='2G' and manifest['resources']['TasksMax']==256
assert manifest['resources']['CPUQuota']=='600%' and manifest['resources']['global_slots']==1
assert manifest['runner']['sha256']=='657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b'
headroom=json.loads((execution/'prelaunch-resource-check.json').read_text())
kernel=json.loads((execution/'prelaunch-kernel-check.json').read_text())
assert kernel['safe'] and kernel['production_enforced'] and kernel['production_required']
assert not kernel['errors'] and len(os.sched_getaffinity(0))>=6
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
def resources():
    return {name:(cg/name).read_text().strip() for name in ['cpu.max','memory.max','memory.swap.max','pids.max',
        'cpu.stat','memory.peak','memory.events','memory.swap.peak','pids.current'] if (cg/name).exists()}
resource_records=[{'phase':'payload-start','at_epoch':time.time(),'kernel':resources()}]
(execution/'combined-resource-stages.json').write_text(json.dumps(resource_records,indent=2)+'\n')
retained=[]
for name,count in [('docs/validation/prepared-reciprocals/server/inputs.json',219),
                   ('docs/validation/prepared-reciprocals/program-sequence-regression/inputs.json',73)]:
    inputs=json.loads((source/name).read_text());assert len(inputs)==count
    bad=[p for p,h in inputs.items() if hashlib.sha256((source/p).read_bytes()).hexdigest()!=h]
    assert not bad,(name,bad)
    retained.append({'manifest':name,'input_count':count,'changed_live_paths':bad,
        'scope':'Retained exact executable input bytes. Existing original-base result is not new combined acceptance.'})
(execution/'retained-input-byte-check.json').write_text(json.dumps(retained,indent=2)+'\n')
stages=[('regfile','scripts/test_regfile_blake2b.py',18,17,3),
        ('finalization','scripts/test_scratchpad_finalization.py',41,19,3)]
commands=[]
unit_argv=[sys.executable,'-B','-m','unittest','discover','-s','tests','-v']
started=time.monotonic()
print('START existing-and-focused-unit-tests',flush=True)
with (execution/'unit-tests-console.log').open('xb') as stream:
    unit_result=subprocess.run(unit_argv,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT)
commands.append({'label':'existing-and-focused-unit-tests','argv':unit_argv,'returncode':unit_result.returncode,
                 'wall_seconds':time.monotonic()-started})
(execution/'combined-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
assert unit_result.returncode==0,commands[-1]
resource_records.append({'phase':'unit-tests-complete','at_epoch':time.time(),'kernel':resources()})
(execution/'combined-resource-stages.json').write_text(json.dumps(resource_records,indent=2)+'\n')
print('COMPLETE existing-and-focused-unit-tests returncode0',flush=True)
for label,driver,rtl,mapped,synthesis in stages:
    output=execution/('combined-'+label)
    argv=[sys.executable,'-B',driver,'--output',str(output),'--synthesize']
    started=time.monotonic()
    print('START',label,flush=True)
    with (execution/(label+'-console.log')).open('xb') as stream:
        result=subprocess.run(argv,cwd=source,env=env,stdout=stream,stderr=subprocess.STDOUT)
    record={'label':label,'argv':argv,'returncode':result.returncode,'wall_seconds':time.monotonic()-started}
    commands.append(record)
    (execution/'combined-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    resource_records.append({'phase':label+'-complete','at_epoch':time.time(),'kernel':resources()})
    (execution/'combined-resource-stages.json').write_text(json.dumps(resource_records,indent=2)+'\n')
    assert result.returncode==0,record
    summary=json.loads((output/'summary.json').read_text())
    assert summary['status']=='pass',summary
    # Exact count fields are retained in each native driver's complete summary;
    # the post-run evidence comparison verifies them without relabeling skips.
    record['expected_scope']={'rtl':rtl,'mapped':mapped,'actual_new_stage_synthesis':synthesis}
    record['summary_sha256']=hashlib.sha256((output/'summary.json').read_bytes()).hexdigest()
    (execution/'combined-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    print('COMPLETE',label,'returncode0',flush=True)
remaining={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ['scripts/test_regfile_blake2b.py','scripts/test_scratchpad_finalization.py']}
(execution/'combined-driver-postcheck.json').write_text(json.dumps(remaining,indent=2)+'\n')
print('Both affected regression commands completed; independent scientific acceptance remains required.',flush=True)
