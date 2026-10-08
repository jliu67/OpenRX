#!/usr/bin/env python3
"""Preserve controlled v1/v2 workload evidence; never estimate power."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
I32_MAX = (1 << 31) - 1
# Pinned src/tests/benchmark.cpp: 1000 nonces, seed 0, hashes (not commitments).
REFERENCES = {
    'v1': '10b649a3f15c7c7f88277812f2e74b337a0f20ce909af09199cccb960771cfa1',
    'v2': 'b85d79e080b10b6ad28c2e6c993601a1361917dba979e03a0a8f7248aaf4ba52',
}


def bounded_int(value, minimum=1, maximum=I32_MAX):
    number = int(value)
    if not minimum <= number <= maximum:
        raise argparse.ArgumentTypeError(f'must be in [{minimum}, {maximum}]')
    return number


def nonnegative(value):
    return bounded_int(value, 0)


def affinity_mask(value):
    return bounded_int(value, 1, (1 << 64) - 1)


def seconds(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError('must be finite and nonnegative')
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['mine', 'verify'], default='mine')
    parser.add_argument('--versions', choices=['v1', 'v2'], nargs='+', default=['v1', 'v2'])
    parser.add_argument('--threads', type=bounded_int, default=1)
    parser.add_argument('--init-threads', type=bounded_int, default=1)
    parser.add_argument('--nonces', type=bounded_int, default=1000)
    parser.add_argument('--repeats', type=bounded_int, default=3)
    parser.add_argument('--warmups', type=nonnegative, default=0,
                        help='separate-process preconditioning runs, excluded from summaries')
    parser.add_argument('--min-run-seconds', type=seconds, default=0,
                        help='reject measured runs shorter than this approximate hashing interval')
    parser.add_argument('--seed', type=nonnegative, default=0)
    parser.add_argument('--timeout', type=bounded_int, default=900)
    parser.add_argument('--affinity', type=affinity_mask)
    parser.add_argument('--large-pages', action='store_true')
    parser.add_argument('--soft-aes', action='store_true')
    parser.add_argument('--interpreter', action='store_true')
    args = parser.parse_args(argv)
    if len(set(args.versions)) != len(args.versions):
        parser.error('--versions must not contain duplicates')
    if args.mode == 'verify' and args.threads != 1:
        parser.error('verification smoke mode requires one thread')
    if args.nonces < args.threads:
        parser.error('--nonces must be at least --threads')
    if args.affinity is not None:
        if args.threads == 1:
            parser.error('upstream ignores --affinity with one thread; use external taskset instead')
        selected = {i for i in range(64) if args.affinity & (1 << i)}
        if len(selected) < args.threads:
            parser.error('affinity mask must contain at least one CPU per thread')
        if hasattr(os, 'sched_getaffinity') and not selected <= os.sched_getaffinity(0):
            parser.error('affinity mask includes CPUs unavailable to this process')
    return args


def capture(command):
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'error': str(exc)}


def resource_context():
    """Visible restrictions, not a claim to exclusive host resources."""
    context = {'logical_cpus_visible': os.cpu_count(), 'allowed_cpus': None,
               'cgroup_files': {}}
    if hasattr(os, 'sched_getaffinity'):
        try:
            context['allowed_cpus'] = sorted(os.sched_getaffinity(0))
        except OSError as exc:
            context['affinity_error'] = str(exc)
    for name in ('cpu.max', 'cpu.stat', 'memory.max', 'memory.current', 'cpuset.cpus.effective'):
        path = Path('/sys/fs/cgroup') / name
        try:
            context['cgroup_files'][str(path)] = path.read_text().strip()
        except OSError:
            pass
    return context


def parse_output(raw, *, mode, version, nonces, seed):
    """Validate output independently of process exit status."""
    calculated = re.findall(r'^Calculated result:\s*([0-9a-fA-F]{64})\s*$', raw, re.M)
    references = re.findall(r'^Reference result:\s*([0-9a-fA-F]{64})\s*$', raw, re.M)
    performance = re.findall(r'^Performance:\s*(\S+)\s+(hashes per second|ms per hash)\s*$', raw, re.M)
    errors = []
    if len(calculated) != 1:
        errors.append('missing or duplicate calculated hash')
    if len(performance) != 1:
        errors.append('missing or duplicate performance')
    if len(references) > 1:
        errors.append('duplicate reference hash')
    value, unit, interval = None, None, None
    if len(performance) == 1:
        token, unit = performance[0]
        try:
            value = float(token)
        except ValueError:
            errors.append('invalid performance number')
        if value is not None and (not math.isfinite(value) or value <= 0):
            errors.append('performance must be finite and positive')
            value = None
        expected_unit = 'hashes per second' if mode == 'mine' else 'ms per hash'
        if unit != expected_unit:
            errors.append('performance unit does not match mode')
        if value is not None and unit == expected_unit:
            interval = nonces / value if mode == 'mine' else nonces * value / 1000
            if not math.isfinite(interval) or interval <= 0:
                errors.append('invalid inferred hashing interval')
                interval = None
    result = calculated[0].lower() if len(calculated) == 1 else None
    reference = references[0].lower() if len(references) == 1 else None
    match = result == reference if result and reference else None
    expected = REFERENCES[version] if nonces == 1000 and seed == 0 else None
    if expected is not None and (result != expected or reference != expected):
        errors.append('pinned known reference mismatch or missing reference')
    elif match is False:
        errors.append('printed reference mismatch')
    if 'ERROR:' in raw or 'Failed to set thread affinity' in raw:
        errors.append('upstream reported an execution or affinity error')
    return {'calculated_result': result, 'reference_matches': match,
            'known_reference_matches': result == expected if expected else None,
            'performance_value': value, 'performance_unit': unit,
            'hashing_seconds_approx': interval, 'validation_errors': errors}


def summarize(runs):
    """Include every measured status; never combine algorithms, units or warmups."""
    summary = {}
    measured = [run for run in runs if run['phase'] == 'measurement']
    for version in sorted({run['version'] for run in measured}):
        group = [run for run in measured if run['version'] == version]
        valid = [run for run in group if run['status'] == 'ok']
        values = [run['performance_value'] for run in valid]
        units = {run['performance_unit'] for run in valid}
        homogeneous = len(units) == 1
        summary[version] = {
            'measured_runs': len(group), 'valid_runs': len(valid),
            'failed_runs': len(group) - len(valid),
            'performance_unit': next(iter(units)) if homogeneous else None,
            'median': statistics.median(values) if values and homogeneous else None,
            'min': min(values) if values and homogeneous else None,
            'max': max(values) if values and homogeneous else None,
        }
    return summary


def save_report(output, report):
    report['summary'] = summarize(report['runs'])
    temp = output / 'results.json.tmp'
    temp.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    temp.replace(output / 'results.json')


def main(argv=None):
    args = parse_args(argv)
    subprocess.run(['python3', str(ROOT / 'scripts/verify_vendor.py')], check=True)
    binary = ROOT / 'build/randomx/randomx-benchmark'
    if not binary.is_file():
        raise SystemExit('build first: bash scripts/build.sh')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output = ROOT / 'benchmarks/results' / stamp
    output.mkdir(parents=True)
    report = {
        'schema_version': 2, 'created_utc': stamp, 'configuration': vars(args),
        'purpose': 'functional smoke' if args.mode == 'verify' else 'native throughput candidate',
        'warmup_scope': 'separate processes; preconditioning only, not same-VM/cache warmup',
        'timing_scope': 'process_elapsed_s includes initialization; hashing_seconds_approx is inferred from rounded upstream performance, not a power-alignment timestamp',
        'power_watts': None, 'hashes_per_joule': None,
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source': json.loads((ROOT / 'vendor/randomx.lock.json').read_text()),
        'project_revision': capture(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
        'project_worktree': capture(['git', '-C', str(ROOT), 'status', '--porcelain']),
        'platform': platform.platform(), 'cpu': capture(['lscpu']),
        'compiler': capture(['c++', '--version']),
        'resources_before': resource_context(), 'runs': [],
    }
    cache = ROOT / 'build/randomx/CMakeCache.txt'
    if cache.exists():
        (output / 'CMakeCache.txt').write_bytes(cache.read_bytes())
    failed = False
    try:
        for phase, count in (('warmup', args.warmups), ('measurement', args.repeats)):
            for repeat in range(count):
                order = args.versions if repeat % 2 == 0 else list(reversed(args.versions))
                for version in order:
                    command = [str(binary), '--' + args.mode, '--threads', str(args.threads),
                               '--init', str(args.init_threads), '--nonces', str(args.nonces),
                               '--seed', str(args.seed)]
                    for enabled, flag in ((not args.interpreter, '--jit'), (version == 'v2', '--v2'),
                                          (args.soft_aes, '--softAes'), (args.large_pages, '--largePages')):
                        if enabled:
                            command.append(flag)
                    if args.affinity is not None:
                        command += ['--affinity', str(args.affinity)]
                    name = ('' if phase == 'measurement' else 'warmup-') + f'{repeat + 1:02d}-{version}.log'
                    print(f'Running {version} {phase} {repeat + 1}', flush=True)
                    started = time.monotonic()
                    status, rc = 'unknown', None
                    with (output / name).open('w') as log:
                        try:
                            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                                     timeout=args.timeout)
                            rc = process.returncode
                            status = 'ok' if rc == 0 else 'failed'
                        except subprocess.TimeoutExpired:
                            status = 'timeout'
                        except OSError as exc:
                            log.write(str(exc))
                            status = 'failed'
                    parsed = parse_output((output / name).read_text(), mode=args.mode, version=version,
                                          nonces=args.nonces, seed=args.seed)
                    if status == 'ok' and parsed['validation_errors']:
                        status = 'invalid-output'
                    interval = parsed['hashing_seconds_approx']
                    if status == 'ok' and phase == 'measurement' and interval < args.min_run_seconds:
                        status = 'too-short'
                        parsed['validation_errors'].append('hashing interval below --min-run-seconds')
                    report['runs'].append({
                        'phase': phase, 'version': version, 'repeat': repeat + 1, 'command': command,
                        'status': status, 'returncode': rc,
                        'process_elapsed_s': time.monotonic() - started, 'log': name, **parsed,
                    })
                    failed |= status != 'ok'
                    save_report(output, report)
    finally:
        report['resources_after'] = resource_context()
        save_report(output, report)
    print(output)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
