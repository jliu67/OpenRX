"""Retained static-prefix traffic contracts; arithmetic only, never a scheduler."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

CAPACITIES = (1048576, 1572864, 2097152)
FULL = 'full_hash_source_order'
WINDOW = 'finite_native_window'
ADJACENT = 'adjacent_source64'
UNMERGED = 'unmerged'
CHILD = 'transaction64_child'
PARENT = 'logical_request_parent'
DATASET = 'dataset_request64'
MACRO = 'macro16_operation'
PINS = {
    'capacity66_validated': ('capacity66/validated.json', 'fa39ea638b6e63c51e36e2cd4d7d075906eac820fa17ee085c3438f8815c695e'),
    'capacity66_native': ('capacity66/native.jsonl', 'ecacfe9843d30c0555fa77b25c512d27da507c03ed40b9081410b3cfe5fb87f1'),
    'service67': ('service67/result.json', '34cb4986edefd18138271b6a740cb657793e85d5410a52eb0e837b13f7de09f1'),
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def binding(capacity, traffic_class, *, scope=FULL, coalescing=ADJACENT, credit_unit=CHILD):
    return dict(capacity_B=capacity, traffic_class=traffic_class, source_scope=scope,
                coalescing=coalescing, credit_unit=credit_unit,
                local_policy='static_prefix_masked16_no_cache', backing_store='partial_RMW64')


def require_join(counts, service):
    need(type(counts) is dict and type(service) is dict and counts == service
         and all(type(v) is type(service[k]) for k, v in counts.items()), 'incompatible traffic/credit contract join')


def project_case(native, policy):
    cap = policy['capacity_B']
    census = native['memory_service_census']
    raw = next(x for x in census['static_capacity66'] if x['local_bytes'] == cap)
    phases = copy.deepcopy(raw['phase_counts'])
    total = lambda key: sum(x[key] for x in phases)
    need(native['canonical_digest_equal'], 'capacity canonical digest')
    need(total('local_read16') == policy['local_read16'] and total('local_write16') == policy['local_write16'], 'macro projection')
    need(total('external_read64') == policy['backing_read64'] and total('external_write64') == policy['backing_write64']
         and total('external_partial_write64') == policy['backing_RMW_extra_read64'], 'backing projection')
    need(raw['refill16'] == raw['writeback16'] == raw['tag_metadata16'] == 0, 'static placement has no hidden cache traffic')
    regions = census['phase_region_RW']
    result = dict(nonce=native['nonce'], digest_hex=native['digest_hex'],
        input_sha256=hashlib.sha256(bytes.fromhex(native['input_hex'])).hexdigest(),
        ordered_event_BLAKE2b256=census['ordered_event_BLAKE2b256'],
        front_read16=sum(x['events'] for x in regions if not x['write']),
        front_write16=sum(x['events'] for x in regions if x['write']),
        useful_B=sum(x['useful_bytes'] for x in regions),
        local_macro_read16=policy['local_read16'], local_macro_write16=policy['local_write16'],
        local_no_byte_enable_extra_read16=policy['local_no_byte_enable_extra_read16'],
        local_refill16=0, local_writeback16=0, local_tag_metadata16=0,
        backing_read64=policy['backing_read64'] + policy['backing_RMW_extra_read64'],
        backing_write64=policy['backing_write64'], dataset_read64=policy['dataset_read64'], phases=phases)
    need(result['front_read16'] + result['front_write16'] == census['events'] == total('events'), 'whole lifecycle front count')
    need(64 * (result['backing_read64'] + result['backing_write64']) == policy['backing_RMW_B'], 'RMW byte projection')
    return result


def policies(native_rows, validated):
    need(len(native_rows) == 3 and native_rows[-1] == dict(kind='completion', requested_inputs=2, completed_inputs=2, bounded_subset=False), 'exact retained two-input completion footer')
    native = {x['nonce']: x for x in native_rows[:-1]}
    need(set(native) == {0, 2} and len(validated['inputs']) == 2, 'exact retained capacity input set')
    result = {}
    for cap in CAPACITIES:
        ident = f'static_prefix_{cap}_adjacent_RMW64'
        cases = []
        for row in validated['inputs']:
            n = native[row['nonce']]
            need(row['digest_hex'] == n['digest_hex'] and row['ordered_event_BLAKE2b256'] == n['memory_service_census']['ordered_event_BLAKE2b256'], 'capacity source identity')
            p = next(p for p in row['policies'] if p['capacity_B'] == cap)
            cases.append(project_case(n, p))
        result[ident] = dict(id=ident, capacity_B=cap, source_ids=['capacity66_native', 'capacity66_validated'],
            traffic_contract=binding(cap, 'scratchpad_backing'), cases=cases)
    return result


def validate_policy(policy, samples):
    need(set(policy) == {'id', 'capacity_B', 'source_ids', 'traffic_contract', 'cases'}, 'policy fields')
    need(type(policy['capacity_B']) is int and policy['capacity_B'] in CAPACITIES, 'supported explicit static capacity')
    require_join(binding(policy['capacity_B'], 'scratchpad_backing'), policy['traffic_contract'])
    need(len({x['nonce'] for x in policy['cases']}) == len(policy['cases']), 'unique policy nonce')
    expected_fields = {'nonce', 'digest_hex', 'input_sha256', 'ordered_event_BLAKE2b256', 'phases',
        'front_read16', 'front_write16', 'useful_B', 'local_macro_read16', 'local_macro_write16',
        'local_no_byte_enable_extra_read16', 'local_refill16', 'local_writeback16', 'local_tag_metadata16',
        'backing_read64', 'backing_write64', 'dataset_read64'}
    for c in policy['cases']:
        need(set(c) == expected_fields, 'policy count fields')
        for key in expected_fields - {'digest_hex', 'input_sha256', 'ordered_event_BLAKE2b256', 'phases'}:
            need(type(c[key]) is int and c[key] >= 0, 'nonnegative integer policy counts')
        for key in ('digest_hex', 'input_sha256', 'ordered_event_BLAKE2b256'):
            need(type(c[key]) is str and len(c[key]) == 64 and all(x in '0123456789abcdef' for x in c[key]), 'policy fingerprint')
        need(c['dataset_read64'] == 16384 and c['local_refill16'] == c['local_writeback16'] == c['local_tag_metadata16'] == 0, 'explicit static/dataset traffic')
    for s in samples:
        c = next((c for c in policy['cases'] if c['nonce'] == s['nonce']), None)
        need(c is not None and c['digest_hex'] == s['digest_hex'] and c['input_sha256'] == s['input_sha256'], 'policy/sample immutable identity')


def load_evidence(repo):
    root = Path(repo) / 'experiments/audit_20261128/evidence'
    data, sources = {}, {}
    for key, (name, digest) in PINS.items():
        path = root / name; raw = path.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == digest, 'retained policy source drift')
        data[key] = [json.loads(x) for x in raw.splitlines()] if path.suffix == '.jsonl' else json.loads(raw)
        sources[key] = dict(path=str(path), bytes=len(raw), sha256=digest, kind='retained_observation',
                            scope=FULL if key != 'service67' else WINDOW)
    return data, sources


def comparison_inputs(repo, baseline):
    """One retained B-resource point at2GHz;100ns child service is an assumption."""
    data, sources = load_evidence(repo)
    d = copy.deepcopy(baseline)
    d['sources'].update(sources)
    d['samples'] = [s for s in d['samples'] if s['nonce'] in (0, 2)]
    d['scenarios'] = [s for s in d['scenarios'] if s['frequency_Hz'] == 2e9][:1]
    d['memory_policies'] = policies(data['capacity66_native'], data['capacity66_validated'])
    base = next(a for a in d['architectures'] if a['id'] == 'B')
    d['architectures'] = []
    for ident, policy in d['memory_policies'].items():
        cap = policy['capacity_B']; a = copy.deepcopy(base)
        a.update(id='B_' + str(cap), placement='static_prefix', memory_policy_id=ident, physical_id=ident,
            credit_contracts={name:dict(unit=unit, per_context=2, storage_B_per_credit=96, qualification='assumed')
                for name, unit in (('dataset', DATASET), ('scratchpad_backing', CHILD))})
        d['architectures'].append(a)
        p = copy.deepcopy(d['physical']['unknown'])
        p['credit_storage_cost'] = dict(area_mm2_per_B=None, leakage_W_per_B=None,
            event_energy_pJ=None, source_id='protocol_assumptions')
        for name, cls, unit in (('private_memory', 'private_macro', MACRO), ('external_memory', 'mixed_external', CHILD)):
            p[name]['traffic_binding'] = binding(cap, cls, credit_unit=unit)
        p['external_classes'] = {}
        for name, unit in (('dataset', DATASET), ('scratchpad_backing', CHILD)):
            m = copy.deepcopy(p['external_memory']); m['traffic_binding'] = binding(cap, name, credit_unit=unit)
            m.update(response_latency_s=100e-9, response_interpretation='fixed_service', qualification='assumed')
            m['parameter_sources']['response_latency_s'] = 'protocol_assumptions'
            p['external_classes'][name] = m
        d['physical'][ident] = p
    # Unused legacy physical profile stays unchanged; no window becomes a witness.
    return d, data['service67']


def window_comparators(result):
    """Typed finite-window summaries only, never joined to full-hash residence."""
    return [dict(window=x['window'], capacity_B=x['capacity_B'], service_ns_assumed=x['assumed_service_ack_ns'],
        cycles_including_drain=x['cycles_including_drain'], context_completion_cycles=x['context_completion_cycles'],
        local_read16=x['local_physical16B_reads'], local_write16=x['local_physical16B_writes'],
        external_classes=x['external_classes'], full_hash_residence_cycles=None,
        traffic_contract=binding(x['capacity_B'], 'scratchpad_backing', scope=WINDOW, coalescing=UNMERGED, credit_unit=PARENT))
        for x in result['cases'] if x['assumed_service_ack_ns'] == 100]


def main(argv=None):
    """One bounded portable DATA report over published retained evidence."""
    import argparse
    from . import machine as M
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    root = Path('.')  # invoke from the repository root, like the existing model
    baseline = M.strict_json((root / 'tools/architecture/fixtures/machine-baseline.json').read_bytes())
    baseline_rows = M.evaluate(baseline)['rows']
    baseline_hash = hashlib.sha256(json.dumps(baseline_rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    need(len(baseline_rows) == 48 and baseline_hash == '89a40aac637f1cb001b2e667aab9b93460f1f29ee1660e6e21737272b0fe02cd', 'all48 legacy rows unchanged')
    d, windows = comparison_inputs(root, baseline)
    need(len(json.dumps(d).encode()) <= M.INPUT_CAP, 'unchanged model input bound')
    M.verify_sources(d)
    rows = M.evaluate(d)['rows']
    report = dict(schema='openrx.machine-intermediate-capacity.DATA.v1',
        source_base='da6efe7289af04bd68c9658ce0aa92e53feafabe',
        target=d['target'], scenarios=d['scenarios'], architectures=d['architectures'],
        model_input_sha256=hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
        source_validation='retained source hashes, canonical identities and exact fullhash capacity/phase projection',
        baseline=dict(rows=48, exact_rows_sha256=baseline_hash, unknown_wall_powers=48),
        assumptions=['Inherited B resource point,2GHz illustrative frequency,unchanged issue/retire/SP constraints; not an achievable schedule.',
            'Dataset and backing separately assumed100ns fixed usable response/writeack,2 credits/context/class. Backing credits count64B children; each active credit charges64B payload+32B ownership storage. Two enqueue/dequeue events per transfer are an explicit cost proxy.',
            'Source-order static-prefix adjacent64B coalescing,partial-store read64-modify-write64,uncombined masked16B local access. No cache/refill/writeback/tag array. Dynamic coalescing implementation/storage is unqualified.',
            'Context/engine floors charge the maximum of compute,declared fullhash residence if any,and each separate class credit-concurrency bound. Private data,base auxiliary state,paid credits and external suffix backing scale together.',
            'Numeric fullhash residence/service inputs currently support assumption-only scope with explicit assumption provenance. Native count records never qualify achieved schedules. Measured service requires hash-bound traffic/load/input/frequency calibration records; record validation does not certify measurement truth.',
            'No qualified service/energy/PVT is supplied. Local read/write credit cycles7/4 are inherited assumptions,not the100ns external service or a macro timing claim. Positive unmodeled parent/control/interconnect costs remain unknown.'],
        rows=rows, retained_window_comparators_not_fullhash=window_comparators(windows),
        thresholds=[dict(nonce=x['nonce'],capacity_B=x['local_capacity_B_per_context'],
            required_external_payload_Bps=x['traffic']['external_payload_B']*d['target']['hashes_per_s'],
            exclusive_external_nJ_per64B_ceiling_at_assumed1000W=1000/(d['target']['hashes_per_s']*(x['traffic']['external_read64']+x['traffic']['external_write64']))*1e9)
            for x in rows],
        evidence={key:{'path':sources['path'],'sha256':sources['sha256'],'bytes':sources['bytes'],'scope':sources['scope']}
                  for key,sources in d['sources'].items() if key in PINS},
        code_sha256={name:hashlib.sha256((root/'tools/architecture'/name).read_bytes()).hexdigest()
                     for name in ('machine.py','memory_policies.py','envelope.py')},
        status='UNRESOLVED_CONDITIONAL_ACCOUNTING_NOT_SCHEDULE_OR_PHYSICAL_CALIBRATION',
        highest_value_missing_input='One compatible identified-device/controller mixed64B child-service record with usable read/writeack latency and sustained service,or a longer causal native lifecycle witness. Service67 parent-credit/unmerged window cycles cannot populate the fullhash coalesced contract.',
        workloads_launched=False, full_hash_residence_known=False, physical_acceptance=False)
    raw = (json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()
    need(len(raw) <= M.OUTPUT_CAP, 'unchanged complete model output bound')
    with args.output.open('xb') as f:
        f.write(raw)
    print(json.dumps(dict(output=str(args.output),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),rows=len(rows),baseline_rows_unchanged=48)))


if __name__ == '__main__':
    main()
