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
SHA_RE = re.compile(r'[0-9a-f]{64}')
MIB = 1024 ** 2
GIB = 1024 ** 3
BOUNDARIES = [
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
    parser.add_argument('--regfile-archive', type=Path, default=E / 'combined-regfile-output01.tar.gz')
    parser.add_argument('--finalization-archive', type=Path, default=E / 'combined-finalization-output01.tar.gz')
    parser.add_argument('--result', type=Path, default=E / 'export-combination01-result.json')
    args = parser.parse_args()
    workspace = load(E / 'active-execution-workspace01.json')
    terminal = load(E / 'combined-terminal01.json')
    comparison_path = args.comparison_report.resolve()
    comparison = load(comparison_path)
    gates(workspace, terminal, comparison)
    require(not Path(workspace['source']).is_symlink(), 'Frozen source root cannot be a symlink')
    source = Path(workspace['source']).resolve()
    execution = Path(workspace['execution_root']).resolve()
    roots = {'regfile': execution / 'combined-regfile', 'finalization': execution / 'combined-finalization'}
    protected = [source, execution, *(Path(comparison[key]['retained_output']['selected_output']).resolve()
                                    for key in ('regfile', 'finalizer'))]
    public = args.public_folder.resolve()
    archive_paths = {'regfile': args.regfile_archive.resolve(), 'finalization': args.finalization_archive.resolve()}
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
        require(sha(execution / 'receipt.json') == terminal['receipt_sha256'], 'Terminal receipt SHA differs')
        process = load(execution / 'process-result.json')
        require(process['returncode'] == 0 and process['status'] == 'PROCESS_EXITED', 'Actual process success absent')
        require(sha(E / 'compare_combined_outputs.py') == comparison['comparison_helper_sha256'],
                'Comparison helper changed after comparison')
        require([row['label'] for row in terminal['commands']] ==
                ['existing-and-focused-unit-tests', 'regfile', 'finalization']
                and all(row['returncode'] == 0 for row in terminal['commands']), 'Terminal command ledger differs')
        require(load(execution / 'combined-commands.json') == terminal['commands'], 'Actual command ledger changed')
        for row in terminal['resource_stages']:
            require(all(row['kernel'].get(key) == value for key, value in {
                'cpu.max': '600000 100000', 'memory.max': '4294967296',
                'memory.swap.max': '2147483648', 'pids.max': '256'}.items()), 'Measured execution resource profile differs')
        snapshots = {key: inventory(root) for key, root in roots.items()}
        resource = headroom(destinations, sum(row['file_bytes'] for row in snapshots.values()))
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
        archives = {key: archive_output(root, snapshots[key], archive_paths[key]) for key, root in roots.items()}
        public.mkdir()
        prefixes = [(str(source), '<FROZEN_SOURCE>'), (str(execution), '<EXECUTION_ROOT>'), (str(E), '<EXTERNAL_EVIDENCE>')]
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
                    if path.is_file() and path.suffix in ('.json', '.txt', '.log', '.stderr')]
        metadata += [(E / name, 'helpers', name) for name in (
            'export_combination01.py', 'run_combined_regressions01.py', 'verify_terminal01.py', 'compare_combined_outputs.py')]
        metadata += [(path, 'execution', path.name) for path in sorted(execution.iterdir())
                     if path.is_file() and path.suffix in ('.json', '.jsonl', '.log', '.txt')]
        require(any(path == comparison_path for path, _, _ in metadata), 'Comparison report must be an external E metadata file')
        for path, category, relative in metadata:
            publish_record(path, public, category, relative, prefixes, records)
        for key, snapshot in snapshots.items():
            save_new(public / 'retention' / (key + '-complete-inventory.json'), snapshot)
        save_new(public / 'source-output-retention.json', {'schema': 'openrx-combined-retention-v1',
            'source': source_retention, 'complete_outputs': archives, 'export_headroom': resource,
            'raw_public_selection': selections, 'portable_prefixes': dict(prefixes), 'boundaries': BOUNDARIES,
            'independent_review_or_acceptance': False})
        ledger = {'fresh_scope': {'rtl_modes': 59, 'mapped_modes': 36, 'actual_new_stage_synthesis': 6, 'unit_tests': 362},
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
        for key, root in roots.items():
            require(inventory(root) == snapshots[key], 'Fresh output changed during export')
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
                  'archives': archives, 'source': source_retention, 'execution_id': workspace['execution_id'],
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
