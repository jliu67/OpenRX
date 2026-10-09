#!/usr/bin/python3
"""Reviewable final988 host-only lifecycle replay. Explicit execution required."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE / 'fixture-root'
SELF = Path(__file__).resolve()
PAYLOAD = BASE / 'toy_payload.py'
PLAN = BASE / 'plan-v2.json'
RELEASE = Path('$OPENRX_LOCAL_ROOT/releases/runner-v1-988cf13f/local_execution.py')
RUNNER_SHA = '988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882'
PROPS = ('LoadState', 'ActiveState', 'SubState', 'Result', 'MainPID', 'ControlPID',
         'ExecMainCode', 'ExecMainStatus', 'ControlGroup', 'MemoryMax',
         'MemorySwapMax', 'CPUQuotaPerSecUSec', 'TasksMax', 'Nice', 'NoNewPrivileges',
         'KillMode', 'KillSignal', 'TimeoutStopUSec', 'SendSIGKILL', 'Restart',
         'NotifyAccess', 'UMask')
EXPECTED = {'MemorySwapMax': '0', 'CPUQuotaPerSecUSec': '100ms', 'TasksMax': '16',
            'Nice': '10', 'NoNewPrivileges': 'yes', 'KillMode': 'mixed',
            'KillSignal': '2', 'TimeoutStopUSec': '45s', 'SendSIGKILL': 'yes',
            'Restart': 'no', 'NotifyAccess': 'exec', 'UMask': '0077'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def binding(path):
    require(not path.is_symlink() and path.is_file(), f'Nonregular bound file: {path}')
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def newjson(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    os.fsync(fd)
    os.close(fd)


def readjson(path):
    return json.loads(path.read_text())


def command(argv):
    result = subprocess.run(argv, capture_output=True, text=True)
    return {'argv': argv, 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def checked_inputs(args):
    require(binding(SELF)['sha256'] == args.expected_self_sha256, 'Replay source binding mismatch')
    require(binding(PLAN)['sha256'] == args.expected_plan_sha256, 'Replay plan binding mismatch')
    plan = readjson(PLAN)
    require(plan['fixture_root'] == str(ROOT), 'Unexpected fixture root')
    require(plan['runner']['sha256'] == RUNNER_SHA and binding(RELEASE) == plan['runner'],
            'Installed runner no longer equals the reviewed final988 release')
    require({item['path'] for item in plan['files']} == {str(SELF), str(PAYLOAD)},
            'Unexpected fixture file inventory')
    for item in plan['files']:
        require(binding(Path(item['path'])) == item, f'Fixture input changed: {item["path"]}')
    return plan


def load_runner():
    spec = importlib.util.spec_from_file_location('final988_lifecycle_release', RELEASE)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    original = runner.systemd_command

    def reduced_command(root, directory, manifest):
        require(Path(root) == ROOT, 'Fixture override attempted outside the isolated root')
        default = original(root, directory, manifest)
        memory = '48M' if manifest['request_key'].endswith('-oom') else '64M'
        replacement = {'--property=MemoryMax=6G': '--property=MemoryMax=' + memory,
                       '--property=MemorySwapMax=1G': '--property=MemorySwapMax=0',
                       '--property=CPUQuota=200%': '--property=CPUQuota=10%',
                       '--property=TasksMax=256': '--property=TasksMax=16'}
        actual = [replacement.get(item, item) for item in default]
        newjson(BASE / (manifest['request_key'] + '-service-command.json'), {
            'execution_id': manifest['execution_id'], 'production_default': default,
            'actual_fixture_command': actual,
            'scope': 'Only submission resource properties overridden for tiny host-only controls; snapshot worker and private finalizer are exact final988 bytes.',
            'manifest_resource_note': 'Manifest records the unmodified production baseline 6G/1G/CPU200/Tasks256. Actual fixture limits are explicit here and in observed properties.'})
        return actual

    runner.systemd_command = reduced_command
    return runner


def submit(runner, name, mode):
    return runner.submit(ROOT, 'final988-' + name, 'validation', BASE,
                         ['/usr/bin/python3', str(PAYLOAD), mode, '{execution_dir}/payload'],
                         [PAYLOAD, SELF, PLAN], [RELEASE], validation_scope='lifecycle')


def properties(unit):
    result = command(['systemctl', '--user', 'show', unit, '--property=' + ','.join(PROPS)])
    return {**result, 'properties': dict(line.split('=', 1) for line in result['stdout'].splitlines() if '=' in line)}


def history(runner, directory):
    return runner.events(directory / 'events.jsonl')


def manager_wait_state(sample):
    require(sample['returncode'] == 0, 'Manager query failed; preserve and inspect without inferring state')
    props = sample['properties']
    require(props.get('LoadState') in {'loaded', 'not-found'}, 'Unknown unit load state')
    require(props.get('ActiveState') in {'active', 'activating', 'deactivating', 'reloading', 'inactive', 'failed'},
            'Unknown unit active state')
    return props


def wait_evidence(runner, eid, predicate, description):
    directory = runner.execution_dir(ROOT, eid)
    manifest = readjson(directory / 'manifest.json')
    while True:
        if predicate(directory):
            return directory
        props = manager_wait_state(properties(manifest['unit']))
        # Recheck after the query: the child may have produced evidence and
        # exited between the first predicate and the observed manager state.
        if predicate(directory):
            return directory
        require(not (directory / 'receipt.json').exists(),
                f'Finalized fixture missing {description}: {eid}')
        require(props['ActiveState'] not in {'inactive', 'failed'},
                f'Terminal fixture missing {description}, including any finalizer failure: {eid}')
        time.sleep(0.1)


def wait_started(runner, eid):
    return wait_evidence(runner, eid,
                         lambda directory: any(item.get('status') == 'CHILD_STARTED'
                                               for item in history(runner, directory)),
                         'CHILD_STARTED evidence')


def wait_payload(runner, eid, relative):
    wait_started(runner, eid)
    return wait_evidence(runner, eid, lambda directory: (directory / 'payload' / relative).exists(),
                         'payload/' + relative)


def observed_resources(runner, eid, memory=64):
    directory = wait_started(runner, eid)
    manifest = readjson(directory / 'manifest.json')
    sample = properties(manifest['unit'])
    actual = sample['properties']
    require(sample['returncode'] == 0 and actual.get('LoadState') == 'loaded', 'Fixture unit not inspectable')
    for key, value in {**EXPECTED, 'MemoryMax': str(memory * 1024 * 1024)}.items():
        require(actual.get(key) == value, f'Actual fixture property mismatch: {key}: {actual.get(key)!r}')
    require(actual.get('ActiveState') == 'active' and int(actual.get('MainPID', '0')) > 0,
            'Expected live fixture worker')
    group = actual.get('ControlGroup', '')
    require(group.endswith('/' + manifest['unit']), 'Unit cgroup name not bound to execution ID')
    newjson(BASE / (manifest['request_key'] + '-actual-properties.json'), sample)
    return actual


def cgroup_empty(group):
    path = Path('/sys/fs/cgroup') / group.lstrip('/')
    if not path.exists():
        return {'path': str(path), 'present': False, 'empty': True}
    pids = sorted({int(pid) for child in path.rglob('cgroup.procs') for pid in child.read_text().split()})
    events = (path / 'cgroup.events').read_text()
    return {'path': str(path), 'present': True, 'pids': pids, 'events': events,
            'empty': not pids and 'populated 0' in events}


def finalized(runner, eid, group=None):
    directory = runner.execution_dir(ROOT, eid)
    manifest = readjson(directory / 'manifest.json')
    while True:
        sample = properties(manifest['unit'])
        props = manager_wait_state(sample)
        terminal = props.get('LoadState') in {'loaded', 'not-found'} and props.get('ActiveState') in {'inactive', 'failed'}
        if terminal:
            require((directory / 'receipt.json').exists(), f'Terminal fixture missing final receipt: {eid}')
            verified = runner.verify(ROOT, eid)
            receipt = readjson(directory / 'receipt.json')
            require(verified['integrity_verified'] and receipt['scientific_acceptance'] == 'unverified'
                    and receipt['resume_allowed'] is False, 'Unexpected integrity/scientific/resume status')
            require(binding(directory / 'runner.py')['sha256'] == RUNNER_SHA, 'Executed runner snapshot differs')
            require(any(Path(item['path']).name == 'submission-result.json' for item in receipt['artifacts']),
                    'Fast finalizer omitted durable submission result')
            runner.check_bindings(ROOT, directory, manifest)
            group = group or props.get('ControlGroup')
            require(group is not None and group.endswith('/' + manifest['unit']), 'Missing named cgroup evidence')
            empty = cgroup_empty(group)
            require(empty['empty'], 'Finalized unit retains processes')
            return {'execution_id': eid, 'unit': manifest['unit'], 'receipt': binding(directory / 'receipt.json'),
                    'integrity': verified, 'process': receipt['process'], 'systemd': receipt['systemd'],
                    'terminal_properties': sample, 'final_cgroup': empty}
        time.sleep(0.1)


def observe_pid(pid, group):
    fd = os.pidfd_open(pid)
    try:
        require(not select.select([fd], [], [], 0)[0], 'Observed process already exited')
        membership = Path(f'/proc/{pid}/cgroup').read_text()
        require(any(line == '0::' + group or line.startswith('0::' + group + '/')
                    for line in membership.splitlines()), 'Observed process outside bound service cgroup')
        return fd, {'pid': pid, 'membership': membership,
                    'stat': Path(f'/proc/{pid}/stat').read_text(), 'pidfd_live': True}
    except BaseException:
        os.close(fd)
        raise


def execute(runner, plan):
    require(not ROOT.exists(), 'Fixture root already exists; inspect/recover retained executions rather than replaying keys')
    require(not (BASE / 'replay-receipt.json').exists(), 'Replay receipt already exists')
    runner.init(ROOT)
    cases = []
    active = []
    start = runner.now()
    parent_group = None
    try:
        eid = submit(runner, 'stop-detached', 'detached')
        active.append(eid)
        directory = wait_payload(runner, eid, 'detached-child.json')
        actual = observed_resources(runner, eid)
        parent_group = str(Path(actual['ControlGroup']).parent)
        child = readjson(directory / 'payload' / 'detached-child.json')['pid']
        fd, live = observe_pid(child, actual['ControlGroup'])
        try:
            wait_payload(runner, eid, 'detached-child-output/ready.json')
            wait_evidence(runner, eid,
                          lambda directory: (directory / 'stdout.log').exists()
                          and 'heartbeat' in (directory / 'stdout.log').read_text(),
                          'inspectable partial heartbeat logs before stop')
            before = (directory / 'stdout.log').read_text()
            stop_result = runner.stop(ROOT, eid)
            result = finalized(runner, eid, actual['ControlGroup'])
            require(result['integrity']['status'] == 'INTERRUPTED', 'Safe-stop control did not record interruption')
            require(signal.SIGINT in result['process']['signals'], 'Safe stop did not record worker signal')
            require(bool(select.select([fd], [], [], 0)[0]), 'Detached descendant did not exit')
            require((directory / 'stdout.log').read_text().startswith(before), 'Partial logs lost on stop')
            cases.append({'case': 'safe-stop-detached-descendant', **result, 'live_descendant': live,
                          'pidfd_observed_exit': True, 'stop': stop_result, 'partial_log_before': before})
        finally:
            os.close(fd)

        for number in range(3):
            eid = submit(runner, 'instant-' + str(number), 'instant')
            active.append(eid)
            group = parent_group + '/' + readjson(runner.execution_dir(ROOT, eid) / 'manifest.json')['unit']
            result = finalized(runner, eid, group)
            require(result['integrity']['status'] == 'PROCESS_EXITED' and result['process']['returncode'] == 0,
                    'Instant-exit control failed')
            cases.append({'case': 'instant-exit-admission-finalizer-race', **result})

        eid = submit(runner, 'exit-seven', 'exit-seven')
        active.append(eid)
        group = parent_group + '/' + readjson(runner.execution_dir(ROOT, eid) / 'manifest.json')['unit']
        result = finalized(runner, eid, group)
        require(result['integrity']['status'] == 'PROCESS_FAILED' and result['process']['returncode'] == 7,
                'Intentional rc7 failure was falsely accepted as success')
        cases.append({'case': 'intentional-nonzero-failure', **result})

        eid = submit(runner, 'worker-killed', 'detached')
        active.append(eid)
        directory = wait_payload(runner, eid, 'detached-child-output/ready.json')
        actual = observed_resources(runner, eid)
        child = readjson(directory / 'payload' / 'detached-child.json')['pid']
        fd, live = observe_pid(child, actual['ControlGroup'])
        try:
            unit = readjson(directory / 'manifest.json')['unit']
            killed = command(['systemctl', '--user', 'kill', '--kill-who=main', '--signal=SIGKILL', unit])
            newjson(BASE / 'worker-hard-kill-command.json', killed)
            require(killed['returncode'] == 0, 'Manager could not kill named worker')
            result = finalized(runner, eid, actual['ControlGroup'])
            require(result['integrity']['status'] == 'INTERRUPTED_UNREAPED' and result['process'] is None,
                    'Hard-killed worker fabricated child exit/reaping')
            require(result['systemd']['SERVICE_RESULT'] == 'signal', 'Manager signal failure was not retained')
            require(bool(select.select([fd], [], [], 0)[0]), 'Hard-kill manager cleanup left detached child alive')
            recovery = runner.recover(ROOT, eid)
            require(recovery['integrity_verified'] and recovery['status'] == 'INTERRUPTED_UNREAPED',
                    'Recovery changed scientific or process outcome')
            cases.append({'case': 'worker-sigkill-inspect-recover', **result, 'live_descendant': live,
                          'pidfd_observed_exit': True, 'recovery': recovery})
        finally:
            os.close(fd)

        eid = submit(runner, 'oom', 'oom')
        active.append(eid)
        directory = wait_payload(runner, eid, 'ready.json')
        actual = observed_resources(runner, eid, memory=48)
        newjson(directory / 'payload' / 'allocate.request', {'scope': 'intentional host-only 48MiB cgroup OOM'})
        result = finalized(runner, eid, actual['ControlGroup'])
        require(result['systemd']['SERVICE_RESULT'] == 'oom-kill', 'Synthetic allocation did not demonstrate cgroup OOM')
        require(result['integrity']['status'] != 'PROCESS_EXITED', 'OOM was incorrectly recorded as successful')
        cases.append({'case': 'fixture-only-small-budget-oom', **result,
                      'actual_fixture_limits': {'MemoryMax': '48M', 'MemorySwapMax': 0}})

        launcher = subprocess.Popen([
            '/usr/bin/python3', str(SELF), '--launch-one',
            '--expected-self-sha256', binding(SELF)['sha256'],
            '--expected-plan-sha256', binding(PLAN)['sha256']],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        launcher_pid = launcher.pid
        output, error = launcher.communicate()
        newjson(BASE / 'independent-launcher-result.json', {
            'pid': launcher_pid, 'returncode': launcher.returncode, 'stdout': output, 'stderr': error,
            'start_new_session': True, 'launching_process_reaped': True})
        require(launcher.returncode == 0, 'Independent launching process failed')
        eid = output.strip()
        active.append(eid)
        directory = wait_payload(runner, eid, 'ready.json')
        actual = observed_resources(runner, eid)
        fd, live = observe_pid(int(actual['MainPID']), actual['ControlGroup'])
        try:
            parent = int(next(line for line in Path(f'/proc/{actual["MainPID"]}/status').read_text().splitlines()
                              if line.startswith('PPid:')).split()[1])
            parent_command = Path(f'/proc/{parent}/cmdline').read_bytes().replace(b'\0', b' ').decode()
            require('systemd' in parent_command and '--user' in parent_command, 'Worker not parented by user systemd')
            require(not Path(f'/proc/{launcher_pid}').exists(), 'Launching process still present')
            before = (directory / 'stdout.log').read_text()
            wait_evidence(runner, eid,
                          lambda directory: (directory / 'stdout.log').exists()
                          and (directory / 'stdout.log').read_text() != before,
                          'log progress after launching process/session exited')
            after = (directory / 'stdout.log').read_text()
            observation = {'launcher_pid': launcher_pid, 'launcher_absent': True,
                           'main_live': live, 'parent_pid': parent, 'parent_command': parent_command,
                           'stdout_before': before, 'stdout_after': after}
            newjson(BASE / 'session-independence-observation.json', observation)
            runner.stop(ROOT, eid)
            result = finalized(runner, eid, actual['ControlGroup'])
            require(result['integrity']['status'] == 'INTERRUPTED', 'Independent job stop did not preserve interruption')
            cases.append({'case': 'launching-process-session-exited-service-progressed', **result,
                          'observation': observation,
                          'limitation': 'Launching process/session was ended; no active Codex daemon shutdown or physical host reboot performed.'})
        finally:
            os.close(fd)

        first = submit(runner, 'serialize-first', 'detached')
        active.append(first)
        first_directory = wait_payload(runner, first, 'detached-child-output/ready.json')
        actual = observed_resources(runner, first)
        descendant_pid = readjson(first_directory / 'payload' / 'detached-child.json')['pid']
        fd, live = observe_pid(descendant_pid, actual['ControlGroup'])
        try:
            second = submit(runner, 'serialize-second', 'instant')
            active.append(second)
            second_directory = runner.execution_dir(ROOT, second)
            second_unit = readjson(second_directory / 'manifest.json')['unit']
            while True:
                sample = properties(second_unit)
                props = manager_wait_state(sample)
                if props.get('ActiveState') == 'active' and int(props.get('MainPID', '0')) > 0:
                    break
                require(not (second_directory / 'receipt.json').exists(), 'Second unit ended before queue observation')
                require(props['ActiveState'] not in {'inactive', 'failed'},
                        'Second unit terminated before queued worker observation')
                time.sleep(0.1)
            records = history(runner, second_directory)
            require(not any(item.get('status') in {'RUNNING', 'CHILD_STARTED'} for item in records),
                    'Second payload admitted while first held the single global slot')
            require(not (second_directory / 'stdout.log').exists(), 'Queued second payload created logs prematurely')
            newjson(BASE / 'serialization-live-before.json', {
                'first': runner.status(ROOT, first), 'second': runner.status(ROOT, second),
                'second_actual_properties': sample, 'first_live_descendant': live,
                'second_payload_not_launched': True})
            runner.stop(ROOT, first)
            first_result = finalized(runner, first, actual['ControlGroup'])
            second_result = finalized(runner, second, parent_group + '/' + second_unit)
            first_end = next(item['at'] for item in history(runner, first_directory) if item.get('status') == 'FINALIZED')
            second_start = next(item['at'] for item in history(runner, second_directory) if item.get('status') == 'CHILD_STARTED')
            require(second_start > first_end, 'Second payload started before prior cgroup/finalizer admission barrier cleared')
            require(bool(select.select([fd], [], [], 0)[0]), 'First detached descendant survived serialization')
            require(first_result['integrity']['status'] == 'INTERRUPTED', 'Serialized first stop was not recorded')
            require(second_result['integrity']['status'] == 'PROCESS_EXITED', 'Serialized second payload failed')
            cases.extend([{'case': 'serialized-first-stopped-and-drained', **first_result, 'live_descendant': live},
                          {'case': 'serialized-second-admitted-after-finalized', **second_result,
                           'first_finalized_at': first_end, 'second_child_started_at': second_start}])
        finally:
            os.close(fd)

        count = len(list((ROOT / 'executions').iterdir()))
        duplicate = command(['/usr/bin/python3', str(RELEASE), '--root', str(ROOT), 'submit',
                             '--request-key', 'final988-exit-seven', '--kind', 'validation',
                             '--validation-scope', 'lifecycle', '--cwd', str(BASE),
                             '--input', str(PAYLOAD), '--', '/usr/bin/python3', str(PAYLOAD),
                             'exit-seven', '{execution_dir}/payload'])
        newjson(BASE / 'duplicate-fresh-process.json', duplicate)
        require(duplicate['returncode'] == 1 and 'already claimed' in duplicate['stderr'],
                'Fresh process did not reject persisted duplicate request')
        require(count == len(list((ROOT / 'executions').iterdir())) == 10, 'Duplicate created an execution or fixture count changed')
        reverified = [runner.verify(ROOT, item['execution_id']) for item in cases]
        require(len(reverified) == 10 and all(item['scientific_acceptance'] == 'unverified' for item in reverified),
                'Final receipt verification set incomplete')
        require(runner.current_state(ROOT) == 'INVENTORY', 'Isolated fixture state unexpectedly advanced')
        for item in plan['files']:
            require(binding(Path(item['path'])) == item, 'Fixture source changed while executing')
        require(binding(RELEASE) == plan['runner'], 'Installed runner changed while executing')
        newjson(BASE / 'replay-receipt.json', {
            'schema': 'openrx.final988.actual.host-lifecycle-replay.v1', 'accepted': True,
            'started_at': start, 'completed_at': runner.now(), 'runner': binding(RELEASE),
            'plan': binding(PLAN), 'fixture_root': str(ROOT), 'cases': cases,
            'duplicate_rejected_in_fresh_process': True, 'final_reverified': reverified,
            'scientific_acceptance': 'unverified', 'migration_activation': False,
            'limitations': plan['limitations'], 'actual_fixture_resources': plan['actual_fixture_resources'],
            'production_resource_baseline': plan['production_resource_baseline']})
        print(json.dumps({'accepted': True, 'host_only_lifecycle_controls': len(cases),
                          'receipt': binding(BASE / 'replay-receipt.json'),
                          'scientific_acceptance': 'unverified'}, sort_keys=True))
    except BaseException as exc:
        cleanup = []
        for eid in active:
            try:
                directory = runner.execution_dir(ROOT, eid)
                if not (directory / 'receipt.json').exists():
                    cleanup.append({'execution_id': eid, 'stop': runner.stop(ROOT, eid)})
            except BaseException as cleanup_error:
                cleanup.append({'execution_id': eid, 'error': repr(cleanup_error)})
        newjson(BASE / 'replay-failure.json', {'accepted': False, 'error': repr(exc), 'started_at': start,
                                            'at': runner.now(), 'completed_cases': cases, 'active_ids': active,
                                            'cleanup': cleanup, 'scientific_acceptance': 'unverified',
                                            'instruction': 'Preserve every artifact. Inspect/recover each ID; do not clear request claims or automatically replay.'})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--describe', action='store_true')
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--launch-one', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--expected-plan-sha256', required=True)
    args = parser.parse_args()
    plan = checked_inputs(args)
    if args.describe:
        print(json.dumps({'execution_started': False, 'plan': plan}, indent=2, sort_keys=True))
        return
    runner = load_runner()
    if args.launch_one:
        require(ROOT.is_dir() and runner.current_state(ROOT) == 'INVENTORY', 'Unexpected launcher fixture state')
        print(submit(runner, 'independent-launcher', 'independent'), flush=True)
    else:
        execute(runner, plan)


if __name__ == '__main__':
    main()
