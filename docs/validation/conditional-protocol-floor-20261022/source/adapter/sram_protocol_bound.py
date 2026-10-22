#!/usr/bin/env python3
"""Conditional necessary ceilings over pinned evidence; not a physical model."""
import argparse
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path


INPUTS = {
    'pr92_report.json': (16811, '67deb5c947d346f84c48db5e30b7000a76a8fdd9c8b0fe67bfa81621d81c9bde'),
    'pr92_provenance.json': (8986, '1689dfdbaf87d1b3563e73134826bae0def89e2cb64652c133e01610cab8afcb'),
    'pr92_contract.json': (14532, '087a18367ddd65bf930e2030070995f0d8e8e2e1adb246d2284be724e7583346'),
    'pr91_report.json': (50216, 'd6baa3de036273b1ac3918ffb5c3418b98f0130acdb43652380c06648eea81ce'),
    'channel.v': (6387, '0d02318cad0991321fed4a365664d231f90f1968ef2e1fdc733c3b5291d06493'),
    'fabric.v': (5597, '4c6c4d5c784ad8c310b20afea5ee62fffa7cd910eb6632a76f6daeb1f171c438'),
    'channel_bench.v': (27225, '5468e7a77fe2dcd4c2a6e8e8cde3e953552e3e4f6e662f84b8a5a1a787325f79'),
    'native_bench.v': (46653, 'eda2ba99830af4568a99acbf88a1bda7f6432be68dd642d13d2d49b66c83eb42'),
    'rtl_protocol.json': (939, 'c30686c0ecd7543d7a430b1b1b44ca07eb64313c87be94f3cbdf727e15a5a2c6'),
    'mapped_protocol.json': (939, 'c30686c0ecd7543d7a430b1b1b44ca07eb64313c87be94f3cbdf727e15a5a2c6'),
    'pr89_source_bindings.json': (3076, 'a8b942b2aea57d660cbc6b5f3181833cd9fe027b272ec4909072ea9e01827b86'),
}
NANOSECONDS_PER_SECOND = 10**9


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_float=Decimal, parse_constant=invalid)


def positive(value):
    require(type(value) in (int, Fraction, Decimal), 'exact rational value required')
    require(not isinstance(value, Decimal) or value.is_finite(), 'nonfinite exact value')
    result = Fraction(value)
    require(result > 0, 'positive value required')
    return result


def rational(value):
    value = positive(value)
    return {'numerator': value.numerator, 'denominator': value.denominator}


def ceiling(interval_ns, period_ns):
    """Intersection of necessary ceilings, without additive latency assumptions."""
    interval, period = positive(interval_ns), positive(period_ns)
    return min(Fraction(NANOSECONDS_PER_SECOND, 1) / interval,
               Fraction(NANOSECONDS_PER_SECOND, 1) / (2 * period))


def load_inputs(root, registry_path):
    require(not root.is_symlink() and root.is_dir(), 'input root must be a real directory')
    root = root.resolve(strict=True)
    require(not registry_path.is_symlink() and registry_path.is_file(), 'real registry required')
    require(registry_path.stat().st_size <= 16384, 'registry too large')
    registry = parse_json(registry_path.read_bytes())
    wanted = {name: {'bytes': n, 'sha256': h} for name, (n, h) in INPUTS.items()}
    require(type(registry) is dict and set(registry) == {'schema', 'files'} and
            registry['schema'] == 'openrx.sram-protocol-bound.inputs.v1' and
            registry['files'] == wanted, 'trusted registry differs')
    require({p.name for p in root.iterdir()} == set(INPUTS), 'input directory set differs')
    result, total = {}, 0
    for name, (size, digest) in INPUTS.items():
        path = root / name
        require(not path.is_symlink() and path.is_file() and path.stat().st_size == size,
                'input type/size differs: ' + name)
        total += size
        require(total <= 262144 and size <= 131072, 'input size bound exceeded')
        raw = path.read_bytes()
        require(sha(raw) == digest, 'input digest differs: ' + name)
        result[name] = parse_json(raw) if name.endswith('.json') else raw
    return result, wanted


def make_report(inputs, bindings):
    report = inputs['pr92_report.json']
    require(report['schema'] == 'openrx.conditional-memory-baseline-report.v1' and
            report['classification'] == 'conditional_analytic_model_observations_only' and
            report['physical_characterization'] is False and
            report['physical_ppa_accepted'] is False and
            report['full_hash_projection_performed'] is False, 'PR92 scope differs')
    organization = report['storage_organization_assumption']
    require((organization['capacity_bytes'], organization['rows'], organization['row_bits'],
             organization['rw_ports_per_bank'], organization['global_credits']) ==
            (131072, 4096, 256, 1, 1), 'organization/credit assumption differs')
    assumptions = report['model_assumptions']
    require((assumptions['node_nm'], assumptions['temperature_k'], assumptions['voltage_v']) ==
            (45, 360, Decimal('1.0')) and assumptions['foundry_corner'] is None and
            assumptions['physical_characterization'] is False, 'conditional model differs')
    cases = report['cases']
    require([x['name'] for x in cases] == ['bank1', 'bank4'] and
            [x['banks'] for x in cases] == [1, 4], 'bank cases differ')
    intervals = []
    for case in cases:
        interval = max(positive(case['modeled_access_ns']), positive(case['modeled_random_cycle_ns']))
        require(interval == positive(case['optimistic_global_one_credit_period_ns']),
                'array interval does not close')
        intervals.append(interval)
    one, four = intervals
    require(one == Fraction(274122, 100000) and four == Fraction(714793, 1000000),
            'accepted interval values differ')
    source = inputs['pr89_source_bindings.json']['files']
    for accepted, local in [('rtl/dataset_shared/randomx_dataset_shared_channel.v', 'channel.v'),
                            ('rtl/dataset_shared/randomx_dataset_shared_fabric.v', 'fabric.v'),
                            ('rtl/dataset_shared/tests/tb_dataset_shared_channel.v', 'channel_bench.v'),
                            ('rtl/dataset_shared/tests/tb_dataset_shared_native.v', 'native_bench.v')]:
        require(source[accepted] == bindings[local], 'accepted RTL/bench binding differs')
    for name in ('rtl_protocol.json', 'mapped_protocol.json'):
        protocol = inputs[name]
        require(protocol['schema'] == 'openrx.shared-dataset-channel-protocol.v1' and
                protocol['status'] == 'pass' and protocol['same_edge_request_response_cases'] == 2 and
                protocol['high_water_mark'] == 1, 'accepted same-edge evidence differs')
    prior = inputs['pr91_report.json']
    require(prior['schema'] == 'openrx.architecture.finite-fabric-service-profile.v1' and
            prior['physical_frequency_hz'] is None and prior['full_hash_projection_performed'] is False,
            'PR91 scope differs')
    require(prior['profiles']['concurrent-ideal']['interfaces']['fetch']
            ['owner_credit_occupied_clocks_per_request'] == {'numerator': 14252, 'denominator': 7126},
            'retained nested occupancy differs')
    periods = [('below_both_breakpoints', four / 4), ('four_bank_breakpoint', four / 2),
               ('between_breakpoints', (four + one) / 4), ('one_bank_breakpoint', one / 2),
               ('above_both_breakpoints', one)]
    witnesses = []
    for name, period in periods:
        bounds = [ceiling(t, period) for t in intervals]
        witnesses.append({'algebraic_witness': name, 'period_ns': rational(period),
                          'necessary_request_ceilings_per_second': [rational(x) for x in bounds],
                          'ratio_of_necessary_ceilings_only': rational(bounds[1] / bounds[0])})
    return {
        'schema': 'openrx.sram-protocol-necessary-bound.v1',
        'classification': 'conditional_necessary_ceilings_only',
        'scientific_acceptance': 'unverified_pending_independent_review',
        'physical_acceptance': False, 'new_full_hash_rtl_cacti_or_gem5_run': False,
        'model_assumptions': {'node_nm': 45, 'voltage_v': '1.0', 'temperature_k': 360,
                              'scope': 'Retained hypothetical CACTI6.5 ITRS HP projection only'},
        'organization': {'capacity_bytes': 131072, 'logical_row_bytes': 32,
                         'global_credits': 1, 'physical_row_mapping_implemented': False},
        'source_bindings': bindings,
        'preserved_input_scientific_flags': {
            'pr92_report': report['scientific_acceptance'],
            'pr92_provenance': inputs['pr92_provenance.json']['scientific_acceptance']},
        'protocol_facts': {'minimum_capture_spacing_clocks': 2,
                           'same_edge_backend_request_response_permitted': True,
                           'independent_memory_latency_contract_selected': False,
                           'attribution': 'Accepted SHA-bound channel RTL49-65/100-132 and bench357-372; static proof, not new simulation'},
        'conditional_formula': 'C_i(P_ns)=min(1000000000/T_i_ns,1000000000/(2*P_ns)), P_ns>0',
        'array_intervals_ns': {'bank1': rational(one), 'bank4': rational(four)},
        'period_breakpoints_ns': {'four_bank': rational(four / 2), 'one_bank': rational(one / 2)},
        'ratio_of_necessary_ceilings_piecewise': [
            {'period_domain': '0<P<=T4/2', 'value': rational(one / four)},
            {'period_domain': 'T4/2<P<T1/2', 'formula': 'T1/(2*P)'},
            {'period_domain': 'P>=T1/2', 'value': rational(1)}],
        'algebraic_witnesses_not_selected_clock_points': witnesses,
        'retained_nested_occupancy': {'numerator': 14252, 'denominator': 7126,
                                     'scope': 'PR91 owned clocks/request only; not provider latency or a universal response contract'},
        'unknown': {key: None for key in ('physical_clock_hz', 'sustainable_physical_requests_per_second',
                   'achieved_hashes_per_second', 'actual_implementation_performance_ratio',
                   'engine_count', 'controller_phy_service_latency', 'whole_machine_wall_power_w',
                   'characterized_process_corner')},
        'scope_notes': [
            'Intersecting necessary ceilings does not prove joint achievability or bound actual performance ratios.',
            'Clock period remains a symbolic variable; witnesses are derived algebraically, not selected physical frequencies.',
            'No bank-count multiplier, universal extra reply clock, additive array/protocol latency or ceil(T/P)+2 assumption.',
            'The declared SRAM row mapping remains unimplemented; prepared cache, scratchpads and controller/PHY are outside.',
            'Accepted protocol scripts and PR91 nested batch counters are not steady physical-throughput evidence.'],
    }


def write_report(output, report, input_root):
    output = output.absolute()
    source = Path(__file__).resolve().parents[1]
    parent = output.parent.resolve(strict=True)
    require(not output.exists() and not output.is_symlink(), 'exclusive new output required')
    resolved_output = parent / output.name
    require(not resolved_output.is_relative_to(source) and
            not resolved_output.is_relative_to(input_root.resolve(strict=True)), 'output intersects frozen source')
    raw = json.dumps(report, indent=2, sort_keys=True, allow_nan=False).encode() + b'\n'
    require(b'/home/' not in raw and b'/tmp/' not in raw, 'private path in report')
    provenance = {'schema': 'openrx.sram-protocol-bound.provenance.v1',
                  'adapter_sha256': sha(Path(__file__).read_bytes()),
                  'source_bindings': report['source_bindings'],
                  'scientific_acceptance': 'unverified_pending_independent_review',
                  'physical_acceptance': False}
    provenance_raw = json.dumps(provenance, indent=2, sort_keys=True).encode() + b'\n'
    output.mkdir(exist_ok=False)
    for name, data in [('protocol-bound.json', raw), ('provenance.json', provenance_raw)]:
        with (output / name).open('xb') as stream:
            stream.write(data)
    index = {name: sha(data) for name, data in [('protocol-bound.json', raw), ('provenance.json', provenance_raw)]}
    with (output / 'artifacts.sha256.json').open('x') as stream:
        json.dump(index, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--registry', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    inputs, bindings = load_inputs(args.inputs, args.registry)
    write_report(args.output, make_report(inputs, bindings), args.inputs)


if __name__ == '__main__':
    main()
