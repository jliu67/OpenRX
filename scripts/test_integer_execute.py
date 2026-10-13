#!/usr/bin/env python3
"""Actual integer RTL/native differential; unsupported operations trap explicitly."""
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
from test_iteration_engine import extract, RTL as ENGINE_RTL

ROOT = Path(__file__).resolve().parents[1]
BASE = 'a6450ceccd32848c438c7dcae6acb98695d2a0e8'
KERNEL = 'rtl/execute/randomx_integer_execute.v'
WRAPPER = 'rtl/execute/randomx_integer_iteration.v'
RTL = [*ENGINE_RTL, KERNEL, WRAPPER]
SUPPORTED = {'IADD_RS', 'IADD_M', 'ISUB_R', 'ISUB_M', 'INEG_R', 'IXOR_R',
             'IXOR_M', 'IROR_R', 'IROL_R', 'ISWAP_R', 'ISTORE'}
ORACLE = ['rtl/execute/tests/oracle.cpp', 'vendor/randomx/src/soft_aes.cpp',
          'vendor/randomx/src/bytecode_machine.cpp', 'vendor/randomx/src/instructions_portable.cpp',
          'vendor/randomx/src/reciprocal.c']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def opcode_map(out):
    configuration = (ROOT / 'vendor/randomx/src/configuration.h').read_text()
    frequencies = re.findall(r'^#define RANDOMX_FREQ_(\w+)\s+(\d+)\s*$', configuration, re.M)
    kinds, ceils = [], {}
    for kind, frequency in frequencies:
        kinds.extend([kind] * int(frequency))
        ceils[kind] = len(kinds)
    declared = {name: int(value) for name, value in re.findall(
        r'localparam integer CEIL_(\w+)=(\d+);', (ROOT / 'rtl/execute/randomx_opcode_ceils.vh').read_text())}
    if len(kinds) != 256 or ceils != declared:
        raise RuntimeError('RTL weighted opcode ceilings differ from pinned native configuration')
    accepted = [opcode for opcode, kind in enumerate(kinds) if kind in SUPPORTED]
    if len(accepted) != 98:
        raise RuntimeError('supported opcode coverage changed')
    (out / 'unsupported.mem').write_text('\n'.join('0' if kind in SUPPORTED else '1' for kind in kinds) + '\n')
    (out / 'opcode-map.json').write_text(json.dumps({'pin': 'aaafe71322df6602c21a5c72937ac284724ae561',
        'ceils': ceils, 'supported_families': sorted(SUPPORTED), 'supported_raw_opcodes': accepted,
        'unsupported_raw_opcodes': [opcode for opcode in range(256) if opcode not in accepted]}, indent=2) + '\n')
    return kinds, accepted


def vectors(out, kinds, accepted):
    names = ('versions chains ev_start ev_count read0 read1 read2 read3 round_in round_out '
             'sp0 sp1 mx ma em0 em1 offset rin ain loadr loadf loade expr expf expe '
             'dsaddr pfaddr dsdata outr outf oute outmx outma fline rline fmem rmem').split()
    rows = [line.split() for line in (out / 'iterations.hex').read_text().splitlines()]
    events = [line.split() for line in (out / 'accesses.hex').read_text().splitlines()]
    oracle = json.loads((out / 'oracle-summary.json').read_text())
    if len(rows) != 8 or len(events) > 2048:
        raise RuntimeError('fixture size differs from integer testbench')
    lines = [f'localparam integer TOTAL_EVENTS={len(events)}, '
             f'BYTECODE_READS={oracle["bytecode_read64"]}, BYTECODE_STORES={oracle["bytecode_store64"]};']
    for index, row in enumerate(rows):
        if len(row) != 38 or int(row[0]) != index:
            raise RuntimeError('bad native iteration record')
        for column, (name, value) in enumerate(zip(names, row[1:])):
            lines.append(f'{name}[{index}]=' + (value if column < 10 else "'h" + value) + ';')
    (out / 'integer_vectors.vh').write_text('\n'.join(lines) + '\n')
    encoded = []
    memory_events = {}
    for row in events:
        case, pc, write = map(int, row[:3])
        address, data = [int(value, 16) for value in row[3:]]
        if not (0 <= case < 8 and 0 <= pc < (384 if case < 4 else 256) and write in (0, 1)
                and 0 <= address <= 2097152 - 8 and address % 8 == 0):
            raise RuntimeError('bad native memory event')
        encoded.append(f'{(write << 85) | (address << 64) | data:022x}')
        memory_events[case, pc] = (write, address, data)
    (out / 'events.mem').write_text('\n'.join(encoded) + '\n')
    programs = [0] * 4096
    states = [0] * 4096
    raw, counts, rotates, shifts, masks, immediates = set(), Counter(), set(), set(), set(), set()
    instructions = {}
    for row in (out / 'programs.hex').read_text().splitlines():
        case, pc, word = row.split()
        case, pc, word = int(case), int(pc), int(word, 16)
        if not (0 <= case < 8 and 0 <= pc < (384 if case < 4 else 256)) or (case, pc) in instructions:
            raise RuntimeError('invalid/duplicate native program word')
        programs[case * 512 + pc] = word
        instructions[case, pc] = word
        if word & 255 not in accepted:
            raise RuntimeError('native supported fixture contains unsupported opcode')
    before = {case: int(row[1 + names.index('loadr')], 16) for case, row in enumerate(rows)}
    seen_steps = set()
    for row in (out / 'instruction-steps.hex').read_text().splitlines():
        case, pc, opcode, word = row.split()
        case, pc, opcode, word = int(case), int(pc), int(opcode), int(word, 16)
        if (case, pc) in seen_steps or (case, pc) not in instructions:
            raise RuntimeError('invalid/duplicate native instruction step')
        seen_steps.add((case, pc))
        instruction = instructions[case, pc]
        if instruction & 255 != opcode:
            raise RuntimeError('native instruction/retirement opcode differs')
        states[case * 512 + pc] = word
        kind = kinds[opcode]
        dst, src, mod, imm = (instruction >> 8) & 7, (instruction >> 16) & 7, (instruction >> 24) & 255, instruction >> 32
        r = [(before[case] >> (64 * reg)) & ((1 << 64) - 1) for reg in range(8)]
        immediate = (imm if imm < 1 << 31 else imm - (1 << 32)) & ((1 << 64) - 1)
        counts[kind] += 1
        raw.add(opcode)
        immediates.add(imm)
        if kind in ('IROR_R', 'IROL_R'):
            rotates.add((imm if dst == src else r[src]) & 63)
        if kind == 'IADD_RS':
            shift = (mod >> 2) & 3
            shifts.add(shift)
            counts['register5_displacements'] += dst == 5
            operand = (((r[src] << shift) & ((1 << 64) - 1)) + (immediate if dst == 5 else 0)) & ((1 << 64) - 1)
            counts['addition_wraps'] += r[dst] + operand >= 1 << 64
        if kind in ('ISUB_R', 'IXOR_R'):
            counts['equal_register_immediates'] += dst == src
        if kind == 'ISUB_R':
            counts['subtraction_wraps'] += r[dst] < (immediate if dst == src else r[src])
        if kind == 'ISWAP_R':
            counts['equal_register_swap_nops'] += dst == src
        if kind.endswith('_M') or kind == 'ISTORE':
            mask = 'L3' if (kind == 'ISTORE' and mod >> 4 >= 14 or kind != 'ISTORE' and dst == src) else ('L1' if mod & 3 else 'L2')
            masks.add(mask)
            counts['zero_base_L3_loads'] += kind != 'ISTORE' and dst == src
            counts['store_upper_half' if memory_events[case, pc][1] & 8 else 'store_lower_half'] += kind == 'ISTORE'
        before[case] = word
    if len(instructions) != 2560 or seen_steps != set(instructions) or raw != set(accepted):
        raise RuntimeError('native full-size/raw-opcode coverage differs')
    if rotates != set(range(64)) or shifts != set(range(4)) or masks != {'L1', 'L2', 'L3'}:
        raise RuntimeError('missing native shift/rotate/address-mask coverage')
    if any(not counts[key] for key in ('addition_wraps', 'subtraction_wraps', 'register5_displacements',
                                      'equal_register_immediates', 'equal_register_swap_nops', 'zero_base_L3_loads',
                                      'store_lower_half', 'store_upper_half')):
        raise RuntimeError('missing required integer edge coverage')
    (out / 'programs.mem').write_text('\n'.join(f'{word:016x}' for word in programs) + '\n')
    (out / 'steps.mem').write_text('\n'.join(f'{word:0128x}' for word in states) + '\n')
    coverage = {'native_instructions': len(instructions), 'supported_raw_opcodes_observed': sorted(raw),
                'rotate_counts_observed': sorted(rotates), 'shift_counts_observed': sorted(shifts),
                'memory_masks_observed': sorted(masks), 'imm32_values_observed': sorted(immediates),
                'counts': dict(counts), 'policy': 'coverage observations only; expected execution comes from unchanged native BytecodeMachine'}
    (out / 'coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
    return oracle, coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    parser.add_argument('--transport-only', action='store_true', help='focused raw-field/return checks; does not rerun synthesis')
    parser.add_argument('--mapped-from', type=Path, help='reuse digest-verified unchanged kernel netlists for --transport-only')
    args = parser.parse_args()
    if args.mapped_from and (not args.transport_only or args.synthesize):
        parser.error('--mapped-from requires focused --transport-only without synthesis')
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents or out.exists():
        parser.error('output must be fresh and outside source; preserve previous attempts')
    if not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('output requires an unambiguous path for HDL tools')
    tools = [('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')] + ([('yosys', '-V')] if args.synthesize else [])
    for tool, _ in tools:
        if not shutil.which(tool):
            parser.error('tool unavailable: ' + tool)
    out.mkdir(parents=True)
    commands = []

    def run(label, argv, timeout=1200):
        record = {'label': label, 'argv': argv, 'cwd': 'repository-root', 'timeout_seconds': timeout}
        commands.append(record)
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print('START ' + label, flush=True)
        start = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as log:
                subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout)
            record['returncode'] = 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            record['error'] = str(error)
            raise
        finally:
            record['elapsed_seconds'] = time.monotonic() - start
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print('PASS ' + label, flush=True)

    def transport(serial, label, netlist=None):
        flags = ['-DINTEGER_EXECUTE_NETLIST'] if netlist else []
        source = str(netlist) if netlist else KERNEL
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *flags, '-Irtl/execute',
            '-s', 'tb_integer_transport', f'-Ptb_integer_transport.SERIAL_IADD={serial}',
            '-o', str(out / (label + '.vvp')), source, 'rtl/execute/tests/tb_integer_transport.v'])
        run(label, ['vvp', str(out / (label + '.vvp'))])
        log = (out / (label + '.log')).read_text()
        expected = (f'PASS integer_transport serial_iadd={serial} contexts=8 v1=4 v2=4 rounding_modes=4 '
            'native_swap_nops=2560 stale_program_drops=2560 return_stall_clocks=24 raw_FE_bits_preserved=1 inactive_request_bus_ignored=1')
        if log.splitlines()[0] != expected:
            raise RuntimeError('raw field/held return acceptance missing: ' + label)
        if netlist and log.splitlines()[0] != (out / f'rtl-{serial}-transport.log').read_text().splitlines()[0]:
            raise RuntimeError('mapped transport differs from RTL')
        return {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', log.splitlines()[0])}

    def manifest():
        (out / 'artifacts.sha256.json').write_text(json.dumps({path.name: sha(path) for path in sorted(out.iterdir())
            if path.is_file() and path.name != 'artifacts.sha256.json'}, indent=2) + '\n')

    try:
        run('vendor', ['python3', 'scripts/verify_vendor.py'])
        preserved = {}
        for binding in ['docs/validation/aes-rtl-corrected-20261012/inputs.json',
                        'docs/validation/iteration-tail-v2-stalls-20261012/inputs.json',
                        'docs/validation/iteration-engine-read-grant-20261013/rtl-inputs.json']:
            inputs = json.loads((ROOT / binding).read_text())
            for path, digest in inputs.items():
                if sha(ROOT / path) != digest:
                    raise RuntimeError('accepted component input changed: ' + path)
            preserved[binding] = {'bindings_verified': len(inputs), 'sha256': sha(ROOT / binding)}
        (out / 'preserved-inputs.json').write_text(json.dumps(preserved, indent=2) + '\n')
        paths = set(RTL + ORACLE + ['rtl/execute/randomx_opcode_ceils.vh', 'scripts/test_integer_execute.py',
            'scripts/test_iteration_engine.py', 'vendor/randomx.sha256.json', 'vendor/randomx.lock.json',
            'vendor/randomx/src/configuration.h', 'vendor/randomx/src/vm_interpreted.cpp',
            'vendor/randomx/src/virtual_machine.cpp', 'vendor/randomx/src/bytecode_machine.hpp'])
        paths.update(str(path.relative_to(ROOT)) for path in (ROOT / 'rtl/execute/tests').glob('*') if path.is_file())
        (out / 'inputs.json').write_text(json.dumps({path: sha(ROOT / path) for path in sorted(paths)}, indent=2) + '\n')
        versions = {tool: subprocess.check_output([tool, flag], text=True, stderr=subprocess.STDOUT) for tool, flag in tools}
        (out / 'tools.json').write_text(json.dumps(versions, indent=2) + '\n')
        for src, dest in [('rtl/execute/LICENSE', 'LICENSE-OpenRX'), ('rtl/aes/vendor/secworks/LICENSE', 'LICENSE-secworks'),
                          ('vendor/randomx/LICENSE', 'LICENSE-RandomX')]:
            shutil.copyfile(ROOT / src, out / dest)
        kinds, accepted = opcode_map(out)
        if args.transport_only:
            focused = {'base': BASE, 'scope': 'raw fields, all rounding modes, native swap NOPs and held return; RTL unchanged',
                       'rtl': {}, 'mapped': {}, 'synthesis_rerun': False}
            for serial in (0, 1):
                focused['rtl'][str(serial)] = transport(serial, f'rtl-{serial}-transport')
            if args.mapped_from:
                prior = args.mapped_from.resolve()
                prior_inputs = json.loads((prior / 'inputs.json').read_text())
                prior_artifacts = json.loads((prior / 'artifacts.sha256.json').read_text())
                for path in [*RTL, 'rtl/execute/randomx_opcode_ceils.vh']:
                    if prior_inputs[path] != sha(ROOT / path):
                        raise RuntimeError('cannot reuse mapped RTL with changed input: ' + path)
                prior_summary = json.loads((prior / 'summary.json').read_text())
                if not prior_summary['synthesis_requested'] or not prior_summary.get('mapped_integrated_default'):
                    raise RuntimeError('prior complete mapped validation missing')
                focused['prior_synthesis'] = {'input_manifest_sha256': sha(prior / 'inputs.json'),
                    'artifact_manifest_sha256': sha(prior / 'artifacts.sha256.json'),
                    'summary_sha256': sha(prior / 'summary.json'), 'netlists': {}}
                for serial in (0, 1):
                    name = f'netlist-kernel-{serial}.v'
                    if sha(prior / name) != prior_artifacts[name]:
                        raise RuntimeError('prior kernel netlist digest differs')
                    netlist = out / name
                    shutil.copyfile(prior / name, netlist)
                    focused['prior_synthesis']['netlists'][name] = sha(netlist)
                    focused['mapped'][str(serial)] = transport(serial, f'mapped-kernel-{serial}-transport', netlist)
            (out / 'summary.json').write_text(json.dumps(focused, indent=2) + '\n')
            print(json.dumps(focused, indent=2), flush=True)
            return
        extract(out)
        run('compile-oracle', ['g++', '-std=c++11', '-O2', '-I' + str(out), '-Ivendor/randomx/src', *ORACLE, '-o', str(out / 'oracle')])
        run('oracle', [str(out / 'oracle'), str(out)])
        if not (out / 'oracle.log').read_text().startswith('PASS native integer iterations=8'):
            raise RuntimeError('native oracle acceptance missing')
        oracle, coverage = vectors(out, kinds, accepted)
        summary = {'base': BASE, 'scope': 'native integer subset, connected iteration controller; external ROM/SRAM/dataset model',
                   'oracle': oracle, 'coverage': coverage, 'rtl': {}, 'kernel_synthesis': {},
                   'mapped_kernels_with_RTL_controller': {}, 'synthesis_requested': args.synthesize}
        plusargs = ['+initial=' + str(out / 'initial.hex'), '+final=' + str(out / 'final.hex'),
                    '+events=' + str(out / 'events.mem'), '+programs=' + str(out / 'programs.mem'), '+steps=' + str(out / 'steps.mem')]

        def tests(serial, label, kernel=None, integrated=None):
            flags = ['-DINTEGER_ITERATION_NETLIST'] if integrated else (['-DINTEGER_EXECUTE_NETLIST'] if kernel else [])
            sources = [str(integrated)] if integrated else ([*ENGINE_RTL, str(kernel), WRAPPER] if kernel else RTL)
            results = {}
            for stall in (0, 1):
                name = f'{label}-{stall}'
                run('compile-' + name, ['iverilog', '-g2012', '-Wall', *flags, '-Irtl/execute', '-I' + str(out),
                    '-s', 'tb_integer_iteration', f'-Ptb_integer_iteration.SERIAL_IADD={serial}', f'-Ptb_integer_iteration.STALL={stall}',
                    '-o', str(out / (name + '.vvp')), *sources, 'rtl/execute/tests/tb_integer_iteration.v'])
                run(name, ['vvp', str(out / (name + '.vvp')), *plusargs])
                log = (out / (name + '.log')).read_text()
                expected = f'PASS integer_hardware serial_iadd={serial} stall={stall} iterations=8 v2=4 v1=4 chains=4 aliases=4 fetched=2560 actual_RTL_retirements=2560 iadd_rs=236 '
                if not log.startswith(expected) or 'full_memory_bytes=2097152' not in log:
                    raise RuntimeError('hardware/native acceptance missing: ' + name)
                stats = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', log.splitlines()[0])}
                if stats['native_reads'] != oracle['bytecode_read64'] or stats['native_stores'] != oracle['bytecode_store64']:
                    raise RuntimeError('hardware/native memory count differs')
                results[str(stall)] = stats
                if kernel or integrated:
                    if log.splitlines()[0] != (out / f'rtl-{serial}-{stall}.log').read_text().splitlines()[0]:
                        raise RuntimeError('mapped hardware response/cycles differ from RTL')
            name = label + '-errors'
            run('compile-' + name, ['iverilog', '-g2012', '-Wall', *flags, '-Irtl/execute', '-s', 'tb_integer_errors',
                f'-Ptb_integer_errors.SERIAL_IADD={serial}', '-o', str(out / (name + '.vvp')), *sources, 'rtl/execute/tests/tb_integer_errors.v'])
            run(name, ['vvp', str(out / (name + '.vvp')), '+unsupported=' + str(out / 'unsupported.mem')])
            log = (out / (name + '.log')).read_text()
            expected = (f'PASS integer_errors serial_iadd={serial} unsupported_raw_opcodes=158 held_errors=160 prefix_store=1 '
                'no_unsupported_commits=1 error_abort_restart=160 reset_held_fetch=1 reset_pending_load=1 reset_held_store=1 '
                'stale_program_reply_drop=1 stale_memory_reply_drop=2 committed_prefix_preserved=1')
            if log.splitlines()[0] != expected:
                raise RuntimeError('unsupported/reset acceptance missing')
            results['errors'] = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', log.splitlines()[0])}
            if kernel or integrated:
                if log.splitlines()[0] != (out / f'rtl-{serial}-errors.log').read_text().splitlines()[0]:
                    raise RuntimeError('mapped unsupported/reset differs from RTL')
            return results

        for serial in (0, 1):
            summary['rtl'][str(serial)] = tests(serial, f'rtl-{serial}')
            summary['rtl'][str(serial)]['transport'] = transport(serial, f'rtl-{serial}-transport')
        bad = ['iverilog', '-g2012', '-Irtl/execute', '-s', 'randomx_integer_execute',
               '-Prandomx_integer_execute.SERIAL_IADD=2', '-o', str(out / 'invalid.vvp'), KERNEL]
        proc = subprocess.run(bad, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / 'invalid-parameter.log').write_text(proc.stdout)
        commands.append({'label': 'invalid-parameter', 'argv': bad, 'returncode': proc.returncode, 'expected_failure': True})
        if proc.returncode == 0 or 'integer_execute_requires_SERIAL_IADD_0_or_1' not in proc.stdout:
            raise RuntimeError('invalid integer parameter accepted')
        summary['invalid_parameter_rejected'] = True

        def synth(label, top, sources, serial):
            netlist = out / ('netlist-' + label + '.v')
            command = (f'read_verilog -Irtl/execute {" ".join(sources)}; chparam -set SERIAL_IADD {serial} {top}; '
                f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
                f'write_verilog -noattr {netlist}; write_json {out}/netlist-{label}.json')
            run('synth-' + label, ['yosys', '-p', command])
            module = json.loads((out / ('netlist-' + label + '.json')).read_text())['modules'][top]
            types = Counter(cell['type'] for cell in module['cells'].values())
            stats = {'num_cells': len(module['cells']), 'flop_cells': sum(value for key, value in types.items() if 'DFF' in key),
                     'num_cells_by_type': dict(sorted(types.items())),
                     'scope': 'actual generic flattened synthesis; external memories excluded; no calibrated timing/physical PPA'}
            return netlist, stats

        if args.synthesize:
            for serial in (0, 1):
                netlist, stats = synth(f'kernel-{serial}', 'randomx_integer_execute', [KERNEL], serial)
                summary['kernel_synthesis'][str(serial)] = stats
                summary['mapped_kernels_with_RTL_controller'][str(serial)] = tests(serial, f'mapped-kernel-{serial}', kernel=netlist)
                summary['mapped_kernels_with_RTL_controller'][str(serial)]['transport'] = transport(serial, f'mapped-kernel-{serial}-transport', netlist)
            netlist, stats = synth('integrated-0', 'randomx_integer_iteration', RTL, 0)
            summary['integrated_default_synthesis'] = stats
            summary['mapped_integrated_default'] = tests(0, 'mapped-integrated-0', integrated=netlist)
        fast, shared = summary['rtl']['0'], summary['rtl']['1']
        differences = {}
        for stall in ('0', '1'):
            whole = shared[stall]['elapsed_cycles'] - fast[stall]['elapsed_cycles']
            execute = shared[stall]['fetch_to_last_commit_cycles'] - fast[stall]['fetch_to_last_commit_cycles']
            if whole != coverage['counts']['IADD_RS'] or execute != whole:
                raise RuntimeError('IADD schedule cycle accounting differs')
            differences[stall] = {'shared_extra_integrated_cycles': whole, 'shared_extra_execute_interval_cycles': execute}
        summary['comparison'] = {'schedule_delta': differences,
            'meaning': 'one added cycle per IADD_RS in these actual executed programs; port/fixture cycles, not full RandomX hash throughput',
            'shared_schedule_scope': 'only IADD_RS shares the two additions across clocks; no whole-ALU resource-sharing claim'}
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
