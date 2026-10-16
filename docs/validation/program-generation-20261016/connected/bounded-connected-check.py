"""Focused native hardware program generation; serial admitted payload only."""
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
records = []
started = time.monotonic()
def run(label, command):
    row = {'label': label, 'argv': command, 'cwd': str(source)}
    records.append(row)
    (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
    print('START ' + label, flush=True)
    began = time.monotonic()
    with (output / (label + '.log')).open('w') as log:
        result = subprocess.run(['/usr/bin/time', '-v', '-o', str(output / (label + '.time.txt')),
                                 *command], cwd=source, stdout=log, stderr=subprocess.STDOUT)
    row.update(returncode=result.returncode, elapsed_seconds=time.monotonic()-began)
    (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
    result.check_returncode()
    print('PASS ' + label, flush=True)
try:
    run('focused-unit-tests', [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_lifecycle_*.py', '-v'])
    common = [sys.executable, '-B', str(source / 'scripts/test_prepared_hash_lifecycle.py'),
              '--native-library', str(library), '--native-build-execution', str(native_execution),
              '--hardware-fill', '--hardware-program', '--programs', '2', '--iterations', '1',
              '--variants', 'prepared', '--event-trace', '--timeout', '3600']
    # The compiled backend gives early focused integration feedback before the
    # slower four-state trace/ledger cross-check. All work shares one payload.
    run('verilator', [*common, '--output', str(output / 'verilator'), '--backend', 'verilator',
                      '--profiles', 'ideal', 'stalled', '--verilator-root', str(toolroot),
                      '--verilator-build-execution', str(tool_execution),
                      '--cancellation', '--cancellation-phases', '7',
                      '--matching-errors', '--error-ports', '1', '8'])
    run('icarus', [*common, '--output', str(output / 'icarus'), '--backend', 'icarus', '--profiles', 'ideal'])
    summaries = {b: json.loads((output / b / 'summary.json').read_text()) for b in ('icarus', 'verilator')}
    assert all(s['status']=='pass_connected_native_reference' and s['programs']==2 and s['iterations']==1
               and s['hardware_fill'] and s['hardware_program'] and not s['full_v2_requested'] for s in summaries.values())
    ideal = {b: s['profiles']['prepared-ideal'] for b,s in summaries.items()}
    assert ideal['icarus']['ledger']==ideal['verilator']['ledger'], 'four-state/two-state complete ideal ledger mismatch'
    assert ideal['icarus']['record']==ideal['verilator']['record'], 'four-state/two-state PASS record mismatch'
    for b in ideal:
        provider=ideal[b]['host_provider']
        assert provider['program_generations']==0 and provider['program_generation_host_seconds']==0
        assert provider['assertion_only_program_generations']==2 and provider['input_hash_calls']==1
        assert provider['software_fill_provider_calls']==0
    files = ['actual-final-digest32.hex','trace.csv']
    for name in files:
        a=output/'icarus'/'prepared-ideal'/name; b=output/'verilator'/'prepared-ideal'/name
        assert a.read_bytes()==b.read_bytes(), 'backend bytes mismatch: '+name
    # Compare the complete immutable native assertion corpus, not just digest.
    golds={b: output/b/'native-reference' for b in summaries}
    assert all(p.is_dir() for p in golds.values()), 'native corpus directory missing'
    native_files={b:{str(p.relative_to(golds[b])):p for p in golds[b].rglob('*') if p.is_file()} for b in summaries}
    assert set(native_files['icarus'])==set(native_files['verilator'])
    assert len(native_files['icarus'])==18, 'complete bounded native assertion corpus required'
    for name,a in native_files['icarus'].items():
        assert a.read_bytes()==native_files['verilator'][name].read_bytes(), 'native corpus mismatch: '+name
    assert len(summaries['verilator']['cancellation'])==1 and len(summaries['verilator']['matching_errors'])==2
    report={'status':'pass_bounded_hardware_program_integration','source_commit':'8100bee97bd592767764e5c9a8d3caa3aa2d7183',
            'programs':2,'iterations_per_program':1,'completed_normal_profiles':3,'focused_generation_cancellation':1,
            'focused_initialization_errors':2,'icarus_verilator_complete_ideal_ledger_record_trace_digest_and_native_corpus_equal':True,
            'native_corpus_files_compared':len(native_files['icarus']),
            'ideal_cycles':ideal['icarus']['ledger']['cycles'],
            'ideal_program_generation_cycles':ideal['icarus']['ledger']['stage_cycles']['program_generation'],
            'native_live_program_provider_calls':0,'new_default_full_workload':False,
            'boundary':'Host input BLAKE2b and native Light dataset/device service remain untimed. Generator mapping excludes the logical 3200-byte image buffer and connected executor. No architecture, MHz/area/watts or physical ASIC/PPA acceptance.',
            'elapsed_seconds':time.monotonic()-started}
    (output/'checks.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report),flush=True)
except Exception as error:
    (output/'failure.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__,'partial_results_not_passed':True},indent=2)+'\n')
    raise
