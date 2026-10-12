#!/usr/bin/env python3
"""Run the opt-in steady adapter; retain raw evidence, never estimate power."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = {
    'v1': '10b649a3f15c7c7f88277812f2e74b337a0f20ce909af09199cccb960771cfa1',
    'v2': 'b85d79e080b10b6ad28c2e6c993601a1361917dba979e03a0a8f7248aaf4ba52',
}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, low=0):
    check(type(value) is int and low <= value <= 2**63 - 1, 'invalid integer in adapter record')
    return value


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        check(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('non-finite JSON constant: ' + value)


def validate(text, expected=None):
    """Validate completeness, order, hashes and clocks before summarizing trials."""
    records = [json.loads(line, object_pairs_hook=strict_object, parse_constant=reject_constant)
               for line in text.splitlines() if line.strip()]
    check(len(records) >= 3 and all(isinstance(r, dict) for r in records), 'incomplete JSONL')
    config, complete = records[0], records[-1]
    check(config.get('type') == 'config' and type(config.get('schema_version')) is int and config['schema_version'] == 1, 'bad schema')
    check(complete.get('type') == 'complete', 'missing completion record')
    for name in ('threads', 'init_threads', 'nonces', 'repeats', 'pid',
                 'monotonic_resolution_ns', 'realtime_resolution_ns'):
        integer(config[name], 1)
    integer(config['warmup_nonces'])
    check(config['threads'] <= 256 and config['init_threads'] <= 256, 'thread count exceeds adapter cap')
    check(config['nonces'] <= 2147483647 and config['warmup_nonces'] <= 2147483647
          and config['repeats'] <= 10000, 'work count exceeds adapter cap')
    check(config['threads'] <= config['nonces'] and
          (not config['warmup_nonces'] or config['threads'] <= config['warmup_nonces']),
          'counts do not cover workers')
    versions = config['versions']
    check(versions in (['v1'], ['v2'], ['v1', 'v2'], ['v2', 'v1']), 'invalid version selection')
    minimum = config['min_seconds']
    check(type(minimum) in (int, float) and math.isfinite(minimum) and minimum >= 0, 'bad duration gate')
    check(config['aes'] in ('hardware', 'software'), 'invalid AES mode')
    check(type(config['flags']) is int and config['flags'] == (14 if config['aes'] == 'hardware' else 12),
          'unexpected effective flags')
    check(type(config['seed']) is int and config['seed'] == 0, 'reference controls require seed 0')
    check(config['scheduler'] == 'static-stride-batch-first-next-last', 'unexpected scheduler')
    check(config.get('power_watts') is None, 'adapter cannot measure power')
    if expected is not None:
        for key, value in expected.items():
            check(config.get(key) == value, 'command/config mismatch: ' + key)
    plan = [('control', v, 0, 1000) for v in versions]
    for repeat in range(1, config['repeats'] + 1):
        order = versions if repeat % 2 else list(reversed(versions))
        for version in order:
            if config['warmup_nonces']:
                plan.append(('warmup', version, repeat, config['warmup_nonces']))
            plan.append(('measurement', version, repeat, config['nonces']))
    intervals = records[1:-1]
    check(len(intervals) == len(plan), 'missing or extra interval')
    prior_end, rejected, clock_deltas, repeated = 0, 0, [], {}
    groups = {v: [] for v in versions}
    for index, (record, target) in enumerate(zip(intervals, plan), 1):
        check(record.get('type') == 'interval', 'unexpected event')
        check(integer(record['sequence'], 1) == index, 'bad sequence')
        check((record['phase'], record['version'], integer(record['repeat']),
               integer(record['hashes'], 1)) == target, 'wrong phase/version/repeat/count')
        digest = record['digest']
        check(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'malformed digest')
        if target[3] == 1000:
            check(digest == REFERENCES[target[1]] and record['reference_matches'] is True,
                  'known reference mismatch')
        else:
            check(record['reference_matches'] is None, 'invented known reference')
        signature = (target[1], target[3])
        check(signature not in repeated or repeated[signature] == digest, 'non-deterministic repeated digest')
        repeated[signature] = digest
        start, end = record['start'], record['end']
        for point in (start, end):
            for key in ('mono_before_ns', 'unix_ns', 'mono_after_ns'):
                integer(point[key], 1)
            check(point['mono_before_ns'] <= point['mono_after_ns'], 'reversed clock bracket')
        check(prior_end <= start['mono_before_ns'] <= start['mono_after_ns'] < end['mono_before_ns'],
              'overlapping or reversed intervals')
        elapsed = integer(record['elapsed_ns'], 1)
        check(elapsed == end['mono_before_ns'] - start['mono_after_ns'], 'inconsistent duration')
        prior_end = end['mono_after_ns']
        delta = (end['unix_ns'] - start['unix_ns']) - (
            (end['mono_before_ns'] + end['mono_after_ns']) -
            (start['mono_before_ns'] + start['mono_after_ns'])) / 2
        clock_deltas.append(delta)
        short = target[0] == 'measurement' and elapsed / 1e9 < minimum
        check(record['status'] == ('too-short' if short else 'ok'), 'incorrect quality status')
        rejected += int(short)
        if target[0] == 'measurement' and not short:
            groups[target[1]].append(target[3] / (elapsed / 1e9))
    check(integer(complete['intervals']) == len(plan), 'wrong completion count')
    check(integer(complete['invalid_intervals']) == rejected, 'wrong rejection count')
    return {'accepted': rejected == 0, 'expected_returncode': 2 if rejected else 0,
            'rejected_measurements': rejected, 'controls_passed': len(versions),
            'balanced_version_order': len(versions) == 1 or config['repeats'] % 2 == 0,
            'wall_clock_alignment_verified': False,
            'max_abs_clock_delta_ns': max(map(abs, clock_deltas)),
            'power_watts': None, 'hashes_per_joule': None,
            'measurements': {v: {'accepted': len(values),
                'attempted': config['repeats'],
                'median_hps': statistics.median(values) if values else None,
                'min_hps': min(values) if values else None,
                'max_hps': max(values) if values else None} for v, values in groups.items()}}


def capture(command):
    try:
        p = subprocess.run(command, text=True, capture_output=True, timeout=15)
        return {'command': command, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'command': command, 'error': str(exc)}


def resources():
    result = {'cpu_affinity': sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None}
    for name in ('cpu.max', 'cpu.stat', 'cpuset.cpus.effective', 'memory.max', 'memory.current'):
        path = Path('/sys/fs/cgroup') / name
        try:
            result[name] = path.read_text()
        except OSError:
            result[name] = None
    return result


def external_output(path):
    """Explicit local outputs must not mutate or contain the retained source."""
    destination, source = Path(path).resolve(), ROOT.resolve()
    check(destination != source and source not in destination.parents and destination not in source.parents,
          'explicit output must be outside and disjoint from the source tree')
    return destination


def validate_build(build, binary):
    """A staged launch must consume the exact successful build and sources."""
    receipt = json.loads((build / 'build.json').read_text(), object_pairs_hook=strict_object,
                         parse_constant=reject_constant)
    check(isinstance(receipt, dict), 'invalid native staging receipt')
    check(receipt.get('schema') == 'openrx.native-stage.v1' and receipt.get('status') == 'built',
          'native staging build is incomplete or failed')
    check(isinstance(receipt.get('source_sha256'), dict) and isinstance(receipt.get('artifacts'), dict),
          'missing native staging bindings')
    check(binary == (build / 'steady/openrx-steady').resolve(), 'binary differs from staged build')
    for relative in ('vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                     'benchmarks/steady/main.cpp', 'benchmarks/steady/CMakeLists.txt'):
        check(receipt['source_sha256'].get(relative) == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
              'staged source mismatch: ' + relative)
    for relative in ('randomx/librandomx.a', 'randomx/randomx-benchmark', 'randomx/randomx-tests',
                     'steady/openrx-steady', 'randomx/CMakeCache.txt', 'steady/CMakeCache.txt'):
        check(receipt['artifacts'].get(relative) == hashlib.sha256((build / relative).read_bytes()).hexdigest(),
              'staged artifact mismatch: ' + relative)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--versions', choices=['v1', 'v2', 'v1,v2', 'v2,v1'], default='v1,v2')
    parser.add_argument('--aes', choices=['hardware', 'software'], default='hardware')
    for name, default in [('threads', 1), ('init-threads', 2), ('nonces', 1000),
                          ('warmup-nonces', 1000), ('repeats', 4)]:
        parser.add_argument('--' + name, type=int, default=default)
    parser.add_argument('--min-seconds', type=float, default=1)
    parser.add_argument('--timeout', type=int, default=900, help='Whole native process deadline in seconds')
    parser.add_argument('--binary', type=Path, help='Explicit verified openrx-steady executable')
    parser.add_argument('--build-root', type=Path, help='Native build root containing randomx/ and steady/')
    parser.add_argument('--output-dir', type=Path, help='Fresh external output; local runner: {execution_dir}/trial')
    args = parser.parse_args(argv)
    if args.timeout < 1 or not math.isfinite(args.min_seconds) or args.min_seconds < 0:
        parser.error('timeout must be positive and minimum duration finite and nonnegative')
    build = (args.build_root or ROOT / 'build').resolve()
    binary = (args.binary or build / 'steady/openrx-steady').resolve()
    try:
        output = external_output(args.output_dir) if args.output_dir else ROOT / 'benchmarks/results' / (
            dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + '-steady')
        check(output != build and output not in build.parents and build not in output.parents,
              'output and build roots must be disjoint')
        check(output != binary and output not in binary.parents, 'output must not contain the binary')
        output.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    config = {name: getattr(args, name) for name in ('versions', 'aes', 'threads', 'init_threads',
              'nonces', 'warmup_nonces', 'repeats', 'min_seconds')}
    command = [str(binary)]
    for key, value in config.items():
        command += ['--' + key.replace('_', '-'), str(value)]
    report = {'schema_version': 1, 'purpose': 'native adapter trial, not calibrated hardware efficiency',
              'command': command, 'configuration': config, 'timeout_s': args.timeout,
              'source_root': str(ROOT), 'build_root': str(build), 'binary': str(binary),
              'platform': platform.platform(), 'python': sys.version,
              'git_revision': capture(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
              'git_status': capture(['git', '-C', str(ROOT), 'status', '--porcelain']),
              'cpu': capture(['lscpu']), 'compiler': capture(['c++', '--version']),
              'resources_before': resources(), 'status': 'started', 'returncode': None,
              'source_sha256': {}, 'power_watts': None, 'hashes_per_joule': None}
    for path in ('vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                 'benchmarks/steady/main.cpp', 'benchmarks/steady/CMakeLists.txt',
                 'scripts/steady_benchmark.py', 'scripts/build_steady.sh'):
        file = ROOT / path
        if file.is_file():
            report['source_sha256'][path] = hashlib.sha256(file.read_bytes()).hexdigest()
    try:
        for name in ('randomx', 'steady'):
            cache = build / name / 'CMakeCache.txt'
            if cache.is_file():
                shutil.copyfile(cache, output / (name + '-CMakeCache.txt'))
        if (build / 'build.json').is_file():
            shutil.copyfile(build / 'build.json', output / 'build.json')
            report['build_receipt_sha256'] = hashlib.sha256((output / 'build.json').read_bytes()).hexdigest()
        report['vendor_integrity'] = capture([sys.executable, str(ROOT / 'scripts/verify_vendor.py')])
        check(report['vendor_integrity'].get('returncode') == 0, 'vendor integrity failed')
        if args.build_root is not None:
            validate_build(build, binary)
        check(binary.is_file(), 'build first: bash scripts/build_steady.sh')
        report['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        with (output / 'adapter.jsonl').open('w') as out, (output / 'adapter.stderr').open('w') as err:
            with subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True) as p:
                try:
                    report['returncode'] = p.wait(timeout=args.timeout)
                except BaseException:
                    # Kill the process group and reap it on timeout or interruption.
                    # wait() can reap the child during KeyboardInterrupt handling.
                    # Never signal its numerical group after that ownership ends.
                    if p.returncode is None:
                        try:
                            os.killpg(p.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    report['returncode'] = p.wait()
                    raise
        expected = dict(config); expected['versions'] = config['versions'].split(',')
        report['summary'] = validate((output / 'adapter.jsonl').read_text(), expected)
        check(report['returncode'] == report['summary']['expected_returncode'], 'unexpected process exit')
        check(not (output / 'adapter.stderr').read_text().strip(), 'adapter wrote unexpected stderr')
        report['status'] = 'ok' if report['summary']['accepted'] else 'rejected-duration'
    except (OSError, ValueError, KeyError, TypeError, OverflowError, subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        report['status'] = 'failed'
        report['error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        report['resources_after'] = resources()
        report['raw_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in output.glob('adapter.*') if p.is_file()}
        (output / 'run.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(output)
    return 0 if report['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
