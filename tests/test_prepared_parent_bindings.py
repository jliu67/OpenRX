"""Reject source/evidence substitutions at the declared parent boundary."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepared_parent_bindings', ROOT / 'scripts/prepared_parent_bindings.py')
bindings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bindings)


class ParentBindingsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='prepared-parent-rejection-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        accepted = json.loads((ROOT / bindings.MANIFEST).read_text())
        recorded = json.loads((ROOT / bindings.SERVER_INPUTS).read_text())
        paths = set(accepted) | set(recorded) | {
            bindings.MANIFEST, bindings.SERVER_INPUTS, bindings.DECLARATION, bindings.HELPER,
            bindings.SERVER + 'artifacts.sha256.json',
            *(bindings.SERVER + name for name in bindings.EVIDENCE),
            *(bindings.SERVER + label + '.log' for label in bindings.RTL_LABELS | bindings.MAPPED_LABELS),
        }
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def edit_declaration(self, edit):
        path = self.root / bindings.DECLARATION
        value = json.loads(path.read_text())
        edit(value)
        path.write_text(json.dumps(value, indent=2) + '\n')

    def test_declared_sources_report_two_exceptions_honestly(self):
        report = bindings.validate(self.root)
        self.assertEqual(report['bindings'], 53)
        self.assertEqual(report['unchanged_accepted_bindings'], 51)
        self.assertFalse(report['all_accepted_driver_IP_RTL_bytes_unchanged'])
        self.assertTrue(report['all_other_accepted_paths_unchanged'])
        self.assertTrue(report['default_PREPARED_RCP_0_verified'])
        self.assertEqual(report['recorded_server_input_bindings'], 219)
        self.assertEqual({row['path'] for row in report['declared_successors']}, set(bindings.OVERRIDES))
        self.assertIn(bindings.DECLARATION, report['input_bindings'])
        self.assertIn(bindings.HELPER, report['input_bindings'])
        evidence = bindings.verify_evidence(self.root)
        self.assertEqual(evidence['retained_server_rtl_checks'], 11)
        self.assertEqual(evidence['retained_server_mapped_checks'], 4)
        self.assertFalse(evidence['fresh_native_simulation_or_synthesis'])

    def test_absent_declaration_preserves_strict_legacy_rejection(self):
        (self.root / bindings.DECLARATION).unlink()
        with self.assertRaisesRegex(ValueError, 'changed undeclared accepted source.*randomx_integer_execute'):
            bindings.validate(self.root)

    def test_changed_undeclared_accepted_source_is_rejected(self):
        path = self.root / 'rtl/execute/randomx_mul64.v'
        path.write_bytes(path.read_bytes() + b'\n// unauthorized successor\n')
        with self.assertRaisesRegex(ValueError, 'changed undeclared accepted source.*randomx_mul64'):
            bindings.validate(self.root)

    def test_stale_old_digest_cannot_redefine_the_accepted_parent(self):
        self.edit_declaration(lambda value: value['overrides']['rtl/execute/randomx_integer_execute.v'].
                              update(accepted_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'stale accepted successor digest'):
            bindings.validate(self.root)

    def test_stale_candidate_digest_cannot_replace_recorded_execution(self):
        self.edit_declaration(lambda value: value['overrides']['rtl/execute/randomx_integer_iteration.v'].
                              update(candidate_sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'stale recorded candidate digest'):
            bindings.validate(self.root)

    def test_live_candidate_must_match_the_recorded_bytes(self):
        path = self.root / 'rtl/execute/randomx_integer_execute.v'
        path.write_bytes(path.read_bytes() + b'\n// unexecuted source\n')
        with self.assertRaisesRegex(ValueError, 'changed candidate source'):
            bindings.validate(self.root)

    def test_extra_override_cannot_broaden_the_boundary(self):
        self.edit_declaration(lambda value: value['overrides'].update({'rtl/execute/randomx_mul64.v': {
            'module': 'randomx_mul64', 'accepted_sha256': '0' * 64, 'candidate_sha256': '1' * 64}}))
        with self.assertRaisesRegex(ValueError, 'exactly the two executor/iteration paths'):
            bindings.validate(self.root)

    def test_missing_or_changed_default_mode_is_rejected(self):
        for relative, replacement in (
            ('rtl/execute/randomx_integer_execute.v', 'PREPARED_RCP=1'),
            ('rtl/execute/randomx_integer_iteration.v', 'RENAMED_RCP=0'),
        ):
            with self.subTest(relative=relative):
                path = self.root / relative
                original = path.read_text()
                self.assertIn('PREPARED_RCP=0', original)
                path.write_text(original.replace('PREPARED_RCP=0', replacement, 1))
                with self.assertRaisesRegex(ValueError, 'PREPARED_RCP default must remain 0'):
                    bindings.validate(self.root)
                path.write_text(original)

    def test_declaration_must_state_the_default_mode(self):
        self.edit_declaration(lambda value: value.pop('default_prepared_rcp'))
        with self.assertRaisesRegex(ValueError, 'unexpected declaration fields'):
            bindings.validate(self.root)

    def test_recorded_manifest_cannot_be_rewritten_to_accept_new_bytes(self):
        path = self.root / bindings.SERVER_INPUTS
        value = json.loads(path.read_text())
        value['rtl/execute/randomx_integer_execute.v'] = '0' * 64
        path.write_text(json.dumps(value, indent=2) + '\n')
        with self.assertRaisesRegex(ValueError, 'recorded server inputs bytes changed'):
            bindings.validate(self.root)

    def test_accepted_manifest_remains_immutable(self):
        path = self.root / bindings.MANIFEST
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'accepted compatibility manifest bytes changed'):
            bindings.validate(self.root)

    def test_retained_pass_log_is_evidence_not_editable_expected_output(self):
        path = self.root / bindings.SERVER / 'rtl-cache-0-0.log'
        path.write_bytes(path.read_bytes().replace(b'preparations=6', b'preparations=7'))
        with self.assertRaisesRegex(ValueError, 'retained PASS log digest changed'):
            bindings.verify_evidence(self.root)


if __name__ == '__main__':
    unittest.main()
