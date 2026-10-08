#!/usr/bin/env python3
"""Run controlled v1/v2 workloads and preserve raw evidence. No power estimation."""
import argparse
import datetime as dt
import json
import hashlib
import os
from pathlib import Path
import platform
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return number

def capture(command):
    try:
        p = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return {'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'error': str(exc)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['mine', 'verify'], default='mine')
    parser.add_argument('--versions', choices=['v1', 'v2'], nargs='+', default=['v1', 'v2'])
    parser.add_argument('--threads', type=positive, default=1)
    parser.add_argument('--init-threads', type=positive, default=1)
    parser.add_argument('--nonces', type=positive, default=1000)
    parser.add_argument('--repeats', type=positive, default=3)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--timeout', type=positive, default=900)
    parser.add_argument('--affinity', type=int)
    parser.add_argument('--large-pages', action='store_true')
    parser.add_argument('--soft-aes', action='store_true')
    parser.add_argument('--interpreter', action='store_true')
    args = parser.parse_args()
    if args.mode == 'verify' and args.threads != 1:
        parser.error('verification smoke mode requires one thread')
    if args.seed < 0 or (args.affinity is not None and args.affinity < 0):
        parser.error('seed and affinity must be nonnegative')
    subprocess.run(['python3', str(ROOT/'scripts/verify_vendor.py')], check=True)
    binary = ROOT/'build/randomx/randomx-benchmark'
    if not binary.is_file():
        parser.error('build first: bash scripts/build.sh')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    output = ROOT/'benchmarks/results'/stamp
    output.mkdir(parents=True)
    report = {'schema_version': 1, 'created_utc': stamp, 'configuration': vars(args),
              'purpose': 'functional smoke' if args.mode == 'verify' else 'native throughput',
              'power_watts': None, 'hashes_per_joule': None,
              'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'source': json.loads((ROOT/'vendor/randomx.lock.json').read_text()),
              'project_revision': capture(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']),
              'platform': platform.platform(), 'cpu': capture(['lscpu']),
              'compiler': capture(['c++', '--version']), 'runs': []}
    cache = ROOT/'build/randomx/CMakeCache.txt'
    if cache.exists():
        (output/'CMakeCache.txt').write_bytes(cache.read_bytes())
    failed = False
    try:
        for repeat in range(args.repeats):
            order = args.versions if repeat % 2 == 0 else list(reversed(args.versions))
            for version in order:
                command = [str(binary), '--'+args.mode, '--threads', str(args.threads),
                           '--init', str(args.init_threads), '--nonces', str(args.nonces),
                           '--seed', str(args.seed)]
                if not args.interpreter:
                    command.append('--jit')
                if version == 'v2':
                    command.append('--v2')
                if args.soft_aes:
                    command.append('--softAes')
                if args.large_pages:
                    command.append('--largePages')
                if args.affinity is not None:
                    command += ['--affinity', str(args.affinity)]
                name = f'{repeat+1:02d}-{version}.log'
                print('Running', version, 'repeat', repeat+1, flush=True)
                started = time.monotonic()
                status = 'unknown'
                rc = None
                with (output/name).open('w') as log:
                    try:
                        p = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                           timeout=args.timeout)
                        rc = p.returncode
                        status = 'ok' if rc == 0 else 'failed'
                    except subprocess.TimeoutExpired:
                        status = 'timeout'
                    except OSError as exc:
                        log.write(str(exc))
                        status = 'failed'
                raw = (output/name).read_text()
                calculated = re.search(r'Calculated result:\s*([0-9a-f]{64})', raw)
                reference = re.search(r'Reference result:\s*([0-9a-f]{64})', raw)
                match = calculated.group(1) == reference.group(1) if calculated and reference else None
                perf = re.search(r'Performance:\s*([\d.eE+-]+)\s+(hashes per second|ms per hash)', raw)
                expects_reference = args.nonces == 1000 and args.seed == 0
                if status == 'ok' and (not calculated or not perf or match is False
                                       or (expects_reference and match is not True) or 'ERROR:' in raw):
                    status = 'invalid-output'
                report['runs'].append({'version': version, 'repeat': repeat+1, 'command': command,
                    'status': status, 'returncode': rc, 'process_elapsed_s': time.monotonic()-started,
                    'log': name, 'calculated_result': calculated.group(1) if calculated else None,
                    'reference_matches': match,
                    'performance_value': float(perf.group(1)) if perf else None,
                    'performance_unit': perf.group(2) if perf else None})
                failed |= status != 'ok'
                (output/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    finally:
        (output/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(output)
    return 1 if failed else 0

if __name__ == '__main__':
    raise SystemExit(main())
