#!/usr/bin/env python3
"""Native differential bounded input BLAKE2b-512 and actual new-wrapper mapping.

Execute only inside the caller's admitted single global resource slot. This
driver acquires no slot and starts no full RandomX workload. It validates input
lengths0..80, rejected lengths81..127 and focused mapped/recovery behavior using
the unchanged accepted compression IP. It establishes no physical PPA or general
input-size support beyond the connected80-byte request boundary.
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
TOP = 'randomx_input_blake2b'
HASH = 'rtl/hash/'
IP = HASH + 'vendor/blake2/'
CORE = HASH + 'randomx_blake2b_chain_core.v'
CORE_SHA = '74921226713d4546c6e8e2485a7205499f8b48a1d9cc355e6315769738c5bda8'
IP_MANIFEST_SHA = '7e09b930df6133ccd5453fdd09eead183212cf2978865a104e96e938d6cc508e'
RTL = [CORE, HASH + TOP + '.v']
BENCH = HASH + 'tests/tb_input_blake2b.v'
ORACLE = HASH + 'tests/input_blake2b_oracle.cpp'
CONTROLS = ['held_response', 'held_request', 'invalid_all', 'invalid_edges',
            *[kind + '_' + stage for kind in ['cancel', 'reset']
              for stage in ['before', 'start', 'early', 'middle', 'final', 'return']]]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_metadata(tool, flag):
    executable = Path(shutil.which(tool)).resolve()
    result = subprocess.run([tool, flag], capture_output=True, text=True)
    return {'path': str(executable), 'sha256': sha(executable), 'version_returncode': result.returncode,
            'version_stdout': result.stdout, 'version_stderr': result.stderr}


def resource_metadata(path):
    result = {}
    text = path.read_text()
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
        parser.error('fresh output directory outside source required; preserve previous attempts')
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
        'boundary': 'Unkeyed BLAKE2b-512 input length0..80 only; unsupported81..127 returns held error. '
                    'New input wrapper reuses unchanged accepted compression core. Native Light dataset '
                    'and physical memory service remain external; no general input or physical PPA claim.',
        'compression_contract': 'One zero-padded128B final block, exact byte counter including0, '
                                'DIGEST_LENGTH64/KEY_LENGTH0/FANOUT1/DEPTH1/twelve rounds. '
                                'Length/descriptor captured; no0x80 or SHA length suffix.',
        'rtl': {}, 'mapped': {}, 'mapping': {},
    }

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n')

    def run(label, argv, timeout=1800):
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout}
        commands.append(row)
        print('START ' + label, flush=True)
        began = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                result = subprocess.run(['/usr/bin/time', '-v', '-o', str(out / (label + '.time.txt')),
                                         *argv], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=timeout)
            row['returncode'] = result.returncode
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
        print('PASS ' + label, flush=True)

    def compile_bench(label, netlist=None, cells=None):
        executable = out / (label + '.vvp')
        sources = [str(netlist), str(cells)] if netlist else RTL
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-I' + IP,
             '-s', 'tb_input_blake2b', '-o', str(executable), *sources, BENCH])
        return executable

    def simulate(label, executable, mode, vectors='vectors.hex', reference=None):
        run(label, ['vvp', str(executable), '+DIR=' + str(out / 'fixtures'),
                    '+MODE=' + mode, '+VECTORS=' + vectors])
        lines = (out / (label + '.log')).read_text().splitlines()
        passes = [line for line in lines if line.startswith('PASS ')]
        assert len(passes) == 1 and passes[0].startswith('PASS input_blake2b '), (label, lines)
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines), label
        record = passes[0]
        if reference:
            assert record == records[reference], (label, record, records[reference])
        records[label] = record
        fields = {key: int(value) for key, value in re.findall(r'(\w+)=(-?\d+)', record)}
        assert fields['latency_min'] == fields['latency_max'] and fields['latency_min'] > 0
        assert fields['native_vector_compute_cycles'] == fields['native_vectors'] * fields['latency_min']
        assert fields['captured_input_tag'] == fields['empty_tail_restart'] == 1
        if mode == 'corpus':
            expected = 26 if vectors == 'mapped-vectors.hex' else 614
            assert fields['native_vectors'] == fields['requests'] == fields['completed'] == expected
            assert fields['invalid_lengths'] == fields['aborts'] == 0
        else:
            assert fields['held_response_cycles'] >= 5
        if mode == 'held_request':
            assert fields['requests'] == fields['completed'] == fields['native_vectors'] == 2
            assert fields['held_request_cycles'] > 0
        if mode in ['invalid_all', 'invalid_edges']:
            invalid = 47 if mode == 'invalid_all' else 2
            assert fields['invalid_lengths'] == invalid and fields['native_vectors'] == 2
            assert fields['requests'] == fields['completed'] == invalid + 2
        if mode.startswith(('cancel_', 'reset_')):
            assert fields['aborts'] == 1
            expected_age = {'start': 0, 'early': 2, 'middle': 14, 'final': 26}.get(mode.split('_')[1], -1)
            assert fields['abort_age'] == expected_age
        return {'record': record, 'mode': mode, **fields}

    def synth():
        netlist = out / 'netlist-input-blake2b.v'
        script = 'read_verilog -I' + IP + ' ' + ' '.join(RTL) + '; '
        script += f'synth -top {TOP} -flatten; check -assert; tee -o {out}/stat-input-blake2b.txt stat; '
        script += f'write_verilog -noattr {netlist}; write_json {out}/netlist-input-blake2b.json'
        run('synth-input-blake2b', ['yosys', '-p', script], timeout=3600)
        mapped = json.loads((out / 'netlist-input-blake2b.json').read_text())['modules'][TOP]
        kinds = Counter(cell['type'] for cell in mapped['cells'].values())
        cells = int(re.search(r'Number of cells:\s*(\d+)', (out / 'stat-input-blake2b.txt').read_text())[1])
        assert cells == sum(kinds.values())
        return netlist, {'top': TOP, 'max_input_bytes': 80, 'digest_bytes': 64, 'num_cells': cells,
                         'flop_cells': sum(n for kind, n in kinds.items() if 'DFF' in kind),
                         'inherited_latch_cells': sum(n for kind, n in kinds.items() if 'LATCH' in kind),
                         'num_cells_by_type': dict(sorted(kinds.items())),
                         'scope': 'Actual new input wrapper plus unchanged compression core; inherited G operand '
                                  'latches reported separately. No whole-lifecycle mapping or physical timing/area/power.'}

    try:
        run('vendor', ['python3', '-B', 'scripts/verify_vendor.py'])
        assert sha(ROOT / CORE) == CORE_SHA, 'accepted compression derivative changed'
        manifest = ROOT / IP / 'manifest.json'
        assert sha(manifest) == IP_MANIFEST_SHA, 'preserved original IP manifest changed'
        original = json.loads(manifest.read_text())
        for name, digest in original['original_files'].items():
            assert sha(manifest.parent / name) == digest, 'original BLAKE2 IP changed: ' + name
        bound = set(RTL) | {BENCH, ORACLE, 'scripts/test_input_blake2b.py', 'scripts/verify_vendor.py',
                           IP + 'manifest.json', 'vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                           'vendor/randomx/LICENSE'}
        bound.update(IP + name for name in original['original_files'])
        bound.update('vendor/randomx/' + name for name in json.loads((ROOT / 'vendor/randomx.sha256.json').read_text()))
        input_hashes = {name: sha(ROOT / name) for name in sorted(bound)}
        save('inputs.json', input_hashes)
        save('preserved-IP.json', {'core': CORE, 'core_sha256': CORE_SHA, 'core_unchanged': True,
             'original_manifest_sha256': IP_MANIFEST_SHA, 'original_files_unchanged': len(original['original_files']),
             'arithmetic_and_message_schedule_changes': False, 'original_ip': original})
        save('tools.json', {tool: tool_metadata(tool, flag) for tool, flag in required})
        for label, path in {'RandomX': 'vendor/randomx/LICENSE', 'BLAKE2-original': IP + 'LICENSE'}.items():
            shutil.copyfile(ROOT / path, out / ('LICENSE-' + label))
        oracle = out / 'input-blake2b-oracle'
        run('compile-native-oracle', ['g++', '-O2', '-std=c++17', '-Wall', '-Wextra', '-Ivendor/randomx/src',
             ORACLE, 'vendor/randomx/src/blake2/blake2b.c', '-o', str(oracle)])
        fixtures = out / 'fixtures'
        fixtures.mkdir()
        run('native-oracle', [str(oracle), str(fixtures)])
        native = json.loads((fixtures / 'native-summary.json').read_text())
        assert native['native_vectors'] == 614 and native['mapped_vectors'] == 26 and native['valid_lengths'] == 81
        assert native['tail_poison_cases'] == 162 and native['arbitrary_cases'] == 128
        assert native['control_vectors'] == 2 and native['empty_null_input_verified'] and native['digest_bytes'] == 64
        for name, expected_rows in [('vectors.hex', 614), ('mapped-vectors.hex', 26), ('control.hex', 2)]:
            rows = (fixtures / name).read_text().splitlines()
            assert len(rows) == expected_rows
            for row in rows:
                length, data, digest = row.split()
                assert 0 <= int(length) <= 80 and len(bytes.fromhex(data)) == 80 and len(bytes.fromhex(digest)) == 64
        fixture_hashes = {path.name: sha(path) for path in sorted(fixtures.iterdir()) if path.is_file()}
        save('fixtures.sha256.json', fixture_hashes)
        save('corpus.json', {'native': native, 'oracle': 'unchanged pinned blake2b.c',
                            'RandomX_pin': json.loads((ROOT / 'vendor/randomx.lock.json').read_text()),
                            'prng_seed': '0x4f70656e52584948',
                            'mapped_lengths': [0, 1, 7, 8, 15, 16, 31, 32, 63, 64, 65, 79, 80]})
        executable = compile_bench('rtl')
        summary['rtl']['rtl-corpus'] = simulate('rtl-corpus', executable, 'corpus')
        # Run the same focused corpus through RTL to compare its exact marker to gates.
        summary['rtl']['rtl-mapped-corpus'] = simulate('rtl-mapped-corpus', executable, 'corpus', 'mapped-vectors.hex')
        for mode in CONTROLS:
            label = 'rtl-control-' + mode
            summary['rtl'][label] = simulate(label, executable, mode)
        if args.synthesize:
            installed = Path('/usr/share/yosys/simcells.v')
            assert installed.is_file()
            cells = out / 'yosys-simcells.v'
            shutil.copyfile(installed, cells)
            save('yosys-cell-model.json', {'installed_path': str(installed), 'sha256': sha(installed),
                                          'copied_sha256': sha(cells), 'license': 'Yosys original ISC notice preserved'})
            netlist, summary['mapping']['input-blake2b'] = synth()
            executable = compile_bench('mapped', netlist, cells)
            summary['mapped']['mapped-corpus'] = simulate('mapped-corpus', executable, 'corpus',
                                                         'mapped-vectors.hex', 'rtl-mapped-corpus')
            for mode in CONTROLS:
                if mode == 'invalid_all':
                    continue
                label = 'mapped-control-' + mode
                summary['mapped'][label] = simulate(label, executable, mode, reference='rtl-control-' + mode)
        summary['native_vectors'] = 614
        summary['valid_lengths'] = 81
        summary['tail_poison_cases'] = 162
        summary['unsupported_lengths_rtl'] = 47
        summary['unsupported_lengths_mapped'] = [81, 127] if args.synthesize else []
        summary['rtl_modes'] = len(summary['rtl'])
        summary['mapped_modes'] = len(summary['mapped'])
        assert summary['rtl_modes'] == 18 and summary['mapped_modes'] == (16 if args.synthesize else 0)
        summary['request_to_response_availability_cycles'] = summary['rtl']['rtl-corpus']['latency_min']
        summary['held_response_clocks_are_nested_observers'] = True
        summary['source_unchanged_after_run'] = all(sha(ROOT / name) == digest for name, digest in input_hashes.items())
        summary['fixture_inputs_unchanged_after_run'] = all(sha(fixtures / name) == digest for name, digest in fixture_hashes.items())
        assert summary['source_unchanged_after_run'] and summary['fixture_inputs_unchanged_after_run']
        summary['status'] = 'pass'
        print('PASS input_blake2b_suite native_vectors=614 valid_lengths=81 rtl_modes=18 mapped_modes='
              + str(summary['mapped_modes']), flush=True)
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
