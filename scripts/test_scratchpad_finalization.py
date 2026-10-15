#!/usr/bin/env python3
"""Native scratchpad AES reduction, A replacement and independently parameterized BLAKE2b-256.

Run serially inside the caller's admitted local payload. This driver does not
acquire a second compute slot or regenerate the accepted program execution.
Default full scratchpad RTL, bounded mapped gates and actual default synthesis
are separate claims. Initialization, program generation, dataset and physical
PPA remain outside this component's acceptance boundary.
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
from scratchpad_finalization_fixture import prepare
from combined_source_bindings import validate_context

ROOT = Path(__file__).resolve().parents[1]
BASE = '4f095fc147b5bc78de79746a0a172f38e34d6450'
ACCEPTED = 'docs/validation/regfile-blake2b-20261013/server/inputs.json'
ACCEPTED_SHA = '5235c3cff1de5ac3fcc16f56b7ccae07c9296f001179d3b99ce97cda9ff93328'
FULL_MANIFEST = 'docs/validation/program-sequence-20261013/full-v2-8x2048/artifacts.sha256.json'
FULL_MANIFEST_SHA = 'd002d55d751718f79df5aee0e08d56e8c5cb91e6e76f18fdc8b20caf766c078f'
HASH = 'rtl/hash/'
TEST = HASH + 'tests/'
AES = ['rtl/aes/vendor/secworks/aes_sbox.v', 'rtl/aes/vendor/secworks/aes_inv_sbox.v',
       'rtl/aes/randomx_aes_round.v']
# The preserved chain core includes its original G/message modules itself.
BLAKE = [HASH + 'randomx_blake2b_chain_core.v', HASH + 'randomx_regfile_blake2b.v']
SCANNER = HASH + 'randomx_scratchpad_aes_hash.v'
FINALIZER = HASH + 'randomx_scratchpad_finalizer.v'
RTL = [*AES, *BLAKE, SCANNER, FINALIZER]
CONTROLS = ['held', 'invalid', 'error_first', 'error_last', 'reset_req', 'reset_read',
            'reset_aes', 'reset_hash', 'reset_return']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_metadata(tool, flag):
    """Retain both version streams and status, including tools printing to stderr."""
    path = Path(shutil.which(tool)).resolve()
    proc = subprocess.run([tool, flag], capture_output=True, text=True)
    return {'path': str(path), 'sha256': sha(path), 'version_stdout': proc.stdout,
            'version_stderr': proc.stderr, 'version_returncode': proc.returncode}


def mapping_output_metadata(top):
    """The scanner produces a 64-byte AES reduction; only finalizers emit a digest."""
    if top == 'randomx_scratchpad_aes_hash':
        return {'aes_output_bytes': 64}
    if top == 'randomx_scratchpad_finalizer':
        return {'aes_output_bytes': 64, 'digest_bytes': 32}
    raise ValueError('unknown finalization mapping top: ' + top)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        parser.error('fresh output outside source required')
    if not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('unambiguous HDL output path required')
    required = [('python3', '--version'), ('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')]
    if args.synthesize:
        required.append(('yosys', '-V'))
    for tool, _ in required:
        if not shutil.which(tool):
            parser.error('missing tool: ' + tool)
    out.mkdir()
    commands, records, summaries = [], {}, {}
    summary = {'validated_draft_parent': BASE, 'synthesis_requested': args.synthesize,
               'boundary': 'Post-execution scratchpad finalization only; initial fill, program generation, '
                           'complete actual dataset and complete hardware hash remain external. '
                           'Full2MiB RTL is separate from bounded256B mapped differential; '
                           'actual default new-stage mapping is not calibrated timing or physical PPA.',
               'rtl': {}, 'mapped': {}, 'mapping': {}, 'full_profile_order': []}
    input_hashes = {}
    cell_model = None

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n')

    def run(label, argv, timeout=3600, expected_failure=False):
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout,
               'expected_failure': expected_failure}
        commands.append(row)
        print('START ' + label, flush=True)
        start = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                proc = subprocess.run(['/usr/bin/time', '-v', '-o', str(out / (label + '.time.txt')),
                                       *argv], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                      timeout=timeout)
            row['returncode'] = proc.returncode
            if expected_failure:
                assert proc.returncode != 0, (label, 'invalid parameter unexpectedly compiled')
            else:
                proc.check_returncode()
        except Exception as error:
            row['error'] = str(error)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - start
            save('commands.json', commands)
        print(('EXPECTED FAILURE ' if expected_failure else 'PASS ') + label, flush=True)

    def compile_bench(label, size, net=None):
        target = out / (label + '.vvp')
        flags = ['-DSCRATCHPAD_FINALIZER_NETLIST'] if net else []
        sources = [str(net), str(cell_model)] if net else RTL
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-I' + HASH + 'vendor/blake2',
            *flags, '-s', 'tb_scratchpad_finalization',
            '-Ptb_scratchpad_finalization.SCRATCHPAD_BYTES=' + str(size),
            '-o', str(target), *sources, TEST + 'tb_scratchpad_finalization.v'])
        return target

    def simulate(label, executable, case, mode, round_mode, reference=None, restart_only=False):
        run(label, ['vvp', str(executable), '+DIR=' + case['directory'], '+MODE=' + mode,
                    '+ROUND_MODE=' + str(round_mode), '+RESTART_ONLY=' + str(int(restart_only))])
        lines = (out / (label + '.log')).read_text().splitlines()
        passes = [line for line in lines if line.startswith('PASS ')]
        assert len(passes) == 1 and passes[0].startswith('PASS scratchpad_finalization mode=' + mode + ' '), (label, lines)
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines), label
        record = passes[0]
        if reference:
            assert record == records[reference], (label, record, records[reference])
        records[label] = record
        fields = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', record)}
        assert fields['bytes'] == case['scratchpad_bytes'] and fields['elapsed_cycles'] > 0
        if mode in ['ideal', 'stalled', 'held']:
            assert fields['primary_reads'] == case['scratchpad_bytes'] // 16
            if mode == 'ideal':
                assert fields['primary_response_latency'] == 3 * (case['scratchpad_bytes'] // 16) + 68
        elif mode == 'invalid':
            assert fields['primary_reads'] == 0
        elif mode == 'error_first':
            assert fields['primary_reads'] == 1
        elif mode == 'error_last':
            assert fields['primary_reads'] == case['scratchpad_bytes'] // 16
        assert fields['restart_only'] == int(restart_only)
        if restart_only:
            assert fields['native_success'] == 0 and fields['restart_reads'] == 1
        else:
            assert fields['native_success'] > 0
            assert fields['native_RFE_round_preserved'] == fields['native_AES_A'] == fields['native_digest32_not_truncated64'] == 1
        summaries[label] = fields
        return {'record': record, **fields, 'case': case['name'], 'round_mode': round_mode}

    def synth(label, top, sources, size=2097152):
        net = out / ('netlist-' + label + '.v')
        script = 'read_verilog -I' + HASH + 'vendor/blake2 ' + ' '.join(sources) + '; '
        script += f'chparam -set SCRATCHPAD_BYTES {size} {top}; '
        script += f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
        script += f'write_verilog -noattr {net}; write_json {out}/netlist-{label}.json'
        run('synth-' + label, ['yosys', '-p', script], timeout=7200)
        counts = Counter()
        with (out / ('netlist-' + label + '.json')).open() as stream:
            for line in stream:
                match = re.fullmatch(r'\s*"type": "([^"]+)",\s*\n?', line)
                if match:
                    counts[match[1]] += 1
        cells = int(re.search(r'Number of cells:\s*(\d+)', (out / ('stat-' + label + '.txt')).read_text()).group(1))
        assert cells == sum(counts.values())
        return net, {'num_cells': cells, 'flop_cells': sum(n for kind, n in counts.items() if 'DFF' in kind),
                     'latch_cells': sum(n for kind, n in counts.items() if 'DLATCH' in kind),
                     'num_cells_by_type': dict(sorted(counts.items())), 'top': top,
                     'scratchpad_bytes': size, **mapping_output_metadata(top),
                     'scope': 'Actual mapped new component only; no execution-core remapping or physical SRAM/timing/power.'}

    try:
        assert sha(ROOT / ACCEPTED) == ACCEPTED_SHA, 'validated/frozen draft 246-source manifest identity'
        accepted = json.loads((ROOT / ACCEPTED).read_text())
        assert len(accepted) == 246
        preserved = validate_context(ROOT, 'finalizer')
        run('vendor', ['python3', 'scripts/verify_vendor.py'])
        pins = [('rtl/aes/vendor/secworks/UPSTREAM.json', 'files'),
                (HASH + 'vendor/blake2/manifest.json', 'original_files')]
        for manifest, field in pins:
            path = ROOT / manifest
            for name, spec in json.loads(path.read_text())[field].items():
                digest = spec['sha256'] if isinstance(spec, dict) else spec
                assert sha(path.parent / name) == digest, name
        own = set(RTL) | {TEST + 'scratchpad_finalization_oracle.cpp', TEST + 'tb_scratchpad_finalization.v',
                         'scripts/scratchpad_finalization_fixture.py', 'scripts/test_scratchpad_finalization.py',
                         'tests/test_scratchpad_finalization_staging.py', '.github/workflows/regfile-blake2b.yml',
                         '.github/workflows/scratchpad-finalization.yml', ACCEPTED}
        assert sha(ROOT / FULL_MANIFEST) == FULL_MANIFEST_SHA, 'accepted program artifact manifest identity'
        bound = set(accepted) | own | {FULL_MANIFEST}
        bound |= {'vendor/randomx/' + path for path in json.loads((ROOT / 'vendor/randomx.sha256.json').read_text())}
        bound |= {'docs/validation/program-sequence-20261013/full-v2-8x2048/final-7.hex.gz',
                  'docs/validation/program-sequence-20261013/full-v2-8x2048/program-registers.hex'}
        bound.update(preserved['input_bindings'])
        input_hashes = {path: sha(ROOT / path) for path in sorted(bound)}
        save('inputs.json', input_hashes)
        save('preserved-inputs.json', {'validated_draft_parent': BASE, 'validated_draft_source_bindings': 246,
             'RandomX_original_files': 171, 'secworks_original_files': 3, 'BLAKE_original_files': 5,
             'all_original_IP_and_native_bytes_unchanged': True,
             'all_original_and_validated_draft_bytes_unchanged': preserved['all_original_and_accepted_bytes_unchanged'],
             **preserved})
        run('staging-guards', ['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests',
                              '-p', 'test_scratchpad_finalization_staging.py', '-v'])
        tools = {}
        for tool, flag in required:
            tools[tool] = tool_metadata(tool, flag)
        save('tools.json', tools)
        licenses = {'RandomX': 'vendor/randomx/LICENSE', 'secworks': 'rtl/aes/vendor/secworks/LICENSE',
                    'BLAKE2-original': HASH + 'vendor/blake2/LICENSE', 'OpenRX-AES': 'rtl/aes/LICENSE'}
        for label, path in licenses.items():
            shutil.copyfile(ROOT / path, out / ('LICENSE-' + label))
        native = out / 'scratchpad-finalization-oracle'
        run('compile-native-oracle', ['g++', '-O2', '-std=c++17', '-maes', '-Ivendor/randomx/src',
            TEST + 'scratchpad_finalization_oracle.cpp', 'vendor/randomx/src/aes_hash.cpp',
            'vendor/randomx/src/soft_aes.cpp', 'vendor/randomx/src/blake2/blake2b.c', '-o', str(native)])
        corpus = prepare(ROOT, out / 'fixtures', native)
        save('corpus.json', corpus)
        assert len(corpus['cases']) == 14 and len(corpus['abba_full_profiles']) == 4
        negatives = out / 'native-invalid'
        negatives.mkdir()
        for index, (scratch_bytes, register_bytes) in enumerate([(0, 256), (16, 256), (65, 256),
                                                               (2097216, 256), (64, 255), (64, 257)]):
            case_dir = negatives / str(index)
            case_dir.mkdir()
            memory_path, register_path = case_dir / 'scratchpad.bin', case_dir / 'register-file.bin'
            memory_path.write_bytes(bytes(scratch_bytes));register_path.write_bytes(bytes(register_bytes))
            run('native-invalid-' + str(index), [str(native), str(memory_path), str(register_path), str(case_dir)],
                expected_failure=True)
            text = (out / ('native-invalid-' + str(index) + '.log')).read_text()
            assert 'PASS native-finalization' not in text
            assert 'scratchpad length must be' in text or 'RegisterFile input must be exactly' in text
            assert {path.name for path in case_dir.iterdir()} == {'scratchpad.bin', 'register-file.bin'}
        by_name = {case['name']: case for case in corpus['cases']}
        sizes = sorted({case['scratchpad_bytes'] for case in corpus['cases']})
        executables = {size: compile_bench('rtl-' + str(size), size) for size in sizes}
        for index, case in enumerate(corpus['cases']):
            if case['scratchpad_bytes'] == 2097152:
                continue
            for mode in ['ideal', 'stalled']:
                label = 'rtl-' + case['name'] + '-' + mode
                summary['rtl'][label] = simulate(label, executables[case['scratchpad_bytes']], case, mode, index % 4)
        bounded = next(case for case in corpus['cases'] if case['scratchpad_bytes'] == 256 and case['kind'] == 'walking')
        for index, mode in enumerate(CONTROLS):
            label = 'rtl-control-' + mode
            summary['rtl'][label] = simulate(label, executables[256], bounded, mode, index % 4)
        for index, profile in enumerate(corpus['abba_full_profiles']):
            case = by_name[profile['case']]
            mode = 'stalled' if profile['stall'] else 'ideal'
            round_mode = (corpus['accepted_full_provenance']['round_mode']
                          if case['name'] == 'full-actual-final7' else index)
            label = 'rtl-full-' + str(index) + '-' + mode
            summary['rtl'][label] = simulate(label, executables[2097152], case, mode, round_mode)
            summary['full_profile_order'].append({'case': case['name'], 'mode': mode, 'round_mode': round_mode})
        full_case = by_name[corpus['abba_full_profiles'][0]['case']]
        for index, mode in enumerate(['invalid', 'error_first', 'reset_req', 'reset_read']):
            label = 'rtl-default-' + mode
            summary['rtl'][label] = simulate(label, executables[2097152], full_case, mode, index,
                                            restart_only=True)
        # Invalid fixed-size hardware parameters must fail elaboration.
        for size in [0, 63, 65, 2097216]:
            run('invalid-parameter-' + str(size), ['iverilog', '-g2012', '-s', 'randomx_scratchpad_aes_hash',
                 '-Prandomx_scratchpad_aes_hash.SCRATCHPAD_BYTES=' + str(size), '-o', str(out / 'invalid.vvp'),
                 *AES, SCANNER], expected_failure=True)
        if args.synthesize:
            installed = Path('/usr/share/yosys/simcells.v')
            assert installed.is_file() and 'Permission to use, copy, modify, and/or distribute' in installed.read_text()
            cell_model = out / 'yosys-simcells.v'
            shutil.copyfile(installed, cell_model)
            save('yosys-cell-model.json', {'installed_path': str(installed), 'sha256': sha(installed),
                 'copied_sha256': sha(cell_model), 'source': 'Installed Yosys release; preserved original ISC notice'})
            shutil.copyfile(cell_model, out / 'LICENSE-Yosys-simcells')
            _, summary['mapping']['scanner-default'] = synth('scanner-default', 'randomx_scratchpad_aes_hash', [*AES, SCANNER])
            default, summary['mapping']['finalizer-default'] = synth('finalizer-default', 'randomx_scratchpad_finalizer', RTL)
            bounded_net, summary['mapping']['finalizer-bounded256'] = synth('finalizer-bounded256', 'randomx_scratchpad_finalizer', RTL, 256)
            mapped = compile_bench('mapped-256', 256, bounded_net)
            for case in [case for case in corpus['cases'] if case['scratchpad_bytes'] == 256]:
                case_index = corpus['cases'].index(case)
                for mode in ['ideal', 'stalled']:
                    label = 'mapped-' + case['name'] + '-' + mode
                    reference = 'rtl-' + case['name'] + '-' + mode
                    summary['mapped'][label] = simulate(label, mapped, case, mode, case_index % 4, reference)
            for index, mode in enumerate(CONTROLS):
                label = 'mapped-control-' + mode
                summary['mapped'][label] = simulate(label, mapped, bounded, mode, index % 4, 'rtl-control-' + mode)
            mapped_default = compile_bench('mapped-default', 2097152, default)
            case = by_name[corpus['abba_full_profiles'][0]['case']]
            for index, mode in enumerate(['invalid', 'error_first', 'reset_req', 'reset_read']):
                label = 'mapped-default-' + mode
                summary['mapped'][label] = simulate(label, mapped_default, case, mode, index,
                    reference='rtl-default-' + mode, restart_only=True)
        summary['rtl_modes'] = len(summary['rtl'])
        summary['mapped_modes'] = len(summary['mapped'])
        summary['invalid_parameter_cases'] = 4
        summary['native_invalid_input_cases'] = 6
        fixture_hashes = json.loads((out / 'fixtures/artifacts.sha256.json').read_text())
        summary['fixture_inputs_unchanged_after_run'] = all(
            sha(out / 'fixtures' / path) == digest for path, digest in fixture_hashes.items())
        assert summary['fixture_inputs_unchanged_after_run']
        summary['source_unchanged_after_run'] = all(sha(ROOT / path) == digest for path, digest in input_hashes.items())
        assert summary['source_unchanged_after_run']
        assert summary['rtl_modes'] == 41
        assert summary['mapped_modes'] == (19 if args.synthesize else 0)
        summary['status'] = 'pass'
        print('PASS scratchpad_finalization_suite rtl_modes=' + str(summary['rtl_modes']) +
              ' mapped_modes=' + str(summary['mapped_modes']) + ' full_balanced_trials=4', flush=True)
    except Exception as error:
        summary['status'] = 'failed'
        summary['error'] = str(error)
        raise
    finally:
        save('summary.json', summary)
        save('pass-records.json', records)
        save('artifacts.sha256.json', {str(path.relative_to(out)): sha(path)
             for path in sorted(out.rglob('*')) if path.is_file() and path != out / 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
