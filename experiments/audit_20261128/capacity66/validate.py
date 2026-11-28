"""Strict parity against accepted locality37 bytes; no producer import/replay."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REFERENCE=ROOT.parent/'evidence/locality37-native.jsonl'
REFERENCE_SHA='650b11ed43be5c293ac4cc79ba477eb09887c06329a918667320672d4c38188b'
PHASES=('init','entry_R','entry_FP','bytecode_read','bytecode_write','tail_R','tail_F','final_scan')
CAPACITIES=(0,16384,262144,524288,1048576,1572864,2097152)
WRITE_PHASES={'init','bytecode_write','tail_R','tail_F'}
PFIELDS={'phase','events','local_read16','local_write16','local_partial_write8',
         'external_read_events','external_write_events','external_read64','external_write64','external_partial_write64'}
LFIELDS={'local_bytes','events','local_events','external_read_events','external_write_events','read_runs64',
         'write_runs64','partial_write_runs64','unmerged_masked_bytes','unmerged_RMW_bytes',
         'adjacent_combined_masked_bytes','adjacent_combined_RMW_bytes'}

def need(value,message):
    if not value:raise ValueError(message)

def integer(n):
    return type(n)is int and 0<=n<2**64

def exact(a,b):
    if type(a)is not type(b):return False
    if type(a)is dict:return set(a)==set(b)and all(exact(a[k],b[k])for k in b)
    if type(a)is list:return len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))
    return a==b

def parse(raw):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate key');out[k]=v
        return out
    return [json.loads(x,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'nonfinite'))for x in raw.splitlines()]

def validate_rows(rows,refs):
    need(len(rows)==3 and exact(rows[-1],dict(kind='completion',requested_inputs=2,completed_inputs=2,bounded_subset=False)),
         'two complete nonce0/2 hashes, no partial success')
    output=[]
    for nonce,row in zip((0,2),rows[:-1]):
        old=refs[nonce];stream=row['memory_service_census']
        need(row['nonce']==nonce and row['canonical_digest_equal']is True,'nonce/canonical identity')
        need('static_capacity66'in stream,'new exact capacity field')
        inherited=copy.deepcopy(row);policies=inherited['memory_service_census'].pop('static_capacity66')
        for k,v in old.items():
            if k!='host_seconds_not_hardware':need(k in inherited and exact(inherited[k],v),'inherited native/policy parity: '+k)
        need(set(inherited)==set(old),'closed root schema')
        need(type(policies)is list and len(policies)==7,'seven exact static policies')
        prior={p['local_bytes']:p for p in stream['static_policies']}
        phase_events={p:sum(v['events']for v in stream['phase_region_RW']if v['phase']==p)for p in PHASES}
        summaries=[]
        for cap,policy in zip(CAPACITIES,policies):
            need(set(policy)=={'local_bytes','logical_policy','phase_counts','refill16','writeback16','tag_metadata16'},'closed policy schema')
            need(type(policy['local_bytes'])is int and policy['local_bytes']==cap,'ordered capacity identity')
            for k in ('refill16','writeback16','tag_metadata16'):need(type(policy[k])is int and policy[k]==0,'no static cache storage traffic')
            logical=policy['logical_policy'];need(set(logical)==LFIELDS and all(integer(v)for v in logical.values()),'strict u64 logical counts')
            need(logical['local_bytes']==cap and logical['events']==stream['events'],'logical event/capacity closure')
            if cap in prior:need(exact(logical,prior[cap]),'independent old-prefix parity')
            phases=policy['phase_counts'];need(type(phases)is list and len(phases)==8,'all lifecycle phases')
            for name,p in zip(PHASES,phases):
                need(set(p)==PFIELDS and p['phase']==name and all(integer(v)for k,v in p.items()if k!='phase'),'strict phase schema')
                need(p['events']==phase_events[name]==p['local_read16']+p['local_write16']+p['external_read_events']+p['external_write_events'],'source event routing closure')
                if name in WRITE_PHASES:
                    need(p['local_read16']==p['external_read_events']==p['external_read64']==0,'write-only phase')
                    need(p['local_partial_write8']==(p['local_write16']if name in {'bytecode_write','tail_R'}else 0),'8B byte-mask accounting')
                else:need(p['local_write16']==p['local_partial_write8']==p['external_write_events']==p['external_write64']==p['external_partial_write64']==0,'read-only phase')
                need(p['external_read64']<=p['external_read_events']and p['external_partial_write64']<=p['external_write64']<=p['external_write_events'],'bounded external coalescing')
            total=lambda key:sum(p[key]for p in phases)
            need(phases[0]['local_write16']==cap//16 and phases[-1]['local_read16']==cap//16,'exact sequential fill/final prefix routing')
            need(total('local_read16')+total('local_write16')==logical['local_events'],'local event closure')
            for ph,lk in [('external_read_events','external_read_events'),('external_write_events','external_write_events'),
                          ('external_read64','read_runs64'),('external_write64','write_runs64'),('external_partial_write64','partial_write_runs64')]:
                need(total(ph)==logical[lk],'phase/logical accounting: '+ph)
            r,w,partial=total('external_read64'),total('external_write64'),total('external_partial_write64')
            need(logical['unmerged_masked_bytes']==64*(logical['external_read_events']+logical['external_write_events'])
                 and logical['unmerged_RMW_bytes']==64*(logical['external_read_events']+2*logical['external_write_events']),'unmerged byte identity')
            need(logical['adjacent_combined_masked_bytes']==64*(r+w)and logical['adjacent_combined_RMW_bytes']==64*(r+w+partial),'64B backing byte identity')
            summaries.append(dict(capacity_B=cap,local_read16=total('local_read16'),local_write16=total('local_write16'),
                local_no_byte_enable_extra_read16=total('local_partial_write8'),dataset_read64=16384,
                backing_read64=r,backing_write64=w,backing_RMW_extra_read64=partial,
                backing_masked_B=64*(r+w),backing_RMW_B=64*(r+w+partial),phase_counts=phases))
        output.append(dict(nonce=nonce,digest_hex=row['digest_hex'],ordered_event_BLAKE2b256=stream['ordered_event_BLAKE2b256'],policies=summaries))
    return dict(schema='openrx.capacity66.validated.v1',canonical_hashes=2,inherited_policy_parity=True,
        inputs=output,physical_acceptance=False,hardware_causal_timing=False,
        macro_interface='one uncombined16B access per local8/16B source access; byte-enable write vs added16B RMW read sensitivity. Static prefix has no cache refill/writeback/tag RAM; comparator, control, data routing energy unpriced.',
        windows='Reuse source-bound trace26 nonce0/2 program0 first two complete iterations; exact retained first_program native state/events reproduced. Source ordering/RF dependencies, not hardware ready/valid or full-hash schedule.')

def validate(path):
    raw=Path(path).read_bytes();need(len(raw)<=131072,'complete capture128KiB')
    old=REFERENCE.read_bytes();need(hashlib.sha256(old).hexdigest()==REFERENCE_SHA,'exact retained source evidence')
    refs={r['nonce']:r for r in parse(old)[:-1]}
    return validate_rows(parse(raw),refs)
