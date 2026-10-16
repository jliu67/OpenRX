#!/usr/bin/env python3
"""Reproduce native four-round program generation and actual generic synthesis.

Run serially inside the caller's admitted local payload. No slot is acquired by
this driver. Full 3200-byte Program images are distinct from bounded mapped
control checks; input hashing, scratchpad fill, execution, dataset generation and
physical PPA remain outside this component's acceptance boundary.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
TOP = 'randomx_program_generation'
TEST = 'rtl/hash/tests/'
AES = ['rtl/aes/vendor/secworks/aes_sbox.v', 'rtl/aes/vendor/secworks/aes_inv_sbox.v',
       'rtl/aes/randomx_aes_round.v']
RTL = [*AES, 'rtl/hash/' + TOP + '.v']
BENCH = TEST + 'tb_program_generation.v'
ORACLE = TEST + 'program_generation_oracle.cpp'
POSTFILL = TEST + 'program_generation_postfill_seed.hex'
PRIOR_FIXTURES = 'docs/validation/initial-scratchpad-fill-20261016/standalone/fixtures.sha256.json'
PRIOR_FIXTURES_SHA = '2350b29960c25ca878fd8f41ecc345785ae7c5fb45cee26a435bc95deb1f833b'
POSTFILL_BINARY_SHA = 'c3f23326844561f9c551f5112ed93294e1903333e689226902501d25a02a7758'
SEEDS = ['zero', 'ones', 'incrementing', 'prng', 'postfill']
SIZES = [64, 256, 3200]
CONTROLS = ['held_response', 'held_request', 'cancel_before', 'reset_before',
            *[kind + '_round' + str(position) for kind in ['cancel', 'reset'] for position in range(4)],
            'cancel_return', 'reset_return']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_metadata(tool, flag):
    executable = Path(shutil.which(tool)).resolve()
    result = subprocess.run([tool, flag], capture_output=True, text=True)
    return {'path': str(executable), 'sha256': sha(executable), 'version_returncode': result.returncode,
            'version_stdout': result.stdout, 'version_stderr': result.stderr}


def resource_metadata(path):
    text = path.read_text()
    result = {}
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        parser.error('fresh output directory outside source required; preserve earlier attempts')
    if not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('unambiguous HDL output path required')
    required = [('python3', '--version'), ('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')]
    if args.synthesize:
        required.append(('yosys', '-V'))
    for tool, _ in required:
        if not shutil.which(tool):
            parser.error('missing tool: ' + tool)
    if not Path('/usr/bin/time').is_file():
        parser.error('missing /usr/bin/time resource recorder')
    out.mkdir(parents=True)
    commands, records, input_hashes, fixture_hashes = [], {}, {}, {}
    summary = {
        'status': 'running', 'synthesis_requested': args.synthesize,
        'boundary': 'Pinned fillAes4Rx4 generation only. Capture seed privately, output native Program '
                    'bytes and retain caller seed. No autonomous hash, architecture choice or physical PPA.',
        'cycle_contract': 'Four serialized AES rounds per 16-byte beat. The fourth result transfers '
                          'only with out_valid/out_ready. Ideal request-to-response availability is '
                          '4*(OUTPUT_BYTES/16); output stalls and held responses are separate observers.',
        'rtl': {}, 'mapped': {}, 'mapping': {}, 'full_program_profiles': [],
    }

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n')

    def run(label, argv, timeout=1800, expected_failure=False):
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT),
               'timeout_seconds': timeout, 'expected_failure': expected_failure}
        commands.append(row)
        print('START ' + label, flush=True)
        began = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                result = subprocess.run(['/usr/bin/time', '-v', '-o', str(out / (label + '.time.txt')),
                                         *argv], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout)
            row['returncode'] = result.returncode
            if expected_failure:
                assert result.returncode != 0, label + ': invalid input unexpectedly accepted'
            else:
                result.check_returncode()
        except Exception as error:
            row['error'] = str(error)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - began
            resource = out / (label + '.time.txt')
            if resource.exists():
                row['resources'] = resource_metadata(resource)
            save('commands.json', commands)
        print(('EXPECTED FAILURE ' if expected_failure else 'PASS ') + label, flush=True)

    def compile_bench(label, size, netlist=None, cells=None):
        executable = out / (label + '.vvp')
        flags = ['-DPROGRAM_GENERATION_NETLIST'] if netlist else []
        sources = [str(netlist), str(cells)] if netlist else RTL
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *flags, '-s', 'tb_program_generation',
             '-Ptb_program_generation.OUTPUT_BYTES=' + str(size), '-o', str(executable), *sources, BENCH])
        return executable

    def simulate(label, executable, case, mode, reference=None):
        run(label, ['vvp', str(executable), '+DIR=' + case['directory'], '+MODE=' + mode])
        lines = (out / (label + '.log')).read_text().splitlines()
        passes = [line for line in lines if line.startswith('PASS ')]
        assert len(passes) == 1 and passes[0].startswith('PASS program_generation '), (label, lines)
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines), label
        record = passes[0]
        if reference:
            assert record == records[reference], (label, record, records[reference])
        records[label] = record
        fields = {key: int(value) for key, value in re.findall(r'(\w+)=(-?\d+)', record)}
        beats = case['bytes'] // 16
        assert fields['bytes'] == case['bytes'] and fields['primary_outputs'] == beats
        assert fields['compute_cycles'] == 4 * beats
        assert fields['native_program_bytes'] == fields['accepted_outputs_persist'] == 1
        assert fields['held_response_cycles'] >= 5 and fields['completed'] >= 1
        assert fields['full_images'] >= fields['completed']
        if mode in ['ideal', 'held_response', 'cancel_before', 'reset_before', 'cancel_return', 'reset_return']:
            assert fields['availability_cycles'] == 4 * beats
        if mode == 'stalled':
            assert fields['output_stall_cycles'] > 0
            assert fields['availability_cycles'] == 4 * beats + fields['output_stall_cycles']
        if mode == 'held_request':
            assert fields['requests'] == fields['completed'] == fields['full_images'] == 2
            assert fields['held_request_cycles'] > 0
        if mode.startswith(('cancel_', 'reset_')):
            assert fields['aborts'] == 1
            expected = 0 if mode.endswith('before') else beats if mode.endswith('return') else 3
            assert fields['aborted_outputs'] == expected
        assert fields['round_position'] == (int(mode[-1]) if '_round' in mode else -1)
        return {'record': record, 'case': case['name'], 'mode': mode, **fields}

    def synth(label, size):
        netlist = out / ('netlist-' + label + '.v')
        script = 'read_verilog ' + ' '.join(RTL) + '; '
        script += f'chparam -set OUTPUT_BYTES {size} {TOP}; '
        script += f'synth -top {TOP} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
        script += f'write_verilog -noattr {netlist}; write_json {out}/netlist-{label}.json'
        run('synth-' + label, ['yosys', '-p', script], timeout=3600)
        mapped = json.loads((out / ('netlist-' + label + '.json')).read_text())['modules'][TOP]
        kinds = Counter(cell['type'] for cell in mapped['cells'].values())
        cells = int(re.search(r'Number of cells:\s*(\d+)', (out / ('stat-' + label + '.txt')).read_text())[1])
        assert cells == sum(kinds.values())
        return netlist, {'top': TOP, 'output_bytes': size, 'num_cells': cells,
                         'flop_cells': sum(n for kind, n in kinds.items() if 'DFF' in kind),
                         'latch_cells': sum(n for kind, n in kinds.items() if 'LATCH' in kind),
                         'num_cells_by_type': dict(sorted(kinds.items())),
                         'scope': 'Actual new generator controller and reused shared AES round only; '
                                  'no output image memory, executor, physical timing/area/power.'}

    try:
        run('vendor', ['python3', '-B', 'scripts/verify_vendor.py'])
        ip = ROOT / 'rtl/aes/vendor/secworks/UPSTREAM.json'
        for name, entry in json.loads(ip.read_text())['files'].items():
            assert sha(ip.parent / name) == entry['sha256'], 'secworks pin: ' + name
        assert sha(ROOT / PRIOR_FIXTURES) == PRIOR_FIXTURES_SHA, 'accepted initial-fill fixture manifest identity'
        prior = json.loads((ROOT / PRIOR_FIXTURES).read_text())
        assert prior['2097152-incrementing/seed-out.bin'] == POSTFILL_BINARY_SHA
        assert sha(ROOT / POSTFILL) == prior['2097152-incrementing/seed-out.hex']
        postfill_bytes = bytes.fromhex((ROOT / POSTFILL).read_text().strip())[::-1]
        assert len(postfill_bytes) == 64 and hashlib.sha256(postfill_bytes).hexdigest() == POSTFILL_BINARY_SHA
        postfill_binary = out / 'accepted-postfill-seed.bin'
        postfill_binary.write_bytes(postfill_bytes)
        save('postfill-seed-provenance.json', {
            'source': POSTFILL, 'accepted_initial_fill_execution': '20261016T082316Z-86c364941cf5',
            'accepted_fixture_manifest': PRIOR_FIXTURES, 'accepted_fixture_manifest_sha256': PRIOR_FIXTURES_SHA,
            'accepted_seed_path': '2097152-incrementing/seed-out.bin', 'binary_sha256': POSTFILL_BINARY_SHA,
            'derivation': 'Byte-reverse the accepted 512-bit readmemh word; no fill/hash/dataset rerun.'})
        bound = set(RTL) | {BENCH, ORACLE, POSTFILL, PRIOR_FIXTURES, 'scripts/test_program_generation.py',
                           'scripts/verify_vendor.py', 'vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                           'vendor/randomx/LICENSE', 'rtl/aes/vendor/secworks/UPSTREAM.json',
                           'rtl/aes/vendor/secworks/LICENSE', 'rtl/aes/LICENSE'}
        bound.update('vendor/randomx/' + name for name in json.loads((ROOT / 'vendor/randomx.sha256.json').read_text()))
        input_hashes = {name: sha(ROOT / name) for name in sorted(bound)}
        save('inputs.json', input_hashes)
        save('tools.json', {tool: tool_metadata(tool, flag) for tool, flag in required})
        for name, path in {'RandomX': 'vendor/randomx/LICENSE', 'secworks': 'rtl/aes/vendor/secworks/LICENSE',
                           'OpenRX-AES': 'rtl/aes/LICENSE'}.items():
            shutil.copyfile(ROOT / path, out / ('LICENSE-' + name))
        oracle = out / 'program-generation-oracle'
        run('compile-native-oracle', ['g++', '-O2', '-std=c++17', '-Wall', '-Wextra', '-maes',
             '-Ivendor/randomx/src', ORACLE, 'vendor/randomx/src/aes_hash.cpp',
             'vendor/randomx/src/soft_aes.cpp', '-o', str(oracle)])
        fixtures = out / 'fixtures'
        fixtures.mkdir()
        cases = {}
        for size in SIZES:
            for seed in SEEDS:
                name = str(size) + '-' + seed
                directory = fixtures / name
                directory.mkdir()
                run('native-' + name, [str(oracle), str(directory), str(size), seed]
                    + ([str(postfill_binary)] if seed == 'postfill' else []))
                native = json.loads((directory / 'native-summary.json').read_text())
                assert native['bytes'] == size and native['seed_kind'] == seed
                assert native['native_program_bytes'] == 3200 and native['entropy_bytes'] == 128
                assert native['maximum_instruction_words'] == 384
                assert native['input_seed_unchanged'] and native['repeated_call_restarts'] and native['native_program_prefix_verified']
                assert (directory / 'image.bin').stat().st_size == size
                assert (directory / 'seed-in.bin').stat().st_size == 64
                cases[name] = {'name': name, 'bytes': size, 'seed': seed, 'directory': str(directory)}
        save('corpus.json', {'cases': list(cases.values()), 'native_function': 'fillAes4Rx4<true>',
                            'native_pin': json.loads((ROOT / 'vendor/randomx.lock.json').read_text()),
                            'prng_seed': '0x4f70656e52584734', 'native_program_bytes': 3200})
        fixture_hashes = {str(path.relative_to(fixtures)): sha(path) for path in sorted(fixtures.rglob('*')) if path.is_file()}
        save('fixtures.sha256.json', fixture_hashes)
        negatives = out / 'native-invalid'
        negatives.mkdir()
        bad_cases = [(0, 'zero', None), (63, 'zero', None), (65, 'zero', None),
                     (3264, 'zero', None), (64, 'unknown', None)]
        for size in [63, 65]:
            path = negatives / ('bad-seed-' + str(size) + '.bin')
            path.write_bytes(bytes(size))
            bad_cases.append((64, 'postfill', path))
        for number, (size, seed, seed_path) in enumerate(bad_cases):
            directory = negatives / str(number)
            directory.mkdir()
            run('native-invalid-' + str(number), [str(oracle), str(directory), str(size), seed]
                + ([str(seed_path)] if seed_path else []), expected_failure=True)
            assert not list(directory.iterdir()), 'invalid native fixture wrote outputs'
        executables = {size: compile_bench('rtl-' + str(size), size) for size in SIZES}
        for size in SIZES:
            for seed in SEEDS:
                case = cases[str(size) + '-' + seed]
                for mode in ['ideal', 'stalled']:
                    label = 'rtl-' + case['name'] + '-' + mode
                    summary['rtl'][label] = simulate(label, executables[size], case, mode)
                    if size == 3200:
                        summary['full_program_profiles'].append(summary['rtl'][label])
        bounded = cases['256-incrementing']
        for mode in CONTROLS:
            label = 'rtl-control-' + mode
            summary['rtl'][label] = simulate(label, executables[256], bounded, mode)
        for size in [0, 63, 65, 3264]:
            label = 'invalid-parameter-' + str(size)
            run(label, ['iverilog', '-g2012', '-s', TOP, '-P' + TOP + '.OUTPUT_BYTES=' + str(size),
                        '-o', str(out / (label + '.vvp')), *RTL], expected_failure=True)
            assert 'program_generation_requires_multiple_of_64_between_64_and_3200' in (out / (label + '.log')).read_text()
        if args.synthesize:
            installed_cells = Path('/usr/share/yosys/simcells.v')
            assert installed_cells.is_file()
            cells = out / 'yosys-simcells.v'
            shutil.copyfile(installed_cells, cells)
            save('yosys-cell-model.json', {'installed_path': str(installed_cells), 'sha256': sha(installed_cells),
                                          'copied_sha256': sha(cells), 'license': 'Preserved Yosys ISC notice in copied file'})
            _, summary['mapping']['default-3200'] = synth('default-3200', 3200)
            bounded_netlist, summary['mapping']['bounded-256'] = synth('bounded-256', 256)
            executable = compile_bench('mapped-256', 256, bounded_netlist, cells)
            for seed in SEEDS:
                case = cases['256-' + seed]
                for mode in ['ideal', 'stalled']:
                    label = 'mapped-' + case['name'] + '-' + mode
                    summary['mapped'][label] = simulate(label, executable, case, mode, 'rtl-' + case['name'] + '-' + mode)
            for mode in CONTROLS:
                label = 'mapped-control-' + mode
                summary['mapped'][label] = simulate(label, executable, bounded, mode, 'rtl-control-' + mode)
        summary['native_cases'] = len(cases)
        summary['native_invalid_cases'] = len(bad_cases)
        summary['invalid_hardware_parameter_cases'] = 4
        summary['rtl_modes'] = len(summary['rtl'])
        summary['mapped_modes'] = len(summary['mapped'])
        assert summary['rtl_modes'] == 44 and len(summary['full_program_profiles']) == 10
        assert summary['mapped_modes'] == (24 if args.synthesize else 0)
        summary['fixture_inputs_unchanged_after_run'] = all(sha(fixtures / name) == digest for name, digest in fixture_hashes.items())
        summary['postfill_fixture_unchanged_after_run'] = sha(postfill_binary) == POSTFILL_BINARY_SHA
        summary['source_unchanged_after_run'] = all(sha(ROOT / name) == digest for name, digest in input_hashes.items())
        assert summary['fixture_inputs_unchanged_after_run'] and summary['source_unchanged_after_run'] and summary['postfill_fixture_unchanged_after_run']
        summary['status'] = 'pass'
        print('PASS program_generation_suite rtl_modes=44 full_program_profiles=10 mapped_modes=' + str(summary['mapped_modes']), flush=True)
    except Exception as error:
        summary['status'] = 'failed'
        summary['error'] = str(error)
        raise
    finally:
        save('summary.json', summary)
        save('artifacts.sha256.json', {str(path.relative_to(out)): sha(path)
             for path in sorted(out.rglob('*')) if path.is_file() and path != out / 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
