#!/usr/bin/env python3
"""Pack native reciprocal/reload gold; all expected metadata is assertion-only.

The parent driver owns resource admission, compilation, execution and timing.
extract() reuses the accepted verbatim native-body extractor. prepare() consumes
one completed native oracle output, checks its coverage/bindings, and supplies
raw instruction/memory images plus separate assertion records. It launches no
compiler, simulator or workload.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
PIN = 'aaafe71322df6602c21a5c72937ac284724ae561'
NATIVE = ['vendor/randomx/src/soft_aes.cpp', 'vendor/randomx/src/bytecode_machine.cpp',
          'vendor/randomx/src/instructions_portable.cpp', 'vendor/randomx/src/reciprocal.c']
ORACLE = 'rtl/execute/tests/prepared_reciprocal_oracle.cpp'
HELPER = 'scripts/prepared_reciprocal_fixture.py'
NAMES = ('versions chains ev_start ev_count read0 read1 read2 read3 round_in round_out '
         'sp0 sp1 mx ma em0 em1 offset rin ain loadr loadf loade expr expf expe '
         'dsaddr pfaddr dsdata outr outf oute outmx outma fline rline fmem rmem').split()
ADMISSIONS, REPEATS, CASES, SLOTS = 12, 4, 48, 512
SCHEDULE = [0, 0, 1, 2, 3, 0]
ADDRESSES = [0x1000, 0x1000, 0x1000, 0x4000, 0x4000, 0x1000]
MASK64 = (1 << 64) - 1


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def write_text(path, value):
    with Path(path).open('x') as stream:
        stream.write(value)


def bindings(root):
    root = Path(root).resolve()
    lock = json.loads((root / 'vendor/randomx.lock.json').read_text())
    if lock['commit'] != PIN or lock['strategy'] != 'unmodified vendored source snapshot':
        raise ValueError('unchanged pinned native source required')
    manifest = json.loads((root / 'vendor/randomx.sha256.json').read_text())
    actual = {str(p.relative_to(root / 'vendor/randomx')): sha(p)
              for p in sorted((root / 'vendor/randomx').rglob('*')) if p.is_file()}
    if actual != manifest:
        raise ValueError('complete native vendor manifest mismatch')
    paths = ['vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
             'scripts/test_iteration_engine.py', ORACLE, HELPER]
    return {**{'vendor/randomx/' + path: digest for path, digest in manifest.items()},
            **{path: sha(root / path) for path in paths}}


def compile_command(out, root=None):
    """Proposal only. Calling this function does not execute the compiler."""
    root = Path(root or ROOT).resolve()
    out = Path(out).resolve()
    return ['g++', '-std=c++11', '-O2', '-I' + str(out), '-I' + str(root / 'vendor/randomx/src'),
            str(root / ORACLE), *[str(root / path) for path in NATIVE], '-o', str(out / 'oracle')]


def extract(out, root=None):
    """Reuse accepted extraction, retaining every pinned byte and license notice."""
    root = Path(root or ROOT).resolve()
    out = Path(out).resolve()
    if out == root or root in out.parents or not out.is_dir():
        raise ValueError('existing fresh staging output outside source required')
    before = bindings(root)
    spec = importlib.util.spec_from_file_location('openrx_reciprocal_pinned_extractor', root / 'scripts/test_iteration_engine.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = root
    module.extract(out)
    if bindings(root) != before:
        raise ValueError('native/source bytes changed during extraction')
    write_json(out / 'prepared-reciprocal-provenance.json', {
        'RandomX_commit': PIN, 'source_sha256': before, 'compile_command_proposal': compile_command(out, root),
        'extraction': json.loads((out / 'extraction.json').read_text()),
        'policy': 'unchanged pinned source and verbatim accepted extraction; no generated gold supplies DUT prepared constants',
        'dataset': 'existing deterministic addressed fixture, not the full dataset', 'full_hash': False})


def kinds(root):
    result = []
    for name, count in re.findall(r'^#define RANDOMX_FREQ_(\w+)\s+(\d+)\s*$',
                                (root / 'vendor/randomx/src/configuration.h').read_text(), re.M):
        result += [name] * int(count)
    if len(result) != 256 or result.count('IMUL_RCP') != 8:
        raise ValueError('pinned opcode distribution differs')
    return result


def records(path, columns):
    result = [line.split() for line in Path(path).read_text().splitlines()]
    if not result or any(len(row) != columns for row in result):
        raise ValueError('invalid native record shape: ' + str(path))
    return result


def nop(divisor):
    return divisor == 0 or divisor & (divisor - 1) == 0


def check_metadata(word, row, opcode_kinds):
    valid, is_nop = map(int, row[:2])
    divisor, constant = map(lambda x: int(x, 16), row[2:])
    expected_valid = opcode_kinds[word & 255] == 'IMUL_RCP'
    expected_divisor = word >> 32 if expected_valid else 0
    if valid != expected_valid or divisor != expected_divisor or is_nop != (expected_valid and nop(divisor)):
        raise ValueError('native compiled reciprocal classification differs from raw instruction')
    # Secondary arbitrary-precision check observes the unchanged native constant.
    # Hardware receives only the raw word; its preparation must compute the result.
    expected_constant = (1 << (63 + divisor.bit_length())) // divisor if expected_valid and not is_nop else 0
    if constant != expected_constant or constant > MASK64:
        raise ValueError('native unsigned reciprocal constant mismatch')
    return (valid << 97) | (is_nop << 96) | (divisor << 64) | constant


def pack_programs(program_rows, metadata_rows, opcode_kinds, lengths, count):
    instructions = {(int(c), int(pc)): int(word, 16) for c, pc, word in program_rows}
    if len(instructions) != sum(lengths) or any(not (0 <= c < count and 0 <= pc < lengths[c])
                                               for c, pc in instructions):
        raise ValueError('native instruction inventory differs')
    program, metadata = [0] * (count * SLOTS), [0] * (count * SLOTS)
    seen = set()
    for c, pc, *row in metadata_rows:
        c, pc = int(c), int(pc)
        if (c, pc) in seen or (c, pc) not in instructions:
            raise ValueError('native metadata inventory differs')
        seen.add((c, pc))
        program[c * SLOTS + pc] = instructions[c, pc]
        metadata[c * SLOTS + pc] = check_metadata(instructions[c, pc], row, opcode_kinds)
    if seen != set(instructions):
        raise ValueError('native metadata omitted a lexical instruction')
    return instructions, program, metadata


def write_mem(path, values, width):
    with Path(path).open('x') as stream:
        for value in values:
            if not 0 <= value < 1 << width:
                raise ValueError('packed field exceeds ABI width')
            stream.write(f'{value:0{(width + 3) // 4}x}\n')


def check_memory(path):
    count = 0
    with Path(path).open() as stream:
        for line in stream:
            if not re.fullmatch(r'[0-9a-f]{32}\n', line):
                raise ValueError('full memory image is not lossless128-bit rows')
            count += 1
    if count != 2097152 // 16:
        raise ValueError('full2MiB memory image required')
    return {'sha256': sha(path), 'bytes': Path(path).stat().st_size, 'rows': count, 'raw_memory_bytes': 2097152}


def prepare(out, root=None):
    root = Path(root or ROOT).resolve()
    out = Path(out).resolve()
    if out == root or root in out.parents:
        raise ValueError('fixture output must be outside source')
    before = bindings(root)
    extraction = json.loads((out / 'extraction.json').read_text())
    if extraction['RandomX_commit'] != PIN:
        raise ValueError('native extraction pin mismatch')
    for path, digest in extraction['source_sha256'].items():
        if sha(root / path) != digest:
            raise ValueError('extracted native input changed: ' + path)
    for path, digest in extraction['generated_sha256'].items():
        if sha(out / path) != digest:
            raise ValueError('verbatim generated native body changed: ' + path)
    provenance_path = out / 'prepared-reciprocal-provenance.json'
    if provenance_path.exists():
        if json.loads(provenance_path.read_text())['source_sha256'] != before:
            raise ValueError('bound source changed after extraction')
    else:
        # Parent may call the accepted extractor itself; retain that exact record.
        write_json(provenance_path, {'RandomX_commit': PIN, 'source_sha256': before,
            'extraction': extraction, 'compile_command_proposal': compile_command(out, root),
            'original_extraction_binding': 'accepted test_iteration_engine.extract',
            'full_hash': False, 'dataset': 'existing deterministic addressed fixture, not full dataset'})
    oracle = json.loads((out / 'oracle-summary.json').read_text())
    if (oracle['admissions'], oracle['iterations'], oracle['iterations_per_admission'], oracle['v2'], oracle['v1'],
        oracle['full_memory_snapshots'], oracle['native_program_compilations']) != (12, 48, 4, 24, 24, 12, 12):
        raise ValueError('bounded admission/iteration contract changed')
    opcode_kinds = kinds(root)
    rows = records(out / 'iterations.hex', 38)
    admission_rows = records(out / 'admissions.hex', 9)
    if len(rows) != CASES or len(admission_rows) != ADMISSIONS:
        raise ValueError('native iteration/admission inventory differs')
    admitted = []
    for expected, row in enumerate(admission_rows):
        a, v2, template, first, repeats, static, active, nanos = map(int, row[:8])
        address = int(row[8], 16)
        if (a, v2, template, first, repeats, address) != (expected, int(expected < 6), SCHEDULE[expected % 6], expected * REPEATS, REPEATS, ADDRESSES[expected % 6]):
            raise ValueError('native reload schedule changed')
        admitted.append({'admission': a, 'v2': v2, 'template': 'ABCD'[template], 'first_case': first,
            'iterations': repeats, 'program_address': address, 'static_rcp': static, 'static_active_rcp': active,
            'native_compile_nanoseconds': nanos,
            'native_compile_timing_scope': 'instrumentation only, uncontrolled native wall time; no performance acceptance'})
    lengths = [384 if a['v2'] else 256 for a in admitted]
    instructions, program, plan = pack_programs(records(out / 'programs.hex', 3), records(out / 'reciprocal-plan.hex', 6), opcode_kinds, lengths, ADMISSIONS)
    branch_targets = [511] * (ADMISSIONS * SLOTS)
    seen = set()
    for a, pc, raw, target in records(out / 'compiled-targets.hex', 4):
        a, pc, raw, target = map(int, [a, pc, raw, target])
        if (a, pc) in seen or instructions[a, pc] & 255 != raw:
            raise ValueError('native branch target inventory mismatch')
        seen.add((a, pc))
        if opcode_kinds[raw] == 'CBRANCH':
            if not 0 <= target <= pc:
                raise ValueError('native target+1 outside lexical prefix')
            branch_targets[a * SLOTS + pc] = target
        elif target != -1:
            raise ValueError('native target present for nonbranch')
    if seen != set(instructions):
        raise ValueError('branch target record omitted an instruction')
    for a, admission in enumerate(admitted):
        values = plan[a * SLOTS:(a + 1) * SLOTS]
        if sum(x >> 97 for x in values) != admission['static_rcp'] or sum((x >> 97) and not (x >> 96 & 1) for x in values) != admission['static_active_rcp']:
            raise ValueError('native static preparation counts differ')
        admission['immutable_instruction_bytes_sha256'] = hashlib.sha256(b''.join(instructions[a, pc].to_bytes(8, 'little') for pc in range(lengths[a]))).hexdigest()
    for base in [0, 6]:
        if len({admitted[base + i]['immutable_instruction_bytes_sha256'] for i in [0, 1, 5]}) != 1:
            raise ValueError('same-program reload bytes changed')
        if admitted[base + 1]['immutable_instruction_bytes_sha256'] == admitted[base + 2]['immutable_instruction_bytes_sha256']:
            raise ValueError('same-address replacement does not replace code')

    step_rows = records(out / 'instruction-steps.hex', 8)
    event_rows = records(out / 'accesses.hex', 5)
    if len(step_rows) != oracle['instruction_steps'] or len(step_rows) > 200000 or len(event_rows) != oracle['bytecode_read64'] + oracle['bytecode_store64']:
        raise ValueError('dynamic native inventory mismatch or corpus runaway')
    step_start, step_count, event_count = {}, Counter(), Counter()
    dynamic, active_dynamic, kinds_by_version = Counter(), Counter(), [Counter(), Counter()]
    lexical_retirements, ordered_rcp_steps = Counter(), []
    next_pc = [0] * CASES
    previous_r = [int(row[NAMES.index('loadr') + 1], 16) for row in rows]
    previous_f = [int(row[NAMES.index('loadf') + 1], 16) for row in rows]
    previous_e = [int(row[NAMES.index('loade') + 1], 16) for row in rows]
    previous_round = [int(row[NAMES.index('round_in') + 1]) for row in rows]
    encoded_steps = []
    for index, row in enumerate(step_rows):
        c, pc, raw = map(int, row[:3]);r, f, e = map(lambda x: int(x, 16), row[3:6]);rm, nxt = map(int, row[6:])
        if not 0 <= c < CASES or pc != next_pc[c] or instructions[c // REPEATS, pc] & 255 != raw:
            raise ValueError('native retirement order/raw word mismatch')
        if index and c < int(step_rows[index - 1][0]):
            raise ValueError('native cases interleaved')
        step_start.setdefault(c, index);step_count[c] += 1;lexical_retirements[c, pc] += 1
        word = instructions[c // REPEATS, pc];kind = opcode_kinds[raw];v2 = int(c < 24)
        kinds_by_version[v2][kind] += 1
        if kind == 'CBRANCH':
            if nxt not in [pc + 1, branch_targets[c // REPEATS * SLOTS + pc]]:
                raise ValueError('native branch jump differs from compiled target')
        elif nxt != pc + 1:
            raise ValueError('native fallthrough order differs')
        if kind == 'CFROUND':
            src = word >> 16 & 7;rotation = word >> 32 & 63;source = previous_r[c] >> (64 * src) & MASK64
            rotated = ((source >> rotation) | (source << ((64 - rotation) & 63))) & MASK64
            apply = not v2 or rotated & 60 == 0
            expected_round = rotated & 3 if apply else previous_round[c]
            if rm != expected_round:
                raise ValueError('native CFROUND guard/rounding drift')
        elif rm != previous_round[c]:
            raise ValueError('non-CFROUND changed native rounding')
        if kind == 'IMUL_RCP':
            dynamic[c] += 1;active_dynamic[c] += not nop(word >> 32)
            dst = word >> 8 & 7
            ordered_rcp_steps.append((c, pc, raw, previous_r[c] >> (64 * dst) & MASK64, r >> (64 * dst) & MASK64))
        previous_r[c], previous_round[c], next_pc[c] = r, rm, nxt
        previous_f[c], previous_e[c] = f, e
        encoded_steps.append((pc << 1555) | (nxt << 1546) | (raw << 1538) | (rm << 1536) | (e << 1024) | (f << 512) | r)
    expected_families = set(opcode_kinds)
    for version in [0, 1]:
        if set(kinds_by_version[version]) != expected_families:
            raise ValueError('mixed native template lost an instruction family')
    if sum(dynamic.values()) != oracle['dynamic_rcp'] or sum(active_dynamic.values()) != oracle['dynamic_active_rcp']:
        raise ValueError('native dynamic reciprocal count differs')
    encoded_events = []
    for c, pc, write, address, value in event_rows:
        c, pc, write = int(c), int(pc), int(write);address, value = int(address, 16), int(value, 16)
        if not 0 <= c < CASES or not 0 <= pc < lengths[c // REPEATS] or write not in [0, 1] or address & 7 or not 0 <= address <= 2097152 - 8 or not 0 <= value <= MASK64:
            raise ValueError('native memory event outside fixed contract')
        event_count[c] += 1;encoded_events.append((write << 85) | (address << 64) | value)
    assignments = []
    for c, row in enumerate(rows):
        if int(row[0]) != c or list(map(int, row[1:3])) != [int(c < 24), int(c % REPEATS != 0)]:
            raise ValueError('native iteration version/chaining schedule differs')
        if int(row[NAMES.index('ev_count') + 1]) != event_count[c] or int(row[NAMES.index('ev_start') + 1]) != sum(event_count[k] for k in range(c)):
            raise ValueError('native event span differs')
        if next_pc[c] != lengths[c // REPEATS]:
            raise ValueError('native program did not complete')
        if (previous_r[c], previous_f[c], previous_e[c], previous_round[c]) != (
                int(row[NAMES.index('expr') + 1], 16), int(row[NAMES.index('expf') + 1], 16),
                int(row[NAMES.index('expe') + 1], 16), int(row[NAMES.index('round_out') + 1])):
            raise ValueError('bytecode final/iteration state mismatch')
        if c % REPEATS:
            for incoming, outgoing in [('rin', 'outr'), ('mx', 'outmx'), ('ma', 'outma'), ('round_in', 'round_out')]:
                base = 10 if incoming.startswith('round') else 16
                if int(row[NAMES.index(incoming) + 1], base) != int(rows[c - 1][NAMES.index(outgoing) + 1], base):
                    raise ValueError('native chained iteration state mismatch')
            if int(row[NAMES.index('sp0') + 1], 16) or int(row[NAMES.index('sp1') + 1], 16):
                raise ValueError('native chained cursor did not reset')
        for column, (name, value) in enumerate(zip(NAMES, row[1:])):
            assignments.append(f'{name}[{c}]=' + (value if column < 10 else "'h" + value) + ';')
        admission = admitted[c // REPEATS]
        extras = {'program_index': c // REPEATS, 'admission_end': int(c % REPEATS == REPEATS - 1),
                  'program_addr': "64'h" + format(admission['program_address'], 'x'),
                  'static_rcp_count': admission['static_rcp'], 'static_active_rcp_count': admission['static_active_rcp'],
                  'dynamic_rcp_count': dynamic[c], 'dynamic_active_rcp_count': active_dynamic[c],
                  'step_start': step_start[c], 'step_count': step_count[c]}
        assignments += [f'{name}[{c}]={value};' for name, value in extras.items()]

    observed_nops, observed_encodings, aliases = [set(), set()], [set(), set()], [set(), set()]
    active_divisors = [set(), set()]
    for (a, pc), word in instructions.items():
        if opcode_kinds[word & 255] != 'IMUL_RCP':
            continue
        version = admitted[a]['v2'];divisor = word >> 32;raw = word & 255
        if nop(divisor):
            observed_nops[version].add((raw, divisor))
        else:
            observed_encodings[version].add(raw);active_divisors[version].add(divisor)
            if admitted[a]['template'] in ['C', 'D']:
                aliases[version].add((raw, word >> 8 & 7, word >> 16 & 7))
    rcp_raw = {i for i, kind in enumerate(opcode_kinds) if kind == 'IMUL_RCP'}
    required_nops = {0} | {1 << k for k in range(32)}
    for version in [0, 1]:
        if observed_nops[version] != {(raw, divisor) for raw in rcp_raw for divisor in required_nops}:
            raise ValueError('all33 NOP classes/all8 raw encodings required in both versions')
        if observed_encodings[version] != rcp_raw or aliases[version] != {(raw, dst, src) for raw in rcp_raw for dst in range(8) for src in range(8)}:
            raise ValueError('active encodings/dst-src alias matrix incomplete')
        if not {0x7fffffff, 0x80000001, 0xfffffffe, 0xffffffff} <= active_divisors[version]:
            raise ValueError('unsigned bit31/extreme active divisor coverage missing')
    rcp_records = records(out / 'reciprocal-events.hex', 9)
    if len(rcp_records) != oracle['dynamic_rcp']:
        raise ValueError('dynamic reciprocal observer omitted retirements')
    wraps = 0
    for expected, row in zip(ordered_rcp_steps, rcp_records):
        c, pc, raw, is_nop = map(int, row[:4]);divisor, before_r, constant, after_r, wrapped = map(lambda x: int(x, 16), row[4:])
        metadata = plan[c // REPEATS * SLOTS + pc]
        if (c, pc, raw, before_r, after_r) != expected or is_nop != (metadata >> 96 & 1) or divisor != (metadata >> 64 & 0xffffffff) or constant != (metadata & MASK64):
            raise ValueError('dynamic reciprocal differs from static native plan')
        expected_after = before_r if is_nop else before_r * constant & MASK64
        expected_wrap = int(not is_nop and before_r * constant > MASK64)
        if after_r != expected_after or wrapped != expected_wrap:
            raise ValueError('native low64 multiply/NOP result mismatch')
        wraps += wrapped
    if wraps != oracle['low64_wraps'] or not wraps or not oracle['branch_taken']:
        raise ValueError('required low64 wrap/branch replay not observed')
    # Explicit lexical check around both NOPs in B, separate from dynamic outcome.
    for a, admission in enumerate(admitted):
        if admission['template'] == 'B':
            b = lengths[a] - 16
            if branch_targets[a * SLOTS + b + 5] != b + 2:
                raise ValueError('RCP NOP changed lexical branch last-write target')
            for c in range(a * REPEATS, (a + 1) * REPEATS):
                if any(lexical_retirements[c, pc] != 3 for pc in range(b + 2, b + 6)):
                    raise ValueError('directed two-taken NOP/store branch replay missing')
    _, primitive_program, primitive_metadata = pack_programs(records(out / 'primitive-programs.hex', 3), records(out / 'primitive-metadata.hex', 6), opcode_kinds, [256, 384], 2)
    primitive_counts = []
    for version in range(2):
        values = primitive_metadata[version * SLOTS:(version + 1) * SLOTS]
        valid = sum(value >> 97 for value in values);noops = sum((value >> 97) and (value >> 96 & 1) for value in values)
        if (valid, noops, valid - noops) != (224, 96, 128):
            raise ValueError('primitive preparation coverage/count changed')
        primitive_counts.append({'v2': version, 'static_rcp': valid, 'static_nop_rcp': noops, 'static_active_rcp': valid - noops})

    sizes = {'TOTAL_ITERATIONS': CASES, 'TOTAL_ADMISSIONS': ADMISSIONS, 'ITERATIONS_PER_ADMISSION': REPEATS,
             'TOTAL_PROGRAM_WORDS': ADMISSIONS * SLOTS, 'TOTAL_STEPS': len(step_rows), 'TOTAL_EVENTS': len(event_rows),
             'BYTECODE_READS': oracle['bytecode_read64'], 'BYTECODE_STORES': oracle['bytecode_store64'],
             'TOTAL_DYNAMIC_RCP': oracle['dynamic_rcp'], 'TOTAL_DYNAMIC_ACTIVE_RCP': oracle['dynamic_active_rcp'],
             'TOTAL_DYNAMIC_NOP_RCP': oracle['dynamic_nop_rcp'],
             'TOTAL_STATIC_RCP': sum(a['static_rcp'] for a in admitted),
             'TOTAL_STATIC_ACTIVE_RCP': sum(a['static_active_rcp'] for a in admitted),
             'PRIMITIVE_PROGRAM_WORDS': 1024, 'PRIMITIVE_RCP_PER_VERSION': 224,
             'PRIMITIVE_ACTIVE_RCP_PER_VERSION': 128, 'PRIMITIVE_NOP_RCP_PER_VERSION': 96}
    write_text(out / 'prepared_reciprocal_sizes.vh', 'localparam integer ' + ','.join(f'{name}={value}' for name, value in sizes.items()) + ';\n')
    write_text(out / 'case_vectors.vh', '\n'.join(assignments) + '\n')
    write_text(out / 'prepared_reciprocal_vectors.vh', '// Compatibility alias: assignments only; sizes belong at module scope.\n`include "case_vectors.vh"\n')
    write_mem(out / 'programs.mem', program, 64)
    write_mem(out / 'targets.mem', branch_targets, 9)
    write_mem(out / 'reciprocal_plan.mem', plan, 98)
    write_mem(out / 'steps.mem', encoded_steps, 1564)
    write_mem(out / 'events.mem', encoded_events, 86)
    write_mem(out / 'primitive-programs.mem', primitive_program, 64)
    write_mem(out / 'primitive-metadata.mem', primitive_metadata, 98)
    snapshots = {path.name: check_memory(path) for path in [out / 'initial.hex', *[out / f'final-{a}.hex' for a in range(ADMISSIONS)]]}
    coverage = {'admissions': admitted, 'iterations': CASES, 'iterations_per_admission': REPEATS,
        'same_program_reloads_per_version': 2, 'same_address_different_program_replacements_per_version': 2,
        'versions': {str(v): {'static_nop_encoding_divisor_pairs': len(observed_nops[v]),
            'active_raw_encodings': sorted(observed_encodings[v]), 'active_dst_src_alias_tuples': len(aliases[v]),
            'active_divisors': sorted(active_divisors[v]), 'dynamic_instruction_counts': dict(kinds_by_version[v])} for v in [0, 1]},
        'primitive': primitive_counts, 'sizes': sizes, 'memory_snapshots': snapshots,
        'branch_lexical_NOP_target_checks': 2, 'low64_wraps': wraps,
        'native_source_pin': PIN, 'source_unchanged_after_preparation': bindings(root) == before,
        'assertion_only': ['steps.mem', 'targets.mem', 'reciprocal_plan.mem', 'primitive-metadata.mem', 'case_vectors.vh', 'final-*.hex'],
        'raw_DUT_inputs': ['initial.hex', 'programs.mem', 'primitive-programs.mem', 'admission request/config inputs'],
        'performance_scope': 'paired baseline/prepared RTL and model must include per-admission preparation and use identical immutable program/lookup/event-ordinal stalls; this helper makes no performance acceptance',
        'boundary': 'native full iteration and full2MiB snapshots; addressed fixture dataset; no full dataset or final hash'}
    if not coverage['source_unchanged_after_preparation']:
        raise ValueError('bound native/oracle/fixture source changed during preparation')
    write_json(out / 'admissions.json', admitted)
    write_json(out / 'coverage.json', coverage)
    fixture_files = sorted(path for path in out.iterdir() if path.is_file()
                           and path.name not in ['oracle', 'artifacts.sha256.json', 'commands.json'])
    write_json(out / 'prepared-reciprocal-fixture-inputs.json', {
        'source_sha256': before, 'native_executable_sha256': sha(out / 'oracle') if (out / 'oracle').is_file() else None,
        'fixture_sha256': {path.name: sha(path) for path in fixture_files},
        'native_oracle_outputs_unchanged': True, 'golden_metadata_is_assertion_only': True,
        'mutable_journal': {'path': 'commands.json', 'excluded_from_fixture_sha256': True,
                           'binding': 'final complete artifacts.sha256.json manifest'}})
    return coverage


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--extract-only', action='store_true')
    args = parser.parse_args()
    if args.extract_only:
        extract(args.output, args.root)
    else:
        print(json.dumps(prepare(args.output, args.root), indent=2))
