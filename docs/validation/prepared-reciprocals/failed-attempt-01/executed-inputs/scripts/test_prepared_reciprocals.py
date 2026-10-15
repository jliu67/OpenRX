#!/usr/bin/env python3
"""Serialized correctness/cycle calibration of program reciprocal preparation.

This is an iteration-level candidate comparison with common immutable program
storage. Missing complete hash stages, real dataset/memory calibration and physical
PPA prevent full-hash performance acceptance. Run inside an admitted server payload.
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
from prepared_reciprocal_fixture import bindings, compile_command, extract, prepare
from hardfloat_compile_view import prepare as prepare_hardfloat_view
from test_iteration_engine import RTL as ENGINE

ROOT = Path(__file__).resolve().parents[1]
LOCK_FDS = (int(os.environ['OPENRX_RESOURCE_LOCK_FD']),) if 'OPENRX_RESOURCE_LOCK_FD' in os.environ else ()
BASE = '8f3b9bc3d7f0182d66185abe95310f0bab00274b'
V = 'rtl/execute/vendor/hardfloat/'
HF = [V + n for n in ['HardFloat_primitives.v', 'HardFloat_rawFN.v', 'isSigNaNRecFN.v',
      'fNToRecFN.v', 'recFNToFN.v', 'addRecFN.v', 'mulRecFN.v', '8086-SSE/HardFloat_specialize.v']]
FP = ['rtl/execute/randomx_fp64.v', 'rtl/execute/randomx_fp128.v']
DS = [V + 'divSqrtRecFN_small.v', 'rtl/execute/randomx_divsqrt64.v', 'rtl/execute/randomx_divsqrt128.v']
CORE = ['rtl/execute/randomx_integer_execute.v', 'rtl/execute/randomx_integer_iteration.v']
CACHE = 'rtl/execute/randomx_program_reciprocals.v'
GUARD = 'rtl/execute/randomx_prepared_rcp_guard.v'
WRAPPER = 'rtl/execute/randomx_prepared_integer_iteration.v'
RCP = 'rtl/execute/randomx_reciprocal32.v'
MUL = 'rtl/execute/randomx_mul64.v'
RTL = [*ENGINE, MUL, RCP, *CORE, *HF, *FP, *DS, CACHE, GUARD, WRAPPER]
T = 'rtl/execute/tests/'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

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
    if any(not shutil.which(tool) for tool, flag in required):
        parser.error('required installed tool missing')
    native_bindings = bindings(ROOT)
    out.mkdir()
    commands, records = [], {}
    inputs = {}
    summary = {'base': BASE, 'status': 'pending', 'rtl': {}, 'mapped': {}, 'mapping': {},
               'synthesis_requested': args.synthesize, 'full_hash_performance_accepted': False,
               'comparison': 'runtime/prepared reciprocal behavior behind identical immutable instruction storage',
               'skipped': [{'test': 'complete-pipeline-performance-acceptance',
                 'reason': 'Initial hash/fill/program AES, full actual dataset and connected final/interprogram hash pipeline are unavailable; no full-hash speed or physical PPA accepted.'}]}
    includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE', '-I' + str(out)]

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n')

    def run(label, argv, timeout=3600, expected_failure=False):
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout,
               'expected_failure': expected_failure}
        commands.append(row)
        print('START ' + label, flush=True)
        started = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                proc = subprocess.run(['/usr/bin/time', '-v', '-o', str(out / (label + '.time.txt')), *argv],
                                      cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout,
                                      pass_fds=LOCK_FDS)
            row['returncode'] = proc.returncode
            if expected_failure:
                assert proc.returncode != 0, label
            else:
                proc.check_returncode()
        except Exception as error:
            row['error'] = str(error)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - started
            save('commands.json', commands)
        print(('EXPECTED FAILURE ' if expected_failure else 'PASS ') + label, flush=True)

    def pass_record(label, prefix, reference=None):
        text = (out / (label + '.log')).read_text()
        lines = [line for line in text.splitlines() if line.startswith('PASS ')]
        assert len(lines) == 1 and lines[0].startswith(prefix), (label, text[-2000:])
        assert 'FATAL:' not in text and not any(line.startswith('FAIL ') for line in text.splitlines())
        if reference:
            assert lines[0] == records[reference], (label, lines[0], records[reference])
        records[label] = lines[0]
        return {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', lines[0])}

    def cache_test(label, prepared, stall, net=None, guard_net=None, cell_model=None):
        executable = out / (label + '.vvp')
        sources = [str(net), str(guard_net), str(cell_model)] if net else [RCP, CACHE, GUARD]
        flags = ['-DPROGRAM_RECIPROCALS_NETLIST'] if net else []
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes, *flags,
            '-s', 'tb_prepared_reciprocals', '-Ptb_prepared_reciprocals.PREPARE_RCP=' + str(prepared),
            '-Ptb_prepared_reciprocals.STALL=' + str(stall), '-o', str(executable),
            *sources, T + 'tb_prepared_reciprocals.v'])
        run(label, ['vvp', str(executable), '+DIR=' + str(out)])
        return pass_record(label, 'PASS prepared_reciprocals ',
                           'rtl-cache-' + str(prepared) + '-' + str(stall) if net else None)

    def synthesis(label, top, sources, parameter=None):
        net = out / ('netlist-' + label + '.v')
        script = 'read_verilog -Irtl/execute ' + ' '.join(sources) + '; '
        if parameter:
            script += f'chparam -set {parameter[0]} {parameter[1]} {top}; '
        script += f'hierarchy -top {top}; proc; opt; tee -o {out}/storage-{label}.txt stat; memory_collect; '
        script += f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
        script += f'write_verilog -noattr {net}; write_json {out}/netlist-{label}.json'
        run('synth-' + label, ['yosys', '-p', script], timeout=7200)
        types = Counter()
        with (out / ('netlist-' + label + '.json')).open() as stream:
            for line in stream:
                match = re.fullmatch(r'\s*"type": "([^"]+)",\s*\n?', line)
                if match:
                    types[match[1]] += 1
        cells = int(re.search(r'Number of cells:\s*(\d+)', (out / ('stat-' + label + '.txt')).read_text()).group(1))
        assert cells == sum(types.values())
        return net, {'cells': cells, 'flop_cells': sum(n for t, n in types.items() if 'DFF' in t),
                     'latch_cells': sum(n for t, n in types.items() if 'DLATCH' in t),
                     'cell_types': dict(sorted(types.items())), 'top': top, 'parameter': parameter,
                     'scope': 'Actual default new store/control or guard; generic gates, no backend/physical SRAM/timing/power acceptance'}

    try:
        run('vendor', ['python3', 'scripts/verify_vendor.py'])
        hf = json.loads((ROOT / V / 'manifest.json').read_text())
        for name, digest in hf['files'].items():
            assert sha(ROOT / V / name) == digest, name
        aes = json.loads((ROOT / 'rtl/aes/vendor/secworks/UPSTREAM.json').read_text())
        for name, row in aes['files'].items():
            assert sha(ROOT / 'rtl/aes/vendor/secworks' / name) == row['sha256'], name
        own = [CACHE, GUARD, WRAPPER, 'scripts/test_prepared_reciprocals.py', 'scripts/reciprocal_cycle_model.py',
               'tests/test_reciprocal_cycle_model.py', '.github/workflows/prepared-reciprocals.yml',
               'docs/validation/prepared-reciprocals/surrounding-stages.json',
               T + 'tb_prepared_reciprocals.v', T + 'tb_prepared_reciprocal_iteration.v']
        all_sources = set(native_bindings) | set(RTL) | set(own) | {V + n for n in hf['files']}
        all_sources |= {V + 'manifest.json', 'rtl/aes/vendor/secworks/UPSTREAM.json',
                        'rtl/execute/randomx_opcode_ceils.vh', 'scripts/hardfloat_compile_view.py',
                        T + 'tb_integer_transport.v'}
        inputs = {name: sha(ROOT / name) for name in sorted(all_sources)}
        save('inputs.json', inputs)
        save('preserved-inputs.json', {'native_originals': 171, 'HardFloat_originals': len(hf['files']),
              'secworks_originals': len(aes['files']), 'all_original_bytes_unchanged': True,
              'intentional_executor_changes': CORE, 'base': BASE})
        versions = {}
        for tool, flag in required:
            path = Path(shutil.which(tool)).resolve()
            proc = subprocess.run([tool, flag], capture_output=True, text=True)
            versions[tool] = {'path': str(path), 'sha256': sha(path), 'stdout': proc.stdout,
                              'stderr': proc.stderr, 'returncode': proc.returncode}
        save('tools.json', versions)
        for name, path in [('OpenRX', 'rtl/execute/LICENSE'), ('RandomX', 'vendor/randomx/LICENSE'),
                           ('secworks', 'rtl/aes/vendor/secworks/LICENSE'), ('HardFloat', V + 'LICENSE')]:
            shutil.copyfile(ROOT / path, out / ('LICENSE-' + name))
        run('model-guards', ['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests',
                            '-p', 'test_reciprocal_cycle_model.py', '-v'])
        extract(out, ROOT)
        run('compile-native-oracle', compile_command(out, ROOT))
        run('native-oracle', [str(out / 'oracle'), str(out)])
        summary['coverage'] = prepare(out, ROOT)
        compatibility = prepare_hardfloat_view(ROOT / DS[0], out)
        compile_sources = [str(compatibility) if name == DS[0] else name for name in RTL]
        for label, top, parameter, value, flags in [
            ('invalid-cache', 'randomx_program_reciprocals', 'PREPARE_RCP', 2, []),
            ('invalid-executor', 'randomx_integer_execute', 'PREPARED_RCP', 2, []),
            ('invalid-legacy-netlist', 'randomx_integer_iteration', 'PREPARED_RCP', 1, ['-DINTEGER_EXECUTE_NETLIST'])]:
            run(label, ['iverilog', '-g2012', *includes, *flags, '-s', top,
                '-P' + top + '.' + parameter + '=' + str(value), '-o', str(out / (label + '.vvp')),
                *compile_sources], expected_failure=True)
            assert 'requires_' in (out / (label + '.log')).read_text(), label
        summary['invalid_parameter_or_abi_guards'] = 3
        for prepared in (0, 1):
            for stall in (0, 1):
                label = f'rtl-cache-{prepared}-{stall}'
                summary['rtl'][label] = cache_test(label, prepared, stall)
        # Balanced configuration order; identical gold and event-ordinal memory profiles.
        summary['paired_order'] = []
        for prepared, stall in [(0, 0), (1, 1), (1, 0), (0, 1)]:
            label = f'rtl-iteration-{prepared}-{stall}'
            executable = out / (label + '.vvp')
            run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes,
                '-s', 'tb_prepared_reciprocal_iteration', '-Ptb_prepared_reciprocal_iteration.PREPARED_RCP=' + str(prepared),
                '-Ptb_prepared_reciprocal_iteration.STALL=' + str(stall), '-o', str(executable),
                *compile_sources, T + 'tb_prepared_reciprocal_iteration.v'])
            run(label, ['vvp', str(executable), '+DIR=' + str(out), '+CONTROL=1',
                        '+METRICS=' + str(out / f'integration-{prepared}-{stall}.json')])
            summary['rtl'][label] = pass_record(label, 'PASS prepared_reciprocal_iteration ')
            summary['paired_order'].append({'prepared': prepared, 'stall': stall})
        label = 'rtl-core-guard'
        executable = out / (label + '.vvp')
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes,
            '-s', 'tb_prepared_rcp_core_guard', '-o', str(executable), *compile_sources,
            T + 'tb_prepared_reciprocals.v'])
        run(label, ['vvp', str(executable)])
        summary['rtl'][label] = pass_record(label, 'PASS prepared_rcp_core_guard ')
        for serial in (0, 1):
            label = 'rtl-default-transport-' + str(serial)
            executable = out / (label + '.vvp')
            run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes, '-s', 'tb_integer_transport',
                '-Ptb_integer_transport.SERIAL_IADD=' + str(serial), '-o', str(executable),
                *compile_sources, T + 'tb_integer_transport.v'])
            run(label, ['vvp', str(executable)])
            summary['rtl'][label] = pass_record(label, 'PASS integer_transport ')
        run('cycle-model', ['python3', 'scripts/reciprocal_cycle_model.py', '--directory', str(out)])
        summary['cycle_model'] = json.loads((out / 'cycle-model.json').read_text())
        if args.synthesize:
            installed = Path('/usr/share/yosys/simcells.v')
            assert 'Permission to use, copy, modify, and/or distribute' in installed.read_text()
            model = out / 'yosys-simcells.v'
            shutil.copyfile(installed, model);shutil.copyfile(model, out / 'LICENSE-Yosys-simcells')
            save('yosys-cell-model.json', {'installed_path': str(installed), 'sha256': sha(installed),
                                        'copied_sha256': sha(model), 'original_ISC_notice_preserved': True})
            nets = {}
            for prepared in (0, 1):
                label = 'cache-' + str(prepared)
                nets[prepared], summary['mapping'][label] = synthesis(label, 'randomx_program_reciprocals',
                                                       [RCP, CACHE], ('PREPARE_RCP', prepared))
            guard_net, summary['mapping']['guard'] = synthesis('guard', 'randomx_prepared_rcp_guard', [GUARD])
            for prepared in (0, 1):
                for stall in (0, 1):
                    label = f'mapped-cache-{prepared}-{stall}'
                    summary['mapped'][label] = cache_test(label, prepared, stall, nets[prepared], guard_net, model)
        expected = json.loads((out / 'prepared-reciprocal-fixture-inputs.json').read_text())
        summary['native_fixture_bytes_unchanged'] = all(sha(out / name) == digest for name, digest in expected['fixture_sha256'].items())
        summary['source_bytes_unchanged'] = all(sha(ROOT / name) == digest for name, digest in inputs.items())
        assert summary['native_fixture_bytes_unchanged'] and summary['source_bytes_unchanged']
        assert len(summary['rtl']) == 11 and len(summary['mapped']) == (4 if args.synthesize else 0)
        summary.update(status='pass', rtl_checks=11, mapped_checks=len(summary['mapped']),
                       unexpected_failures=0, skipped_checks=len(summary['skipped']))
        print('PASS prepared_reciprocal_suite rtl_checks=11 mapped_checks=' + str(len(summary['mapped'])) +
              ' native_iterations=48 admissions=12 skipped_complete_pipeline=1 unexpected_failures=0', flush=True)
    except Exception as error:
        summary['status'] = 'failed';summary['error'] = str(error)
        summary['unexpected_failures'] = 1
        raise
    finally:
        save('summary.json', summary);save('pass-records.json', records)
        save('artifacts.sha256.json', {str(path.relative_to(out)): sha(path) for path in sorted(out.rglob('*'))
                                     if path.is_file() and path != out / 'artifacts.sha256.json'})

if __name__ == '__main__':
    main()
