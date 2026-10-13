#!/usr/bin/env python3
"""Pinned native differential for iteration memory/control, not a bytecode core."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = '5a688512041eb3c156ead207eb57ed83e375a5d2'
RTL = ['rtl/aes/vendor/secworks/aes_sbox.v', 'rtl/aes/vendor/secworks/aes_inv_sbox.v',
       'rtl/aes/randomx_aes_round.v', 'rtl/aes/randomx_v2_aes_mix.v',
       'rtl/aes/randomx_exec_aes_commit.v', 'rtl/iteration/randomx_iteration_store.v',
       'rtl/engine/randomx_i32_to_f64.v', 'rtl/engine/randomx_iteration_engine.v']
ORACLE = ['rtl/engine/tests/oracle.cpp', 'vendor/randomx/src/soft_aes.cpp',
          'vendor/randomx/src/bytecode_machine.cpp', 'vendor/randomx/src/instructions_portable.cpp',
          'vendor/randomx/src/reciprocal.c']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(source, marker, body=False):
    """Extract one pinned function using balanced braces; never rewrite its body."""
    start = source.index(marker)
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[opening + 1:end - 1] if body else source[start:end]


def extract(out):
    paths = ['vendor/randomx/src/vm_interpreted.cpp',
             'vendor/randomx/src/virtual_machine.cpp', 'vendor/randomx/src/bytecode_machine.hpp']
    vm, virtual, bytecode = [(ROOT / p).read_text() for p in paths]
    start = vm.index('\t\t\tuint64_t spMix =')
    iteration = vm[start:vm.index('\n\t\t}\n\n\t\tfor', start)]
    start = vm.index('\t\tuint64_t* datasetLine =')
    dataset = vm[start:vm.index('\n\t}\n', start)]
    generated = {
        'pinned_iteration.inc': (vm, iteration),
        'pinned_dataset_read.inc': (vm, dataset),
        'pinned_destructor.inc': (virtual, function(virtual, 'randomx_vm::~randomx_vm()')),
        'pinned_bytecode_loop.inc': (bytecode, function(bytecode, 'static void executeBytecode(', True)),
        'pinned_scratchpad_address.inc': (bytecode, function(bytecode, 'static void* getScratchpadAddress(')),
        'pinned_float_masks.inc': (virtual,
            function(virtual, 'static inline uint64_t getStaticExponent(') + '\n' +
            function(virtual, 'static inline uint64_t getFloatMask('))}
    for name, (source, data) in generated.items():
        (out / name).write_text(source[:source.index('*/') + 2] + '\n' + data)
    (out / 'extraction.json').write_text(json.dumps({
        'RandomX_commit': 'aaafe71322df6602c21a5c72937ac284724ae561',
        'source_sha256': {p: sha(ROOT / p) for p in paths},
        'policy': 'verbatim functions/bodies with upstream notices; observer invokes unchanged instruction implementation',
        'generated_sha256': {n: sha(out / n) for n in generated},
        'verbatim_body_sha256': {n: hashlib.sha256(v[1].encode()).hexdigest() for n, v in generated.items()}
    }, indent=2) + '\n')


def vectors(out):
    names = ('versions chains ev_start ev_count read0 read1 read2 read3 round_in round_out '
             'sp0 sp1 mx ma em0 em1 offset rin ain loadr loadf loade expr expf expe '
             'dsaddr pfaddr dsdata outr outf oute outmx outma fline rline fmem rmem').split()
    rows = [line.split() for line in (out / 'iterations.hex').read_text().splitlines()]
    events = [line.split() for line in (out / 'accesses.hex').read_text().splitlines()]
    summary = json.loads((out / 'oracle-summary.json').read_text())
    if len(rows) != 32 or len(events) > 8192:
        raise RuntimeError('fixture size differs from testbench')
    lines = [f'localparam integer TOTAL_EVENTS={len(events)}, '
             f'BYTECODE_READS={summary["bytecode_read64"]}, BYTECODE_STORES={summary["bytecode_store64"]};']
    for index, row in enumerate(rows):
        if len(row) != 38 or int(row[0]) != index:
            raise RuntimeError('bad iteration record')
        for column, (name, value) in enumerate(zip(names, row[1:])):
            literal = value if column < 10 else "'h" + value
            lines.append(f'{name}[{index}]={literal};')
    (out / 'case_vectors.vh').write_text('\n'.join(lines) + '\n')
    encoded = []
    for row in events:
        case, pc, write = map(int, row[:3])
        address, data = map(lambda s: int(s, 16), row[3:])
        if not (0 <= case < 32 and 0 <= pc < 384 and write in (0, 1) and
                0 <= address <= 2097152 - 8 and address % 8 == 0):
            raise RuntimeError('bad native memory event')
        encoded.append(f'{(write << 85) | (address << 64) | data:022x}')
    (out / 'events.mem').write_text('\n'.join(encoded) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('output must be outside source')
    if out.exists():
        parser.error('output must be fresh; preserve previous attempts')
    if any(c.isspace() or c in ';"\\' for c in str(out)):
        parser.error('output requires a quote-free path for HDL tools')
    for name in ['g++', 'iverilog', 'vvp'] + (['yosys'] if args.synthesize else []):
        if not shutil.which(name):
            parser.error('tool unavailable: ' + name)
    out.mkdir(parents=True)
    commands = []

    def run(label, argv, timeout=1200):
        record = {'label': label, 'argv': argv, 'cwd': 'repository-root', 'timeout_seconds': timeout}
        commands.append(record)
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print('START ' + label, flush=True)
        begin = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                               check=True, timeout=timeout)
            record['returncode'] = 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            record['error'] = str(error)
            raise
        finally:
            record['elapsed_seconds'] = time.monotonic() - begin
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print('PASS ' + label, flush=True)

    def manifest():
        (out / 'artifacts.sha256.json').write_text(json.dumps({p.name: sha(p) for p in
            sorted(out.iterdir()) if p.is_file() and p.name != 'artifacts.sha256.json'}, indent=2) + '\n')

    try:
        run('vendor', ['python3', 'scripts/verify_vendor.py'])
        preserved = {}
        for binding in ['docs/validation/aes-rtl-corrected-20261012/inputs.json',
                        'docs/validation/iteration-tail-v2-stalls-20261012/inputs.json']:
            inputs = json.loads((ROOT / binding).read_text())
            for path, digest in inputs.items():
                if sha(ROOT / path) != digest:
                    raise RuntimeError('merged input changed: ' + path)
            preserved[binding] = {'bindings_verified': len(inputs), 'sha256': sha(ROOT / binding)}
        (out / 'preserved-inputs.json').write_text(json.dumps(preserved, indent=2) + '\n')
        paths = set(RTL + ORACLE + ['scripts/test_iteration_engine.py', 'vendor/randomx.sha256.json',
            'vendor/randomx.lock.json', 'vendor/randomx/src/vm_interpreted.cpp',
            'vendor/randomx/src/virtual_machine.cpp', 'vendor/randomx/src/bytecode_machine.hpp'])
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT / 'rtl/engine/tests').glob('*') if p.is_file())
        (out / 'inputs.json').write_text(json.dumps({p: sha(ROOT / p) for p in sorted(paths)}, indent=2) + '\n')
        versions = {tool: subprocess.check_output([tool, flag], stderr=subprocess.STDOUT, text=True)
                    for tool, flag in [('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')] +
                    ([('yosys', '-V')] if args.synthesize else [])}
        (out / 'tools.json').write_text(json.dumps(versions, indent=2) + '\n')
        for src, dest in [('rtl/engine/LICENSE', 'LICENSE-OpenRX'),
                          ('rtl/aes/vendor/secworks/LICENSE', 'LICENSE-secworks'),
                          ('vendor/randomx/LICENSE', 'LICENSE-RandomX')]:
            shutil.copyfile(ROOT / src, out / dest)
        extract(out)
        run('compile-oracle', ['g++', '-std=c++11', '-O2', '-I' + str(out), '-Ivendor/randomx/src',
                              *ORACLE, '-o', str(out / 'oracle')])
        run('oracle', [str(out / 'oracle'), str(out)])
        if not (out / 'oracle.log').read_text().startswith('PASS pinned engine iterations=32'):
            raise RuntimeError('missing native oracle acceptance')
        oracle = vectors(out)
        run('compile-i32', ['iverilog', '-g2012', '-s', 'tb_i32', '-o', str(out / 'i32.vvp'),
                           'rtl/engine/randomx_i32_to_f64.v', 'rtl/engine/tests/tb_i32.v'])
        run('native-i32', ['vvp', str(out / 'i32.vvp'), '+vectors=' + str(out / 'i32-vectors.hex')])
        if (out / 'native-i32.log').read_text().splitlines()[0] != 'PASS native signed32-to-binary64 vectors=4096 rounding_modes=4':
            raise RuntimeError('missing native conversion acceptance')
        summary = {'base': BASE, 'scope': 'iteration memory/control with external arithmetic kernel and physical SRAM/dataset',
                   'oracle': oracle, 'conversion_vectors': 4096, 'conversion_rounding_modes': 4,
                   'configurations': {}, 'synthesis_requested': args.synthesize}
        plusargs = ['+initial=' + str(out / 'initial.hex'), '+final=' + str(out / 'final.hex'),
                    '+events=' + str(out / 'events.mem')]

        def differential(lanes, serial, coalesce, stall, label, netlist=None):
            flags = ['-DENGINE_NETLIST'] if netlist else []
            sources = [str(netlist)] if netlist else RTL
            run('compile-' + label, ['iverilog', '-g2012', '-Wall', *flags, '-I' + str(out),
                '-s', 'tb_engine', f'-Ptb_engine.LANES={lanes}',
                f'-Ptb_engine.SERIAL_CONVERT={serial}', f'-Ptb_engine.COALESCE_LINES={coalesce}',
                f'-Ptb_engine.STALL={stall}', '-o', str(out / (label + '.vvp')),
                *sources, 'rtl/engine/tests/tb_engine.v'])
            run(label, ['vvp', str(out / (label + '.vvp')), *plusargs])
            log = (out / (label + '.log')).read_text()
            expected = (f'PASS engine lanes={lanes} serial={serial} coalesce={coalesce} stall={stall} '
                        'iterations=32 v2=16 v1=16 chained=16 aliases=8 ')
            if not log.startswith(expected) or 'reset_aborts=3 committed_abort_writes=1' not in log:
                raise RuntimeError('missing differential/reset acceptance: ' + label)
            stats = {name: int(value) for name, value in re.findall(r'(\w+)=(\d+)', log)}
            if stats['bytecode_reads'] != oracle['bytecode_read64'] or stats['bytecode_stores'] != oracle['bytecode_store64']:
                raise RuntimeError('native memory counts differ')
            if not stall and stats['front_total_cycles'] != 2 * stats['entry_reads'] + 32 * (1 + 16 * serial):
                raise RuntimeError('ideal control-cycle accounting differs')
            return log, stats

        def arbitration(lanes, serial, coalesce, label, netlist=None):
            flags = ['-DENGINE_NETLIST'] if netlist else []
            sources = [str(netlist)] if netlist else RTL
            run('compile-' + label, ['iverilog', '-g2012', '-Wall', *flags,
                '-s', 'tb_arbitration', f'-Ptb_arbitration.LANES={lanes}',
                f'-Ptb_arbitration.SERIAL_CONVERT={serial}', f'-Ptb_arbitration.COALESCE_LINES={coalesce}',
                '-o', str(out / (label + '.vvp')), *sources, 'rtl/engine/tests/tb_arbitration.v'])
            run(label, ['vvp', str(out / (label + '.vvp'))])
            log = (out / (label + '.log')).read_text()
            expected = (f'PASS arbitration lanes={lanes} serial={serial} coalesce={coalesce} '
                'cases=3 v1=1 v2=2 reads=5 writes=3 read_stall_cycles=12 write_stall_cycles=8 '
                'response_stall_cycles=6 stale_drops=6 reset_held_grant=1 committed_bytes_preserved=1')
            if log.splitlines()[0] != expected:
                raise RuntimeError('missing overlapping arbitration acceptance: ' + label)
            return log, {name: int(value) for name, value in re.findall(r'(\w+)=(\d+)', log)}

        for name, lanes, serial, coalesce in [('A', 4, 1, 0), ('B', 4, 0, 0),
                                              ('C', 4, 0, 1), ('C-lanes1', 1, 0, 1)]:
            cfg = {'lanes': lanes, 'serial_convert': serial, 'coalesce_lines': coalesce, 'rtl': {}}
            summary['configurations'][name] = cfg
            for stall in (0, 1):
                _, cfg['rtl'][str(stall)] = differential(lanes, serial, coalesce, stall, f'rtl-{name}-{stall}')
            _, cfg['arbitration_rtl'] = arbitration(lanes, serial, coalesce, f'arbitration-rtl-{name}')
        for parameter, value in [('SERIAL_CONVERT', 2), ('COALESCE_LINES', 2)]:
            argv = ['iverilog', '-g2012', '-s', 'randomx_iteration_engine',
                    f'-Prandomx_iteration_engine.{parameter}={value}', '-o', str(out / ('invalid-' + parameter + '.vvp')), *RTL]
            bad = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            (out / ('invalid-' + parameter + '.log')).write_text(bad.stdout)
            commands.append({'label': 'invalid-' + parameter, 'argv': argv, 'returncode': bad.returncode,
                             'expected_failure': True, 'cwd': 'repository-root'})
            if bad.returncode == 0 or 'iteration_engine_requires_boolean_parameters' not in bad.stdout:
                raise RuntimeError('invalid parameter not rejected: ' + parameter)
        summary['invalid_parameters_rejected'] = True
        if args.synthesize:
            for name in ('A', 'C'):
                cfg = summary['configurations'][name]
                serial, coalesce = cfg['serial_convert'], cfg['coalesce_lines']
                netlist = out / ('netlist-' + name + '.v')
                cmd = (f'read_verilog {" ".join(RTL)}; chparam -set LANES 4 -set SERIAL_CONVERT {serial} '
                       f'-set COALESCE_LINES {coalesce} randomx_iteration_engine; '
                       'synth -top randomx_iteration_engine -flatten; check -assert; '
                       f'tee -o {out}/stat-{name}.txt stat; write_verilog -noattr {netlist}; '
                       f'write_json {out}/netlist-{name}.json')
                run('synth-' + name, ['yosys', '-p', cmd])
                module = json.loads((out / ('netlist-' + name + '.json')).read_text())['modules']['randomx_iteration_engine']
                types = Counter(cell['type'] for cell in module['cells'].values())
                cfg['generic_synthesis'] = {'num_cells': len(module['cells']),
                    'num_cells_by_type': dict(sorted(types.items())),
                    'flop_cells': sum(n for t, n in types.items() if 'DFF' in t),
                    'scope': 'generic flattened cells; excludes SRAM/dataset and external arithmetic kernel; no physical timing/power'}
                cfg['mapped'] = {}
                for stall in (0, 1):
                    log, cfg['mapped'][str(stall)] = differential(4, serial, coalesce, stall,
                        f'mapped-{name}-{stall}', netlist)
                    if log != (out / f'rtl-{name}-{stall}.log').read_text():
                        raise RuntimeError('mapped response/cycles differ from RTL: ' + name)
                log, cfg['arbitration_mapped'] = arbitration(4, serial, coalesce,
                    f'arbitration-mapped-{name}', netlist)
                if log != (out / f'arbitration-rtl-{name}.log').read_text():
                    raise RuntimeError('mapped arbitration differs from RTL: ' + name)
        a = summary['configurations']['A']['rtl']['0']
        b = summary['configurations']['B']['rtl']['0']
        c = summary['configurations']['C']['rtl']['0']
        summary['comparison'] = {'ideal_front_total_cycles_A_B_C': [a['front_total_cycles'], b['front_total_cycles'], c['front_total_cycles']],
            'parallel_conversion_cycles_saved_per_iteration': (a['front_total_cycles'] - b['front_total_cycles']) // 32,
            'coalesced_reads_saved_in_8_alias_cases': b['entry_reads'] - c['entry_reads'],
            'coalesced_cycles_saved_per_alias': (b['front_total_cycles'] - c['front_total_cycles']) // 8,
            'scope': 'specified minimum-latency port and controlled fixture; replayed kernel memory latency, not measured arithmetic latency or hash throughput'}
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2), flush=True)
    except Exception as error:
        (out / 'failure.json').write_text(json.dumps({'type': type(error).__name__, 'error': str(error)}, indent=2) + '\n')
        raise
    finally:
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        manifest()


if __name__ == '__main__':
    main()
