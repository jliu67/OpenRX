"""Portable retained-DATA reconstruction only; never simulate or run native/RTL."""

import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parent

COUNT = 16384

DATASET_B = 2181038016

INPUT_HEX = '4f70656e525820636f6e6e65637465642070726570617265642064617461736574206c6966656379636c65203230323631303138'

DIGEST = '4778fba5f3af5094a588969c6de78f70aaf54117e8664c2539387d31eaa24bfa'

ORDER_SHA = '8d5ba9941d076bd71ed3c1a7706a75a8d5ff2d4d890e6e9b6baa549bd373f86f'

SOURCE_SHA = '16eb394aa4ca59abbc83364847c965737a3747e5d122651bb4d5c5f1ab3df45f'

HEADER = 'tag,address,image_epoch,item_namespace,item_cycles,core_cycles,executor_cycles,session_launch_extra,stages,retired,muls,instruction_service_extra,cache_service_extra,request_to_first_response'

COLUMNS = ['ordinal','full_external_tag','byte_address','image_epoch','item_namespace',
    'modeled_item_availability_cycles','observed_model_return_progress_cycle']

def need(ok, message):
    if not ok: raise ValueError(message)

def strict(raw):
    def pairs(items):
        d = {}
        for k,v in items:
            need(k not in d,'duplicate JSON key'); d[k] = v
        return d
    def bad(value): raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def location(address,channels=64):
    need(type(address)is int and 0<=address<DATASET_B and address%64==0,'dataset64 address')
    need(type(channels)is int and channels in (1,64),'closed channel configuration')
    line=address//64; channel=line%channels; inside=line//channels
    # Same intra-channel ordering as pinned RoBaRaCoCh: Col,BG,Bank,Row.
    col=inside&127; bg=(inside>>7)&3; bank=(inside>>9)&3; row=inside>>11
    need(row<65536,'rank row bound')
    return channel,bg,bank,row,col*8

def reconstruct(v,channels=64):
    need(type(v)is tuple and len(v)==5 and all(type(x)is int for x in v),'physical fields')
    c,g,b,r,col=v
    need(channels in (1,64) and 0<=c<channels and 0<=g<4 and 0<=b<4
        and 0<=r<65536 and 0<=col<1024 and col%8==0,'physical geometry')
    a=((((r*4+b)*4+g)*128+col//8)*channels+c)*64
    need(a<DATASET_B,'mapped padding is not dataset data')
    return a

def validate_rows(data,native_raw,csv_raw):
    need(data['schema']=='openrx.memory-demand.ordered-dataset-rows.v1'
        and data['columns']==COLUMNS and data['request_edge_or_offered_arrival_inferred']is False
        and data['physical_seconds_or_service_capacity_inferred']is False
        and data['physical_acceptance']is False,'source-order scope only')
    rows=data['rows'];native=native_raw.decode('ascii').splitlines()
    table=list(csv.reader(io.StringIO(csv_raw.decode('ascii'))))
    need(len(rows)==len(native)==COUNT and len(table)==COUNT+1 and ','.join(table[0])==HEADER,'complete ordered/native/csv records')
    h=hashlib.sha256();previous=-1;values={}
    for n,(row,gold,actual) in enumerate(zip(rows,native,table[1:]),1):
        need(type(row)is list and len(row)==7 and all(type(x)is int and 0<=x<2**64 for x in row),'u64 record shape')
        need(row[0]==n and row[1]==65536+n and row[3]==19619 and row[4]==n,'ordered owner/epoch/namespace')
        need(row[5]==53400 and row[6]>previous,'legacy modeled return coordinates');previous=row[6]
        match=re.fullmatch(r'([0-9a-f]{16}) ([0-9a-f]{128})',gold)
        need(match is not None and int(match[1],16)==row[2],'native address order')
        value=hashlib.sha256(bytes.fromhex(match[2])).digest()
        need(row[2] not in values or values[row[2]]==value,'immutable dataset value per address/epoch')
        values[row[2]]=value
        need(len(actual)==14 and all(re.fullmatch(r'[0-9a-f]+',x) for x in actual),'actual csv fields')
        need([int(x,16)for x in actual[:4]]==[row[1],row[2],row[3],row[4]],'retained csv order/ownership')
        need(int(actual[4])==row[5],'legacy availability identity')
        for channels in (1,64):need(reconstruct(location(row[2],channels),channels)==row[2],'mapping roundtrip')
        h.update(struct.pack('<Q',row[2]))
    need(h.hexdigest()==data['address_order_sha256_LE64']==ORDER_SHA,'lossless address order hash')
    return {'records':COUNT,'unique_native_dataset_lines':len(values),'address_order_sha256_LE64':h.hexdigest(),
        'native_values_bound_not_recomputed':True,'program_iteration_labels':'ordinal division only; no readiness/timing inference'}

def causal_gate(fields,identity):
    need(identity==hashlib.sha256(bytes.fromhex(INPUT_HEX)).hexdigest(),'same immutable input for causal joins')
    required={'address_ready_source_event','consumer_ready_source_event','consumer_end_source_event',
        'program_begin_end','two_ahead_owner_and_reuse','causal_work_dependencies'}
    need(required<=set(fields),'missing causal source/dependency evidence; return progress is not readiness')

def periodic_bounds():
    # Fixed periodic hot refresh, not refresh postponement or achieved service.
    active=5200-467
    acts=4*((active+28-1)//28)
    return dict(max_ACT_per_3900ns=acts,
        one_ACT_per64B_Bps=Fraction(acts*64*10**12,5200*750),
        DQ_peak_Bps=Fraction(64*10**12,4*750),
        refresh_only_ceiling_Bps=Fraction(64*10**12,4*750)*Fraction(active,5200))


ORIGINALS={'ordered': {'bytes': 836535, 'sha256': '16eb394aa4ca59abbc83364847c965737a3747e5d122651bb4d5c5f1ab3df45f'}, 'native_items': {'bytes': 2392064, 'sha256': '80abe136ff5f2bb6bbf55317df6d6740668deae3a5d351303a6a14ce194b310c'}, 'item_csv': {'bytes': 1343680, 'sha256': '6a2afdc0dfbe7d07dff6566548b1942ae27476141bd62aae2a193e848e3b5691'}, 'native_canonical': {'bytes': 318, 'sha256': 'd32f1c7be4cfa63c952f93b420c874c1b5049f8deaa1942826fb7b09c2ad2fb9'}, 'native_summary': {'bytes': 530, 'sha256': '42a9e5fcfee220dd9b3bd946d64e3bef986519aed1a002f3a13dc71a10f68ef6'}, 'native_digest': {'bytes': 65, 'sha256': '6f1e7caab64b6c7665a41ccb023b4c17b5af6802a3acfab6225b2c0c2586e447'}}


def relative_read(pin,base=ROOT):
    need(set(pin)=={'path','bytes','sha256'} and type(pin['path'])is str,'closed relative role pin')
    relative=Path(pin['path'])
    need(not relative.is_absolute() and all(x not in ('..','.')for x in relative.parts),'relative role path')
    path=(base/relative).resolve()
    need(path.is_relative_to(base) and type(pin['bytes'])is int and 0<=pin['bytes']<=3*1048576
        and path.stat().st_size==pin['bytes'],'bounded contained role')
    raw=path.read_bytes()
    need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'public role integrity')
    return raw


def decode(records,t):
    need(type(records)is bytes and len(records)==COUNT*80,'exact uncompressed80B record file')
    need(t['schema']=='openrx.dataset72.lossless-template.v1' and t['record_format']=='<QQ64s'
        and t['record_bytes']==80 and t['records']==COUNT and t['ordinal_start']==1
        and t['tag_base']==65536 and t['epoch']==19619 and t['item_availability_legacy']==53400,'fixed lossless template')
    need(','.join(t['csv_header'])==HEADER and type(t['csv_tail'])is list
        and len(t['csv_tail'])==10 and all(type(x)is str and re.fullmatch(r'[0-9]+',x)for x in t['csv_tail']),'exact csv template')
    rows=[];native=[];csv_rows=[HEADER+'\n']
    for n,(address,legacy_return,value)in enumerate(struct.iter_unpack('<QQ64s',records),1):
        location(address)
        rows.append([n,65536+n,address,19619,n,53400,legacy_return])
        native.append(f'{address:016x} {value.hex()}\n')
        csv_rows.append(f'{65536+n:08x},{address:016x},4ca3,{n:08x},'+','.join(t['csv_tail'])+'\n')
    ordered=dict(t['ordered_metadata']);need('rows'not in ordered,'row fields have one lossless source');ordered['rows']=rows
    originals=dict(ordered=(json.dumps(ordered,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode(),
        native_items=''.join(native).encode('ascii'),item_csv=''.join(csv_rows).encode('ascii'))
    for key in ('native_canonical','native_summary','native_digest'):
        need(type(t[key+'_raw'])is str and len(t[key+'_raw'])<4096,'small original identity representation')
        originals[key]=t[key+'_raw'].encode('ascii')
    for key,raw in originals.items():
        need(len(raw)==ORIGINALS[key]['bytes'] and hashlib.sha256(raw).hexdigest()==ORIGINALS[key]['sha256'],
            'lossless original identity: '+key)
    return originals


def identity_check(i,originals,accepted):
    canonical=strict(originals['native_canonical']);native=strict(originals['native_summary'])
    need(i['input_hex']==canonical['input_hex']==INPUT_HEX and i['cache_key']==canonical['cache_key']=='test key 000','historical52B identity')
    need(canonical['canonical_randomx_calculate_hash_verified']is True
        and i['native_canonical_verified']is True and i['final_digest_hex']==originals['native_digest'].decode().strip()==DIGEST,'canonical digest identity')
    need(type(i['v2'])is int and i['v2']==native['v2']==1 and i['programs']==native['programs']==8
        and i['iterations']==native['iterations_per_program']==2048,'one full native v2 input')
    need(i['source_tree']==accepted['accepted_source']['public_tree']=='cb3e0615f9df861a081ba2cbb1d47c65603b84cd'
        and i['accepted_public_source']==accepted['accepted_source']['public_head']=='e8277c63504ef035bb82791263b6842c0cc51f51','existing public accepted source binding')
    need(i['raw_runner_status']=='PROCESS_EXITED' and i['raw_scientific_acceptance']=='unverified'
        and i['independent_outcome']=='accepted_full_hardware_dataset_functional_hash'
        and i['full_hash_functionally_accepted']is True and i['physical_acceptance']is False,'preserve original independent scope and raw flags')


def intervals(first_offer,last_usable,last_credit,observation_start,observation_end,payload_B):
    # DATA arithmetic only; caller must supply a separately qualified event ledger.
    need(all(type(v)is int for v in (first_offer,last_usable,last_credit,observation_start,observation_end,payload_B)),'integer interval coordinates')
    need(0<=observation_start<=first_offer<last_usable<=last_credit<=observation_end
        and payload_B>0,'ordered active/padded observation')
    return dict(active_ticks=last_credit-first_offer,padded_observation_ticks=observation_end-observation_start,
        idle_padding_ticks=(observation_end-observation_start)-(last_credit-first_offer),
        active_payload_B_per_tick=Fraction(payload_B,last_credit-first_offer),
        padded_duty_average_B_per_tick=Fraction(payload_B,observation_end-observation_start),
        sustainable_service_qualified=False)


def close(manifest_raw=None):
    m=strict((ROOT/'INPUTS.json').read_bytes()if manifest_raw is None else manifest_raw)
    need(m['schema']=='openrx.dataset72.portable-inputs.v1' and set(m['files'])=={'records','templates','identity','CONTRACT'},'closed portable roles')
    need({k:{a:b for a,b in v.items()if a!='representation'}for k,v in m['originals'].items()}==ORIGINALS,'original hashes cannot be rebaselined')
    need(m['causal_ready']is False and all(m[k]is None for k in ['full_hash_residence_cycles','measured_service_Bps','read_energy_pJ','write_energy_pJ']),'unknown service/energy remains unknown')
    public={k:relative_read(v)for k,v in m['files'].items()}
    originals=decode(public['records'],strict(public['templates']))
    need(set(m['repository_sources'])=={'accepted_summary'},'single reused public summary')
    pin=m['repository_sources']['accepted_summary'];need(pin['path']=='docs/status-evidence-20261020.json','historical public summary role')
    accepted=strict(relative_read(pin,ROOT.parents[1]));identity_check(strict(public['identity']),originals,accepted)
    report=validate_rows(strict(originals['ordered']),originals['native_items'],originals['item_csv'])
    contract=strict(public['CONTRACT']);b=periodic_bounds()
    need(contract['status']=='SOURCE_CLOSURE_ONLY_NO_SERVICE_SIMULATION'
        and contract['reference_corrections']['periodic_max_ACT_per_3900ns']==b['max_ACT_per_3900ns']==680,'correct conservative periodic bound')
    threshold=(1-Fraction(64)*b['one_ACT_per64B_Bps']/Fraction(COUNT*64*1000000))*100
    need(abs(contract['reference_corrections']['conservative_activation_threshold_percent']-float(threshold))<1e-12,'31.891percent conditional activation threshold')
    need(contract['experiments']['causal']['status']=='BLOCKED_NOT_RUNNABLE'
        and contract['measurements']['new_simulations']==contract['measurements']['new_native_runs']==0,'source-only blocked scope')
    need(contract['intervals']['active_demand']['start']!=contract['intervals']['observation']['start']
        and 'idle observation'in contract['intervals']['observation']['meaning'],'do not call idle padding loaded service')
    report.update(status='VERIFIED_LOSSLESS_RETAINED_DATA_NOT_A_SERVICE_RUN',input_bytes=52,input_hex=INPUT_HEX,
        input_sha256=hashlib.sha256(bytes.fromhex(INPUT_HEX)).hexdigest(),canonical_digest=DIGEST,
        reconstructed_originals=ORIGINALS,causal_ready=False,new_simulations=0,full_hash_residence_cycles=None,
        measured_service_Bps=None,energy_per_access_pJ=None,physical_acceptance=False,
        conservative_periodic_ACT_per3900ns=680,conditional_no_fresh_ACT_threshold_percent=float(threshold),
        full_causal_optimistic_RD_only_floor_DDR_CK=188416,prior_window_cap_DDR_CK=32768,
        limits='One historical52B input,not population. Source order and legacy return coordinates do not supply readiness or a hardware schedule. Padded observation is not demand-active sustainable service. Full upstream metadata are explicitly selected/sanitized projections,not claimed byte-exact originals.')
    return report


if __name__=='__main__':print(json.dumps(close(),sort_keys=True))
