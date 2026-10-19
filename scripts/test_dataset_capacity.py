#!/usr/bin/env python3
"""Bounded dataset session namespace validation using retained native reference.

Run only through reviewed admission. No reference executable, native gold,
Argon/cache export or superscalar preparation campaign is run by this driver.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from dataset_capacity_support import (Supervisor, load, save, sha, verify_assets,
    verify_reference, verify_selected_assets, REFERENCE_LOCK, FIXTURE_INDEX)
from test_dataset_hash_lifecycle import validate_outer, EXTRA
from test_divsqrt_execute import RTL as EXECUTE_RTL, V
from test_iteration_engine import extract, function
from test_dataset_item import provenance_library
from hardfloat_compile_view import prepare as compile_view
from program_sequence_fixture import prepare as prepare_assertions

ROOT = Path(__file__).resolve().parents[1]
BASE = 'a84602c5348723e4c388ccd50f3a16096f3054f9'
TEST = 'rtl/dataset_capacity/tests/'
BENCH = TEST + 'tb_dataset_capacity_hash_lifecycle.v'
UNIT_BENCH = TEST + 'tb_dataset_capacity.v'
LOCK = 'rtl/dataset_service/dataset-context.lock.json'
PUBLIC_BASELINE = 'docs/validation/dataset-lifecycle-20261018/bounded-results.json'
PUBLIC_SOURCE_INDEX = 'docs/validation/dataset-lifecycle-20261018/source-inputs.json'
SERVICE_RTL = ['rtl/execute/randomx_mul64.v', 'rtl/execute/randomx_superscalar_execute.v',
    'rtl/dataset/randomx_dataset_item.v', 'rtl/dataset_capacity/randomx_dataset_item_session.v',
    'rtl/dataset_capacity/randomx_dataset_capacity_service.v']
WRAPPER = 'rtl/dataset_capacity/randomx_prepared_dataset_capacity_hash_lifecycle.v'
STAGES = {'control_and_metadata': 8, 'execution': 4995, 'finalization': 393286,
    'held_return': 1, 'initialization_hardware_fill': 131074, 'input_hash': 30,
    'interprogram_seed': 60, 'program_generation': 1606, 'program_preparation': 3322}
NESTED = {'executor': 4935, 'finalization': 393286, 'initial_fill': 131074,
          'input_hash': 30, 'iteration': 4995, 'program_generation': 1606}


def source_inputs(sources):
    """Actual consumed sources plus explicit public trust bindings, no claims-only reuse."""
    names = set(sources + [BENCH, UNIT_BENCH, LOCK, REFERENCE_LOCK, FIXTURE_INDEX,
                          PUBLIC_BASELINE, PUBLIC_SOURCE_INDEX])
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'vendor/randomx').rglob('*') if p.is_file())
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'scripts').glob('*.py'))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'tests').glob('test_dataset_capacity_*.py'))
    for directory in (ROOT/'rtl/hash/tests', ROOT/TEST):
        names.update(str(p.relative_to(ROOT)) for p in directory.glob('*')
                     if p.is_file() and p.suffix in ('.cpp', '.hpp'))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'rtl').rglob('*')
                 if p.is_file() and (p.suffix in ('.vh', '.vi') or
                                     p.name in ('LICENSE', 'manifest.json', 'UPSTREAM.json')))
    names.update(['vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                  'rtl/execute/tests/program_native_helpers.hpp'])
    return {n: {'bytes': (ROOT/n).stat().st_size, 'sha256': sha(ROOT/n)} for n in sorted(names)}


def validate_dataset(dataset, ledger, rows, native_items, stalled):
    """Close measured session, private core and executor costs independently."""
    assert len(native_items) == len(rows) == 2
    assert dataset['schema'] == 'openrx.dataset-capacity.nested-ledger.v1'
    assert dataset['hardware_dataset'] == 1 and dataset['outer_cycles'] == ledger['cycles']
    for key in ('dataset_costs_are_nested_not_added_to_outer_total', 'all_descriptors_captured',
                'full_native_digest_registers_scratchpad'):
        assert dataset[key] is True
    assert dataset['physical_cache_service'] is None
    assert dataset['demands'] == dataset['responses'] == dataset['items'] == dataset['item_returns'] == 2
    assert dataset['live_native_dataset_calls'] == 0
    assert dataset['session_namespace_bits'] == 32 and dataset['external_tag_bits'] == 64
    assert dataset['sessions_used'] == 2 and dataset['captured_asset_epoch'] == 0x4ca3
    counters = ['demands', 'responses', 'items', 'item_returns', 'stages', 'retirements',
        'item_availability_clocks', 'core_item_availability_clocks', 'session_launch_extra_clocks',
        'executor_clocks', 'ideal_executor_clocks_each', 'program_service_extra_clocks',
        'cache_service_extra_clocks', 'cache_requests', 'cache_responses',
        'instruction_requests', 'instruction_responses', 'stale_packets_drained',
        'cache_request_stalls', 'instruction_request_stalls', 'sessions_used']
    assert all(type(dataset[k]) is int and dataset[k] >= 0 for k in counters)
    for key, size in [('service_phase_cycles', 3), ('session_phase_cycles', 3), ('item_phase_cycles', 9)]:
        assert len(dataset[key]) == size
        assert all(type(x) is int and x >= 0 for x in dataset[key])
    assert sum(dataset['service_phase_cycles']) == sum(dataset['session_phase_cycles']) == ledger['stage_cycles']['execution']
    assert sum(dataset['item_phase_cycles']) <= sum(dataset['session_phase_cycles'])
    assert dataset['session_phase_cycles'][1] == 2
    assert dataset['ideal_executor_clocks_each'] == 53325
    assert dataset['stages'] == dataset['cache_requests'] == dataset['cache_responses'] == 16
    assert dataset['retirements'] == dataset['instruction_requests'] == dataset['instruction_responses'] == 7126
    totals = Counter()
    numeric = ['item_cycles', 'core_cycles', 'executor_cycles', 'session_launch_extra',
        'stages', 'retired', 'muls', 'instruction_service_extra', 'cache_service_extra',
        'request_to_first_response']
    for ordinal, (row, expected) in enumerate(zip(rows, native_items), 1):
        assert int(row['tag'], 16) == 0x10000 + ordinal
        assert int(row['item_namespace'], 16) == ordinal
        assert int(row['image_epoch'], 16) == dataset['captured_asset_epoch']
        assert int(row['address'], 16) == int(expected[0], 16)
        values = {k: int(row[k]) for k in numeric}
        assert all(v >= 0 for v in values.values())
        assert values['stages'] == 8 and values['retired'] == 3563 and values['muls'] == 1254
        assert values['executor_cycles'] == 53325 + values['instruction_service_extra']
        assert values['core_cycles'] == values['executor_cycles'] + 74 + values['cache_service_extra']
        assert values['session_launch_extra'] == 1
        assert values['item_cycles'] == values['core_cycles'] + values['session_launch_extra']
        assert values['request_to_first_response'] == values['item_cycles']
        totals.update(values)
    for field, column in [('item_availability_clocks', 'item_cycles'),
        ('core_item_availability_clocks', 'core_cycles'), ('session_launch_extra_clocks', 'session_launch_extra'),
        ('executor_clocks', 'executor_cycles'), ('stages', 'stages'), ('retirements', 'retired'),
        ('program_service_extra_clocks', 'instruction_service_extra'), ('cache_service_extra_clocks', 'cache_service_extra')]:
        assert dataset[field] == totals[column]
    assert dataset['executor_clocks'] == 106650 + dataset['program_service_extra_clocks']
    assert dataset['core_item_availability_clocks'] == dataset['executor_clocks'] + 148 + dataset['cache_service_extra_clocks']
    assert dataset['session_launch_extra_clocks'] == 2
    assert dataset['item_availability_clocks'] == dataset['core_item_availability_clocks'] + 2
    extras = ['program_service_extra_clocks', 'cache_service_extra_clocks', 'stale_packets_drained',
              'cache_request_stalls', 'instruction_request_stalls']
    if stalled:
        assert all(dataset[k] > 0 for k in extras)
    else:
        assert dataset['item_availability_clocks'] == 106800
        assert dataset['core_item_availability_clocks'] == 106798
        assert all(dataset[k] == 0 for k in extras)


def compare_ideal_profiles(profile, baseline=None):
    """Compare with the source-bound PUBLIC software baseline, not reused raw claims."""
    baseline = load(ROOT/PUBLIC_BASELINE) if baseline is None else baseline
    assert baseline['schema'] == 'openrx.dataset-lifecycle.bounded-results.v1'
    software = baseline['normal_profiles']['software-dataset-ideal']
    assert software['stage_cycles'] == STAGES and software['nested_phase_sums'] == NESTED
    assert software['total_modeled_clocks'] == software['stage_sum'] == sum(STAGES.values()) == 534382
    assert software['dataset_reply_wait_clocks'] == 2
    assert software['full_native_registers_2MiB_scratchpad_digest_equal'] is True
    ledger, dataset = profile['ledger'], profile['dataset']
    delta = ledger['cycles'] - software['total_modeled_clocks']
    assert delta == dataset['item_availability_clocks'] == 106800
    assert set(ledger['stage_cycles']) == set(STAGES)
    assert sum(ledger['stage_cycles'].values()) == ledger['cycles']
    for stage, clocks in STAGES.items():
        assert ledger['stage_cycles'][stage] - clocks == (delta if stage == 'execution' else 0)
    assert ledger['nested_reply_waits']['dataset'] - software['dataset_reply_wait_clocks'] == delta
    actual = {'executor': sum(ledger['nested_executor_phases']),
        'finalization': sum(ledger['nested_finalization_phases']),
        'initial_fill': sum(ledger['nested_initialization']['fill_phases']),
        'input_hash': sum(ledger['nested_input_hash_phases']),
        'program_generation': sum(ledger['nested_program_generation_phases'])}
    assert actual == {k: v for k, v in NESTED.items() if k != 'iteration'}
    assert sum(ledger['nested_iteration_phases']) == STAGES['execution'] + delta
    assert ledger['nested_initialization']['provider_wait'] == 0
    digest = baseline['native_reference']['digest32_hex']
    assert re.fullmatch('[0-9a-f]{64}', digest)
    assert profile['actual_digest_sha256'] == hashlib.sha256((digest+'\n').encode()).hexdigest()
    return {'public_baseline': PUBLIC_BASELINE, 'outer_cycle_delta': delta,
        'execution_cycle_delta': delta, 'dataset_reply_wait_delta': delta,
        'other_stage_clocks_equal': True, 'non_dataset_nested_sums_equal': True,
        'native_digest_equal': True, 'nested_costs_added_twice': False}


def selected_fixtures():
    names = ['cases.hex', 'cache-0.bin', 'case-018/seed.hex', 'case-018/stages.mem',
             'case-000/seed.hex', 'case-000/stages.mem']
    names += [f'case-000/{kind}-{i}.mem' for i in range(8)
              for kind in ('program', 'steps', 'rcp-valid', 'rcp-index', 'reciprocals')]
    return names


def pass_record(out, label, prefix):
    lines = (out/(label+'.log')).read_text().splitlines()
    assert not any('FATAL:' in x or x.startswith('FAIL ') for x in lines)
    records = [x for x in lines if x.startswith(prefix)]
    assert len(records) == 1, (label, records)
    return records[0]


def validate_protocol(ledger, rows, record, mode, mapped=False):
    assert ledger['schema'] == 'openrx.dataset-capacity.protocol.v1' and ledger['mode'] == mode
    assert ledger['full_hash_execution'] is False
    fields = dict(re.findall(r'([A-Za-z_][A-Za-z_0-9]*)=([^ ]+)', record))
    assert fields['mode'] == mode and fields['full_hash_execution'] == '0'
    assert ledger['rtl_private_observer'] == (0 if mapped else 1)
    assert (ledger['private_program_accepts'] == -1) if mapped else (ledger['private_program_accepts'] >= 0)
    if mode == 'short':
        expected = {'session_bits': 4, 'items_per_batch': 1, 'retained_case': 18,
            'identity_derivative': 1, 'successes': 9, 'errors': 8, 'cancellations': 4,
            'batch_accepts': 21, 'ds_accepts': 20, 'returns': 17, 'stages': 72,
            'retirements': 20, 'muls': 0, 'native_final_checks': 9,
            'native_instruction_checks': 20, 'held_checks': 28, 'quiescent_resets': 2,
            'stale_packets': 12, 'foreign_topbit_packets': 4, 'private_stale_packets': 4}
        assert ledger['launch_held_edges'] > 0
        if not mapped:
            assert ledger['private_program_accepts'] == 78
    elif mode == 'long':
        expected = {'session_bits': 32, 'items_per_batch': 16384, 'retained_case': 18,
            'identity_derivative': 1, 'successes': 16384, 'errors': 0, 'cancellations': 0,
            'batch_accepts': 1, 'ds_accepts': 16384, 'returns': 16384, 'stages': 131072,
            'retirements': 32768, 'muls': 0, 'native_final_checks': 16384,
            'native_instruction_checks': 32768, 'quiescent_resets': 1, 'held_checks': 8,
            'stale_packets': 24, 'foreign_topbit_packets': 8, 'private_stale_packets': 8,
            'items_over_old8191': 8193, 'programs_over_old65535': 65537,
            'private_program_accepts': 131072, 'session_availability_clocks': 1327128,
            'private_core_clocks': 1310744, 'executor_clocks': 98316}
        assert not mapped
    else:
        assert mode == 'native'
        expected = {'session_bits': 32, 'items_per_batch': 1, 'retained_case': 0,
            'identity_derivative': 0, 'successes': 1, 'errors': 0, 'cancellations': 0,
            'batch_accepts': 1, 'ds_accepts': 1, 'returns': 1, 'stages': 8,
            'retirements': 3563, 'muls': 1254, 'native_final_checks': 1,
            'native_instruction_checks': 3563, 'quiescent_resets': 1, 'held_checks': 4,
            'stale_packets': 0, 'foreign_topbit_packets': 0, 'private_stale_packets': 0,
            'session_availability_clocks': 53400, 'private_core_clocks': 53399,
            'executor_clocks': 53325, 'private_program_accepts': 8}
    for key, value in expected.items():
        assert type(ledger[key]) is int and ledger[key] == value, (mode, key, ledger[key], value)
    for public, key in [('session_bits','session_bits'), ('items_per_batch','items_per_batch'),
        ('successes','successes'), ('errors','errors'), ('cancellations','cancellations'),
        ('stages','stages'), ('retired','retirements'), ('rtl_private_observer','rtl_private_observer'),
        ('private_program_accepts','private_program_accepts'), ('stale_packets','stale_packets'),
        ('total_clocks','total_testbench_clocks')]:
        assert int(fields[public]) == ledger[key], (mode, public)
    assert len(rows) == ledger['returns']
    successful = [row for row in rows if int(row['stages']) == 8]
    assert len(successful) == ledger['successes']
    assert sum(int(row['retired']) for row in rows) == ledger['retirements']
    assert sum(int(row['muls']) for row in rows) == ledger['muls']
    for row in rows:
        assert int(row['namespace']) > 0
        assert int(row['session_cycles']) == int(row['private_core_cycles']) + 1
    for field, column in [('session_availability_clocks','session_cycles'),
        ('private_core_clocks','private_core_cycles'), ('executor_clocks','executor_cycles')]:
        assert ledger[field] == sum(int(row[column]) for row in successful)
    assert ledger['session_availability_clocks'] == ledger['private_core_clocks'] + ledger['successes']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--asset-root', type=Path, required=True)
    p.add_argument('--asset-receipt', type=Path)
    p.add_argument('--asset-receipt-sha256')
    p.add_argument('--asset-root-verify', type=Path)
    p.add_argument('--reuse-root', type=Path, required=True, help='Prior integration OUTPUT containing native-reference/; never modified')
    p.add_argument('--reuse-execution-root', type=Path)
    p.add_argument('--reuse-receipt-sha256')
    p.add_argument('--reuse-manifest-sha256')
    p.add_argument('--reuse-root-verify', type=Path)
    p.add_argument('--reuse-root-verify-sha256')
    p.add_argument('--native-library', type=Path)
    p.add_argument('--native-build-execution', type=Path)
    p.add_argument('--jobs', type=int, default=6, choices=range(1,7))
    p.add_argument('--synthesize', action='store_true', help='Reduced SESSION_BITS=4/N=1 service mapping and short protocol parity only')
    args = p.parse_args()
    out = args.out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents or not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        p.error('fresh unambiguous output outside source required; retain prior attempts')
    if bool(args.native_library) != bool(args.native_build_execution):
        p.error('both native archive reuse arguments required')
    if not args.native_library and os.environ.get('CI') != 'true':
        p.error('outside CI use the retained archive with both native reuse arguments; do not rebuild it')
    private = [args.reuse_execution_root, args.reuse_receipt_sha256, args.reuse_manifest_sha256,
               args.reuse_root_verify, args.reuse_root_verify_sha256]
    if any(private) and not all(private):
        p.error('all five private reference bindings required together')
    asset_private = [args.asset_receipt, args.asset_receipt_sha256, args.asset_root_verify]
    if any(asset_private) and not all(asset_private):
        p.error('all three private prepared-asset bindings required together')
    required = ['python3','g++','cmake','iverilog','iverilog-vpi','vvp'] + (['yosys'] if args.synthesize else [])
    tools = {n: Path(shutil.which(n)).resolve() for n in required if shutil.which(n)}
    if len(tools) != len(required): p.error('native/simulation tool unavailable')
    assert not subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip(), 'freeze source before admitted execution'
    out.mkdir(parents=True)
    supervisor = Supervisor(out); run = supervisor.run
    sources = list(dict.fromkeys([*EXECUTE_RTL, *EXTRA, *SERVICE_RTL, WRAPPER,
        *[str(x.relative_to(ROOT)) for x in sorted((ROOT/'rtl/hash').glob('randomx_*.v'))
          if x.name not in ('randomx_program_hash_sequence.v','randomx_prepared_dataset_hash_lifecycle.v')]]))
    hashes = source_inputs(sources); save(out/'inputs.json', hashes)
    summary = {'schema':'openrx.dataset-capacity.validation.v1','status':'running','base':BASE,
        'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_tree':subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,text=True).strip(),
        'programs':2,'iterations':1,'jobs':args.jobs,'normal_profiles':{},'controls':{},'protocol_profiles':{},'mapping':{'requested':args.synthesize,'status':'pending' if args.synthesize else 'not_requested'},
        'full_hash_execution':False,'native_reference_regenerated':False,'old_component_workloads_repeated':False,
        'scope':'New finite non-recycled item namespace with unchanged accepted core; 16384 items derived from a retained empty-program native case with two identity instructions, plus retained native 2x1 connected profiles, not a full default hash.'}
    try:
        reference_kwargs = {'execution_root':args.reuse_execution_root,
            'receipt_sha':args.reuse_receipt_sha256,'manifest_sha':args.reuse_manifest_sha256,
            'verify_path':args.reuse_root_verify,'verify_sha':args.reuse_root_verify_sha256}
        reused = verify_reference(args.reuse_root/'native-reference',ROOT/REFERENCE_LOCK,ROOT,**reference_kwargs)
        assets = verify_assets(args.asset_root,ROOT/LOCK,ROOT,receipt=args.asset_receipt,
            receipt_sha=args.asset_receipt_sha256,verify=args.asset_root_verify)
        selected = verify_selected_assets(args.asset_root,selected_fixtures(),ROOT)
        save(out/'reference-provenance.json',reused);save(out/'prepared-assets.json',assets);save(out/'selected-fixtures.json',selected)
        summary['reference_provenance']=reused;summary['prepared_assets']=assets;summary['selected_fixtures']=selected
        run('toolchain-identity',['python3','-B','scripts/check_superscalar_toolchain.py','--output',str(out/'toolchain-identity.json')])
        run('identity-and-ledger-unit',['python3','-B','-m','unittest','discover','-s','tests','-p','test_dataset_capacity_*.py','-v'])
        for name,flag in [('g++','--version'),('iverilog','-V'),('vvp','-V')]:
            result=subprocess.run([str(tools[name]),flag],cwd=ROOT,capture_output=True,text=True)
            summary.setdefault('tools',{})[name]={'path':str(tools[name]),'sha256':sha(tools[name]),
                'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
        licenses=[('rtl/dataset/LICENSE','LICENSE-dataset'),('rtl/execute/LICENSE','LICENSE-OpenRX'),
            ('vendor/randomx/LICENSE','LICENSE-RandomX'),('rtl/aes/vendor/secworks/LICENSE','LICENSE-secworks'),
            (V+'LICENSE','LICENSE-HardFloat'),('rtl/hash/vendor/blake2/LICENSE','LICENSE-BLAKE2')]
        if (ROOT/'rtl/dataset_capacity/LICENSE').is_file(): licenses.append(('rtl/dataset_capacity/LICENSE','LICENSE-dataset-capacity'))
        for path,name in licenses:shutil.copyfile(ROOT/path,out/name)
        gold=out/'native-reference';gold.mkdir()
        for name,identity in reused['files'].items():
            shutil.copyfile(args.reuse_root/'native-reference'/name,gold/name)
            assert {'bytes':(gold/name).stat().st_size,'sha256':sha(gold/name)}==identity
        # These four packing operations are idempotent assertion-only views.
        # Every one of the 19 retained bytestring identities must remain exact.
        summary['native_reference']=prepare_assertions(gold)
        assert {x.name for x in gold.iterdir()}==set(reused['files'])
        assert all(sha(gold/name)==row['sha256'] for name,row in reused['files'].items())
        save(out/'native-reference-files.json',reused['files'])
        native=load(gold/'oracle-summary.json')
        item_rows=[x.split() for x in (gold/'dataset-items.hex').read_text().splitlines()]
        assert len(item_rows)==2 and all(len(x)==2 for x in item_rows)
        summary['native_dataset_items']=[{'address_hex':a,'item_hex':b} for a,b in item_rows]
        compat=compile_view(ROOT/V/'divSqrtRecFN_small.v',out)
        sources=[str(compat) if n==V+'divSqrtRecFN_small.v' else n for n in sources]
        extract(out)
        virtual=(ROOT/'vendor/randomx/src/virtual_machine.cpp').read_text();notice=virtual[:virtual.index('*/')+2]+'\n'
        bodies={'pinned_program_initialize.inc':function(virtual,'void randomx_vm::initialize()',True),
            'pinned_program_float_helpers.inc':'namespace randomx {\n'+'\n'.join(function(virtual,n) for n in
                ['static inline uint64_t getSmallPositiveFloatBits(','static inline uint64_t getStaticExponent(',
                 'static inline uint64_t getFloatMask('])+'\n}\n'}
        for name,body in bodies.items():(out/name).write_text(notice+body)
        save(out/'program-extraction.json',{'source_sha256':sha(ROOT/'vendor/randomx/src/virtual_machine.cpp'),
            'generated':{name:sha(out/name) for name in bodies}})
        if args.native_library:
            library=args.native_library.resolve();summary['native_library']=provenance_library(library,args.native_build_execution.resolve())
            summary['native_library']['fresh_pinned_build']=False
        else:
            build=out/'native-library'
            run('configure-native-library',['cmake','-S','vendor/randomx','-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DARCH=default','-DCMAKE_POSITION_INDEPENDENT_CODE=ON'])
            run('build-native-library',['cmake','--build',str(build),'--parallel',str(args.jobs)])
            library=build/'librandomx.a';summary['native_library']={'fresh_pinned_build':True,'ARCH':'default','sha256':sha(library),
                'scope':'Routine unchanged native library compile for callbacks only; no native reference/cache generation campaign.'}
        cflags=[x for x in subprocess.check_output(['iverilog-vpi','--cflags'],text=True).split() if x.startswith('-I')];assert cflags
        run('compile-vpi',['g++','-std=c++17','-O2','-Wall','-Wextra','-fPIC','-shared',*cflags,
            '-I'+str(out),'-Ivendor/randomx/src','-Irtl/execute/tests','-I'+TEST,
            TEST+'dataset_capacity_source_vpi.cpp',str(library),'-pthread','-ldl','-o',str(out/'dataset_capacity_source.vpi')])
        env=dict(os.environ,RX_PREPARED_CACHE_ROOT=str(args.asset_root.resolve()));env.pop('RX_PREPARED_REFERENCE_OUTPUT',None)
        includes=['-Irtl/execute','-I'+V,'-I'+V+'8086-SSE','-Irtl/hash/vendor/blake2','-I'+str(gold)]
        # Elaboration proves namespace capacity only; this is not 8x2048 execution.
        top='randomx_prepared_dataset_capacity_hash_lifecycle'
        for label,parameters in [('elaborate-legacy-default',{}),('elaborate-full-hardware-capacity',{'HARDWARE_DATASET':1})]:
            run(label,['iverilog','-g2012',*includes,'-s',top,*['-P'+top+'.'+k+'='+str(v) for k,v in parameters.items()],
                '-o',str(out/(label+'.vvp')),*sources])
        service='randomx_dataset_capacity_service'
        invalid=[('reject-batch-65536',{'ITEMS_PER_BATCH':65536},'dataset_service_requires_batch_1_to_min_65535_SESSION_MAX'),
            ('reject-session-0',{'SESSION_BITS':0},'dataset_service_requires_SESSION_BITS_1_to_32'),
            ('reject-session-33',{'SESSION_BITS':33},'dataset_service_requires_SESSION_BITS_1_to_32'),
            ('reject-batch-over-session',{'ITEMS_PER_BATCH':16,'SESSION_BITS':4},'dataset_service_requires_batch_1_to_min_65535_SESSION_MAX')]
        for label,parameters,diagnostic in invalid:
            run(label,['iverilog','-g2012','-s',service,*['-P'+service+'.'+k+'='+str(v) for k,v in parameters.items()],
                '-o',str(out/(label+'.vvp')),*SERVICE_RTL],expected_returncodes=(1,2,3,4))
            assert diagnostic in (out/(label+'.log')).read_text()
        summary['elaboration']={'legacy_default':'pass','hardware_8x2048':'pass_elaboration_only','invalid_parameter_rejections':[x[0] for x in invalid]}

        capture_label='capacity-capture-RTL';capture_directory=out/capture_label;capture_directory.mkdir()
        run('compile-'+capture_label,['iverilog','-g2012','-Wall','-s','tb_dataset_capacity_capture',
            '-o',str(out/(capture_label+'.vvp')),*SERVICE_RTL,UNIT_BENCH])
        run(capture_label,['vvp',str(out/(capture_label+'.vvp')),'+output='+str(capture_directory)])
        capture_pass=pass_record(out,capture_label,'PASS dataset_capacity_capture ')
        capture=load(capture_directory/'capture-ledger.json')
        assert capture=={'schema':'openrx.dataset-capacity.capture.v1','actual_child_public_captures':4,
            'caller_poisoned_before_launch':4,'fields_checked_each_capture':6,'first_last_count_and_address_errors':4,
            'total_testbench_clocks':21,'rtl_only_passive_observer':True,'native_workloads_repeated':False}
        assert capture_pass=='PASS dataset_capacity_capture actual_child_public_captures=4 caller_poisoned_before_launch=4 first_last_count_and_address_errors=4 total_clocks=21 rtl_only_passive_observer=1'
        summary['descriptor_capture']={'PASS':capture_pass,'ledger':capture}

        def unit(label,mode,session_bits,items,netlist=None,cells=None):
            binary=out/(label+'.vvp');directory=out/label;directory.mkdir()
            selected_sources=[str(netlist),str(cells)] if netlist else SERVICE_RTL
            definitions=['-DDATASET_CAPACITY_NETLIST'] if netlist else []
            run('compile-'+label,['iverilog','-g2012','-Wall','-s','tb_dataset_capacity',*definitions,
                '-Ptb_dataset_capacity.SESSION_BITS='+str(session_bits),'-Ptb_dataset_capacity.ITEMS_PER_BATCH='+str(items),
                '-o',str(binary),*selected_sources,UNIT_BENCH])
            run(label,['vvp',str(binary),'+asset_root='+str(args.asset_root.resolve()),'+output='+str(directory),'+MODE='+mode,'+CASE=0'])
            record=pass_record(out,label,'PASS dataset_capacity ')
            ledger=load(directory/'capacity-ledger.json')
            with (directory/'items.csv').open(newline='') as f:rows=list(csv.DictReader(f))
            validate_protocol(ledger,rows,record,mode,mapped=netlist is not None)
            return {'PASS':record,'ledger':ledger,'item_rows_sha256':sha(directory/'items.csv')}

        unit_specs=[('capacity-native-0-RTL','native',32,1),('capacity-long-RTL','long',32,16384),('capacity-short-RTL','short',4,1)]
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures=[(x[0],pool.submit(unit,*x)) for x in unit_specs];errors=[]
            for label,future in futures:
                try:summary['protocol_profiles'][label]=future.result()
                except BaseException as error:errors.append({'label':label,'error':repr(error)})
            if errors:summary['protocol_failures']=errors;raise RuntimeError('Protocol failures after all joined: '+repr(errors))
        if args.synthesize:
            netlist=out/'netlist-dataset-capacity.v'
            script='read_verilog '+' '.join(SERVICE_RTL)+'; '
            script+='chparam -set ITEMS_PER_BATCH 1 -set SESSION_BITS 4 randomx_dataset_capacity_service; synth -top randomx_dataset_capacity_service -flatten; check -assert; '
            script+=f'tee -o {out}/stat-dataset-capacity.txt stat; write_verilog -noattr {netlist}; write_json {out}/netlist-dataset-capacity.json'
            run('synth-dataset-capacity',['yosys','-p',script],timeout=3600)
            module=load(out/'netlist-dataset-capacity.json')['modules']['randomx_dataset_capacity_service']
            kinds=Counter(x['type'] for x in module['cells'].values())
            summary['mapping']={'requested':True,'status':'pending_short_protocol','top':'randomx_dataset_capacity_service','ITEMS_PER_BATCH':1,'SESSION_BITS':4,'MUL_RADIX4':1,
                'cells':sum(kinds.values()),'DFF':sum(n for k,n in kinds.items() if 'DFF' in k),
                'latches':sum(n for k,n in kinds.items() if 'LATCH' in k),'cell_types':dict(sorted(kinds.items())),
                'scope':'Reduced namespace service plus all accepted child arithmetic, short protocol matrix only; not full lifecycle mapping or physical PPA.'}
            assert summary['mapping']['latches']==0
            cells=out/'yosys-simcells.v';shutil.copyfile('/usr/share/yosys/simcells.v',cells)
            save(out/'yosys-cell-model.json',{'installed':'/usr/share/yosys/simcells.v','sha256':sha(cells)})
            mapped=unit('capacity-short-mapped','short',4,1,netlist,cells)
            rtl=summary['protocol_profiles']['capacity-short-RTL']
            omit={'rtl_private_observer','private_program_accepts'}
            assert {k:v for k,v in mapped['ledger'].items() if k not in omit}=={k:v for k,v in rtl['ledger'].items() if k not in omit}
            assert mapped['item_rows_sha256']==rtl['item_rows_sha256']
            summary['protocol_profiles']['capacity-short-mapped']=mapped
            summary['mapping']['status']='pass_short_protocol_parity'

        reference_lock=load(ROOT/REFERENCE_LOCK);message=bytes.fromhex(reference_lock['profile']['input_hex'])
        def profile(name,stalled=0,cancellation=0,error=0):
            parameters={'PROGRAMS':2,'ITERATIONS':1,'PREPARED_RCP':1,'HARDWARE_FILL':1,'HARDWARE_PROGRAM':1,
                'HARDWARE_INPUT_HASH':1,'HARDWARE_DATASET':1,'DATASET_SESSION_BITS':32,'EVENT_TRACE':1,
                'STALL':stalled,'DATASET_CANCEL':cancellation,'DATASET_ERROR':error}
            binary=out/(name+'.vvp');directory=out/name;directory.mkdir()
            run('compile-'+name,['iverilog','-g2012','-Wall',*includes,'-s','tb_dataset_capacity_hash_lifecycle',
                *['-Ptb_dataset_capacity_hash_lifecycle.'+k+'='+str(v) for k,v in parameters.items()],'-o',str(binary),*sources,BENCH])
            run(name,['vvp','-M'+str(out),'-mdataset_capacity_source',str(binary),'+directory='+str(gold),
                '+output='+str(directory),'+asset_root='+str(args.asset_root.resolve()),
                '+input='+format(int.from_bytes(message,'little'),'x'),'+input_bytes='+str(len(message))],env=env)
            provider=load(directory/'provider-host-time.json')
            for key in ['input_hash_calls','software_fill_provider_calls','program_generations','dataset_requests',
                        'argon_initializations','native_cache_program_generations','cache_image_export_bytes']:
                assert provider[key]==0
            if cancellation or error:
                prefix='PASS dataset_capacity_lifecycle_cancel ' if cancellation else 'PASS dataset_capacity_lifecycle_error '
                record=pass_record(out,name,prefix)
                assert 'prefix_only=1' in record and 'changed_generation=1' in record and 'changed_input=1' in record
                return {'parameters':parameters,'PASS':record,'provider':provider,'scope':'Recovery prefix, not another completed hash.'}
            record=pass_record(out,name,'PASS dataset_capacity_hash_lifecycle ')
            native_record=pass_record(out,name,'PASS prepared_hash_lifecycle ')
            ledger=load(directory/'ledger.json');dataset=load(directory/'dataset-ledger.json')
            validate_outer(ledger,provider,native,True)
            assert provider['assertion_only_dataset_requests']==0
            with (directory/'dataset-items-ledger.csv').open(newline='') as f:rows=list(csv.DictReader(f))
            validate_dataset(dataset,ledger,rows,item_rows,stalled)
            assert (directory/'actual-final-digest32.hex').read_bytes()==(gold/'final-digest32.hex').read_bytes()
            return {'parameters':parameters,'PASS':[record,native_record],'provider':provider,'ledger':ledger,'dataset':dataset,
                'dataset_rows':rows,'actual_digest_sha256':sha(directory/'actual-final-digest32.hex')}
        specs=[('hardware-dataset-ideal',0,0,0),('hardware-dataset-stalled',1,0,0)]
        specs += [('hardware-cancel-'+str(i),1,i,0) for i in (1,2,3)]
        specs += [('hardware-error-'+str(i),1,0,i) for i in (1,2)]
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures=[(s[0],pool.submit(profile,*s)) for s in specs];errors=[]
            for name,future in futures:
                try:
                    result=future.result();summary['controls' if result['parameters']['DATASET_CANCEL'] or result['parameters']['DATASET_ERROR'] else 'normal_profiles'][name]=result
                except BaseException as error:errors.append({'profile':name,'error':repr(error)})
            if errors:summary['profile_failures']=errors;raise RuntimeError('Connected failures after all joined: '+repr(errors))
        assert len(summary['normal_profiles'])==2 and len(summary['controls'])==5
        summary['paired_ideal_clock_closure']=compare_ideal_profiles(summary['normal_profiles']['hardware-dataset-ideal'])
        assert all(sha(ROOT/n)==row['sha256'] for n,row in hashes.items())
        assert all(sha(gold/n)==row['sha256'] for n,row in reused['files'].items())
        verify_reference(args.reuse_root/'native-reference',ROOT/REFERENCE_LOCK,ROOT,**reference_kwargs)
        verify_assets(args.asset_root,ROOT/LOCK,ROOT,receipt=args.asset_receipt,receipt_sha=args.asset_receipt_sha256,verify=args.asset_root_verify)
        verify_selected_assets(args.asset_root,selected_fixtures(),ROOT)
        assert sha(library)==summary['native_library']['sha256']
        summary['source_reference_and_prepared_assets_unchanged_after_run']=True
        summary['remaining_host_services']=['Retained Argon/cache initialization, cache export and superscalar/global reciprocal preparation',
            'Tagged immutable cache/program/table responses and external scratchpad model',
            'Separately counted native assertion callbacks and retained bounded native reference',
            'Full8x2048 execution, physical memory service, calibrated performance/PPA and architecture selection remain unproven']
        summary['status']='pass_bounded_dataset_capacity'
        print('PASS dataset_capacity_suite programs=2 iterations=1 normal_profiles=2 recovery_profiles=5 native_gold_regenerated=0 full_hash_execution=0',flush=True)
    except BaseException as error:
        summary['status']='failed';summary['error']=repr(error);raise
    finally:
        save(out/'summary.json',summary)
        save(out/'artifacts.sha256.json',{str(x.relative_to(out)):sha(x) for x in sorted(out.rglob('*'))
            if x.is_file() and x.name!='artifacts.sha256.json'})


if __name__=='__main__':main()
