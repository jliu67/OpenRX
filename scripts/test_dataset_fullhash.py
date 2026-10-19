#!/usr/bin/env python3
"""Admitted full 8x2048 hardware-dataset hash using retained prepared cache0.

--prepare-only builds one model and NEW compatible full native assertion gold;
it does not execute the RTL workload. A later admitted invocation can reuse that
output with an externally pinned --prepared-manifest-sha256. No accepted cache,
superscalar program, reciprocal table, native archive or old campaign is rebuilt.
"""
import argparse
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
from dataset_capacity_support import load, save, sha, verify_assets, REFERENCE_LOCK
from dataset_lifecycle_support import Supervisor
from test_dataset_capacity import (BENCH, TEST, LOCK, SERVICE_RTL, WRAPPER, source_inputs)
from test_dataset_hash_lifecycle import EXTRA
from test_divsqrt_execute import RTL as EXECUTE_RTL, V
from test_iteration_engine import extract, function
from test_dataset_item import provenance_library
from hardfloat_compile_view import prepare as compile_view
from program_sequence_fixture import prepare as prepare_assertions

ROOT = Path(__file__).resolve().parents[1]
BASE = 'fa0bc79bdcd89c91aab11596b6f7f5e104aa6884'
PROGRAMS, ITERATIONS, ITEMS = 8, 2048, 16384
IDEAL_EXECUTOR, CORE_OVERHEAD, LAUNCH = 53325, 74, 1
WATCHDOG = 1500000000
REFERENCE = TEST + 'dataset_fullhash_reference.cpp'
PREPARED_SCHEMA = 'openrx.dataset-fullhash.prepared.v1'


def identity(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), str(path)
    return {'bytes': path.stat().st_size, 'sha256': sha(path)}


def regular_under(root, relative):
    relative = Path(relative)
    assert relative.parts and not relative.is_absolute() and '..' not in relative.parts
    path = root
    for part in relative.parts:
        path = path / part
        assert not path.is_symlink(), str(path)
    assert path.is_file(), str(path)
    return path


def fresh_output(value, source=ROOT):
    """Canonicalize traversal/symlink ancestors before checking source isolation."""
    source = Path(source).resolve(strict=True)
    path = Path(value).resolve(strict=False)
    assert not path.exists() and path != source and source not in path.parents
    assert re.fullmatch('[-A-Za-z0-9_./]+', str(path))
    return path


def message_bytes():
    profile = load(ROOT / REFERENCE_LOCK)['profile']
    assert profile['cache_key'] == 'test key 000' and profile['input_bytes'] == 52
    message = bytes.fromhex(profile['input_hex'])
    assert len(message) == profile['input_bytes']
    return message


def parameters(watchdog=WATCHDOG, progress=64):
    assert type(watchdog) is int and 1000000000 <= watchdog <= 2000000000
    assert type(progress) is int and 1 <= progress <= 2048
    return {'PROGRAMS': PROGRAMS, 'ITERATIONS': ITERATIONS, 'PREPARED_RCP': 1,
        'HARDWARE_FILL': 1, 'HARDWARE_PROGRAM': 1, 'HARDWARE_INPUT_HASH': 1,
        'HARDWARE_DATASET': 1, 'DATASET_SESSION_BITS': 32, 'DATASET_MUL_RADIX4': 1,
        'EVENT_TRACE': 1, 'STALL': 0, 'WATCHDOG_CYCLES': watchdog, 'PROGRESS_ITEMS': progress}


def validate_mode(prepare_only, prepared_output, manifest_sha, wall_seconds):
    assert bool(prepared_output) == bool(manifest_sha), 'prepared output and externally trusted manifest SHA256 required together'
    assert not (prepare_only and prepared_output), 'prepare-only creates a new prepared output'
    if not prepare_only:
        assert prepared_output, 'first admit prepare-only; full execution reuses its pinned prepared output'
        assert type(wall_seconds) is int and wall_seconds > 0, 'full execution needs its admitted explicit positive wall-time budget'


def simulation_argv(prepared, output, assets, message):
    return [str(prepared / 'obj-fullhash/sim'), '+directory=' + str(prepared / 'native-reference'),
        '+output=' + str(output), '+asset_root=' + str(assets),
        '+input=' + format(int.from_bytes(message, 'little'), 'x'),
        '+input_bytes=' + str(len(message))]


def validate_reference(gold, message):
    native, full, host = (load(gold / name) for name in
        ('oracle-summary.json', 'full-reference.json', 'dataset-native-host-time.json'))
    assert native['programs'] == PROGRAMS and native['iterations_per_program'] == ITERATIONS
    assert native['total_iterations'] == ITEMS and native['v2'] == 1
    assert native['instruction_steps'] >= ITEMS * 384 and native['bytecode_events'] > 0
    assert full['canonical_randomx_calculate_hash_verified'] is True
    assert full['bounded_iteration_profile'] is False and full['cache_key'] == 'test key 000'
    assert full['input_hex'] == message.hex() and full['canonical_host_seconds'] >= 0
    assert host['role'] == 'native-reference'
    assert host['dataset_requests'] == host['native_dataset_gold_export_rows'] == ITEMS
    assert host['assertion_only_dataset_requests'] == 0
    for name in ('argon_initializations', 'native_cache_program_generations', 'cache_image_export_bytes'):
        assert host[name] == 0
    items = [line.split() for line in (gold / 'dataset-items.hex').read_text().splitlines()]
    assert len(items) == ITEMS
    for row in items:
        assert len(row) == 2 and re.fullmatch('[0-9a-f]{16}', row[0])
        assert re.fullmatch('[0-9a-f]{128}', row[1])
        assert int(row[0], 16) % 64 == 0 and int(row[0], 16) <= 2181038016 - 64
    assert re.fullmatch('[0-9a-f]{64}\n', (gold / 'final-digest32.hex').read_text())
    for program in range(PROGRAMS):
        assert len((gold / f'final-{program}.hex').read_text().splitlines()) == 131072
        assert len((gold / f'program-{program}.mem').read_text().splitlines()) == 384
    assert len((gold / 'iterations.hex').read_text().splitlines()) == ITEMS
    assert len((gold / 'metadata.hex').read_text().splitlines()) == PROGRAMS
    return native, full, host, items


def validate_full_ledgers(ledger, dataset, provider, native, rows, items):
    """Close actual full-run cost partitions, including every native item address."""
    assert all(ledger[key] is True for key in
        ('hardware_fill_enabled', 'hardware_program_enabled', 'hardware_input_hash_enabled'))
    assert 0 < ledger['cycles'] < 2000000000
    assert sum(ledger['stage_cycles'].values()) == ledger['cycles']
    for phases, stage in [('nested_iteration_phases', 'execution'),
        ('nested_finalization_phases', 'finalization'), ('nested_input_hash_phases', 'input_hash'),
        ('nested_program_generation_phases', 'program_generation')]:
        assert all(type(x) is int and x >= 0 for x in ledger[phases])
        assert sum(ledger[phases]) == ledger['stage_cycles'][stage]
    assert sum(ledger['nested_executor_phases']) == ledger['nested_iteration_phases'][7]
    assert ledger['nested_initialization']['provider_wait'] == 0
    assert sum(ledger['nested_initialization']['fill_phases']) == ledger['stage_cycles']['initialization_hardware_fill']
    assert ledger['scratchpad_bytes'] == 2097152
    assert ledger['dataset_logical_bytes'] == ITEMS * 64
    assert ledger['logical_entry_bytes'] == ledger['logical_tail_bytes'] == ITEMS * 128
    assert ledger['program_image_load_bytes'] == PROGRAMS * 384 * 8
    assert ledger['logical_bytecode_memory_bytes'] == native['bytecode_events'] * 8
    assert ledger['preparation_reciprocals'] == native['static_active_reciprocals']
    assert ledger['runtime_reciprocals'] == 0 and ledger['untimed_provider_device_cycles'] is None
    assert provider['cache_key_hex'] == '74657374206b657920303030'
    for name in ('input_hash_calls', 'software_fill_provider_calls', 'program_generations',
        'dataset_requests', 'assertion_only_dataset_requests', 'argon_initializations',
        'native_cache_program_generations', 'cache_image_export_bytes', 'cache_initialization_host_seconds'):
        assert provider[name] == 0, name
    assert provider['assertion_only_input_hash_calls'] == 1
    assert provider['assertion_only_program_generations'] == PROGRAMS
    assert provider['cache_bytes'] == 268435456 and provider['materialized_dataset_bytes'] == 0
    assert provider['logical_dataset_bytes'] == 2181038016 and provider['provider_device_cycles'] is None
    assert dataset['schema'] == 'openrx.dataset-capacity.nested-ledger.v1'
    assert dataset['hardware_dataset'] == 1 and dataset['outer_cycles'] == ledger['cycles']
    for key in ('dataset_costs_are_nested_not_added_to_outer_total', 'all_descriptors_captured',
                'full_native_digest_registers_scratchpad'):
        assert dataset[key] is True
    assert dataset['physical_cache_service'] is None
    assert dataset['session_namespace_bits'] == 32 and dataset['external_tag_bits'] == 64
    assert dataset['captured_asset_epoch'] == 0x4ca3
    assert len(rows) == len(items) == ITEMS
    for name in ('demands', 'responses', 'items', 'item_returns', 'sessions_used'):
        assert dataset[name] == ITEMS
    assert dataset['live_native_dataset_calls'] == 0
    assert dataset['stages'] == dataset['cache_requests'] == dataset['cache_responses'] == ITEMS * 8
    assert dataset['retirements'] == dataset['instruction_requests'] == dataset['instruction_responses'] == ITEMS * 3563
    for phases, count in [('service_phase_cycles', 3), ('session_phase_cycles', 3), ('item_phase_cycles', 9)]:
        assert len(dataset[phases]) == count
        assert all(type(x) is int and x >= 0 for x in dataset[phases])
    assert sum(dataset['service_phase_cycles']) == sum(dataset['session_phase_cycles']) == ledger['stage_cycles']['execution']
    assert sum(dataset['item_phase_cycles']) <= ledger['stage_cycles']['execution']
    assert dataset['session_phase_cycles'][1] == ITEMS
    totals = Counter()
    numeric = ['item_cycles', 'core_cycles', 'executor_cycles', 'session_launch_extra', 'stages',
        'retired', 'muls', 'instruction_service_extra', 'cache_service_extra', 'request_to_first_response']
    for ordinal, (row, native_item) in enumerate(zip(rows, items), 1):
        assert int(row['tag'], 16) == 0x10000 + ordinal
        assert int(row['item_namespace'], 16) == ordinal
        assert int(row['image_epoch'], 16) == dataset['captured_asset_epoch']
        assert int(row['address'], 16) == int(native_item[0], 16)
        values = {key: int(row[key]) for key in numeric}
        assert all(value >= 0 for value in values.values())
        assert values['stages'] == 8 and values['retired'] == 3563 and values['muls'] == 1254
        assert values['executor_cycles'] == IDEAL_EXECUTOR and values['instruction_service_extra'] == 0
        assert values['core_cycles'] == IDEAL_EXECUTOR + CORE_OVERHEAD and values['cache_service_extra'] == 0
        assert values['session_launch_extra'] == LAUNCH
        assert values['item_cycles'] == values['request_to_first_response'] == IDEAL_EXECUTOR + CORE_OVERHEAD + LAUNCH
        totals.update(values)
    for field, column in [('item_availability_clocks', 'item_cycles'),
        ('core_item_availability_clocks', 'core_cycles'), ('session_launch_extra_clocks', 'session_launch_extra'),
        ('executor_clocks', 'executor_cycles'), ('stages', 'stages'), ('retirements', 'retired'),
        ('program_service_extra_clocks', 'instruction_service_extra'), ('cache_service_extra_clocks', 'cache_service_extra')]:
        assert dataset[field] == totals[column]
    assert dataset['ideal_executor_clocks_each'] == IDEAL_EXECUTOR
    assert dataset['item_availability_clocks'] == ITEMS * 53400 == 874905600
    assert dataset['core_item_availability_clocks'] == ITEMS * 53399
    assert dataset['executor_clocks'] == ITEMS * IDEAL_EXECUTOR
    assert dataset['session_launch_extra_clocks'] == ITEMS
    for key in ('program_service_extra_clocks', 'cache_service_extra_clocks', 'stale_packets_drained',
                'cache_request_stalls', 'instruction_request_stalls'):
        assert dataset[key] == 0
    # The request/reply bridge overhead of one clock per iteration is outside the
    # child availability; both are already included in outer execution.
    assert ledger['nested_reply_waits']['dataset'] == dataset['item_availability_clocks'] + ITEMS
    return {'all_iteration_states_checked': ITEMS, 'program_scratchpad_bytes_checked': PROGRAMS * 2097152,
        'dataset_items_compared_to_native': ITEMS, 'dataset_item_availability_clocks': dataset['item_availability_clocks'],
        'dataset_executor_clocks': dataset['executor_clocks'],
        'dataset_costs_nested_in_outer_cycles': True, 'physical_service_or_PPA_validated': False}


def verify_prepared(directory, expected_sha, current_sources, message):
    directory = Path(directory).absolute()
    assert directory.is_dir() and all(not p.is_symlink() for p in [directory, *directory.parents])
    directory = directory.resolve(strict=True)
    manifest_path = regular_under(directory, 'prepared-manifest.json')
    assert re.fullmatch('[0-9a-f]{64}', expected_sha or '')
    assert sha(manifest_path) == expected_sha, 'externally pinned prepared-manifest identity'
    manifest = load(manifest_path)
    assert manifest['schema'] == PREPARED_SCHEMA and manifest['status'] == 'prepared_not_executed'
    assert manifest['source_inputs'] == current_sources
    assert manifest['input_hex'] == message.hex() and manifest['programs'] == PROGRAMS and manifest['iterations'] == ITERATIONS
    assert manifest['parameters'] == parameters(manifest['parameters']['WATCHDOG_CYCLES'], manifest['parameters']['PROGRESS_ITEMS'])
    files = manifest['files']
    assert set(files) == {'obj-fullhash/sim'} | {
        'native-reference/' + p.name for p in (directory / 'native-reference').iterdir() if p.is_file()}
    for name, expected in files.items():
        assert identity(regular_under(directory, name)) == expected, 'actual prepared input: ' + name
    command_path = regular_under(directory, 'commands.json')
    assert identity(command_path) == manifest['commands_identity']
    commands = load(command_path)
    assert commands == manifest['commands']
    assert [row['label'] for row in commands] == [
        'fullhash-unit', 'compile-full-reference', 'native-full-reference', 'compile-fullhash']
    for row in commands:
        assert row['returncode'] == 0 and row['wall_timeout'] is False
        assert row['group_empty_after_cleanup'] is True and 'error' not in row
    assert commands[2]['argv'] == [str(directory / 'reference'), str(directory / 'native-reference'),
        '8', '2048', '1', message.hex()]
    assert manifest['source_tree'] == subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip()
    validate_reference(directory / 'native-reference', message)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--asset-root', type=Path, required=True)
    parser.add_argument('--asset-receipt', type=Path)
    parser.add_argument('--asset-receipt-sha256')
    parser.add_argument('--asset-root-verify', type=Path)
    parser.add_argument('--native-library', type=Path, required=True)
    parser.add_argument('--native-build-execution', type=Path, required=True)
    parser.add_argument('--verilator-root', type=Path, required=True)
    parser.add_argument('--verilator-build-execution', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6, choices=range(1, 7))
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--prepared-output', type=Path)
    parser.add_argument('--prepared-manifest-sha256')
    parser.add_argument('--simulation-timeout-seconds', type=int)
    parser.add_argument('--watchdog-cycles', type=int, default=WATCHDOG)
    parser.add_argument('--progress-items', type=int, default=64)
    args = parser.parse_args()
    try:
        out = fresh_output(args.out)
    except AssertionError:
        parser.error('fresh unambiguous output outside source required; preserve all attempts')
    try:
        validate_mode(args.prepare_only, args.prepared_output, args.prepared_manifest_sha256,
                      args.simulation_timeout_seconds)
    except AssertionError as error:
        parser.error(str(error))
    params = parameters(args.watchdog_cycles, args.progress_items)
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip(), 'freeze clean source before admission'
    sources = list(dict.fromkeys([*EXECUTE_RTL, *EXTRA, *SERVICE_RTL, WRAPPER,
        *[str(p.relative_to(ROOT)) for p in sorted((ROOT / 'rtl/hash').glob('randomx_*.v'))
          if p.name not in ('randomx_program_hash_sequence.v', 'randomx_prepared_dataset_hash_lifecycle.v')]]))
    source_hashes = source_inputs(sources)
    for name in [REFERENCE, 'scripts/test_dataset_fullhash.py', 'tests/test_dataset_fullhash.py']:
        source_hashes[name] = identity(ROOT / name)
    message = message_bytes()
    out.mkdir(parents=True)
    supervisor = Supervisor(out)
    run = supervisor.run
    summary = {'schema': 'openrx.dataset-fullhash.validation.v1', 'status': 'running', 'base': BASE,
        'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip(),
        'programs': PROGRAMS, 'iterations': ITERATIONS, 'input_hex': message.hex(), 'cache_key': 'test key 000',
        'full_hash_execution': False, 'prepare_only': args.prepare_only, 'jobs': args.jobs,
        'old_component_campaigns_repeated': False, 'accepted_assets_regenerated': False,
        'physical_PPA_validated': False, 'parameters': params}
    save(out / 'inputs.json', source_hashes)
    try:
        assets = args.asset_root.resolve(strict=True)
        library = args.native_library.resolve(strict=True)
        toolroot = args.verilator_root.resolve(strict=True)
        summary['prepared_assets'] = verify_assets(assets, ROOT / LOCK, ROOT, receipt=args.asset_receipt,
            receipt_sha=args.asset_receipt_sha256, verify=args.asset_root_verify)
        summary['native_library'] = provenance_library(library, args.native_build_execution.resolve(strict=True))
        toolreceipt = load(args.verilator_build_execution / 'receipt.json')
        assert toolreceipt['process']['returncode'] == 0
        toolrows = {Path(row['path']): row for row in toolreceipt['artifacts']}
        toolfiles = {}
        for path in sorted(toolroot.rglob('*')):
            assert not path.is_symlink(), str(path)
            if not path.is_file(): continue
            value = identity(path); row = toolrows[path]
            assert value == {'bytes': row['bytes'], 'sha256': row['sha256']}
            toolfiles[str(path.relative_to(toolroot))] = value
        assert toolfiles and 'bin/verilator' in toolfiles and 'bin/verilator_bin' in toolfiles
        summary['verilator'] = {'root': str(toolroot), 'files': toolfiles,
            'receipt_sha256': sha(args.verilator_build_execution / 'receipt.json')}
        env = dict(os.environ, VERILATOR_ROOT=str(toolroot), RX_PREPARED_CACHE_ROOT=str(assets))
        env.pop('RX_PREPARED_REFERENCE_OUTPUT', None)
        if args.prepared_output:
            prepared = args.prepared_output.absolute()
            manifest = verify_prepared(prepared, args.prepared_manifest_sha256, source_hashes, message)
            assert manifest['parameters'] == params
            assert manifest['native_archive_sha256'] == sha(library)
            assert manifest['prepared_assets'] == summary['prepared_assets']['assets']
            assert manifest['verilator_files'] == toolfiles
            summary['prepared_reuse'] = {'path': str(prepared), 'manifest_sha256': args.prepared_manifest_sha256,
                'actual_consumed_files_verified': len(manifest['files']), 'source_tree_equal': True}
            summary['native_reference_generated'] = False
        else:
            prepared = out
            run('fullhash-unit', ['python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_dataset_fullhash.py', '-v'])
            compat = compile_view(ROOT / V / 'divSqrtRecFN_small.v', out)
            compile_sources = [str(compat) if name == V + 'divSqrtRecFN_small.v' else name for name in sources]
            extract(out)
            virtual = (ROOT / 'vendor/randomx/src/virtual_machine.cpp').read_text()
            notice = virtual[:virtual.index('*/') + 2] + '\n'
            bodies = {'pinned_program_initialize.inc': function(virtual, 'void randomx_vm::initialize()', True),
                'pinned_program_float_helpers.inc': 'namespace randomx {\n' + '\n'.join(function(virtual, name) for name in
                    ['static inline uint64_t getSmallPositiveFloatBits(', 'static inline uint64_t getStaticExponent(',
                     'static inline uint64_t getFloatMask(']) + '\n}\n'}
            for name, body in bodies.items(): (out / name).write_text(notice + body)
            save(out / 'program-extraction.json', {'source_sha256': sha(ROOT / 'vendor/randomx/src/virtual_machine.cpp'),
                'generated': {name: sha(out / name) for name in bodies}})
            run('compile-full-reference', ['g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-I' + str(out),
                '-Ivendor/randomx/src', '-Irtl/execute/tests', '-Irtl/hash/tests', '-I' + TEST,
                REFERENCE, str(library), '-pthread', '-ldl', '-o', str(out / 'reference')], timeout=1800)
            gold = out / 'native-reference'; gold.mkdir()
            run('native-full-reference', [str(out / 'reference'), str(gold), '8', '2048', '1', message.hex()],
                env=dict(env, RX_PREPARED_REFERENCE_OUTPUT=str(gold)), timeout=1800)
            summary['native_reference'] = prepare_assertions(gold)
            validate_reference(gold, message)
            summary['native_reference_generated'] = True
            includes = ['-Irtl/execute', '-I' + V, '-I' + V + '8086-SSE', '-Irtl/hash/vendor/blake2', '-I' + str(gold)]
            cppflags = '-std=c++20 -O2 ' + ' '.join('-I' + str(ROOT / path) for path in
                ('vendor/randomx/src', 'rtl/execute/tests', 'rtl/hash/tests', TEST))
            run('compile-fullhash', [str(toolroot / 'bin/verilator'), '--binary', '--timing', '-j', str(args.jobs),
                '-Wno-fatal', '-MAKEFLAGS', 'OPT_FAST=-O3', '--top-module', 'tb_dataset_capacity_hash_lifecycle',
                '--Mdir', str(out / 'obj-fullhash'), '-o', 'sim', *includes,
                *['-G' + key + '=' + str(value) for key, value in params.items()], '-CFLAGS', cppflags,
                '-LDFLAGS', str(library) + ' -pthread -ldl', *compile_sources, BENCH,
                str(ROOT / TEST / 'dataset_capacity_source_dpi.cpp')], env=env, timeout=7200)
            files = {'obj-fullhash/sim': identity(out / 'obj-fullhash/sim')}
            files.update({'native-reference/' + path.name: identity(path) for path in sorted(gold.iterdir())})
            manifest = {'schema': PREPARED_SCHEMA, 'status': 'prepared_not_executed',
                'source_head': summary['source_head'], 'source_tree': summary['source_tree'], 'source_inputs': source_hashes,
                'programs': PROGRAMS, 'iterations': ITERATIONS, 'input_hex': message.hex(), 'parameters': params,
                'files': files, 'native_archive_sha256': sha(library),
                'prepared_assets': summary['prepared_assets']['assets'], 'verilator_files': toolfiles,
                'commands_identity': identity(out / 'commands.json'), 'commands': supervisor.commands}
            save(out / 'prepared-manifest.json', manifest)
            summary['prepared_manifest_sha256'] = sha(out / 'prepared-manifest.json')
        gold = prepared / 'native-reference'
        native, canonical, native_host, items = validate_reference(gold, message)
        summary.update({'native_reference': native, 'canonical_reference': canonical, 'native_host': native_host})
        if args.prepare_only:
            summary['status'] = 'prepared_not_executed'
            print('PASS dataset_fullhash_prepare canonical_native=1 rtl_hash_executed=0', flush=True)
        else:
            directory = out / 'hardware-dataset-full-ideal'; directory.mkdir()
            summary['simulation_command'] = simulation_argv(prepared, directory, assets, message)
            summary['simulation_command_result'] = run('hardware-dataset-full-ideal', summary['simulation_command'],
                env=env, timeout=args.simulation_timeout_seconds)
            with (directory / 'dataset-items-ledger.csv').open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            ledger, dataset, provider = (load(directory / name) for name in
                ('ledger.json', 'dataset-ledger.json', 'provider-host-time.json'))
            summary['comparison'] = validate_full_ledgers(ledger, dataset, provider, native, rows, items)
            assert (directory / 'actual-final-digest32.hex').read_bytes() == (gold / 'final-digest32.hex').read_bytes()
            lines = (out / 'hardware-dataset-full-ideal.log').read_text().splitlines()
            assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines)
            records = [line for line in lines if line.startswith('PASS ')]
            assert len(records) == 2 and any(line.startswith('PASS dataset_capacity_hash_lifecycle ') for line in records)
            assert any(line.startswith('PASS prepared_hash_lifecycle ') for line in records)
            progress = [json.loads(line) for line in (directory / 'progress.jsonl').read_text().splitlines()]
            assert progress[0]['event_kind'] == 0 and progress[-1]['event_kind'] == 3
            assert progress[-1]['iterations_checked'] == progress[-1]['dataset_items_checked'] == ITEMS
            assert progress[-1]['programs_checked'] == PROGRAMS
            summary.update({'status': 'pass_full_hardware_dataset_hash', 'full_hash_execution': True,
                'ledger': ledger, 'dataset': dataset, 'provider': provider, 'PASS': records,
                'final_digest_hex': (gold / 'final-digest32.hex').read_text().strip()})
            print('PASS dataset_fullhash programs=8 iterations=2048 native_canonical=1 full_hardware_dataset=1 physical_PPA=0', flush=True)
        for name, expected in source_hashes.items(): assert identity(ROOT / name) == expected
        verify_assets(assets, ROOT / LOCK, ROOT, receipt=args.asset_receipt,
            receipt_sha=args.asset_receipt_sha256, verify=args.asset_root_verify)
        assert sha(library) == summary['native_library']['sha256']
        for name, expected in toolfiles.items(): assert identity(toolroot / name) == expected
        for name, expected in manifest['files'].items(): assert identity(regular_under(prepared, name)) == expected
        summary['all_consumed_sources_prepared_gold_assets_and_tools_unchanged'] = True
    except BaseException as error:
        summary['status'] = 'failed'; summary['error'] = repr(error)
        raise
    finally:
        summary['remaining_host_services'] = [
            'Retained host Argon2/cache image, superscalar programs and global reciprocal preparation (not regenerated)',
            'Host immutable prepared cache/program/reciprocal service responses and scratchpad model; physical latency/traffic unknown',
            'Native reference and separately counted assertion-only input/program/interprogram hashes; no live software dataset/input/fill/program provider on RTL path',
            'No physical ASIC/PPA, calibrated clock frequency or architecture selection']
        summary['host_timing_boundary'] = {
            'native_reference_whole_command_and_canonical_hash': 'Measured separately in command ledger and full-reference.json',
            'native_dataset_items_cache_load_and_gold_export': 'Separately measured host seconds; never hardware clocks',
            'native_reference_input_fill_program_interprogram_and_finalization': 'Inside whole native command; not individually timed by callback counters',
            'RTL_live_input_fill_program_and_dataset_providers': 'Must all have zero calls for a completed run',
            'RTL_assertion_callbacks': 'Input/program/hash assertions separately counted or timed; outside modeled hardware clocks',
            'host_prepared_cache_instruction_reciprocal_and_scratchpad_services': 'Testbench service model only; physical service cycles/traffic/PPA unknown'}
        save(out / 'summary.json', summary)
        save(out / 'artifacts.sha256.json', {str(path.relative_to(out)): sha(path) for path in sorted(out.rglob('*'))
            if path.is_file() and path.name != 'artifacts.sha256.json'})


if __name__ == '__main__': main()
