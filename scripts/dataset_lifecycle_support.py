#!/usr/bin/env python3
"""Shared provenance and fixed-process supervision for the new dataset lifecycle.

Importing defines helpers only. Actual verification/process launches belong to
an independently admitted caller. Original component inputs/results stay read-only.
"""
import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n')


def _directory(path):
    value = Path(path)
    assert value.is_dir() and not value.is_symlink(), str(value)
    return value.resolve(strict=True)


def _regular(path):
    value = Path(path)
    assert value.is_file() and not value.is_symlink(), str(value)
    return value


def _under(root, relative):
    relative = PurePosixPath(relative)
    assert not relative.is_absolute() and relative.parts and not any(p in ['.', '..'] for p in relative.parts)
    path = root
    for i, part in enumerate(relative.parts):
        path = path / part
        assert not path.is_symlink(), str(path)
        assert path.is_file() if i == len(relative.parts)-1 else path.is_dir(), str(path)
    return path


def _identity(path):
    path = _regular(path)
    return {'bytes': path.stat().st_size, 'sha256': sha(path)}


def verify_assets(asset_root, lock_path, source_root, receipt=None, receipt_sha=None, verify=None):
    """Verify actual seven-file context identity, with optional raw-journal proof.

    The lock is a consumed committed source input. A CI extraction can establish
    byte identity to it without possession of the original private runner journal;
    that mode is explicitly not raw-journal integrity verification. Receipt mode
    additionally binds actual original artifact/source bytes to the pinned journal.
    """
    assets, source = _directory(asset_root), _directory(source_root)
    committed_lock = _under(source, 'rtl/dataset_service/dataset-context.lock.json')
    assert _regular(lock_path).resolve(strict=True) == committed_lock.resolve(strict=True)
    lock = load(committed_lock)
    assert lock['schema'] == 'openrx.dataset-lifecycle.prepared-cache-lock.v1'
    assert lock['cache_id'] == 0 and lock['cache_bytes'] == 268435456
    assert lock['key_hex'] == '74657374206b657920303030' and lock['prepared_programs'] == 8
    assert lock['global_reciprocal_entries'] == 239
    assert lock['native_pin'] == 'aaafe71322df6602c21a5c72937ac284724ae561'
    files, sources, accepted = lock['files'], lock['source_inputs'], lock['accepted_ip']
    assert len(files) == 7 and len(sources) == 181 and len(accepted) == 8
    actual_assets = {}
    for relative, expected in files.items():
        path = _under(assets, relative)
        actual_assets[relative] = _identity(path)
        assert actual_assets[relative] == expected, 'prepared context identity: ' + relative
    combined = dict(sources)
    for relative, expected in accepted.items():
        assert relative not in combined or combined[relative] == expected
        combined[relative] = expected
    for relative, expected in combined.items():
        assert _identity(_under(source, relative)) == expected, 'accepted source identity: ' + relative
    result = {'schema': 'openrx.dataset-lifecycle.asset-provenance.v1',
        'identity_verified_by_trusted_lock': True, 'raw_journal_verified': False,
        'verification_mode': 'trusted_committed_lock_only', 'asset_root': str(assets),
        'lock': {'path': str(committed_lock), **_identity(committed_lock)},
        'execution_id': lock['execution_id'], 'selected_fixture_files_verified': len(files),
        'selected_fixture_bytes': sum(r['bytes'] for r in actual_assets.values()),
        'source_inputs_verified': len(sources), 'accepted_ip_verified': len(accepted),
        'actual_current_source_files_verified': len(combined), 'assets': actual_assets,
        'retained_receipt_anchor_sha256': lock['receipt_sha256'],
        'retained_manifest_anchor_sha256': lock['manifest_sha256'],
        'retained_root_verify_anchor_sha256': lock['root_verify_sha256'],
        'native_or_component_validation_regenerated': False,
        'archive_bytes_rehashed': False,
        'boundary': 'Actual selected file/source identity only unless raw_journal_verified is true. Hosted archive metadata is not a local archive-byte verification claim.'}
    supplied = [receipt is not None, receipt_sha is not None, verify is not None]
    assert not any(supplied) or all(supplied), 'raw journal verification requires receipt, receipt_sha and verify together'
    if not any(supplied):
        return result
    receipt_path, verify_path = _regular(receipt).resolve(strict=True), _regular(verify).resolve(strict=True)
    assert re.fullmatch('[0-9a-f]{64}', receipt_sha)
    assert sha(receipt_path) == lock['receipt_sha256'] == receipt_sha
    assert sha(verify_path) == lock['root_verify_sha256']
    journal, checked = load(receipt_path), load(verify_path)
    assert journal['execution_id'] == checked['execution_id'] == lock['execution_id']
    assert journal['status'] == checked['status'] == 'PROCESS_EXITED'
    assert journal['process']['returncode'] == 0 and checked['integrity_verified'] is True
    rows = {Path(row['path']): row for row in journal['artifacts']}
    assert len(rows) == len(journal['artifacts'])

    def bound(path):
        row = rows[path]
        value = _identity(path)
        assert value == {'bytes': row['bytes'], 'sha256': row['sha256']}, str(path)
        return value

    manifest_path = _under(receipt_path.parent, 'manifest.json')
    manifest_identity = bound(manifest_path)
    assert manifest_identity['sha256'] == lock['manifest_sha256']
    manifest = load(manifest_path)
    assert manifest['execution_id'] == lock['execution_id']
    source_rows = [row for entry in manifest['sources'] for row in entry['files']]
    # The actual receipt-bound manifest is authority, not inputs.json claims.
    for relative, expected in combined.items():
        matches = [row for row in source_rows if row['relative'] == relative]
        assert len(matches) == 1, 'unique consumed source: ' + relative
        row = matches[0]
        assert {'bytes': row['bytes'], 'sha256': row['sha256']} == expected
        assert _identity(_under(source, relative)) == expected
    origin_rows = {}
    for relative, expected in files.items():
        original = _under(receipt_path.parent, 'output/fixtures/' + relative)
        assert bound(original) == expected
        origin_rows[relative] = {'path': str(original), **expected}
    result.update({'raw_journal_verified': True, 'verification_mode': 'trusted_lock_and_retained_raw_journal',
        'actual_prior_manifest_source_rows_verified': len(combined),
        'actual_prior_source_inputs_verified': len(sources), 'actual_prior_accepted_ip_verified': len(accepted),
        'actual_prior_fixture_artifact_rows_verified': len(origin_rows), 'raw_fixture_origins': origin_rows,
        'receipt': {'path': str(receipt_path), **_identity(receipt_path)},
        'manifest': {'path': str(manifest_path), **manifest_identity},
        'root_verify': {'path': str(verify_path), **_identity(verify_path)},
        'original_runner_scientific_acceptance': journal.get('scientific_acceptance', 'unavailable')})
    return result


def _process_group(pgid):
    """Accepted /proc observation method; only the original PGID/SID."""
    members = []
    ticks = os.sysconf('SC_CLK_TCK')
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            raw = (directory / 'stat').read_text()
            close = raw.rindex(')')
            fields = raw[close + 2:].split()
            if int(fields[2]) != pgid or int(fields[3]) != pgid:
                continue
            status = (directory / 'status').read_text()
            memory = {name: int(value) for name, value in re.findall(r'^(VmRSS|VmHWM):\s*(\d+) kB$', status, re.M)}
            members.append({'pid': int(directory.name), 'ppid': int(fields[1]),
                'process_group': int(fields[2]), 'session': int(fields[3]), 'state': fields[0],
                'comm': raw[raw.index('(') + 1:close], 'start_ticks': int(fields[19]),
                'user_ticks': int(fields[11]), 'system_ticks': int(fields[12]),
                'user_seconds': int(fields[11]) / ticks, 'system_seconds': int(fields[12]) / ticks,
                'threads': int(fields[17]), 'memory_kib': memory,
                'cmdline': (directory / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')})
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
            continue
    return sorted(members, key=lambda row: row['pid'])


class Supervisor:
    """Accepted held-leader group cleanup, packaged for the new admitted driver.

    This controls known fixed tools retaining the original process group/session;
    it does not promise containment of an escaped group/session. Runner cgroup
    containment remains the outer boundary. commands returns a locked snapshot.
    """
    def __init__(self, out):
        self.out = _directory(out)
        assert not (self.out / 'commands.json').exists(), 'fresh command ledger required'
        self._commands, self._labels, self._lock = [], set(), Lock()
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER unavailable')

    @property
    def commands(self):
        with self._lock:
            return copy.deepcopy(self._commands)

    def _persist(self):
        with self._lock:
            temporary = self.out / 'commands.json.tmp'
            save(temporary, self._commands)
            temporary.replace(self.out / 'commands.json')

    def run(self, label, argv, timeout=1800, env=None, expected_returncodes=(0,)):
        assert re.fullmatch('[-A-Za-z0-9_]+', label), 'unambiguous fresh log label required'
        assert timeout > 0 and expected_returncodes
        expected_returncodes = tuple(expected_returncodes)
        environment = dict(env) if env is not None else None
        row = {'label': label, 'argv': [str(x) for x in argv], 'cwd': str(ROOT),
               'timeout_seconds': timeout, 'expected_returncodes': list(expected_returncodes),
               'cleanup_scope': 'Original fixed-tool PGID/SID; runner cgroup is outer containment.'}
        if environment is not None:
            row['environment_overrides'] = {key: value for key, value in environment.items()
                                            if os.environ.get(key) != value}
        with self._lock:
            assert label not in self._labels, 'duplicate command/output label: ' + label
            self._labels.add(label)
            row_index = len(self._commands)
            self._commands.append(copy.deepcopy(row))
        self._persist()
        print('START ' + label, flush=True)
        began, timed_out, samples = time.monotonic(), False, []
        try:
            with (self.out / (label + '.log')).open('w') as log, (self.out / (label + '-process-samples.jsonl')).open('w') as observations:
                child = subprocess.Popen(row['argv'], cwd=row['cwd'], env=environment,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    row['process_group'] = child.pid
                    while True:
                        members = _process_group(child.pid)
                        sample = {'elapsed_seconds': time.monotonic()-began, 'members': members}
                        samples.append(sample)
                        observations.write(json.dumps(sample, sort_keys=True)+'\n')
                        observations.flush()
                        exited = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                        if exited is not None:
                            row['leader_exit_observed_without_reap'] = {'code': exited.si_code, 'status': exited.si_status}
                            break
                        remaining = timeout-(time.monotonic()-began)
                        if remaining <= 0:
                            timed_out = True
                            break
                        time.sleep(min(0.5, remaining))
                finally:
                    # Immediate post-spawn guard. No poll/wait before final signal;
                    # the waitable leader pins the numeric process-group identity.
                    pgid = child.pid
                    os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if os.getpgid(child.pid) != pgid or os.getsid(child.pid) != pgid:
                        raise RuntimeError('fixed-tool leader left original PGID/SID; no group signal sent')
                    try:
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    row['returncode'] = child.wait(timeout=2)
                    reaped, deadline = [], time.monotonic()+2
                    while True:
                        try:
                            pid, status = os.waitpid(-pgid, os.WNOHANG)
                            if pid:
                                reaped.append({'pid': pid, 'wait_status': status})
                                continue
                        except ChildProcessError:
                            pass
                        surviving = _process_group(pgid)
                        if not surviving:
                            break
                        if time.monotonic() >= deadline:
                            raise RuntimeError('process group remains after bounded kill/reap: '+repr(surviving))
                        time.sleep(0.02)
                    row['reaped_adopted_descendants'] = reaped
                    row['group_empty_after_cleanup'] = True
            row['wall_timeout'] = timed_out
            if timed_out:
                raise TimeoutError(label+' exceeded '+str(timeout)+' seconds')
            if row['returncode'] not in expected_returncodes:
                raise subprocess.CalledProcessError(row['returncode'], row['argv'])
        except BaseException as error:
            row['error'] = str(error)
            raise
        finally:
            row['elapsed_seconds'] = time.monotonic()-began
            observed = [member for sample in samples for member in sample['members']]
            row['resources'] = {'maximum_sampled_rss_kib': max((m['memory_kib'].get('VmRSS', 0) for m in observed), default=0),
                'maximum_observed_hwm_kib': max((m['memory_kib'].get('VmHWM', 0) for m in observed), default=0),
                'largest_sampled_process_cpu_seconds': max((m['user_seconds']+m['system_seconds'] for m in observed), default=0),
                'scope': 'Periodic /proc observations, not unsampled true peaks or complete descendant CPU accounting.'}
            with self._lock:
                self._commands[row_index] = copy.deepcopy(row)
            self._persist()
        print('PASS ' + label, flush=True)
        return copy.deepcopy(row)
