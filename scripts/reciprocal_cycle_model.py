#!/usr/bin/env python3
"""Calibrate paired iteration-stage costs from actual RTL clock ledgers.

Preparation is charged for every admission, including an identical reload.
Transport/FSM observers are nested costs, never added to the outer clock total.
Draft surrounding hash-stage evidence is contextual; it is not a connected
complete-pipeline measurement. Unknown stages remain unknown, never zero.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PHASES = ('launch_clocks', 'entry_clocks', 'kernel_clocks', 'dataset_clocks',
          'tail_clocks', 'return_clocks')
COMMON = ('stall', 'control', 'admissions', 'iterations', 'reloads', 'program_reads',
          'retirements', 'static_rcp', 'static_active_rcp', 'dynamic_rcp', 'dynamic_active_rcp', 'dynamic_nop_rcp',
          'scratchpad_reads', 'scratchpad_writes', 'tail_writes', 'full_memory_bytes')
WAIT_OBSERVERS = ('prep_request_stall', 'prep_reply_wait', 'sp_request_stall',
                  'sp_reply_wait', 'sp_store_stall', 'dataset_request_stall',
                  'dataset_reply_wait', 'return_hold_wait', 'fetch_request_stall',
                  'fetch_reply_wait', 'tail_aes_wait')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_ledger(row):
    """Validate measured, disjoint clocks and nested occupancy before modeling."""
    for key, value in row.items():
        require(type(value) is int and value >= 0, 'nonnegative integer metric: ' + key)
    require(row['prepared'] in (0, 1) and row['stall'] in (0, 1), 'unknown profile')
    require(row['full_hash_measured'] == 0, 'iteration fixture cannot certify a full hash')
    require(row['execution_clocks'] == sum(row[k] for k in PHASES), 'execution ledger does not close')
    require(row['preparation_clocks'] == sum(row[f'prep_s{i}'] for i in range(6)),
            'preparation occupancy does not close')
    require(row['kernel_clocks'] == sum(row[f'ex_s{i}'] for i in range(18)),
            'kernel occupancy does not close')
    require(row['elapsed_cycles'] == row['preparation_clocks'] + row['execution_clocks'] +
            row['control_clocks'] + row['outside_clocks'], 'elapsed ledger does not close')
    require(row['dynamic_rcp'] == row['dynamic_active_rcp'] + row['dynamic_nop_rcp'],
            'dynamic reciprocal classification mismatch')
    require(row['reloads'] == row['admissions'], 'every admission must charge a reload')
    require(row['preparation_response_clocks'] <= row['preparation_clocks'],
            'response latency exceeds preparation window')


def compare(baseline, prepared, static_active):
    """Return measured cost/saving only for equivalent native-stage workloads."""
    validate_ledger(baseline)
    validate_ledger(prepared)
    require(baseline['prepared'] == 0 and prepared['prepared'] == 1, 'baseline/prepared reversed')
    require(type(static_active) is int and static_active > 0, 'positive static active count required')
    require(prepared['static_active_rcp'] == static_active, 'native static calibration count mismatch')
    for key in COMMON:
        require(baseline[key] == prepared[key], 'paired workload mismatch: ' + key)
    dynamic = baseline['dynamic_active_rcp']
    require(dynamic > 0, 'active dynamic calibration missing')
    require(baseline['preparation_rcp_requests'] == 0 and prepared['runtime_rcp_requests'] == 0,
            'reciprocal work in wrong stage')
    require(prepared['preparation_rcp_requests'] == static_active and
            baseline['runtime_rcp_requests'] == dynamic, 'reciprocal handshake count mismatch')
    require(baseline['prep_s3'] == baseline['prep_s4'] == 0 and
            prepared['ex_s12'] == prepared['ex_s13'] == 0, 'unused reciprocal FSM occupied')
    # Derive unit cost from actual occupancies, not wall time or a guessed CPU rate.
    require(prepared['prep_s3'] == static_active and baseline['ex_s12'] == dynamic,
            'reciprocal request occupancy mismatch')
    prep_wait, prep_remainder = divmod(prepared['prep_s4'], static_active)
    run_wait, run_remainder = divmod(baseline['ex_s13'], dynamic)
    require(prep_remainder == run_remainder == 0 and prep_wait == run_wait and prep_wait > 0,
            'reciprocal unit latency not calibrated equally')
    cost = 1 + prep_wait
    for key in PHASES:
        if key != 'kernel_clocks':
            require(baseline[key] == prepared[key], 'common phase changed: ' + key)
    for i in range(6):
        if i not in (3, 4):
            require(baseline[f'prep_s{i}'] == prepared[f'prep_s{i}'], 'common preparation FSM changed')
    for i in range(18):
        if i not in (12, 13):
            require(baseline[f'ex_s{i}'] == prepared[f'ex_s{i}'], 'common execution FSM changed')
    prep_cost = prepared['preparation_clocks'] - baseline['preparation_clocks']
    kernel_saved = baseline['kernel_clocks'] - prepared['kernel_clocks']
    require(prep_cost == cost * static_active, 'preparation cost not charged')
    require(kernel_saved == cost * dynamic, 'runtime savings do not match calibration')
    base_total = baseline['preparation_clocks'] + baseline['execution_clocks']
    new_total = prepared['preparation_clocks'] + prepared['execution_clocks']
    require(base_total - new_total == cost * (dynamic - static_active), 'stage delta mismatch')
    return {'stall': baseline['stall'], 'scope': 'native iteration stage including every preparation',
            'baseline_clocks': base_total, 'prepared_clocks': new_total,
            'static_active_rcp': static_active, 'dynamic_active_rcp': dynamic,
            'measured_request_clocks_each': 1, 'measured_reply_wait_clocks_each': prep_wait,
            'measured_active_rcp_clocks_each': cost,
            'preparation_added_clocks': prep_cost, 'kernel_saved_clocks': kernel_saved,
            'net_stage_saved_clocks': base_total - new_total,
            'baseline_phases': {k: baseline[k] for k in PHASES},
            'prepared_phases': {k: prepared[k] for k in PHASES},
            'nested_wait_observers': {name: {'baseline': baseline[name], 'prepared': prepared[name]}
                                      for name in WAIT_OBSERVERS},
            'control_and_outside_excluded_from_native_window': {
                mode: {k: row[k] for k in ('control_clocks', 'outside_clocks', 'elapsed_cycles')}
                for mode, row in [('baseline', baseline), ('prepared', prepared)]},
            'full_hash_performance_accepted': False}


def pipeline_context(components):
    """Preserve separate draft component costs and explicit missing integration."""
    require(components['connected_complete_pipeline_measured'] is False,
            'unvalidated complete-pipeline declaration')
    missing = components['missing_stages_or_calibration']
    require(isinstance(missing, list) and len(missing) > 0, 'missing stages cannot be omitted')
    for stage in missing:
        require(stage['clocks'] is None, 'unknown stage cost must remain null')
    for stage in components['draft_component_evidence']:
        require(stage['status'] == 'draft-component-only', 'component acceptance overstated')
        require(re.fullmatch('[a-f0-9]{64}', stage['summary_sha256']) is not None,
                'component summary binding missing')
    return {**components, 'complete_pipeline_clocks': None,
            'full_hash_speedup': None, 'physical_PPA_accepted': False,
            'aggregation': 'Component fixtures have different boundaries and memory providers; do not sum them into a measured hash.'}


def read_record(path):
    lines = [line for line in path.read_text().splitlines()
             if line.startswith('PASS prepared_reciprocal_iteration ')]
    require(len(lines) == 1, 'one integration PASS required: ' + str(path))
    return {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', lines[0])}


def validate_admissions(metrics, expected):
    require(metrics['wait_observers_are_nested'] is True, 'wait observers must remain nested')
    require(len(metrics['controller_phase_clocks']) == 12 and
            sum(metrics['controller_phase_clocks']) == metrics['execution_clocks'],
            'controller occupancy does not close')
    records = metrics['admission_records']
    require(len(records) == metrics['admissions'] == len(expected), 'admission metrics missing')
    for index, (row, native) in enumerate(zip(records, expected)):
        require(row['admission'] == index and row['v2'] == native['v2'] and
                row['static_active_rcp'] == native['static_active_rcp'], 'admission/native mismatch')
        require(row['execution_clocks'] == sum(row[k] for k in PHASES), 'admission phase ledger mismatch')
        require(row['iterations'] == native['iterations'], 'admission iteration count mismatch')
    for key in ('iterations', 'program_reads', 'retirements', 'dynamic_rcp', 'dynamic_active_rcp',
                'dynamic_nop_rcp', 'preparation_clocks', 'preparation_response_clocks',
                'execution_clocks', 'preparation_rcp_requests', 'runtime_rcp_requests', *PHASES):
        require(sum(row[key] for row in records) == metrics[key], 'admission sum mismatch: ' + key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--components', type=Path,
                        default=ROOT / 'docs/validation/prepared-reciprocals/surrounding-stages.json')
    args = parser.parse_args()
    directory = args.directory.resolve()
    inputs = {str(args.components): hashlib.sha256(args.components.read_bytes()).hexdigest()}
    coverage_path = directory / 'coverage.json'
    coverage = json.loads(coverage_path.read_text())
    inputs[coverage_path.name] = hashlib.sha256(coverage_path.read_bytes()).hexdigest()
    static_active = sum(row['static_active_rcp'] for row in coverage['admissions'])
    results = []
    for stall in (0, 1):
        rows, detailed = [], []
        for mode in (0, 1):
            log = directory / f'rtl-iteration-{mode}-{stall}.log'
            rows.append(read_record(log))
            inputs[log.name] = hashlib.sha256(log.read_bytes()).hexdigest()
            metrics_path = directory / f'integration-{mode}-{stall}.json'
            metrics = json.loads(metrics_path.read_text())
            inputs[metrics_path.name] = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
            for key, value in rows[-1].items():
                require(metrics[key] == value, 'JSON/PASS disagreement: ' + key)
            validate_admissions(metrics, coverage['admissions'])
            detailed.append(metrics['admission_records'])
        result = compare(*rows, static_active)
        result['per_admission'] = []
        cost = result['measured_active_rcp_clocks_each']
        for baseline, prepared in zip(*detailed):
            for key in ('admission', 'v2', 'epoch', 'iterations', 'program_reads', 'retirements',
                        'static_rcp', 'static_active_rcp', 'dynamic_rcp', 'dynamic_active_rcp', 'dynamic_nop_rcp'):
                require(baseline[key] == prepared[key], 'admission paired workload mismatch: ' + key)
            added = prepared['preparation_clocks'] - baseline['preparation_clocks']
            saved = baseline['execution_clocks'] - prepared['execution_clocks']
            require(added == cost * baseline['static_active_rcp'] and
                    saved == cost * baseline['dynamic_active_rcp'], 'admission calibration mismatch')
            result['per_admission'].append({'admission': baseline['admission'], 'v2': baseline['v2'],
                'preparation_added_clocks': added, 'execution_saved_clocks': saved,
                'net_stage_saved_clocks': saved - added})
        results.append(result)
    require(results[0]['measured_active_rcp_clocks_each'] == results[1]['measured_active_rcp_clocks_each'],
            'memory profile changed reciprocal unit cost')
    output = {'status': 'calibrated-stage-candidate', 'pairs': results,
              'surrounding_hash_stages': pipeline_context(json.loads(args.components.read_text())),
              'inputs_sha256': inputs, 'full_hash_performance_accepted': False}
    with (directory / 'cycle-model.json').open('x') as stream:
        stream.write(json.dumps(output, indent=2) + '\n')
    print('PASS reciprocal_cycle_model profiles=2 full_hash_performance_accepted=0')


if __name__ == '__main__':
    main()
