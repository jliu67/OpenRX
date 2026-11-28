"""Matched retained-count sensitivity; no simulator, new trace or physical calibration."""
import hashlib,json,math
from pathlib import Path

R=Path(__file__).resolve().parent;B=R.parent;T=B.parent
H=1000000;GIB=2**30;F=2000000000;LOCAL_BUDGET=8*GIB
PINS={'evidence/capacity66/validated.json': 'fa39ea638b6e63c51e36e2cd4d7d075906eac820fa17ee085c3438f8815c695e', 'evidence/memory58/reconciliation.json': '9131353959ba717799e9c9d1970dcd717d797b0a8006634f0b0a28dd6fa86e67', 'evidence/hbm2/organization.json': '3ce1c221cd1e61cf0971b670a56a81180fdd3f305d74ec10b175a2cfaa5597e7', 'evidence/hbm2/timing.json': 'b5c52430905b1ee43e2d05dfda5365ceb1d351b5f6d73fbf9832ef838736a172', 'evidence/hbm2/power.json': '6e4093401b256fce9c503a87fce17cb48b00cf8e38dac17abe8c41cc0bde45f0', 'evidence/service39/result.json': '063bb3db75d9d8c4becb76d82b304be877e9a960ae50d0c1b0262b6de22c09ac', 'evidence/service39/early-local.json': '0d03409f5ba1f11f00ccb5a50b7dd4314ee8eca47f5b056ccccb1e819d71b151', 'evidence/service39/later-tiered.json': '724924655d2c2587c2ce88f72535c28ae98638d192fcad5f6e9f12c8bd09fcf8', 'reference/service39-shared.py': 'c2e1ddabc437c32b1a4698fbdd423ab918c594bae7efcae894eda0c9fd845367'}
REPORT=B/'evidence/model-floor-rows.json'
REPORT_SHA='255a5e31ae851bfb210f9fc91b320eb2dc26d8752207c593ff0761b182a8fb38'

def require(v,msg):
    if not v:raise ValueError(msg)

def read(p,digest):
    raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==digest,'source drift: '+str(p))
    return json.loads(raw)if p.suffix=='.json'else raw.decode('utf-8')

def credits(rate,latency_ns):
    require(rate>=0 and latency_ns>=0,'nonnegative rate/latency')
    return math.ceil(rate*latency_ns/1e9)

def provision(floor_cycles,residence,contexts,cap,macro,rx,tx,frequency=F):
    require(all(type(x)is int and x>0 for x in (floor_cycles,residence,contexts,cap,frequency)),'positive integer point')
    # Fixed resources/engine: paid compute floor plus one16B port for each
    # local macro, external capture and external launch. No zero-cost pooling.
    engines=max(math.ceil(H*floor_cycles/frequency),math.ceil(H*residence/(frequency*contexts)),
                math.ceil(H*macro/frequency),math.ceil(H*rx/frequency),math.ceil(H*tx/frequency))
    states=engines*contexts
    return dict(engines=engines,provisioned_contexts=states,local_data_B=states*cap,
        backing_private_image_B=states*(2097152-cap),dataset_shared_B=2181038016,
        local_data_fits8GiB=states*cap<=LOCAL_BUDGET,
        assumed_dataset_credits=2*states,assumed_backing_child_credits=2*states,
        declared_return_storage_B=4*states*96,
        local_data_plus_declared_returns_fit8GiB=states*(cap+4*96)<=LOCAL_BUDGET,
        macro_port_utilization_floor=H*macro/(engines*frequency),
        external_capture_port_utilization_floor=H*rx/(engines*frequency),
        external_launch_port_utilization_floor=H*tx/(engines*frequency))

def rounded_envelope(cap):
    # Rounded design rates intentionally remain distinct from exact per-nonce classes.
    bandwidth={1048576:10.80e12,1572864:5.72e12}[cap];rate=bandwidth/64
    return dict(capacity_B=cap,required_payload_Bps=bandwidth,required_transactions64_per_s=rate,
        external64_nJ_ceiling_at250W=250/rate*1e9,external64_nJ_ceiling_at1250W=1250/rate*1e9,
        HBM2_1200MT_DQ_wire_ceiling_Bps=153.6e9,
        stacks_at_assumed_payload_efficiency=[dict(assumed_efficiency=e,minimum_stacks=math.ceil(bandwidth/(153.6e9*e)))for e in (1,.8,.5)],
        data_only_contexts_at8GiB=LOCAL_BUDGET//cap,
        full4context_engines_at8GiB=LOCAL_BUDGET//(4*cap),
        data_only_residence_ceiling_at2GHz=(LOCAL_BUDGET//cap)*2000,
        full4context_engine_residence_ceiling_at2GHz=(LOCAL_BUDGET//(4*cap))*8000)

def build():
    bound={name:read(B/name,digest)for name,digest in PINS.items()};old=read(REPORT,REPORT_SHA)
    refs=bound['evidence/capacity66/validated.json']['inputs'];rows=[]
    ignore={'SP16_front','bank_balanced_SP','finite_SP_credit','receiver16_grant','return_grant'}
    for ref in refs:
        for p in ref['policies']:
            if p['capacity_B']not in (1048576,1572864):continue
            cap=p['capacity_B'];r=p['backing_read64']+p['backing_RMW_extra_read64'];w=p['backing_write64']
            macro=p['local_read16']+p['local_write16'];rx=4*(16384+r);tx=4*w
            rates=dict(dataset64=H*16384,backing_read64_with_RMW=H*r,backing_write64=H*w)
            cases=[]
            for arch in ('B','C'):
                prior=next(x for x in old['rows']if x['architecture']==arch and x['nonce']==ref['nonce']and x['scenario']=='optimistic')
                kept={k:v for k,v in prior['resource_floors_cycles'].items()if k not in ignore}
                floor=max(kept.values());ctx=1 if arch=='B'else 4
                for residence in (8000000,12000000):
                    point=provision(floor,residence,ctx,cap,macro,rx,tx)
                    for credit_key,rate_key in [('assumed_dataset_credits','dataset64'),('assumed_backing_child_credits',None)]:
                        rate=rates[rate_key]if rate_key else rates['backing_read64_with_RMW']+rates['backing_write64']
                        point['mean_latency_ceiling_ns_'+('dataset'if rate_key else'backing_read_and_writeack')]=point[credit_key]/rate*1e9
                    point.update(retained_compute_architecture=arch,contexts_per_engine=ctx,
                        retained_nonmemory_and_baseline_issue_necessary_floor=floor,
                        floor_bottleneck=max(kept,key=kept.get),assumed_stall_inclusive_residence_clocks=residence,
                        engine_count_without_byte_enable=provision(floor,residence,ctx,cap,macro+p['local_no_byte_enable_extra_read16'],rx,tx)['engines'])
                    cases.append(point)
            rows.append(dict(nonce=ref['nonce'],capacity_B=cap,class_rates_per_s=rates,
                macro_read16_per_hash=p['local_read16'],macro_write16_per_hash=p['local_write16'],
                no_byte_enable_extra_macro_read16_per_hash=p['local_no_byte_enable_extra_read16'],
                macro_refill16=0,macro_writeback16=0,macro_tag_metadata16=0,
                receiver_capture16_beats_per_hash=rx,external_launch16_beats_per_hash=tx,
                per_class_credit_sensitivities=[dict(assumed_usable_response_ns=t,
                    dataset_min_outstanding=credits(rates['dataset64'],t),
                    backing_read_min_outstanding=credits(rates['backing_read64_with_RMW'],t),
                    backing_read_and_writeack_min_outstanding=credits(rates['backing_read64_with_RMW']+rates['backing_write64'],t))for t in (50,100,200)],
                provisioning=cases))
    windows=[]
    for name in ('early_causal_local_c2','later_causal_tiered_c2'):
        ledger=bound['evidence/service39/'+('early-local'if name=='early_causal_local_c2'else'later-tiered')+'.json']['memory'];sp=[x['source']for x in ledger if x['source']['space']=='sp']
        windows.append(dict(retained_case=name,actual_native_source_instructions=1538 if name.startswith('early')else 1536,
            selected_program=0 if name.startswith('early')else 1,SP_source_events=len(sp),
            routing_only=[dict(capacity_B=c,external_logical_source_events=sum(x['address']>=c for x in sp),
                external_useful_B=sum(x['size']for x in sp if x['address']>=c))for c in (1048576,1572864)],
            new_policy_cycles=None,new_policy_arrivals=None))
    return dict(schema='openrx.capacity66.conditional-frontier.v1',physical_acceptance=False,
        sources=dict(PINS)|{'evidence/model-floor-rows.json':REPORT_SHA},rounded_design_envelopes=[rounded_envelope(c)for c in (1048576,1572864)],
        exact_source_cases=rows,retained_causal_windows=windows,
        same_residence_energy_break_even=dict(assumed_frequency_Hz=F,assumed_residence_clocks=8000000,minimum_live_contexts=4000,
            extra_local_data_GiB_for1p5MiB=4000*.5/1024,
            rounded_external_transaction_reduction_per_s=79.375e9,
            saved_external_W_per_assumed_nJ_per64B=79.375,
            extra_memory_leakage_and_controller_W_per_GiB_ceiling_per_nJ_per64B=79.375/(4000*.5/1024),
            local_dynamic_extra_formula_W='H*((R1p5-R1)*e_read_pJ+(W1p5-W1)*e_write_pJ+optional(partial1p5-partial1)*e_read_pJ)*1e-12; subtract from saved external W. No assumed macro price.',
            warning='Common residence is a sensitivity only. Different stalls alter engines, contexts, leakage, queues and capacity; compare full provisioned points, not this cancellation alone.'),
        known_physical_reference=dict(technology='HBM2 author1200MT/s config only',DQ_wire_rate_Bps=153.6e9,
            wire_rate_formula='8channels*2PC*64DQ*1.2e9transfers/s/8; not sustainable mixed payload',
            author_model_capacity_B=4294967296,power_source_scope='measurement-derived per-PC current model; not a complete identified-device/PVT/command/PHY contract',
            service_and_energy_qualified=False,source_reconciliation_status=bound['evidence/memory58/reconciliation.json']['status']),
        explicit_unknowns=dict(sustainable_mixed_payload_Bps=None,dataset_usable_response_latency=None,
            backing_read_write_response_latency=None,full_hash_causal_stall_residence=None,
            per_class_energy_J=None,local_macro_PVT_service_energy=None,PHY_controller_cooling_conversion_leakage=None,wall_power_W=None),
        scheduling_scope=['B/C compute units,initiation and dispatch/retire/fetch/base internal issue floors are inherited. Memory-specific old floors are removed and replaced by declared local macro/external capture/external launch port floors. Extra internal metadata/staging/issue work is unknown positive cost, not a complete schedule.',
            'Three finite16B interfaces/engine are assumed separately: local macro1RW,external capture andexternal launch. Shared wiring would require summing demands. Byte-enable local stores are an explicit case; no-byte-enable adds16B RMW reads.',
            'Two dataset credits/context use native two-ahead source ownership. Two backing64B child credits/context are assumed, held until usable read/writeack. Each declared credit charges64B data+32B owner/address storage. RMW parent queues, RF and other state are additional unknown cost.',
            'Service39 remains the only retained finite-window scheduler. It hardcodes256KiB+16KiB cache, unqualified timing, and incomplete command legality. Its cycles cannot be reused as1MiB/1.5MiB results; no existing exact qualified command for this new pair.',
            'Retained dependency windows are program0/1 first2iterations for nonce0/2. Address routing changes are real source evidence; new service arrival times must be recomputed in causal loop, never replay saved issue timestamps. No whole-hash extrapolation.'],
        decision='Retain1MiB versus1.5MiB as a conditional tradeoff, not a selected architecture. Shared C four-context resource point is already excluded at2GHz/8GiB for both capacities by its compute-driven provisioned state floor. Replicated B survives some data-only points but its many engines and all energy remain unqualified.',
        single_next_required_datum='One independently reproducible controller-level calibration record for an identified accessible device/mapping/PVT under the retained windows and declared64B read/write/RMW mix: achieved useful payload,mean usable read/writeack latency and complete energy including controller/PHY/refresh. Source must bind RL/WL,bank/rank/burst mapping,refresh and command legality. This can populate one compatible contract; vendor DQ peak or unjoined IDD data cannot.',
        next_test_if_datum_available='One matched finite-window comparison through existing scheduler, two source windows/nonces and identical controller/FU/port/credit resources; replace only static prefix1MiB versus1.5MiB, no cache. Recompute readiness/feedback,retain exact values/owners/ordered stores and reserve all16B transport/staging beats. New narrow adapter review needed; no command is claimed qualified or launched now.')
