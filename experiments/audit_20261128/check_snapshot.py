"""Ordinary read-only publication checks; never launch a scientific workload."""
from pathlib import Path
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SNAPSHOT_COMMIT='20e6d4881a3a130bf9f9ba0ee7eecdba584fedad'
SNAPSHOT_TREE='9e73d07d48c9b87c0cc65122dcd9410daafb8111'
MANIFEST_PATH='experiments/audit_20261128/PROVENANCE.json'
MANIFEST_BYTES=35502
MANIFEST_SHA256='d246c6fe590cfac8b44eb5e401f42bfbc9cdbb0fbf5f52650d57595c4c19e1c5'
BLOB_CAP=1048576

def require(ok,message):
    if not ok:raise ValueError(message)

def git_bytes(*args):
    try:
        return subprocess.run(['git','--no-replace-objects','-C',str(ROOT),*args],
            check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10).stdout
    except (OSError,subprocess.SubprocessError) as e:
        raise ValueError('Historical snapshot unavailable; fetch the pinned public audit commit: '
            'git fetch --no-tags --depth=1 origin '+SNAPSHOT_COMMIT) from e

def historical_bytes(relative,size):
    require(type(relative)is str and not relative.startswith('/')
        and all(p not in ('','..','.')for p in relative.split('/')),'historical repository path')
    require(type(size)is int and 0<=size<=BLOB_CAP,'bounded historical blob')
    obj=SNAPSHOT_COMMIT+':'+relative
    require(git_bytes('cat-file','-s',obj).strip()==str(size).encode(),'historical blob length: '+relative)
    raw=git_bytes('cat-file','blob',obj)
    require(len(raw)==size,'historical blob read length: '+relative)
    return raw

def decode_window(data):
    require(data['schema']=='openrx.exact-token-pool.v1','token schema')
    pool=data['tokens'];rows=data['rows']
    require(len(pool)<32768 and len(rows)<4096,'bounded pool')
    require(all(type(s)is str and len(s)<=8192 and ' 'not in s and '\n'not in s for s in pool),'exact ASCII tokens')
    require(all(type(i)is int and 0<=i<len(pool)for row in rows for i in row),'closed token index')
    raw=(''.join(' '.join(pool[i]for i in row)+'\n'for row in rows)).encode('ascii')
    require(len(raw)==data['original_bytes']<1048576 and hashlib.sha256(raw).hexdigest()==data['original_sha256'],'lossless trace identity')
    return raw

def verify_manifest():
    require(git_bytes('rev-parse',SNAPSHOT_COMMIT+'^{tree}').strip().decode()==SNAPSHOT_TREE,'historical tree identity')
    manifest_raw=historical_bytes(MANIFEST_PATH,MANIFEST_BYTES)
    require(hashlib.sha256(manifest_raw).hexdigest()==MANIFEST_SHA256,'historical manifest identity')
    require((HERE/'PROVENANCE.json').read_bytes()==manifest_raw,'immutable local manifest')
    manifest=json.loads(manifest_raw)
    require(len({r['path']for r in manifest['files']})==len(manifest['files']),'unique publication paths')
    for row in manifest['files']:
        path=(ROOT/row['path']).resolve();require(path.is_relative_to(ROOT),'repository source path')
        raw=historical_bytes(row['path'],row['bytes'])
        require(hashlib.sha256(raw).hexdigest()==row['sha256'],'historical public-copy hash: '+row['path'])
        # Retained payloads stay immutable in the live checkout too. The checker
        # is current code; its original bytes were checked above, not rebased.
        if row['path'].startswith('experiments/audit_20261128/')and path!=HERE/'check_snapshot.py':
            require(path.read_bytes()==raw,'retained public-copy hash: '+row['path'])
        if row['representation']=='byte_exact':
            require(row['original_sha256']==row['sha256']and row['original_bytes']==row['bytes'],'exact-copy declaration')
    return len(manifest['files'])

def check():
    from tools.architecture import machine
    from experiments.audit_20261128.capacity66 import validate,frontier
    n=verify_manifest()
    fixture=json.loads((ROOT/'tools/architecture/fixtures/machine-baseline.json').read_bytes())
    machine.verify_sources(fixture);report=machine.evaluate(fixture)
    require(len(report['rows'])==48 and all(r['cost']['wall']['wall_power_w']is None and not r['demonstrated_hardware_feasibility']for r in report['rows']),'unknown power stays unknown')
    capacity=validate.validate(HERE/'evidence/capacity66/native.jsonl')
    require(capacity['canonical_hashes']==2 and capacity['inherited_policy_parity'],'retained capacity parity')
    published=json.loads((HERE/'evidence/capacity66/validated.json').read_bytes())
    projected=[{k:([{a:b for a,b in p.items()if a!='phase_counts'}for p in v]if k=='policies'else v)
                for k,v in row.items()}for row in capacity['inputs']]
    require(published['inputs']==projected,'published capacity totals match exact retained stream')
    conditional=frontier.build();require(len(conditional['exact_source_cases'])==4 and not conditional['physical_acceptance'],'conditional arithmetic scope')
    traces=[decode_window(json.loads(p.read_bytes()))for p in sorted((HERE/'evidence/windows').glob('*.json'))]
    require(len(traces)==2,'two retained source windows')
    failure=json.loads((HERE/'evidence/isolation68/result.json').read_bytes())
    require(failure['status']=='FAILED_NO_RETRY','original failure status')
    activity={}
    for line in (HERE/'evidence/isolation68/simulation.txt').read_text().splitlines():
        m=re.fullmatch(r'ACT id=(\d+) phase=(\d+) binary=(\d+) fourstate=(\d+)',line)
        if m:
            i,p,b,x=map(int,m.groups());require((i,p)not in activity,'unique actual activity row');activity[i,p]=(b,x)
    require(len(activity)==48,'complete actual activity')
    require(sum(activity[i,1][1]for i in range(8,16))==88,'retained rejection cause')
    require(all(activity[i,p][0]==0 for i in range(8,16)for p in (1,3)),'partial binary observation')
    correction=json.loads((HERE/'evidence/isolation68/correction-source-only.json').read_bytes())
    require(correction['status']=='SOURCE_ONLY_UNRUN_NO_ADMISSION','unrun correction remains unrun')
    recovery=json.loads((HERE/'evidence/reconciliation/result.json').read_bytes())
    require(recovery['status']=='EXACT_OWNED_MARKER_RECONCILED_NO_WORKLOAD'and recovery['workloads_launched']==0 and recovery['original_failure_status_unchanged'],'administrative recovery only')
    require(recovery['marker_absent_verified_under_original_lock']and recovery['parent_directory_fsynced'],'recorded exact recovery')
    require(recovery['source']['sha256']==recovery['executed_source_archive']['sha256'],'recorded executed-source archive identity')
    journal=[json.loads(line)for line in (HERE/'evidence/reconciliation/journal.jsonl').read_text().splitlines()]
    require(len(journal)==7 and journal[-1]['stage']=='RESULT_DURABLE_UNDER_ORIGINAL_LOCK','recorded recovery stages')
    return dict(public_files_verified=n,model_rows=48,wall_powers_known=0,retained_capacity_hashes=2,
        exact_window_bytes=[len(t)for t in traces],failed_proxy_preserved=True,recovery_workloads=0,
        scope='Publication integrity/arithmetic/cross-record checks only. No native,RTL,scheduler,synthesis,systemd orreconciliation execution.')

if __name__=='__main__':print(json.dumps(check(),sort_keys=True))
