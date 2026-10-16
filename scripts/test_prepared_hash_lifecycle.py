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


def validate_ledger(ledger, provider, iterations, programs):
    assert type(ledger['cycles']) is int and ledger['cycles'] > 0
    assert all(type(value) is int and value >= 0 for value in ledger['stage_cycles'].values())
    assert len(ledger['nested_iteration_phases']) == 12 and len(ledger['nested_finalization_phases']) == 6
    assert all(type(value) is int and value >= 0 for value in
               ledger['nested_iteration_phases'] + ledger['nested_finalization_phases'])
    assert sum(ledger['stage_cycles'].values()) == ledger['cycles']
    assert sum(ledger['nested_iteration_phases']) == ledger['stage_cycles']['execution']
    assert sum(ledger['nested_finalization_phases']) == ledger['stage_cycles']['finalization']
    assert ledger['scratchpad_bytes'] == 2097152
    assert ledger['dataset_logical_bytes'] == programs * iterations * 64
    assert ledger['program_image_load_bytes'] == programs * 384 * 8
    assert ledger['untimed_provider_device_cycles'] is None
    assert provider['provider_device_cycles'] is None
    assert provider['dataset_requests'] == programs * iterations and provider['program_generations'] == programs
    assert provider['cache_bytes'] == 268435456 and provider['logical_dataset_bytes'] == 2181038016
    assert provider['materialized_dataset_bytes'] == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-library', type=Path)
    parser.add_argument('--native-build-execution', type=Path)
    parser.add_argument('--programs', type=int, default=8, choices=range(1, 9))
    parser.add_argument('--iterations', type=int, default=2)
    parser.add_argument('--profiles', nargs='+', choices=['ideal', 'stalled'], default=['ideal', 'stalled'])
    parser.add_argument('--full-v2', action='store_true')
    parser.add_argument('--compile-only', action='store_true')
    parser.add_argument('--cancellation', action='store_true')
    parser.add_argument('--input-hex', default=MESSAGE.hex())
    parser.add_argument('--timeout', type=int, default=10800)
    args = parser.parse_args()
    if len(args.profiles) != len(set(args.profiles)):
        parser.error('duplicate output profiles are not permitted')
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
    out.mkdir()
    commands = []
    summary = {'schema': 'openrx.connected-prepared-v2.v1', 'status': 'pending',
               'base': 'aebe30a0c2d1547fed6b66976ba0757b4b66389a', 'programs': args.programs,
               'iterations': args.iterations, 'full_v2_requested': args.full_v2,
               'compile_only': args.compile_only, 'profiles': {}, 'cancellation': {},
               'input_hex': message.hex(), 'power_watts': None, 'device_frequency_hz': None,
               'physical_area': None, 'whole_machine_efficiency_accepted': False}
    compat = None

    def run(label, argv, timeout=args.timeout):
        if argv[0] == 'iverilog' and compat is not None:
            argv = [str(compat) if item == V + 'divSqrtRecFN_small.v' else item for item in argv]
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout}
        commands.append(row)
        print('START ' + label, flush=True)
        began = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as stream:
                process = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
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
                   *[str(path.relative_to(ROOT)) for path in sorted((ROOT / 'rtl/hash').glob('randomx_*.v'))]]))
        native_sources = [str(path.relative_to(ROOT)) for path in (ROOT / 'vendor/randomx').rglob('*') if path.is_file()]
        inputs = set(sources + native_sources + [TEST + name for name in
                     ['lifecycle_native.hpp', 'lifecycle_source_vpi.cpp', 'lifecycle_reference.cpp', 'tb_prepared_hash_lifecycle.v']])
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'scripts').glob('*.py'))
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'rtl/hash/vendor/blake2').glob('*.v'))
        inputs.update(str(path.relative_to(ROOT)) for path in (ROOT / 'rtl').rglob('*')
                      if path.is_file() and (path.suffix in ('.vh', '.vi') or path.name in ('LICENSE', 'manifest.json', 'UPSTREAM.json')))
        inputs.update(['rtl/execute/tests/program_native_helpers.hpp', 'vendor/randomx.sha256.json', 'vendor/randomx.lock.json'])
        hashes = {name: sha(ROOT / name) for name in sorted(inputs)}
        save(out / 'inputs.json', hashes)
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
        cflags = subprocess.check_output(['iverilog-vpi', '--cflags'], text=True).split()
        vpi_include = [flag for flag in cflags if flag.startswith('-I')]
        assert vpi_include
        run('compile-vpi', ['g++', '-std=c++17', '-O2', '-fPIC', '-shared', *vpi_include, *native_includes,
                            TEST + 'lifecycle_source_vpi.cpp', str(library), '-pthread', '-ldl', '-o', str(out / 'lifecycle_source.vpi')])
        gold = out / 'native-reference'
        gold.mkdir()
        run('native-reference', [str(out / 'reference'), str(gold), str(args.programs), str(args.iterations), '1', message.hex()])
        corpus = prepare_assertions(gold)
        summary['native_reference'] = corpus
        summary['canonical_reference'] = json.loads((gold / 'full-reference.json').read_text())
        assert summary['canonical_reference']['canonical_randomx_calculate_hash_verified'] == (args.programs == 8 and args.iterations == 2048)
        includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE', '-Irtl/hash/vendor/blake2', '-I' + str(gold)]

        def profile(prepared, stalled, cancellation=0):
            name = ('prepared' if prepared else 'baseline') + ('-stalled' if stalled else '-ideal')
            if cancellation:
                name += '-cancel-' + str(cancellation)
            binary = out / (name + '.vvp')
            run('compile-' + name, ['iverilog', '-g2012', '-Wall', *includes, '-s', 'tb_prepared_hash_lifecycle',
                 '-Ptb_prepared_hash_lifecycle.PROGRAMS=' + str(args.programs),
                 '-Ptb_prepared_hash_lifecycle.ITERATIONS=' + str(args.iterations),
                 '-Ptb_prepared_hash_lifecycle.PREPARED_RCP=' + str(prepared),
                 '-Ptb_prepared_hash_lifecycle.STALL=' + str(stalled),
                 '-Ptb_prepared_hash_lifecycle.CANCEL_PHASE=' + str(cancellation), '-o', str(binary),
                 *sources, TEST + 'tb_prepared_hash_lifecycle.v'])
            if args.compile_only:
                return
            directory = out / name
            directory.mkdir()
            run(name, ['vvp', '-M' + str(out), '-mlifecycle_source', str(binary), '+directory=' + str(gold),
                       '+output=' + str(directory), '+input=' + format(int.from_bytes(message, 'little'), 'x'),
                       '+input_bytes=' + str(len(message))])
            records = [line for line in (out / (name + '.log')).read_text().splitlines() if line.startswith('PASS ')]
            assert len(records) == 1
            if cancellation:
                assert records[0].startswith('PASS lifecycle_cancel phase=' + str(cancellation) + ' ')
                summary['cancellation'][name] = records[0]
            else:
                assert records[0].startswith('PASS prepared_hash_lifecycle ')
                ledger = json.loads((directory / 'ledger.json').read_text())
                provider = json.loads((directory / 'provider-host-time.json').read_text())
                validate_ledger(ledger, provider, args.iterations, args.programs)
                if prepared:
                    assert ledger['runtime_reciprocals'] == 0
                else:
                    assert ledger['preparation_reciprocals'] == 0
                summary['profiles'][name] = {'record': records[0], 'ledger': ledger, 'host_provider': provider,
                                             'trace_sha256': sha(directory / 'trace.csv')}

        for stalled in [int(name == 'stalled') for name in args.profiles]:
            for prepared in (0, 1):
                profile(prepared, stalled)
        if args.cancellation and not args.compile_only:
            for phase in range(1, 7):
                profile(1, 1, phase)
        for mode in args.profiles:
            if args.compile_only:
                continue
            baseline = summary['profiles']['baseline-' + mode]['ledger']
            prepared = summary['profiles']['prepared-' + mode]['ledger']
            assert all(baseline[name] == prepared[name] for name in
                       ['scratchpad_bytes', 'physical_port_read_bytes', 'physical_port_write_bus_bytes',
                        'strobed_write_bytes', 'dataset_logical_bytes', 'logical_bytecode_memory_bytes',
                        'logical_entry_bytes', 'logical_tail_bytes', 'program_image_load_bytes'])
        assert all(sha(ROOT / name) == value for name, value in hashes.items()), 'source changed during execution'
        assert sha(library) == summary['native_library']['sha256']
        summary['status'] = 'compile_only' if args.compile_only else 'pass_connected_native_reference'
        summary['source_unchanged_after_run'] = True
        summary['boundary'] = ('Software input BLAKE2b, scratchpad AES fill, AES program generation and pinned native light dataset provider; '
                               f'hardware scratchpad transport, immutable preparation, execution, {args.programs - 1} interprogram hashes, finalizer/digest. '
                               'Provider host seconds are separate. No complete ASIC, physical DRAM timing, MHz or watts claim.')
        save(out / 'summary.json', summary)
        print(json.dumps({'status': summary['status'], 'profiles': len(summary['profiles']),
                          'cancellation': len(summary['cancellation']), 'full_v2': args.full_v2}), flush=True)
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
