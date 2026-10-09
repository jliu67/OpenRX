#!/usr/bin/python3
"""Read-only metadata/integrity recheck after the independently accepted guest.

No input rehash or scientific rerun: the accepted checker already verified those.
Adds an explicit final check of the exact earlier live cgroup namespace.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

R = Path('$OPENRX_LOCAL_ROOT')
E = R / 'migrations/20261009'
ID = '20261009T193937Z-576aa858c033'
D = R / 'executions' / ID
REVIEW = E / 'independent-runtime-review-v1/independent-runtime-review.json'
REVIEW_SHA = '12db13426bddda29b7857f423e52fca0b87842c3225d81b2ec2cb3f793170bae'
LIVE = E / 'runtime-live-production-observation-20261009T194045375434Z.json'
LIVE_SHA = '625e316aa9eb5a732d3d265f28597acfa95ab6740891547ff109f97e624a078e'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def binding(path):
    data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}

def require(value,message):
    if not value: raise ValueError(message)

def encode(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()

def main():
    require(binding(REVIEW)['sha256']==REVIEW_SHA,'Accepted checker receipt changed')
    require(binding(LIVE)['sha256']==LIVE_SHA,'Original live cgroup observation changed')
    review=json.loads(REVIEW.read_bytes());live=json.loads(LIVE.read_bytes())
    require(review['execution_id']==ID and review['independent_review_accepted'] is True and
            review['activation_authorized'] is False and len(review['checks_completed'])==9 and
            all(c['passed'] is True for c in review['checks_completed']),'Actual review is not accepted scope')
    receipt=json.loads((D/'receipt.json').read_bytes())
    expected={item['path']:item for item in receipt['artifacts']}
    require(len(expected)==len(receipt['artifacts']),'Duplicate artifact paths')
    actual={}
    ignored={D/'receipt.json',D/'events.lock',D/'finalize.lock'}
    for path in sorted(D.rglob('*')):
        require(not path.is_symlink(),'Execution artifact symlink')
        mode=path.stat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode),'Execution nonregular artifact')
        if stat.S_ISREG(mode) and path not in ignored:actual[str(path)]=binding(path)
    require(actual==expected,'Final retained artifact path set or bytes changed')
    receipt_binding=binding(D/'receipt.json')
    journal=[];previous=None
    for line in (R/'state/execution-receipts.jsonl').read_bytes().splitlines():
        record=json.loads(line);digest=record['sha256']
        unsigned={key:value for key,value in record.items() if key!='sha256'}
        require(record['previous_sha256']==previous and sha(encode(unsigned))==digest,'Receipt journal chain drift')
        journal.append(record);previous=digest
    matches=[record for record in journal if record['execution_id']==ID]
    require(len(matches)==1 and matches[0]['receipt']==receipt_binding,'External receipt binding changed')
    relative=live['retained_cgroup']
    require(relative.startswith('/') and '..' not in Path(relative).parts and
            relative.endswith('/openrx-'+ID+'.service'),'Original cgroup namespace invalid')
    cgroup=Path('/sys/fs/cgroup')/relative.lstrip('/')
    exists=cgroup.exists();pids=[];populated=False
    if exists:
        pids=sorted({int(pid) for p in cgroup.rglob('cgroup.procs') for pid in p.read_text().split()})
        populated='populated 1' in (cgroup/'cgroup.events').read_text()
    require(not pids and not populated,'Earlier live cgroup still contains processes')
    query=subprocess.run(['systemctl','--user','show','openrx-'+ID+'.service',
        '--property=LoadState,ActiveState,SubState,ControlGroup'],capture_output=True,text=True)
    properties=dict(line.split('=',1) for line in query.stdout.splitlines() if '=' in line)
    require(query.returncode==0 and properties.get('LoadState') in {'loaded','not-found'} and
            properties.get('ActiveState') in {'inactive','failed'},'Manager is not a known terminal state')
    result={'schema':'openrx.runtime.postreview.integrity.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'execution_id':ID,'read_only_recheck_accepted':True,'independent_review':binding(REVIEW),
        'prior_live_observation':binding(LIVE),'retained_artifacts_verified':len(actual),
        'receipt':receipt_binding,'external_receipt_journal_binding':matches[0],
        'exact_earlier_live_cgroup':{'path':str(cgroup),'exists':exists,'populated':populated,'pids':pids},
        'current_manager':{'query_returncode':query.returncode,**properties},
        'scope':'Additional retained output path/hash and external receipt binding recheck, plus the actual earlier live cgroup namespace now empty or absent. Accepted guest correctness comes from the exact separately pinned independent checker receipt.',
        'not_inferred':'Transient manager defaults are not terminal service-result evidence; no rerun, recovery, stop, state transition, or cutover.',
        'source':binding(Path(__file__).resolve()),'migration_complete':False}
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=E/('actual-runtime-postreview-integrity-'+stamp+'.json')
    data=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    fd=os.open(E,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    print(json.dumps({'path':str(path),'sha256':sha(data),'accepted':True}),flush=True)

if __name__=='__main__':main()
