#!/usr/bin/env python3
"""Fixed native RegisterFile BLAKE2b, hardware interprogram seeds and bounded gates.

Runs serially inside the caller's admitted payload. The caller owns the global
compute slot and fresh actual-cgroup admission; this driver never acquires a
second slot. All generated files and evidence go to a fresh external directory.
Native initialization, AES program generation, addressed fixture dataset, and
final scratchpad/final RegisterFile hashing remain external. No full VM hash or
physical PPA is claimed. Digest32 uses its own BLAKE2 parameter block.
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
from program_sequence_fixture import prepare as program_fixture
from regfile_hash_fixture import prepare as hash_fixture
from combined_source_bindings import validate_context

ROOT = Path(__file__).resolve().parents[1]
BASE = '990f36830c5a9854bf8e2cf1fe7fd7d4ccf7f192'
ACCEPTED = 'docs/validation/program-sequence-20261013/server-current/inputs.json'
ACCEPTED_SHA = '3ef49b7f6ffbce270676aa5f45cecd344008a08009e19cf6184cecc04e29822b'
VENDOR_SHA = '2763c092b465bb99d71d544915b9fd847064ec195cc438c6370c34ecdf9b746d'
IP_MANIFEST_SHA = '7e09b930df6133ccd5453fdd09eead183212cf2978865a104e96e938d6cc508e'
HASH = 'rtl/hash/'
TEST = HASH + 'tests/'
FULL_REGISTERS_SHA = 'b7ec8f825f289807c8d70a809dcb9b5b1dce598fe219efa20d72f35f34898798'
FULL_REGISTER_PROVENANCE_SHA = 'c2d3f4d5173375cc13f867ddc03319c1babe8b2d2f50c8174ff60574a4c7756a'
IP = HASH + 'vendor/blake2/'
CORE = HASH + 'randomx_blake2b_chain_core.v'
UNIT = HASH + 'randomx_regfile_blake2b.v'
SEED = HASH + 'randomx_program_seed.v'
TOP = HASH + 'randomx_program_hash_sequence.v'
CONTROL = 'rtl/execute/randomx_program_control.v'
SEQUENCE = 'rtl/execute/randomx_program_sequence.v'
NATIVE_TEST = 'rtl/execute/tests/'
NATIVE = [*LIBS, 'vendor/randomx/src/aes_hash.cpp', 'vendor/randomx/src/blake2/blake2b.c']
# These are comparisons to independently accepted native short profiles, not
# new timing measurements or a promised full8x2048 throughput result.
PARENT_CLOCKS = {(1, 0): 110934, (1, 1): 185396, (0, 0): 70110, (0, 1): 120864}
HASH_CLOCKS = {(1, 0): 111348, (1, 1): 185810, (0, 0): 70524, (0, 1): 121278}
BOUNDARY = ('Hardware hashes 256-byte native R/F/E/A after program indices0..6; '
            'index7 bypasses. Actual hardware seeds alone drive next AES programs. '
            'Native scratchpad initialization, AES program generation, addressed '
            'fixture dataset and final scratchpad/final RegisterFile hashes remain '
            'external. Default backend8x2048 is unchanged; connected coverage8x4. '
            'Mapping covers only new digest32/64 units and program_seed bridge; '
            'accepted execution RTL remains behavioral in connected gate tests.')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
            parser.error('tool missing: ' + tool)
    if not shutil.which('iverilog-vpi'):
        parser.error('installed Icarus VPI compiler driver missing')
    out.mkdir()
    commands, pass_records = [], {}
    summary = {'accepted_parent': BASE, 'synthesis_requested': args.synthesize,
               'boundary': BOUNDARY, 'rtl': {}, 'mapping': {}, 'mapped': {}, 'negative': {},
               'programs': 8, 'connected_iterations_per_program': 4,
               'accepted_backend_default_iterations_per_program': 2048}
    compat = None
    cell_model = None
    includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE', '-I' + IP]

    def save(name, value):
        (out / name).write_text(json.dumps(value, indent=2) + '\n')

    def run(label, argv, timeout=2400, expected_failure=None):
        if argv[0] == 'iverilog' and compat is not None:
            argv = [str(compat) if item == V + 'divSqrtRecFN_small.v' else item for item in argv]
        if argv[0] == 'iverilog' and any(flag in argv for flag in
                ('-DREGFILE_BLAKE2B_NETLIST', '-DPROGRAM_SEED_NETLIST')):
            assert cell_model is not None, 'installed Yosys simulation cell model unavailable'
            argv = [*argv, str(cell_model)]
        row = {'label': label, 'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout}
        if expected_failure:
            row['expected_failure_marker'] = expected_failure
        commands.append(row)
        print('START ' + label, flush=True)
        began = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as stream:
                result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                        timeout=timeout)
            row['returncode'] = result.returncode
            if expected_failure:
                log = (out / (label + '.log')).read_text()
                assert result.returncode != 0 and expected_failure in log, (label, result.returncode, log)
                assert 'PASS ' not in log, label
                row['expected_failure_observed'] = True
            else:
                result.check_returncode()
        except Exception as exc:
            row['error'] = str(exc)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic() - began
            save('commands.json', commands)
        print(('EXPECTED FAILURE ' if expected_failure else 'PASS ') + label, flush=True)

    def check(label, prefix, reference=None):
        # Explicit executed labels prevent empty oracle stdout from entering the
        # PASS summary. Compiler diagnostics can precede the single test PASS.
        lines = (out / (label + '.log')).read_text().splitlines()
        records = [line for line in lines if line.startswith('PASS ')]
        assert len(records) == 1 and records[0].startswith(prefix), (label, lines)
        line = records[0]
        assert not any('FATAL:' in item or item.startswith('FAIL ') for item in lines), label
        if reference:
            assert line == pass_records[reference], (label, line, pass_records[reference])
        pass_records[label] = line
        return {'record': line, **{key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', line)}}

    def sources(seed_net=None, unit_net=None):
        flags = ['-DPROGRAM_SEED_NETLIST'] if seed_net else ['-DREGFILE_BLAKE2B_NETLIST'] if unit_net else []
        stage = [str(seed_net)] if seed_net else [str(unit_net), SEED] if unit_net else [CORE, UNIT, SEED]
        return flags, [*RTL, CONTROL, SEQUENCE, *stage, TOP]

    def unit(label, digest, net=None, reference=None):
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-I' + IP,
            *(['-DREGFILE_BLAKE2B_NETLIST'] if net else []), '-s', 'tb_regfile_hash',
            '-Ptb_regfile_hash.DIGEST_BYTES=' + str(digest), '-o', str(out / (label + '.vvp')),
            *([str(net)] if net else [CORE, UNIT]), TEST + 'tb_regfile_hash.v'])
        run(label, ['vvp', str(out / (label + '.vvp')), '+vectors=' + str(out / f'hash{digest}.hex')])
        record = check(label, f'PASS regfile_hash digest_bytes={digest} native_vectors=524 ', reference)
        assert record['latency_min'] == record['latency_max'] == 56 and record['resets'] == 3
        assert record['invalid_lengths'] == 6 and record['native_vector_compute_cycles'] == 524 * 56
        return record

    def seed(label, net=None, unit_net=None, reference=None):
        flags = ['-DPROGRAM_SEED_NETLIST'] if net else ['-DREGFILE_BLAKE2B_NETLIST'] if unit_net else []
        stage = [str(net)] if net else [str(unit_net), SEED] if unit_net else [CORE, UNIT, SEED]
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-I' + IP, *flags,
            '-s', 'tb_program_seed', '-o', str(out / (label + '.vvp')), *stage, TEST + 'tb_program_seed.v'])
        run(label, ['vvp', str(out / (label + '.vvp')), '+vectors=' + str(out / 'hash64.hex')])
        record = check(label, 'PASS program_seed native_records=524 ', reference)
        assert record['hashes'] == 459 and record['final_bypasses'] == 65
        assert record['resets'] == 4 and record['invalid_iterations'] == 3
        return record

    def connected(label, directory, v2, stall, seed_net=None, reference=None, cancel_mode=None):
        flags, rtl = sources(seed_net)
        tb = 'tb_program_hash_cancel' if cancel_mode is not None else 'tb_program_hash_sequence'
        parameters = [f'-P{tb}.V2={v2}', f'-P{tb}.STALL={stall}']
        if cancel_mode is not None:
            parameters.append(f'-P{tb}.CANCEL_MODE={cancel_mode}')
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes, '-I' + str(directory),
            *flags, '-s', tb, *parameters, '-o', str(out / (label + '.vvp')), *rtl, TEST + tb + '.v'])
        run(label, ['vvp', '-M' + str(out), '-mprogram_source', str(out / (label + '.vvp')),
                    '+directory=' + str(directory)])
        prefix = 'PASS program_hash_cancel ' if cancel_mode is not None else 'PASS program_hash_sequence '
        record = check(label, prefix, reference)
        if cancel_mode is None:
            assert record['hardware_seed_hashes'] == 7 and record['programs'] == 8
            assert record['total_iterations'] == 32 and record['iterations_per_program'] == 4
            assert record['elapsed_cycles'] == HASH_CLOCKS[v2, stall]
            assert record['elapsed_cycles'] - PARENT_CLOCKS[v2, stall] == 414
        else:
            assert record['mode'] == cancel_mode and record['all_memory_bytes_preserved'] == 2097152
            assert record['cancelled_generation_wait'] == 140 and record['version_restart'] == 1
            assert record['native_iterations'] == (4 if cancel_mode <= 3 else 32)
        return record

    def backend_cancel(label, seed_net=None, reference=None):
        flags, rtl = sources(seed_net)
        run('compile-' + label, ['iverilog', '-g2012', '-Wall', *includes, *flags,
            '-s', 'tb_program_cancel', '-o', str(out / (label + '.vvp')), *rtl,
            str(out / 'tb_program_cancel-wrapper-view.v')])
        run(label, ['vvp', str(out / (label + '.vvp'))])
        return check(label, 'PASS program_cancel metadata_stale=1 ', reference)

    def synth(label, top, rtl, digest=None):
        net = out / ('netlist-' + label + '.v')
        script = 'read_verilog -I' + IP + ' ' + ' '.join(rtl) + '; '
        if digest is not None:
            script += f'chparam -set DIGEST_BYTES {digest} {top}; '
        script += f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; '
        script += f'write_verilog -noattr {net}; write_json {out}/netlist-{label}.json'
        run('synth-' + label, ['yosys', '-p', script], timeout=5400)
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
                     'digest_bytes': digest if digest is not None else 64,
                     'scope': 'actual new-stage generic mapping only; no execution-core regeneration, physical timing/power/memory area'}

    try:
        accepted_manifest = ROOT / ACCEPTED
        assert sha(accepted_manifest) == ACCEPTED_SHA, 'accepted 69-source manifest identity'
        accepted = json.loads(accepted_manifest.read_text())
        assert len(accepted) == 69
        preserved = validate_context(ROOT, 'regfile')
        assert sha(ROOT / 'vendor/randomx.sha256.json') == VENDOR_SHA
        assert len(json.loads((ROOT / 'vendor/randomx.sha256.json').read_text())) == 171
        run('vendor', ['python3', 'scripts/verify_vendor.py'])
        ip_manifest = ROOT / IP / 'manifest.json'
        assert sha(ip_manifest) == IP_MANIFEST_SHA
        ip = json.loads(ip_manifest.read_text())
        assert ip['commit'] == '36f00fd6351f82cb476fd82af8d615f28aaf677d' and len(ip['original_files']) == 5
        for path, digest in ip['original_files'].items():
            assert sha(ROOT / IP / path) == digest, 'original BLAKE2 IP changed: ' + path
        assert {p.name for p in (ROOT / IP).iterdir() if p.is_file()} == set(ip['original_files']) | {'manifest.json'}
        full_registers = ROOT / TEST / 'accepted-full-registers.hex'
        full_provenance = ROOT / TEST / 'accepted-full-registers.json'
        assert sha(full_provenance) == FULL_REGISTER_PROVENANCE_SHA, 'full-frame provenance identity'
        full_record = json.loads(full_provenance.read_text())
        assert full_record['accepted_head'] == BASE
        assert full_record['SHA256'] == FULL_REGISTERS_SHA == sha(full_registers)
        assert full_record['review'] == 'https://github.com/jliu67/OpenRX/pull/63#pullrequestreview-5505712453'
        full_rows = [row.split() for row in full_registers.read_text().splitlines()]
        assert len(full_rows) == 8 and all(len(row) == 3 and int(row[0]) == index and
            len(row[1]) == 512 and 0 <= int(row[2]) <= 3 for index, row in enumerate(full_rows))
        bound = set(accepted) | {ACCEPTED, 'vendor/randomx.sha256.json', IP + 'manifest.json',
            CORE, UNIT, SEED, TOP, HASH + 'blake2b_micro_oracle.cpp', HASH + 'tb_blake2b_micro.v',
            TEST + 'regfile_hash_oracle.cpp', TEST + 'tb_regfile_hash.v', TEST + 'tb_program_seed.v',
            TEST + 'tb_program_hash_sequence.v', TEST + 'tb_program_hash_cancel.v',
            TEST + 'accepted-full-registers.hex', TEST + 'accepted-full-registers.json',
            'scripts/test_regfile_blake2b.py', 'scripts/regfile_hash_fixture.py',
            'scripts/hardfloat_compile_view.py', 'scripts/program_sequence_fixture.py'}
        bound |= {IP + path for path in ip['original_files']}
        bound |= {'vendor/randomx/' + path for path in json.loads((ROOT / 'vendor/randomx.sha256.json').read_text())}
        bound.update(preserved['input_bindings'])
        input_hashes = {path: sha(ROOT / path) for path in sorted(bound)}
        save('inputs.json', input_hashes)
        save('preserved-inputs.json', {'accepted_parent': BASE, 'accepted_source_bindings': 69,
            'accepted_manifest_sha256': ACCEPTED_SHA, 'RandomX_original_files': 171,
            'RandomX_manifest_sha256': VENDOR_SHA, 'BLAKE2_original_files': 5,
            'BLAKE2_manifest_sha256': IP_MANIFEST_SHA,
            'all_original_IP_and_native_bytes_unchanged': True, **preserved})
        save('accepted-full-register-vector-source.json', {**full_record,
            'provenance_json_sha256': FULL_REGISTER_PROVENANCE_SHA, 'vector_records': 8,
            'use': 'assertion-only native unit corpus; generated short fixtures remain separate connected references'})
        tool_versions = {}
        for tool, flag in required:
            resolved = Path(shutil.which(tool)).resolve()
            tool_versions[tool] = {'path': str(resolved), 'sha256': sha(resolved),
                'version_argv': [tool, flag],
                'version': subprocess.check_output([tool, flag], stderr=subprocess.STDOUT, text=True)}
        tool_versions['iverilog-vpi'] = {'path': str(Path(shutil.which('iverilog-vpi')).resolve()),
            'sha256': sha(Path(shutil.which('iverilog-vpi')).resolve()),
            'cflags_argv': ['iverilog-vpi', '--cflags'],
            'cflags': subprocess.check_output(['iverilog-vpi', '--cflags'], text=True)}
        if args.synthesize:
            yosys_binary = Path(tool_versions['yosys']['path'])
            candidates = [yosys_binary.parent.parent / 'share/yosys/simcells.v',
                          yosys_binary.parent / 'share/yosys/simcells.v',
                          Path('/usr/share/yosys/simcells.v')]
            discovery = {'resolved_yosys_binary': str(yosys_binary),
                         'candidate_paths': list(dict.fromkeys(str(path) for path in candidates))}
            model_source = next((path for path in candidates if path.is_file()), None)
            if model_source is None and shutil.which('yosys-config'):
                argv = ['yosys-config', '--datdir']
                result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                discovery['yosys_config'] = {'argv': argv, 'returncode': result.returncode, 'output': result.stdout}
                if result.returncode == 0:
                    candidate = Path(result.stdout.strip()) / 'simcells.v'
                    if candidate.is_file():
                        model_source = candidate
            assert model_source is not None, 'actual installed Yosys simcells.v missing; mapped checks cannot run'
            raw_model = model_source.read_bytes()
            assert b'module \\$_DLATCH_P_' in raw_model, 'installed simulation model lacks positive-enable latch'
            assert raw_model.startswith(b'/*') and b'*/' in raw_model, 'installed cell model license notice missing'
            license_notice = raw_model[:raw_model.index(b'*/') + 2] + b'\n'
            assert b'Permission' in license_notice or b'permission' in license_notice, 'cell model license notice unavailable'
            cell_model = out / 'yosys-simcells.v'
            cell_model.write_bytes(raw_model)
            (out / 'LICENSE-Yosys-simcells').write_bytes(license_notice)
            assert cell_model.read_bytes() == raw_model, 'installed cell model copy changed'
            model_record = {**discovery, 'installed_source_path': str(model_source.resolve()),
                'installed_source_sha256': sha(model_source), 'copied_file': cell_model.name,
                'copied_sha256': sha(cell_model), 'bytes': len(raw_model),
                'license_file': 'LICENSE-Yosys-simcells', 'license_sha256': sha(out / 'LICENSE-Yosys-simcells'),
                'all_model_bytes_and_original_notice_unchanged': True,
                'scope': 'installed Yosys simulation cells in mapped Icarus invocations only; no hardware transformation'}
            save('yosys-cell-model.json', model_record)
            tool_versions['yosys']['simulation_cell_model'] = model_record
        save('tools.json', tool_versions)
        for path, name in [('rtl/execute/LICENSE', 'LICENSE-OpenRX'), ('vendor/randomx/LICENSE', 'LICENSE-RandomX'),
                ('rtl/aes/vendor/secworks/LICENSE', 'LICENSE-secworks'), (V + 'LICENSE', 'LICENSE-HardFloat'),
                (IP + 'LICENSE', 'LICENSE-BLAKE2-original')]:
            shutil.copyfile(ROOT / path, out / name)
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
        save('program-extraction.json', {'policy': 'original accepted helper extraction; verbatim pinned bodies with upstream notices',
            'source_sha256': sha(ROOT / 'vendor/randomx/src/virtual_machine.cpp'),
            'generated_sha256': {name: sha(out / name) for name in bodies}})
        original_cancel = ROOT / NATIVE_TEST / 'tb_program_cancel.v'
        original = original_cancel.read_text()
        assert original.count(' randomx_program_sequence ') == 2 and original.count('dut.iteration.execute.state_q') == 1
        view = original.replace(' randomx_program_sequence ', ' randomx_program_hash_sequence ')
        view = view.replace('dut.iteration.execute.state_q', 'dut.iteration_chain.iteration.execute.state_q')
        (out / 'tb_program_cancel-wrapper-view.v').write_text(view)
        save('backend-cancel-view.json', {'source': str(original_cancel.relative_to(ROOT)), 'source_sha256': sha(original_cancel),
            'generated_sha256': sha(out / 'tb_program_cancel-wrapper-view.v'),
            'transform': 'two DUT type names and one hierarchy observer path only; original cancellation/error scenarios unchanged',
            'protected_source_unchanged': original_cancel.read_text() == original})
        run('compile-program-oracle', ['g++', '-std=c++11', '-O2', '-I' + str(out), '-Ivendor/randomx/src',
            '-Irtl/execute/tests', NATIVE_TEST + 'program_sequence_oracle.cpp', *NATIVE, '-o', str(out / 'oracle')])
        cflags = tool_versions['iverilog-vpi']['cflags'].split()
        vpi_include = [flag for flag in cflags if flag.startswith('-I')]
        assert vpi_include, 'Icarus VPI include directory unavailable'
        run('compile-program-vpi', ['g++', '-std=c++11', '-O2', '-fPIC', '-shared', *vpi_include,
            '-Ivendor/randomx/src', '-Irtl/execute/tests', NATIVE_TEST + 'program_source_vpi.cpp',
            'vendor/randomx/src/aes_hash.cpp', 'vendor/randomx/src/soft_aes.cpp',
            'vendor/randomx/src/blake2/blake2b.c', '-o', str(out / 'program_source.vpi')])
        run('compile-hash-oracle', ['g++', '-std=c++11', '-O2', '-Ivendor/randomx/src',
            TEST + 'regfile_hash_oracle.cpp', 'vendor/randomx/src/blake2/blake2b.c', '-o', str(out / 'hash-oracle')])
        run('compile-micro-oracle', ['g++', '-std=c++11', '-O2', '-Ivendor/randomx/src',
            HASH + 'blake2b_micro_oracle.cpp', 'vendor/randomx/src/blake2/blake2b.c', '-o', str(out / 'micro-oracle')])
        run('micro-oracle', [str(out / 'micro-oracle'), str(out / 'micro-vectors.hex')])
        for digest in (64, 32):
            for original in (1, 0):
                label = f'micro-{original}-{digest}'
                run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-I' + IP, '-s', 'tb_blake2b_micro',
                    f'-Ptb_blake2b_micro.ORIGINAL={original}', f'-Ptb_blake2b_micro.DIGEST_BYTES={digest}',
                    '-o', str(out / (label + '.vvp')),
                    IP + 'blake2_core.v' if original else CORE, HASH + 'tb_blake2b_micro.v'])
                run(label, ['vvp', str(out / (label + '.vvp')), '+vectors=' + str(out / 'micro-vectors.hex')],
                    expected_failure='native two-block mismatch original=1' if original else None)
                if original:
                    summary['negative'][label] = {'expected_failure_observed': True, 'log_sha256': sha(out / (label + '.log'))}
                else:
                    summary['rtl'][label] = check(label, f'PASS blake2b_micro original=0 digest_bytes={digest} ')
        fixtures = {}
        for version in (1, 0):
            directory = out / ('v2' if version else 'v1')
            directory.mkdir()
            run('oracle-' + str(version), [str(out / 'oracle'), str(directory), '8', '4', str(version)])
            native_summary = program_fixture(directory)
            assert native_summary['programs'] == 8 and native_summary['total_iterations'] == 32
            fixtures[version] = directory
        corpus = hash_fixture(out, full_registers)
        assert corpus == 524
        run('hash-oracle', [str(out / 'hash-oracle'), str(out / 'register-inputs.hex'),
            str(out / 'hash64.hex'), str(out / 'hash32.hex')])
        native64 = [row.split() for row in (out / 'hash64.hex').read_text().splitlines()]
        native32 = [row.split() for row in (out / 'hash32.hex').read_text().splitlines()]
        assert len(native64) == len(native32) == 524
        for row64, row32 in zip(native64, native32):
            assert row64[0] == row32[0]
            message = bytes.fromhex(row64[0])[::-1]
            d64, d32 = bytes.fromhex(row64[1])[::-1], bytes.fromhex(row32[1])[::-1]
            assert d64 == hashlib.blake2b(message, digest_size=64).digest()
            assert d32[:32] == hashlib.blake2b(message, digest_size=32).digest() and d32[32:] == bytes(32)
            assert d32[:32] != d64[:32], 'digest32 incorrectly truncated digest64'
        save('independent-vector-crosscheck.json', {'native_pinned_C_vectors_per_digest': 524,
            'secondary_oracle': 'Python hashlib.blake2b independent API', 'digest32_differs_from_truncated64_all_vectors': True,
            'hash64_sha256': sha(out / 'hash64.hex'), 'hash32_sha256': sha(out / 'hash32.hex')})
        for digest in (64, 32):
            label = f'rtl-hash-{digest}'
            summary['rtl'][label] = unit(label, digest)
        summary['rtl']['rtl-seed'] = seed('rtl-seed')
        summary['rtl']['rtl-backend-cancel'] = backend_cancel('rtl-backend-cancel')
        cancel_cases = [(v2, mode) for v2 in (1, 0) for mode in (1, 2, 3)] + [(1, 4), (1, 5)]
        for version in (1, 0):
            for stall in (0, 1):
                label = f'rtl-connected-{version}-{stall}'
                summary['rtl'][label] = connected(label, fixtures[version], version, stall)
        for version, mode in cancel_cases:
            label = f'rtl-cancel-{version}-{mode}'
            summary['rtl'][label] = connected(label, fixtures[version], version, 1, cancel_mode=mode)
        if args.synthesize:
            unit_nets = {}
            for digest in (64, 32):
                net, counts = synth(f'hash-{digest}', 'randomx_regfile_blake2b', [CORE, UNIT], digest)
                unit_nets[digest] = net
                summary['mapping'][f'hash-{digest}'] = counts
                label = f'mapped-hash-{digest}'
                summary['mapped'][label] = unit(label, digest, net, f'rtl-hash-{digest}')
            summary['mapped']['mapped-hash-seed'] = seed('mapped-hash-seed', unit_net=unit_nets[64], reference='rtl-seed')
            net, counts = synth('seed', 'randomx_program_seed', [CORE, UNIT, SEED])
            summary['mapping']['seed'] = counts
            summary['mapped']['mapped-seed'] = seed('mapped-seed', net, reference='rtl-seed')
            summary['mapped']['mapped-backend-cancel'] = backend_cancel('mapped-backend-cancel', net, 'rtl-backend-cancel')
            for version in (1, 0):
                for stall in (0, 1):
                    label = f'mapped-connected-{version}-{stall}'
                    summary['mapped'][label] = connected(label, fixtures[version], version, stall, net,
                        f'rtl-connected-{version}-{stall}')
            for version, mode in cancel_cases:
                label = f'mapped-cancel-{version}-{mode}'
                summary['mapped'][label] = connected(label, fixtures[version], version, 1, net,
                    f'rtl-cancel-{version}-{mode}', mode)
        # Fail closed if any source changed while the admitted serial run used it.
        assert all(sha(ROOT / path) == digest for path, digest in input_hashes.items()), 'bound source changed during run'
        if cell_model is not None:
            assert sha(cell_model) == model_record['copied_sha256'], 'simulation cell model changed during run'
            assert sha(model_source) == model_record['installed_source_sha256'], 'installed cell model changed during run'
        summary['exact_PASS_records'] = pass_records
        summary['source_unchanged_after_run'] = True
        summary['new_stage_clock_cost_each_profile'] = 414
        summary['rtl_modes'] = len(summary['rtl'])
        summary['mapped_modes'] = len(summary['mapped'])
        save('summary.json', summary)
        print(json.dumps(summary, indent=2), flush=True)
    except Exception as exc:
        save('failure.json', {'type': type(exc).__name__, 'error': str(exc),
            'completed_PASS_records': pass_records, 'unfinished_modes_not_passed': True})
        raise
    finally:
        save('commands.json', commands)
        save('artifacts.sha256.json', {str(path.relative_to(out)): sha(path)
            for path in sorted(out.rglob('*')) if path.is_file() and path.name != 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
