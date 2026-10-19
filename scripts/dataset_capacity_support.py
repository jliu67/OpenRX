#!/usr/bin/env python3
"""Reference/selected-fixture identity checks for the dataset capacity extension.

No work is launched on import. The accepted supervisor and seven-file cache
verification are reused unchanged. Optional private journals are caller inputs;
no private execution identity or digest is a committed trust constant here.
"""
from pathlib import Path
import re

from dataset_lifecycle_support import Supervisor, load, save, sha, verify_assets

REFERENCE_LOCK = 'rtl/dataset_capacity/reference-2x1.lock.json'
FIXTURE_INDEX = 'docs/validation/dataset-item-20261018/correctness01/correctness-fixtures-index.json'
NATIVE_PIN = 'aaafe71322df6602c21a5c72937ac284724ae561'
REFERENCE_NAMES = frozenset('accesses.hex dataset-items.hex events.mem final-0.hex final-1.hex '
    'final-a.hex final-digest32.hex final-rf.hex full-reference.json initial.hex iterations.hex '
    'iterations.mem metadata.hex metadata.mem oracle-summary.json program-0.mem program-1.mem '
    'program-registers.hex sequence_sizes.vh'.split())
REFERENCE_SOURCES = frozenset(['rtl/hash/tests/dataset_lifecycle_reference.cpp',
    'rtl/hash/tests/dataset_lifecycle_native.hpp', 'rtl/hash/tests/lifecycle_reference.cpp',
    'rtl/hash/tests/lifecycle_native.hpp', 'rtl/execute/tests/program_native_helpers.hpp',
    'vendor/randomx.lock.json', 'vendor/randomx.sha256.json'])


def _root(value):
    path = Path(value).absolute()
    assert all(not p.is_symlink() for p in [path, *path.parents]), str(path)
    assert path.is_dir(), str(path)
    return path.resolve(strict=True)


def _under(root, relative):
    path = Path(relative)
    assert not path.is_absolute() and path.parts and '..' not in path.parts, str(relative)
    result = root
    for i, part in enumerate(path.parts):
        assert part not in ('.', ''), str(relative)
        result = result / part
        assert not result.is_symlink(), str(result)
        assert result.is_file() if i == len(path.parts)-1 else result.is_dir(), str(result)
    return result


def _file(value):
    path = Path(value).absolute()
    return _under(_root(path.parent), path.name)


def _identity(path):
    return {'bytes': path.stat().st_size, 'sha256': sha(path)}


def _hex(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def _reference_metadata(gold, lock):
    profile = lock['profile']
    assert profile['programs'] == 2 and profile['iterations_per_program'] == 1 and profile['v2'] == 1
    assert profile['cache_key'] == 'test key 000' and profile['input_bytes'] == 52
    assert len(bytes.fromhex(profile['input_hex'])) == profile['input_bytes']
    assert profile['canonical_randomx_calculate_hash_verified'] is False
    assert _hex(profile['final_digest_hex'])
    oracle = load(_under(gold, 'oracle-summary.json'))
    assert oracle == profile['oracle'], 'native reference counts/metadata'
    assert oracle['programs'] == 2 and oracle['iterations_per_program'] == 1
    assert oracle['total_iterations'] == 2 and oracle['v2'] == 1 and oracle['instruction_steps'] == 768
    full = load(_under(gold, 'full-reference.json'))
    assert full['canonical_randomx_calculate_hash_verified'] is False
    assert full['bounded_iteration_profile'] is True and full['cache_key'] == profile['cache_key']
    assert full['input_hex'] == profile['input_hex']
    assert _under(gold, 'final-digest32.hex').read_text().strip() == profile['final_digest_hex']
    return oracle


def _source_identities(source, lock):
    expected = lock['public_source']['reference_sources']
    assert set(expected) == REFERENCE_SOURCES
    result = {}
    for relative, identity in expected.items():
        result[relative] = _identity(_under(source, relative))
        assert result[relative] == identity, 'accepted reference source identity: ' + relative
    native_lock = load(_under(source, 'vendor/randomx.lock.json'))
    assert native_lock['commit'] == NATIVE_PIN
    native = load(_under(source, 'vendor/randomx.sha256.json'))
    assert len(native) == 171
    for relative, digest in native.items():
        name = 'vendor/randomx/' + relative
        result[name] = _identity(_under(source, name))
        assert result[name]['sha256'] == digest, 'native pinned source identity: ' + name
    return result


def verify_reference(reuse_root, lock_path, source_root, *, execution_root=None,
                     receipt_sha=None, manifest_sha=None, verify_path=None, verify_sha=None):
    """Verify 19 deterministic gold files; optionally bind actual private records.

    Lock-only CI verifies file/source identity. Raw mode additionally checks the
    supplied journal digests, actual original artifacts and actual manifest source
    rows; it preserves the original runner's separate scientific classification.
    """
    gold, source = _root(reuse_root), _root(source_root)
    committed = _under(source, REFERENCE_LOCK)
    assert _file(lock_path) == committed, 'current source reference lock is required'
    lock_identity = _identity(committed)
    lock = load(committed)
    assert lock['schema'] == 'openrx.dataset-capacity.reference-lock.v1'
    assert lock['native_pin'] == NATIVE_PIN
    assert lock['excluded_nondeterministic_files'] == ['dataset-native-host-time.json']
    assert set(lock['files']) == REFERENCE_NAMES
    assert re.fullmatch('[0-9a-f]{40}', lock['public_source']['head'])
    assert re.fullmatch('[0-9a-f]{40}', lock['public_source']['tree'])
    actual = {}
    for relative, expected in lock['files'].items():
        actual[relative] = _identity(_under(gold, relative))
        assert actual[relative] == expected, 'reference identity: ' + relative
    oracle = _reference_metadata(gold, lock)
    sources = _source_identities(source, lock)
    result = {'schema': 'openrx.dataset-capacity.reference-provenance.v1',
        'gold_path': str(gold), 'files': actual, 'selected_reference_files_verified': len(actual),
        'selected_reference_bytes': sum(row['bytes'] for row in actual.values()),
        'lock': {'path': str(committed), **lock_identity},
        'identity_verified_by_trusted_lock': True, 'raw_journal_verified': False,
        'verification_mode': 'trusted_committed_lock_only',
        'public_source': lock['public_source'], 'hosted_origin': lock['hosted_origin'],
        'actual_current_source_files_verified': len(sources), 'native_reference': oracle,
        'canonical_randomx_calculate_hash_verified': False, 'native_reference_regenerated': False,
        'archive_bytes_rehashed': False,
        'boundary': 'Actual selected gold and source identities. Hosted archive identity is API advertised; raw private journal integrity is a separate optional check.'}
    supplied = [execution_root is not None, receipt_sha is not None, manifest_sha is not None,
                verify_path is not None, verify_sha is not None]
    assert not any(supplied) or all(supplied), 'all five private journal bindings are required together'
    if any(supplied):
        assert all(_hex(x) for x in (receipt_sha, manifest_sha, verify_sha))
        execution = _root(execution_root)
        receipt_path = _under(execution, 'receipt.json')
        manifest_path = _under(execution, 'manifest.json')
        checked_path = _file(verify_path)
        assert sha(receipt_path) == receipt_sha and sha(manifest_path) == manifest_sha
        assert sha(checked_path) == verify_sha
        journal, manifest, checked = load(receipt_path), load(manifest_path), load(checked_path)
        assert journal['execution_id'] == manifest['execution_id'] == checked['execution_id']
        assert journal['status'] == checked['status'] == 'PROCESS_EXITED'
        assert journal['process']['returncode'] == 0 and checked['integrity_verified'] is True
        rows = {Path(row['path']): row for row in journal['artifacts']}
        assert len(rows) == len(journal['artifacts']), 'unique actual receipt artifact paths'

        def bound(path):
            identity = _identity(path)
            row = rows[path]
            assert identity == {'bytes': row['bytes'], 'sha256': row['sha256']}, str(path)
            return identity

        bound(manifest_path)
        summary_path = _under(execution, 'output/summary.json'); bound(summary_path)
        summary = load(summary_path)
        assert summary['status'] == 'pass_bounded_dataset_lifecycle_integration'
        assert summary['programs'] == 2 and summary['iterations'] == 1
        assert summary['source_tree'] == lock['public_source']['tree']
        assert re.fullmatch('[0-9a-f]{40}', summary['source_head'])
        inventory_path = _under(execution, 'output/native-reference-files.json'); bound(inventory_path)
        inventory = load(inventory_path)
        assert set(inventory) == REFERENCE_NAMES | {'dataset-native-host-time.json'}
        originals = {}
        for relative, expected in actual.items():
            path = _under(execution, 'output/native-reference/' + relative)
            assert bound(path) == expected == inventory[relative], relative
            originals[relative] = {'path': str(path), **expected}
        source_rows = [row for entry in manifest['sources'] for row in entry['files']]
        for relative, expected in sources.items():
            matches = [row for row in source_rows if row['relative'] == relative]
            assert len(matches) == 1, 'unique actual consumed source: ' + relative
            row = matches[0]
            assert expected == {'bytes': row['bytes'], 'sha256': row['sha256']}, relative
        result.update({'raw_journal_verified': True,
            'verification_mode': 'trusted_lock_and_supplied_private_journal',
            'execution_id': journal['execution_id'], 'executed_source_head': summary['source_head'],
            'executed_source_tree': summary['source_tree'],
            'actual_prior_reference_artifact_rows_verified': len(originals),
            'actual_prior_manifest_source_rows_verified': len(sources), 'raw_reference_origins': originals,
            'receipt': {'path': str(receipt_path), **_identity(receipt_path)},
            'manifest': {'path': str(manifest_path), **_identity(manifest_path)},
            'root_verify': {'path': str(checked_path), **_identity(checked_path)},
            'original_runner_scientific_acceptance': journal.get('scientific_acceptance', 'unavailable')})
    assert _identity(committed) == lock_identity, 'reference lock changed during verification'
    for relative, identity in actual.items():
        assert _identity(_under(gold, relative)) == identity, 'reference changed during verification: ' + relative
    return result


def verify_selected_assets(asset_root, selected_names, source_root):
    """Verify only named actual files against the existing public PR80 index."""
    assets, source = _root(asset_root), _root(source_root)
    index_path = _under(source, FIXTURE_INDEX)
    index_identity = _identity(index_path)
    index = load(index_path)
    assert index['schema'] == 'openrx.dataset-item.fixture-export.v1'
    assert index['counts'] == {'excluded_retained_cache_images': 2, 'original': 898, 'selected': 896}
    rows = {row['fixture_path']: row for row in index['entries']}
    assert len(rows) == len(index['entries']) == 898
    names = list(selected_names)
    assert names and len(names) == len(set(names)), 'nonempty unique selected fixture names'
    actual = {}
    for relative in names:
        row = rows[relative]
        assert row['receipt_bound'] is True
        expected = {'bytes': row['original_bytes'], 'sha256': row['original_sha256']}
        actual[relative] = _identity(_under(assets, relative))
        assert actual[relative] == expected, 'selected prepared fixture identity: ' + relative
    assert _identity(index_path) == index_identity, 'public fixture index changed during verification'
    for relative, identity in actual.items():
        assert _identity(_under(assets, relative)) == identity, 'selected fixture changed during verification: ' + relative
    return {'schema': 'openrx.dataset-capacity.selected-fixtures.v1',
        'asset_root': str(assets), 'files': actual, 'selected_fixture_files_verified': len(actual),
        'selected_fixture_bytes': sum(row['bytes'] for row in actual.values()),
        'index': {'path': str(index_path), **index_identity},
        'identity_verified_by_trusted_public_index': True, 'raw_journal_verified': False,
        'archive_bytes_rehashed': False,
        'boundary': 'Only selected actual file identities from the committed public index; no whole archive or private journal integrity claim.'}
