#!/usr/bin/env python3
"""Run Linux runtime controls, preserving raw output and failed reports."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys

ORACLES = {
    'sigill-recovery': 4,
    'rw-execution-denied': 11,
    'initial-cache-flush': 0,
    'generated-return': 7,
    'rx-write-denied': 11,
    'overwrite-cache-flush': 0,
    'overwritten-return': 19,
    'restore-cache-flush': 0,
    'restored-return': 7,
}


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field: ' + key)
        result[key] = value
    return result


def validate_output(raw, *, expect_architecture=None):
    rows = [json.loads(line, object_pairs_hook=strict_object) for line in raw.splitlines() if line.strip()]
    if len(rows) != 11 or any(type(r) is not dict for r in rows):
        raise ValueError('Expected config, nine runtime checks and summary')
    config, summary = rows[0], rows[-1]
    if (set(config) != {'type', 'schema_version', 'architecture', 'flush_path', 'functional_only'}
            or config['type'] != 'config' or type(config['schema_version']) is not int
            or config['schema_version'] != 1 or config['functional_only'] is not True):
        raise ValueError('Invalid runtime configuration')
    paths = {'x86_64': 'compiler-builtin', 'riscv64': 'linux-riscv-flush-icache'}
    if (type(config['architecture']) is not str or config['architecture'] not in paths
            or config['flush_path'] != paths[config['architecture']]
            or (expect_architecture is not None and config['architecture'] != expect_architecture)):
        raise ValueError('Architecture/cache flush path mismatch')
    for row, (name, value) in zip(rows[1:-1], ORACLES.items()):
        if (set(row) != {'type', 'name', 'actual', 'expected', 'status'}
                or row['type'] != 'check' or row['name'] != name or row['status'] != 'pass'
                or type(row['actual']) is not int or type(row['expected']) is not int
                or row['actual'] != value or row['expected'] != value):
            raise ValueError('Failed, reordered or unknown runtime control: ' + name)
    if (set(summary) != {'type', 'checks', 'status', 'functional_only'}
            or summary['type'] != 'summary' or type(summary['checks']) is not int
            or summary['checks'] != 9 or summary['status'] != 'pass'
            or summary['functional_only'] is not True):
        raise ValueError('Invalid runtime summary')
    return {'checks_passed': 9, 'architecture': config['architecture'],
            'flush_path': config['flush_path'], 'timing_calibrated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--qemu')
    parser.add_argument('--sysroot', type=Path, default=Path('/usr/riscv64-linux-gnu'))
    parser.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('timeout must be positive')
    binary = args.binary.resolve(strict=True)
    data = binary.read_bytes()
    if len(data) < 20 or data[:6] != b'\x7fELF\x02\x01':
        parser.error('Expected ELF64 little-endian binary')
    machine = int.from_bytes(data[18:20], 'little')
    architectures = {62: 'x86_64', 243: 'riscv64'}
    if machine not in architectures or (args.qemu and machine != 243):
        parser.error('Wrong runtime ELF architecture')
    command = [str(binary)]
    if args.qemu:
        command = [args.qemu, '-cpu', 'rv64,v=false', '-L', str(args.sysroot.resolve()), str(binary)]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = {'schema_version': 1, 'binary_sha256': hashlib.sha256(data).hexdigest(),
              'command': command, 'timeout_seconds': args.timeout, 'host': platform.platform(),
              'evidence_class': 'functional-emulation' if args.qemu else 'native-functional',
              'timing_calibrated': False, 'power_measured': False}
    stdout = stderr = b''
    try:
        result = subprocess.run(command, capture_output=True, timeout=args.timeout)
        stdout, stderr = result.stdout, result.stderr
        report['returncode'] = result.returncode
        if result.returncode != 0 or stderr.strip():
            raise ValueError('Runtime probe failed or wrote stderr')
        report['validated'] = validate_output(stdout.decode(), expect_architecture=architectures[machine])
        report['status'] = 'pass'
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        report.update(status='fail', error='Runtime timeout', returncode=None)
    except (OSError, ValueError, UnicodeError) as exc:
        report.update(status='fail', error=str(exc))
    finally:
        (args.output_dir / 'runtime.jsonl').write_bytes(stdout)
        (args.output_dir / 'stderr.log').write_bytes(stderr)
        report['raw_sha256'] = {'runtime.jsonl': hashlib.sha256(stdout).hexdigest(),
                                'stderr.log': hashlib.sha256(stderr).hexdigest()}
        (args.output_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get('status') == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
