"""Bounded hardware-fill integration under the existing single admitted payload."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

source, output = map(Path, sys.argv[1:3])
output.mkdir(parents=True, exist_ok=False)
native_execution = Path('/home/server/openrx-local/v1/executions/20261012T013303Z-848c58102f71')
tool_execution = Path('/home/server/openrx-local/v1/executions/20261016T005835Z-851d576006d4')
library = native_execution / 'build-only/native-build/randomx/librandomx.a'
toolroot = tool_execution / 'output/verilator-5c5314b39cd888f427807d626e1502cbf222c292'
common = [sys.executable, '-B', str(source / 'scripts/test_prepared_hash_lifecycle.py'),
          '--native-library', str(library), '--native-build-execution', str(native_execution),
          '--hardware-fill', '--programs', '2', '--iterations', '1', '--variants', 'prepared',
          '--event-trace', '--timeout', '3600']
records = []
started = time.monotonic()
try:
    for backend in ('icarus', 'verilator'):
        command = [*common, '--output', str(output / backend), '--backend', backend,
                   '--profiles', 'ideal']
        if backend == 'verilator':
            command += ['stalled', '--verilator-root', str(toolroot),
                        '--verilator-build-execution', str(tool_execution),
                        '--cancellation', '--cancellation-phases', '1',
                        '--matching-errors', '--error-ports', '1', '8']
        record = {'backend': backend, 'argv': command}
        records.append(record)
        (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        print('START connected-' + backend, flush=True)
        with (output / (backend + '.log')).open('w') as log:
            result = subprocess.run(['/usr/bin/time', '-v', '-o', str(output / (backend + '.time.txt')),
                                     *command], cwd=source, stdout=log, stderr=subprocess.STDOUT)
        record['returncode'] = result.returncode
        (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        result.check_returncode()
        print('PASS connected-' + backend, flush=True)
    outputs = {backend: json.loads((output / backend / 'summary.json').read_text())
               for backend in ('icarus', 'verilator')}
    assert all(value['status'] == 'pass_connected_native_reference' for value in outputs.values())
    assert all(value['programs'] == 2 and value['iterations'] == 1 and not value['full_v2_requested']
               for value in outputs.values())
    ideal = {backend: value['profiles']['prepared-ideal']['ledger'] for backend, value in outputs.items()}
    assert ideal['icarus'] == ideal['verilator'], 'Four-state/two-state ideal ledger mismatch'
    digest = lambda backend: (output / backend / 'prepared-ideal/actual-final-digest32.hex').read_bytes()
    assert digest('icarus') == digest('verilator'), 'Four-state/two-state actual digest mismatch'
    assert len(outputs['verilator']['cancellation']) == 1
    assert len(outputs['verilator']['matching_errors']) == 2
    full_evidence = source / 'docs/validation/architecture-feasibility-20261016/full-evidence.json'
    assert hashlib.sha256(full_evidence.read_bytes()).hexdigest() == '33f4cbe95805d33068fa9eceee90820f230cd0457d06f35407f9323d1d547ecf'
    original = json.loads(full_evidence.read_text())
    old_total = original['trace']['total_cycles']
    old_stage = original['trace']['stage_cycles']['initialization_transport']
    new_stage = ideal['icarus']['stage_cycles']['initialization_hardware_fill']
    assert 'initialization_transport' not in ideal['icarus']['stage_cycles']
    assert old_total == 40975538 and old_stage == 131074
    report = {
        'status': 'pass_bounded_hardware_fill_integration', 'programs': 2, 'iterations_per_program': 1,
        'icarus_verilator_ideal_ledger_and_digest_equal': True,
        'completed_profiles': 3, 'focused_cancellation_profiles': 1, 'focused_initialization_errors': 2,
        'standalone_full_v2_rerun': False,
        'historical_stage_substitution': {
            'classification': 'derived stage substitution only; no new full-hash measurement',
            'prior_hardware_transport_cycles': old_total,
            'removed_initialization_transport_cycles': old_stage,
            'inserted_measured_initialization_hardware_fill_cycles': new_stage,
            'stage_delta_cycles': new_stage - old_stage,
            'derived_known_hardware_transport_cycles': old_total - old_stage + new_stage,
            'new_full_workload_measured_cycles': None,
        },
        'boundary': 'Host input BLAKE2b, AES program generation and native light dataset provider remain untimed; physical feasibility and alternative full-hash performance unresolved.',
        'elapsed_seconds': time.monotonic() - started,
    }
    (output / 'checks.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report), flush=True)
except Exception as error:
    (output / 'failure.json').write_text(json.dumps({'error': str(error), 'type': type(error).__name__,
                                                   'partial_results_not_passed': True}, indent=2) + '\n')
    raise
