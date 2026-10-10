"""Fixed owner CLI: observe pinned gem5, request stop, retain truthful evidence.

This controller never activates infrastructure, changes scientific criteria,
resumes simulations, or posts to GitHub. Supply the independently reviewed
request SHA256. Reentry adopts an existing request; it never duplicates a run.
"""
from pathlib import Path
import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import select
import signal
import stat
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
R = Path('$OPENRX_LOCAL_ROOT')
E = R / 'migrations/20261009'
S = None  # Bound only from the exact owner-reviewed request.
B = E / 'build-attempt-03'
G = R / 'builds/gem5-rebuild-03/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt'
RES = R / 'artifacts/guest-resources-ranged-20261009'
ELF = R / 'artifacts/guest-20261008/openrx-runtime-probe'
PREFLIGHT = E / 'local-validation-preflight.json'
FIRST_CAPTURE = E / 'runtime-capture-summary.json'
KEY = 'issue-27-gem5-stop-migration-attempt-01'
SPEC = R / ('requests/spec-' + KEY + '.json')
WORK = E / 'gem5-stop-proof-attempt-01'
SOURCE_COMMIT = None
CONFIG_SHA = 'f839a59b33a593a63c3f5bef53bfac468df0619fcc46c3583c76b08b2d08564c'
RESOURCES_SHA = '67c3838d04b617b3a4f34a874f84cc2c5517eca51c9049456bc6df19312404bb'
ELF_SHA = '8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    require(not path.is_symlink() and path.is_file(), 'Missing regular file: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(4 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def binding(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def newjson(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as out:
        out.write(json.dumps(value, sort_keys=True, indent=2) + '\n')
        out.flush()
        os.fsync(out.fileno())
    syncdir(path.parent)


def mkdir(path):
    require(not path.is_symlink(), 'Evidence directory is a symlink')
    path.mkdir(mode=0o700, exist_ok=True)
    syncdir(path)
    syncdir(path.parent)


def readjson(path):
    return json.loads(path.read_text())


def checked(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    require(result.returncode == 0, 'Command failed: ' + repr(command) + '; ' + result.stderr)
    return result.stdout


def cgroup_state(relative):
    if not relative:
        return {'present': False, 'populated': False, 'pids': []}
    require(relative.startswith('/') and '..' not in Path(relative).parts, 'Invalid manager cgroup path')
    directory = Path('/sys/fs/cgroup') / relative.lstrip('/')
    if not directory.exists():
        return {'path': str(directory), 'present': False, 'populated': False, 'pids': []}
    pids = sorted({int(pid) for procs in directory.rglob('cgroup.procs') for pid in procs.read_text().split()})
    text = (directory / 'cgroup.events').read_text()
    return {'path': str(directory), 'present': True, 'populated': 'populated 1' in text, 'pids': pids}


def observe_gem5(relative):
    expected = G.stat()
    for pid in cgroup_state(relative)['pids']:
        fd = None
        try:
            fd = os.pidfd_open(pid)
            poller = select.poll()
            poller.register(fd, select.POLLIN)
            if poller.poll(0):
                continue
            actual = Path('/proc') / str(pid)
            exe = (actual / 'exe').stat()
            if (exe.st_dev, exe.st_ino) != (expected.st_dev, expected.st_ino):
                continue
            require((actual / 'exe').resolve() == G.resolve(), 'Observed executable path mismatch')
            membership = (actual / 'cgroup').read_text().splitlines()
            require(any(line == '0::' + relative or line.startswith('0::' + relative + '/')
                        for line in membership), 'Observed process outside service cgroup')
            if poller.poll(0):
                continue
            observation = {'pid': pid, 'exe': str((actual / 'exe').resolve()),
                           'exe_device': exe.st_dev, 'exe_inode': exe.st_ino,
                           'cgroup': relative, 'pidfd_opened_while_live': True,
                           'proc_stat': (actual / 'stat').read_text(),
                           'commandline': (actual / 'cmdline').read_bytes().replace(b'\x00', b' ').decode(),
                           'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            returned = fd
            fd = None
            return returned, observation
        except (FileNotFoundError, ProcessLookupError):
            pass
        finally:
            if fd is not None:
                os.close(fd)
    return None, None


def prerequisites(request_sha):
    global S, SOURCE_COMMIT
    require(re.fullmatch('[0-9a-f]{64}', request_sha), 'Expected request SHA must be exactly 64 lowercase hexadecimal characters')
    require(sha(SPEC) == request_sha, 'Owner-reviewed request changed')
    spec = readjson(SPEC)
    require(spec.get('schema') == 'openrx.local.request.v1' and spec.get('request_key') == KEY and
            spec.get('kind') == 'validation' and
            spec.get('validation_scope') == 'guest-runtime-smoke', 'Fixed owner request identity/scope mismatch')
    require(sha(Path(__file__).resolve()) == spec['controller_sha256'], 'Owner-reviewed controller changed')
    SOURCE_COMMIT = spec['source_commit']
    require(re.fullmatch('[0-9a-f]{40}', SOURCE_COMMIT), 'Source commit must be exact lowercase hexadecimal')
    checkout = Path(spec['execution_checkout_relative'])
    require(not checkout.is_absolute() and '..' not in checkout.parts and len(checkout.parts) == 2 and
            checkout.parts[0] == 'checkouts' and checkout.name == 'execution-' + SOURCE_COMMIT[:7],
            'Scientific source must be the declared frozen execution checkout')
    S = R / checkout
    release = Path(spec['runner_release_relative'])
    require(not release.is_absolute() and '..' not in release.parts and release.parts[0] == 'releases' and
            release.name == 'local_execution.py', 'Runner must be a reviewed local release')
    runner_path = R / release
    require(re.fullmatch('[0-9a-f]{64}', spec['runner_sha256']) and sha(runner_path) == spec['runner_sha256'], 'Reviewed runner release changed')
    loader = importlib.util.spec_from_file_location('openrx_reviewed_local_runner', runner_path)
    runner = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(runner)
    require(runner.current_state(R) == 'LOCAL_VALIDATING', 'Stop proof requires actual LOCAL_VALIDATING state')
    preflight = readjson(PREFLIGHT)
    require(preflight.get('state') == 'LOCAL_VALIDATING' and preflight.get('source_commit') == SOURCE_COMMIT and
            preflight.get('runner_sha256') == spec['runner_sha256'] and preflight.get('guest_resources_verified') is True and
            preflight.get('new_binary_pinned') is True, 'Successful preflight unavailable or mismatched')
    latest = runner.events(R / 'state/events.jsonl')[-1]
    require(latest.get('evidence', {}).get('sha256') == sha(PREFLIGHT), 'Authoritative transition does not bind this preflight')
    build = readjson(B / 'build-result.json')
    require(build.get('returncode') == 0 and not build.get('source_changed') and build.get('build-info_exit') == 0 and
            build.get('loader_exit') == 0 and build.get('config_sha256_after') == CONFIG_SHA, 'Simulator build not verified')
    require(preflight.get('build_result_sha256') == sha(B / 'build-result.json') and
            preflight.get('build', {}).get('binary_sha256') == build['binary_sha256'] and
            sha(G) == build['binary_sha256'] and G.stat().st_size == build['binary_bytes'], 'Pinned simulator identity changed')
    require(sha(G.parent / 'gem5.build/config') == CONFIG_SHA and sha(B / 'canonical-config') == CONFIG_SHA, 'Simulator build configuration changed')
    require(checked(['git', 'rev-parse', 'HEAD'], S).strip() == SOURCE_COMMIT and
            not checked(['git', 'status', '--porcelain', '--untracked-files=all'], S).strip(), 'Frozen scientific source changed')
    for path in (S, *S.rglob('*')):
        require(not path.is_symlink() and not (path.stat().st_mode & 0o222), 'Frozen source became writable or linked: ' + str(path))
    require(sha(S / 'simulator/gem5/run.py') == spec['simulator_wrapper_sha256'], 'Reviewed simulator wrapper changed')
    require(sha(S / 'simulator/gem5/resources.json') == RESOURCES_SHA and sha(ELF) == ELF_SHA and
            preflight.get('guest_runtime_sha256') == ELF_SHA, 'Essential guest input pin changed')
    resources = readjson(S / 'simulator/gem5/resources.json')
    for item in resources['resources']:
        path = RES / item['filename']
        require(path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], 'Guest resource changed: ' + str(path))
    profile_dir = R / ('toolchains/gem5-runtime-' + build['binary_sha256'][:12])
    profile_path = profile_dir / 'runtime-libraries.json'
    require(sha(profile_path) == preflight.get('runtime_library_profile_sha256'), 'Verified runtime library profile changed')
    profile = readjson(profile_path)
    require(profile.get('binary_sha256') == build['binary_sha256'], 'Runtime library profile belongs to a different simulator')
    for item in profile['libraries']:
        copy = Path(item['pinned_copy'])
        require(copy.parent == profile_dir / 'lib' and sha(copy) == item['sha256'] and
                copy.stat().st_size == item['bytes'], 'Pinned runtime library changed')
        if item.get('interpreter'):
            require(sha(Path(item['host_path'])) == item['sha256'], 'Host ELF interpreter changed')
    first = readjson(FIRST_CAPTURE)
    require(first.get('request_key') == preflight.get('request_key') and first.get('receipt_sha256') ==
            sha(R / 'executions' / first['execution_id'] / 'receipt.json'), 'Required first capture receipt missing or changed')
    runner.verify(R, first['execution_id'])
    return runner, runner_path, profile_dir, resources, preflight, first


def execute(request_sha, attempt):
    evidence = {'schema': 'openrx.gem5.stop-proof.v1', 'accepted': False, 'missing_proof': [],
                'scientific_acceptance': 'unverified; expected interruption is not a scientific pass',
                'migration_complete': False, 'resume_verified': False,
                'limitations': ['No graceful gem5 stats/checkpoint finalization is claimed',
                                'No complete guest boot or runtime acceptance is inferred from this stop test',
                                'No host reboot or full Codex daemon termination is tested']}
    pidfd = None
    try:
        runner, runner_path, profile_dir, resources, preflight, first = prerequisites(request_sha)
        argv = ['/usr/bin/python3', 'simulator/gem5/run.py', '--gem5', str(G), '--resources', str(RES),
                '--runtime-binary', str(ELF), '--output-dir', '{execution_dir}/payload',
                '--max-ticks', '10000000000000', '--stop-file', '{execution_dir}/stop.request']
        command = ['/usr/bin/python3', str(runner_path), '--root', str(R), 'submit', '--request-key', KEY,
                   '--kind', 'validation', '--validation-scope', 'guest-runtime-smoke', '--cwd', str(S)]
        declared_inputs = [G, ELF, RES / 'opensbi', RES / 'vmlinux', RES / 'ubuntu.img', profile_dir, SPEC,
                           PREFLIGHT, Path(__file__).resolve()]
        for path in declared_inputs:
            command.extend(['--input', str(path)])
        command += ['--source', str(S), '--env', 'LD_LIBRARY_PATH=' + str(profile_dir / 'lib'), '--', *argv]
        newjson(attempt / 'fixed-submission-command.json', {'argv': command, 'request': binding(SPEC),
                  'controller': binding(Path(__file__).resolve()), 'preflight': binding(PREFLIGHT),
                  'first_capture': binding(FIRST_CAPTURE)})
        request_path = R / 'requests' / (hashlib.sha256(KEY.encode()).hexdigest() + '.json')
        if request_path.exists():
            execution_id = readjson(request_path)['execution_id']
            newjson(attempt / 'adopted-existing-request.json', {'execution_id': execution_id,
                       'reason': 'Fixed key already claimed; no new submission or restart'})
        else:
            output = checked(command)
            execution_id = json.loads(output)['execution_id']
            newjson(attempt / 'submitted-new-request.json', {'execution_id': execution_id, 'stdout': output})
        directory = runner.execution_dir(R, execution_id)
        manifest = readjson(directory / 'manifest.json')
        expected_argv = [str(Path(argv[0]).resolve())] + [word.replace('{execution_dir}', str(directory)) for word in argv[1:]]
        require(manifest['request_key'] == KEY and manifest['kind'] == 'validation' and
                manifest['validation_scope'] == 'guest-runtime-smoke' and manifest['cwd'] == str(S) and
                manifest['argv'] == expected_argv and manifest['runner']['sha256'] == sha(runner_path), 'Stored fixed request manifest mismatch')
        require(manifest['env'] == dict(runner.DEFAULT_ENV, LD_LIBRARY_PATH=str(profile_dir / 'lib')) and
                {item['path'] for item in manifest['inputs']} == {str(path) for path in declared_inputs} and
                len(manifest['inputs']) == len(declared_inputs) and
                len(manifest['sources']) == 1 and manifest['sources'][0]['path'] == str(S),
                'Stored manifest must bind the entire declared input/source/environment set')
        runner.check_bindings(R, directory, manifest)
        evidence.update(execution_id=execution_id, manifest=binding(directory / 'manifest.json'))
        marker = directory / 'stop.request'
        initial_cgroup = None
        while True:
            unit = runner.unit_status(manifest['unit'])
            require(unit.get('query_returncode') == 0, 'Cannot inspect manager safely')
            relative = unit.get('ControlGroup')
            if relative:
                require(relative.endswith('/' + manifest['unit']), 'Manager cgroup is not this execution service')
                initial_cgroup = relative
                pidfd, observation = observe_gem5(relative)
                if observation:
                    newjson(attempt / 'observed-live-pinned-gem5.json', observation)
                    evidence['actual_simulator_observed'] = observation
                    if not marker.exists():
                        newjson(marker, {'schema': 'openrx.owner.stop-request.v1', 'execution_id': execution_id,
                              'observed_live_simulator': observation, 'controller': binding(Path(__file__).resolve()),
                              'request_sha256': request_sha, 'reason': 'Declared migration stop lifecycle proof'})
                        evidence['marker_created_after_live_observation'] = True
                        newjson(attempt / 'created-stop-marker.json', binding(marker))
                    else:
                        evidence['marker_created_after_live_observation'] = False
                        evidence['missing_proof'].append('Marker already existed on this controller attempt; creation timing cannot be inferred')
                    break
            if unit.get('ActiveState') in {'inactive', 'failed'}:
                evidence['missing_proof'].append('Service finished before this attempt observed a live pinned simulator')
                break
            time.sleep(0.2)
        while True:
            final_unit = runner.unit_status(manifest['unit'])
            require(final_unit.get('query_returncode') == 0, 'Cannot inspect manager completion safely')
            if final_unit.get('ActiveState') in {'inactive', 'failed'}:
                break
            time.sleep(0.2)  # polling interval, never an experiment wall timeout
        if pidfd is not None:
            poller = select.poll()
            poller.register(pidfd, select.POLLIN)
            evidence['observed_process_pidfd_exit'] = bool(poller.poll(0))
        else:
            evidence['observed_process_pidfd_exit'] = False
        evidence['final_unit'] = final_unit
        evidence['final_cgroup'] = cgroup_state(initial_cgroup or final_unit.get('ControlGroup'))
        require(not evidence['final_cgroup']['populated'] and not evidence['final_cgroup']['pids'], 'Service cgroup retains processes')
        runner.recover(R, execution_id)
        evidence['output_integrity'] = runner.verify(R, execution_id)
        # Independent controller checks remain mandatory when terminal framing
        # caused run.py to return before reaching its own post-execution hashes.
        runner.check_bindings(R, directory, manifest)
        evidence['stored_inputs_sources_runner_and_request_unchanged'] = True
        evidence['receipt'] = binding(directory / 'receipt.json')
        report_path = directory / 'payload/report.json'
        require(report_path.exists(), 'Missing scientific wrapper interruption report')
        report = readjson(report_path)
        evidence['wrapper_report'] = binding(report_path)
        evidence['report_controls'] = {key: report.get(key) for key in ('status', 'interrupted', 'interruption_source',
                  'stop_file_observed', 'child_returncode', 'runtime_validated', 'boot_observed', 'error')}
        require(report.get('status') == 'fail' and report.get('interrupted') is True and
                report.get('interruption_source') == 'stop-file' and report.get('stop_file_observed') is True and
                report.get('child_returncode') == -signal.SIGKILL, 'Exact declared stop-file interruption controls missing')
        require(report.get('stop_file') == str(marker) and report.get('gem5_binary_sha256') == preflight['build']['binary_sha256'] and
                report.get('config_sha256') == sha(S / 'simulator/gem5/fs.py') and
                report.get('resource_manifest_sha256') == RESOURCES_SHA, 'Wrapper simulator/config/resource bindings mismatch')
        expected_command = [str(G), '--outdir=' + str(directory / 'payload/m5out'), str(S / 'simulator/gem5/fs.py'),
                            '--resources', str(RES), '--readfile', str(directory / 'payload/guest.sh'),
                            '--max-ticks', '10000000000000']
        require(report.get('command') == expected_command and report.get('max_ticks_per_simulate_call') == 10000000000000 and
                report.get('hash_controls_requested') is False and report.get('full_dataset') is False and
                report.get('timeout_seconds') is None, 'Wrapper command/scope/tick controls changed')
        guest = report.get('guest_binaries', {}).get('runtime', {})
        require(guest.get('path') == str(ELF) and guest.get('sha256') == ELF_SHA and guest.get('bytes') == ELF.stat().st_size, 'Wrapper runtime ELF binding mismatch')
        require(report.get('readfile_sha256') == sha(directory / 'payload/guest.sh'), 'Guest readfile binding mismatch')
        observed = {item['role']: item for item in report.get('resources', [])}
        for item in resources['resources']:
            record = observed.get(item['role'], {})
            require(record.get('sha256') == item['sha256'] and record.get('observed', {}).get('sha256') == item['sha256'] and
                    record.get('observed', {}).get('bytes') == item['bytes'] and record.get('observed', {}).get('md5') == item['upstream_md5'],
                    'Wrapper resource binding incomplete: ' + item['role'])
        terminals = list((directory / 'payload/m5out').glob('*terminal*'))
        evidence['wrapper_postcheck_limit'] = ('A unique terminal exists; controller nevertheless independently rechecked every bound input' if len(terminals) == 1
                  else 'Wrapper terminal check may have preceded its posthash checks; controller independently rechecked all bound inputs/sources')
        require(evidence.get('marker_created_after_live_observation') is True and
                evidence['observed_process_pidfd_exit'] is True and not evidence['missing_proof'], 'Live-process creation/exit evidence incomplete')
        evidence['accepted'] = True
    except (ValueError, OSError, KeyError, TypeError) as exc:
        evidence['missing_proof'].append(str(exc))
    finally:
        if pidfd is not None:
            os.close(pidfd)
        evidence['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        newjson(attempt / 'stop-proof-receipt.json', evidence)
    print(json.dumps(evidence, sort_keys=True, indent=2))
    return 0 if evidence['accepted'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-sha256', required=True, help='Exact independently reviewed owner request SHA256')
    args = parser.parse_args()
    mkdir(WORK)
    fd = os.open(WORK / 'controller.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempts = WORK / 'attempts'
        mkdir(attempts)
        attempt = attempts / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:12])
        attempt.mkdir(mode=0o700)
        syncdir(attempt)
        syncdir(attempts)
        return execute(args.request_sha256, attempt)
    finally:
        os.close(fd)


if __name__ == '__main__':
    sys.exit(main())
