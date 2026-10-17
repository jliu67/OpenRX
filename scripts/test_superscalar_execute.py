#!/usr/bin/env python3
"""Admitted, bounded native superscalar differential and optional mapped checks.

Run only inside the caller's admitted global execution slot. Default performs
native fixture generation and RTL correctness first. --synthesize adds mapping
after correctness; --synthesize-only reuses an independently verified prior run
through exact receipt bindings and performs no native/correctness regeneration.
No Argon/cache/dataset allocation or whole-hash/physical performance claim.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]
TOP = 'randomx_superscalar_execute'
BENCH_TOP = 'tb_superscalar_execute'
RTL = ['rtl/execute/randomx_mul64.v', 'rtl/execute/' + TOP + '.v']
BENCH = 'rtl/execute/tests/' + BENCH_TOP + '.v'
ORACLE = 'rtl/execute/tests/superscalar_oracle.cpp'
DRIVER = 'scripts/test_superscalar_execute.py'
PIN = 'aaafe71322df6602c21a5c72937ac284724ae561'
PIN_MANIFEST = '2763c092b465bb99d71d544915b9fd847064ec195cc438c6370c34ecdf9b746d'
PIN_LOCK = '2c210a233afaedd668463647d25da27f9ffdb7235e53248f91c6f78c7943e3cd'
RETAINED_LIBRARY_SHA = 'bddb3f9a206b1ec34ca78d3a9b13a9388d7312d6660b7d148d4ed514958fb8d6'
NATIVE = ['superscalar.cpp', 'blake2_generator.cpp', 'instructions_portable.cpp',
          'reciprocal.c', 'blake2/blake2b.c']
NAMES = ['ISUB_R', 'IXOR_R', 'IADD_RS', 'IMUL_R', 'IROR_C', 'IADD_C7',
         'IXOR_C7', 'IADD_C8', 'IXOR_C8', 'IADD_C9', 'IXOR_C9', 'IMULH_R',
         'ISMULH_R', 'IMUL_RCP']
REG_SOURCE = {0, 1, 2, 3, 11, 12}
MULTIPLY = {3, 11, 12, 13}
CONTROLS = ['stalled', 'held', 'malformed', 'stale', 'cancel', 'reset']


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def resource_metadata(path):
    text, result = path.read_text(), {}
    for key, pattern, convert in [
        ('peak_rss_kib', r'Maximum resident set size \(kbytes\):\s*(\d+)', int),
        ('user_seconds', r'User time \(seconds\):\s*([0-9.]+)', float),
        ('system_seconds', r'System time \(seconds\):\s*([0-9.]+)', float),
        ('cpu_percent', r'Percent of CPU this job got:\s*([0-9.]+)%', float),
    ]:
        match = re.search(pattern, text)
        if match:
            result[key] = convert(match[1])
    return result


def provenance_library(library, execution):
    """Actual retained archive/build/source bindings, without rebuilding it."""
    receipt, manifest = load(execution / 'receipt.json'), load(execution / 'manifest.json')
    assert receipt['process']['returncode'] == 0
    artifacts = {Path(row['path']): row for row in receipt['artifacts']}

    def bound(path):
        row = artifacts[path]
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']

    bound(library)
    assert sha(library) == RETAINED_LIBRARY_SHA, 'different archive; use pinned source fallback instead'
    bound(execution / 'manifest.json')
    native = [row for source in manifest['sources'] for row in source['files']
              if row['relative'].startswith('vendor/randomx/')]
    assert native and all(sha(ROOT / row['relative']) == row['sha256'] for row in native)
    build = library.parent.parent / 'build.json'
    flags = library.parent / 'CMakeFiles/randomx.dir/flags.make'
    bound(build)
    bound(flags)
    data = load(build)
    assert data['status'] == 'built' and data['artifacts']['randomx/librandomx.a'] == sha(library)
    return {'library': str(library), 'sha256': sha(library), 'native_source_files_verified': len(native),
            'execution': str(execution), 'manifest_sha256': sha(execution / 'manifest.json'),
            'receipt_sha256': sha(execution / 'receipt.json'), 'build_sha256': sha(build),
            'flags_sha256': sha(flags), 'archive_rebuilt_or_modified': False}


def corpus(fixtures):
    """Validate representation/coverage. Native executeSuperscalar supplies gold."""
    tables = {}
    for line in (fixtures / 'tables.hex').read_text().splitlines():
        group, index, divisor, value = line.split()
        key = int(group), int(index)
        assert key not in tables
        tables[key] = int(divisor, 16), int(value, 16)
    cases, counts, shifts, rotations, indices = {}, Counter(), set(), set(), set()
    aliases, ignored, signs = Counter(), Counter(), set()
    for line in (fixtures / 'cases.hex').read_text().splitlines():
        case, size, address, table_count, initial, final = line.split()
        case, size, address, table_count = map(int, (case, size, address, table_count))
        assert case not in cases and 0 <= size <= 512 and 0 <= address < 8
        assert len(initial) == len(final) == 128
        int(initial, 16); int(final, 16)
        directory = fixtures / f'case-{case:03d}'
        metadata = load(directory / 'metadata.json')
        group = metadata['table_id']
        rows = {name: (directory / name).read_text().splitlines() for name in
                ['programs.mem', 'original-programs.mem', 'steps.mem',
                 'rcp-valid.mem', 'rcp-index.mem', 'reciprocals.mem']}
        assert all(len(values) == size for values in rows.values())
        assert (directory / 'initial.hex').read_text().strip() == initial
        assert (directory / 'final.hex').read_text().strip() == final
        assert sum(g == group for g, _ in tables) == table_count
        opcounts = Counter()
        before = int(initial, 16)
        for pc in range(size):
            raw = int(rows['programs.mem'][pc], 16)
            original = int(rows['original-programs.mem'][pc], 16)
            state = int(rows['steps.mem'][pc], 16)
            assert len(rows['programs.mem'][pc]) == 16 and len(rows['steps.mem'][pc]) == 128
            assert state < 1 << 512
            op, dst, src, mod, imm = raw & 255, raw >> 8 & 255, raw >> 16 & 255, raw >> 24 & 255, raw >> 32
            assert op < 14 and dst < 8 and (op not in REG_SOURCE or src < 8)
            assert op != 4 or imm <= 63
            valid = int(rows['rcp-valid.mem'][pc], 16)
            index = int(rows['rcp-index.mem'][pc], 16)
            value = int(rows['reciprocals.mem'][pc], 16)
            assert valid == (op == 13)
            if valid:
                assert index == imm < table_count
                divisor, expected = tables[group, index]
                assert value == expected and original >> 32 == divisor
                assert raw & 0xffffffff == original & 0xffffffff
                indices.add(index)
            else:
                assert index == value == 0 and raw == original
            counts[NAMES[op]] += 1
            opcounts[NAMES[op]] += 1
            if op in REG_SOURCE:
                aliases[NAMES[op]] += dst == src
            else:
                ignored[NAMES[op]] += src == 255
            if op == 2:
                shifts.add(mod >> 2 & 3)
            if op == 4:
                rotations.add(imm)
            if op in [5, 6, 7, 8, 9, 10]:
                signs.add(imm >> 31)
            before = state
        assert before == int(final, 16)
        cases[case] = {'count': size, 'address_reg': address, 'table_count': table_count,
                       'opcounts': dict(opcounts), 'muls': sum(opcounts[NAMES[op]] for op in MULTIPLY),
                       'initial': initial, 'final': final, 'kind': metadata['kind']}
    assert set(cases) == set(range(130))
    assert cases[128]['count'] == 512 and cases[129]['count'] == 0
    assert all(cases[i]['count'] > 0 and cases[i]['kind'] == 'native-generated-complete' for i in range(16))
    assert set(counts) == set(NAMES) and shifts == set(range(4)) and {0, 63} <= rotations
    assert {0, 1, 2, 4, 511, 512, 513, 65537} <= indices and signs == {0, 1}
    assert all(aliases[name] > 0 for name in [NAMES[op] for op in REG_SOURCE])
    assert all(ignored[name] > 0 for name in [NAMES[op] for op in set(range(14)) - REG_SOURCE])
    sets = {}
    for name, expected in [('cases.hex', set(range(130))), ('cases-mapped.hex', {0, 8, *range(16, 130)}),
                           ('cases-control.hex', {0, 8})]:
        lines = (fixtures / name).read_text().splitlines()
        ids = [int(line.split()[0]) for line in lines]
        assert len(ids) == len(set(ids)) and set(ids) == expected
        assert all(line in (fixtures / 'cases.hex').read_text().splitlines() for line in lines)
        sets[name] = ids
    native = load(fixtures / 'native-summary.json')
    assert native['cases'] == 130 and native['mapped_cases'] == 116 and native['control_cases'] == 2
    assert native['singleton_full_native_agree'] and native['prepared_raw_native_agree']
    assert native['post_instruction_steps'] == sum(row['count'] for row in cases.values())
    assert native['opcounts'] == dict(counts) and not native['cache_allocation']
    assert native['argon_calls'] == native['dataset_calls'] == 0
    return native, cases, sets, {'cases': len(cases), 'generated_complete_programs': 16,
        'crafted_max_count': 512, 'empty_programs': 1, 'native_retirements': sum(row['count'] for row in cases.values()),
        'opcounts': dict(counts), 'register_aliases': dict(aliases), 'ignored_src255': dict(ignored),
        'shifts': sorted(shifts), 'rotations': sorted(rotations), 'sign_immediate_classes': sorted(signs),
        'reciprocal_indices': sorted(indices), 'largest_index': max(indices),
        'reciprocal_table_entries': len(tables), 'oracle': 'unchanged pinned executeSuperscalar; no Python arithmetic golden'}


def reused_fixtures(args, fixtures, inputs):
    receipt_path = args.validated_receipt.resolve()
    assert sha(receipt_path) == args.validated_receipt_sha256
    receipt, verify = load(receipt_path), load(args.validated_verify.resolve())
    assert receipt['process']['returncode'] == 0 and receipt['status'] == 'PROCESS_EXITED'
    assert verify['integrity_verified'] and verify['status'] == 'PROCESS_EXITED'
    assert verify['execution_id'] == receipt['execution_id']
    artifacts = {Path(row['path']): row for row in receipt['artifacts']}

    def bound(path):
        row = artifacts[path]
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']

    prior = args.validated_out.resolve()
    for name in ['summary.json', 'inputs.json', 'fixtures.sha256.json', 'coverage.json']:
        bound(prior / name)
    summary = load(prior / 'summary.json')
    assert summary['status'] in ['pass_correctness', 'pass'] and summary['correctness_completed']
    assert load(prior / 'inputs.json') == inputs
    hashes = load(prior / 'fixtures.sha256.json')
    actual = {str(path.relative_to(prior / 'fixtures')): sha(path)
              for path in sorted((prior / 'fixtures').rglob('*')) if path.is_file()}
    assert actual == hashes
    for relative in hashes:
        bound(prior / 'fixtures' / relative)
    shutil.copytree(prior / 'fixtures', fixtures)
    assert {str(path.relative_to(fixtures)): sha(path) for path in sorted(fixtures.rglob('*')) if path.is_file()} == hashes
    return summary, {'prior_output': str(prior), 'receipt_sha256': sha(receipt_path),
        'root_verify_sha256': sha(args.validated_verify.resolve()), 'fixture_files_receipt_verified': len(hashes),
        'actual_prior_summary_sha256': sha(prior / 'summary.json'), 'source_inputs_byte_equal': True,
        'native_or_completed_rtl_regenerated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', '--output', dest='out', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    parser.add_argument('--synthesize-only', action='store_true')
    parser.add_argument('--validated-out', type=Path)
    parser.add_argument('--validated-receipt', type=Path)
    parser.add_argument('--validated-receipt-sha256')
    parser.add_argument('--validated-verify', type=Path)
    parser.add_argument('--native-library', type=Path)
    parser.add_argument('--native-build-execution', type=Path)
    parser.add_argument('--jobs', type=int, default=6, help='independent simulator processes within one admitted payload (1..6)')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 6:
        parser.error('--jobs must be1..6')
    reuse = [args.validated_out, args.validated_receipt, args.validated_receipt_sha256, args.validated_verify]
    if args.synthesize_only != all(bool(x) for x in reuse) or (any(reuse) and not all(reuse)):
        parser.error('--synthesize-only requires all four --validated-* bindings; they apply only to reuse')
    if args.synthesize and args.synthesize_only:
        parser.error('choose full --synthesize or reuse --synthesize-only')
    if bool(args.native_library) != bool(args.native_build_execution) or (args.synthesize_only and args.native_library):
        parser.error('both native reuse flags are required together and only for correctness')
    out = args.out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents or not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('fresh unambiguous output path outside source required; preserve all previous attempts')
    needed = ['iverilog', 'vvp'] + ([] if args.synthesize_only else ['g++'])
    if args.synthesize or args.synthesize_only:
        needed += ['yosys']
    tools = {name: Path(shutil.which(name)).resolve() for name in needed if shutil.which(name)}
    if len(tools) != len(needed) or not Path('/usr/bin/time').is_file():
        parser.error('required compiler/simulator/resource tool unavailable')
    out.mkdir(parents=True)
    commands, records = [], {}
    command_lock, record_lock = Lock(), Lock()
    summary = {'status': 'running', 'correctness_completed': False, 'rtl': {}, 'mapped': {}, 'mapping': {},
        'mode_parallelism': args.jobs, 'parallelism_scope': 'Independent simulations only; immutable fixtures and separate logs/results. Native compilation/generation and synthesis are sequential phases.',
        'scope': 'One externally prepared native superscalar program; host program/table preparation remains external. '
                 'No cache/Argon/dataset allocation, full-hash performance, physical PPA or architecture selection.',
        'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}

    def run(label, argv, timeout=1800):
        row = {'label': label, 'argv': [str(x) for x in argv], 'cwd': str(ROOT), 'timeout_seconds': timeout}
        with command_lock:
            commands.append(row)
        print('START ' + label, flush=True)
        began = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                result = subprocess.run(['/usr/bin/time', '-v', '-o', str(out / (label + '.time.txt')),
                    *row['argv']], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            with command_lock:
                row['returncode'] = result.returncode
            result.check_returncode()
        except Exception as error:
            with command_lock:
                row['error'] = str(error)
            raise
        finally:
            resource = out / (label + '.time.txt')
            with command_lock:
                row['elapsed_seconds'] = time.monotonic() - began
                if resource.is_file():
                    row['resources'] = resource_metadata(resource)
                temporary = out / 'commands.json.tmp'
                save(temporary, commands)
                temporary.replace(out / 'commands.json')
        print('PASS ' + label, flush=True)

    def compile_bench(label, radix4=1, netlist=None, cells=None):
        executable = out / (label + '.vvp')
        sources = [str(netlist), str(cells)] if netlist else RTL
        argv = [str(tools['iverilog']), '-g2012', '-Wall', '-s', BENCH_TOP,
                '-P' + BENCH_TOP + '.MUL_RADIX4=' + str(radix4), '-o', str(executable)]
        if netlist:
            argv += ['-DSUPERSCALAR_NETLIST']
        run('compile-' + label, [*argv, *sources, BENCH])
        return executable

    def simulate(label, executable, mode, selection='cases-control.hex', reference=None, radix4=1):
        result_path = out / (label + '-latencies.hex')
        run(label, [str(tools['vvp']), str(executable), '+DIR=' + str(out / 'fixtures'),
                   '+CASES=' + selection, '+MODE=' + mode, '+RESULTS=' + str(result_path)])
        lines = (out / (label + '.log')).read_text().splitlines()
        passes = [line for line in lines if line.startswith('PASS ')]
        assert len(passes) == 1 and passes[0].startswith('PASS superscalar_execute ')
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines)
        record = passes[0]
        if reference:
            with record_lock:
                assert record == records[reference], (label, record, records[reference])
        fields = {key: int(value) for key, value in re.findall(r'(\w+)=(-?\d+)', record)}
        measured = []
        if mode in ['corpus', 'stalled']:
            assert result_path.is_file(), 'missing per-completed-program measured latency records'
            for line in result_path.read_text().splitlines():
                case, retired, muls, cycles = map(int, line.split())
                assert case in cases and retired == cases[case]['count'] and muls == cases[case]['muls']
                assert cycles >= 0 and (retired == 0 or cycles > 0)
                if retired == 0:
                    assert cycles == 0
                if mode == 'corpus':
                    assert cycles == 3 * retired + (34 if radix4 else 2) * muls
                measured.append({'case': case, 'retired': retired, 'muls': muls, 'cycles': cycles})
            assert [row['case'] for row in measured] == selections[selection]
            assert fields['cases'] == fields['completed'] == len(measured)
            assert fields['retired'] == sum(row['retired'] for row in measured)
            assert fields['muls'] == sum(row['muls'] for row in measured)
            assert fields['cycles'] == sum(row['cycles'] for row in measured)
            assert fields['errors'] == fields['aborts'] == 0
        with record_lock:
            records[label] = record
        return {'record': record, 'mode': mode, 'selection': selection, **fields, 'program_measurements': measured}

    def simulation_batch(specifications):
        """Join every submitted mode before reporting failures; preserve all logs."""
        results, failures = {}, []
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            pending = [(row['label'], pool.submit(simulate, **row)) for row in specifications]
            for label, future in pending:
                try:
                    results[label] = future.result()
                except Exception as error:
                    failures.append((label, str(error)))
        if failures:
            summary.setdefault('completed_modes_before_batch_failure', {}).update(results)
            summary['batch_failures'] = failures
            raise RuntimeError('simulation batch failed after all futures joined: ' + repr(failures))
        return results

    try:
        assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
        assert sha(ROOT / 'vendor/randomx.lock.json') == PIN_LOCK
        assert sha(ROOT / 'vendor/randomx.sha256.json') == PIN_MANIFEST
        lock = load(ROOT / 'vendor/randomx.lock.json')
        assert lock['commit'] == PIN and lock['tag'] == 'v2.0.1'
        manifest = load(ROOT / 'vendor/randomx.sha256.json')
        assert {str(p.relative_to(ROOT / 'vendor/randomx')): sha(p)
                for p in sorted((ROOT / 'vendor/randomx').rglob('*')) if p.is_file()} == manifest
        bound = {*RTL, BENCH, ORACLE, DRIVER, 'vendor/randomx.lock.json', 'vendor/randomx.sha256.json'}
        bound.update('vendor/randomx/' + name for name in manifest)
        inputs = {name: sha(ROOT / name) for name in sorted(bound)}
        save(out / 'inputs.json', inputs)
        metadata = {}
        for name, path in tools.items():
            result = subprocess.run([str(path), '-V' if name in ['iverilog', 'vvp', 'yosys'] else '--version'], capture_output=True, text=True)
            metadata[name] = {'path': str(path), 'sha256': sha(path), 'version_returncode': result.returncode,
                              'version_stdout': result.stdout, 'version_stderr': result.stderr}
        save(out / 'tools.json', metadata)
        shutil.copyfile(ROOT / 'vendor/randomx/LICENSE', out / 'LICENSE-RandomX')
        fixtures = out / 'fixtures'
        if args.synthesize_only:
            prior, summary['validated_reuse'] = reused_fixtures(args, fixtures, inputs)
            summary['prior_correctness'] = {'summary_status': prior['status'], 'rtl': prior['rtl']}
            # Exact prior PASS strings are receipt-bound through summary.json.
            records.update({label: row['record'] for label, row in prior['rtl'].items()})
        else:
            fixtures.mkdir()
            native = [ORACLE]
            if args.native_library:
                library = args.native_library.resolve()
                summary['native_library'] = provenance_library(library, args.native_build_execution.resolve())
                native += [str(library)]
            else:
                native += ['vendor/randomx/src/' + name for name in NATIVE]
                summary['native_library'] = {'fallback': 'compile five unchanged pinned native translation units; no cache build'}
            executable = out / 'superscalar-oracle'
            run('compile-native-oracle', [str(tools['g++']), '-O2', '-std=c++17', '-Wall', '-Wextra',
                '-Ivendor/randomx/src', *native, '-pthread', '-o', str(executable)])
            run('native-oracle', [str(executable), str(fixtures)])
        native, cases, selections, coverage = corpus(fixtures)
        save(out / 'native-corpus.json', native)
        save(out / 'coverage.json', coverage)
        fixture_hashes = {str(p.relative_to(fixtures)): sha(p) for p in sorted(fixtures.rglob('*')) if p.is_file()}
        save(out / 'fixtures.sha256.json', fixture_hashes)
        if not args.synthesize_only:
            executable = compile_bench('rtl')
            baseline = compile_bench('rtl-radix0', radix4=0)
            specifications = []
            for label, mode, selection in [('rtl-corpus', 'corpus', 'cases.hex'),
                    ('rtl-mapped-corpus', 'corpus', 'cases-mapped.hex'),
                    *[('rtl-' + mode, mode, 'cases-control.hex') for mode in [*CONTROLS, 'exhaustion']]]:
                specifications.append({'label': label, 'executable': executable, 'mode': mode, 'selection': selection})
            specifications.append({'label': 'rtl-radix0-corpus', 'executable': baseline, 'mode': 'corpus',
                                   'selection': 'cases-mapped.hex', 'radix4': 0})
            summary['rtl'] = simulation_batch(specifications)
            summary['correctness_completed'] = True
        else:
            summary['correctness_completed'] = True
        if args.synthesize or args.synthesize_only:
            netlist = out / 'netlist-superscalar.v'
            script = 'read_verilog ' + ' '.join(RTL) + '; '
            script += f'synth -top {TOP} -flatten; check -assert; tee -o {out}/stat-superscalar.txt stat; '
            script += f'write_verilog -noattr {netlist}; write_json {out}/netlist-superscalar.json'
            run('synth-superscalar', [str(tools['yosys']), '-p', script], timeout=3600)
            module = load(out / 'netlist-superscalar.json')['modules'][TOP]
            kinds = Counter(row['type'] for row in module['cells'].values())
            cells = int(re.search(r'Number of cells:\s*(\d+)', (out / 'stat-superscalar.txt').read_text())[1])
            assert cells == sum(kinds.values())
            summary['mapping'] = {'top': TOP, 'MUL_RADIX4': 1, 'num_cells': cells,
                'flop_cells': sum(n for kind, n in kinds.items() if 'DFF' in kind),
                'latch_cells': sum(n for kind, n in kinds.items() if 'LATCH' in kind),
                'num_cells_by_type': dict(sorted(kinds.items())),
                'scope': 'Actual prepared program executor and multiplier; excludes external program/table generation/service and cache/dataset/physical implementation.'}
            assert summary['mapping']['latch_cells'] == 0
            installed = Path('/usr/share/yosys/simcells.v')
            cells_model = out / 'yosys-simcells.v'
            shutil.copyfile(installed, cells_model)
            save(out / 'yosys-cell-model.json', {'installed_path': str(installed), 'sha256': sha(installed), 'copied_sha256': sha(cells_model)})
            executable = compile_bench('mapped', netlist=netlist, cells=cells_model)
            specifications = [{'label': 'mapped-corpus', 'executable': executable, 'mode': 'corpus',
                               'selection': 'cases-mapped.hex', 'reference': 'rtl-mapped-corpus'}]
            specifications.extend({'label': 'mapped-' + mode, 'executable': executable,
                                   'mode': mode, 'reference': 'rtl-' + mode} for mode in CONTROLS)
            summary['mapped'] = simulation_batch(specifications)
        summary['native_cases'] = len(cases)
        summary['native_retirements'] = coverage['native_retirements']
        summary['rtl_modes_newly_executed'] = len(summary['rtl'])
        summary['mapped_modes_newly_executed'] = len(summary['mapped'])
        assert len(summary['rtl']) == (0 if args.synthesize_only else 10)
        assert len(summary['mapped']) == (7 if args.synthesize or args.synthesize_only else 0)
        summary['source_unchanged_after_run'] = all(sha(ROOT / name) == value for name, value in inputs.items())
        summary['fixtures_unchanged_after_run'] = all(sha(fixtures / name) == value for name, value in fixture_hashes.items())
        assert summary['source_unchanged_after_run'] and summary['fixtures_unchanged_after_run']
        summary['status'] = 'pass' if args.synthesize or args.synthesize_only else 'pass_correctness'
        print('PASS superscalar_suite native_cases=130 mapped_cases=116 rtl_modes=' + str(len(summary['rtl']))
              + ' mapped_modes=' + str(len(summary['mapped'])), flush=True)
    except Exception as error:
        summary['status'] = 'failed'
        summary['error'] = str(error)
        raise
    finally:
        save(out / 'summary.json', summary)
        save(out / 'artifacts.sha256.json', {str(p.relative_to(out)): sha(p)
            for p in sorted(out.rglob('*')) if p.is_file() and p != out / 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
