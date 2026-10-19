"""Tiny synthetic provenance mutations; no native program/cache work or HDL tools.

The shapes exercise the production trust boundaries. Tiny placeholder gold and
171 placeholder native files are intentionally not runnable RandomX fixtures.
"""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dataset_capacity_support import (FIXTURE_INDEX, NATIVE_PIN, REFERENCE_LOCK,
    REFERENCE_NAMES, REFERENCE_SOURCES, load, save, sha, verify_reference, verify_selected_assets)


class ReferenceReuseIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dataset-capacity-identity-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source, self.gold = self.base / 'source', self.base / 'gold'
        self.execution = self.base / 'original-execution'
        self.original = self.execution / 'output/native-reference'
        for p in (self.source, self.gold, self.original): p.mkdir(parents=True)
        self.lock_path = self.source / REFERENCE_LOCK
        self.lock_path.parent.mkdir(parents=True)
        self.oracle = {'programs': 2, 'iterations_per_program': 1, 'total_iterations': 2,
                       'v2': 1, 'instruction_steps': 768, 'bytecode_events': 165}
        self.full = {'canonical_randomx_calculate_hash_verified': False,
                     'bounded_iteration_profile': True, 'cache_key': 'test key 000',
                     'input_hex': '42' * 52}
        self.digest = 'f' * 64
        for name in REFERENCE_NAMES:
            (self.gold / name).write_text('synthetic deterministic ' + name + '\n')
        save(self.gold / 'oracle-summary.json', self.oracle)
        save(self.gold / 'full-reference.json', self.full)
        (self.gold / 'final-digest32.hex').write_text(self.digest + '\n')
        self.files = {name: self.identity(self.gold / name) for name in sorted(REFERENCE_NAMES)}
        for name in self.files: shutil.copyfile(self.gold / name, self.original / name)
        native = {}
        for n in range(171):
            relative = f'src/synthetic-{n:03d}.txt'
            path = self.source / 'vendor/randomx' / relative
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(f'native placeholder {n}\n')
            native[relative] = sha(path)
        for name in REFERENCE_SOURCES:
            path = self.source / name; path.parent.mkdir(parents=True, exist_ok=True)
            if name == 'vendor/randomx.lock.json': save(path, {'commit': NATIVE_PIN})
            elif name == 'vendor/randomx.sha256.json': save(path, native)
            else: path.write_text('synthetic accepted reference body\n')
        public_sources = {name: self.identity(self.source / name) for name in REFERENCE_SOURCES}
        self.source_files = dict(public_sources)
        self.source_files.update({'vendor/randomx/' + name: self.identity(self.source / 'vendor/randomx' / name)
                                  for name in native})
        self.lock = {'schema': 'openrx.dataset-capacity.reference-lock.v1', 'native_pin': NATIVE_PIN,
            'profile': {'programs': 2, 'iterations_per_program': 1, 'v2': 1, 'cache_key': 'test key 000',
                'input_hex': self.full['input_hex'], 'input_bytes': 52,
                'canonical_randomx_calculate_hash_verified': False, 'final_digest_hex': self.digest,
                'oracle': self.oracle},
            'public_source': {'head': '1'*40, 'tree': '2'*40, 'reference_sources': public_sources},
            'hosted_origin': {'archive_bytes_rehashed': False, 'digest_kind': 'synthetic API advertised'},
            'files': copy.deepcopy(self.files), 'excluded_nondeterministic_files': ['dataset-native-host-time.json']}
        save(self.lock_path, self.lock)
        self.manifest = {'execution_id': 'synthetic-original', 'sources': [{'files': [
            {'relative': name, **row} for name, row in sorted(self.source_files.items())]}]}
        self.summary = {'status': 'pass_bounded_dataset_lifecycle_integration', 'programs': 2,
                        'iterations': 1, 'source_head': '3'*40, 'source_tree': '2'*40}
        self.verify_path = self.base / 'verify.json'
        save(self.verify_path, {'execution_id': 'synthetic-original', 'status': 'PROCESS_EXITED',
                                'integrity_verified': True, 'scientific_acceptance': 'unverified'})
        self.rebind_journal()
        self.assets = self.base / 'assets'; self.assets.mkdir()
        fixture = self.assets / 'cases-empty.hex'; fixture.write_text('tiny selected fixture\n')
        self.index_path = self.source / FIXTURE_INDEX
        self.index_path.parent.mkdir(parents=True)
        self.index = {'schema': 'openrx.dataset-item.fixture-export.v1',
            'counts': {'excluded_retained_cache_images': 2, 'original': 898, 'selected': 896},
            'entries': [{'fixture_path': 'cases-empty.hex' if n == 0 else f'unselected-{n:03d}',
                         'original_bytes': fixture.stat().st_size, 'original_sha256': sha(fixture),
                         'receipt_bound': True} for n in range(898)]}
        save(self.index_path, self.index)

    @staticmethod
    def identity(path):
        return {'bytes': path.stat().st_size, 'sha256': sha(path)}

    def rebind_journal(self):
        manifest_path = self.execution / 'manifest.json'; save(manifest_path, self.manifest)
        summary_path = self.execution / 'output/summary.json'; save(summary_path, self.summary)
        inventory_path = self.execution / 'output/native-reference-files.json'
        save(inventory_path, {**self.files, 'dataset-native-host-time.json': {'bytes': 1, 'sha256': '0'*64}})
        paths = [manifest_path, summary_path, inventory_path, *[self.original / n for n in self.files]]
        self.receipt_path = self.execution / 'receipt.json'
        save(self.receipt_path, {'execution_id': 'synthetic-original', 'status': 'PROCESS_EXITED',
            'process': {'returncode': 0}, 'scientific_acceptance': 'unverified',
            'artifacts': [{'path': str(path), **self.identity(path)} for path in paths]})

    def private_args(self):
        return {'execution_root': self.execution, 'receipt_sha': sha(self.receipt_path),
                'manifest_sha': sha(self.execution / 'manifest.json'),
                'verify_path': self.verify_path, 'verify_sha': sha(self.verify_path)}

    def check(self, raw=False, **kwargs):
        options = self.private_args() if raw else {}
        options.update(kwargs)
        return verify_reference(self.gold, self.lock_path, self.source, **options)

    def test_lock_only_verifies_19_actual_files_and_no_raw_claim(self):
        result = self.check()
        self.assertEqual(result['selected_reference_files_verified'], 19)
        self.assertEqual(result['actual_current_source_files_verified'], 178)
        self.assertFalse(result['raw_journal_verified'])
        self.assertFalse(result['canonical_randomx_calculate_hash_verified'])
        self.assertEqual(result['files'], self.files)

    def test_actual_private_records_and_source_rows(self):
        result = self.check(raw=True)
        self.assertTrue(result['raw_journal_verified'])
        self.assertEqual(result['actual_prior_reference_artifact_rows_verified'], 19)
        self.assertEqual(result['actual_prior_manifest_source_rows_verified'], 178)
        self.assertEqual(result['executed_source_head'], '3'*40)
        self.assertEqual(result['original_runner_scientific_acceptance'], 'unverified')

    def test_mutated_gold_bytes_reject_stale_claim(self):
        path = self.gold / 'events.mem'; path.write_text(path.read_text().upper())
        with self.assertRaises(AssertionError): self.check()

    def test_stale_lock_byte_count_is_rejected(self):
        self.lock['files']['events.mem']['bytes'] += 1; save(self.lock_path, self.lock)
        with self.assertRaises(AssertionError): self.check()

    def test_mutated_counts_reject_stale_hash(self):
        row = load(self.gold / 'oracle-summary.json'); row['instruction_steps'] += 1
        save(self.gold / 'oracle-summary.json', row)
        with self.assertRaises(AssertionError): self.check()

    def test_coherently_rebound_bad_profile_count_is_rejected(self):
        self.lock['profile']['oracle']['total_iterations'] = 3
        save(self.gold / 'oracle-summary.json', self.lock['profile']['oracle'])
        self.lock['files']['oracle-summary.json'] = self.identity(self.gold / 'oracle-summary.json')
        save(self.lock_path, self.lock)
        with self.assertRaises(AssertionError): self.check()

    def test_coherently_rebound_canonical_claim_is_rejected(self):
        row = load(self.gold / 'full-reference.json'); row['canonical_randomx_calculate_hash_verified'] = True
        save(self.gold / 'full-reference.json', row)
        self.lock['files']['full-reference.json'] = self.identity(self.gold / 'full-reference.json')
        save(self.lock_path, self.lock)
        with self.assertRaises(AssertionError): self.check()

    def test_gold_leaf_symlink_is_rejected(self):
        path = self.gold / 'events.mem'; path.unlink(); path.symlink_to(self.original / path.name)
        with self.assertRaises(AssertionError): self.check()

    def test_gold_root_symlink_is_rejected(self):
        alias = self.base / 'gold-alias'; alias.symlink_to(self.gold, target_is_directory=True)
        with self.assertRaises(AssertionError): verify_reference(alias, self.lock_path, self.source)

    def test_replacement_lock_outside_current_source_is_rejected(self):
        other = self.base / 'replacement-lock.json'; shutil.copyfile(self.lock_path, other)
        with self.assertRaises(AssertionError): verify_reference(self.gold, other, self.source)

    def test_symlink_current_lock_is_rejected(self):
        other = self.base / 'replacement-lock.json'; shutil.copyfile(self.lock_path, other)
        self.lock_path.unlink(); self.lock_path.symlink_to(other)
        with self.assertRaises(AssertionError): self.check()

    def test_mutated_accepted_reference_source_is_rejected(self):
        path = self.source / 'rtl/hash/tests/lifecycle_native.hpp'; path.write_text('changed\n')
        with self.assertRaises(AssertionError): self.check()

    def test_mutated_native_file_is_rejected(self):
        path = self.source / 'vendor/randomx/src/synthetic-000.txt'; path.write_text('changed\n')
        with self.assertRaises(AssertionError): self.check()

    def test_partial_private_arguments_are_rejected(self):
        with self.assertRaises(AssertionError): self.check(execution_root=self.execution)

    def test_bad_private_receipt_digest_is_rejected(self):
        options = self.private_args(); options['receipt_sha'] = '0'*64
        with self.assertRaises(AssertionError): self.check(**options)

    def test_bad_private_manifest_digest_is_rejected(self):
        options = self.private_args(); options['manifest_sha'] = '0'*64
        with self.assertRaises(AssertionError): self.check(**options)

    def test_failed_private_verification_rejects_matching_file_hash(self):
        row = load(self.verify_path); row['integrity_verified'] = False; save(self.verify_path, row)
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_private_changed_original_rejects_good_runtime_copy(self):
        (self.original / 'events.mem').write_text('changed original\n')
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_private_manifest_source_claim_cannot_replace_actual_source(self):
        self.manifest['sources'][0]['files'][0]['sha256'] = '0'*64; self.rebind_journal()
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_private_summary_tree_is_bound_to_public_tree(self):
        self.summary['source_tree'] = '4'*40; self.rebind_journal()
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_selected_fixture_only_identity(self):
        result = verify_selected_assets(self.assets, ['cases-empty.hex'], self.source)
        self.assertEqual(result['selected_fixture_files_verified'], 1)
        self.assertFalse(result['raw_journal_verified'])
        self.assertFalse(result['archive_bytes_rehashed'])

    def test_mutated_selected_fixture_is_rejected(self):
        (self.assets / 'cases-empty.hex').write_text('changed\n')
        with self.assertRaises(AssertionError): verify_selected_assets(self.assets, ['cases-empty.hex'], self.source)

    def test_symlink_selected_fixture_is_rejected(self):
        original = self.base / 'selected'; shutil.copyfile(self.assets / 'cases-empty.hex', original)
        path = self.assets / 'cases-empty.hex'; path.unlink(); path.symlink_to(original)
        with self.assertRaises(AssertionError): verify_selected_assets(self.assets, ['cases-empty.hex'], self.source)

    def test_duplicate_selected_names_are_rejected(self):
        with self.assertRaises(AssertionError):
            verify_selected_assets(self.assets, ['cases-empty.hex', 'cases-empty.hex'], self.source)


if __name__ == '__main__':
    unittest.main()
