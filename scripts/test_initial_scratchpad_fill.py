#!/usr/bin/env python3
"""Native differential initial scratchpad fill, control tests and actual synthesis.

Run serially inside the caller's admitted payload. This driver does not acquire
a second compute slot. Four complete 2 MiB RTL images and native post-fill seeds
are separate from bounded mapped differential/control tests and actual default
new-component synthesis. Input BLAKE2b, program generation, dataset generation,
physical memories and physical PPA remain outside this component.
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
HASH = 'rtl/hash/'
TEST = HASH + 'tests/'
TOP = 'randomx_initial_scratchpad_fill'
AES = ['rtl/aes/vendor/secworks/aes_sbox.v', 'rtl/aes/vendor/secworks/aes_inv_sbox.v',
       'rtl/aes/randomx_aes_round.v']
RTL = [*AES, HASH + TOP + '.v']
BENCH = TEST + 'tb_initial_scratchpad_fill.v'
ORACLE = TEST + 'initial_scratchpad_fill_oracle.cpp'
SEEDS = ['zero', 'ones', 'incrementing', 'prng']
SIZES = [64, 256, 2097152]
CONTROLS = ['held_response', 'held_request', 'cancel_before', 'reset_before',
            'cancel_stream', 'reset_stream', 'cancel_stall', 'reset_stall',
            'cancel_return', 'reset_return']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_metadata(tool, flag):
    executable = Path(shutil.which(tool)).resolve()
    result = subprocess.run([tool, flag], capture_output=True, text=True)
    return {'path': str(executable), 'sha256': sha(executable),
            'version_returncode': result.returncode, 'version_stdout': result.stdout,
            'version_stderr': result.stderr}


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
        parser.error('fresh output directory outside source required; preserve prior attempts')
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
        'boundary': 'Initial fillAes1Rx4 only, starting from host input BLAKE2b-512; '
                    'program0 consumes hardware postfill seed. No autonomous full hash, '
                    'selected architecture, physical memory model or physical PPA claim.',
        'rtl': {}, 'mapped': {}, 'mapping': {}, 'full_profiles': [],
        'cycle_contract': 'One updated 16-byte lane per accepted write; ideal request-to-response '
                          'availability equals scratchpad_bytes/16. Held response clocks and '
                          'write-stall clocks are observers, not extra AES work.',
        'historical_accounting': 'The preserved40975538-clock connected result already includes '
                                 '131074 initialization transport clocks. Replace that stage '
                                 'with measured new connected initialization; do not add the '
                                 'complete fill write count again.',
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
        flags = ['-DINITIAL_SCRATCHPAD_FILL_NETLIST'] if netlist else []
        sources = [str(netlist), str(cells)] if netlist else RTL
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *flags,
             '-s', 'tb_initial_scratchpad_fill',
             '-Ptb_initial_scratchpad_fill.SCRATCHPAD_BYTES=' + str(size),
             '-o', str(executable), *sources, BENCH])
        return executable

    def simulate(label, executable, case, mode, reference=None):
        run(label, ['vvp', str(executable), '+DIR=' + case['directory'], '+MODE=' + mode])
        lines = (out / (label + '.log')).read_text().splitlines()
        passes = [line for line in lines if line.startswith('PASS ')]
        assert len(passes) == 1 and passes[0].startswith('PASS initial_scratchpad_fill '), (label, lines)
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines), label
        record = passes[0]
        if reference:
            assert record == records[reference], (label, record, records[reference])
        records[label] = record
        fields = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', record)}
        assert fields['bytes'] == case['bytes']
        assert fields['primary_writes'] == case['bytes'] // 16
        assert fields['native_final_seed'] == fields['accepted_writes_persist'] == 1
        assert fields['held_response_cycles'] >= 5 and fields['completed'] >= 1
        assert fields['full_images'] >= fields['completed']
        if mode in ['ideal', 'held_response', 'cancel_before', 'reset_before', 'cancel_return', 'reset_return']:
            assert fields['availability_cycles'] == case['bytes'] // 16
        if mode == 'stalled':
            assert fields['stall_cycles'] > 0 and fields['availability_cycles'] > case['bytes'] // 16
        if mode == 'held_request':
            assert fields['requests'] == fields['completed'] == fields['full_images'] == 2
            assert fields['held_request_cycles'] > 0
        if mode.startswith(('cancel_', 'reset_')):
            assert fields['aborts'] == 1
            expected = 0 if mode.endswith('before') else case['bytes'] // 16 if mode.endswith('return') else 3
            assert fields['aborted_writes'] == expected
        return {'record': record, 'case': case['name'], 'mode': mode, **fields}

    def synth(label, size):
        netlist = out / ('netlist-' + label + '.v')
        script = 'read_verilog ' + ' '.join(RTL) + '; '
        script += f'chparam -set SCRATCHPAD_BYTES {size} {TOP}; '
        script += f'synth -top {TOP} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
        script += f'write_verilog -noattr {netlist}; write_json {out}/netlist-{label}.json'
        run('synth-' + label, ['yosys', '-p', script], timeout=3600)
        mapped = json.loads((out / ('netlist-' + label + '.json')).read_text())['modules'][TOP]
        kinds = Counter(cell['type'] for cell in mapped['cells'].values())
        cells = int(re.search(r'Number of cells:\s*(\d+)', (out / ('stat-' + label + '.txt')).read_text())[1])
        assert cells == sum(kinds.values())
        return netlist, {'top': TOP, 'scratchpad_bytes': size, 'num_cells': cells,
                         'flop_cells': sum(n for kind, n in kinds.items() if 'DFF' in kind),
                         'latch_cells': sum(n for kind, n in kinds.items() if 'LATCH' in kind),
                         'num_cells_by_type': dict(sorted(kinds.items())),
                         'scope': 'Actual default new fill component, reused AES round and controller only; '
                                  'no SRAM/executor mapping or calibrated timing/area/power.'}

    try:
        run('vendor', ['python3', '-B', 'scripts/verify_vendor.py'])
        ip = ROOT / 'rtl/aes/vendor/secworks/UPSTREAM.json'
        for name, entry in json.loads(ip.read_text())['files'].items():
            assert sha(ip.parent / name) == entry['sha256'], 'secworks pin: ' + name
        bound = set(RTL) | {BENCH, ORACLE, 'scripts/test_initial_scratchpad_fill.py',
                           'scripts/verify_vendor.py', 'vendor/randomx.lock.json',
                           'vendor/randomx.sha256.json', 'vendor/randomx/LICENSE',
                           'rtl/aes/vendor/secworks/UPSTREAM.json', 'rtl/aes/vendor/secworks/LICENSE',
                           'rtl/aes/LICENSE'}
        bound.update('vendor/randomx/' + name for name in json.loads((ROOT / 'vendor/randomx.sha256.json').read_text()))
        input_hashes = {name: sha(ROOT / name) for name in sorted(bound)}
        save('inputs.json', input_hashes)
        save('tools.json', {tool: tool_metadata(tool, flag) for tool, flag in required})
        for name, path in {'RandomX': 'vendor/randomx/LICENSE',
                           'secworks': 'rtl/aes/vendor/secworks/LICENSE', 'OpenRX-AES': 'rtl/aes/LICENSE'}.items():
            shutil.copyfile(ROOT / path, out / ('LICENSE-' + name))
        oracle = out / 'initial-scratchpad-fill-oracle'
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
                run('native-' + name, [str(oracle), str(directory), str(size), seed])
                native = json.loads((directory / 'native-summary.json').read_text())
                assert native['bytes'] == size and native['seed_kind'] == seed
                assert native['split_call_continuation_verified'] and native['final_seed_is_last_64_bytes']
                assert (directory / 'image.bin').stat().st_size == size
                assert (directory / 'seed-in.bin').stat().st_size == (directory / 'seed-out.bin').stat().st_size == 64
                assert (directory / 'image.bin').read_bytes()[-64:] == (directory / 'seed-out.bin').read_bytes()
                cases[name] = {'name': name, 'bytes': size, 'seed': seed, 'directory': str(directory)}
        save('corpus.json', {'cases': list(cases.values()), 'native_function': 'fillAes1Rx4<true>',
                            'native_pin': json.loads((ROOT / 'vendor/randomx.lock.json').read_text()),
                            'prng_seed': '0x4f70656e52584631'})
        fixture_hashes = {str(path.relative_to(fixtures)): sha(path) for path in sorted(fixtures.rglob('*')) if path.is_file()}
        save('fixtures.sha256.json', fixture_hashes)
        negatives = out / 'native-invalid'
        negatives.mkdir()
        for number, (size, seed) in enumerate([(0, 'zero'), (63, 'zero'), (65, 'zero'),
                                              (2097216, 'zero'), (64, 'unknown')]):
            directory = negatives / str(number)
            directory.mkdir()
            run('native-invalid-' + str(number), [str(oracle), str(directory), str(size), seed], expected_failure=True)
            assert not list(directory.iterdir()), 'invalid native fixture wrote output'
        executables = {size: compile_bench('rtl-' + str(size), size) for size in SIZES}
        for size in SIZES[:2]:
            for seed in SEEDS:
                case = cases[str(size) + '-' + seed]
                for mode in ['ideal', 'stalled']:
                    label = 'rtl-' + case['name'] + '-' + mode
                    summary['rtl'][label] = simulate(label, executables[size], case, mode)
        bounded = cases['256-incrementing']
        for mode in CONTROLS:
            label = 'rtl-control-' + mode
            summary['rtl'][label] = simulate(label, executables[256], bounded, mode)
        # Balanced ideal/stalled full-size profiles across the four raw seeds.
        for seed, mode in [('zero', 'ideal'), ('ones', 'stalled'), ('incrementing', 'stalled'), ('prng', 'ideal')]:
            case = cases['2097152-' + seed]
            label = 'rtl-' + case['name'] + '-' + mode
            summary['rtl'][label] = simulate(label, executables[2097152], case, mode)
            summary['full_profiles'].append({'case': case['name'], 'mode': mode, **summary['rtl'][label]})
        for size in [0, 63, 65, 2097216]:
            label = 'invalid-parameter-' + str(size)
            run(label, ['iverilog', '-g2012', '-s', TOP, '-P' + TOP + '.SCRATCHPAD_BYTES=' + str(size),
                        '-o', str(out / (label + '.vvp')), *RTL], expected_failure=True)
            assert 'initial_scratchpad_fill_requires_multiple_of_64_between_64_and_2097152' in (out / (label + '.log')).read_text()
        if args.synthesize:
            installed_cells = Path('/usr/share/yosys/simcells.v')
            assert installed_cells.is_file()
            cells = out / 'yosys-simcells.v'
            shutil.copyfile(installed_cells, cells)
            save('yosys-cell-model.json', {'installed_path': str(installed_cells), 'sha256': sha(installed_cells),
                                          'copied_sha256': sha(cells), 'license': 'Preserved Yosys ISC notice in copied file'})
            _, summary['mapping']['default-2097152'] = synth('default-2097152', 2097152)
            bounded_netlist, summary['mapping']['bounded-256'] = synth('bounded-256', 256)
            executable = compile_bench('mapped-256', 256, bounded_netlist, cells)
            for seed in SEEDS:
                case = cases['256-' + seed]
                for mode in ['ideal', 'stalled']:
                    label = 'mapped-' + case['name'] + '-' + mode
                    reference = 'rtl-' + case['name'] + '-' + mode
                    summary['mapped'][label] = simulate(label, executable, case, mode, reference)
            for mode in CONTROLS:
                label = 'mapped-control-' + mode
                summary['mapped'][label] = simulate(label, executable, bounded, mode, 'rtl-control-' + mode)
        summary['native_cases'] = len(cases)
        summary['native_invalid_cases'] = 5
        summary['invalid_hardware_parameter_cases'] = 4
        summary['rtl_modes'] = len(summary['rtl'])
        summary['mapped_modes'] = len(summary['mapped'])
        assert summary['rtl_modes'] == 30 and len(summary['full_profiles']) == 4
        assert summary['mapped_modes'] == (18 if args.synthesize else 0)
        summary['fixture_inputs_unchanged_after_run'] = all(sha(fixtures / name) == digest for name, digest in fixture_hashes.items())
        summary['source_unchanged_after_run'] = all(sha(ROOT / name) == digest for name, digest in input_hashes.items())
        assert summary['fixture_inputs_unchanged_after_run'] and summary['source_unchanged_after_run']
        summary['status'] = 'pass'
        print('PASS initial_scratchpad_fill_suite rtl_modes=30 full_images=4 mapped_modes=' + str(summary['mapped_modes']), flush=True)
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
