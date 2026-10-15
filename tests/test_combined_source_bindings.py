"""Reject substitutions across the retained PR70 and merged-main boundaries.

These checks mutate isolated copies of the real immutable source maps. They do
not execute native code, HDL or synthesis, or manufacture workload acceptance.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('combined_source_bindings', ROOT / 'scripts/combined_source_bindings.py')
bindings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bindings)


class CombinedBindingsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='combined-binding-rejection-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        paths = {bindings.HELPER, bindings.DECLARATION, bindings.OLD_DECLARATION,
                 'scripts/prepared_parent_bindings.py', bindings.EXECUTED_FINALIZER[0],
                 *bindings.STAGED}
        for relative, _, _ in bindings.MANIFESTS.values():
            paths.add(relative)
            paths.update(json.loads((ROOT / relative).read_text()))
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def edit_declaration(self, edit):
        path = self.root / bindings.DECLARATION
        value = json.loads(path.read_text())
        edit(value)
        path.write_text(json.dumps(value, indent=2) + '\n')

    def test_report_separates_identity_from_fresh_execution(self):
        report = bindings.validate(self.root)
        self.assertTrue(report['original_prepared219_live_bytes_unchanged'])
        self.assertTrue(report['original_regression73_live_bytes_unchanged'])
        self.assertTrue(report['original_pr70_declaration_bytes_preserved'])
        self.assertFalse(report['combined_context_previously_executed'])
        self.assertFalse(report['fresh_native_or_hdl_validation_performed'])
        expected = {'legacy53': 2, 'sequence69': 3, 'prepared219': 0,
                    'regression73': 0, 'regfile246': 4, 'finalizer259': 7}
        for key, changes in expected.items():
            row = report['historical_sources'][key]
            self.assertTrue(row['historical_manifest_bytes_preserved'])
            self.assertEqual(len(row['declared_live_successors']), changes)
            self.assertEqual(row['unchanged_live_source_count'] + changes, bindings.MANIFESTS[key][2])
        for row in report['staged_metadata_successors'].values():
            self.assertEqual(row['validation_state'], 'staged_not_executed')
        for relative, digest in report['input_bindings'].items():
            self.assertEqual(bindings.sha(self.root / relative), digest)

    def test_prior_finalizer_metadata_corrections_are_not_new_science(self):
        report = bindings.validate(self.root)
        self.assertTrue(report['executed_finalizer_manifest_bytes_preserved'])
        corrections = report['prior_finalizer_metadata_successors']
        self.assertEqual({row['path'] for row in corrections}, {
            '.github/workflows/scratchpad-finalization.yml',
            'scripts/test_scratchpad_finalization.py',
            'tests/test_scratchpad_finalization_staging.py'})
        self.assertTrue(all(row['executed_sha256'] != row['published_parent_sha256'] for row in corrections))
        self.assertEqual([row['path'] for row in report['prior_finalizer_published_input_additions']], [
            'docs/validation/program-sequence-20261013/full-v2-8x2048/artifacts.sha256.json'])

    def test_context_reports_do_not_claim_old_live_inputs_unchanged(self):
        for context in bindings.CONTEXTS:
            report = bindings.validate_context(self.root, context)
            self.assertTrue(report['declaration_used'])
            self.assertFalse(report['all_original_and_accepted_bytes_unchanged'])
            self.assertFalse(report['fresh_native_or_hdl_validation_performed'])

    def test_absent_declaration_restores_strict_legacy_guard(self):
        (self.root / bindings.DECLARATION).unlink()
        for context in bindings.CONTEXTS:
            with self.subTest(context=context), self.assertRaisesRegex(ValueError, 'legacy accepted source changed'):
                bindings.validate_context(self.root, context)

    def test_every_historical_manifest_rejects_edits_and_empty_maps(self):
        for relative, _, _ in [*bindings.MANIFESTS.values(), bindings.EXECUTED_FINALIZER]:
            path = self.root / relative
            original = path.read_bytes()
            for replacement in (original + b'\n', b'{}\n'):
                with self.subTest(path=relative, empty=replacement == b'{}\n'):
                    path.write_bytes(replacement)
                    with self.assertRaisesRegex(ValueError, 'historical manifest bytes changed'):
                        bindings.validate(self.root)
            path.write_bytes(original)

    def test_stale_old_manifest_digest_cannot_redefine_history(self):
        self.edit_declaration(lambda value: value['historical_manifests']['sequence69'].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'historical manifest identities changed'):
            bindings.validate(self.root)

    def test_original_pr70_declaration_bytes_remain_immutable(self):
        path = self.root / bindings.OLD_DECLARATION
        value = json.loads(path.read_text())
        value['overrides']['rtl/execute/randomx_integer_execute.v']['accepted_sha256'] = '0' * 64
        path.write_text(json.dumps(value) + '\n')
        with self.assertRaisesRegex(ValueError, 'original PR70 declaration bytes changed'):
            bindings.validate(self.root)

    def test_stale_reviewed_candidate_digest_is_rejected(self):
        self.edit_declaration(lambda value: value['successors']['scripts/test_program_sequence.py'].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'reviewed successor digest is stale'):
            bindings.validate(self.root)

    def test_stale_staged_candidate_digest_is_rejected(self):
        self.edit_declaration(lambda value: value['successors']['scripts/test_regfile_blake2b.py'].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'live successor changed'):
            bindings.validate(self.root)

    def test_extra_successor_cannot_broaden_the_allowlist(self):
        self.edit_declaration(lambda value: value['successors'].update({'rtl/execute/randomx_mul64.v': {
            'kind': 'binding_report_driver', 'sha256': '0' * 64, 'validation_state': 'staged_not_executed'}}))
        with self.assertRaisesRegex(ValueError, 'exact allowlist'):
            bindings.validate(self.root)

    def test_missing_successor_is_rejected(self):
        self.edit_declaration(lambda value: value['successors'].pop('scripts/test_program_sequence.py'))
        with self.assertRaisesRegex(ValueError, 'exact allowlist'):
            bindings.validate(self.root)

    def test_different_parent_cannot_reuse_the_source_declaration(self):
        self.edit_declaration(lambda value: value['parents'].update(merged_main='0' * 40))
        with self.assertRaisesRegex(ValueError, 'exact combined parents'):
            bindings.validate(self.root)

    def test_changed_or_missing_runtime_default_is_rejected(self):
        for relative, replacement in (
            ('rtl/execute/randomx_integer_execute.v', 'PREPARED_RCP=1'),
            ('rtl/execute/randomx_integer_iteration.v', 'RENAMED_RCP=0'),
        ):
            path = self.root / relative
            original = path.read_text()
            self.assertIn('PREPARED_RCP=0', original)
            path.write_text(original.replace('PREPARED_RCP=0', replacement, 1))
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, 'PREPARED_RCP default must remain 0'):
                bindings.validate(self.root)
            path.write_text(original)

    def test_unlisted_live_change_is_rejected(self):
        path = self.root / 'rtl/execute/randomx_mul64.v'
        path.write_bytes(path.read_bytes() + b'\n// undeclared change\n')
        with self.assertRaisesRegex(ValueError, 'undeclared historical source changed'):
            bindings.validate(self.root)

    def test_retained_prepared_and_regression_sources_stay_strict(self):
        for relative in ('rtl/execute/randomx_program_reciprocals.v', 'scripts/prepared_parent_bindings.py'):
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b'\n')
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, 'retained executable input changed'):
                bindings.validate(self.root)
            path.write_bytes(original)

    def test_even_redeclared_reviewed_rtl_must_match_retained_execution(self):
        relative = 'rtl/execute/randomx_integer_execute.v'
        path = self.root / relative
        path.write_bytes(path.read_bytes() + b'\n// unexecuted candidate\n')
        self.edit_declaration(lambda value: value['successors'][relative].update(sha256=bindings.sha(path)))
        with self.assertRaisesRegex(ValueError, 'reviewed successor digest is stale'):
            bindings.validate(self.root)

    def test_staged_metadata_cannot_claim_execution(self):
        self.edit_declaration(lambda value: value['successors']['scripts/test_regfile_blake2b.py'].
                              update(validation_state='executed'))
        with self.assertRaisesRegex(ValueError, 'cannot claim executed acceptance'):
            bindings.validate(self.root)

    def test_duplicate_keys_cannot_hide_a_substitution(self):
        path = self.root / bindings.DECLARATION
        path.write_text('{"schema_version":1,"schema_version":2}\n')
        with self.assertRaisesRegex(ValueError, 'duplicate JSON binding key'):
            bindings.validate(self.root)


if __name__ == '__main__':
    unittest.main()
