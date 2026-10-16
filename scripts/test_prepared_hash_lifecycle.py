#!/usr/bin/env python3
"""Serial, admitted connected-v2 validation with an actual native dataset provider.

Run inside the existing immutable local runner. All generated files stay in a
fresh external output directory. Native providers are untimed host callbacks;
their host seconds never become invented device cycles or physical power.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from test_iteration_engine import extract, function
from test_divsqrt_execute import RTL, V
from hardfloat_compile_view import prepare as compile_view
from program_sequence_fixture import prepare as prepare_assertions

ROOT = Path(__file__).resolve().parents[1]
TEST = 'rtl/hash/tests/'
EXTRA = ['rtl/execute/randomx_program_control.v',
         'rtl/execute/randomx_program_reciprocals.v',
         'rtl/execute/randomx_prepared_rcp_guard.v',
         'rtl/execute/randomx_prepared_integer_iteration.v',
         'rtl/execute/randomx_prepared_program_sequence.v']
TOP = 'rtl/hash/randomx_prepared_hash_lifecycle.v'
MESSAGE = b'OpenRX connected prepared RandomX v2 lifecycle 20261016'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def reused_library(library, execution, source):
    """Verify build provenance rather than trusting a retired CMake source path."""
    manifest = json.loads((execution / 'manifest.json').read_text())
    receipt = json.loads((execution / 'receipt.json').read_text())
    row = [a for a in receipt['artifacts'] if Path(a['path']) == library]
    assert len(row) == 1 and row[0]['sha256'] == sha(library)
    assert receipt['process']['returncode'] == 0
    native = [a for record in manifest['sources'] for a in record['files']
              if a['relative'].startswith('vendor/randomx/')]
    assert native and all(sha(source / a['relative']) == a['sha256'] for a in native)
    build = library.parent.parent / 'build.json'
    data = json.loads(build.read_text())
    assert data['status'] == 'built' and data['artifacts']['randomx/librandomx.a'] == sha(library)
    record = next(a for a in receipt['artifacts'] if Path(a['path']) == build)
    assert sha(build) == record['sha256']
    flags = library.parent / 'CMakeFiles/randomx.dir/flags.make'
    record = next(a for a in receipt['artifacts'] if Path(a['path']) == flags)
    assert sha(flags) == record['sha256'] and '-fPIC' in flags.read_text()
    return {'library': str(library), 'sha256': sha(library), 'native_source_files_verified': len(native),
            'execution': str(execution), 'manifest_sha256': sha(execution / 'manifest.json'),
            'receipt_sha256': sha(execution / 'receipt.json'), 'build_sha256': sha(build),
            'PIC_flags_sha256': sha(flags), 'reconfigured_or_modified': False}


def validate_ledger(ledger, provider, iterations, programs, native, prepared):
    assert set(ledger['stage_cycles']) == {'initialization_transport', 'control_and_metadata',
        'program_preparation', 'execution', 'interprogram_seed', 'finalization', 'held_return'}
    assert type(ledger['cycles']) is int and ledger['cycles'] > 0
    assert all(type(value) is int and value >= 0 for value in ledger['stage_cycles'].values())
    assert len(ledger['nested_iteration_phases']) == 12 and len(ledger['nested_finalization_phases']) == 6
    assert len(ledger['nested_executor_phases']) == 18
    assert all(type(value) is int and value >= 0 for value in
               ledger['nested_iteration_phases'] + ledger['nested_finalization_phases'] + ledger['nested_executor_phases'])
    assert sum(ledger['stage_cycles'].values()) == ledger['cycles']
    assert sum(ledger['nested_iteration_phases']) == ledger['stage_cycles']['execution']
    assert sum(ledger['nested_finalization_phases']) == ledger['stage_cycles']['finalization']
    assert sum(ledger['nested_executor_phases']) == ledger['nested_iteration_phases'][7]
    assert ledger['scratchpad_bytes'] == 2097152
    for name in ('physical_port_read_bytes', 'physical_port_write_bus_bytes', 'strobed_write_bytes',
                 'logical_bytecode_memory_bytes', 'logical_entry_bytes', 'logical_tail_bytes'):
        assert type(ledger[name]) is int and ledger[name] >= 0
    assert ledger['physical_port_read_bytes'] % 16 == 0 and ledger['physical_port_write_bus_bytes'] % 16 == 0
    assert ledger['strobed_write_bytes'] <= ledger['physical_port_write_bus_bytes']
    assert ledger['logical_entry_bytes'] == programs * iterations * 128
    assert ledger['logical_tail_bytes'] == programs * iterations * 128
    assert ledger['dataset_logical_bytes'] == programs * iterations * 64
    assert ledger['logical_bytecode_memory_bytes'] == native['bytecode_events'] * 8
    assert ledger['program_image_load_bytes'] == programs * 384 * 8
    assert ledger['untimed_provider_device_cycles'] is None
    assert provider['provider_device_cycles'] is None
    assert provider['dataset_requests'] == programs * iterations and provider['program_generations'] == programs
    assert provider['cache_bytes'] == 268435456 and provider['logical_dataset_bytes'] == 2181038016
    assert provider['materialized_dataset_bytes'] == 0
    for name in ('preparation_reciprocals', 'runtime_reciprocals'):
        assert type(ledger[name]) is int and ledger[name] >= 0
    assert ledger['preparation_reciprocals'] == (native['static_active_reciprocals'] if prepared else 0)
    assert ledger['runtime_reciprocals'] == (0 if prepared else native['dynamic_active_reciprocals'])


def compare_variants(baseline, prepared, native):
    """Compare equal native work and derive reciprocal cost from observed cycles."""
    for name in ('scratchpad_bytes', 'physical_port_read_bytes', 'physical_port_write_bus_bytes',
                 'strobed_write_bytes', 'dataset_logical_bytes', 'logical_bytecode_memory_bytes',
                 'logical_entry_bytes', 'logical_tail_bytes', 'program_image_load_bytes'):
        assert baseline[name] == prepared[name], 'paired workload mismatch: ' + name
    for name in baseline['stage_cycles']:
        if name not in ('program_preparation', 'execution'):
            assert baseline['stage_cycles'][name] == prepared['stage_cycles'][name], 'common stage changed: ' + name
    for phase in range(12):
        if phase != 7:
            assert baseline['nested_iteration_phases'][phase] == prepared['nested_iteration_phases'][phase]
    for phase in range(18):
        if phase not in (12, 13):
            assert baseline['nested_executor_phases'][phase] == prepared['nested_executor_phases'][phase]
    static, dynamic = native['static_active_reciprocals'], native['dynamic_active_reciprocals']
    assert baseline['preparation_reciprocals'] == prepared['runtime_reciprocals'] == 0
    assert prepared['preparation_reciprocals'] == static and baseline['runtime_reciprocals'] == dynamic
    assert prepared['nested_executor_phases'][12:14] == [0, 0]
    request, wait = baseline['nested_executor_phases'][12:14]
    assert request == dynamic
    if dynamic:
        wait_each, remainder = divmod(wait, dynamic)
        assert not remainder and wait_each > 0
        cost = 1 + wait_each
    else:
        assert static == wait == 0
        cost = None
    added = prepared['stage_cycles']['program_preparation'] - baseline['stage_cycles']['program_preparation']
    saved = baseline['stage_cycles']['execution'] - prepared['stage_cycles']['execution']
    assert added == (cost or 0) * static and saved == (cost or 0) * dynamic
    assert baseline['cycles'] - prepared['cycles'] == saved - added
    return {'native_work_and_common_stages_equal': True, 'static_active_reciprocals': static,
            'dynamic_active_reciprocals': dynamic, 'measured_reciprocal_cycles_each': cost,
            'preparation_added_cycles': added, 'execution_saved_cycles': saved,
            'net_saved_cycles': baseline['cycles'] - prepared['cycles'],
            'physical_timing_or_power_accepted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-library', type=Path)
    parser.add_argument('--native-build-execution', type=Path)
    parser.add_argument('--programs', type=int, default=8, choices=range(1, 9))
    parser.add_argument('--iterations', type=int, default=2)
    parser.add_argument('--profiles', nargs='+', choices=['ideal', 'stalled'], default=['ideal', 'stalled'])
    parser.add_argument('--variants', nargs='+', choices=['baseline', 'prepared'], default=['baseline', 'prepared'])
    parser.add_argument('--event-trace', action='store_true', help='Keep retirements/transfers and outer/iteration/executor transitions instead of idle rows')
    parser.add_argument('--backend', choices=['icarus', 'verilator'], default='icarus')
    parser.add_argument('--verilator-root', type=Path)
    parser.add_argument('--verilator-build-execution', type=Path)
    parser.add_argument('--full-v2', action='store_true')
    parser.add_argument('--compile-only', action='store_true')
    parser.add_argument('--cancellation', action='store_true')
    parser.add_argument('--matching-errors', action='store_true', help='Six provider errors plus invalid input/write, held return and fresh-generation handoff')
    parser.add_argument('--capacity-checks', action='store_true', help='Batch-epoch/hash-tag exhaustion and drained hard-reset recovery')
    parser.add_argument('--interfaces-only', action='store_true', help='Run requested recovery/capacity checks without a completed-hash claim')
    parser.add_argument('--input-hex', default=MESSAGE.hex())
    parser.add_argument('--timeout', type=int, default=10800)
    args = parser.parse_args()
    if len(args.profiles) != len(set(args.profiles)):
        parser.error('duplicate output profiles are not permitted')
    if len(args.variants) != len(set(args.variants)):
        parser.error('duplicate variants are not permitted')
    if args.interfaces_only and (args.full_v2 or args.compile_only or not
                                (args.cancellation or args.matching_errors or args.capacity_checks)):
        parser.error('interfaces-only requires a recovery/capacity check and cannot select full-v2/compile-only')
    if args.full_v2:
        args.programs, args.iterations = 8, 2048
    if not 1 <= args.iterations <= 2048 or args.timeout <= 0:
        parser.error('bounded positive iterations/timeout required')
    try:
        message = bytes.fromhex(args.input_hex)
    except ValueError:
        parser.error('input must be hexadecimal bytes')
    if len(message) > 80:
        parser.error('lifecycle input port holds at most80 bytes')
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        parser.error('fresh external output directory required')
    if not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('unambiguous HDL paths required')
    if bool(args.native_library) != bool(args.native_build_execution):
        parser.error('reuse requires both library and immutable build execution')
    if args.backend == 'verilator' and not (args.verilator_root and args.verilator_build_execution):
        parser.error('Verilator requires an exact retained build root and execution receipt')
    out.mkdir()
    commands = []
    summary = {'schema': 'openrx.connected-prepared-v2.v1', 'status': 'pending',
               'base': 'aebe30a0c2d1547fed6b66976ba0757b4b66389a', 'programs': args.programs,
               'iterations': args.iterations, 'full_v2_requested': args.full_v2,
               'compile_only': args.compile_only, 'variants': args.variants, 'event_trace': args.event_trace,
               'interfaces_only': args.interfaces_only,
               'backend': args.backend, 'simulation_state_model': 'four-state' if args.backend == 'icarus' else 'two-state; bounded cross-check with Icarus required',
               'balanced_variant_cycle_comparison': False, 'paired_cycle_comparisons': {},
               'profiles': {}, 'cancellation': {}, 'matching_errors': {}, 'capacity_checks': {},
               'input_hex': message.hex(), 'power_watts': None, 'device_frequency_hz': None,
               'physical_area': None, 'whole_machine_efficiency_accepted': False}
    compat = None

    def run(label, argv, timeout=args.timeout, env=None):
        if Path(argv[0]).name in ('iverilog', 'verilator') and compat is not None:
            argv = [str(compat) if item == V + 'divSqrtRecFN_small.v' else item for item in argv]
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout}
        if env is not None:
            row['environment_overrides'] = {key: value for key, value in env.items() if os.environ.get(key) != value}
        commands.append(row)
        print('START ' + label, flush=True)
        began = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as stream:
                process = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout, env=env)
            row['returncode'] = process.returncode
            process.check_returncode()
        except Exception as error:
            row['error'] = str(error)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - began
            save(out / 'commands.json', commands)
        print('PASS ' + label, flush=True)

    try:
        sources = list(dict.fromkeys([*RTL, *EXTRA,
                   *[str(path.relative_to(ROOT)) for path in sorted((ROOT / 'rtl/hash').glob('randomx_*.v'))
                     if path.name != 'randomx_program_hash_sequence.v']]))
        native_sources = [str(path.relative_to(ROOT)) for path in (ROOT / 'vendor/randomx').rglob('*') if path.is_file()]
        inputs = set(sources + native_sources + [TEST + name for name in
                     ['lifecycle_native.hpp', 'lifecycle_source_vpi.cpp', 'lifecycle_source_dpi.cpp', 'lifecycle_reference.cpp', 'tb_prepared_hash_lifecycle.v']])
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'scripts').glob('*.py'))
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'rtl/hash/vendor/blake2').glob('*.v'))
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'rtl').rglob('*')
                      if path.is_file() and (path.suffix in ('.vh', '.vi') or path.name in ('LICENSE', 'manifest.json', 'UPSTREAM.json')))
        inputs.update(['rtl/execute/tests/program_native_helpers.hpp', 'vendor/randomx.sha256.json', 'vendor/randomx.lock.json'])
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'tests').glob('test_lifecycle_*.py'))
        hashes = {name: sha(ROOT / name) for name in sorted(inputs)}
        save(out / 'inputs.json', hashes)
        test_tmp = out / 'test-tmp'
        test_tmp.mkdir()
        run('lifecycle-unit-tests', ['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_lifecycle_*.py', '-v'],
            env=dict(os.environ, TMPDIR=str(test_tmp)))
        run('vendor', ['python3', '-B', 'scripts/verify_vendor.py'])
        for tool, flag in [('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')]:
            executable = Path(shutil.which(tool)).resolve()
            summary.setdefault('tools', {})[tool] = {'path': str(executable), 'sha256': sha(executable),
                'version': subprocess.check_output([tool, flag], stderr=subprocess.STDOUT, text=True)}
        for source, name in [('rtl/execute/LICENSE', 'LICENSE-OpenRX'), ('vendor/randomx/LICENSE', 'LICENSE-RandomX'),
                             ('rtl/aes/vendor/secworks/LICENSE', 'LICENSE-secworks'), (V + 'LICENSE', 'LICENSE-HardFloat'),
                             ('rtl/hash/vendor/blake2/LICENSE', 'LICENSE-BLAKE2')]:
            shutil.copyfile(ROOT / source, out / name)
        compat = compile_view(ROOT / V / 'divSqrtRecFN_small.v', out)
        extract(out)
        virtual = (ROOT / 'vendor/randomx/src/virtual_machine.cpp').read_text()
        notice = virtual[:virtual.index('*/') + 2] + '\n'
        bodies = {'pinned_program_initialize.inc': function(virtual, 'void randomx_vm::initialize()', True),
                  'pinned_program_float_helpers.inc': 'namespace randomx {\n' + '\n'.join(function(virtual, name)
                    for name in ['static inline uint64_t getSmallPositiveFloatBits(',
                                 'static inline uint64_t getStaticExponent(', 'static inline uint64_t getFloatMask(']) + '\n}\n'}
        for name, body in bodies.items():
            (out / name).write_text(notice + body)
        save(out / 'program-extraction.json', {'source_sha256': sha(ROOT / 'vendor/randomx/src/virtual_machine.cpp'),
                                               'generated': {name: sha(out / name) for name in bodies}})
        if args.native_library:
            library = args.native_library.resolve()
            summary['native_library'] = reused_library(library, args.native_build_execution.resolve(), ROOT)
        else:
            build = out / 'native-library'
            run('configure-native-library', ['cmake', '-S', 'vendor/randomx', '-B', str(build),
                                             '-DCMAKE_BUILD_TYPE=Release', '-DARCH=native', '-DCMAKE_POSITION_INDEPENDENT_CODE=ON'])
            run('build-native-library', ['cmake', '--build', str(build), '--parallel', '6'])
            library = build / 'librandomx.a'
            summary['native_library'] = {'library': str(library), 'sha256': sha(library), 'fresh_pinned_build': True}
        native_includes = ['-I' + str(out), '-Ivendor/randomx/src', '-Irtl/execute/tests', '-I' + TEST]
        run('compile-reference', ['g++', '-std=c++17', '-O2', *native_includes, TEST + 'lifecycle_reference.cpp',
                                  str(library), '-pthread', '-ldl', '-o', str(out / 'reference')])
        backend_env = None
        if args.backend == 'icarus':
            cflags = subprocess.check_output(['iverilog-vpi', '--cflags'], text=True).split()
            vpi_include = [flag for flag in cflags if flag.startswith('-I')]
            assert vpi_include
            run('compile-vpi', ['g++', '-std=c++17', '-O2', '-fPIC', '-shared', *vpi_include, *native_includes,
                                TEST + 'lifecycle_source_vpi.cpp', str(library), '-pthread', '-ldl', '-o', str(out / 'lifecycle_source.vpi')])
        else:
            toolroot = args.verilator_root.resolve()
            toolreceipt = json.loads((args.verilator_build_execution / 'receipt.json').read_text())
            assert toolreceipt['process']['returncode'] == 0
            for executable in (toolroot / 'bin/verilator', toolroot / 'bin/verilator_bin'):
                row = next(item for item in toolreceipt['artifacts'] if Path(item['path']) == executable)
                assert row['sha256'] == sha(executable)
            backend_env = dict(os.environ, VERILATOR_ROOT=str(toolroot))
            summary['tools']['verilator'] = {'root': str(toolroot), 'binary_sha256': sha(toolroot / 'bin/verilator_bin'),
                'receipt_sha256': sha(args.verilator_build_execution / 'receipt.json'),
                'version': subprocess.check_output([str(toolroot / 'bin/verilator'), '--version'], env=backend_env, text=True)}
        gold = out / 'native-reference'
        gold.mkdir()
        run('native-reference', [str(out / 'reference'), str(gold), str(args.programs), str(args.iterations), '1', message.hex()])
        corpus = prepare_assertions(gold)
        summary['native_reference'] = corpus
        summary['canonical_reference'] = json.loads((gold / 'full-reference.json').read_text())
        native_counts = json.loads((gold / 'oracle-summary.json').read_text())
        assert summary['canonical_reference']['canonical_randomx_calculate_hash_verified'] == (args.programs == 8 and args.iterations == 2048)
        includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE', '-Irtl/hash/vendor/blake2', '-I' + str(gold)]

        def profile(prepared, stalled, cancellation=0, error_port=0, capacity=0):
            name = ('prepared' if prepared else 'baseline') + ('-stalled' if stalled else '-ideal')
            if cancellation:
                name += '-cancel-' + str(cancellation)
            if error_port:
                name += '-error-' + str(error_port)
            if capacity:
                name += '-capacity'
            parameters = {'PROGRAMS': args.programs, 'ITERATIONS': args.iterations, 'PREPARED_RCP': prepared,
                          'EVENT_TRACE': int(args.event_trace), 'STALL': stalled, 'CANCEL_PHASE': cancellation,
                          'ERROR_PORT': error_port, 'CAPACITY_TEST': capacity}
            if args.backend == 'icarus':
                binary = out / (name + '.vvp')
                run('compile-' + name, ['iverilog', '-g2012', '-Wall', *includes, '-s', 'tb_prepared_hash_lifecycle',
                     *['-Ptb_prepared_hash_lifecycle.' + key + '=' + str(value) for key, value in parameters.items()],
                     '-o', str(binary), *sources, TEST + 'tb_prepared_hash_lifecycle.v'])
                simulator = ['vvp', '-M' + str(out), '-mlifecycle_source', str(binary)]
            else:
                directory = out / ('obj-' + name)
                cppflags = '-std=c++20 -O2 ' + ' '.join('-I' + str(ROOT / path) for path in
                    ('vendor/randomx/src', 'rtl/execute/tests', 'rtl/hash/tests'))
                run('compile-' + name, [str(toolroot / 'bin/verilator'), '--binary', '--timing', '-j', '6', '-Wno-fatal',
                    '-MAKEFLAGS', 'OPT_FAST=-O3',
                    '--top-module', 'tb_prepared_hash_lifecycle', '--Mdir', str(directory), '-o', 'sim',
                    *includes, *['-G' + key + '=' + str(value) for key, value in parameters.items()],
                    '-CFLAGS', cppflags, '-LDFLAGS', str(library) + ' -pthread -ldl',
                    *sources, TEST + 'tb_prepared_hash_lifecycle.v', str(ROOT / TEST / 'lifecycle_source_dpi.cpp')], env=backend_env)
                simulator = [str(directory / 'sim')]
            if args.compile_only:
                return
            directory = out / name
            directory.mkdir()
            run(name, [*simulator, '+directory=' + str(gold),
                       '+output=' + str(directory), '+input=' + format(int.from_bytes(message, 'little'), 'x'),
                       '+input_bytes=' + str(len(message))], env=backend_env)
            records = [line for line in (out / (name + '.log')).read_text().splitlines() if line.startswith('PASS ')]
            assert len(records) == 1
            if capacity:
                assert records[0].startswith('PASS lifecycle_capacity programs=' + str(args.programs) + ' ')
                summary['capacity_checks'][name] = records[0]
            elif error_port:
                assert records[0].startswith('PASS lifecycle_matching_error port=' + str(error_port) + ' ')
                summary['matching_errors'][name] = records[0]
            elif cancellation:
                assert records[0].startswith('PASS lifecycle_cancel phase=' + str(cancellation) + ' ')
                summary['cancellation'][name] = records[0]
            else:
                assert records[0].startswith('PASS prepared_hash_lifecycle ')
                ledger = json.loads((directory / 'ledger.json').read_text())
                provider = json.loads((directory / 'provider-host-time.json').read_text())
                validate_ledger(ledger, provider, args.iterations, args.programs, native_counts, prepared)
                summary['profiles'][name] = {'record': records[0], 'ledger': ledger, 'host_provider': provider,
                                             'trace_sha256': sha(directory / 'trace.csv')}

        if not args.interfaces_only:
            for stalled in [int(name == 'stalled') for name in args.profiles]:
                for prepared in [int(name == 'prepared') for name in args.variants]:
                    profile(prepared, stalled)
        if args.cancellation and not args.compile_only:
            for phase in range(1, 7):
                profile(1, 1, phase)
        if args.matching_errors and not args.compile_only:
            for error_port in range(1, 9):
                profile(1, 1, error_port=error_port)
        if args.capacity_checks and not args.compile_only:
            profile(1, 0, capacity=1)
        for mode in args.profiles:
            if args.compile_only or args.interfaces_only or len(args.variants) != 2:
                continue
            baseline = summary['profiles']['baseline-' + mode]['ledger']
            prepared = summary['profiles']['prepared-' + mode]['ledger']
            summary['paired_cycle_comparisons'][mode] = compare_variants(baseline, prepared, native_counts)
        summary['balanced_variant_cycle_comparison'] = bool(summary['paired_cycle_comparisons'])
        assert all(sha(ROOT / name) == value for name, value in hashes.items()), 'source changed during execution'
        assert sha(library) == summary['native_library']['sha256']
        summary['status'] = ('compile_only' if args.compile_only else
                             'pass_lifecycle_interfaces' if args.interfaces_only else 'pass_connected_native_reference')
        summary['source_unchanged_after_run'] = True
        summary['boundary'] = ('Software input BLAKE2b, scratchpad AES fill, AES program generation and pinned native light dataset provider; '
                               f'hardware scratchpad transport, immutable preparation, execution, {args.programs - 1} interprogram hashes, finalizer/digest. '
                               'Provider host seconds are separate. No complete ASIC, physical DRAM timing, MHz or watts claim.')
        save(out / 'summary.json', summary)
        print(json.dumps({'status': summary['status'], 'profiles': len(summary['profiles']),
                          'cancellation': len(summary['cancellation']), 'matching_errors': len(summary['matching_errors']),
                          'capacity_checks': len(summary['capacity_checks']),
                          'full_v2': args.full_v2}), flush=True)
    except Exception as error:
        save(out / 'failure.json', {'type': type(error).__name__, 'error': str(error),
                                    'completed_profiles': list(summary['profiles']), 'unfinished_not_passed': True})
        raise
    finally:
        save(out / 'commands.json', commands)
        save(out / 'artifacts.sha256.json', {str(path.relative_to(out)): sha(path)
            for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
