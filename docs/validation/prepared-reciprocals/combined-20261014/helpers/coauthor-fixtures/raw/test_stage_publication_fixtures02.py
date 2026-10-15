"""Tiny synthetic publication staging fixtures; no real payload or helper main."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

E = Path(__file__).resolve().parent
sys.path.insert(0, str(E))
sys.dont_write_bytecode = True
import stage_publication_source02 as staging
import test_terminal_publication_helpers01 as parent_fixtures


class StagingFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='openrx-stage-proof-fixture-')
        self.root = Path(self.temp.name)
        self.evidence = self.root / 'evidence'
        self.authoring = self.root / 'authoring'
        self.public = self.evidence / 'public'
        self.public.mkdir(parents=True)
        self.authoring.mkdir()
        self.target = self.authoring / staging.EVIDENCE_SUBTREE
        self.fixture()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + '\n')

    def fixture(self):
        parents = staging.publication_checks.PARENTS
        source_path = str(self.root / 'frozen')
        source_archive = self.evidence / 'source.tar.gz'; source_archive.write_bytes(b'source-archive')
        source_sha = hashlib.sha256(source_archive.read_bytes()).hexdigest()
        workspace = {'source': source_path, 'source_tree': 'a' * 40, 'parents': parents,
                     'source_archive': str(source_archive), 'source_archive_sha256': source_sha,
                     'execution_id': 'original', 'execution_root': str(self.root / 'original')}
        recovery = {'source': source_path, 'execution_id': 'recovery', 'execution_root': str(self.root / 'recovery')}
        frozen = {'source': source_path, 'staged_git_tree': 'a' * 40, 'parents': parents,
                  'archive': str(source_archive), 'archive_sha256': source_sha, 'file_count': 2}
        attempts = []
        archives = {}
        for role, identity, status, rc in [('original-failed', workspace, 'PROCESS_FAILED', 1),
                                          ('finalizer-recovery', recovery, 'PROCESS_EXITED', 0)]:
            attempts.append({'role': role, 'execution_id': identity['execution_id'],
                             'execution_root': identity['execution_root'], 'status': status, 'returncode': rc})
            archive = self.evidence / (role + '.tar.gz'); archive.write_bytes(b'tiny-archive')
            archives[role] = {'role': role, 'execution_id': identity['execution_id'], 'output': identity['execution_root'],
                             'original_runner_status': status, 'original_returncode': rc,
                             'archive': str(archive), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                             'archive_bytes': archive.stat().st_size, 'archive_root': 'output',
                             'tree_kind': 'complete_runner_execution_directory',
                             'complete_output_bytes_and_original_modes_verified': True,
                             'every_archive_member_reverified': True, 'original_output_unmodified': True}
        terminal = {'source': source_path, 'runner_attempts': attempts, 'schema': 'openrx.composite-closeout.v1',
                    'composite_closeout_complete': True, 'original_wrapper_succeeded': False}
        comparison = {'source': source_path, 'status': 'pass_evidence_comparison'}
        self.context = {'workspace': workspace, 'recovery': recovery, 'frozen': frozen,
                        'terminal': terminal, 'comparison': comparison}
        self.write(self.evidence / 'combined-terminal01.json', terminal)
        self.write(self.evidence / 'combined-evidence-comparison01.json', comparison)
        (self.evidence / 'export_combination01.py').write_text('# tiny exporter identity\n')
        source = {'source': source_path, 'staged_git_tree': 'a' * 40, 'parents': parents,
                  'archive': str(source_archive), 'archive_sha256': source_sha,
                  'archive_bytes': source_archive.stat().st_size, 'file_count': 2,
                  'original_file_modes_and_complete_bytes_reverified': True, 'frozen_live_files_unchanged': True}
        coverage = {'regfile': {'runner_role': 'original-failed'}, 'finalization': {'runner_role': 'finalizer-recovery'}}
        retention = {'schema': 'openrx-combined-retention-v2-composite', 'source': source,
                     'complete_runner_attempts': archives, 'complete_component_coverage': coverage,
                     'independent_review_or_acceptance': False}
        self.write(self.public / 'source-output-retention.json', retention)
        self.write(self.public / 'raw/data.json', {'actual': 'tiny fixed data'})
        manifest = {path.relative_to(self.public).as_posix(): staging.checks.sha(path)
                    for path in self.public.rglob('*') if path.is_file()}
        self.write(self.public / 'public-files.sha256.json', manifest)
        self.result = {'status': 'pass_preservation_export', 'independent_review_or_acceptance': False,
                       'original_failed_execution_id': 'original', 'finalizer_recovery_execution_id': 'recovery',
                       'terminal_record_raw_sha256': staging.checks.sha(self.evidence / 'combined-terminal01.json'),
                       'comparison_record_raw_sha256': staging.checks.sha(self.evidence / 'combined-evidence-comparison01.json'),
                       'exporter_sha256': staging.checks.sha(self.evidence / 'export_combination01.py'),
                       'source': source, 'complete_runner_attempt_archives': archives, 'complete_component_coverage': coverage,
                       'public_folder': str(self.public), 'public_manifest_sha256': staging.checks.sha(self.public / 'public-files.sha256.json'),
                       'public_file_count': len(manifest) + 1}
        self.save_result()
        shutil.copytree(self.public, self.target)
        (self.target / 'README.md').write_text('# Added evidence explanation\n')

    def save_result(self):
        self.write(self.evidence / 'export-combination01-result.json', self.result)

    def verify(self):
        return staging.verify_export_copy(self.context, self.authoring, self.evidence)

    def test_complete_exact_copy_with_only_added_readme(self):
        proof = self.verify()
        self.assertTrue(proof['complete_export_file_set_and_exact_modes_verified'])
        self.assertEqual(proof['only_permitted_added_file'], 'README.md')
        self.assertEqual(proof['exported_public_files'], 3)

    def test_failed_export_status_rejected(self):
        self.result['status'] = 'failed'; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'Successful coauthor export'):
            self.verify()

    def test_wrong_original_export_id_rejected(self):
        self.result['original_failed_execution_id'] = 'stale'; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'execution IDs differ'):
            self.verify()

    def test_wrong_recovery_export_id_rejected(self):
        self.result['finalizer_recovery_execution_id'] = 'stale'; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'execution IDs differ'):
            self.verify()

    def test_stale_terminal_receipt_rejected(self):
        self.result['terminal_record_raw_sha256'] = 'b' * 64; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'receipt SHA differs'):
            self.verify()

    def test_stale_comparison_receipt_rejected(self):
        self.result['comparison_record_raw_sha256'] = 'b' * 64; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'receipt SHA differs'):
            self.verify()

    def test_changed_exporter_identity_rejected(self):
        (self.evidence / 'export_combination01.py').write_text('# changed\n')
        with self.assertRaisesRegex(RuntimeError, 'helper changed'):
            self.verify()

    def test_wrong_source_archive_identity_rejected(self):
        self.result['source']['archive_sha256'] = 'b' * 64; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'source retention identity'):
            self.verify()

    def test_wrong_source_parents_rejected(self):
        self.result['source']['parents'] = list(reversed(staging.publication_checks.PARENTS)); self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'source retention identity'):
            self.verify()

    def test_missing_retained_source_archive_rejected(self):
        Path(self.result['source']['archive']).unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify()

    def test_changed_retained_runner_archive_size_rejected(self):
        Path(self.result['complete_runner_attempt_archives']['original-failed']['archive']).write_bytes(b'wrong-size')
        with self.assertRaisesRegex(RuntimeError, 'archive is missing or has changed size'):
            self.verify()

    def test_original_failed_archive_cannot_be_relabeled_success(self):
        self.result['complete_runner_attempt_archives']['original-failed']['original_runner_status'] = 'PROCESS_EXITED'; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'archive binding differs'):
            self.verify()

    def test_wrong_public_manifest_sha_rejected(self):
        self.result['public_manifest_sha256'] = 'b' * 64; self.save_result()
        with self.assertRaisesRegex(RuntimeError, 'public manifest SHA differs'):
            self.verify()

    def test_mutated_copied_file_rejected(self):
        (self.target / 'raw/data.json').write_text('changed\n')
        with self.assertRaisesRegex(RuntimeError, 'public file bytes differ'):
            self.verify()

    def test_extra_copied_file_rejected(self):
        (self.target / 'extra.json').write_text('{}\n')
        with self.assertRaisesRegex(RuntimeError, 'missing/extra files'):
            self.verify()

    def test_deleted_copied_file_rejected(self):
        (self.target / 'raw/data.json').unlink()
        with self.assertRaisesRegex(RuntimeError, 'missing/extra files'):
            self.verify()

    def test_mutated_original_public_file_rejected(self):
        (self.public / 'raw/data.json').write_text('changed\n')
        with self.assertRaisesRegex(RuntimeError, 'public file bytes differ'):
            self.verify()

    def test_extra_original_public_file_rejected(self):
        (self.public / 'extra.json').write_text('{}\n')
        with self.assertRaisesRegex(RuntimeError, 'public file inventory'):
            self.verify()

    def test_deleted_original_public_file_rejected(self):
        (self.public / 'raw/data.json').unlink()
        with self.assertRaisesRegex(RuntimeError, 'public file inventory'):
            self.verify()

    def test_copied_mode_change_rejected(self):
        path = self.target / 'raw/data.json'; path.chmod(path.stat().st_mode ^ 0o020)
        with self.assertRaisesRegex(RuntimeError, 'public file mode differs'):
            self.verify()

    def test_empty_added_readme_rejected(self):
        (self.target / 'README.md').write_text('')
        with self.assertRaisesRegex(RuntimeError, 'README is empty'):
            self.verify()

    def test_copied_symlink_rejected(self):
        path = self.target / 'raw/data.json'; path.unlink(); path.symlink_to(self.public / 'raw/data.json')
        with self.assertRaisesRegex(RuntimeError, 'Linked/special'):
            self.verify()

    def test_cross_record_retention_mismatch_rejected(self):
        retention = staging.checks.load(self.public / 'source-output-retention.json')
        retention['complete_component_coverage'] = {}; self.write(self.public / 'source-output-retention.json', retention)
        with self.assertRaisesRegex(RuntimeError, 'retention record differs'):
            self.verify()

    def test_full_composite_gate_valid_ancestry(self):
        fixture = parent_fixtures.HelperFixtures('test_exact_execution_bindings'); fixture.setUp()
        try:
            b = fixture.publication_bundle()
            context = dict(zip(['workspace', 'spec', 'frozen', 'manifest', 'precheck', 'terminal', 'comparison',
                                'publication', 'recovery', 'recovery_manifest'], b))
            with patch.object(staging.publication_checks, 'OUT', fixture.root):
                candidate = staging.gate_candidate(context, b[7]['files'], fixture.root / 'authoring', fixture.root)
            self.assertEqual(candidate['declared_metadata_deltas'], [])
        finally:
            fixture.tearDown()

    def test_full_composite_gate_wrong_ancestry_rejected(self):
        fixture = parent_fixtures.HelperFixtures('test_exact_execution_bindings'); fixture.setUp()
        try:
            b = fixture.publication_bundle(); b[2]['parents'] = list(reversed(staging.publication_checks.PARENTS))
            context = dict(zip(['workspace', 'spec', 'frozen', 'manifest', 'precheck', 'terminal', 'comparison',
                                'publication', 'recovery', 'recovery_manifest'], b))
            with patch.object(staging.publication_checks, 'OUT', fixture.root), self.assertRaisesRegex(RuntimeError, 'parents differ'):
                staging.gate_candidate(context, b[7]['files'], fixture.root / 'authoring', fixture.root)
        finally:
            fixture.tearDown()

    def test_full_composite_gate_scientific_change_rejected(self):
        fixture = parent_fixtures.HelperFixtures('test_exact_execution_bindings'); fixture.setUp()
        try:
            b = fixture.publication_bundle(); files = copy.deepcopy(b[7]['files']); files['f-0']['sha256'] = 'b' * 64
            context = dict(zip(['workspace', 'spec', 'frozen', 'manifest', 'precheck', 'terminal', 'comparison',
                                'publication', 'recovery', 'recovery_manifest'], b))
            with patch.object(staging.publication_checks, 'OUT', fixture.root), self.assertRaisesRegex(RuntimeError, 'outside bounded metadata'):
                staging.gate_candidate(context, files, fixture.root / 'authoring', fixture.root)
        finally:
            fixture.tearDown()

    def test_contract_and_export_gates_precede_copy_archive(self):
        tree = ast.parse((E / 'stage_publication_source02.py').read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        calls = [n for n in ast.walk(main) if isinstance(n, ast.Call)]
        gates = [n.lineno for n in calls if isinstance(n.func, ast.Name) and n.func.id in ['gate_candidate', 'verify_export_copy']]
        staging_writes = [n.lineno for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr in ['mkdtemp', 'copy2']]
        self.assertEqual(len(gates), 2)
        self.assertLess(max(gates), min(staging_writes))


if __name__ == '__main__':
    unittest.main(verbosity=2)
