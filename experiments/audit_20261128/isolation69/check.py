"""Verify retained public copies only; never compile, simulate or admit a job."""
import hashlib
import json
from pathlib import Path
from . import analyze

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
EVIDENCE=HERE.parent/'evidence/isolation69'
EMITTED='/[source-path-redacted]/isolation69/tb_compare.v'

def need(ok,message):
    if not ok:raise ValueError(message)

def bound(row,root=ROOT):
    p=(root/row['path']).resolve()
    need(p.is_relative_to(root)and p.stat().st_size==row['bytes']<=1048576,'bounded public source')
    raw=p.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==row['sha256'],'public source integrity')
    return raw

def outcome(status,receipt,prefix):
    need(status['status']==receipt['status']=='FAILED_NO_RETRY'and status['overall_pass']is False
        and status['scientific_retry_allowed']is False and status['physical_acceptance']is False,'failure must remain failure')
    need(receipt['child_rc']==1 and receipt['capture_complete']is True
        and receipt['marker_present_at_receipt']is True
        and receipt['marker_release_eligible_after_receipt']is False,'outer failure/hold unchanged')
    need(status['stages']==[dict(name='compile',capture_complete=True,returncode=0),
        dict(name='simulation',capture_complete=True,returncode=0),
        dict(name='synth-baseline',capture_complete=False,returncode=None),
        dict(name='synth-isolated',status='UNRUN_FIRST_FAILURE_STOP')],'exact partial stage scope')
    f=status['synthesis_failure']
    need(f['original_capture_B']==f['original_capture_cap_B']==262144
        and f['public_capture_B']==len(prefix)and f['baseline_returncode']is None
        and f['isolated_synthesis']=='UNRUN_FIRST_FAILURE_STOP','capture failure,not synthesis completion')
    need(prefix.count(b'Warning: Range [2:1] select out of bounds')==2,'range warnings retained')
    need(prefix[f['public_stat_JSON_start']:].startswith(b'{\n'),'stat prefix position')
    try:json.loads(prefix[f['public_stat_JSON_start']:])
    except json.JSONDecodeError:pass
    else:raise ValueError('retained capture must remain visibly truncated')
    need(receipt['drain']['direct_child_reaped']is True
        and receipt['drain']['scope_descendants_absent']is True,'recorded drain scope')

def activity_claim(claim,activity):
    expected=dict(accepted_pairs=activity['accepted_pairs'],cycles=activity['cycles'],
        native_results=activity['native_result_vectors'],native_flags_oracle=activity['native_flag_oracle'],
        baseline_flags_equivalent=activity['baseline_flags_equivalent'],corners=activity['control_and_special_vectors'],
        records=108,FIRST=activity['diagnostics']['first'],SNAP=activity['diagnostics']['snapshots'],
        GATE=activity['diagnostics']['gates'],ACT=48,isolated_idle_held_binary=0,isolated_idle_held_fourstate=0)
    need({k:v for k,v in claim.items()if k!='scope'}==expected,'published functional claim must match raw collector')

def check():
    proof=json.loads((EVIDENCE/'PROVENANCE.json').read_bytes())
    need(proof['schema']=='openrx.isolation69.public-copy-provenance.v1'
        and proof['sanitized_emitted_bench_path']==EMITTED,'declared sanitized terminal identity')
    need({x['file']for x in proof['members']}=={'simulation.txt','result.json','status.json','synth-baseline-prefix.txt'}
        and len(proof['members'])==4,'closed public evidence set')
    raw={}
    for row in proof['members']:
        p=EVIDENCE/row['file'];data=p.read_bytes()
        need(len(data)==row['bytes']<=1048576 and hashlib.sha256(data).hexdigest()==row['sha256'],'public evidence integrity')
        need(row['representation']!='byte_exact'and len(row['original']['sha256'])==64,'sanitized/projected identity is separate')
        raw[row['file']]=data
    need(proof['source_collector']['original']['sha256']==hashlib.sha256((HERE/'analyze.py').read_bytes()).hexdigest(),'byte-exact actual collector')
    replay=json.loads(bound(proof['source_closure']))
    need(len(replay['source_files'])==16,'compact full HDL/vector/identity/collector closure')
    for row in replay['source_files']:bound(row)
    future=json.loads(bound(proof['future_logging']))
    need(future['status']=='UNREVIEWED_SOURCE_ONLY_NOT_ADMITTED_UNRUN'
        and len(future['changes'])==2,'future logging proposal remains unrun')
    for row in future['changes']:
        need(row['after']==row['before'].replace('tee -o ','tee -q -o ',1),'only scoped stat logging change')
    negative=bound(proof['reused_negative_control'])
    need(hashlib.sha256(negative).hexdigest()=='754a1e856fdf112a73a28c44d126110d2bfa433f1524f18fbeb51b0695fadffa','exact original negative control')
    try:analyze.activity(negative,emitted_bench_path=EMITTED)
    except ValueError:pass
    else:raise ValueError('original failed control cannot pass new collector')
    status=json.loads(raw['status.json']);receipt=json.loads(raw['result.json'])
    outcome(status,receipt,raw['synth-baseline-prefix.txt'])
    activity=analyze.activity(raw['simulation.txt'],emitted_bench_path=EMITTED)
    activity_claim(status['functional_claim'],activity)
    return dict(status='FAILED_NO_RETRY',scoped_simulation=activity,
        generic_comparison=None,physical_acceptance=False,
        scope='Retained DATA validation only; no new scientific execution or admission.')

if __name__=='__main__':
    r=check();print(json.dumps(dict(status=r['status'],accepted=r['scoped_simulation']['accepted_pairs'],
        cycles=r['scoped_simulation']['cycles'],generic_comparison=None,physical_acceptance=False),sort_keys=True))
