"""Tiny external fixtures only; no runner/scientific command or GitHub invocation."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

E = Path(__file__).resolve().parent
sys.path.insert(0, str(E))
sys.dont_write_bytecode = True
import verify_terminal01 as terminal
import publish_combination01 as publisher


class HelperFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='openrx-helper-fix-fixture-')
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def file(self, name, data=b'x', mode=0o644):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)
        return path

    def identities(self):
        source, execution = str(self.root / 'source'), str(self.root / 'execution')
        digest = hashlib.sha256(b'x').hexdigest()
        files = {'f-' + str(i): {'sha256': digest, 'bytes': 1, 'mode': '0o644'} for i in range(281)}
        workspace = {'source': source, 'execution_root': execution, 'execution_id': 'tiny-execution',
                     'parents': terminal.PARENTS, 'source_tree': 't' * 40, 'source_archive': str(self.root / 'source.tar.gz'),
                     'source_archive_sha256': 'a' * 64, 'immutable_runner_sha256': terminal.RUNNER_SHA}
        spec = {'source': source, 'parents': terminal.PARENTS, 'staged_git_tree': 't' * 40,
                'source_archive_sha256': 'a' * 64, 'runner': str(terminal.RUNNER), 'wrapper': str(self.root / 'wrapper.py'),
                'wrapper_sha256': digest, 'request_key': 'tiny-request', 'kind': 'simulation'}
        frozen = {'source': source, 'parents': terminal.PARENTS, 'staged_git_tree': 't' * 40,
                  'archive': workspace['source_archive'], 'archive_sha256': 'a' * 64, 'files': files, 'file_count': 281}
        manifest = {'cwd': source, 'execution_id': 'tiny-execution', 'unit': 'tiny-fixture.service', 'runner': {'sha256': terminal.RUNNER_SHA, 'path': str(terminal.RUNNER)},
                    'request_key': 'tiny-request', 'kind': 'simulation',
                    'argv': ['/tiny/python', '-B', spec['wrapper'], source, execution],
                    'inputs': [{'path': spec['wrapper'], 'sha256': digest}],
                    'sources': [{'path': source, 'kind': 'directory',
                                 'files': [{'relative': name, 'sha256': row['sha256'], 'bytes': 1} for name, row in files.items()]}]}
        precheck = {'status': 'pass', 'parents': {'reviewed_pr70': terminal.PARENTS[0], 'merged_main': terminal.PARENTS[1]},
                    'input_bindings': {name: row['sha256'] for name, row in files.items()}}
        return workspace, spec, frozen, manifest, precheck

    def test_exact_execution_bindings(self):
        values = self.identities()
        self.assertEqual(len(terminal.bind_inputs(*values)), 281)

    def publication_bundle(self):
        workspace, spec, frozen, manifest, precheck = self.identities()
        recovery_root = self.root / 'recovery'
        recovery = {'source': workspace['source'], 'execution_root': str(recovery_root), 'execution_id': 'tiny-recovery',
                    'request_key': 'tiny-recovery-request', 'wrapper': str(self.root / 'recover.py'),
                    'wrapper_sha256': spec['wrapper_sha256'], 'runner': str(terminal.RUNNER),
                    'immutable_runner_sha256': terminal.RUNNER_SHA, 'parents': terminal.PARENTS,
                    'source_tree': workspace['source_tree'], 'source_archive_sha256': workspace['source_archive_sha256']}
        recovery_manifest = copy.deepcopy(manifest)
        recovery_manifest.update(execution_id=recovery['execution_id'], request_key=recovery['request_key'],
            argv=['/tiny/python', '-B', recovery['wrapper'], recovery['source'], str(recovery_root)],
            inputs=[{'path': recovery['wrapper'], 'sha256': recovery['wrapper_sha256']}])
        records = {'active-execution-workspace01.json': workspace, 'execution-spec01.json': spec,
                   'combined-source01.json': frozen, 'combined-binding-precheck01.json': precheck,
                   'recovery-execution02.json': recovery}
        for name, value in records.items():
            self.file(name, json.dumps(value).encode())
        for name in ['verify_terminal01.py', 'compare_combined_outputs.py']:
            self.file(name, (E / name).read_bytes())
        old_commands = [{'label': 'existing-and-focused-unit-tests', 'returncode': 0}, {'label': 'regfile', 'returncode': 0}]
        new_commands = [{'label': 'finalization', 'returncode': 0}]
        commands = [{**row, 'attempt_role': 'original-failed', 'execution_id': workspace['execution_id']} for row in old_commands]
        commands += [{**row, 'attempt_role': 'finalizer-recovery', 'execution_id': recovery['execution_id']} for row in new_commands]
        stages = {'original-failed': [{'phase': p} for p in ['payload-start', 'unit-tests-complete', 'regfile-complete']],
                  'finalizer-recovery': [{'phase': p} for p in ['payload-start', 'finalization-complete']]}
        attempts = []
        for relative, identity, bound, status, rc, ledger, role in [
            ('execution', workspace, manifest, 'PROCESS_FAILED', 1, old_commands, 'original-failed'),
            ('recovery', recovery, recovery_manifest, 'PROCESS_EXITED', 0, new_commands, 'finalizer-recovery')]:
            process = {'status': status, 'returncode': rc}
            receipt = {'status': status, 'execution_id': identity['execution_id'], 'process': process,
                       'systemd': {'SERVICE_RESULT': 'success' if rc == 0 else 'exit-code'}}
            for name, value in [('manifest.json', bound), ('process-result.json', process), ('receipt.json', receipt),
                                ('combined-commands.json', ledger), ('combined-resource-stages.json', stages[role])]:
                self.file(relative + '/' + name, json.dumps(value).encode())
            attempts.append({'role': role, 'execution_id': identity['execution_id'], 'execution_root': identity['execution_root'],
                'status': status, 'returncode': rc, 'integrity_verified': True, 'owned_descendants_drained': True,
                'runner_verification': {'execution_id': identity['execution_id'], 'integrity_verified': True,
                                       'scientific_acceptance': 'unverified', 'status': status},
                'receipt_sha256': terminal.sha(self.root / relative / 'receipt.json'),
                'execution_manifest_sha256': terminal.sha(self.root / relative / 'manifest.json'),
                'runner_source_file_bindings_sha256': hashlib.sha256(json.dumps(bound['sources'][0]['files'],
                    sort_keys=True, separators=(',', ':')).encode()).hexdigest(), 'source_file_count': frozen['file_count']})
        diagnostic = self.file('execution/stderr.log', b"KeyError: 'status'\n")
        terminal_record = {'schema': 'openrx.composite-closeout.v1',
            'source': workspace['source'], 'execution_root': workspace['execution_root'], 'execution_id': workspace['execution_id'],
            'parents': terminal.PARENTS, 'source_tree': workspace['source_tree'], 'source_archive_sha256': workspace['source_archive_sha256'],
            'terminal_success_and_integrity_verified': False, 'original_wrapper_succeeded': False,
            'composite_closeout_complete': True, 'recovery_wrapper_succeeded': True, 'owned_descendants_drained': True,
            'global_nonblocking_slot_free_at_verification': True, 'exact_execute_masks_and_regular_entries_verified': True,
            'unit_tests': 362, 'immutable_runner_sha256': terminal.RUNNER_SHA, 'scientific_provenance_input_count': 281,
            'scientific_provenance_input_bindings': precheck['input_bindings'], 'runner_attempts': attempts,
            'runner_verification': attempts[0]['runner_verification'], 'receipt_sha256': attempts[0]['receipt_sha256'],
            'execution_manifest_sha256': attempts[0]['execution_manifest_sha256'],
            'coordination_receipt_sha256': {name: terminal.sha(self.root / name) for name in records},
            'terminal_helper_sha256': terminal.sha(self.root / 'verify_terminal01.py'),
            'original_failure': {'diagnostic': "KeyError: 'status'", 'external_wrapper_line': 70,
                'original_wrapper_succeeded': False, 'unit_tests': 362, 'native_component_driver_returncode': 0,
                'finalization_started_in_original': False, 'stderr_sha256': terminal.sha(diagnostic)},
            'component_commands': commands, 'commands': commands, 'resource_stages_by_attempt': stages,
            'component_outputs': {'regfile': str(self.root / 'execution/combined-regfile'),
                                  'finalizer': str(self.root / 'recovery/combined-finalization')}, 'component_records': {}}
        comparison = {'source': workspace['source'], 'status': 'pass_evidence_comparison',
            'independent_review_or_acceptance': False,
            'comparison_helper_sha256': terminal.sha(self.root / 'compare_combined_outputs.py'),
            'retained_source_bindings': {name: {'all_unchanged': True, 'count': count, 'unchanged_count': count, 'mismatches': {}}
                                       for name, count in [('prepared_219', 219), ('program_sequence_73', 73)]}}
        for key, output, counts in [('regfile', 'execution/combined-regfile', (18, 17)),
                                    ('finalizer', 'recovery/combined-finalization', (41, 19))]:
            inputs = self.file(output + '/inputs.json', json.dumps(precheck['input_bindings']).encode())
            summary = self.file(output + '/summary.json', b'{}')
            artifact = self.file(output + '/artifacts.sha256.json', b'{}')
            comparison[key] = {'fresh_output': str(inputs.parent), 'rtl_modes': counts[0], 'mapped_modes': counts[1],
                'actual_synthesis_count': 3, 'all_fresh_and_retained_logged_records_equal': True,
                'fresh_source_bindings': {'sha256': terminal.sha(inputs)}}
            terminal_record['component_records'][key] = {'output': str(inputs.parent), 'rtl_modes': counts[0],
                'mapped_modes': counts[1], 'actual_synthesis_count': 3, 'actual_PASS_logs_verified': True,
                'summary_sha256': terminal.sha(summary), 'artifact_manifest_sha256': terminal.sha(artifact),
                'inputs_sha256': terminal.sha(inputs)}
        publication = {'parents': terminal.PARENTS, 'executed_source': workspace['source'],
            'executed_source_record_sha256': terminal.sha(self.root / 'combined-source01.json'),
            'complete_bytes_and_original_modes_verified': True, 'files': copy.deepcopy(frozen['files']),
            'declared_metadata_deltas': []}
        return [workspace, spec, frozen, manifest, precheck, terminal_record, comparison, publication, recovery, recovery_manifest]

    def test_publication_gate_binds_all_281(self):
        bundle = self.publication_bundle()
        with patch.object(publisher, 'OUT', self.root):
            self.assertEqual(publisher.publication_gate(*bundle), [])

    def test_recovery_manifest_source_change_rejected(self):
        bundle = self.publication_bundle(); bundle[9]['sources'][0]['files'][0]['sha256'] = 'b' * 64
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'file bindings differ'):
            publisher.publication_gate(*bundle)

    def test_recovery_request_identity_change_rejected(self):
        bundle = self.publication_bundle(); bundle[8]['request_key'] += '-wrong'
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'request identity'):
            publisher.publication_gate(*bundle)

    def test_recovery_declared_parent_change_rejected(self):
        bundle = self.publication_bundle(); bundle[8]['parents'] = list(reversed(terminal.PARENTS))
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'declared original identity differs'):
            publisher.publication_gate(*bundle)

    def test_failed_original_cannot_be_relabeled_success(self):
        bundle = self.publication_bundle(); bundle[5]['runner_attempts'][0]['status'] = 'PROCESS_EXITED'
        bundle[5]['runner_attempts'][0]['returncode'] = 0
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'relabeled'):
            publisher.publication_gate(*bundle)

    def test_legacy_terminal_success_flag_rejected(self):
        bundle = self.publication_bundle(); bundle[5]['terminal_success_and_integrity_verified'] = True
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'preserved original failure'):
            publisher.publication_gate(*bundle)

    def test_incomplete_composite_rejected(self):
        bundle = self.publication_bundle(); bundle[5]['composite_closeout_complete'] = False
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'preserved original failure'):
            publisher.publication_gate(*bundle)

    def test_recovery_receipt_mutation_rejected(self):
        bundle = self.publication_bundle(); self.file('recovery/receipt.json', b'{}')
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'receipt/manifest changed'):
            publisher.publication_gate(*bundle)

    def test_collected_failed_service_uses_exact_failed_receipt(self):
        bundle = self.publication_bundle(); root = Path(bundle[0]['execution_root'])
        receipt = terminal.load(root / 'receipt.json')
        verified = bundle[5]['runner_attempts'][0]['runner_verification']
        status = {'execution_id': bundle[0]['execution_id'], 'receipt': receipt,
                  'unit': {'query_returncode': 1, 'LoadState': 'not-found', 'ActiveState': 'inactive'}}
        attempt = self.root / 'verification'; attempt.mkdir()
        control = 'LoadState=not-found\nActiveState=inactive\nResult=success\nExecMainStatus=0\nControlGroup=\n'
        with patch.object(terminal.subprocess, 'check_output', side_effect=[json.dumps(status), json.dumps(verified), control]):
            row = terminal.verify_runner_attempt('original-failed', bundle[0]['execution_id'], root,
                                                 bundle[3], 'PROCESS_FAILED', 1, attempt)
        self.assertEqual(row['status'], 'PROCESS_FAILED')
        self.assertEqual(row['returncode'], 1)

    def test_unexplained_service_query_error_rejected(self):
        bundle = self.publication_bundle(); root = Path(bundle[0]['execution_root'])
        receipt = terminal.load(root / 'receipt.json')
        status = {'execution_id': bundle[0]['execution_id'], 'receipt': receipt,
                  'unit': {'query_returncode': 1, 'LoadState': 'error', 'ActiveState': 'inactive'}}
        attempt = self.root / 'verification'; attempt.mkdir()
        with patch.object(terminal.subprocess, 'check_output', return_value=json.dumps(status)), \
             self.assertRaisesRegex(RuntimeError, 'not finalized/drained'):
            terminal.verify_runner_attempt('original-failed', bundle[0]['execution_id'], root,
                                           bundle[3], 'PROCESS_FAILED', 1, attempt)

    def test_components_cannot_point_to_wrong_attempt(self):
        bundle = self.publication_bundle(); bundle[5]['component_outputs']['finalizer'] = str(self.root / 'execution/combined-finalization')
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'component roots differ'):
            publisher.publication_gate(*bundle)

    def failed_wrapper_fixture(self):
        root = self.root / 'original'
        spec = {'wrapper': str(self.root / 'wrapper.py')}
        text = ('Traceback (most recent call last):\n  File "' + spec['wrapper'] +
                '", line 70, in <module>\n    assert summary[\'status\']==\'pass\',summary\nKeyError: \'status\'\n')
        self.file('original/stderr.log', text.encode())
        self.file('original/stdout.log', b'START existing-and-focused-unit-tests\nCOMPLETE existing-and-focused-unit-tests returncode0\nSTART regfile\n')
        self.file('original/unit-tests-console.log', b'\nRan 362 tests in 0.01s\n\nOK\n')
        self.file('original/combined-regfile/summary.json', b'{"rtl_modes":18}')
        return root, spec, [{'label': 'existing-and-focused-unit-tests', 'returncode': 0}, {'label': 'regfile', 'returncode': 0}], [
            {'phase': name} for name in ['payload-start', 'unit-tests-complete', 'regfile-complete']]

    def test_exact_original_wrapper_diagnostic_preserved(self):
        result = terminal.check_failed_wrapper(*self.failed_wrapper_fixture())
        self.assertFalse(result['original_wrapper_succeeded'])
        self.assertEqual(result['diagnostic'], "KeyError: 'status'")

    def test_different_original_failure_rejected(self):
        values = self.failed_wrapper_fixture(); self.file('original/stderr.log', b'other failure\n')
        with self.assertRaisesRegex(RuntimeError, 'exact preserved status-key'):
            terminal.check_failed_wrapper(*values)

    def test_original_finalizer_cannot_be_fabricated(self):
        values = self.failed_wrapper_fixture(); self.file('original/combined-finalization/summary.json', b'{}')
        with self.assertRaisesRegex(RuntimeError, 'unexpected finalization output'):
            terminal.check_failed_wrapper(*values)

    def test_original_summary_cannot_gain_status(self):
        values = self.failed_wrapper_fixture(); self.file('original/combined-regfile/summary.json', b'{"status":"pass"}')
        with self.assertRaisesRegex(RuntimeError, 'status-less output'):
            terminal.check_failed_wrapper(*values)

    def test_publication_wrong_terminal_source(self):
        bundle = self.publication_bundle(); bundle[5]['source'] += '-wrong'
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'execution identity differs'):
            publisher.publication_gate(*bundle)

    def test_publication_wrong_executed_ancestor(self):
        bundle = self.publication_bundle(); bundle[7]['executed_source_record_sha256'] = 'b' * 64
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'ancestor unbound'):
            publisher.publication_gate(*bundle)

    def test_publication_stale_coordination_receipt(self):
        bundle = self.publication_bundle(); self.file('execution-spec01.json', b'{}')
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'coordination receipt changed'):
            publisher.publication_gate(*bundle)

    def test_publication_missing_actual_input_binding(self):
        bundle = self.publication_bundle()
        path = self.file('execution/combined-regfile/inputs.json', b'{}')
        bundle[6]['regfile']['fresh_source_bindings']['sha256'] = terminal.sha(path)
        bundle[5]['component_records']['regfile']['inputs_sha256'] = terminal.sha(path)
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'omits Scientific'):
            publisher.publication_gate(*bundle)

    def test_publication_undeclared_metadata_addition(self):
        bundle = self.publication_bundle()
        bundle[7]['files'][publisher.NEW_EVIDENCE + 'README.md'] = {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o644'}
        with patch.object(publisher, 'OUT', self.root), self.assertRaisesRegex(RuntimeError, 'delta declaration'):
            publisher.publication_gate(*bundle)

    def test_source_identity_mismatch(self):
        values = self.identities(); values[1]['source'] += '-wrong'
        with self.assertRaisesRegex(RuntimeError, 'source identities'):
            terminal.bind_inputs(*values)

    def test_parent_identity_mismatch(self):
        values = self.identities(); values[2]['parents'] = list(reversed(terminal.PARENTS))
        with self.assertRaisesRegex(RuntimeError, 'parents differ'):
            terminal.bind_inputs(*values)

    def test_runner_source_blob_mismatch(self):
        values = self.identities(); values[3]['sources'][0]['files'][0]['sha256'] = 'b' * 64
        with self.assertRaisesRegex(RuntimeError, 'file bindings differ'):
            terminal.bind_inputs(*values)

    def test_duplicate_runner_source_path(self):
        values = self.identities(); values[3]['sources'][0]['files'].append(values[3]['sources'][0]['files'][0])
        with self.assertRaisesRegex(RuntimeError, 'inventory differs'):
            terminal.bind_inputs(*values)

    def test_281_bound_input_mutation(self):
        values = self.identities(); values[4]['input_bindings']['f-0'] = 'b' * 64
        with self.assertRaisesRegex(RuntimeError, '281 inputs differ'):
            terminal.bind_inputs(*values)

    def test_exact_partial_execute_mask(self):
        path = self.file('source/tool', mode=0o744)
        record = {'files': {'tool': {'sha256': terminal.sha(path), 'bytes': 1, 'mode': '0o744'}}, 'file_count': 1}
        self.assertEqual(terminal.verify_source(path.parent, record), 1)
        path.chmod(0o755)
        with self.assertRaisesRegex(RuntimeError, 'execute mask changed'):
            terminal.verify_source(path.parent, record)

    def test_source_symlink_rejected(self):
        path = self.file('source/real'); (path.parent / 'link').symlink_to(path.name)
        with self.assertRaisesRegex(RuntimeError, 'Linked/special'):
            terminal.inventory(path.parent)

    def test_source_fifo_rejected(self):
        path = self.file('source/real'); os.mkfifo(path.parent / 'fifo')
        with self.assertRaisesRegex(RuntimeError, 'Linked/special'):
            terminal.inventory(path.parent)

    def test_exclusive_receipt_preserves_original(self):
        path = self.root / 'receipt.json'; terminal.save(path, {'old': True})
        with self.assertRaises(FileExistsError):
            terminal.save(path, {'new': True})
        self.assertEqual(terminal.load(path), {'old': True})

    def test_metadata_allowlist_exact_delta(self):
        before = {'memory/STATE.md': {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o644'}}
        after = copy.deepcopy(before); after['memory/STATE.md']['sha256'] = 'b' * 64
        new = publisher.NEW_EVIDENCE + 'README.md'
        after[new] = {'sha256': 'c' * 64, 'bytes': 1, 'mode': '0o444'}
        self.assertEqual(publisher.metadata_deltas(before, after), [
            {'path': new, 'old_sha256': None, 'new_sha256': 'c' * 64},
            {'path': 'memory/STATE.md', 'old_sha256': 'a' * 64, 'new_sha256': 'b' * 64}])

    def test_post_execution_driver_edit_rejected(self):
        before = {'scripts/test_regfile_blake2b.py': {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o755'}}
        after = copy.deepcopy(before); after[next(iter(after))]['sha256'] = 'b' * 64
        with self.assertRaisesRegex(RuntimeError, 'outside bounded metadata'):
            publisher.metadata_deltas(before, after)

    def test_root_readme_edit_rejected(self):
        before = {'README.md': {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o644'}}
        after = copy.deepcopy(before); after['README.md']['sha256'] = 'b' * 64
        with self.assertRaisesRegex(RuntimeError, 'outside bounded metadata'):
            publisher.metadata_deltas(before, after)

    def test_historical_map_edit_rejected(self):
        name = 'docs/validation/prepared-reciprocals/server/inputs.json'
        before = {name: {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o644'}}
        after = copy.deepcopy(before); after[name]['sha256'] = 'b' * 64
        with self.assertRaisesRegex(RuntimeError, 'outside bounded metadata'):
            publisher.metadata_deltas(before, after)

    def test_publication_deletion_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'deletes'):
            publisher.metadata_deltas({'old': {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o644'}}, {})

    def test_publication_partial_execute_change_rejected(self):
        before = {'tool': {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o744'}}
        after = copy.deepcopy(before); after['tool']['mode'] = '0o755'
        with self.assertRaisesRegex(RuntimeError, 'exact execute mask'):
            publisher.metadata_deltas(before, after)

    def test_new_executable_evidence_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'executable'):
            publisher.metadata_deltas({}, {publisher.NEW_EVIDENCE + 'tool': {'sha256': 'a' * 64, 'bytes': 1, 'mode': '0o755'}})

    def test_body_requires_concrete_validation(self):
        path = self.file('body.md', b'362 units;18 RTL / 17 mapped;41 RTL / 19 mapped;219 and 73; failed wrapper recovered; independent review; __PUBLISHED_HEAD__')
        self.assertIn('__PUBLISHED_HEAD__', publisher.body_preflight(path))
        for placeholder in ['__VALIDATION__', '__validation__']:
            path.write_text('draft ' + placeholder + ' __PUBLISHED_HEAD__')
            with self.assertRaisesRegex(RuntimeError, 'Unresolved'):
                publisher.body_preflight(path)

    def test_body_missing_rejected_before_api(self):
        values = self.identities()
        names = ['active-execution-workspace01.json', 'execution-spec01.json', 'combined-source01.json',
                 'manifest.json', 'combined-binding-precheck01.json', 'combined-terminal01.json',
                 'combined-evidence-comparison01.json', 'publication-source01.json']
        records = dict(zip(names, [values[0], values[1], values[2], values[3], values[4], {}, {}, {}]))
        records['recovery-execution02.json'] = {'execution_root': str(self.root / 'recovery')}
        called = []
        with patch.object(publisher, 'OUT', self.root), patch.object(publisher, 'load', side_effect=lambda p: records[p.name]), \
             patch.object(publisher, 'publication_gate', return_value=[]), patch.object(publisher, 'api', side_effect=lambda *a, **k: called.append(a)):
            with self.assertRaises(FileNotFoundError):
                publisher.main()
        self.assertEqual(called, [])

    def test_terminal_integrity_call_lexically_under_lock(self):
        # This structural check complements the pure fixtures: executing main
        # would invoke the immutable runner. No real runner is called here.
        import ast
        tree = ast.parse((E / 'verify_terminal01.py').read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        lock = next(n for n in ast.walk(main) if isinstance(n, ast.With) and any(
            isinstance(i.optional_vars, ast.Name) and i.optional_vars.id == 'slot' for i in n.items))
        calls = [n for n in ast.walk(lock) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == 'verify_runner_attempt']
        self.assertEqual(len(calls), 2)
        self.assertLess(next(n.lineno for n in ast.walk(lock) if isinstance(n, ast.Call)
                             and isinstance(n.func, ast.Attribute) and n.func.attr == 'flock'), min(n.lineno for n in calls))



if __name__ == '__main__':
    unittest.main(verbosity=2)
