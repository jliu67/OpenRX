#!/usr/bin/env python3
"""Admitted, bounded native dataset-item differential and optional mapped checks.

Run only inside the caller's admitted global execution slot. Default performs
native fixture generation and RTL correctness first. --synthesize adds mapping
after correctness; --synthesize-only reuses an independently verified prior run
through exact receipt bindings and performs no native/correctness regeneration.
Two actual 256 MiB native caches are prepared once per key and exported.
No 2 GiB dataset allocation, whole-hash or physical performance claim.
"""
import argparse
import ctypes
import os
import signal
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]
TOP = 'randomx_dataset_item'
BENCH_TOP = 'tb_dataset_item'
RTL = ['rtl/execute/randomx_mul64.v', 'rtl/execute/randomx_superscalar_execute.v',
       'rtl/dataset/' + TOP + '.v']
BENCH = 'rtl/dataset/tests/' + BENCH_TOP + '.v'
ORACLE = 'rtl/dataset/tests/dataset_item_oracle.cpp'
DRIVER = 'scripts/test_dataset_item.py'
PIN = 'aaafe71322df6602c21a5c72937ac284724ae561'
PIN_MANIFEST = '2763c092b465bb99d71d544915b9fd847064ec195cc438c6370c34ecdf9b746d'
PIN_LOCK = '2c210a233afaedd668463647d25da27f9ffdb7235e53248f91c6f78c7943e3cd'
RETAINED_LIBRARY_SHA = 'bddb3f9a206b1ec34ca78d3a9b13a9388d7312d6660b7d148d4ed514958fb8d6'
NAMES = ['ISUB_R', 'IXOR_R', 'IADD_RS', 'IMUL_R', 'IROR_C', 'IADD_C7',
         'IXOR_C7', 'IADD_C8', 'IXOR_C8', 'IADD_C9', 'IXOR_C9', 'IMULH_R',
         'ISMULH_R', 'IMUL_RCP']
REG_SOURCE = {0, 1, 2, 3, 11, 12}
MULTIPLY = {3, 11, 12, 13}
CONTROLS = ['stalled', 'held', 'malformed', 'stale', 'cancel', 'reset']
RTL_PROFILES = {'rtl-corpus': ('corpus', 'cases.hex'),
                'rtl-mapped-corpus': ('corpus', 'cases-mapped.hex'),
                **{'rtl-'+mode: (mode, 'cases-mapped.hex' if mode == 'stalled' else 'cases-control.hex')
                   for mode in CONTROLS},
                'rtl-exhaustion': ('exhaustion', 'cases-empty.hex'),
                'rtl-outer-exhaustion': ('outer-exhaustion', 'cases-control.hex'),
                'rtl-radix0-corpus': ('corpus', 'cases-mapped.hex'),
                'rtl-radix0-stalled': ('stalled', 'cases-mapped.hex')}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def process_group(pgid):
    """Snapshot only this newly created session/group; tolerate exit races."""
    members = []
    ticks = os.sysconf('SC_CLK_TCK')
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            raw = (directory / 'stat').read_text()
            close = raw.rindex(')')
            fields = raw[close + 2:].split()
            if int(fields[2]) != pgid or int(fields[3]) != pgid:
                continue
            status = (directory / 'status').read_text()
            memory = {name: int(value) for name, value in re.findall(r'^(VmRSS|VmHWM):\s*(\d+) kB$', status, re.M)}
            members.append({'pid': int(directory.name), 'ppid': int(fields[1]),
                'process_group': int(fields[2]), 'session': int(fields[3]), 'state': fields[0],
                'comm': raw[raw.index('(') + 1:close], 'start_ticks': int(fields[19]),
                'user_ticks': int(fields[11]), 'system_ticks': int(fields[12]),
                'user_seconds': int(fields[11]) / ticks, 'system_seconds': int(fields[12]) / ticks,
                'threads': int(fields[17]), 'memory_kib': memory,
                'cmdline': (directory / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')})
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
            continue
    return sorted(members, key=lambda row: row['pid'])


def provenance_library(library, execution):
    """Actual retained archive/build/source bindings, without rebuilding it."""
    receipt, manifest = load(execution / 'receipt.json'), load(execution / 'manifest.json')
    assert receipt['process']['returncode'] == 0
    artifacts = {Path(row['path']): row for row in receipt['artifacts']}

    def bound(path):
        row = artifacts[path]
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']

    bound(library)
    assert sha(library) == RETAINED_LIBRARY_SHA, 'different archive; use pinned source fallback instead'
    bound(execution / 'manifest.json')
    native = [row for source in manifest['sources'] for row in source['files']
              if row['relative'].startswith('vendor/randomx/')]
    assert native and all(sha(ROOT / row['relative']) == row['sha256'] for row in native)
    build = library.parent.parent / 'build.json'
    flags = library.parent / 'CMakeFiles/randomx.dir/flags.make'
    bound(build)
    bound(flags)
    data = load(build)
    assert data['status'] == 'built' and data['artifacts']['randomx/librandomx.a'] == sha(library)
    return {'library': str(library), 'sha256': sha(library), 'native_source_files_verified': len(native),
            'execution': str(execution), 'manifest_sha256': sha(execution / 'manifest.json'),
            'receipt_sha256': sha(execution / 'receipt.json'), 'build_sha256': sha(build),
            'flags_sha256': sha(flags), 'archive_rebuilt_or_modified': False}


def corpus(fixtures):
    """Validate actual fixture representation; all arithmetic gold is native C++."""
    tables, prepared, originals = {}, {}, {}
    for cache in range(2):
        image = fixtures / f'cache-{cache}.bin'
        assert image.stat().st_size == 268435456 and not image.is_symlink()
        meta = load(fixtures / f'cache-{cache}-metadata.json')
        assert meta['cache_id'] == cache and meta['cache_bytes'] == 268435456
        assert meta['cache_lines'] == 4194304 and meta['native_flags'] == 0
        assert meta['argon_initializations'] == 1 and meta['prepared_programs'] == 8
        assert meta['prepared_replay_identity_checked'] is True
        expected_key = b'test key 000' if cache == 0 else bytes(range(32))
        assert bytes.fromhex(meta['key_hex']) == expected_key and meta['key_bytes'] == len(expected_key)
        tables[cache] = [int(x, 16) for x in (fixtures / f'cache-{cache}-reciprocals.mem').read_text().splitlines()]
        assert len(tables[cache]) == meta['reciprocal_count']
        reciprocal = load(fixtures / f'cache-{cache}-reciprocal-metadata.json')
        assert reciprocal['global_indices'] and reciprocal['deduplicated'] is False
        assert [row['index'] for row in reciprocal['entries']] == list(range(len(tables[cache])))
        assert [int(row['value_hex'], 16) for row in reciprocal['entries']] == tables[cache]
        prepared[cache] = [int(x, 16) for x in (fixtures / f'cache-{cache}-prepared-programs.mem').read_text().splitlines()]
        originals[cache] = [int(x, 16) for x in (fixtures / f'cache-{cache}-original-programs.mem').read_text().splitlines()]
        assert len(prepared[cache]) == len(originals[cache]) == 4096
        for raw, original in zip(prepared[cache], originals[cache]):
            if raw & 255 == 13:
                entry = reciprocal['entries'][raw >> 32]
                assert original >> 32 == entry['divisor'] and raw & 0xffffffff == original & 0xffffffff
            else:
                assert raw == original
    cases, opcounts, post_xor_differences = {}, Counter(), 0
    expected_items = [0, 10000000, 20000000, 30000000, 0x3fffff, 0x400000, 0x207fffe, (1 << 64)-1,
                      0, 1, 2, 0x400001, 0xffffffff, 0x100000000, (1 << 64)-2, 1 << 63,
                      1, (1 << 64)-2, 0, 2]
    for line in (fixtures / 'cases.hex').read_text().splitlines():
        ident, cache, item, table_count, packed_counts, packed_addresses, final = line.split()
        ident, cache = int(ident), int(cache)
        item, table_count, packed_counts, packed_addresses = [int(x, 16) for x in (item, table_count, packed_counts, packed_addresses)]
        assert ident not in cases and 0 <= ident < 20 and cache == (0 if ident < 8 or ident in [16, 18] else 1)
        assert item == expected_items[ident] and table_count == len(tables[cache])
        assert packed_counts < 1 << 80 and packed_addresses < 1 << 64 and len(final) == 128
        counts = [(packed_counts >> (10*i)) & 1023 for i in range(8)]
        addresses = [(packed_addresses >> (8*i)) & 255 for i in range(8)]
        assert all(n <= 512 for n in counts) and all(a < 8 for a in addresses)
        directory = fixtures / f'case-{ident:03d}'
        meta = load(directory / 'metadata.json')
        assert meta['case_id'] == ident and meta['cache_id'] == cache and int(meta['item_hex'], 16) == item
        assert meta['native_generated_programs'] == (ident < 16)
        assert meta['full_native_final_agrees'] and meta['singleton_full_stage_agrees']
        initial = (directory / 'seed.hex').read_text().strip()
        assert len(initial) == 128 and (directory / 'final.hex').read_text().strip() == final
        stages = [row.split() for row in (directory / 'stages.mem').read_text().splitlines()]
        assert len(stages) == 8 and all(len(row) == 6 for row in stages)
        before, selected, muls = int(initial, 16), item, 0
        with (fixtures / f'cache-{cache}.bin').open('rb') as image:
            for stage, row in enumerate(stages):
                index, cache_line, pre, post, mixed, next_selected = [int(x, 16) for x in row]
                assert index == selected & 0x3fffff and pre == before
                image.seek(index * 64)
                actual_line = image.read(64)
                assert len(actual_line) == 64 and int.from_bytes(actual_line, 'little') == cache_line
                assert post ^ cache_line == mixed
                assert next_selected == (mixed >> (64 * addresses[stage])) & ((1 << 64)-1)
                post_xor_differences += ((post >> (64 * addresses[stage])) & 0x3fffff) != (next_selected & 0x3fffff)
                rows = {name: (directory / f'{name}-{stage}.mem').read_text().splitlines()
                        for name in ['program', 'steps', 'rcp-valid', 'rcp-index', 'reciprocals']}
                assert all(len(values) == 512 for values in rows.values())
                after = pre
                for pc in range(512):
                    raw, state, valid, index_rcp, value = [int(rows[name][pc], 16)
                        for name in ['program', 'steps', 'rcp-valid', 'rcp-index', 'reciprocals']]
                    assert len(rows['program'][pc]) == 16 and len(rows['steps'][pc]) == 128
                    if pc >= counts[stage]:
                        assert raw == state == valid == index_rcp == value == 0
                        continue
                    op, dst, src, imm = raw & 255, raw >> 8 & 255, raw >> 16 & 255, raw >> 32
                    assert op < 14 and dst < 8 and (op not in REG_SOURCE or src < 8)
                    assert op != 4 or imm <= 63
                    assert valid == (op == 13)
                    if valid:
                        assert index_rcp == imm < table_count and value == tables[cache][imm]
                    else:
                        assert index_rcp == value == 0
                    if ident < 16:
                        assert raw == prepared[cache][stage*512+pc]
                    opcounts[NAMES[op]] += 1
                    muls += op in MULTIPLY
                    after = state
                assert after == post
                before, selected = mixed, next_selected
        assert before == int(final, 16)
        assert meta['retired'] == sum(counts) and meta['muls'] == muls
        cases[ident] = {'cache': cache, 'item_hex': f'{item:016x}', 'counts': counts, 'address_regs': addresses,
                        'retired': sum(counts), 'muls': muls, 'kind': meta['kind'], 'final': final}
    assert set(cases) == set(range(20)) and set(opcounts) == set(NAMES)
    assert cases[19]['retired'] == cases[19]['muls'] == 4096
    assert cases[18]['retired'] == 0 and cases[16]['retired'] == cases[17]['retired'] == 24
    for ident in [16, 17]:
        assert int((fixtures / f'case-{ident:03d}/program-0.mem').read_text().splitlines()[0], 16) & 255 == 3
    selections = {}
    all_lines = (fixtures / 'cases.hex').read_text().splitlines()
    for name, expected in [('cases.hex', set(range(20))), ('cases-real.hex', set(range(16))),
                           ('cases-control.hex', {16, 17}), ('cases-empty.hex', {18}),
                           ('cases-mapped.hex', {0, 8, 16, 17, 18})]:
        lines = (fixtures / name).read_text().splitlines()
        ids = [int(line.split()[0]) for line in lines]
        assert len(ids) == len(set(ids)) and set(ids) == expected and all(line in all_lines for line in lines)
        selections[name] = ids
    native = load(fixtures / 'native-summary.json')
    expected = {'cases': 20, 'native_generated_cases': 16, 'crafted_control_cases': 2, 'crafted_empty_cases': 1,
                'crafted_maximum_cases': 1, 'mapped_cases': 5, 'cache_images': 2, 'cache_image_bytes': 268435456,
                'argon_initializations': 2, 'dataset_allocation_bytes': 0, 'full_native_item_calls': 20,
                'stages': 160, 'max_aggregate_retired': 4096, 'max_aggregate_muls': 4096,
                'upstream_first_word_anchors': 4, 'item_bits': 64}
    assert all(native[key] == value for key, value in expected.items())
    assert native['pin'] == PIN and native['status'] == 'pass'
    assert native['post_instruction_states'] == sum(row['retired'] for row in cases.values())
    assert native['post_xor_address_differences'] == post_xor_differences > 0
    assert native['little_endian'] and native['full_native_final_agrees'] and native['singleton_full_stage_agrees']
    return native, cases, selections, {**expected, 'native_retirements': sum(row['retired'] for row in cases.values()),
        'opcounts': dict(opcounts), 'post_xor_address_differences': post_xor_differences,
        'mapped_case_ids': selections['cases-mapped.hex'], 'rtl_only_aggregate_width_case': 19,
        'actual_cache_bytes_checked_by_requested_index': True,
        'oracle': 'Unchanged pinned initDatasetItem final and executeSuperscalar instruction states; no Python instruction arithmetic golden.'}


def reused_fixtures(args, fixtures, inputs):
    receipt_path = args.validated_receipt.resolve()
    assert sha(receipt_path) == args.validated_receipt_sha256
    receipt, verify = load(receipt_path), load(args.validated_verify.resolve())
    assert receipt['process']['returncode'] == 0 and receipt['status'] == 'PROCESS_EXITED'
    assert verify['integrity_verified'] and verify['status'] == 'PROCESS_EXITED'
    assert verify['execution_id'] == receipt['execution_id']
    artifacts = {Path(row['path']): row for row in receipt['artifacts']}

    def bound(path):
        row = artifacts[path]
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']

    prior = args.validated_out.resolve()
    manifest_path = receipt_path.parent / 'manifest.json'
    bound(manifest_path)
    manifest = load(manifest_path)
    assert manifest['execution_id'] == receipt['execution_id']
    source_rows = [row for source in manifest['sources'] for row in source['files']]
    # These are the runner's actual consumed-source bindings, anchored in the
    # supplied receipt. inputs.json is only a consistency report, not authority.
    for relative, digest in inputs.items():
        matches = [row for row in source_rows if row['relative'] == relative]
        assert len(matches) == 1
        actual = ROOT / relative
        assert matches[0]['sha256'] == digest == sha(actual)
        assert matches[0]['bytes'] == actual.stat().st_size
    for name in ['summary.json', 'inputs.json', 'fixtures.sha256.json', 'coverage.json',
                 'native-cache-host-timing.json', 'commands.json', 'tools.json']:
        bound(prior / name)
    summary = load(prior / 'summary.json')
    assert summary['status'] in ['pass_correctness', 'pass'] and summary['correctness_completed']
    assert set(summary['rtl']) == set(RTL_PROFILES)
    assert summary['source_unchanged_after_run'] and summary['fixtures_unchanged_after_run']
    prior_commands, prior_tools = load(prior / 'commands.json'), load(prior / 'tools.json')
    for label, (mode, selection) in RTL_PROFILES.items():
        bound(prior / (label + '.log'))
        bound(prior / (label + '-latencies.hex'))
        runs = [row for row in prior_commands if row['label'] == label]
        assert len(runs) == 1
        run = runs[0]
        executable = prior / ('rtl-radix0.vvp' if label.startswith('rtl-radix0-') else 'rtl.vvp')
        bound(executable)
        expected_argv = [prior_tools['vvp']['path'], str(executable), '+DIR='+str(prior / 'fixtures'),
                         '+CASES='+selection, '+MODE='+mode, '+RESULTS='+str(prior / (label+'-latencies.hex'))]
        assert run['argv'] == expected_argv and run['returncode'] == 0
        assert run['wall_timeout'] is False and run['group_empty_after_cleanup'] is True and 'error' not in run
        assert summary['rtl'][label]['mode'] == mode and summary['rtl'][label]['selection'] == selection
        lines = (prior / (label+'.log')).read_text().splitlines()
        assert [line for line in lines if line.startswith('PASS ')] == [summary['rtl'][label]['record']]
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines)
    assert load(prior / 'inputs.json') == inputs
    hashes = load(prior / 'fixtures.sha256.json')
    actual = {str(path.relative_to(prior / 'fixtures')): sha(path)
              for path in sorted((prior / 'fixtures').rglob('*')) if path.is_file()}
    assert actual == hashes
    for relative in hashes:
        bound(prior / 'fixtures' / relative)
    shutil.copytree(prior / 'fixtures', fixtures)
    shutil.copyfile(prior / 'native-cache-host-timing.json', fixtures.parent / 'prior-native-cache-host-timing.json')
    assert {str(path.relative_to(fixtures)): sha(path) for path in sorted(fixtures.rglob('*')) if path.is_file()} == hashes
    return summary, {'prior_output': str(prior), 'receipt_sha256': sha(receipt_path),
        'root_verify_sha256': sha(args.validated_verify.resolve()), 'fixture_files_receipt_verified': len(hashes),
        'actual_prior_summary_sha256': sha(prior / 'summary.json'), 'source_inputs_byte_equal': True,
        'actual_runner_source_manifest_sha256': sha(manifest_path), 'actual_runner_source_files_verified': len(inputs),
        'prior_rtl_raw_logs_and_latencies_receipt_verified': len(RTL_PROFILES),
        'native_or_completed_rtl_regenerated': False,
        'host_timing_artifact_is_prior_measurement': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', '--output', dest='out', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    parser.add_argument('--synthesize-only', action='store_true')
    parser.add_argument('--validated-out', type=Path)
    parser.add_argument('--validated-receipt', type=Path)
    parser.add_argument('--validated-receipt-sha256')
    parser.add_argument('--validated-verify', type=Path)
    parser.add_argument('--native-library', type=Path)
    parser.add_argument('--native-build-execution', type=Path)
    parser.add_argument('--jobs', type=int, default=6, help='independent simulator processes within one admitted payload (1..6)')
    args = parser.parse_args()
    if not 1 <= args.jobs <= 6:
        parser.error('--jobs must be1..6')
    reuse = [args.validated_out, args.validated_receipt, args.validated_receipt_sha256, args.validated_verify]
    if args.synthesize_only != all(bool(x) for x in reuse) or (any(reuse) and not all(reuse)):
        parser.error('--synthesize-only requires all four --validated-* bindings; they apply only to reuse')
    if args.synthesize and args.synthesize_only:
        parser.error('choose full --synthesize or reuse --synthesize-only')
    if bool(args.native_library) != bool(args.native_build_execution) or (args.synthesize_only and args.native_library):
        parser.error('both native reuse flags are required together and only for correctness')
    out = args.out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents or not re.fullmatch(r'[-A-Za-z0-9_./]+', str(out)):
        parser.error('fresh unambiguous output path outside source required; preserve all previous attempts')
    for preserved in [args.validated_out, args.native_build_execution]:
        if preserved and (out == preserved.resolve() or preserved.resolve() in out.parents):
            parser.error('output must not be inside a preserved execution or output directory')
    needed = ['iverilog', 'vvp'] + ([] if args.synthesize_only else ['g++'] + ([] if args.native_library else ['cmake']))
    if args.synthesize or args.synthesize_only:
        needed += ['yosys']
    tools = {name: Path(shutil.which(name)).resolve() for name in needed if shutil.which(name)}
    if len(tools) != len(needed):
        parser.error('required compiler/simulator/resource tool unavailable')
    out.mkdir(parents=True)
    commands, records = [], {}
    command_lock, record_lock = Lock(), Lock()
    summary = {'status': 'running', 'correctness_completed': False, 'rtl': {}, 'mapped': {}, 'mapping': {},
        'mode_parallelism': args.jobs, 'parallelism_scope': 'Independent simulations only; immutable fixtures and separate logs/results. Native compilation/generation and synthesis are sequential phases.',
        'scope': 'Eight prepared native superscalar programs plus dataset-item seed/cache XOR recurrence. '
                 'Host Argon/cache/program/reciprocal preparation remains external. Two real 256 MiB cache images; '
                 'no 2 GiB dataset allocation, full-hash performance, physical PPA or architecture selection.'}


    def persist_commands():
        with command_lock:
            temporary = out / 'commands.json.tmp'
            save(temporary, commands)
            temporary.replace(out / 'commands.json')

    def run(label, argv, timeout=1800):
        """Supervise fixed tools in original PGID/SID, retaining leader until signals end.

        No escaped-process-group/session guarantee: the admitted runner cgroup
        remains the outer containment. Resource samples are actual observations,
        not an unsampled true peak or complete accounting of short-lived children.
        """
        row = {'label': label, 'argv': [str(x) for x in argv], 'cwd': str(ROOT),
               'timeout_seconds': timeout, 'cleanup_scope': 'Original fixed-tool PGID/SID; runner cgroup is outer containment.'}
        with command_lock:
            row_index = len(commands)
            # Workers mutate their private row until completion. Shared rows
            # change only under this lock, so concurrent JSON saves are safe.
            commands.append(dict(row))
        persist_commands()
        print('START ' + label, flush=True)
        began, timed_out, samples = time.monotonic(), False, []
        try:
            with (out / (label + '.log')).open('w') as log, (out / (label + '-process-samples.jsonl')).open('w') as observations:
                child = subprocess.Popen(row['argv'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    row['process_group'] = child.pid
                    while True:
                        members = process_group(child.pid)
                        sample = {'elapsed_seconds': time.monotonic()-began, 'members': members}
                        samples.append(sample)
                        observations.write(json.dumps(sample, sort_keys=True)+'\n')
                        observations.flush()
                        exited = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                        if exited is not None:
                            row['leader_exit_observed_without_reap'] = {'code': exited.si_code, 'status': exited.si_status}
                            break
                        remaining = timeout-(time.monotonic()-began)
                        if remaining <= 0:
                            timed_out = True
                            break
                        time.sleep(min(0.5, remaining))
                finally:
                    # Immediate post-spawn guard. No poll/wait before final signal;
                    # the waitable leader pins the numeric process-group identity.
                    pgid = child.pid
                    os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if os.getpgid(child.pid) != pgid or os.getsid(child.pid) != pgid:
                        raise RuntimeError('fixed-tool leader left original PGID/SID; no group signal sent')
                    try:
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    row['returncode'] = child.wait(timeout=2)
                    reaped, deadline = [], time.monotonic()+2
                    while True:
                        try:
                            pid, status = os.waitpid(-pgid, os.WNOHANG)
                            if pid:
                                reaped.append({'pid': pid, 'wait_status': status})
                                continue
                        except ChildProcessError:
                            pass
                        surviving = process_group(pgid)
                        if not surviving:
                            break
                        if time.monotonic() >= deadline:
                            raise RuntimeError('process group remains after bounded kill/reap: '+repr(surviving))
                        time.sleep(0.02)
                    row['reaped_adopted_descendants'] = reaped
                    row['group_empty_after_cleanup'] = True
            row['wall_timeout'] = timed_out
            if timed_out:
                raise TimeoutError(label+' exceeded '+str(timeout)+' seconds')
            if row['returncode'] != 0:
                raise subprocess.CalledProcessError(row['returncode'], row['argv'])
        except BaseException as error:
            row['error'] = str(error)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic()-began
            observed = [member for sample in samples for member in sample['members']]
            row['resources'] = {'maximum_sampled_rss_kib': max((m['memory_kib'].get('VmRSS', 0) for m in observed), default=0),
                'maximum_observed_hwm_kib': max((m['memory_kib'].get('VmHWM', 0) for m in observed), default=0),
                'largest_sampled_process_cpu_seconds': max((m['user_seconds']+m['system_seconds'] for m in observed), default=0),
                'scope': 'Periodic /proc observations, not unsampled true peaks or complete descendant CPU accounting.'}
            with command_lock:
                commands[row_index] = row
            persist_commands()
        print('PASS ' + label, flush=True)

    def compile_bench(label, radix4=1, netlist=None, cells=None):
        executable = out / (label + '.vvp')
        sources = [str(netlist), str(cells)] if netlist else RTL
        argv = [str(tools['iverilog']), '-g2012', '-Wall', '-s', BENCH_TOP,
                '-P' + BENCH_TOP + '.MUL_RADIX4=' + str(radix4), '-o', str(executable)]
        if netlist:
            argv += ['-DDATASET_ITEM_NETLIST']
        run('compile-' + label, [*argv, *sources, BENCH])
        return executable

    def simulate(label, executable, mode, selection='cases-control.hex', reference=None, radix4=1):
        result_path = out / (label + '-latencies.hex')
        run(label, [str(tools['vvp']), str(executable), '+DIR=' + str(out / 'fixtures'),
                   '+CASES=' + selection, '+MODE=' + mode, '+RESULTS=' + str(result_path)])
        lines = (out / (label + '.log')).read_text().splitlines()
        passes = [line for line in lines if line.startswith('PASS ')]
        assert len(passes) == 1 and passes[0].startswith('PASS dataset_item ')
        assert not any('FATAL:' in line or line.startswith('FAIL ') for line in lines)
        record = passes[0]
        if reference:
            with record_lock:
                assert record == records[reference], (label, record, records[reference])
            prior_path = (args.validated_out.resolve() if args.synthesize_only else out) / (reference+'-latencies.hex')
            assert result_path.read_bytes() == prior_path.read_bytes(), 'mapped per-return measurements differ'
        fields = {key: int(value) for key, value in re.findall(r'(\w+)=(-?\d+)', record)}
        expected_fields = {'cases', 'completed', 'stages', 'retired', 'muls', 'cycles', 'exec_cycles', 'errors',
                           'aborts', 'stale', 'fetch_stalls', 'cache_stalls', 'aborted_retired', 'aborted_muls',
                           'aborted_stages', 'aborted_cycles'}
        assert set(fields) == expected_fields and all(x >= 0 for x in fields.values())
        measured = []
        assert result_path.is_file(), 'missing per-successful-item measured latency records'
        for line in result_path.read_text().splitlines():
            case, stages, retired, muls, cycles, exec_cycles = map(int, line.split())
            assert case in cases and stages == 8 and retired == cases[case]['retired'] and muls == cases[case]['muls']
            ideal_exec = 3*retired+(34 if radix4 else 2)*muls
            assert exec_cycles >= ideal_exec and cycles >= exec_cycles
            ideal_outer = 74 if radix4 else 42
            core_extra = exec_cycles-ideal_exec
            outer_extra = cycles-exec_cycles-ideal_outer
            assert outer_extra >= 0
            if mode == 'corpus':
                assert exec_cycles == ideal_exec and cycles == (74 if radix4 else 42)+ideal_exec
            measured.append({'case': case, 'stages': stages, 'retired': retired, 'muls': muls,
                             'cycles': cycles, 'exec_cycles': exec_cycles,
                             'ideal_program_cycles': ideal_exec, 'ideal_outer_cycles': ideal_outer,
                             'program_service_extra_cycles': core_extra,
                             'outer_service_extra_cycles': outer_extra})
        assert fields['completed'] == len(measured)
        for key in ['stages', 'retired', 'muls', 'cycles', 'exec_cycles']:
            successful = sum(row[key] for row in measured)
            # Terminal totals include native-checked failed prefixes; RESULTS
            # deliberately contains successful complete items only.
            assert fields[key] >= successful
            if fields['errors'] == 0:
                assert fields[key] == successful
        if mode in ['corpus', 'stalled', 'held']:
            assert [row['case'] for row in measured] == selections[selection]
            assert fields['cases'] == len(measured) and fields['errors'] == fields['aborts'] == 0
        elif mode == 'malformed':
            assert fields['errors'] == 22 and fields['completed'] == 1 and fields['cases'] == 23 and fields['aborts'] == 0
        elif mode in ['cancel', 'reset']:
            assert fields['errors'] == 0 and fields['aborts'] == fields['completed'] == 18 and fields['cases'] == 36
            assert fields['aborted_cycles'] > 0
        elif mode == 'stale':
            assert fields['errors'] == fields['aborts'] == 0 and fields['completed'] == len(selections[selection])
            assert fields['stale'] > 0
        elif mode == 'exhaustion':
            assert fields['errors'] == 0 and fields['aborts'] == 1 and fields['completed'] == 8192 and fields['cases'] == 8193
        elif mode == 'outer-exhaustion':
            assert fields['errors'] == 65534 and fields['aborts'] == 0 and fields['completed'] == 2 and fields['cases'] == 65536
        with record_lock:
            records[label] = record
        return {'record': record, 'mode': mode, 'selection': selection, **fields, 'item_measurements': measured,
                'terminal_totals_include_error_prefix_work': fields['errors'] > 0,
                'item_measurements_include_successful_returns_only': True}

    def simulation_batch(specifications):
        """Join every submitted mode before reporting failures; preserve all logs."""
        results, failures = {}, []
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            pending = [(row['label'], pool.submit(simulate, **row)) for row in specifications]
            for label, future in pending:
                try:
                    results[label] = future.result()
                except Exception as error:
                    failures.append((label, str(error)))
        if failures:
            summary.setdefault('completed_modes_before_batch_failure', {}).update(results)
            summary['batch_failures'] = failures
            raise RuntimeError('simulation batch failed after all futures joined: ' + repr(failures))
        return results

    try:
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER unavailable')
        summary['process_local_subreaper_enabled'] = True
        summary['source_head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
        assert sha(ROOT / 'vendor/randomx.lock.json') == PIN_LOCK
        assert sha(ROOT / 'vendor/randomx.sha256.json') == PIN_MANIFEST
        lock = load(ROOT / 'vendor/randomx.lock.json')
        assert lock['commit'] == PIN and lock['tag'] == 'v2.0.1'
        manifest = load(ROOT / 'vendor/randomx.sha256.json')
        assert {str(p.relative_to(ROOT / 'vendor/randomx')): sha(p)
                for p in sorted((ROOT / 'vendor/randomx').rglob('*')) if p.is_file()} == manifest
        bound = {*RTL, BENCH, ORACLE, DRIVER, 'rtl/dataset/LICENSE', 'rtl/execute/LICENSE',
                 'vendor/randomx.lock.json', 'vendor/randomx.sha256.json'}
        bound.update('vendor/randomx/' + name for name in manifest)
        inputs = {name: sha(ROOT / name) for name in sorted(bound)}
        save(out / 'inputs.json', inputs)
        metadata = {}
        for name, path in tools.items():
            result = subprocess.run([str(path), '-V' if name in ['iverilog', 'vvp', 'yosys'] else '--version'], capture_output=True, text=True)
            metadata[name] = {'path': str(path), 'sha256': sha(path), 'version_returncode': result.returncode,
                              'version_stdout': result.stdout, 'version_stderr': result.stderr}
        save(out / 'tools.json', metadata)
        shutil.copyfile(ROOT / 'vendor/randomx/LICENSE', out / 'LICENSE-RandomX')
        shutil.copyfile(ROOT / 'rtl/dataset/LICENSE', out / 'LICENSE-OpenRX-dataset')
        shutil.copyfile(ROOT / 'rtl/execute/LICENSE', out / 'LICENSE-OpenRX-execute')
        fixtures = out / 'fixtures'
        if args.synthesize_only:
            prior, summary['validated_reuse'] = reused_fixtures(args, fixtures, inputs)
            summary['prior_correctness'] = {'summary_status': prior['status'], 'rtl': prior['rtl']}
            # Exact prior PASS strings are receipt-bound through summary.json.
            records.update({label: row['record'] for label, row in prior['rtl'].items()})
        else:
            fixtures.mkdir()
            if args.native_library:
                library = args.native_library.resolve()
                summary['native_library'] = provenance_library(library, args.native_build_execution.resolve())
            else:
                native_build = out / 'native-library'
                run('configure-native-library', [str(tools['cmake']), '-S', 'vendor/randomx', '-B', str(native_build),
                    '-DCMAKE_BUILD_TYPE=Release', '-DARCH=default', '-DBUILD_SHARED_LIBS=OFF'])
                run('build-native-library', [str(tools['cmake']), '--build', str(native_build), '--target', 'randomx',
                    '--parallel', str(args.jobs)], timeout=3600)
                library = native_build / 'librandomx.a'
                assert library.is_file()
                summary['native_library'] = {'fallback': 'Build unchanged pinned native RandomX static library for actual Argon/cache preparation.',
                                             'path': str(library), 'sha256': sha(library)}
            executable = out / 'dataset-item-oracle'
            run('compile-native-oracle', [str(tools['g++']), '-O2', '-std=c++17', '-Wall', '-Wextra',
                '-Ivendor/randomx/src', ORACLE, str(library), '-pthread', '-o', str(executable)])
            run('native-oracle', [str(executable), str(fixtures)])
            timing = load(out / 'native-cache-host-timing.json')
            assert all(len(timing[key]) == 2 and all(x >= 0 for x in timing[key])
                       for key in ['cache_initialization_host_seconds', 'cache_export_host_seconds'])
            summary['native_host_timing'] = {'artifact': 'native-cache-host-timing.json',
                'sha256': sha(out / 'native-cache-host-timing.json'), 'hardware_cycles': False}
        native, cases, selections, coverage = corpus(fixtures)
        save(out / 'native-corpus.json', native)
        save(out / 'coverage.json', coverage)
        fixture_hashes = {str(p.relative_to(fixtures)): sha(p) for p in sorted(fixtures.rglob('*')) if p.is_file()}
        save(out / 'fixtures.sha256.json', fixture_hashes)
        if not args.synthesize_only:
            executable = compile_bench('rtl')
            baseline = compile_bench('rtl-radix0', radix4=0)
            specifications = []
            for label, mode, selection in [('rtl-corpus', 'corpus', 'cases.hex'),
                    ('rtl-mapped-corpus', 'corpus', 'cases-mapped.hex'),
                    *[('rtl-' + mode, mode, 'cases-mapped.hex' if mode == 'stalled' else 'cases-control.hex') for mode in CONTROLS],
                    ('rtl-exhaustion', 'exhaustion', 'cases-empty.hex'),
                    ('rtl-outer-exhaustion', 'outer-exhaustion', 'cases-control.hex')]:
                specifications.append({'label': label, 'executable': executable, 'mode': mode, 'selection': selection})
            specifications.append({'label': 'rtl-radix0-corpus', 'executable': baseline, 'mode': 'corpus',
                                   'selection': 'cases-mapped.hex', 'radix4': 0})
            specifications.append({'label': 'rtl-radix0-stalled', 'executable': baseline, 'mode': 'stalled',
                                   'selection': 'cases-mapped.hex', 'radix4': 0})
            summary['rtl'] = simulation_batch(specifications)
            summary['correctness_completed'] = True
        else:
            summary['correctness_completed'] = True
        if args.synthesize or args.synthesize_only:
            netlist = out / 'netlist-dataset-item.v'
            script = 'read_verilog ' + ' '.join(RTL) + '; '
            script += f'synth -top {TOP} -flatten; check -assert; tee -o {out}/stat-dataset-item.txt stat; '
            script += f'write_verilog -noattr {netlist}; write_json {out}/netlist-dataset-item.json'
            run('synth-dataset-item', [str(tools['yosys']), '-p', script], timeout=3600)
            module = load(out / 'netlist-dataset-item.json')['modules'][TOP]
            kinds = Counter(row['type'] for row in module['cells'].values())
            cells = int(re.search(r'Number of cells:\s*(\d+)', (out / 'stat-dataset-item.txt').read_text())[1])
            assert cells == sum(kinds.values())
            summary['mapping'] = {'top': TOP, 'MUL_RADIX4': 1, 'num_cells': cells,
                'flop_cells': sum(n for kind, n in kinds.items() if 'DFF' in kind),
                'latch_cells': sum(n for kind, n in kinds.items() if 'LATCH' in kind),
                'num_cells_by_type': dict(sorted(kinds.items())),
                'scope': 'Actual dataset-item seed/controller, prepared superscalar executor and multiplier; excludes external Argon/cache images/program/table preparation and service, dataset storage and physical implementation.'}
            assert summary['mapping']['latch_cells'] == 0
            installed = Path('/usr/share/yosys/simcells.v')
            cells_model = out / 'yosys-simcells.v'
            shutil.copyfile(installed, cells_model)
            save(out / 'yosys-cell-model.json', {'installed_path': str(installed), 'sha256': sha(installed), 'copied_sha256': sha(cells_model)})
            executable = compile_bench('mapped', netlist=netlist, cells=cells_model)
            specifications = [{'label': 'mapped-corpus', 'executable': executable, 'mode': 'corpus',
                               'selection': 'cases-mapped.hex', 'reference': 'rtl-mapped-corpus'}]
            specifications.extend({'label': 'mapped-' + mode, 'executable': executable,
                                   'mode': mode, 'selection': 'cases-mapped.hex' if mode == 'stalled' else 'cases-control.hex',
                                   'reference': 'rtl-' + mode} for mode in CONTROLS)
            summary['mapped'] = simulation_batch(specifications)
        summary['native_cases'] = len(cases)
        summary['native_retirements'] = coverage['native_retirements']
        summary['rtl_modes_newly_executed'] = len(summary['rtl'])
        summary['mapped_modes_newly_executed'] = len(summary['mapped'])
        assert set(summary['rtl']) == (set() if args.synthesize_only else set(RTL_PROFILES))
        assert len(summary['mapped']) == (7 if args.synthesize or args.synthesize_only else 0)
        summary['source_unchanged_after_run'] = all(sha(ROOT / name) == value for name, value in inputs.items())
        summary['fixtures_unchanged_after_run'] = {str(p.relative_to(fixtures)): sha(p)
            for p in sorted(fixtures.rglob('*')) if p.is_file()} == fixture_hashes
        assert summary['source_unchanged_after_run'] and summary['fixtures_unchanged_after_run']
        summary['status'] = 'pass' if args.synthesize or args.synthesize_only else 'pass_correctness'
        print('PASS dataset_item_suite native_cases=20 mapped_cases=5 rtl_modes=' + str(len(summary['rtl']))
              + ' mapped_modes=' + str(len(summary['mapped'])), flush=True)
    except Exception as error:
        summary['status'] = 'failed'
        summary['error'] = str(error)
        raise
    finally:
        save(out / 'summary.json', summary)
        save(out / 'artifacts.sha256.json', {str(p.relative_to(out)): sha(p)
            for p in sorted(out.rglob('*')) if p.is_file() and p != out / 'artifacts.sha256.json'})


if __name__ == '__main__':
    main()
