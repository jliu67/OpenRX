#!/usr/bin/env python3
"""Archive terminal combined component evidence; never run scientific payloads.

Invoke only after combined-terminal01.json and the exact evidence comparison
pass. All writes use new external paths. Inputs, old receipts, archives and the
frozen source are never changed. Complete opaque output archives stay on the
server; compact public records are explicitly partial views of those archives.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tarfile

sys.dont_write_bytecode = True
E = Path(__file__).resolve().parent
SLOT = Path('/home/server/openrx-local/v1/locks/execution.lock')
PARENTS = ['35c2cae61092107acb2c684bbca308aca8fb280b',
           '5f28dd4363504ecf33a8f10451c53405773c564f']
RUNNER_SHA = '657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b'
RUNNER_PATH = '/home/server/openrx-local/v1/releases/runner-v1-657b23f1/local_execution.py'
COMPOSITE_SCHEMA = 'openrx.composite-closeout.v1'
SHA_RE = re.compile(r'[0-9a-f]{64}')
MIB = 1024 ** 2
GIB = 1024 ** 3
BOUNDARIES = [
    'The original runner attempt failed after completed unit/seed commands; its wrapper failure remains a failure. A separate finalizer-only recovery supplies the missing component.',
    'Fresh combined-source component runs: 59 RTL modes, 36 mapped modes, six new-stage synthesis jobs and 362 unit tests.',
    'Exact original prepared219 and program-sequence73 input bytes support retained proof only; those suites were not rerun here.',
    'Seed chains use the default runtime-reciprocal backend. No complete prepared-mode hardware hash or new full8x2048 run is claimed.',
    'Default2MiB mapped finalizer checks are bounded restart controls, not full2MiB mapped hash completion.',
    'Export and comparison are coauthor preservation checks, not independent review or acceptance.',
    'Cells and fixture clocks establish no MHz, hash/s, watts, joules/hash or whole-system efficiency result.',
]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/linked JSON: ' + str(path))
    with path.open() as stream:
        return json.load(stream, object_pairs_hook=unique_object)


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def stream_sha(stream):
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(MIB), b''):
        digest.update(block)
        size += len(block)
    return digest.hexdigest(), size


def sha(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/linked file: ' + str(path))
    before = path.stat()
    with path.open('rb') as stream:
        digest, size = stream_sha(stream)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_mode) ==
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_mode) and size == before.st_size,
            'File changed while hashing: ' + str(path))
    return digest


def member(root, relative):
    require(isinstance(relative, str), 'Non-string member name')
    p = PurePosixPath(relative)
    require(relative and relative != '.' and not p.is_absolute() and '..' not in p.parts
            and '\\' not in relative and relative == p.as_posix(), 'Unsafe member: ' + relative)
    result = root / relative
    require(result.resolve().is_relative_to(root.resolve()), 'Escaping member: ' + relative)
    return result


def inventory(root):
    """Bind all files and directories, including omitted nested manifests."""
    require(root.is_dir() and not root.is_symlink(), 'Missing/linked inventory root')
    rows = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        require(not path.is_symlink() and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)),
                'Linked/special inventory member: ' + str(path))
        row = {'kind': 'directory' if path.is_dir() else 'file', 'mode': oct(stat.S_IMODE(info.st_mode)),
               'uid': info.st_uid, 'gid': info.st_gid, 'mtime_ns': info.st_mtime_ns}
        if row['kind'] == 'file':
            row.update(bytes=info.st_size, sha256=sha(path))
        rows[relative] = row
    return {'root': str(root), 'root_mode': oct(stat.S_IMODE(root.stat().st_mode)),
            'file_count': sum(row['kind'] == 'file' for row in rows.values()),
            'directory_count': sum(row['kind'] == 'directory' for row in rows.values()),
            'file_bytes': sum(row.get('bytes', 0) for row in rows.values()), 'members': rows}


def verify_artifacts(root, snapshot):
    """Honor root and nested driver maps; reject non-manifest unbound files."""
    top = root / 'artifacts.sha256.json'
    values = load(top)
    require(isinstance(values, dict) and values, 'Empty output artifact manifest')
    actual_files = {name for name, row in snapshot['members'].items() if row['kind'] == 'file'}
    verified_nested = []
    for path in [top, *(root / name for name in sorted(actual_files)
                       if name != top.name and PurePosixPath(name).name == 'artifacts.sha256.json')]:
        entries = load(path)
        require(isinstance(entries, dict) and entries, 'Empty nested artifact manifest: ' + str(path))
        for name, digest in entries.items():
            require(isinstance(digest, str) and SHA_RE.fullmatch(digest), 'Invalid artifact digest')
            item = member(path.parent, name)
            relative = item.relative_to(root).as_posix()
            require(relative in actual_files and snapshot['members'][relative]['sha256'] == digest,
                    'Artifact manifest mismatch: ' + relative)
        if path != top:
            verified_nested.append({'path': path.relative_to(root).as_posix(), 'sha256': sha(path),
                                    'bound_files': len(entries)})
    extras = actual_files - set(values) - {top.name}
    require(all(PurePosixPath(name).name == 'artifacts.sha256.json' for name in extras),
            'Non-manifest files absent from root output map: ' + repr(sorted(extras)))
    require(set(values) <= actual_files, 'Root output map references absent files')
    return {'root_manifest_sha256': sha(top), 'bound_files': len(values),
            'omitted_nested_manifests_verified': verified_nested, 'complete_inventory_verified': True}


def archive_output(root, snapshot, archive):
    """Serial streaming gzip/tar; preserve every original member mode and byte."""
    require(not archive.exists(), 'Archive already exists: ' + str(archive))
    with archive.open('xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode='w|', format=tarfile.PAX_FORMAT, dereference=True) as tar:
                tar.add(root, arcname='output', recursive=False)
                for relative in snapshot['members']:
                    tar.add(root / relative, arcname='output/' + relative, recursive=False)
    seen = set()
    root_seen = False
    with tarfile.open(archive, 'r|gz') as tar:
        for item in tar:
            if item.name == 'output':
                require(not root_seen and item.isdir() and item.mode == int(snapshot['root_mode'], 8),
                        'Archive root duplicated or mode changed')
                root_seen = True
                continue
            require(item.name.startswith('output/'), 'Unexpected archive prefix')
            relative = item.name[len('output/'):]
            member(root, relative)
            require(relative not in seen and relative in snapshot['members'], 'Extra/duplicate archive member')
            seen.add(relative)
            row = snapshot['members'][relative]
            require(item.mode == int(row['mode'], 8) and item.uid == row['uid'] and item.gid == row['gid'],
                    'Archive mode/ownership mismatch: ' + relative)
            if row['kind'] == 'directory':
                require(item.isdir(), 'Archive directory type changed: ' + relative)
            else:
                require(item.isfile() and item.size == row['bytes'], 'Archive file type/size changed: ' + relative)
                with tar.extractfile(item) as stream:
                    digest, size = stream_sha(stream)
                require(digest == row['sha256'] and size == row['bytes'], 'Archive bytes changed: ' + relative)
    require(root_seen and seen == set(snapshot['members']), 'Archive inventory mismatch')
    require(inventory(root) == snapshot, 'Output changed during archiving')
    return {'output': str(root), 'archive': str(archive), 'archive_sha256': sha(archive),
            'archive_bytes': archive.stat().st_size, 'file_count': snapshot['file_count'],
            'directory_count': snapshot['directory_count'],
            'complete_output_bytes_and_original_modes_verified': True,
            'every_archive_member_reverified': True, 'original_output_unmodified': True,
            'publication': 'Opaque archive retained on authorized server; not copied into compact public evidence.',
            'over_100MiB': archive.stat().st_size > 100 * MIB,
            'retrieval_limitation': 'Full binaries, netlists and large memory images require access to this retained server archive.'}


def verify_source(source, record, archive):
    require(source.is_dir() and not source.is_symlink(), 'Missing/linked frozen source root')
    require(sha(archive) == record['archive_sha256'], 'Frozen source archive SHA changed')
    require(record.get('complete_bytes_and_original_modes_verified') is True, 'Original source-mode receipt absent')
    expected = record['files']
    require(isinstance(expected, dict) and expected and len(expected) == record['file_count'], 'Source inventory absent')
    actual = set()
    for path in source.rglob('*'):
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode) and
                (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)),
                'Linked/special frozen source entry: ' + str(path))
        if stat.S_ISREG(info.st_mode):
            actual.add(path.relative_to(source).as_posix())
    require(actual == set(expected), 'Frozen source file inventory changed')
    for name, row in expected.items():
        path = member(source, name)
        require(sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'Frozen source bytes changed: ' + name)
        require((path.stat().st_mode & 0o111) == (int(row['mode'], 8) & 0o111),
                'Frozen source execution bits changed: ' + name)
    seen = set()
    with tarfile.open(archive, 'r|gz') as tar:
        for item in tar:
            require(item.name == 'source' or item.name.startswith('source/'), 'Source archive prefix changed')
            if item.isdir():
                continue
            name = item.name[len('source/'):]
            require(item.isfile() and name in expected and name not in seen, 'Source archive file inventory changed')
            seen.add(name)
            row = expected[name]
            require(item.mode == int(row['mode'], 8) and item.size == row['bytes'], 'Original source archive mode/size changed')
            with tar.extractfile(item) as stream:
                digest, size = stream_sha(stream)
            require(digest == row['sha256'] and size == row['bytes'], 'Source archive bytes changed: ' + name)
    require(seen == set(expected), 'Source archive omitted files')
    return {'source': str(source), 'staged_git_tree': record['staged_git_tree'], 'parents': record['parents'],
            'archive': str(archive), 'archive_sha256': record['archive_sha256'],
            'archive_bytes': archive.stat().st_size, 'original_file_modes_and_complete_bytes_reverified': True,
            'frozen_live_files_unchanged': True, 'file_count': len(expected),
            'archive_publication': 'Retained on server; full source inventory is published separately.'}


def prefix_derivative(value, prefixes):
    if isinstance(value, str):
        for prefix, role in prefixes:
            value = re.sub(re.escape(prefix) + r'(?=/|$)', lambda _: role, value)
        return value
    if isinstance(value, list):
        return [prefix_derivative(item, prefixes) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            renamed = prefix_derivative(key, prefixes)
            require(renamed not in result, 'Portable JSON key collision')
            result[renamed] = prefix_derivative(item, prefixes)
        return result
    return value


def publish_record(path, public, category, relative, prefixes, records):
    """Preserve exact raw data; path-normalized JSON is a distinct derivative."""
    digest = sha(path)
    info = path.stat()
    compress = path.suffix in ('.log', '.txt', '.stderr', '.stdout', '.jsonl')
    target = member(public, category + '/raw/' + relative + ('.gz' if compress else ''))
    target.parent.mkdir(parents=True, exist_ok=True)
    if compress:
        with target.open('xb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
                with path.open('rb') as stream:
                    shutil.copyfileobj(stream, zipped, MIB)
        with gzip.open(target, 'rb') as stream:
            decompressed, size = stream_sha(stream)
        require(decompressed == digest and size == info.st_size, 'Lossless log compression mismatch')
        target.chmod(stat.S_IMODE(info.st_mode))
    else:
        require(not target.exists(), 'Public raw file exists')
        shutil.copy2(path, target)
        require(sha(target) == digest, 'Public raw copy changed')
    require(sha(path) == digest and path.stat().st_mode == info.st_mode, 'Input changed during public copy')
    row = {'original_path': str(path), 'raw_original_sha256': digest, 'raw_original_bytes': info.st_size,
           'raw_original_mode': oct(stat.S_IMODE(info.st_mode)),
           'public_path': target.relative_to(public).as_posix(), 'public_sha256': sha(target),
           'public_bytes': target.stat().st_size,
           'encoding': 'lossless_gzip_of_exact_raw_bytes' if compress else 'exact_raw_bytes'}
    if path.suffix == '.json':
        portable = member(public, category + '/portable/' + relative)
        save_new(portable, prefix_derivative(load(path), prefixes))
        row['portable_derivative'] = {'path': portable.relative_to(public).as_posix(), 'sha256': sha(portable),
                                      'bytes': portable.stat().st_size,
                                      'kind': 'JSON_path_prefix_derivative_not_original_receipt'}
    records.append(row)


def selected_output(path):
    # Machine netlists and large memory payloads remain COMPLETE in the archive.
    # Science metadata and all logs are retained whole, without clipping.
    return ((path.suffix == '.json' and not path.name.startswith('netlist-')) or
            path.suffix in ('.log', '.txt', '.stderr', '.stdout', '.jsonl', '.ys') or
            path.name.startswith('LICENSE') or
            (path.suffix in ('.hex', '.mem', '.vh') and path.stat().st_size <= MIB))


def terminal_attempt_records(terminal, evidence=E):
    """Select only SHA-bound records from the one successful verification attempt.

    The canonical terminal record precedes outcome.json, so outcome.json is not
    one of its bound receipts. Other failed/successor attempts stay untouched and
    are not silently substituted for the named successful attempt.
    """
    evidence = Path(evidence).resolve()
    container = evidence / 'terminal-verification-attempts'
    attempt = Path(terminal['verification_attempt'])
    require(attempt.is_absolute() and attempt.parent == container and
            re.fullmatch(r'\d{8}T\d{6}Z-[0-9a-f]{32}', attempt.name) is not None,
            'Successful terminal attempt identity/path differs')
    require(container.is_dir() and not container.is_symlink() and attempt.is_dir()
            and not attempt.is_symlink() and attempt.resolve() == attempt,
            'Linked/missing successful terminal attempt directory')
    receipts = terminal['attempt_receipts_sha256']
    expected = {'runner-status.json', 'runner-integrity.json', 'terminal-service.txt'}
    if terminal.get('schema') == COMPOSITE_SCHEMA:
        expected = {prefix + '-' + name for prefix in ('original', 'recovery') for name in expected}
    require(isinstance(receipts, dict) and set(receipts) == expected,
            'Exact successful terminal receipt names required')
    selected = []
    for name, digest in sorted(receipts.items()):
        require(isinstance(digest, str) and SHA_RE.fullmatch(digest), 'Invalid terminal receipt digest')
        path = member(attempt, name)
        require(sha(path) == digest, 'Successful terminal receipt SHA differs: ' + name)
        selected.append((path, 'coordination/terminal-attempt', name))
    return selected


def gates(workspace, terminal, comparison):
    require(workspace['parents'] == PARENTS and workspace['immutable_runner_sha256'] == RUNNER_SHA,
            'Execution parent/immutable-runner identity differs')
    require(terminal['execution_id'] == workspace['execution_id'] and terminal['source'] == workspace['source']
            and terminal['execution_root'] == workspace['execution_root'], 'Terminal execution identity differs')
    require(terminal.get('terminal_success_and_integrity_verified') is True
            and terminal.get('owned_descendants_drained') is True
            and terminal.get('global_nonblocking_slot_free_at_verification') is True
            and terminal.get('unit_tests') == 362 and terminal.get('immutable_runner_sha256') == RUNNER_SHA,
            'Successful terminal/drain/integrity record required')
    require(comparison.get('status') == 'pass_evidence_comparison'
            and comparison.get('independent_review_or_acceptance') is False
            and comparison.get('source') == workspace['source'], 'Exact passing coauthor comparison required')
    for key, count in [('prepared_219', 219), ('program_sequence_73', 73)]:
        row = comparison['retained_source_bindings'][key]
        require(row['count'] == count and row['unchanged_count'] == count and row['all_unchanged'] is True
                and not row['mismatches'], 'Retained input identity differs')
    for key, counts, output in [('regfile', (18, 17), 'combined-regfile'),
                                 ('finalizer', (41, 19), 'combined-finalization')]:
        row = comparison[key]
        require(row['rtl_modes'] == counts[0] and row['mapped_modes'] == counts[1]
                and row['actual_synthesis_count'] == 3 and row['all_fresh_and_retained_logged_records_equal'] is True
                and Path(row['fresh_output']).resolve() == Path(workspace['execution_root']) / output,
                'Fresh comparison scope/output identity differs: ' + key)


def composite_gates(workspace, terminal, comparison, recovery):
    """Require two honest runner outcomes and successful component closeout."""
    require(terminal.get('schema') == COMPOSITE_SCHEMA and terminal.get('composite_closeout_complete') is True
            and terminal.get('original_wrapper_succeeded') is False
            and terminal.get('terminal_success_and_integrity_verified') is False,
            'Honest composite closeout with original wrapper failure required')
    require(workspace['parents'] == PARENTS and workspace['immutable_runner_sha256'] == RUNNER_SHA
            and terminal['execution_id'] == workspace['execution_id']
            and terminal['execution_root'] == workspace['execution_root'] and terminal['source'] == workspace['source'],
            'Original composite execution identity differs')
    require(terminal.get('owned_descendants_drained') is True
            and terminal.get('global_nonblocking_slot_free_at_verification') is True
            and terminal.get('unit_tests') == 362 and terminal.get('immutable_runner_sha256') == RUNNER_SHA,
            'Composite drain/unit/immutable-runner verification absent')
    require(recovery['source'] == workspace['source'] and recovery['immutable_runner_sha256'] == RUNNER_SHA
            and recovery['runner'] == RUNNER_PATH and recovery['execution_id'] != workspace['execution_id'],
            'Recovery source/runner identity differs')
    for name in ('source_tree', 'parents', 'source_archive_sha256'):
        if name in recovery:
            require(recovery[name] == workspace[name], 'Optional recovery source identity differs: ' + name)
    for name in ('request_key', 'wrapper', 'wrapper_sha256'):
        require(isinstance(recovery[name], str) and recovery[name], 'Recovery binding absent: ' + name)
    require(SHA_RE.fullmatch(recovery['wrapper_sha256']), 'Recovery wrapper digest invalid')
    attempts = terminal['runner_attempts']
    require(isinstance(attempts, list) and len(attempts) == 2
            and [row['role'] for row in attempts] == ['original-failed', 'finalizer-recovery'], 'Exact runner attempt roles required')
    for row, identity, expected_status, rc in zip(attempts, (workspace, recovery), ('PROCESS_FAILED', 'PROCESS_EXITED'), (1, 0)):
        require(row['execution_id'] == identity['execution_id'] and row['execution_root'] == identity['execution_root']
                and row['status'] == expected_status and row['returncode'] == rc
                and row['integrity_verified'] is True and row['owned_descendants_drained'] is True,
                'Original failure/recovery success identity differs: ' + row['role'])
        require(row['runner_verification']['execution_id'] == identity['execution_id']
                and row['runner_verification']['status'] == expected_status
                and row['runner_verification']['integrity_verified'] is True,
                'Runner integrity receipt identity differs: ' + row['role'])
        require(SHA_RE.fullmatch(row['receipt_sha256']) and SHA_RE.fullmatch(row['execution_manifest_sha256']),
                'Attempt receipt/manifest digest invalid')
    require(terminal['receipt_sha256'] == attempts[0]['receipt_sha256'], 'Canonical original-failure receipt differs')
    outputs = {'regfile': str(Path(workspace['execution_root']) / 'combined-regfile'),
               'finalizer': str(Path(recovery['execution_root']) / 'combined-finalization')}
    require(terminal['component_outputs'] == outputs, 'Composite component source/output selection differs')
    require(comparison.get('status') == 'pass_evidence_comparison'
            and comparison.get('independent_review_or_acceptance') is False
            and comparison.get('source') == workspace['source'], 'Exact passing coauthor comparison required')
    for key, count in [('prepared_219', 219), ('program_sequence_73', 73)]:
        row = comparison['retained_source_bindings'][key]
        require(row['count'] == count and row['unchanged_count'] == count and row['all_unchanged'] is True
                and not row['mismatches'], 'Retained input identity differs')
    for key, counts in [('regfile', (18, 17)), ('finalizer', (41, 19))]:
        row = comparison[key]
        require(row['rtl_modes'] == counts[0] and row['mapped_modes'] == counts[1]
                and row['actual_synthesis_count'] == 3 and row['all_fresh_and_retained_logged_records_equal'] is True
                and Path(row['fresh_output']).resolve() == Path(outputs[key]),
                'Composite fresh comparison scope/output differs: ' + key)


def component_inventory(snapshot, root):
    """Derive a complete component view from the full runner inventory."""
    parent = Path(snapshot['root'])
    relative = root.relative_to(parent).as_posix()
    require(relative in snapshot['members'] and snapshot['members'][relative]['kind'] == 'directory',
            'Component root is absent from runner inventory')
    rows = {name[len(relative) + 1:]: row for name, row in snapshot['members'].items() if name.startswith(relative + '/')}
    require(rows, 'Empty component inventory')
    return {'root': str(root), 'root_mode': snapshot['members'][relative]['mode'],
            'file_count': sum(row['kind'] == 'file' for row in rows.values()),
            'directory_count': sum(row['kind'] == 'directory' for row in rows.values()),
            'file_bytes': sum(row.get('bytes', 0) for row in rows.values()), 'members': rows}


def verify_original_failure(stderr, spec, terminal):
    """Bind the original diagnostic to the canonical verified raw SHA.

    Match its complete content, without assuming a Python traceback line count.
    The terminal helper already verified this exact external-wrapper failure.
    """
    failure = terminal['original_failure']
    require(failure['diagnostic'] == "KeyError: 'status'" and failure['external_wrapper_line'] == 70
            and failure['original_wrapper_succeeded'] is False and failure['native_component_driver_returncode'] == 0
            and failure['unit_tests'] == 362 and failure['finalization_started_in_original'] is False,
            'Canonical original-wrapper diagnostic identity differs')
    require(isinstance(failure['stderr_sha256'], str) and SHA_RE.fullmatch(failure['stderr_sha256'])
            and sha(stderr) == failure['stderr_sha256'], 'Original failed-wrapper stderr SHA differs from terminal')
    expected = ('Traceback (most recent call last):\n  File "' + spec['wrapper'] +
                '", line 70, in <module>\n    assert summary[\'status\']==\'pass\',summary\nKeyError: \'status\'\n')
    require(stderr.read_text() == expected,
            'Original failed-wrapper diagnostic differs; never relabel it as success')


def headroom(archive_paths, raw_bytes):
    memory = {line.split(':')[0]: int(line.split()[1]) * 1024
              for line in Path('/proc/meminfo').read_text().splitlines()}
    require(memory['MemAvailable'] >= 2 * GIB, 'Fresh 2GiB available-memory headroom required')
    needed = raw_bytes + raw_bytes // 20 + 2 * GIB
    devices = {}
    for path in archive_paths:
        parent = path.parent
        require(parent.is_dir(), 'External archive/public parent missing')
        devices.setdefault(parent.stat().st_dev, parent)
    disks = []
    for parent in devices.values():
        free = shutil.disk_usage(parent).free
        require(free >= needed, 'Fresh disk headroom insufficient: ' + str(parent))
        disks.append({'path': str(parent), 'available_bytes': free, 'required_bytes': needed})
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split(':')[-1].lstrip('/')
    limits = {name: (cg / name).read_text().strip() for name in
              ('cpu.max', 'memory.max', 'memory.current', 'memory.swap.max', 'pids.max', 'pids.current')
              if (cg / name).exists()}
    if limits.get('memory.max') not in (None, 'max'):
        require(int(limits['memory.max']) - int(limits['memory.current']) >= 128 * MIB,
                'Exporter cgroup has less than 128MiB unused memory')
    return {'created_utc': datetime.now(timezone.utc).isoformat(), 'global_nonblocking_slot': True,
            'MemAvailable': memory['MemAvailable'], 'SwapFree': memory['SwapFree'],
            'minimum_MemAvailable': 2 * GIB, 'disks': disks, 'actual_exporter_cgroup': str(cg),
            'kernel_limits': limits, 'workers': 1, 'scope': 'Serial streaming evidence archive/copy only; no scientific execution.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison-report', type=Path, default=E / 'combined-evidence-comparison01.json')
    parser.add_argument('--public-folder', type=Path, default=E / 'public-combined-evidence01')
    parser.add_argument('--original-attempt-archive', type=Path, default=E / 'combined-original-failed-execution01.tar.gz')
    parser.add_argument('--recovery-attempt-archive', type=Path, default=E / 'combined-finalizer-recovery-execution02.tar.gz')
    parser.add_argument('--result', type=Path, default=E / 'export-combination01-result.json')
    args = parser.parse_args()
    workspace = load(E / 'active-execution-workspace01.json')
    terminal = load(E / 'combined-terminal01.json')
    recovery = load(E / 'recovery-execution02.json')
    comparison_path = args.comparison_report.resolve()
    comparison = load(comparison_path)
    composite_gates(workspace, terminal, comparison, recovery)
    require(not Path(workspace['source']).is_symlink(), 'Frozen source root cannot be a symlink')
    source = Path(workspace['source']).resolve()
    execution = Path(workspace['execution_root']).resolve()
    require(not Path(recovery['execution_root']).is_symlink(), 'Linked recovery execution root')
    runner_roots = {'original-failed': execution, 'finalizer-recovery': Path(recovery['execution_root']).resolve()}
    require(runner_roots['original-failed'] != runner_roots['finalizer-recovery'] and
            not any(a.is_relative_to(b) for a, b in ((runner_roots['original-failed'], runner_roots['finalizer-recovery']),
                                                   (runner_roots['finalizer-recovery'], runner_roots['original-failed']))),
            'Runner attempt directories overlap')
    roots = {'regfile': Path(terminal['component_outputs']['regfile']).resolve(),
             'finalization': Path(terminal['component_outputs']['finalizer']).resolve()}
    component_roles = {'regfile': 'original-failed', 'finalization': 'finalizer-recovery'}
    protected = [source, *runner_roots.values(), *(Path(comparison[key]['retained_output']['selected_output']).resolve()
                                    for key in ('regfile', 'finalizer'))]
    public = args.public_folder.resolve()
    archive_paths = {'original-failed': args.original_attempt_archive.resolve(),
                     'finalizer-recovery': args.recovery_attempt_archive.resolve()}
    result_path = args.result.resolve()
    destinations = [public, *archive_paths.values(), result_path]
    require(len(set(destinations)) == len(destinations), 'Export destinations overlap')
    for path in destinations:
        require(not path.exists() and path.parent.is_dir(), 'Fresh external destination required: ' + str(path))
        require(not any(path.is_relative_to(root) or root.is_relative_to(path) for root in protected),
                'Destination overlaps frozen/fresh/retained inputs: ' + str(path))
    require(all(not other.is_relative_to(public) for other in [*archive_paths.values(), result_path]),
            'Opaque archive/result must remain outside compact public folder')
    with SLOT.open('a+') as slot:
        fcntl.flock(slot, fcntl.LOCK_EX | fcntl.LOCK_NB)
        resource = headroom(destinations, 0)
        terminal_metadata = terminal_attempt_records(terminal)
        attempts = {row['role']: row for row in terminal['runner_attempts']}
        manifests = {}
        for role, root in runner_roots.items():
            row = attempts[role]
            require(sha(root / 'receipt.json') == row['receipt_sha256'] and
                    sha(root / 'manifest.json') == row['execution_manifest_sha256'], 'Attempt receipt/manifest SHA differs: ' + role)
            process, receipt = load(root / 'process-result.json'), load(root / 'receipt.json')
            require(process['status'] == row['status'] and process['returncode'] == row['returncode']
                    and receipt['execution_id'] == row['execution_id'] and receipt['status'] == row['status']
                    and receipt['process'] == process, 'Actual attempt process/receipt outcome differs: ' + role)
            manifests[role] = load(root / 'manifest.json')
        spec = load(E / 'execution-spec01.json')
        verify_original_failure(execution / 'stderr.log', spec, terminal)
        require(sha(E / 'compare_combined_outputs.py') == comparison['comparison_helper_sha256'],
                'Comparison helper changed after comparison')
        actual_commands = []
        for role, root in runner_roots.items():
            commands = load(root / 'combined-commands.json')
            labels = ['existing-and-focused-unit-tests', 'regfile'] if role == 'original-failed' else ['finalization']
            require([row['label'] for row in commands] == labels and all(row['returncode'] == 0 for row in commands),
                    'Actual component command completion differs: ' + role)
            actual_commands += [{**row, 'attempt_role': role, 'execution_id': attempts[role]['execution_id']} for row in commands]
            stages = load(root / 'combined-resource-stages.json')
            require(stages == terminal['resource_stages_by_attempt'][role], 'Attempt resource-stage record changed')
            for row in stages:
                require(all(row['kernel'].get(key) == value for key, value in {
                    'cpu.max': '600000 100000', 'memory.max': '4294967296',
                    'memory.swap.max': '2147483648', 'pids.max': '256'}.items()), 'Measured execution resource profile differs')
        require(actual_commands == terminal['component_commands'], 'Composite command attribution differs')
        runner_snapshots = {role: inventory(root) for role, root in runner_roots.items()}
        snapshots = {key: component_inventory(runner_snapshots[component_roles[key]], root) for key, root in roots.items()}
        resource = headroom(destinations, sum(row['file_bytes'] for row in runner_snapshots.values()))
        for key, root in roots.items():
            require(not (root / 'failure.json').exists(), 'Failed component output present')
            artifact_check = verify_artifacts(root, snapshots[key])
            comparison_key = 'finalizer' if key == 'finalization' else key
            prior = comparison[comparison_key]['fresh_complete_manifest']
            require(artifact_check['root_manifest_sha256'] == prior['sha256'],
                    'Compared fresh artifact manifest changed: ' + key)
            omitted = {}
            for row in prior['separately_verified_omitted_nested_manifests']:
                path = Path(row['path']).resolve()
                require(path.is_relative_to(root), 'Compared nested manifest path escaped output')
                omitted[path.relative_to(root).as_posix()] = row['sha256']
            values = load(root / 'artifacts.sha256.json')
            extras = {name for name, row in snapshots[key]['members'].items() if row['kind'] == 'file'} - set(values) - {'artifacts.sha256.json'}
            require(set(omitted) == extras and all(snapshots[key]['members'][name]['sha256'] == digest
                                                 for name, digest in omitted.items()),
                    'Compared omitted nested manifest set/bytes changed: ' + key)
            require(sha(root / 'inputs.json') == comparison[comparison_key]['fresh_source_bindings']['sha256'],
                    'Compared executable input map changed: ' + key)
        source_record = load(E / 'combined-source01.json')
        require(source_record['source'] == str(source) and source_record['parents'] == PARENTS
                and source_record['staged_git_tree'] == workspace['source_tree'], 'Frozen source identity differs')
        source_archive = Path(workspace['source_archive']).resolve()
        require(source_record['archive_sha256'] == workspace['source_archive_sha256'], 'Source archive receipt differs')
        source_retention = verify_source(source, source_record, source_archive)
        for role, manifest in manifests.items():
            identity = spec if role == 'original-failed' else recovery
            require(manifest['execution_id'] == attempts[role]['execution_id'] and manifest['cwd'] == str(source)
                    and manifest['request_key'] == identity['request_key'] and manifest['runner']['sha256'] == RUNNER_SHA
                    and manifest['runner']['path'] == RUNNER_PATH, 'Actual runner manifest identity differs')
            sources = manifest['sources']
            require(len(sources) == 1 and sources[0]['path'] == str(source) and sources[0]['kind'] == 'directory',
                    'Actual runner source-directory binding differs')
            bound = {row['relative']: row for row in sources[0]['files']}
            require(len(bound) == len(sources[0]['files']) and set(bound) == set(source_record['files'])
                    and all(row['sha256'] == source_record['files'][name]['sha256']
                            and row['bytes'] == source_record['files'][name]['bytes'] for name, row in bound.items()),
                    'Actual runner/frozen complete source bindings differ')
            require(manifest['argv'][1:] == ['-B', identity['wrapper'], str(source), str(runner_roots[role])]
                    and sha(Path(identity['wrapper'])) == identity['wrapper_sha256'], 'Executed wrapper/live binding differs')
            wrapper_rows = [row for row in manifest['inputs'] if row['path'] == identity['wrapper']]
            require(len(wrapper_rows) == 1 and wrapper_rows[0]['sha256'] == identity['wrapper_sha256'],
                    'Executed wrapper input digest differs')
        archives = {role: {**archive_output(root, runner_snapshots[role], archive_paths[role]),
                           'archive_root': 'output', 'tree_kind': 'complete_runner_execution_directory',
                           'execution_id': attempts[role]['execution_id'], 'role': role,
                           'original_runner_status': attempts[role]['status'], 'original_returncode': attempts[role]['returncode']}
                    for role, root in runner_roots.items()}
        public.mkdir()
        prefixes = [(str(source), '<FROZEN_SOURCE>'), (str(execution), '<ORIGINAL_FAILED_EXECUTION_ROOT>'),
                    (str(runner_roots['finalizer-recovery']), '<FINALIZER_RECOVERY_EXECUTION_ROOT>'), (str(E), '<EXTERNAL_EVIDENCE>')]
        prefixes += [(comparison[key]['retained_output']['selected_output'], '<RETAINED_' + key.upper() + '_OUTPUT>')
                     for key in ('regfile', 'finalizer')]
        prefixes.sort(key=lambda pair: len(pair[0]), reverse=True)
        records = []
        selections = {}
        for key, root in roots.items():
            selected = []
            for relative, row in snapshots[key]['members'].items():
                if row['kind'] == 'file' and selected_output(root / relative):
                    publish_record(root / relative, public, key, relative, prefixes, records)
                    selected.append(relative)
            commands = load(root / 'commands.json')
            require(all(row['label'] + '.log' in selected for row in commands), 'A positive/negative command log was omitted')
            require(all(name in selected for name in ('summary.json', 'commands.json', 'inputs.json',
                                                       'artifacts.sha256.json', 'preserved-inputs.json', 'tools.json')),
                    'Required science/source record omitted')
            selections[key] = {'selected_raw_files': selected,
                               'archive_only_files': sorted(name for name, row in snapshots[key]['members'].items()
                                                            if row['kind'] == 'file' and name not in selected),
                               'public_view_is_complete_output': False,
                               'all_positive_and_negative_command_logs_preserved_losslessly': True}
        metadata = [(path, 'coordination', path.name) for path in sorted(E.iterdir())
                    if path.is_file() and path.suffix in ('.json', '.jsonl', '.txt', '.log', '.stderr', '.stdout')]
        metadata += [(E / name, 'helpers', name) for name in (
            'export_combination01.py', 'run_combined_regressions01.py', 'verify_terminal01.py', 'compare_combined_outputs.py')]
        metadata.append((Path(recovery['wrapper']), 'helpers', Path(recovery['wrapper']).name))
        # Helper fixture scripts/results are coauthor preservation checks. Their
        # counts are separate from the 362 admitted repository unit tests.
        metadata += [(path, 'helpers/coauthor-fixtures', path.name) for path in sorted(E.glob('test_*_fixtures*.py'))]
        fixture_helper = E / 'test_terminal_publication_helpers01.py'
        if fixture_helper.is_file():
            metadata.append((fixture_helper, 'helpers/coauthor-fixtures', fixture_helper.name))
        metadata += [(path, 'helpers/preserved-exporter-history', path.name)
                     for path in sorted(E.glob('export_combination01.pre-*.py'))]
        metadata += terminal_metadata
        for role, root in runner_roots.items():
            metadata += [(path, 'execution/' + role, path.name) for path in sorted(root.iterdir())
                         if path.is_file() and path.suffix in ('.json', '.jsonl', '.log', '.txt')]
        require(any(path == comparison_path for path, _, _ in metadata), 'Comparison report must be an external E metadata file')
        for path, category, relative in metadata:
            publish_record(path, public, category, relative, prefixes, records)
        for key, snapshot in snapshots.items():
            save_new(public / 'retention' / (key + '-complete-inventory.json'), snapshot)
        for role, snapshot in runner_snapshots.items():
            save_new(public / 'retention' / (role + '-complete-runner-inventory.json'), snapshot)
        coverage = {key: {'original_output': str(root), 'runner_role': component_roles[key],
                          'execution_id': attempts[component_roles[key]]['execution_id'],
                          'archive': archives[component_roles[key]]['archive'],
                          'archive_sha256': archives[component_roles[key]]['archive_sha256'], 'archive_root': 'output',
                          'component_root_member_prefix': 'output/' + root.relative_to(runner_roots[component_roles[key]]).as_posix(),
                          'complete_component_inventory': 'retention/' + key + '-complete-inventory.json',
                          'complete_component_inventory_sha256': sha(public / 'retention' / (key + '-complete-inventory.json')),
                          'separate_duplicate_component_archive_created': False} for key, root in roots.items()}
        save_new(public / 'source-output-retention.json', {'schema': 'openrx-combined-retention-v2-composite',
            'source': source_retention, 'complete_runner_attempts': archives, 'complete_component_coverage': coverage,
            'original_wrapper_outcome': 'PROCESS_FAILED returncode1; completed unit/seed commands retained as component evidence',
            'finalizer_recovery_outcome': 'PROCESS_EXITED returncode0', 'export_headroom': resource,
            'raw_public_selection': selections, 'portable_prefixes': dict(prefixes), 'boundaries': BOUNDARIES,
            'successful_terminal_attempt_receipts': terminal['attempt_receipts_sha256'],
            'terminal_attempt_public_prefix': 'coordination/terminal-attempt',
            'coauthor_helper_fixtures_are_separate_from_362_repository_unit_tests': True,
            'independent_review_or_acceptance': False})
        ledger = {'fresh_scope': {'rtl_modes': 59, 'mapped_modes': 36, 'actual_new_stage_synthesis': 6, 'unit_tests': 362},
                  'original_wrapper_succeeded': False, 'composite_closeout_complete': True,
                  'runner_attempt_outcomes': [{'role': role, 'execution_id': row['execution_id'],
                                               'status': row['status'], 'returncode': row['returncode']} for role, row in attempts.items()],
                  'retained_scope_only': comparison['retained_source_bindings'],
                  'actual_PASS_records': {key: comparison[key]['actual_logged_PASS_records'] for key in ('regfile', 'finalizer')},
                  'actual_mapping_records': {key: comparison[key]['actual_mapping'] for key in ('regfile', 'finalizer')},
                  'component_profiles': {key: {name: value for name, value in comparison[key].items() if name in
                      ('profile_clocks', 'full_ABBA_trials', 'mapped_scope', 'connected_scope', 'expected_failures', 'native_cases',
                       'native_register_digests', 'full_chain_rerun')} for key in ('regfile', 'finalizer')},
                  'no_full_pipeline_or_efficiency_claim': True, 'boundaries': BOUNDARIES}
        save_new(public / 'science-ledger.json', ledger)
        save_new(public / 'raw-public-preservation-map.json', {'records': records,
            'raw_SHA_identity_is_separate_from_portable_derivative_SHA': True,
            'portable_derivatives_are_not_original_receipts': True})
        require(sum(path.stat().st_size for path in public.rglob('*') if path.is_file()) <= 100 * MIB,
                'Compact public folder exceeds 100MiB; preserve attempt and choose a separately reviewed selection')
        # Check raw inputs and both directories again after all copies. Never chmod
        # or rewrite them; archives are additional preserved representations.
        for role, root in runner_roots.items():
            require(inventory(root) == runner_snapshots[role], 'Runner execution directory changed during export')
        for row in records:
            require(sha(Path(row['original_path'])) == row['raw_original_sha256'], 'Metadata/log source changed during export')
        public_inventory = inventory(public)
        save_new(public / 'public-files.sha256.json', {name: row['sha256'] for name, row in public_inventory['members'].items()
                                                      if row['kind'] == 'file'})
        require({p.relative_to(public).as_posix() for p in public.rglob('*') if p.is_file()} ==
                set(load(public / 'public-files.sha256.json')) | {'public-files.sha256.json'}, 'Public inventory incomplete')
        for name, digest in load(public / 'public-files.sha256.json').items():
            require(sha(public / name) == digest, 'Public final SHA verification failed')
        result = {'status': 'pass_preservation_export', 'created_utc': datetime.now(timezone.utc).isoformat(),
                  'public_folder': str(public), 'public_file_count': public_inventory['file_count'] + 1,
                  'public_manifest_sha256': sha(public / 'public-files.sha256.json'),
                  'complete_runner_attempt_archives': archives, 'complete_component_coverage': coverage,
                  'source': source_retention, 'original_failed_execution_id': workspace['execution_id'],
                  'finalizer_recovery_execution_id': recovery['execution_id'],
                  'terminal_record_raw_sha256': sha(E / 'combined-terminal01.json'),
                  'comparison_record_raw_sha256': sha(comparison_path), 'exporter_sha256': sha(Path(__file__).resolve()),
                  'scope': BOUNDARIES, 'independent_review_or_acceptance': False}
        save_new(result_path, result)
        print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, tarfile.TarError) as error:
        # Preserve partial attempts. No overwrite, deletion, chmod, retry or
        # publication takes place on failure; a successor must use fresh paths.
        print('Export did not complete; preserve this attempt: ' + str(error), file=sys.stderr)
        sys.exit(1)
