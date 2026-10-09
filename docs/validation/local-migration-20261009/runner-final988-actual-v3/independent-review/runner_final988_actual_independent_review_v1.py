"""Read-only final988 lifecycle evidence audit; no jobs or scientific validation."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, signal, sys
sys.dont_write_bytecode = True
R = Path('$OPENRX_LOCAL_ROOT')
B = R / 'validation/runner-lifecycle-final988-20261009'
ROOT = B / 'fixture-root'
E = R / 'migrations/20261009'
RELEASE = R / 'releases/runner-v1-988cf13f/local_execution.py'
SHA = '988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882'

def bind(path):
    require(not path.is_symlink() and path.is_file(), 'Nonregular evidence')
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(path):
    return json.loads(path.read_text())

def main():
    own = bind(Path(__file__))
    require(bind(RELEASE)['sha256'] == SHA, 'Runner source drift')
    spec = importlib.util.spec_from_file_location('independent_final988_audit', RELEASE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    plan = read(B / 'plan-v3.json')
    replay = read(B / 'replay-receipt.json')
    require(replay['accepted'] is True and len(replay['cases']) == 10, 'Replay did not accept exactly ten controls')
    require(replay['runner'] == bind(RELEASE) and replay['plan'] == bind(B / 'plan-v3.json')
            and replay['externally_approved_plan_sha256'] == 'af7c0fcc7329cf2755c8c340f9ea578dde5ec5bcbe5ad71751e939402537d837',
            'Replay source/plan drift')
    require(bind(B / 'replay-v3.py')['sha256'] == '632c9ca0072e9c06e25d4c90d3910b4ea3bc5584859e09354484ed9bf0a60d72'
            and bind(B / 'toy_payload.py')['sha256'] == '3e04fade4ef3f9a436be96b6295cba1d66ca8b55993e1d7803fa8081818328e6',
            'Actual fixture source drift')
    require(not (B / 'replay-failure.json').exists(), 'Replay has a failure record')
    expected = {
        'final988-stop-detached': ('detached', 'INTERRUPTED'),
        'final988-instant-0': ('instant', 'PROCESS_EXITED'),
        'final988-instant-1': ('instant', 'PROCESS_EXITED'),
        'final988-instant-2': ('instant', 'PROCESS_EXITED'),
        'final988-exit-seven': ('exit-seven', 'PROCESS_FAILED'),
        'final988-worker-killed': ('detached', 'INTERRUPTED_UNREAPED'),
        'final988-oom': ('oom', 'INTERRUPTED'),
        'final988-independent-launcher': ('independent', 'INTERRUPTED'),
        'final988-serialize-first': ('detached', 'INTERRUPTED'),
        'final988-serialize-second': ('instant', 'PROCESS_EXITED'),
    }
    cases, samples, ids = [], [], {}
    for case in replay['cases']:
        eid = case['execution_id']
        directory = ROOT / 'executions' / eid
        manifest = read(directory / 'manifest.json')
        receipt = read(directory / 'receipt.json')
        key = manifest['request_key']
        require(key in expected and key not in ids, 'Unexpected/duplicate fixture key')
        ids[key] = eid
        mode, status = expected[key]
        require(manifest['execution_id'] == eid and manifest['kind'] == 'validation'
                and manifest['validation_scope'] == 'lifecycle' and manifest['migration_state'] == 'INVENTORY',
                'Fixture admission identity/scope drift')
        require(manifest['argv'] == [str(Path('/usr/bin/python3').resolve()), str(B / 'toy_payload.py'), mode, str(directory / 'payload')]
                and manifest['cwd'] == str(B) and manifest['env'] == m.DEFAULT_ENV,
                'Fixture argv/environment drift')
        require(manifest['resource_lock'] == str(ROOT / 'locks/execution.lock'), 'Fixture lock outside isolated root')
        require(len(manifest['inputs']) == 3 and {q['path'] for q in manifest['inputs']} ==
                {str(B / 'toy_payload.py'), str(B / 'replay-v3.py'), str(B / 'plan-v3.json')}, 'Fixture input set drift')
        require(len(manifest['sources']) == 1 and manifest['sources'][0]['path'] == str(RELEASE), 'Runner source binding drift')
        require(manifest['runner'] == m.digest(RELEASE) and bind(directory / 'runner.py')['sha256'] == SHA, 'Runner snapshot drift')
        require(manifest['resources'] == {'MemoryMax': '6G', 'MemorySwapMax': '1G', 'CPUQuota': '200%',
                'TasksMax': 256, 'Nice': 10, 'NoNewPrivileges': True, 'global_slots': 1}, 'Production manifest baseline changed')
        m.check_bindings(ROOT, directory, manifest)
        verified = m.verify(ROOT, eid)
        require(verified == case['integrity'] and verified['status'] == status and verified['scientific_acceptance'] == 'unverified',
                'Retained receipt integrity/outcome mismatch')
        require(case['receipt'] == bind(directory / 'receipt.json') and receipt['process'] == case['process']
                and receipt['systemd'] == case['systemd'] and receipt['resume_allowed'] is False, 'Receipt report mismatch')
        normal = m.systemd_command(ROOT, directory, manifest)
        overrides = {'--property=MemoryMax=6G': '--property=MemoryMax=' + ('48M' if key == 'final988-oom' else '64M'),
            '--property=MemorySwapMax=1G': '--property=MemorySwapMax=0',
            '--property=CPUQuota=200%': '--property=CPUQuota=10%', '--property=TasksMax=256': '--property=TasksMax=16'}
        tiny = [overrides.get(q, q) for q in normal]
        recorded = read(B / (key + '-service-command.json'))
        require(recorded['production_default'] == normal and recorded['actual_fixture_command'] == tiny
                and read(directory / 'submission-command.json')['argv'] == tiny
                and read(directory / 'submission-result.json')['returncode'] == 0, 'Submission overrides/admission mismatch')
        history = m.events(directory / 'events.jsonl')
        statuses = [q.get('status') for q in history]
        require(statuses.count('RUNNING') == statuses.count('CHILD_STARTED') == statuses.count('FINALIZED') == 1
                and statuses.index('RUNNING') < statuses.index('CHILD_STARTED') < statuses.index('FINALIZED'), 'Lifecycle event chain mismatch')
        if status == 'PROCESS_EXITED':
            require(receipt['process']['returncode'] == 0 and receipt['process']['signals'] == []
                    and receipt['systemd']['SERVICE_RESULT'] == 'success', 'Successful fixture failed')
        if key == 'final988-exit-seven':
            require(receipt['process']['returncode'] == 7 and receipt['systemd']['SERVICE_RESULT'] == 'exit-code', 'Intentional rc7 not truthful')
        if key == 'final988-worker-killed':
            require(receipt['process'] is None and not (directory / 'process-result.json').exists()
                    and receipt['systemd']['SERVICE_RESULT'] == 'signal' and receipt['systemd']['EXIT_STATUS'] == 'KILL'
                    and case['pidfd_observed_exit'] is True and case['recovery'] == verified, 'Hard-kill/recovery fabricated outcome')
        if key == 'final988-oom':
            require(receipt['systemd']['SERVICE_RESULT'] == 'oom-kill' and receipt['status'] != 'PROCESS_EXITED', 'Actual OOM not established')
        if key in ['final988-stop-detached', 'final988-serialize-first', 'final988-independent-launcher']:
            require(signal.SIGINT in receipt['process']['signals'], 'Expected stop signal not retained')
        if 'live_descendant' in case:
            live = case['live_descendant']
            group = case['final_cgroup']['path'].removeprefix('/sys/fs/cgroup')
            require(live['membership'].strip() == '0::' + group and live['pidfd_live'] is True, 'Descendant identity/cgroup mismatch')
            child = read(directory / 'payload/detached-child.json')
            ready = read(directory / 'payload/detached-child-output/ready.json')
            require(child['pid'] == live['pid'] == ready['pid'] and child['start_new_session'] is True, 'Detached child witness mismatch')
        sample_path = B / (key + '-actual-properties.json')
        if sample_path.exists():
            sample = read(sample_path)
            props = sample['properties']
            require(sample['returncode'] == 0 and props['LoadState'] == 'loaded' and props['ActiveState'] == 'active', 'Live manager sample unavailable')
            budget = {'MemoryMax': str((48 if key == 'final988-oom' else 64) * 1024 * 1024), 'MemorySwapMax': '0',
                'CPUQuotaPerSecUSec': '100ms', 'TasksMax': '16', 'Nice': '10', 'NoNewPrivileges': 'yes',
                'KillMode': 'mixed', 'KillSignal': '2', 'TimeoutStopUSec': '45s', 'SendSIGKILL': 'yes',
                'Restart': 'no', 'NotifyAccess': 'exec', 'UMask': '0077'}
            require(all(props[q] == value for q, value in budget.items()) and props['ControlGroup'].endswith('/' + manifest['unit']),
                    'Actual tiny limits/cgroup mismatch')
            samples.append({'request_key': key, 'sample': bind(sample_path), 'actual_resources': budget})
        group = Path(case['final_cgroup']['path'])
        require(group.name == manifest['unit'] and case['final_cgroup']['empty'] is True, 'Recorded final cgroup not empty')
        pids = sorted({int(pid) for q in group.rglob('cgroup.procs') for pid in q.read_text().split()}) if group.exists() else []
        require(not pids, 'Current cgroup descendants remain')
        if group.exists():
            require(dict(line.split() for line in (group / 'cgroup.events').read_text().splitlines())['populated'] == '0', 'Current cgroup populated')
        unit = m.unit_status(manifest['unit'])
        require(unit['query_returncode'] == 0 and unit['LoadState'] in ['loaded', 'not-found']
                and unit['ActiveState'] in ['inactive', 'failed'], 'Actual unit remains live or unknown')
        terminal = case['terminal_properties']
        require(terminal['returncode'] == 0 and terminal['properties']['ActiveState'] in ['inactive', 'failed'], 'Recorded terminal sample missing')
        cases.append({'execution_id': eid, 'request_key': key, 'process_status': status,
            'child_returncode': receipt['process']['returncode'] if receipt['process'] else None,
            'manager_result': receipt['systemd']['SERVICE_RESULT'], 'manifest': bind(directory / 'manifest.json'),
            'receipt': bind(directory / 'receipt.json'), 'actual_submission': bind(directory / 'submission-command.json'),
            'receipt_integrity_verified': True, 'input_and_source_bindings_reverified': True,
            'current_unit': unit, 'current_owned_cgroup_empty': True, 'status_sequence': statuses})
    require(set(ids) == set(expected) and len(list((ROOT / 'executions').iterdir())) == 10 and len(samples) == 5,
            'Execution/sample inventory incomplete')
    require(m.current_state(ROOT) == 'INVENTORY', 'Fixture advanced migration state')
    for item in plan['files']:
        require(bind(Path(item['path'])) == item, 'Fixture source changed')
    launcher = read(B / 'independent-launcher-result.json')
    observed = read(B / 'session-independence-observation.json')
    require(launcher['returncode'] == 0 and launcher['launching_process_reaped'] is True and launcher['start_new_session'] is True
            and observed['launcher_pid'] == launcher['pid'] and observed['launcher_absent'] is True, 'Launching process/session did not exit')
    require(observed['stdout_after'].startswith(observed['stdout_before']) and observed['stdout_after'] != observed['stdout_before']
            and 'systemd' in observed['parent_command'] and '--user' in observed['parent_command']
            and observed['main_live']['pidfd_live'] is True, 'Manager-owned post-launch log progress missing')
    independent = ROOT / 'executions' / ids['final988-independent-launcher']
    require(next(q['pid'] for q in m.events(independent / 'events.jsonl') if q.get('status') == 'RUNNING')
            == observed['main_live']['pid'], 'Independent worker PID witness mismatch')
    queued = read(B / 'serialization-live-before.json')
    second = ROOT / 'executions' / ids['final988-serialize-second']
    require(queued['second_payload_not_launched'] is True and queued['second']['execution_id'] == second.name
            and queued['second']['latest_event'] == m.events(second / 'events.jsonl')[0]
            and queued['second']['latest_event']['status'] == 'QUEUED'
            and queued['second']['latest_event']['previous_sha256'] is None, 'Live serialized queue witness mismatch')
    first = ROOT / 'executions' / ids['final988-serialize-first']
    first_finalized = next(q['at'] for q in m.events(first / 'events.jsonl') if q.get('status') == 'FINALIZED')
    second_started = next(q['at'] for q in m.events(second / 'events.jsonl') if q.get('status') == 'CHILD_STARTED')
    require(second_started > first_finalized, 'Empirical serialized timing witness not observed')
    duplicate = read(B / 'duplicate-fresh-process.json')
    require(duplicate['returncode'] == 1 and 'already claimed' in duplicate['stderr'] and duplicate['argv'][1] == str(RELEASE),
            'Fresh-process duplicate not denied')
    hard = read(B / 'worker-hard-kill-command.json')
    require(hard['returncode'] == 0 and hard['argv'] == ['systemctl', '--user', 'kill', '--kill-who=main', '--signal=SIGKILL',
            'openrx-' + ids['final988-worker-killed'] + '.service'], 'Worker kill did not target exact named service')
    log = read(B / 'replay-v3-service.log')
    require(log['accepted'] is True and log['receipt'] == bind(B / 'replay-receipt.json'), 'Controller stdout receipt binding mismatch')
    for item in cases:
        require(m.verify(ROOT, item['execution_id'])['integrity_verified'] is True, 'Final output recheck failed')
    require(bind(Path(__file__)) == own and bind(RELEASE)['sha256'] == SHA, 'Independent reviewer/release drift')
    result = {'schema': 'openrx.final988.actual-host-lifecycle-independent-review.v1',
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reviewer': 'scientific_inventory independent subagent; shared owner account, not independent human approval',
        'independent_actual_review_accepted': True, 'checker': own,
        'source': bind(B / 'replay-v3.py'), 'plan': bind(B / 'plan-v3.json'), 'toy': bind(B / 'toy_payload.py'),
        'runner': bind(RELEASE), 'actual_replay_receipt': bind(B / 'replay-receipt.json'),
        'executions_verified': 10, 'cases': cases, 'live_actual_resources_sampled_units': 5, 'resource_samples': samples,
        'resource_scope': 'All10 recorded exact tiny submission overrides;5 live controls have actual manager samples. Production6G/1G/200%/256 baseline unchanged, not measured by tiny fixtures.',
        'launcher_independence_witness': observed, 'duplicate_rejected_fresh_process': True,
        'named_main_worker_sigkill_preserved_unreaped_failure': True, 'deliberate_48MiB_cgroup_oom_manager_result': 'oom-kill',
        'partial_logs_retained': True,
        'serialization_witness': {'first_finalized_at': first_finalized, 'second_child_started_at': second_started,
            'observed_second_after_first_finalized': True,
            'scope': 'Empirical in this replay only; prior FINALIZED is not a formal admission guarantee due worker-exit/private-finalizer startup gap. Formal guarantee is single flock payload plus drained prior workload/descendants.'},
        'fixture_state': 'INVENTORY', 'production_migration_state_observed': m.current_state(R),
        'scientific_acceptance': 'unverified', 'activation_authorized': False, 'migration_complete': False,
        'reviewer_schema_correction': bind(E / 'runner-final988-independent-audit-schema-correction.json'),
        'limitations': ['Host-only toys, no simulator/scientific workload acceptance',
            'Whole Codex daemon shutdown/host reboot not performed; exited launcher/session with manager-owned progress explicitly scoped',
            'Successful transient unit GC defaults never treated as actual resource or terminal Result evidence',
            'Intentional stop/rc7/hard-kill/OOM remain interruption/failure outcomes; control pass means truthful expected failure behavior',
            'Long-finalizer55s evidence remains separate; no100GB/large-output throughput demonstration',
            'Harness failure cleanup statically reviewed; successful replay did not force controller failure cleanup'],
        'review_actions': 'Read-only hashing, exact988 verify/check_bindings/events/command construction and manager/cgroup reads. No recover,stop,submit,rerun,state,GitHub or simulation.'}
    path = E / 'runner-final988-replay-actual-independent-review.json'
    with path.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    os.fsync(fd)
    os.close(fd)
    print(json.dumps({'accepted': True, 'executions': 10, 'samples': 5, 'receipt': bind(path), 'migration_complete': False}))

if __name__ == '__main__':
    main()
