#!/usr/bin/env python3
"""Compare completed combined-tree component runs with preserved raw evidence.

This external evidence helper runs no compiler, simulator, native executable,
network operation or repository script. Invoke only after the manager releases
the serialized execution slot. It reads complete output manifests (potentially
about a GiB), and writes exactly one NEW JSON report outside all input trees.
It is a coauthor comparison, not independent review or scientific acceptance.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


REGFILE = 'docs/validation/regfile-blake2b-20261013'
FINALIZER = 'docs/validation/scratchpad-finalization-20261013'
PREPARED = 'docs/validation/prepared-reciprocals/server/inputs.json'
SEQUENCE = 'docs/validation/prepared-reciprocals/program-sequence-regression/inputs.json'
SHA_RE = re.compile(r'[0-9a-f]{64}')
HASH_CACHE = {}


class ComparisonFailure(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise ComparisonFailure(message)


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


def sha(path):
    require(path.is_file() and not path.is_symlink(), 'Missing/linked file: ' + str(path))
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if key not in HASH_CACHE:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        HASH_CACHE[key] = digest.hexdigest()
    return HASH_CACHE[key]


def member(root, relative):
    require(isinstance(relative, str), 'Manifest path is not a string')
    p = PurePosixPath(relative)
    require(not p.is_absolute() and '..' not in p.parts and relative == p.as_posix()
            and relative not in ('', '.'), 'Unsafe manifest path: ' + relative)
    result = root / relative
    require(result.resolve().is_relative_to(root.resolve()), 'Escaping input path: ' + relative)
    return result


def verify_manifest(root, manifest_path, complete=False):
    manifest = load(manifest_path)
    require(isinstance(manifest, dict) and manifest, 'Empty/non-object manifest: ' + str(manifest_path))
    total_bytes = 0
    for relative, expected in manifest.items():
        require(isinstance(expected, str) and SHA_RE.fullmatch(expected),
                'Invalid SHA256 in ' + str(manifest_path) + ': ' + relative)
        path = member(root, relative)
        require(sha(path) == expected, 'Artifact SHA256 mismatch: ' + str(path))
        total_bytes += path.stat().st_size
    omitted_nested_manifests = []
    if complete:
        # Regfile's original driver excluded ALL files named artifacts.sha256.json;
        # finalizer excluded only its root manifest. Verify any omitted nested
        # manifest separately, and reject every other unbound extra file.
        actual = set()
        for path in root.rglob('*'):
            require(not path.is_symlink(), 'Symlink in output inventory: ' + str(path))
            if path.is_file() and path != manifest_path:
                actual.add(path.relative_to(root).as_posix())
        extra = actual - set(manifest)
        for relative in sorted(extra):
            require(PurePosixPath(relative).name == 'artifacts.sha256.json',
                    'Output file absent from complete manifest: ' + relative)
            nested = member(root, relative)
            receipt, _ = verify_manifest(nested.parent, nested)
            omitted_nested_manifests.append(receipt)
        require(set(manifest) <= actual, 'Manifest inventory exceeds present output files')
    return {'path': str(manifest_path), 'sha256': sha(manifest_path),
            'bound_files': len(manifest), 'bound_bytes': total_bytes,
            'all_bound_bytes_match': True, 'inventory_checked': complete,
            'separately_verified_omitted_nested_manifests': omitted_nested_manifests}, manifest


def binding_check(source, relative, count):
    path = source / relative
    binding = load(path)
    require(isinstance(binding, dict) and len(binding) == count,
            'Wrong retained binding count: ' + relative)
    mismatches = {}
    for name, expected in binding.items():
        require(isinstance(expected, str) and SHA_RE.fullmatch(expected), 'Invalid retained binding SHA: ' + name)
        p = member(source, name)
        actual = sha(p) if p.is_file() else None
        if actual != expected:
            mismatches[name] = {'retained_sha256': expected, 'supplied_source_sha256': actual}
    return {'manifest': relative, 'manifest_sha256': sha(path), 'count': count,
            'unchanged_count': count - len(mismatches), 'all_unchanged': not mismatches,
            'mismatches': mismatches,
            'scope': 'Retained original execution inputs; comparison does not rerun that suite.'}


def resolve_reference(source, relative, override):
    path = source / relative / 'source-output-retention.json'
    receipt = load(path)
    record = receipt['complete_output']
    original = Path(record['output']).resolve()
    selected = Path(override).resolve() if override else original
    require(selected.is_dir(), 'Retained complete output unavailable: ' + str(selected))
    require(any(record.get(key) is True for key in
                ['complete_output_bytes_and_modes_verified', 'complete_output_bytes_and_original_modes_verified']),
            'Original receipt does not attest complete byte/mode preservation: ' + str(path))
    return selected, {'retention_receipt': str(path), 'receipt_sha256': sha(path),
                      'receipt_original_output': str(original), 'selected_output': str(selected),
                      'archive': record.get('archive'), 'archive_sha256': record.get('archive_sha256'),
                      'archive_reverified_here': False,
                      'scope': 'Frozen original raw directory; selected bytes checked against Git-bound public raw manifest.'}


def verify_commands(output, commands, expected_negative, reference_labels, source=None):
    require(isinstance(commands, list), 'Command journal must be a list')
    rows = {}
    negatives = set()
    for row in commands:
        label = row.get('label')
        require(isinstance(label, str) and re.fullmatch(r'[\w.-]+', label), 'Invalid command label')
        require(label not in rows, 'Duplicate command journal label: ' + label)
        rows[label] = row
        require('error' not in row and isinstance(row.get('returncode'), int), 'Unfinished/failed journal row: ' + label)
        if source is not None:
            require(Path(row['cwd']).resolve() == source, 'Command used a different source: ' + label)
        argv = row.get('argv')
        require(isinstance(argv, list) and argv and all(isinstance(a, str) for a in argv), 'Invalid executed argv: ' + label)
        log = member(output, label + '.log')
        require(log.is_file(), 'Command log missing: ' + label)
        if label in expected_negative:
            negatives.add(label)
            require(row['returncode'] != 0, 'Expected negative unexpectedly returned zero: ' + label)
            text = log.read_text()
            require('PASS ' not in text, 'Expected negative log contains PASS: ' + label)
            if label.startswith('micro-1-'):
                marker = 'native two-block mismatch original=1'
                require(row.get('expected_failure_observed') is True
                        and row.get('expected_failure_marker') == marker and marker in text,
                        'Original-IP expected mismatch absent: ' + label)
            elif label.startswith('native-invalid-'):
                require(row.get('expected_failure') is True
                        and ('scratchpad length must be' in text or 'RegisterFile input must be exactly' in text),
                        'Malformed native diagnostic absent: ' + label)
            else:
                require(row.get('expected_failure') is True
                        and ('error:' in text.lower() or 'error(s)' in text.lower()),
                        'Invalid parameter compile diagnostic absent: ' + label)
        else:
            require(row['returncode'] == 0 and not row.get('expected_failure')
                    and not row.get('expected_failure_marker'), 'Unexpected command failure: ' + label)
    require(negatives == set(expected_negative), 'Missing expected negative command labels')
    require(set(reference_labels) <= set(rows), 'Original command labels absent from fresh journal')
    return rows, {'completed_commands': len(rows), 'expected_negative_labels': sorted(negatives),
                  'all_positive_returncodes_zero': True, 'same_original_command_label_coverage': True}


def pass_record(output, label, row):
    lines = member(output, label + '.log').read_text().splitlines()
    records = [line for line in lines if line.startswith('PASS ')]
    require(len(records) == 1 and records[0] == row.get('record'), 'Actual PASS log/summary mismatch: ' + label)
    require(not any('FATAL:' in line or line.startswith(('FAIL ', 'ERROR:')) for line in lines),
            'Failure text in positive log: ' + label)
    fields = {key: int(value) for key, value in re.findall(r'(\w+)=(\d+)', records[0])}
    for key, value in fields.items():
        require(row.get(key) == value, 'PASS numeric field differs from summary: ' + label + ':' + key)
    return fields


def normalized_argv(row, output):
    roots = [(str(Path(row['cwd']).resolve()), '<SOURCE>'), (str(output), '<OUTPUT>')]
    result = []
    for argument in row['argv']:
        for original, token in sorted(roots, key=lambda item: len(item[0]), reverse=True):
            argument = argument.replace(original, token)
        result.append(argument)
    return result


def mappings(output, summary, reference):
    require(set(summary['mapping']) == set(reference['mapping']) and len(summary['mapping']) == 3,
            'Actual synthesis label set differs')
    result = {}
    for label, row in summary['mapping'].items():
        counts = Counter()
        with member(output, 'netlist-' + label + '.json').open() as stream:
            for line in stream:
                match = re.fullmatch(r'\s*"type": "([^"]+)",\s*', line)
                if match:
                    counts[match[1]] += 1
        stats = re.findall(r'Number of cells:\s*(\d+)', member(output, 'stat-' + label + '.txt').read_text())
        require(stats and all(int(n) == sum(counts.values()) for n in stats), 'Netlist/stat count mismatch: ' + label)
        derived = {'num_cells': sum(counts.values()),
                   'flop_cells': sum(n for kind, n in counts.items() if 'DFF' in kind),
                   'latch_cells': sum(n for kind, n in counts.items() if 'DLATCH' in kind),
                   'num_cells_by_type': dict(sorted(counts.items()))}
        for key, value in derived.items():
            require(row.get(key) == value, 'Fresh mapped cell summary does not match actual netlist: ' + label)
            require(reference['mapping'][label].get(key) == value,
                    'Actual mapped resource counts differ from original: ' + label)
        text = member(output, 'synth-' + label + '.log').read_text()
        require('found and reported 0 problems.' in text.lower() and 'ERROR:' not in text,
                'Actual synthesis check assertion missing/failed: ' + label)
        result[label] = {**derived, 'top': row.get('top'), 'same_as_retained': True}
    return result


def native_equivalence(fresh, retained, fresh_manifest, old_manifest, paths):
    require(paths, 'No native fixture files selected')
    result = {}
    for name in sorted(paths):
        require(name in fresh_manifest and name in old_manifest, 'Native fixture not manifest-bound: ' + name)
        old, new = sha(member(retained, name)), sha(member(fresh, name))
        require(old == old_manifest[name] and new == fresh_manifest[name] and old == new,
                'Native input/expected-byte difference: ' + name)
        result[name] = new
    return {'files': len(result), 'same_native_input_and_expected_bytes': True, 'sha256': result}


def verify_register_digests(output):
    messages = member(output, 'register-inputs.hex').read_text().splitlines()
    rows32 = member(output, 'hash32.hex').read_text().splitlines()
    rows64 = member(output, 'hash64.hex').read_text().splitlines()
    require(len(messages) == len(rows32) == len(rows64) == 524, 'Expected 524 native register frames per digest')
    for raw, line32, line64 in zip(messages, rows32, rows64):
        row32, row64 = line32.split(), line64.split()
        require(len(row32) == len(row64) == 2 and row32[0] == row64[0] == raw, 'Register/digest input packing mismatch')
        message = bytes.fromhex(raw)[::-1]
        d32, d64 = bytes.fromhex(row32[1])[::-1], bytes.fromhex(row64[1])[::-1]
        require(len(message) == 256 and len(d32) == len(d64) == 64, 'Wrong register/digest byte width')
        require(d64 == hashlib.blake2b(message, digest_size=64).digest(), 'Native 64-byte digest mismatch')
        require(d32[:32] == hashlib.blake2b(message, digest_size=32).digest() and d32[32:] == bytes(32)
                and d32[:32] != d64[:32], 'Native 32-byte parameterization/truncation mismatch')
    return {'messages_per_digest': 524, 'input_bytes': 256, 'independent_hashlib_crosscheck': True,
            'digest32_differs_from_digest64_truncation_all_524': True}


def verify_finalizer_native(output, corpus):
    cases = corpus['cases']
    require(len(cases) == 14 and len({c['name'] for c in cases}) == 14, 'Expected 14 unique native finalizer cases')
    native_rows = load(output / 'fixtures/native-commands.json')
    require(len(native_rows) == 14 and {r['case'] for r in native_rows} == {c['name'] for c in cases}
            and all(r.get('returncode') == 0 and 'error' not in r for r in native_rows), 'Incomplete native fixture executions')
    result = []
    for case in cases:
        directory = member(output, 'fixtures/' + case['name'])
        require(Path(case['directory']).resolve() == directory, 'Case directory differs from actual output')
        rf = (directory / 'register-file.bin').read_bytes()
        require(len(rf) == 256 and sha(directory / 'register-file.bin') == case['input_register_sha256'], 'Raw register hash/size mismatch')
        require((directory / 'scratchpad.bin').stat().st_size == case['scratchpad_bytes']
                and sha(directory / 'scratchpad.bin') == case['input_scratchpad_sha256'], 'Raw scratchpad hash/size mismatch')
        decoded = {}
        for name, width in [('rf-in', 256), ('aes-hash', 64), ('rf-final', 256), ('digest32', 32), ('digest64', 64)]:
            rows = (directory / (name + '.hex')).read_text().splitlines()
            require(len(rows) == 1, 'Native single-record file wrong shape: ' + case['name'] + '/' + name)
            decoded[name] = bytes.fromhex(rows[0])[::-1]
            require(len(decoded[name]) == width, 'Native record byte width wrong: ' + name)
        require(decoded['rf-in'] == rf and decoded['rf-final'] == rf[:192] + decoded['aes-hash'],
                'Native finalization did not replace only A bank')
        require(decoded['digest32'] == hashlib.blake2b(decoded['rf-final'], digest_size=32).digest()
                and decoded['digest64'] == hashlib.blake2b(decoded['rf-final'], digest_size=64).digest()
                and decoded['digest32'] != decoded['digest64'][:32], 'Native finalization digest parameter mismatch')
        expected = ('PASS native-finalization scratchpad_bytes=' + str(case['scratchpad_bytes']) +
                    ' groups=' + str(case['scratchpad_bytes'] // 64) +
                    ' register_bytes=256 digest32=32 digest64=64 RFE_preserved=1')
        require((directory / 'native-oracle.log').read_text().splitlines() == [expected], 'Actual native oracle PASS missing')
        result.append({'case': case['name'], 'scratchpad_bytes': case['scratchpad_bytes'],
                       'input_scratchpad_sha256': case['input_scratchpad_sha256'],
                       'input_register_sha256': case['input_register_sha256'],
                       'aes_hash_sha256': sha(directory / 'aes-hash.hex'),
                       'digest32_sha256': sha(directory / 'digest32.hex'),
                       'digest64_sha256': sha(directory / 'digest64.hex')})
    return result


def compare_suite(source, fresh, relative, override, finalizer):
    public = source / relative / 'server'
    old_summary = load(public / 'summary.json')
    retained, retention = resolve_reference(source, relative, override)
    require(fresh.is_dir() and fresh != retained and not fresh.is_relative_to(source), 'Fresh output is not a distinct external directory')
    require(not (fresh / 'failure.json').exists(), 'Fresh output contains failure.json')
    old_receipt, old_manifest = verify_manifest(retained, public / 'artifacts.sha256.json')
    fresh_receipt, fresh_manifest = verify_manifest(fresh, fresh / 'artifacts.sha256.json', complete=True)
    summary = load(fresh / 'summary.json')
    require(load(retained / 'summary.json') == old_summary, 'Public raw summary differs from preserved original')
    counts = (41, 19) if finalizer else (18, 17)
    require(summary.get('synthesis_requested') is True and summary.get('source_unchanged_after_run') is True,
            'Fresh full mapped/source-guard completion absent')
    if finalizer:
        require(summary.get('status') == 'pass' and summary.get('fixture_inputs_unchanged_after_run') is True
                and summary.get('invalid_parameter_cases') == 4 and summary.get('native_invalid_input_cases') == 6,
                'Finalizer terminal pass/fixture/negative counts absent')
    fresh_inputs, _ = verify_manifest(source, fresh / 'inputs.json')
    expected_negative = ({'native-invalid-' + str(i) for i in range(6)} |
                         {'invalid-parameter-' + str(i) for i in [0, 63, 65, 2097216]}) if finalizer else {'micro-1-32', 'micro-1-64'}
    old_commands = load(public / 'commands.json')
    require(load(retained / 'commands.json') == old_commands, 'Public journal differs from preserved raw original')
    fresh_commands = load(fresh / 'commands.json')
    command_rows, journal = verify_commands(fresh, fresh_commands, expected_negative,
                                            [r['label'] for r in old_commands], source)
    verify_commands(retained, old_commands, expected_negative, [r['label'] for r in old_commands])
    old_rows = {row['label']: row for row in old_commands}
    scientific_labels = set(summary.get('rtl', {})) | set(summary.get('mapped', {})) | expected_negative
    scientific_labels.update('synth-' + label for label in summary.get('mapping', {}))
    scientific_labels.update({'compile-native-oracle'} if finalizer else
                             {'hash-oracle', 'compile-hash-oracle', 'oracle-0', 'oracle-1', 'compile-program-oracle'})
    for label in scientific_labels:
        require(label in command_rows and label in old_rows, 'Scientific executed command missing: ' + label)
        require(normalized_argv(command_rows[label], fresh) == normalized_argv(old_rows[label], retained),
                'Executed scientific arguments differ after source/output path normalization: ' + label)
    journal['scientific_command_arguments_equal_after_path_normalization'] = sorted(scientific_labels)
    records = {}
    for family, count in [('rtl', counts[0]), ('mapped', counts[1])]:
        require(len(summary.get(family, {})) == count and summary.get(family + '_modes') == count
                and set(summary[family]) == set(old_summary[family]), 'Fresh PASS label/count mismatch: ' + family)
        for label, row in summary[family].items():
            pass_record(fresh, label, row)
            pass_record(retained, label, old_summary[family][label])
            require(row == old_summary[family][label], 'Fresh PASS record differs from retained: ' + label)
            if family == 'mapped':
                counterpart = 'rtl-seed' if label == 'mapped-hash-seed' else label.replace('mapped-', 'rtl-', 1)
                require(row == summary['rtl'][counterpart], 'Mapped result differs from fresh RTL: ' + label)
            records[label] = row
    mapped_counts = mappings(fresh, summary, old_summary)
    tools = load(fresh / 'tools.json')
    old_tools = load(retained / 'tools.json')
    tool_comparison = {name: {'fresh_sha256': row.get('sha256'), 'retained_sha256': old_tools.get(name, {}).get('sha256'),
                              'same_executable': row.get('sha256') == old_tools.get(name, {}).get('sha256')}
                       for name, row in tools.items()}
    result = {'scope': 'FRESH combined-tree component execution compared with RETAINED original component proof',
              'fresh_output': str(fresh), 'retained_output': retention,
              'retained_raw_manifest': old_receipt, 'fresh_complete_manifest': fresh_receipt,
              'fresh_source_bindings': fresh_inputs, 'command_completion': journal,
              'rtl_modes': counts[0], 'mapped_modes': counts[1], 'actual_synthesis_count': 3,
              'actual_logged_PASS_records': records, 'actual_mapping': mapped_counts,
              'tool_executable_comparison': tool_comparison,
              'all_fresh_and_retained_logged_records_equal': True}
    if finalizer:
        corpus = load(fresh / 'corpus.json')
        old_corpus = load(public / 'corpus.json')
        require(load(retained / 'corpus.json') == old_corpus, 'Public corpus differs from raw retained corpus')
        require(corpus['pinned_randomx'] == old_corpus['pinned_randomx']
                and corpus.get('source_and_accepted_inputs_unchanged_after_generation') is True, 'Native source/provenance guard absent')
        stable = lambda c: {k: v for k, v in c.items() if k != 'directory'}
        require([stable(c) for c in corpus['cases']] == [stable(c) for c in old_corpus['cases']], 'Native corpus metadata changed')
        require(corpus['abba_full_profiles'] == old_corpus['abba_full_profiles']
                and summary['full_profile_order'] == old_summary['full_profile_order'], 'Four-trial ABBA profile/order changed')
        full_labels = ['rtl-full-' + str(index) + '-' + profile['mode']
                       for index, profile in enumerate(summary['full_profile_order'])]
        require([row['label'] for row in fresh_commands if row['label'].startswith('rtl-full-')] == full_labels,
                'Actual command journal does not follow the four-trial ABBA order')
        old_native_rows = load(retained / 'fixtures/native-commands.json')
        new_native_rows = load(fresh / 'fixtures/native-commands.json')
        require([row['case'] for row in new_native_rows] == [row['case'] for row in old_native_rows],
                'Native case execution order differs')
        for new, old in zip(new_native_rows, old_native_rows):
            require(Path(new['cwd']).resolve() == source
                    and normalized_argv(new, fresh) == normalized_argv(old, retained),
                    'Actual native finalization fixture arguments differ: ' + new['case'])
        provenance_keys = ['artifact_manifest_sha256', 'memory_artifact_sha256', 'memory_hex_sha256',
                           'memory_binary_sha256', 'registers_artifact_sha256', 'selected_register_binary_sha256',
                           'program_index', 'round_mode', 'no_program_chain_rerun']
        require(all(corpus['accepted_full_provenance'].get(k) == old_corpus['accepted_full_provenance'].get(k)
                    for k in provenance_keys), 'Accepted full final7/RF provenance digests changed')
        cases = [c['name'] for c in corpus['cases']]
        paths = {'fixtures/' + case + '/' + name for case in cases for name in
                 ['scratchpad.bin', 'register-file.bin', 'scratchpad.hex', 'rf-in.hex', 'aes-hash.hex',
                  'rf-final.hex', 'digest32.hex', 'digest64.hex', 'native-inputs.json']}
        result['native_equivalence'] = native_equivalence(fresh, retained, fresh_manifest, old_manifest, paths)
        result['native_cases'] = verify_finalizer_native(fresh, corpus)
        result['full_ABBA_trials'] = []
        require(len(summary['full_profile_order']) == 4, 'Expected four full ABBA trials')
        for index, profile in enumerate(summary['full_profile_order']):
            label = 'rtl-full-' + str(index) + '-' + profile['mode']
            row = summary['rtl'][label]
            latency = 393284 if profile['mode'] == 'ideal' else 1048649
            require(row['bytes'] == 2097152 and row['primary_reads'] == 131072
                    and row['restart_only'] == 0 and row['native_success'] == 1
                    and row['primary_response_latency'] == latency, 'Full native RTL trial bound mismatch: ' + label)
            result['full_ABBA_trials'].append({'label': label, **profile,
                                              'elapsed_cycles': row['elapsed_cycles'], 'primary_response_latency': latency,
                                              'reads128': 131072, 'same_as_retained': True})
        require(all(r['restart_only'] == 1 and r['native_success'] == 0 and r['restart_reads'] == 1
                    for k, r in summary['mapped'].items() if k.startswith('mapped-default-')),
                'Default mapped gates are not accurately bounded restart-only checks')
        result['mapped_scope'] = 'Six bounded256 native profiles + nine bounded controls + four default2MiB restart-only checks; no full2MiB mapped hash completion.'
        result['expected_failures'] = {'malformed_native': 6, 'invalid_hardware_parameters': 4}
        result['full_chain_rerun'] = False
    else:
        require(summary.get('programs') == 8 and summary.get('connected_iterations_per_program') == 4
                and summary.get('new_stage_clock_cost_each_profile') == 414,
                'Hardware seed short-chain/preparation clock boundary changed')
        require(set(summary.get('negative', {})) == expected_negative
                and all(r.get('expected_failure_observed') is True for r in summary['negative'].values()),
                'Original-IP expected failure summary incomplete')
        paths = {'register-inputs.hex', 'hash32.hex', 'hash64.hex', 'micro-vectors.hex',
                 'hash-corpus.json', 'independent-vector-crosscheck.json'}
        paths.update(name for name in old_manifest if name.startswith(('v1/', 'v2/'))
                     and PurePosixPath(name).suffix in ('.hex', '.mem', '.vh'))
        result['native_equivalence'] = native_equivalence(fresh, retained, fresh_manifest, old_manifest, paths)
        result['native_register_digests'] = verify_register_digests(fresh)
        result['profile_clocks'] = []
        for v2, stall, clocks in [(1, 0, 111348), (1, 1, 185810), (0, 0, 70524), (0, 1, 121278)]:
            label = 'rtl-connected-' + str(v2) + '-' + str(stall)
            row = summary['rtl'][label]
            require(row['elapsed_cycles'] == clocks and row['total_iterations'] == 32
                    and row['hardware_seed_hashes'] == 7 and row['full_memory_bytes'] == 2097152,
                    'Connected native seed clock/count mismatch: ' + label)
            result['profile_clocks'].append({'label': label, 'v2': v2, 'stall': stall,
                                             'elapsed_cycles': clocks, 'hardware_seed_hashes': 7,
                                             'seed_stage_clock_increment': 414, 'same_as_retained': True})
        result['expected_failures'] = {'original_IP_two_block_native_mismatch': 2}
        result['connected_scope'] = 'Eight programs x4 iterations per v1/v2 profile with addressed fixture dataset; ordinary backend default PREPARED_RCP=0, not connected prepared-mode full hash.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Exact frozen combined source used by both fresh jobs')
    parser.add_argument('--regfile-output', type=Path, required=True)
    parser.add_argument('--finalizer-output', type=Path, required=True)
    parser.add_argument('--regfile-reference', type=Path, help='Optional moved raw original, still checked against preserved public raw SHA manifest')
    parser.add_argument('--finalizer-reference', type=Path, help='Optional moved raw original, still checked against preserved public raw SHA manifest')
    parser.add_argument('--report', type=Path, required=True, help='NEW external JSON path; existing report is never overwritten')
    args = parser.parse_args()
    source = args.source.resolve()
    regfile, finalizer = args.regfile_output.resolve(), args.finalizer_output.resolve()
    target = args.report.resolve()
    require(source.is_dir() and target.parent.is_dir(), 'Source/report parent missing')
    protected = [source, regfile, finalizer]
    for relative, override in [(REGFILE, args.regfile_reference), (FINALIZER, args.finalizer_reference)]:
        retained, _ = resolve_reference(source, relative, override)
        protected.append(retained)
    require(not target.exists() and not any(target.is_relative_to(p) for p in protected),
            'Report must be new and outside every source/fresh/retained tree')
    require(regfile != finalizer and not regfile.is_relative_to(finalizer) and not finalizer.is_relative_to(regfile),
            'Fresh component output directories overlap')
    report = {'schema': 'openrx-combined-evidence-comparison-v1',
              'created_utc': datetime.now(timezone.utc).isoformat(), 'source': str(source),
              'comparison_helper_sha256': sha(Path(__file__).resolve()), 'status': 'comparison_pending',
              'independent_review_or_acceptance': False,
              'boundaries': ['Fresh seed/hash and scratchpad-finalizer component regressions are separate runs.',
                             'Original prepared reciprocal and program-sequence runs are retained proof, not fresh execution.',
                             'No full8x2048 rerun or complete prepared-mode hardware hash was measured here.',
                             'Generic cells and fixture clocks establish no MHz, hash/s, watts, joules/hash or whole-system1MH/s/2500W result.']}
    exit_code = 1
    try:
        report['retained_source_bindings'] = {'prepared_219': binding_check(source, PREPARED, 219),
                                               'program_sequence_73': binding_check(source, SEQUENCE, 73)}
        report['regfile'] = compare_suite(source, regfile, REGFILE, args.regfile_reference, False)
        report['finalizer'] = compare_suite(source, finalizer, FINALIZER, args.finalizer_reference, True)
        # Repeat the guards after all manifest/log/corpus comparisons, so a source
        # edit during postprocessing cannot silently enter an unchanged report.
        for output in [regfile, finalizer]:
            verify_manifest(source, output / 'inputs.json')
        final_bindings = {'prepared_219': binding_check(source, PREPARED, 219),
                          'program_sequence_73': binding_check(source, SEQUENCE, 73)}
        require(final_bindings == report['retained_source_bindings'], 'Retained source bindings changed during comparison')
        require(all(r['all_unchanged'] for r in report['retained_source_bindings'].values()),
                'Retained219/73 inputs changed; reuse requires separately declared revalidation, not an unchanged label')
        report['status'] = 'pass_evidence_comparison'
        report['outcome'] = 'Actual fresh component records/native bytes/mapped counts agree with preserved originals; original219/73 input bindings remain exact.'
        exit_code = 0
    except (ComparisonFailure, KeyError, ValueError, OSError, TypeError) as error:
        report['status'] = 'failed_evidence_comparison'
        report['error'] = str(error)
    # Exclusive creation prevents modifying any earlier successful or failed report.
    with target.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'status': report['status'], 'report': str(target), 'report_sha256': sha(target)}))
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ComparisonFailure, OSError, ValueError) as error:
        print('Comparison could not create a new safe report: ' + str(error), file=sys.stderr)
        sys.exit(2)
