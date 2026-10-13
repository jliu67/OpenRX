#!/usr/bin/env python3
"""Native-generated program sequencing, tagged control and actual generic mapping.

The default profile is eight complete programs with four iterations each, in
both native versions and ideal/stalled transport. --full-v2 selects the unchanged
native eight-program/2048-iteration v2 counts. Dataset contents are an addressed
fixture. Scratchpad fill, program generation, interprogram BLAKE2b and final hash
remain outside the hardware boundary. Golden state never supplies DUT inputs.
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
from test_divsqrt_execute import RTL, V, LIBS
from hardfloat_compile_view import prepare as compile_view
from program_sequence_fixture import prepare

ROOT = Path(__file__).resolve().parents[1]
BASE = '7f299c74f81332257eefd775086b355969ad85f3'
CONTROL = 'rtl/execute/randomx_program_control.v'
TOP = 'rtl/execute/randomx_program_sequence.v'
TEST = 'rtl/execute/tests/'
NATIVE = [*LIBS, 'vendor/randomx/src/aes_hash.cpp', 'vendor/randomx/src/blake2/blake2b.c']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    parser.add_argument('--full-v2', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        parser.error('fresh output outside source required')
    if not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('unambiguous HDL output path required')
    if args.full_v2 and args.synthesize:
        parser.error('serialize the full native RTL profile and bounded mapping profiles separately')
    required = [('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')]
    if args.synthesize:
        required += [('yosys', '-V')]
    for tool, _ in required:
        if not shutil.which(tool):
            parser.error('tool missing: ' + tool)
    # The compiler driver supplies the installed Icarus VPI include directory.
    if not shutil.which('iverilog-vpi'):
        parser.error('installed Icarus VPI compiler driver missing')
    out.mkdir()
    commands = []
    summary = {'accepted_parent': BASE, 'programs': 8, 'native_iterations_per_program': 2048,
               'profile_iterations': 2048 if args.full_v2 else 4, 'full_v2_requested': args.full_v2,
               'synthesis_requested': args.synthesize, 'rtl': {}, 'mapping': {}, 'mapped': {},
               'boundary': 'RTL initializes entropy/config and sequences actual bytecode/iteration execution; '
                           'software supplies native initial scratchpad, programs from DUT-derived seeds, '
                           'interprogram BLAKE2b, and deterministic addressed dataset lines; final hash outside'}
    compat = None
    includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE']

    def run(label, argv, timeout=2400):
        if argv[0] == 'iverilog' and compat is not None:
            argv = [str(compat) if x == V + 'divSqrtRecFN_small.v' else x for x in argv]
        row = {'label': label, 'argv': argv, 'cwd': 'repository-root', 'timeout_seconds': timeout}
        commands.append(row)
        print('START ' + label, flush=True)
        started = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as stream:
                subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                               check=True, timeout=timeout)
            row['returncode'] = 0
        except Exception as exc:
            row['error'] = str(exc)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - started
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print('PASS ' + label, flush=True)

    def check(label, prefix, reference=None):
        line = (out / (label + '.log')).read_text().splitlines()[0]
        assert line.startswith(prefix), (label, line)
        if reference:
            assert line == (out / (reference + '.log')).read_text().splitlines()[0], label
        return {'record': line, **{k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', line)}}

    def fixture(label, iterations, v2):
        directory = out / label
        directory.mkdir()
        run('oracle-' + label, [str(out / 'oracle'), str(directory), '8', str(iterations), str(v2)])
        prepare(directory)
        return directory

    def connected(label, directory, iterations, v2, stall, flags=None, sources=None,
                  reset_program=False, reset_iteration=False, reference=None):
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes,
            '-I' + str(directory), *(flags or []), '-s', 'tb_program_sequence',
            '-Ptb_program_sequence.ITERATIONS=' + str(iterations),
            '-Ptb_program_sequence.V2=' + str(v2), '-Ptb_program_sequence.STALL=' + str(stall),
            '-Ptb_program_sequence.RESET_PROGRAM=' + str(int(reset_program)),
            '-Ptb_program_sequence.RESET_ITERATION=' + str(int(reset_iteration)),
            '-o', str(out / (label + '.vvp')), *(sources or [*RTL, CONTROL, TOP]),
            TEST + 'tb_program_sequence.v'])
        run(label, ['vvp', '-M' + str(out), '-mprogram_source', str(out / (label + '.vvp')),
                    '+directory=' + str(directory)], timeout=10800 if args.full_v2 else 2400)
        prefix = 'PASS program_sequence_first_iteration ' if reset_iteration else \
                 'PASS program_sequence_cancel ' if reset_program else 'PASS program_sequence '
        return check(label, prefix, reference)

    def control(label, directory, net=None, reference=None):
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-s', 'tb_program_control',
            *(['-DPROGRAM_CONTROL_NETLIST'] if net else []), '-o', str(out / (label + '.vvp')),
            str(net) if net else CONTROL, TEST + 'tb_program_control.v'])
        run(label, ['vvp', str(out / (label + '.vvp')), '+directory=' + str(directory)])
        return check(label, 'PASS program_control programs=8 iterations_per_program=2048 ', reference)

    def cancel(label, net=None, reference=None):
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes,
            *(['-DPROGRAM_SEQUENCE_NETLIST'] if net else []), '-s', 'tb_program_cancel',
            '-o', str(out / (label + '.vvp')), *([str(net)] if net else [*RTL, CONTROL, TOP]),
            TEST + 'tb_program_cancel.v'])
        run(label, ['vvp', str(out / (label + '.vvp'))])
        return check(label, 'PASS program_cancel ', reference)

    def synth(label, top, sources, iterations=None):
        net = out / ('netlist-' + label + '.v')
        script = 'read_verilog -Irtl/execute -I' + V + ' -I' + V + '8086-SSE ' + ' '.join(sources) + '; '
        if iterations is not None:
            script += f'chparam -set ITERATIONS {iterations} {top}; '
        script += f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
        script += f'write_verilog -noattr {net}; write_json {out}/netlist-{label}.json'
        run('synth-' + label, ['yosys', '-p', script], timeout=5400)
        counts = Counter()
        with (out / ('netlist-' + label + '.json')).open() as stream:
            for line in stream:
                match = re.fullmatch(r'\s*"type": "([^\"]+)",\s*\n?', line)
                if match:
                    counts[match[1]] += 1
        cells = int(re.search(r'Number of cells:\s*(\d+)', (out / ('stat-' + label + '.txt')).read_text()).group(1))
        assert cells == sum(counts.values())
        return net, {'num_cells': cells, 'flop_cells': sum(n for t, n in counts.items() if 'DFF' in t),
                     'num_cells_by_type': dict(sorted(counts.items())),
                     'programs': 8, 'iterations_per_program': iterations or 2048,
                     'scope': 'actual generic mapping; external memories/provider/physical timing and power excluded'}

    try:
        run('vendor', ['python3', 'scripts/verify_vendor.py'])
        parent_bindings = ROOT / 'docs/validation/divsqrt-execute-20261013/compat-rtl-inputs.json'
        accepted = json.loads(parent_bindings.read_text())
        for path, digest in accepted.items():
            assert sha(ROOT / path) == digest, path
        configuration = (ROOT / 'vendor/randomx/src/configuration.h').read_text()
        for name, expected in [('RANDOMX_PROGRAM_COUNT', 8), ('RANDOMX_PROGRAM_ITERATIONS', 2048),
                               ('RANDOMX_PROGRAM_SIZE_V1', 256), ('RANDOMX_PROGRAM_SIZE_V2', 384)]:
            assert int(re.search(r'^#define\s+' + name + r'\s+(\d+)', configuration, re.M).group(1)) == expected
        inputs = set(accepted) | set(RTL + NATIVE + [CONTROL, TOP, 'scripts/test_program_sequence.py',
            'scripts/program_sequence_fixture.py', TEST + 'program_native_helpers.hpp',
            TEST + 'program_sequence_oracle.cpp', TEST + 'program_source_vpi.cpp',
            TEST + 'tb_program_sequence.v', TEST + 'tb_program_control.v', TEST + 'tb_program_cancel.v',
            'vendor/randomx/src/program.hpp', 'vendor/randomx/src/blake2/blake2.h',
            'vendor/randomx/src/aes_hash.hpp', 'vendor/randomx/src/virtual_machine.hpp'])
        (out / 'inputs.json').write_text(json.dumps({p: sha(ROOT / p) for p in sorted(inputs)}, indent=2) + '\n')
        (out / 'preserved-inputs.json').write_text(json.dumps({'accepted_parent': BASE,
            'bindings': len(accepted), 'manifest_sha256': sha(parent_bindings),
            'all_accepted_driver_IP_RTL_bytes_unchanged': True}, indent=2) + '\n')
        (out / 'tools.json').write_text(json.dumps({tool: subprocess.check_output([tool, flag],
            stderr=subprocess.STDOUT, text=True) for tool, flag in required}, indent=2) + '\n')
        for source, name in [('rtl/execute/LICENSE', 'LICENSE-OpenRX'), ('vendor/randomx/LICENSE', 'LICENSE-RandomX'),
                             ('rtl/aes/vendor/secworks/LICENSE', 'LICENSE-secworks'), (V + 'LICENSE', 'LICENSE-HardFloat')]:
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
        (out / 'program-extraction.json').write_text(json.dumps({'policy': 'verbatim pinned native initialization/helper bodies with upstream notices',
            'source_sha256': sha(ROOT / 'vendor/randomx/src/virtual_machine.cpp'),
            'generated_sha256': {n: sha(out / n) for n in bodies}}, indent=2) + '\n')
        run('compile-oracle', ['g++', '-std=c++11', '-O2', '-I' + str(out), '-Ivendor/randomx/src',
            '-Irtl/execute/tests', TEST + 'program_sequence_oracle.cpp', *NATIVE, '-o', str(out / 'oracle')])
        cflags = subprocess.check_output(['iverilog-vpi', '--cflags'], text=True).split()
        vpi_include = [flag for flag in cflags if flag.startswith('-I')]
        assert vpi_include, 'Icarus VPI include directory unavailable'
        run('compile-vpi', ['g++', '-std=c++11', '-O2', '-fPIC', '-shared', *vpi_include,
            '-Ivendor/randomx/src', '-Irtl/execute/tests', TEST + 'program_source_vpi.cpp',
            'vendor/randomx/src/aes_hash.cpp', 'vendor/randomx/src/soft_aes.cpp',
            'vendor/randomx/src/blake2/blake2b.c', '-o', str(out / 'program_source.vpi')])
        if args.full_v2:
            directory = fixture('full-v2', 2048, 1)
            summary['rtl']['full-v2'] = connected('full-v2', directory, 2048, 1, 0)
        else:
            fixtures = {}
            for version in (1, 0):
                directory = fixture('v' + str(version) + '-short', 4, version)
                fixtures[version] = directory
                for stall in (0, 1):
                    label = f'rtl-{version}-{stall}'
                    summary['rtl'][label] = connected(label, directory, 4, version, stall)
                label = 'rtl-program-reset-' + str(version)
                summary['rtl'][label] = connected(label, directory, 4, version, 1, reset_program=True)
            summary['rtl']['control'] = control('rtl-control', fixtures[1])
            summary['rtl']['cancel'] = cancel('rtl-cancel')
            first = fixture('v2-first', 1, 1)
            summary['rtl']['first'] = connected('rtl-first', first, 1, 1, 1, reset_iteration=True)
            for programs, iterations in [(0, 2048), (9, 2048), (8, 0), (8, 2049)]:
                argv = ['iverilog', '-g2012', '-s', 'randomx_program_control',
                    f'-Prandomx_program_control.PROGRAMS={programs}', f'-Prandomx_program_control.ITERATIONS={iterations}',
                    '-o', str(out / 'invalid.vvp'), CONTROL]
                result = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                (out / f'invalid-{programs}-{iterations}.log').write_text(result.stdout)
                assert result.returncode and 'program_control_requires_PROGRAMS_1_to_8_and_ITERATIONS_1_to_2048' in result.stdout
            summary['invalid_parameters_rejected'] = 4
            if args.synthesize:
                net, counts = synth('control-default', 'randomx_program_control', [CONTROL])
                summary['mapping']['control-default'] = counts
                summary['mapped']['control-default'] = control('mapped-control-default', fixtures[1], net, 'rtl-control')
                net, counts = synth('control-short', 'randomx_program_control', [CONTROL], iterations=4)
                summary['mapping']['control-short'] = counts
                for version in (1, 0):
                    for stall in (0, 1):
                        label = f'mapped-control-{version}-{stall}'
                        summary['mapped'][label] = connected(label, fixtures[version], 4, version, stall,
                            ['-DPROGRAM_CONTROL_NETLIST'], [*RTL, str(net), TOP], reference=f'rtl-{version}-{stall}')
                    label = f'mapped-program-reset-{version}'
                    summary['mapped'][label] = connected(label, fixtures[version], 4, version, 1,
                        ['-DPROGRAM_CONTROL_NETLIST'], [*RTL, str(net), TOP], reset_program=True,
                        reference=f'rtl-program-reset-{version}')
                # Map the actual default8x2048 top; a bounded first native iteration
                # plus resets is used for gates. Complete count/transition behavior
                # is separately checked on default mapped control and short connected control.
                net, counts = synth('sequence-default', 'randomx_program_sequence', [*RTL, CONTROL, TOP])
                summary['mapping']['sequence-default'] = counts
                summary['mapped']['first'] = connected('mapped-first', first, 1, 1, 1,
                    ['-DPROGRAM_SEQUENCE_NETLIST'], [str(net)], reset_iteration=True, reference='rtl-first')
                summary['mapped']['cancel'] = cancel('mapped-cancel', net, 'rtl-cancel')
                summary['mapped_scope'] = 'default8x2048 control counts/contract; actual8x4 v1/v2 mapped-control transitions; '
                summary['mapped_scope'] += 'default whole-top gates validate one native v2 iteration and cancellation, not a full16384-iteration gate run'
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2), flush=True)
    except Exception as exc:
        (out / 'failure.json').write_text(json.dumps({'type': type(exc).__name__, 'error': str(exc)}, indent=2) + '\n')
        raise
    finally:
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        (out / 'artifacts.sha256.json').write_text(json.dumps({str(p.relative_to(out)): sha(p)
            for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'artifacts.sha256.json'}, indent=2) + '\n')


if __name__ == '__main__':
    main()
