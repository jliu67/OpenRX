#!/usr/bin/env python3
"""Focused native-cache dataset/lifecycle integration; run under reviewed admission.

The accepted component matrices are reused. Only the new service boundary and
bounded 2-program x 1-iteration connected work are executed. Original sources,
prepared assets and all previous outputs are immutable inputs.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from dataset_lifecycle_support import Supervisor, load, save, sha, verify_assets
from test_divsqrt_execute import RTL as EXECUTE_RTL, V
from test_iteration_engine import extract, function
from test_dataset_item import provenance_library
from hardfloat_compile_view import prepare as compile_view
from program_sequence_fixture import prepare as prepare_assertions

ROOT = Path(__file__).resolve().parents[1]
BASE = '901c6557b3a988902dbbf4c1cdde227a7cf2d31c'
TEST = 'rtl/hash/tests/'
BENCH = TEST + 'tb_dataset_hash_lifecycle.v'
UNIT_BENCH = 'rtl/dataset_service/tests/tb_dataset_service.v'
LOCK = 'rtl/dataset_service/dataset-context.lock.json'
SERVICE_RTL = ['rtl/execute/randomx_mul64.v',
               'rtl/execute/randomx_superscalar_execute.v',
               'rtl/dataset/randomx_dataset_item.v',
               'rtl/dataset_service/randomx_dataset_service.v']
EXTRA = ['rtl/execute/randomx_program_control.v',
         'rtl/execute/randomx_program_reciprocals.v',
         'rtl/execute/randomx_prepared_rcp_guard.v',
         'rtl/execute/randomx_prepared_integer_iteration.v',
         'rtl/execute/randomx_prepared_program_sequence.v']
MESSAGE = b'OpenRX connected prepared dataset lifecycle 20261018'
NORMAL = [('software-dataset-ideal', 0, 0), ('hardware-dataset-ideal', 1, 0),
          ('hardware-dataset-stalled', 1, 1)]


def source_inputs(sources):
    """Bind actual consumed originals, generated-view sources and new adapters."""
    names = set(sources + [BENCH, UNIT_BENCH, LOCK])
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / 'vendor/randomx').rglob('*') if p.is_file())
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / 'scripts').glob('*.py'))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / 'tests').glob('test_dataset_lifecycle_*.py'))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / TEST).glob('*') if p.is_file() and p.suffix in ('.cpp', '.hpp'))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / 'rtl').rglob('*')
                 if p.is_file() and (p.suffix in ('.vh', '.vi') or p.name in ('LICENSE', 'manifest.json', 'UPSTREAM.json')))
    names.update(['vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                  'rtl/execute/tests/program_native_helpers.hpp'])
    return {n: {'bytes': (ROOT / n).stat().st_size, 'sha256': sha(ROOT / n)} for n in sorted(names)}


def validate_outer(ledger, provider, native, hardware):
    assert ledger['hardware_fill_enabled'] and ledger['hardware_program_enabled'] and ledger['hardware_input_hash_enabled']
    assert ledger['cycles'] > 0 and sum(ledger['stage_cycles'].values()) == ledger['cycles']
    assert sum(ledger['nested_iteration_phases']) == ledger['stage_cycles']['execution']
    assert sum(ledger['nested_finalization_phases']) == ledger['stage_cycles']['finalization']
    assert sum(ledger['nested_executor_phases']) == ledger['nested_iteration_phases'][7]
    assert sum(ledger['nested_input_hash_phases']) == ledger['stage_cycles']['input_hash']
    assert sum(ledger['nested_program_generation_phases']) == ledger['stage_cycles']['program_generation']
    assert ledger['nested_initialization']['provider_wait'] == 0
    assert sum(ledger['nested_initialization']['fill_phases']) == ledger['stage_cycles']['initialization_hardware_fill']
    assert ledger['scratchpad_bytes'] == 2097152 and ledger['dataset_logical_bytes'] == 128
    assert ledger['logical_entry_bytes'] == ledger['logical_tail_bytes'] == 256
    assert ledger['program_image_load_bytes'] == 768 * 8
    assert ledger['logical_bytecode_memory_bytes'] == native['bytecode_events'] * 8
    assert ledger['runtime_reciprocals'] == 0
    assert ledger['preparation_reciprocals'] == native['static_active_reciprocals']
    assert provider['cache_key_hex'] == '74657374206b657920303030'
    assert provider['argon_initializations'] == provider['native_cache_program_generations'] == 0
    assert provider['cache_image_export_bytes'] == provider['cache_initialization_host_seconds'] == 0
    assert provider['input_hash_calls'] == provider['software_fill_provider_calls'] == provider['program_generations'] == 0
    assert provider['dataset_requests'] == (0 if hardware else 2)
    assert provider['assertion_only_input_hash_calls'] == 1
    assert provider['assertion_only_program_generations'] == 2
    assert provider['cache_bytes'] == 268435456 and provider['materialized_dataset_bytes'] == 0
    assert provider['logical_dataset_bytes'] == 2181038016
    assert provider['provider_device_cycles'] is None and ledger['untimed_provider_device_cycles'] is None
    for name in ('asset_load_host_seconds', 'dataset_provider_host_seconds',
                 'assertion_only_dataset_host_seconds'):
        assert isinstance(provider[name], (float, int)) and provider[name] >= 0


def validate_dataset(dataset, ledger, rows, native_items, hardware, stalled):
    """Validate measured counters and disjoint clocks, not just PASS strings."""
    assert len(native_items) == 2
    assert dataset['schema'] == 'openrx.dataset-lifecycle.nested-ledger.v1'
    assert dataset['hardware_dataset'] == hardware
    assert dataset['outer_cycles'] == ledger['cycles']
    assert dataset['dataset_costs_are_nested_not_added_to_outer_total'] is True
    assert dataset['all_descriptors_captured'] is True
    assert dataset['full_native_digest_registers_scratchpad'] is True
    assert dataset['physical_cache_service'] is None
    assert dataset['demands'] == dataset['responses'] == 2
    assert dataset['live_native_dataset_calls'] == (0 if hardware else 2)
    counters = ['items', 'item_returns', 'stages', 'retirements', 'item_availability_clocks',
                'executor_clocks', 'ideal_executor_clocks_each', 'program_service_extra_clocks',
                'cache_service_extra_clocks', 'cache_requests', 'cache_responses',
                'instruction_requests', 'instruction_responses', 'stale_packets_drained',
                'cache_request_stalls', 'instruction_request_stalls']
    assert all(type(dataset[k]) is int and dataset[k] >= 0 for k in counters)
    assert len(dataset['service_phase_cycles']) == 3 and len(dataset['item_phase_cycles']) == 9
    assert all(type(v) is int and v >= 0 for k in ('service_phase_cycles', 'item_phase_cycles') for v in dataset[k])
    # Exact accepted cache0 programs: N=3563, M=1254, iterative multiplier.
    ideal = 3 * 3563 + 34 * 1254
    assert dataset['ideal_executor_clocks_each'] == ideal == 53325
    if not hardware:
        assert rows == []
        assert all(dataset[k] == 0 for k in counters if k != 'ideal_executor_clocks_each')
        assert sum(dataset['service_phase_cycles']) == sum(dataset['item_phase_cycles']) == 0
        return
    assert dataset['items'] == dataset['item_returns'] == len(rows) == 2
    assert dataset['stages'] == dataset['cache_requests'] == dataset['cache_responses'] == 16
    assert dataset['retirements'] == dataset['instruction_requests'] == dataset['instruction_responses'] == 2 * 3563
    assert sum(dataset['service_phase_cycles']) == ledger['stage_cycles']['execution']
    assert sum(dataset['item_phase_cycles']) <= sum(dataset['service_phase_cycles'])
    numeric = ['item_cycles', 'executor_cycles', 'stages', 'retired', 'muls',
               'instruction_service_extra', 'cache_service_extra', 'request_to_first_response']
    totals = Counter()
    tags = set()
    for row, expected in zip(rows, native_items):
        tag = int(row['tag'], 16)
        assert tag not in tags and tag >> 16 != 0
        tags.add(tag)
        assert int(row['address'], 16) == int(expected[0], 16)
        assert int(row['image_epoch'], 16) == dataset['captured_asset_epoch']
        values = {k: int(row[k]) for k in numeric}
        assert all(v >= 0 for v in values.values())
        assert values['stages'] == 8 and values['retired'] == 3563 and values['muls'] == 1254
        assert values['executor_cycles'] == ideal + values['instruction_service_extra']
        assert values['item_cycles'] == values['executor_cycles'] + 74 + values['cache_service_extra']
        assert values['request_to_first_response'] == values['item_cycles']
        totals.update(values)
    for field, column in [('item_availability_clocks', 'item_cycles'), ('executor_clocks', 'executor_cycles'),
                          ('stages', 'stages'), ('retirements', 'retired'),
                          ('program_service_extra_clocks', 'instruction_service_extra'),
                          ('cache_service_extra_clocks', 'cache_service_extra')]:
        assert dataset[field] == totals[column]
    assert dataset['executor_clocks'] == 2 * ideal + dataset['program_service_extra_clocks']
    assert dataset['item_availability_clocks'] == dataset['executor_clocks'] + 148 + dataset['cache_service_extra_clocks']
    if stalled:
        assert all(dataset[k] > 0 for k in ['program_service_extra_clocks', 'cache_service_extra_clocks',
                   'stale_packets_drained', 'cache_request_stalls', 'instruction_request_stalls'])
    else:
        assert dataset['item_availability_clocks'] == 106798
        assert all(dataset[k] == 0 for k in ['program_service_extra_clocks', 'cache_service_extra_clocks',
                   'stale_packets_drained', 'cache_request_stalls', 'instruction_request_stalls'])


def compare_ideal_profiles(profiles):
    software = profiles['software-dataset-ideal']['ledger']
    hardware = profiles['hardware-dataset-ideal']['ledger']
    delta = hardware['cycles'] - software['cycles']
    # Ideal software service responds on the next edge. The hardware service
    # adds exactly the measured child availability, without another queue.
    assert delta == profiles['hardware-dataset-ideal']['dataset']['item_availability_clocks'] == 106798
    for stage, clocks in software['stage_cycles'].items():
        assert hardware['stage_cycles'][stage] - clocks == (delta if stage == 'execution' else 0)
    assert hardware['nested_reply_waits']['dataset'] - software['nested_reply_waits']['dataset'] == delta
    for key in ('nested_executor_phases', 'nested_initialization', 'nested_input_hash_phases',
                'nested_program_generation_phases', 'nested_finalization_phases'):
        assert hardware[key] == software[key]
    assert profiles['hardware-dataset-ideal']['actual_digest_sha256'] == profiles['software-dataset-ideal']['actual_digest_sha256']
    return {'outer_cycle_delta': delta, 'execution_cycle_delta': delta, 'dataset_reply_wait_delta': delta,
            'other_stage_clocks_equal': True, 'native_digest_equal': True, 'nested_costs_added_twice': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--asset-root', type=Path, required=True)
    p.add_argument('--asset-receipt', type=Path)
    p.add_argument('--asset-receipt-sha256')
    p.add_argument('--asset-root-verify', type=Path)
    p.add_argument('--native-library', type=Path)
    p.add_argument('--native-build-execution', type=Path)
    p.add_argument('--jobs', type=int, default=6, choices=range(1, 7))
    p.add_argument('--synthesize', action='store_true', help='Map only the new service boundary with accepted child IP; no whole hash mapping')
    args = p.parse_args()
    out = args.out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents or not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        p.error('a fresh unambiguous output outside source is required; retain prior attempts')
    if bool(args.native_library) != bool(args.native_build_execution):
        p.error('both native archive reuse arguments are required together')
    raw = [args.asset_receipt, args.asset_receipt_sha256, args.asset_root_verify]
    if any(raw) and not all(raw):
        p.error('raw asset verification requires receipt, expected SHA and original root verification')
    required = ['python3', 'g++', 'cmake', 'iverilog', 'iverilog-vpi', 'vvp'] + (['yosys'] if args.synthesize else [])
    tools = {n: Path(shutil.which(n)).resolve() for n in required if shutil.which(n)}
    if len(tools) != len(required):
        p.error('required native/simulator tool unavailable')
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip(), 'freeze the source before admitted execution'
    out.mkdir(parents=True)
    supervisor = Supervisor(out)
    run = supervisor.run
    sources = list(dict.fromkeys([*EXECUTE_RTL, *EXTRA, *SERVICE_RTL,
               *[str(x.relative_to(ROOT)) for x in sorted((ROOT / 'rtl/hash').glob('randomx_*.v'))
                 if x.name != 'randomx_program_hash_sequence.v']]))
    hashes = source_inputs(sources)
    save(out / 'inputs.json', hashes)
    summary = {'schema': 'openrx.dataset-lifecycle.integration.v1', 'status': 'running', 'base': BASE,
               'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'source_tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip(),
               'programs': 2, 'iterations': 1, 'full_v2_requested': False, 'jobs': args.jobs,
               'scope': 'New dataset service and unchanged full-memory lifecycle over two native VM programs, one iteration each. The accepted dataset-item/executor validation is reused.',
               'normal_profiles': {}, 'controls': {}, 'service_unit': {}, 'mapping': {},
               'old_component_native_RTL_mapped_regenerated': False, 'physical_or_full_hash_acceptance': False}
    try:
        assets = verify_assets(args.asset_root.resolve(), ROOT / LOCK, ROOT,
                               receipt=args.asset_receipt.resolve() if args.asset_receipt else None,
                               receipt_sha=args.asset_receipt_sha256,
                               verify=args.asset_root_verify.resolve() if args.asset_root_verify else None)
        save(out / 'prepared-assets.json', assets)
        summary['prepared_assets'] = assets
        run('toolchain-identity', ['python3', '-B', 'scripts/check_superscalar_toolchain.py',
             '--output', str(out / 'toolchain-identity.json')])
        run('identity-and-ledger-unit', ['python3', '-B', '-m', 'unittest', 'discover',
             '-s', 'tests', '-p', 'test_dataset_lifecycle_*.py', '-v'])
        for name, flag in [('g++', '--version'), ('iverilog', '-V'), ('vvp', '-V')]:
            r = subprocess.run([str(tools[name]), flag], cwd=ROOT, capture_output=True, text=True)
            summary.setdefault('tools', {})[name] = {'path': str(tools[name]), 'sha256': sha(tools[name]),
                'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}
        for path, name in [('rtl/dataset/LICENSE', 'LICENSE-dataset'), ('rtl/execute/LICENSE', 'LICENSE-OpenRX'),
                           ('vendor/randomx/LICENSE', 'LICENSE-RandomX'), ('rtl/aes/vendor/secworks/LICENSE', 'LICENSE-secworks'),
                           (V + 'LICENSE', 'LICENSE-HardFloat'), ('rtl/hash/vendor/blake2/LICENSE', 'LICENSE-BLAKE2')]:
            shutil.copyfile(ROOT / path, out / name)
        compat = compile_view(ROOT / V / 'divSqrtRecFN_small.v', out)
        sources = [str(compat) if n == V + 'divSqrtRecFN_small.v' else n for n in sources]
        extract(out)
        virtual = (ROOT / 'vendor/randomx/src/virtual_machine.cpp').read_text()
        notice = virtual[:virtual.index('*/') + 2] + '\n'
        bodies = {'pinned_program_initialize.inc': function(virtual, 'void randomx_vm::initialize()', True),
                  'pinned_program_float_helpers.inc': 'namespace randomx {\n' + '\n'.join(function(virtual, n) for n in
                    ['static inline uint64_t getSmallPositiveFloatBits(', 'static inline uint64_t getStaticExponent(',
                     'static inline uint64_t getFloatMask(']) + '\n}\n'}
        for name, body in bodies.items():
            (out / name).write_text(notice + body)
        save(out / 'program-extraction.json', {'source_sha256': sha(ROOT / 'vendor/randomx/src/virtual_machine.cpp'),
             'generated': {name: sha(out / name) for name in bodies}})
        if args.native_library:
            library = args.native_library.resolve()
            summary['native_library'] = provenance_library(library, args.native_build_execution.resolve())
        else:
            library_build = out / 'native-library'
            run('configure-native-library', ['cmake', '-S', 'vendor/randomx', '-B', str(library_build),
                '-DCMAKE_BUILD_TYPE=Release', '-DARCH=default', '-DCMAKE_POSITION_INDEPENDENT_CODE=ON'])
            run('build-native-library', ['cmake', '--build', str(library_build), '--parallel', str(args.jobs)])
            library = library_build / 'librandomx.a'
            summary['native_library'] = {'fresh_pinned_build': True, 'ARCH': 'default', 'sha256': sha(library)}
        native_includes = ['-I' + str(out), '-Ivendor/randomx/src', '-Irtl/execute/tests', '-I' + TEST]
        run('compile-reference', ['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', *native_includes,
             TEST + 'dataset_lifecycle_reference.cpp', str(library), '-pthread', '-ldl', '-o', str(out / 'reference')])
        vpi_includes = [x for x in subprocess.check_output(['iverilog-vpi', '--cflags'], text=True).split() if x.startswith('-I')]
        assert vpi_includes
        run('compile-vpi', ['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-fPIC', '-shared', *vpi_includes,
             *native_includes, TEST + 'dataset_lifecycle_source_vpi.cpp', str(library), '-pthread', '-ldl',
             '-o', str(out / 'dataset_lifecycle_source.vpi')])
        env = dict(os.environ, RX_PREPARED_CACHE_ROOT=str(args.asset_root.resolve()))
        env.pop('RX_PREPARED_REFERENCE_OUTPUT', None)
        gold = out / 'native-reference'; gold.mkdir()
        run('native-reference', [str(out / 'reference'), str(gold), '2', '1', '1', MESSAGE.hex()],
            env=dict(env, RX_PREPARED_REFERENCE_OUTPUT=str(gold)))
        summary['native_reference'] = prepare_assertions(gold)
        native = load(gold / 'oracle-summary.json')
        canonical = load(gold / 'full-reference.json')
        assert canonical['canonical_randomx_calculate_hash_verified'] is False
        item_rows = [x.split() for x in (gold / 'dataset-items.hex').read_text().splitlines()]
        assert len(item_rows) == 2 and all(len(x) == 2 and len(x[0]) == 16 and len(x[1]) == 128 for x in item_rows)
        host = load(gold / 'dataset-native-host-time.json')
        assert host['dataset_requests'] == host['native_dataset_gold_export_rows'] == 2
        assert host['argon_initializations'] == host['native_cache_program_generations'] == 0
        summary['native_dataset_items'] = [{'address_hex': a, 'item_hex': b} for a, b in item_rows]
        summary['native_reference_host_time'] = host
        gold_hashes = {str(x.relative_to(gold)): {'bytes': x.stat().st_size, 'sha256': sha(x)} for x in sorted(gold.rglob('*')) if x.is_file()}
        save(out / 'native-reference-files.json', gold_hashes)
        includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE', '-Irtl/hash/vendor/blake2', '-I' + str(gold)]
        # Legacy defaults remain legal; an unsupported full hardware dataset
        # hash must fail elaboration rather than recycle the accepted namespace.
        guard_top = 'randomx_prepared_dataset_hash_lifecycle'
        run('elaborate-legacy-default', ['iverilog', '-g2012', *includes, '-s', guard_top,
             '-o', str(out / 'legacy-default.vvp'), *sources])
        run('reject-full-hardware-capacity', ['iverilog', '-g2012', *includes, '-s', guard_top,
             '-P' + guard_top + '.HARDWARE_DATASET=1', '-o', str(out / 'invalid-capacity.vvp'), *sources],
             expected_returncodes=(1, 2, 3, 4))
        assert 'dataset_service_requires_ITEMS_PER_BATCH_1_to_8191' in (out / 'reject-full-hardware-capacity.log').read_text()
        summary['elaboration_guards'] = {'legacy_default_8x2048': 'elaborates',
            'hardware_dataset_8x2048': 'rejected_by_explicit_8191_item_capacity_guard'}

        def profile(name, hardware=1, stalled=0, cancellation=0, error=0):
            parameters = {'PROGRAMS': 2, 'ITERATIONS': 1, 'PREPARED_RCP': 1, 'HARDWARE_FILL': 1,
                          'HARDWARE_PROGRAM': 1, 'HARDWARE_INPUT_HASH': 1, 'HARDWARE_DATASET': hardware,
                          'EVENT_TRACE': 1, 'STALL': stalled, 'DATASET_CANCEL': cancellation, 'DATASET_ERROR': error}
            binary = out / (name + '.vvp')
            run('compile-' + name, ['iverilog', '-g2012', '-Wall', *includes, '-s', 'tb_dataset_hash_lifecycle',
                 *['-Ptb_dataset_hash_lifecycle.' + k + '=' + str(v) for k, v in parameters.items()],
                 '-o', str(binary), *sources, BENCH])
            directory = out / name; directory.mkdir()
            run(name, ['vvp', '-M' + str(out), '-mdataset_lifecycle_source', str(binary),
                 '+directory=' + str(gold), '+output=' + str(directory), '+asset_root=' + str(args.asset_root.resolve()),
                 '+input=' + format(int.from_bytes(MESSAGE, 'little'), 'x'), '+input_bytes=' + str(len(MESSAGE))], env=env)
            lines = (out / (name + '.log')).read_text().splitlines()
            assert not any('FATAL:' in x or x.startswith('FAIL ') for x in lines)
            passes = [x for x in lines if x.startswith('PASS ')]
            provider = load(directory / 'provider-host-time.json')
            assert provider['argon_initializations'] == provider['native_cache_program_generations'] == 0
            assert provider['dataset_requests'] == (0 if hardware else 2)
            if cancellation or error:
                required_prefix = 'PASS dataset_lifecycle_cancel ' if cancellation else 'PASS dataset_lifecycle_error '
                assert any(x.startswith(required_prefix) for x in passes)
                return {'parameters': parameters, 'PASS': passes, 'provider': provider, 'scope': 'Cancellation/error prefix and changed-generation/input recovery; not a completed new hash.'}
            assert any(x.startswith('PASS prepared_hash_lifecycle ') for x in passes)
            assert any(x.startswith('PASS dataset_hash_lifecycle ') for x in passes)
            ledger = load(directory / 'ledger.json'); dataset = load(directory / 'dataset-ledger.json')
            validate_outer(ledger, provider, native, hardware)
            with (directory / 'dataset-items-ledger.csv').open(newline='') as f:
                rows = list(csv.DictReader(f))
            validate_dataset(dataset, ledger, rows, item_rows, hardware, stalled)
            digest = (directory / 'actual-final-digest32.hex').read_bytes()
            assert digest == (gold / 'final-digest32.hex').read_bytes()
            return {'parameters': parameters, 'PASS': passes, 'ledger': ledger, 'dataset': dataset,
                    'provider': provider, 'dataset_rows': rows, 'actual_digest_sha256': sha(directory / 'actual-final-digest32.hex')}

        specs = [(n, h, s, 0, 0) for n, h, s in NORMAL]
        specs += [('hardware-cancel-' + str(n), 1, 1, n, 0) for n in (1, 2, 3)]
        specs += [('hardware-error-' + str(n), 1, 1, 0, n) for n in (1, 2)]
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            pending = [(s[0], pool.submit(profile, *s)) for s in specs]
            failures = []
            for name, future in pending:
                try:
                    result = future.result()
                    summary['controls' if result['parameters']['DATASET_CANCEL'] or result['parameters']['DATASET_ERROR'] else 'normal_profiles'][name] = result
                except Exception as e:
                    failures.append({'profile': name, 'error': str(e)})
            if failures:
                summary['profile_failures'] = failures
                raise RuntimeError('Integration profiles failed after all submitted work joined: ' + repr(failures))
        summary['paired_ideal_clock_closure'] = compare_ideal_profiles(summary['normal_profiles'])

        def unit(label, netlist=None, cells=None):
            binary = out / (label + '.vvp')
            selected = [str(netlist), str(cells)] if netlist else SERVICE_RTL
            definitions = ['-DDATASET_SERVICE_NETLIST'] if netlist else []
            run('compile-' + label, ['iverilog', '-g2012', '-Wall', '-s', 'tb_dataset_service',
                 *definitions, '-o', str(binary), *selected, UNIT_BENCH])
            directory = out / label; directory.mkdir()
            run(label, ['vvp', '-M' + str(out), '-mdataset_lifecycle_source', str(binary),
                 '+asset_root=' + str(args.asset_root.resolve()), '+output=' + str(directory), '+MODE=all'], env=env)
            passes = [x for x in (out / (label + '.log')).read_text().splitlines() if x.startswith('PASS ')]
            assert passes and not any('FATAL:' in x or x.startswith('FAIL ') for x in (out / (label + '.log')).read_text().splitlines())
            provider = load(directory / 'provider-host-time.json')
            assert provider['dataset_requests'] == 0 and provider['assertion_only_dataset_requests'] == 5
            assert provider['argon_initializations'] == provider['native_cache_program_generations'] == 0
            assert provider['asset_load_host_seconds'] >= 0 and provider['assertion_only_dataset_host_seconds'] >= 0
            return {'PASS': passes, 'provider': provider}

        summary['service_unit']['RTL'] = unit('dataset-service-RTL')
        if args.synthesize:
            netlist = out / 'netlist-dataset-service.v'
            script = 'read_verilog ' + ' '.join(SERVICE_RTL) + '; '
            script += 'chparam -set ITEMS_PER_BATCH 2 randomx_dataset_service; synth -top randomx_dataset_service -flatten; check -assert; '
            script += f'tee -o {out}/stat-dataset-service.txt stat; write_verilog -noattr {netlist}; write_json {out}/netlist-dataset-service.json'
            run('synth-dataset-service', ['yosys', '-p', script], timeout=3600)
            module = load(out / 'netlist-dataset-service.json')['modules']['randomx_dataset_service']
            kinds = Counter(x['type'] for x in module['cells'].values())
            summary['mapping'] = {'top': 'randomx_dataset_service', 'ITEMS_PER_BATCH': 2, 'cells': sum(kinds.values()),
                'DFF': sum(n for k, n in kinds.items() if 'DFF' in k), 'latches': sum(n for k, n in kinds.items() if 'LATCH' in k),
                'cell_types': dict(sorted(kinds.items())), 'scope': 'New service bridge plus unchanged dataset-item/executor/multipliers; no whole lifecycle or physical mapping.'}
            assert summary['mapping']['latches'] == 0
            cells = out / 'yosys-simcells.v'; shutil.copyfile('/usr/share/yosys/simcells.v', cells)
            save(out / 'yosys-cell-model.json', {'installed': '/usr/share/yosys/simcells.v', 'sha256': sha(cells)})
            summary['service_unit']['mapped'] = unit('dataset-service-mapped', netlist, cells)
            assert summary['service_unit']['mapped']['PASS'] == summary['service_unit']['RTL']['PASS']
        assert len(summary['normal_profiles']) == 3 and len(summary['controls']) == 5
        assert all(sha(ROOT / n) == row['sha256'] for n, row in hashes.items())
        assert all(sha(gold / n) == row['sha256'] for n, row in gold_hashes.items())
        verify_assets(args.asset_root.resolve(), ROOT / LOCK, ROOT,
                      receipt=args.asset_receipt.resolve() if args.asset_receipt else None,
                      receipt_sha=args.asset_receipt_sha256,
                      verify=args.asset_root_verify.resolve() if args.asset_root_verify else None)
        assert sha(library) == summary['native_library']['sha256']
        summary['source_and_prepared_assets_unchanged_after_run'] = True
        summary['status'] = 'pass_bounded_dataset_lifecycle_integration'
        summary['remaining_host_services'] = ['Retained Argon2/cache initialization and superscalar/global reciprocal preparation/export',
            'Tagged immutable cache/program/table responses and external scratchpad service',
            'Assertion-only native input/AES program/dataset/reference computations, separately counted',
            'Full default hash requires a separately reviewed transaction namespace extension or quiescent rotation']
        print('PASS dataset_hash_lifecycle_suite programs=2 iterations=1 native_dataset_items=2 normal_profiles=3 recovery_profiles=5 old_component_workloads_repeated=0', flush=True)
    except BaseException as e:
        summary['status'] = 'failed'; summary['error'] = repr(e)
        raise
    finally:
        save(out / 'summary.json', summary)
        save(out / 'artifacts.sha256.json', {str(x.relative_to(out)): sha(x) for x in sorted(out.rglob('*'))
             if x.is_file() and x.name != 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
