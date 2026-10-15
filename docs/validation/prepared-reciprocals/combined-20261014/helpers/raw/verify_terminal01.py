"""Verify one completed admitted execution; preserve every verification attempt."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time
import uuid

OUT = Path(__file__).resolve().parent
PARENTS = ['35c2cae61092107acb2c684bbca308aca8fb280b', '5f28dd4363504ecf33a8f10451c53405773c564f']
RUNNER = Path('/home/server/openrx-local/v1/releases/runner-v1-657b23f1/local_execution.py')
RUNNER_SHA = '657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b'
SLOT = Path('/home/server/openrx-local/v1/locks/execution.lock')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def pairs(values):
    result = {}
    for key, value in values:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def regular(path):
    require(stat.S_ISREG(path.lstat().st_mode), 'Linked/special/missing file: ' + str(path))
    return path


def load(path):
    with regular(path).open() as stream:
        return json.load(stream, object_pairs_hook=pairs)


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def sha(path):
    before = regular(path).stat()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode) ==
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode), 'File changed while hashing: ' + str(path))
    return digest.hexdigest()


def member(root, name):
    value = PurePosixPath(name)
    require(name and name != '.' and not value.is_absolute() and '..' not in value.parts
            and '\\' not in name and value.as_posix() == name, 'Unsafe source member')
    return root / name


def inventory(root):
    require(stat.S_ISDIR(root.lstat().st_mode), 'Linked/special source root')
    result = set()
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'Linked/special source entry: ' + str(path))
        if stat.S_ISREG(mode):
            result.add(path.relative_to(root).as_posix())
    return result


def verify_source(source, record):
    require(inventory(source) == set(record['files']) and len(record['files']) == record['file_count'],
            'Complete frozen source inventory changed')
    for name, row in record['files'].items():
        path = member(source, name)
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Frozen source bytes changed: ' + name)
        require((path.stat().st_mode & 0o111) == (int(row['mode'], 8) & 0o111),
                'Exact source execute mask changed: ' + name)
    return len(record['files'])


def bind_inputs(workspace, spec, frozen, manifest, precheck):
    source = str(Path(workspace['source']).resolve())
    require(workspace['parents'] == spec['parents'] == frozen['parents'] == PARENTS, 'Exact parents differ')
    require(source == spec['source'] == frozen['source'] == manifest['cwd'], 'Execution source identities differ')
    require(workspace['source_tree'] == spec['staged_git_tree'] == frozen['staged_git_tree'], 'Frozen Git tree identities differ')
    require(workspace['source_archive_sha256'] == spec['source_archive_sha256'] == frozen['archive_sha256']
            and workspace['source_archive'] == frozen['archive'], 'Frozen archive identities differ')
    require(workspace['immutable_runner_sha256'] == manifest['runner']['sha256'] == RUNNER_SHA
            and spec['runner'] == manifest['runner']['path'] == str(RUNNER), 'Immutable runner identities differ')
    require(workspace['execution_id'] == manifest['execution_id']
            and spec['request_key'] == manifest['request_key'] and spec['kind'] == manifest['kind'] == 'simulation',
            'Execution/request identity differs')
    argv = manifest['argv']
    require(len(argv) == 5 and argv[1:] == ['-B', spec['wrapper'], source, workspace['execution_root']], 'Executed wrapper argv differs')
    wrapper = [row for row in manifest['inputs'] if row['path'] == spec['wrapper']]
    require(len(wrapper) == 1 and wrapper[0]['sha256'] == spec['wrapper_sha256'], 'Executed wrapper binding absent')
    sources = manifest['sources']
    require(len(sources) == 1 and sources[0]['path'] == source and sources[0]['kind'] == 'directory', 'Runner source binding differs')
    bound = {row['relative']: row for row in sources[0]['files']}
    require(len(bound) == len(sources[0]['files']) and set(bound) == set(frozen['files']), 'Runner/frozen source inventory differs')
    require(all(row['sha256'] == frozen['files'][name]['sha256'] and row['bytes'] == frozen['files'][name]['bytes']
                for name, row in bound.items()), 'Runner/frozen source file bindings differ')
    inputs = precheck['input_bindings']
    require(precheck['status'] == 'pass' and len(inputs) == 281 and
            precheck['parents'] == {'reviewed_pr70': PARENTS[0], 'merged_main': PARENTS[1]}, '281 source/provenance precheck identity differs')
    require(all(name in frozen['files'] and row == frozen['files'][name]['sha256'] for name, row in inputs.items()),
            'Scientific/provenance281 inputs differ from admitted source')
    return inputs


def service_values(text):
    return dict(line.split('=', 1) for line in text.splitlines() if '=' in line)


def bind_recovery(workspace, spec, frozen, manifest, precheck, recovery):
    require(recovery['source'] == workspace['source'], 'Recovery source differs from original frozen source')
    require(recovery['runner'] == str(RUNNER) and recovery['immutable_runner_sha256'] == RUNNER_SHA,
            'Recovery immutable runner identity differs')
    require(recovery['execution_id'] != workspace['execution_id']
            and recovery['execution_root'] != workspace['execution_root'], 'Recovery must be a distinct additive execution')
    for key, expected in [('parents', PARENTS), ('source_tree', workspace['source_tree']),
                          ('source_archive_sha256', workspace['source_archive_sha256']),
                          ('original_failed_execution', workspace['execution_id'])]:
        if key in recovery:
            require(recovery[key] == expected, 'Recovery declared original identity differs: ' + key)
    derived_workspace = dict(workspace, execution_id=recovery['execution_id'], execution_root=recovery['execution_root'])
    derived_spec = dict(spec, wrapper=recovery['wrapper'], wrapper_sha256=recovery['wrapper_sha256'],
                        request_key=recovery['request_key'])
    science = bind_inputs(derived_workspace, derived_spec, frozen, manifest, precheck)
    require(str(Path(recovery['execution_root']) / 'combined-finalization') ==
            recovery.get('component_output', str(Path(recovery['execution_root']) / 'combined-finalization')),
            'Recovery finalization output is not its isolated component directory')
    return science


def check_failed_wrapper(execution, spec, commands, stages):
    require([row['label'] for row in commands] == ['existing-and-focused-unit-tests', 'regfile']
            and all(row['returncode'] == 0 for row in commands), 'Original successful unit/seed command journal differs')
    require([row['phase'] for row in stages] == ['payload-start', 'unit-tests-complete', 'regfile-complete'],
            'Original failure progress stages differ')
    expected = ('Traceback (most recent call last):\n  File "' + spec['wrapper'] +
                '", line 70, in <module>\n    assert summary[\'status\']==\'pass\',summary\nKeyError: \'status\'\n')
    require(regular(execution / 'stderr.log').read_text() == expected, 'Original failure is not the exact preserved status-key wrapper error')
    stdout = regular(execution / 'stdout.log').read_text()
    require('START regfile' in stdout and 'START finalization' not in stdout
            and 'Both affected regression commands completed' not in stdout, 'Original wrapper progress contradicts preserved failure')
    require(not (execution / 'combined-finalization').exists()
            and not (execution / 'combined-finalization').is_symlink(), 'Original failed attempt contains an unexpected finalization output')
    units = regular(execution / 'unit-tests-console.log').read_text()
    match = re.search(r'Ran (\d+) tests in .*?\n\nOK\s*$', units, re.S)
    require(match is not None and int(match[1]) == 362, 'Original successful362 unit-test terminal record absent')
    summary = load(execution / 'combined-regfile/summary.json')
    require('status' not in summary, 'Original seed summary differs from the status-less output that triggered the known wrapper failure')
    return {'diagnostic': "KeyError: 'status'", 'external_wrapper_line': 70,
            'stderr_sha256': sha(execution / 'stderr.log'), 'original_wrapper_succeeded': False,
            'native_component_driver_returncode': 0, 'unit_tests': 362,
            'finalization_started_in_original': False}


def check_stages(rows):
    for row in rows:
        require(all(row['kernel'].get(key) == value for key, value in {
            'cpu.max': '600000 100000', 'memory.max': '4294967296',
            'memory.swap.max': '2147483648', 'pids.max': '256'}.items()), 'Actual admitted resource limits differ')


def check_component(output, science, frozen, finalizer):
    summary = load(output / 'summary.json')
    expected = (41, 19) if finalizer else (18, 17)
    require(summary.get('synthesis_requested') is True and summary.get('source_unchanged_after_run') is True
            and summary.get('rtl_modes') == len(summary['rtl']) == expected[0]
            and summary.get('mapped_modes') == len(summary['mapped']) == expected[1]
            and len(summary['mapping']) == 3, 'Actual completed component summary differs')
    if finalizer:
        require(summary.get('status') == 'pass' and summary.get('fixture_inputs_unchanged_after_run') is True
                and summary.get('native_invalid_input_cases') == 6 and summary.get('invalid_parameter_cases') == 4,
                'Recovery finalizer native/guard terminal summary differs')
    else:
        require(set(summary['negative']) == {'micro-1-32', 'micro-1-64'}
                and all(row.get('expected_failure_observed') is True for row in summary['negative'].values()),
                'Original seed expected-IP failure evidence differs')
    for family in ['rtl', 'mapped']:
        for label, row in summary[family].items():
            lines = regular(output / (label + '.log')).read_text().splitlines()
            require([line for line in lines if line.startswith('PASS ')] == [row['record']]
                    and not any('FATAL:' in line or line.startswith(('FAIL ', 'ERROR:')) for line in lines),
                    'Actual component PASS log differs: ' + label)
            if family == 'mapped':
                reference = 'rtl-seed' if label == 'mapped-hash-seed' else label.replace('mapped-', 'rtl-', 1)
                require(row == summary['rtl'][reference], 'Actual mapped/RTL record differs: ' + label)
    inputs = load(output / 'inputs.json')
    require(isinstance(inputs, dict) and len(inputs) >= 281
            and all(inputs.get(name) == digest for name, digest in science.items()), 'Component omitted original281 scientific/provenance inputs')
    require(all(name in frozen['files'] and frozen['files'][name]['sha256'] == digest
                for name, digest in inputs.items()), 'Actual component input differs from original frozen source')
    regular(output / 'artifacts.sha256.json')
    return {'output': str(output), 'rtl_modes': expected[0], 'mapped_modes': expected[1], 'actual_synthesis_count': 3,
            'summary_sha256': sha(output / 'summary.json'), 'artifact_manifest_sha256': sha(output / 'artifacts.sha256.json'),
            'inputs_sha256': sha(output / 'inputs.json'), 'actual_PASS_logs_verified': True}


def verify_runner_attempt(role, execution_id, execution, manifest, expected_status, expected_rc, attempt):
    command = ['python3', '-B', str(RUNNER), '--root', '/home/server/openrx-local/v1']
    prefix = 'original' if role == 'original-failed' else 'recovery'
    status = json.loads(subprocess.check_output([*command, 'status', execution_id], text=True), object_pairs_hook=pairs)
    save(attempt / (prefix + '-runner-status.json'), status)
    require(status['execution_id'] == execution_id and status['receipt'] is not None
            and (status['unit']['query_returncode'] == 0 or status['unit'].get('LoadState') == 'not-found')
            and status['unit']['ActiveState'] in ('inactive', 'failed'), 'Runner attempt is not finalized/drained: ' + role)
    result = load(execution / 'process-result.json')
    require(result['status'] == expected_status and result['returncode'] == expected_rc, 'Attempt process status differs: ' + role)
    verified = json.loads(subprocess.check_output([*command, 'verify', execution_id], text=True), object_pairs_hook=pairs)
    save(attempt / (prefix + '-runner-integrity.json'), verified)
    require(verified == {'execution_id': execution_id, 'integrity_verified': True,
            'scientific_acceptance': 'unverified', 'status': expected_status}, 'Immutable verified attempt status differs: ' + role)
    receipt = load(execution / 'receipt.json')
    require(receipt == status['receipt'] and receipt['execution_id'] == execution_id
            and receipt['status'] == expected_status and receipt['process'] == result,
            'Preserved runner receipt/process/status differs: ' + role)
    manager = 'success' if expected_rc == 0 else 'exit-code'
    require(receipt['systemd']['SERVICE_RESULT'] == manager, 'Preserved attempt manager result differs: ' + role)
    control = subprocess.check_output(['systemctl', '--user', 'show', manifest['unit'],
        '--property=LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,ControlGroup'], text=True)
    state = service_values(control)
    require(state.get('ActiveState') in ('inactive', 'failed'), 'Owned attempt service is still active: ' + role)
    if state.get('LoadState') != 'not-found':
        require(state.get('Result') == manager and state.get('ExecMainStatus') == str(expected_rc),
                'Retained/current attempt service exit result differs: ' + role)
    if state.get('ControlGroup'):
        cg = Path('/sys/fs/cgroup') / state['ControlGroup'].lstrip('/')
        require(not cg.exists() or not any(path.read_text().strip() for path in cg.rglob('cgroup.procs')),
                'Owned attempt cgroup descendants remain: ' + role)
    with (attempt / (prefix + '-terminal-service.txt')).open('x') as stream:
        stream.write(control)
    source_map = manifest['sources'][0]
    return {'role': role, 'execution_id': execution_id, 'execution_root': str(execution),
            'status': expected_status, 'returncode': expected_rc, 'integrity_verified': True,
            'owned_descendants_drained': True, 'runner_verification': verified,
            'receipt_sha256': sha(execution / 'receipt.json'), 'execution_manifest_sha256': sha(execution / 'manifest.json'),
            'runner_source_file_bindings_sha256': hashlib.sha256(json.dumps(source_map['files'], sort_keys=True,
                separators=(',', ':')).encode()).hexdigest(), 'source_file_count': len(source_map['files']),
            'scientific_acceptance': 'unverified'}


def main():
    require(not (OUT / 'combined-terminal01.json').exists(), 'Canonical terminal closeout already exists')
    attempts = OUT / 'terminal-verification-attempts'
    attempts.mkdir(exist_ok=True)
    require(stat.S_ISDIR(attempts.lstat().st_mode), 'Linked/special attempt directory')
    attempt = attempts / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex)
    attempt.mkdir()
    try:
        workspace = load(OUT / 'active-execution-workspace01.json')
        spec = load(OUT / 'execution-spec01.json')
        frozen = load(OUT / 'combined-source01.json')
        precheck = load(OUT / 'combined-binding-precheck01.json')
        recovery = load(OUT / 'recovery-execution02.json')
        execution, source = Path(workspace['execution_root']), Path(workspace['source'])
        recovery_root = Path(recovery['execution_root'])
        require(not execution.is_symlink() and not recovery_root.is_symlink() and not source.is_symlink(),
                'Linked execution/source root')
        require(not recovery_root.is_relative_to(execution) and not execution.is_relative_to(recovery_root),
                'Recovery overlaps the preserved failed attempt')
        manifest = load(execution / 'manifest.json')
        recovery_manifest = load(recovery_root / 'manifest.json')
        science = bind_inputs(workspace, spec, frozen, manifest, precheck)
        require(bind_recovery(workspace, spec, frozen, recovery_manifest, precheck, recovery) == science,
                'Recovery281 bindings differ')
        require(sha(RUNNER) == RUNNER_SHA and sha(Path(spec['wrapper'])) == spec['wrapper_sha256']
                and sha(Path(recovery['wrapper'])) == recovery['wrapper_sha256'], 'Runner/original/recovery wrapper bytes differ')
        # Both complete immutable-runner verifies and all output/source postguards
        # run only while the global compute slot is exclusively held.
        with SLOT.open('a+') as slot:
            fcntl.flock(slot, fcntl.LOCK_EX | fcntl.LOCK_NB)
            original = verify_runner_attempt('original-failed', workspace['execution_id'], execution,
                                             manifest, 'PROCESS_FAILED', 1, attempt)
            recovered = verify_runner_attempt('finalizer-recovery', recovery['execution_id'], recovery_root,
                                              recovery_manifest, 'PROCESS_EXITED', 0, attempt)
            count = verify_source(source, frozen)
            old_commands = load(execution / 'combined-commands.json')
            old_stages = load(execution / 'combined-resource-stages.json')
            failure = check_failed_wrapper(execution, spec, old_commands, old_stages)
            new_commands = load(recovery_root / 'combined-commands.json')
            new_stages = load(recovery_root / 'combined-resource-stages.json')
            require([row['label'] for row in new_commands] == ['finalization']
                    and all(row['returncode'] == 0 for row in new_commands), 'Recovery ran a component other than the missing finalizer')
            require([row['phase'] for row in new_stages] == ['payload-start', 'finalization-complete'], 'Recovery progress stages differ')
            require('Missing finalization regression completed; original wrapper failure retained; independent review required.'
                    in regular(recovery_root / 'stdout.log').read_text(), 'Recovery finalizer-only completion marker absent')
            require(not (recovery_root / 'combined-regfile').exists()
                    and not (recovery_root / 'unit-tests-console.log').exists(), 'Recovery unexpectedly reran completed seed/unit scope')
            check_stages(old_stages)
            check_stages(new_stages)
            outputs = {'regfile': execution / 'combined-regfile', 'finalizer': recovery_root / 'combined-finalization'}
            components = {key: check_component(path, science, frozen, key == 'finalizer') for key, path in outputs.items()}
            old_identity = {'execution_id': workspace['execution_id'], 'execution_root': str(execution)}
            new_identity = {'execution_id': recovery['execution_id'], 'execution_root': str(recovery_root)}
            component_commands = [{**row, 'attempt_role': 'original-failed', 'execution_id': workspace['execution_id']}
                                  for row in old_commands]
            component_commands += [{**row, 'attempt_role': 'finalizer-recovery', 'execution_id': recovery['execution_id']}
                                   for row in new_commands]
            identities = {name: sha(OUT / name) for name in ['active-execution-workspace01.json', 'execution-spec01.json',
                'combined-source01.json', 'combined-binding-precheck01.json', 'recovery-execution02.json']}
            record = {'schema': 'openrx.composite-closeout.v1',
                **old_identity, 'source': str(source), 'parents': PARENTS,
                'source_tree': workspace['source_tree'], 'source_archive_sha256': workspace['source_archive_sha256'],
                'terminal_success_and_integrity_verified': False, 'original_wrapper_succeeded': False,
                'composite_closeout_complete': True, 'recovery_wrapper_succeeded': True,
                'owned_descendants_drained': True, 'global_nonblocking_slot_free_at_verification': True,
                'complete_source_postcheck_files': count, 'exact_execute_masks_and_regular_entries_verified': True,
                'scientific_provenance_input_count': len(science), 'scientific_provenance_input_bindings': science,
                'coordination_receipt_sha256': identities, 'original_failure': failure,
                'runner_attempts': [original, recovered], 'component_outputs': {key: str(value) for key, value in outputs.items()},
                'component_records': components, 'component_commands': component_commands, 'commands': component_commands,
                'resource_stages_by_attempt': {'original-failed': old_stages, 'finalizer-recovery': new_stages},
                'unit_tests': 362, 'immutable_runner_sha256': RUNNER_SHA,
                'runner_verification': original['runner_verification'],
                'receipt_sha256': original['receipt_sha256'], 'execution_manifest_sha256': original['execution_manifest_sha256'],
                'verification_attempt': str(attempt),
                'attempt_receipts_sha256': {p.name: sha(p) for p in attempt.iterdir() if p.is_file()},
                'terminal_helper_sha256': sha(Path(__file__)),
                'scientific_acceptance': 'Composite coauthor closeout preserves failed original wrapper; exact-head independent review remains required.',
                'at_epoch': time.time()}
            save(OUT / 'combined-terminal01.json', record)
            save(attempt / 'outcome.json', {'status': 'pass_composite_component_closeout',
                                           'original_status': 'PROCESS_FAILED', 'recovery_status': 'PROCESS_EXITED',
                                           'canonical_record_sha256': sha(OUT / 'combined-terminal01.json')})
        print(json.dumps({key: value for key, value in record.items() if key not in
                          ('commands', 'component_commands', 'resource_stages_by_attempt', 'scientific_provenance_input_bindings')}, indent=2))
    except Exception as error:
        save(attempt / 'failure.json', {'status': 'failed_composite_verification', 'error': str(error), 'at_epoch': time.time()})
        raise


if __name__ == '__main__':
    main()
