#!/usr/bin/env python3
"""UNRUN preparation: five-command payload, usable only after fresh admission."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
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
    require(not output.is_relative_to(source), 'outputs must be outside frozen inputs')
    admitted = json.loads((output.parent / 'manifest.json').read_text())
    require(admitted.get('schema') == 'openrx.local.execution.v1' and
            admitted.get('migration_state') == 'LOCAL_ACTIVE' and
            admitted.get('cwd') == str(source), 'fresh active admission required')
    require(admitted.get('kind') == 'simulation' and admitted.get('validation_scope') is None and
            admitted.get('request_key') == 'issue72-conditional-sram-baseline-20261022-01',
            'exact proposed model/build bundle admission required')
    argv = admitted.get('argv', [])
    driver = str(Path(__file__).resolve())
    require(driver in argv and argv[argv.index(driver) + 1:] == sys.argv[1:] and
            Path(argv[0]).resolve() == Path(sys.executable).resolve() and
            sys.dont_write_bytecode, 'live Python/driver argv mismatch')
    unit = admitted.get('unit')
    require(isinstance(unit, str) and any(unit in row.split(':', 2)[-1].split('/')
            for row in Path('/proc/self/cgroup').read_text().splitlines()),
            'driver is outside its admitted cgroup')
    caps = admitted.get('resources', {})
    require(caps.get('CPUQuota') == '600%' and caps.get('MemoryMax') == '1073741824' and
            caps.get('MemorySwapMax') == '2G' and caps.get('TasksMax') == 256 and
            caps.get('global_slots') == 1, 'proposed resource limits changed')
    require(admitted.get('resource_profile', {}).get('name') == 'owner-local-max-v1',
            'pinned resource profile required; outer runner verifies kernel/ancestors')
    frozen = json.loads(args.source_manifest.read_text())
    require(frozen.get('schema') == 'openrx.conditional-memory-preparation.v1',
            'unexpected source manifest')

    def check_source():
        for rel, pin in frozen['files'].items():
            path = source / rel
            require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(source) and
                    path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'],
                    'changed frozen input: ' + rel)

    def check_tools():
        for name, pin in json.loads((source / 'tool-bindings.json').read_text())['files'].items():
            path = Path(name)
            require(path.resolve(strict=True) == Path(pin['resolved_path']) and
                    path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'],
                    'changed admitted tool: ' + name)

    check_source()
    check_tools()
    output.mkdir(parents=True, exist_ok=False)
    commands = []
    summary = {'schema': 'openrx.conditional-memory-validation.v1', 'status': 'running',
               'scientific_acceptance': 'unverified_pending_independent_review',
               'physical_acceptance': False, 'conditional_only': True, 'commands': commands,
               'source_manifest_sha256': sha(args.source_manifest),
               'new_full_hash_or_rtl_or_gem5_simulation': False}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', LC_ALL='C', OMP_NUM_THREADS='1')
    env['PATH'] = '/usr/bin:/bin'
    for key in ('MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES', 'GCC_EXEC_PREFIX', 'COMPILER_PATH',
                'CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'LIBRARY_PATH', 'LD_PRELOAD'):
        env.pop(key, None)

    def run(name, command, cwd, logdir, metadata=None):
        started = time.monotonic()
        row = {'name': name, 'argv': command, 'cwd': str(cwd), 'returncode': None,
               'timed_out': False}
        row.update(metadata or {})
        commands.append(row)
        try:
            with (logdir / 'stdout.txt').open('x') as stdout, (logdir / 'stderr.txt').open('x') as stderr:
                proc = subprocess.Popen(['/usr/bin/time', '-v', '-o', str(logdir / 'time.txt'),
                                         *command], cwd=cwd, env=env, stdout=stdout, stderr=stderr,
                                        start_new_session=True)
                try:
                    row['returncode'] = proc.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    row['timed_out'] = True
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    row['returncode'] = proc.returncode
                    raise
        finally:
            row['wall_seconds'] = time.monotonic() - started
            save(logdir / 'status.json', row)
            print(json.dumps(row), flush=True)
        require(row['returncode'] == 0, name + ' failed; stop without fallback or retry')
        return row

    try:
        unitdir = output / 'units'
        unitdir.mkdir()
        run('memory-baseline-units', [sys.executable, '-B', '-m', 'unittest', 'discover',
                                    '-s', 'tests', '-p', 'test_memory_baseline.py', '-v'],
            source, unitdir)
        log = (unitdir / 'stderr.txt').read_text()
        matches = re.findall(r'^Ran (\d+) tests? in ', log, re.MULTILINE)
        require(matches == [str(frozen['expected_unit_methods'])] and
                re.search(r'^OK\s*$', log, re.MULTILINE) and
                not re.search(r'\b(skipped|FAILED|ERROR)\b', log), 'unit count/result mismatch')
        summary['actual_unit_tests'] = int(matches[0])

        build = output / 'build' / 'cacti'
        build.parent.mkdir()
        shutil.copytree(source / 'inputs/cacti', build, copy_function=shutil.copy2)
        buildlog = output / 'build-log'
        buildlog.mkdir()
        run('build-cacti', ['/usr/bin/make', '-j1', 'NTHREADS=1', 'CXX=/usr/bin/g++',
                            'CC=/usr/bin/gcc',
                            'CXXFLAGS=-O3 -std=gnu++98 -msse2 -mfpmath=sse -DNTHREADS=1 -Wno-unknown-pragmas'],
            build, buildlog)
        binary = build / 'cacti'
        require(binary.is_file() and os.access(binary, os.X_OK), 'no executable model artifact')
        binary_pin = {'bytes': binary.stat().st_size, 'sha256': sha(binary)}
        summary['generated_binary'] = binary_pin

        spec = importlib.util.spec_from_file_location('admitted_memory_baseline',
                                                     source / 'adapter/memory_baseline.py')
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        contract = json.loads((source / 'contract.json').read_text())
        cases = output / 'cases'
        cases.mkdir()
        for case in contract['cases']:
            require(sha(binary) == binary_pin['sha256'], 'generated model binary changed')
            case_dir = cases / case['name']
            case_dir.mkdir()
            shutil.copy2(source / ('inputs/configs/' + case['name'] + '.cfg'), case_dir / 'input.cfg')
            run('model-' + case['name'], [str(binary), '-infile', str(case_dir / 'input.cfg')],
                case_dir, case_dir, {'model_binary_sha256': binary_pin['sha256']})
            # Strict static-result parsing is bounded bookkeeping, not another model run.
            adapter.validate_case(case_dir, case, contract)
        reportlog = output / 'report-log'
        reportlog.mkdir()
        run('conditional-report', [sys.executable, '-B', 'adapter/memory_baseline.py',
            '--contract', str(source / 'contract.json'), '--inputs', str(source / 'inputs'),
            '--cases', str(cases), '--output', str(output / 'conditional-report')], source, reportlog)
        require(sha(binary) == binary_pin['sha256'], 'generated model binary changed')
        for rel, pin in contract['source_files'].items():
            if rel.startswith('cacti/'):
                require(sha(build / rel.removeprefix('cacti/')) == pin['sha256'],
                        'source modified in writable build copy: ' + rel)
        summary.update(status='pass_conditional_model_only', commands_completed=len(commands))
    except BaseException as exc:
        summary.update(status='interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'failed',
                       failure_type=type(exc).__name__, failure=str(exc))
        raise
    finally:
        try:
            check_source()
            check_tools()
            summary['bound_inputs_tools_unchanged'] = True
        except Exception as exc:
            summary['bound_inputs_tools_unchanged'] = False
            summary['postcheck_failure'] = str(exc)
            summary['status'] = 'failed'
            raise
        finally:
            save(output / 'validation-summary.json', summary)


if __name__ == '__main__':
    main()
