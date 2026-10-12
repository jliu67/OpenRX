#!/usr/bin/env python3
"""Build unchanged native controls in a fresh external execution destination.

Invoke through the immutable local runner for substantial builds. This builder
does not allocate a resource slot, submit requests or authorize experiments.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def external_directory(path):
    destination = Path(path).resolve()
    source = ROOT.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise ValueError('staging destination must be outside and disjoint from the source tree')
    return destination


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-root', type=Path, required=True,
                        help='Fresh external directory; use {execution_dir}/native-build with the local runner')
    available_cpus = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else os.cpu_count() or 1
    parser.add_argument('--jobs', type=int, default=os.environ.get('BUILD_JOBS', str(min(6, available_cpus))))
    parser.add_argument('--arch', default=os.environ.get('ARCH', 'native'), choices=('native', 'default'))
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error('jobs must be positive')
    if args.arch not in ('native', 'default'):
        parser.error('arch must be native or default')
    try:
        build = external_directory(args.build_root)
        # Exclusive creation preserves prior builds, logs and failed attempts.
        build.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    commands = [
        [sys.executable, str(ROOT / 'scripts/verify_vendor.py')],
        ['cmake', '-S', str(ROOT / 'vendor/randomx'), '-B', str(build / 'randomx'),
         '-DCMAKE_BUILD_TYPE=Release', '-DARCH=' + args.arch],
        ['cmake', '--build', str(build / 'randomx'), '--parallel', str(args.jobs)],
        ['cmake', '-S', str(ROOT / 'benchmarks/steady'), '-B', str(build / 'steady'),
         '-DCMAKE_BUILD_TYPE=Release', '-DRANDOMX_LIBRARY=' + str(build / 'randomx/librandomx.a')],
        ['cmake', '--build', str(build / 'steady'), '--parallel', str(args.jobs)],
    ]
    report = {'schema': 'openrx.native-stage.v1', 'source_root': str(ROOT),
              'build_root': str(build), 'jobs': args.jobs, 'arch': args.arch,
              'status': 'started', 'steps': [], 'source_sha256': {}, 'artifacts': {},
              'scientific_acceptance': 'unverified'}
    try:
        for relative in ('vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                         'scripts/verify_vendor.py', 'scripts/build_steady.sh', 'scripts/stage_native.py',
                         'benchmarks/steady/main.cpp', 'benchmarks/steady/CMakeLists.txt'):
            report['source_sha256'][relative] = sha256(ROOT / relative)
        # Retain tool versions and complete logs; failures leave the directory intact.
        for index, command in enumerate([['cmake', '--version'], ['c++', '--version'], *commands]):
            step = {'command': command, 'log': f'{index:02d}.log', 'returncode': None}
            report['steps'].append(step)
            with (build / step['log']).open('x') as log:
                process = subprocess.run(command, cwd=build, stdout=log, stderr=subprocess.STDOUT)
            step['returncode'] = process.returncode
            if process.returncode:
                raise ValueError('build step failed: ' + step['log'])
        report['status'] = 'built'
    except (OSError, ValueError, KeyboardInterrupt) as exc:
        report['status'] = 'failed'
        report['error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        for relative in ('randomx/librandomx.a', 'randomx/randomx-benchmark', 'randomx/randomx-tests',
                         'steady/openrx-steady', 'randomx/CMakeCache.txt', 'steady/CMakeCache.txt'):
            path = build / relative
            if path.is_file():
                report['artifacts'][relative] = sha256(path)
        if report['status'] == 'built' and len(report['artifacts']) != 6:
            report.update(status='failed', error='missing required build artifacts')
        report['log_sha256'] = {p.name: sha256(p) for p in build.glob('*.log')}
        (build / 'build.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(build)
    return 0 if report['status'] == 'built' else 1


if __name__ == '__main__':
    raise SystemExit(main())
