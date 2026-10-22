#!/usr/bin/env python3
"""UNRUN two-command analytical payload; fresh specific admission is required."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--source-manifest', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.absolute()
    require(not output.is_relative_to(source), 'output must be outside frozen source')
    require(args.source_manifest.resolve(strict=True) == source / 'SOURCE-MANIFEST01.json',
            'manifest must be the frozen source manifest')
    admitted = json.loads((output.parent / 'manifest.json').read_text())
    require(admitted.get('schema') == 'openrx.local.execution.v1' and
            admitted.get('migration_state') == 'LOCAL_ACTIVE' and
            admitted.get('cwd') == str(source), 'fresh active admission required')
    require(admitted.get('kind') == 'simulation' and admitted.get('validation_scope') is None and
            admitted.get('request_key') == 'issue72-protocol-floor-20261022-01',
            'exact proposed analytical-bundle admission required')
    require(admitted.get('runner', {}).get('sha256') ==
            '657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b',
            'pinned immutable runner required')
    argv, driver = admitted.get('argv', []), str(Path(__file__).resolve())
    require(driver in argv and argv[argv.index(driver) + 1:] == sys.argv[1:] and
            Path(argv[0]).resolve() == Path(sys.executable).resolve() and
            sys.dont_write_bytecode, 'live Python/driver argv differs')
    unit = admitted.get('unit')
    require(isinstance(unit, str) and any(unit in row.split(':', 2)[-1].split('/')
            for row in Path('/proc/self/cgroup').read_text().splitlines()),
            'driver outside admitted cgroup')
    caps = admitted.get('resources', {})
    require(caps.get('CPUQuota') == '600%' and caps.get('MemoryMax') == '1073741824' and
            caps.get('MemorySwapMax') == '2G' and caps.get('TasksMax') == 256 and
            caps.get('global_slots') == 1 and
            admitted.get('resource_profile', {}).get('name') == 'owner-local-max-v1',
            'proposed resource limits changed; outer runner verifies kernel/ancestors')
    manifest_pin = sha(args.source_manifest)
    frozen = json.loads(args.source_manifest.read_text())
    require(frozen.get('schema') == 'openrx.sram-protocol-preparation.v1' and
            frozen.get('expected_timed_commands') == 2, 'unexpected frozen source manifest')

    def check_source():
        require(sha(args.source_manifest) == manifest_pin, 'source manifest changed during payload')
        physical = set()
        for path in source.rglob('*'):
            require(not path.is_symlink(), 'symlink in frozen source')
            if path.is_file():
                physical.add(str(path.relative_to(source)))
        require(physical == set(frozen['files']) | {'SOURCE-MANIFEST01.json'},
                'frozen source file set changed')
        for rel, pin in frozen['files'].items():
            path = source / rel
            require(path.resolve(strict=True).is_relative_to(source) and
                    path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'],
                    'frozen input changed: ' + rel)

    def check_tools():
        for name, pin in json.loads((source / 'tool-bindings.json').read_text())['files'].items():
            path = Path(name)
            require(str(path.resolve(strict=True)) == pin['resolved_path'] and
                    path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'],
                    'bound tool changed: ' + name)

    check_source()
    check_tools()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    summary = {'schema': 'openrx.sram-protocol-bound.validation.v1', 'status': 'running',
               'scientific_acceptance': 'unverified_pending_independent_review',
               'physical_acceptance': False, 'commands': rows, 'commands_planned': 2,
               'new_full_hash_rtl_cacti_gem5_or_synthesis': False,
               'source_manifest_sha256': sha(args.source_manifest)}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', LC_ALL='C')
    env['PATH'] = '/usr/bin:/bin'
    env.pop('PYTHONPATH', None)
    env.pop('LD_PRELOAD', None)

    def run(name, command):
        directory = output / name
        directory.mkdir()
        started = time.monotonic()
        row = {'name': name, 'argv': command, 'cwd': str(source),
               'returncode': None, 'timed_out': False}
        rows.append(row)
        try:
            with (directory / 'stdout.txt').open('x') as stdout, (directory / 'stderr.txt').open('x') as stderr:
                process = subprocess.Popen(['/usr/bin/time', '-v', '-o', str(directory / 'time.txt'),
                                            *command], cwd=source, env=env, stdout=stdout,
                                           stderr=stderr, start_new_session=True)
                try:
                    row['returncode'] = process.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    row['timed_out'] = True
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    row['returncode'] = process.returncode
                    raise
        finally:
            row['wall_seconds'] = time.monotonic() - started
            save(directory / 'status.json', row)
            print(json.dumps(row), flush=True)
        require(row['returncode'] == 0, name + ' failed; preserve and stop without retry')

    try:
        run('protocol-bound-units', [sys.executable, '-B', '-m', 'unittest', 'discover',
                                    '-s', 'tests', '-p', 'test_sram_protocol_bound.py', '-v'])
        log = (output / 'protocol-bound-units/stderr.txt').read_text()
        count = re.findall(r'^Ran (\d+) tests? in ', log, re.MULTILINE)
        require(count == [str(frozen['expected_unit_methods'])] and
                re.search(r'^OK\s*$', log, re.MULTILINE) and
                not re.search(r'\b(skipped|FAILED|ERROR)\b', log), 'unit count/result mismatch')
        summary['actual_unit_tests'] = int(count[0])
        run('protocol-bound-report', [sys.executable, '-B', 'adapter/sram_protocol_bound.py',
            '--inputs', str(source / 'inputs'), '--registry', str(source / 'input-bindings.json'),
            '--output', str(output / 'protocol-bound-report-output')])
        report_directory = output / 'protocol-bound-report-output'
        index = json.loads((report_directory / 'artifacts.sha256.json').read_text())
        require(set(index) == {'protocol-bound.json', 'provenance.json'} and
                all(sha(report_directory / name) == digest for name, digest in index.items()),
                'report artifact index differs')
        report = json.loads((report_directory / 'protocol-bound.json').read_text())
        require(report.get('schema') == 'openrx.sram-protocol-necessary-bound.v1' and
                report.get('physical_acceptance') is False and
                report.get('scientific_acceptance') == 'unverified_pending_independent_review' and
                all(x is None for x in report['unknown'].values()), 'report scope/unknowns differ')
        summary.update(status='pass_conditional_necessary_ceilings_only', commands_completed=2)
    except BaseException as exc:
        summary.update(status='interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'failed',
                       failure_type=type(exc).__name__, failure=str(exc))
        raise
    finally:
        try:
            check_source()
            check_tools()
            summary['bound_source_tools_unchanged'] = True
        except Exception as exc:
            summary.update(status='failed', bound_source_tools_unchanged=False,
                           postcheck_failure=str(exc))
            raise
        finally:
            save(output / 'validation-summary.json', summary)


if __name__ == '__main__':
    main()
