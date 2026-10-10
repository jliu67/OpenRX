#!/usr/bin/env python3
"""Independent retained stop03 review. No simulations, signals or state writes."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
R = Path('$OPENRX_LOCAL_ROOT')
E = R / 'migrations/20261009'
ID = '20261009T202537Z-a1ca7df2cf1c'
D = R / 'executions' / ID
A = E / 'gem5-stop-proof-attempt-03/attempts/20261009T202455Z-bafaf3718c37'
S = R / 'checkouts/execution-b4b5ffc'
RES = R / 'artifacts/guest-resources-ranged-20261009'
G = R / 'builds/gem5-rebuild-03/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt'
RUNNER = R / 'releases/runner-v1-988cf13f/local_execution.py'
CHECKER = E / 'independent_runtime_review_v1.py'
SPEC = R / 'requests/spec-issue-27-gem5-stop-migration-attempt-03.json'
CONTROLLER = E / 'prove_gem5_stop_v3.py'
PINNED = {
    RUNNER: '988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882',
    CHECKER: '97430d48d73eb1014ce1c1acd5e1de14aa2815da285ad5d84771329aa8bbd62e',
    SPEC: 'd425c756d2ac184a56d61de80a8ade0dafd226da29657e4567a2cb0a1e261010',
    CONTROLLER: '6743268de7074a27e2fcf16e2c8f8cea2ae2af6fd5dc495c2e4b762867171c39',
    E / 'independent-runtime-review-v1/independent-runtime-review.json': '12db13426bddda29b7857f423e52fca0b87842c3225d81b2ec2cb3f793170bae',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def duplicate_free(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'Duplicate JSON key: ' + k)
        result[k] = v
    return result


def read(path):
    return json.loads(Path(path).read_bytes(), object_pairs_hook=duplicate_free)


def digest(path):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        before = os.fstat(f.fileno())
        require(stat.S_ISREG(before.st_mode), 'Nonregular evidence: ' + str(path))
        h = hashlib.sha256()
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
        after = os.fstat(f.fileno())
    key = lambda t: (t.st_dev, t.st_ino, t.st_size, t.st_mtime_ns, t.st_ctime_ns)
    require(key(before) == key(after), 'Evidence changed: ' + str(path))
    return {'path': str(path), 'bytes': after.st_size, 'sha256': h.hexdigest()}


def module(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def main():
    utc = datetime.datetime.now(datetime.timezone.utc)
    result = {'schema': 'openrx.independent.actual-running-stop03.review.v1',
              'reviewer': 'Independent scientific_inventory subagent; separate from controller author; shared workspace/account',
              'review_utc': utc.isoformat(), 'execution_id': ID,
              'scope': 'Fresh read-only assessment of retained actual firmware-running controlled stop; no execution replay',
              'migration_state_observed': 'LOCAL_VALIDATING', 'migration_complete': False,
              'local_activation_accepted': False, 'scientific_acceptance': 'unverified for interrupted stop03',
              'checks': {}, 'limitations': [
                  'Historical live PID/pidfd/cgroup observation is source-bound retained evidence, not a newly replayed live process.',
                  'This stop proves expected OpenSBI firmware execution followed by controlled termination; no complete Linux boot or nine-control scientific pass is inferred.',
                  'Actual child status is -9; wrapper logical SIGINT cancellation label is not a claim of graceful child signal exit.',
                  'No graceful gem5 statistics/checkpoint finalization, verified checkpoint resume, host reboot or whole Codex shutdown is demonstrated.',
                  'Historical 6G/1G/CPU200 manifest and manager properties do not prove historical kernel CPU quota enforcement; new owner resource policy is a separate review.',
              ]}
    try:
        fixed = []
        for path, sha in PINNED.items():
            item = digest(path)
            require(item['sha256'] == sha, 'Fixed identity drift: ' + str(path))
            fixed.append(item)
        result['fixed_bindings'] = fixed
        runner = module('independent_stop03_runner', RUNNER)
        checker = module('independent_stop03_checker', CHECKER)
        m = read(D / 'manifest.json')
        spec = read(SPEC)
        proof = read(A / 'stop-proof-receipt.json')
        receipt = read(D / 'receipt.json')
        report = read(D / 'payload/report.json')
        process = read(D / 'process-result.json')
        require(m['execution_id'] == ID and m['unit'] == f'openrx-{ID}.service'
                and m['request_key'] == spec['request_key'] and m['cwd'] == str(S)
                and m['migration_state'] == 'LOCAL_VALIDATING' and m['scientific_acceptance'] == 'unverified',
                'Execution admission identity mismatch')
        require(len(m['inputs']) == 9 and len({i['path'] for i in m['inputs']}) == 9,
                'Exact nine unique input bindings missing')
        require(len(m['sources']) == 1 and m['sources'][0]['path'] == str(S)
                and len(m['sources'][0]['files']) == 890, 'Expected frozen scientific source tree missing')
        runner.check_bindings(R, D, m)
        result['checks']['unchanged_exact_request_runner_executable_nine_inputs_and_890_source_files'] = True
        result['current_output_verification'] = runner.verify(R, ID)
        require(result['current_output_verification']['status'] == 'PROCESS_FAILED', 'Wrong retained process status')
        result['checks']['complete_21_artifact_pathset_hashes_event_chain_external_receipt_binding'] = len(receipt['artifacts']) == 21
        require(result['checks']['complete_21_artifact_pathset_hashes_event_chain_external_receipt_binding'], 'Wrong artifact count')
        stage = read(A / 'observed-running-guest-stage.json')
        live = read(A / 'observed-live-pinned-gem5.json')
        marker = read(D / 'stop.request')
        serial = (A / 'observed-running-guest-serial.txt').read_bytes()
        terminal = (D / 'payload/m5out/board.platform.terminal').read_bytes()
        require(len(serial) == 868 and hashlib.sha256(serial).hexdigest() == 'ea9d1a993695589fc843823ea79584cf18f0504c3f57b3aa89f4962fe673fb86'
                and b'\r\nOpenSBI v1.3.1\r\n' in serial
                and b'Platform HART Count       : 1\r\n' in serial,
                'Exact raw CRLF firmware/hart snapshot invalid')
        require(stage == proof['actual_guest_stage_observed'] == marker['observed_running_guest']
                and live == proof['actual_simulator_observed'] == marker['observed_live_simulator']
                and digest(A / 'observed-running-guest-serial.txt') == stage['snapshot']
                and digest(D / 'stop.request') == read(A / 'created-stop-marker.json'), 'Stage/marker witness binding drift')
        gstat = G.stat()
        cg = f'/user.slice/user-1000.slice/user@1000.service/app.slice/openrx-{ID}.service'
        require(live['pid'] == 87741 and live['pidfd_opened_while_live'] is True
                and live['exe'] == str(G) and live['cgroup'] == cg
                and live['exe_inode'] == gstat.st_ino and live['exe_device'] == gstat.st_dev
                and stage['same_pinned_process_pidfd_still_live'] is True
                and marker['controller'] == digest(CONTROLLER)
                and marker['request_sha256'] == PINNED[SPEC]
                and live['commandline'].split() == report['command'], 'Pinned actual live-process/marker witness invalid')
        require(proof['marker_created_after_live_observation'] is True and proof['observed_process_pidfd_exit'] is True
                and terminal.startswith(serial), 'Live-before-marker or retained serial prefix missing')
        require(datetime.datetime.fromisoformat(live['utc']) <= datetime.datetime.fromisoformat(stage['utc'])
                < datetime.datetime.fromisoformat(process['finished_at'])
                < datetime.datetime.fromisoformat(proof['finished_utc']), 'Witness chronology invalid')
        result['checks']['raw_868_byte_expected_firmware_same_live_pidfd_executable_and_premarker_witness'] = True
        result['checks']['retained_final_serial_preserves_exact_snapshot_prefix'] = True
        require(report['status'] == 'fail' and report['interrupted'] is True
                and report['interruption_source'] == 'stop-file' and report['stop_file_observed'] is True
                and report['runtime_validated'] is False and report['boot_observed'] is False
                and type(report['child_returncode']) is int and report['child_returncode'] == -9
                and process['returncode'] == 1 and process['status'] == 'PROCESS_FAILED'
                and read(D / 'stdout.log') == report and receipt['process'] == process
                and receipt['scientific_acceptance'] == 'unverified' and receipt['resume_allowed'] is False,
                'Interrupted failure/scientific status controls invalid')
        require((D / 'payload/m5out/stats.txt').stat().st_size == 0
                and b'OPENRX_GUEST_COMPLETE' not in terminal,
                'Unexpected graceful scientific completion assertion')
        result['checks']['truthful_child_minus9_wrapper1_failure_no_scientific_pass_no_resume'] = True
        result['actual_model'] = checker.inspect_model(read(D / 'payload/m5out/config.json'), RES,
                                                       D / 'payload/guest.sh', D / 'payload/m5out')
        require(report['gem5_binary_sha256'] == spec['simulator_binary_sha256']
                and report['config_sha256'] == '5608189a6f2a41a45e86f117f10af8408ab87ea1aab600294a336ab31375e7c5'
                and report['resource_manifest_sha256'] == '67c3838d04b617b3a4f34a874f84cc2c5517eca51c9049456bc6df19312404bb'
                and report['readfile_sha256'] == digest(D / 'payload/guest.sh')['sha256'],
                'Actual simulator/model/resource/readfile drift')
        result['checks']['unchanged_actual_scalar_RV64_atomic_1core_1GHz_4GiB_caches_COW_model'] = True
        unit = runner.unit_status(m['unit'])
        require(unit['query_returncode'] == 0 and unit.get('LoadState') in {'loaded', 'not-found'}
                and unit.get('ActiveState') in {'inactive', 'failed'}, 'Unknown or live current manager state')
        cgp = Path('/sys/fs/cgroup') / cg.lstrip('/')
        populated = cgp.exists()
        if populated:
            require(all(not p.read_text().strip() for p in cgp.rglob('cgroup.procs'))
                    and 'populated 1' not in (cgp / 'cgroup.events').read_text(), 'Owned cgroup still populated')
        require(not proof['final_cgroup']['populated'] and proof['final_cgroup']['pids'] == []
                and proof['final_unit']['query_returncode'] == 0
                and proof['final_unit']['Result'] == 'exit-code'
                and proof['final_unit']['ExecMainStatus'] == '1', 'Historical failure/drain witness inconsistent')
        result['current_manager'] = unit
        result['current_cgroup'] = {'path': str(cgp), 'present': cgp.exists(), 'populated': False}
        result['checks']['historical_exit_failure_and_current_named_cgroup_drained'] = True
        require(proof['accepted'] is True and proof['missing_proof'] == [] and proof['migration_complete'] is False,
                'Controller receipt not accepted in bounded scope')
        result['retained_evidence'] = [digest(p) for p in sorted(A.iterdir()) if p.is_file()]
        result['execution_bindings'] = [digest(D / name) for name in ('manifest.json', 'receipt.json', 'stop.request', 'payload/report.json')]
        result['launch'] = digest(E / 'gem5-running-stop-controller-v3-launch-20261009T202455Z.json')
        result['accepted'] = all(result['checks'].values())
        result['technical_gate_outcome'] = 'Expected running-firmware stop, inspected failed process/logs and immutable-input/output integrity accepted; original complete-guest science acceptance remains separate.'
    except Exception as exc:
        result['accepted'] = False
        result['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    result['review_script'] = digest(Path(__file__).resolve())
    path = E / ('independent-actual-running-stop03-review-' + utc.strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    data = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    fd = os.open(E, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({'accepted': result['accepted'], 'receipt': digest(path), 'checks': result['checks'], 'error': result.get('error')}, indent=2))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
