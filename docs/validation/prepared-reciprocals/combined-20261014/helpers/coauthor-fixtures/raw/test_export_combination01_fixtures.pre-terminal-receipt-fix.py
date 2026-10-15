#!/usr/bin/env python3
"""Tiny external preservation fixtures; no real evidence or science execution."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import unittest

sys.dont_write_bytecode = True
E = Path(__file__).resolve().parent
HELPER = E / 'export_combination01.py'
spec = importlib.util.spec_from_file_location('export_combination01', HELPER)
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


class ExportPreservationFixtures(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='openrx-export-tiny-fixtures-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.program = self.source / 'program.v'
        self.program.write_bytes(b'// synthetic preservation fixture only\n')
        self.program.chmod(0o751)
        self.source_archive = self.root / 'tiny-source.tar.gz'
        with tarfile.open(self.source_archive, 'x:gz') as stream:
            stream.add(self.source, arcname='source')
        self.source_record = {
            'archive_sha256': export.sha(self.source_archive),
            'complete_bytes_and_original_modes_verified': True,
            'files': {'program.v': {'sha256': export.sha(self.program), 'bytes': self.program.stat().st_size,
                                    'mode': '0o751'}},
            'file_count': 1, 'staged_git_tree': 'synthetic-fixture-tree', 'parents': export.PARENTS,
        }
        self.program.chmod(0o551)

    def source_check(self):
        return export.verify_source(self.source, self.source_record, self.source_archive)

    def test_complete_source_fixture_retains_original_archive_mode(self):
        record = self.source_check()
        self.assertTrue(record['original_file_modes_and_complete_bytes_reverified'])
        self.assertTrue(record['frozen_live_files_unchanged'])
        self.assertEqual(stat.S_IMODE(self.program.stat().st_mode), 0o551)

    def test_individual_execute_mask_change_is_rejected(self):
        self.program.chmod(0o541)
        self.assertTrue(self.program.stat().st_mode & 0o111)
        with self.assertRaisesRegex(RuntimeError, 'execution bits changed'):
            self.source_check()

    def test_file_symlink_is_rejected(self):
        (self.source / 'linked-file').symlink_to(self.program)
        with self.assertRaisesRegex(RuntimeError, 'Linked/special frozen source entry'):
            self.source_check()

    def test_directory_symlink_is_rejected(self):
        target = self.root / 'outside-directory'
        target.mkdir()
        (self.source / 'linked-directory').symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'Linked/special frozen source entry'):
            self.source_check()

    def test_linked_source_root_is_rejected(self):
        linked = self.root / 'linked-source-root'
        linked.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'Missing/linked frozen source root'):
            export.verify_source(linked, self.source_record, self.source_archive)

    def test_special_source_entry_is_rejected_without_reading_it(self):
        os.mkfifo(self.source / 'synthetic-fifo')
        with self.assertRaisesRegex(RuntimeError, 'Linked/special frozen source entry'):
            self.source_check()

    def test_output_inventory_rejects_symlinks_and_special_entries(self):
        linked = self.source / 'linked-file'
        linked.symlink_to(self.program)
        with self.assertRaisesRegex(RuntimeError, 'Linked/special inventory member'):
            export.inventory(self.source)
        linked.unlink()
        os.mkfifo(self.source / 'synthetic-fifo')
        with self.assertRaisesRegex(RuntimeError, 'Linked/special inventory member'):
            export.inventory(self.source)

    def test_output_archive_is_complete_in_bytes_and_original_modes(self):
        output = self.root / 'tiny-output'
        output.mkdir(mode=0o750)
        (output / 'empty-directory').mkdir(mode=0o710)
        (output / 'binary').write_bytes(bytes(range(256)) + b'\x00\xff\r\n')
        (output / 'binary').chmod(0o640)
        (output / 'command.log').write_bytes(b'synthetic positive/negative command fixture\n')
        (output / 'command.log').chmod(0o604)
        snapshot = export.inventory(output)
        archive = self.root / 'tiny-output.tar.gz'
        receipt = export.archive_output(output, snapshot, archive)
        self.assertTrue(receipt['complete_output_bytes_and_original_modes_verified'])
        self.assertTrue(receipt['every_archive_member_reverified'])
        self.assertEqual(receipt['file_count'], 2)
        self.assertEqual(receipt['directory_count'], 1)
        self.assertEqual(export.inventory(output), snapshot)
        with tarfile.open(archive, 'r:gz') as stream:
            actual = {item.name: item for item in stream.getmembers()}
            self.assertEqual(set(actual), {'output', 'output/binary', 'output/command.log', 'output/empty-directory'})
            for name, row in snapshot['members'].items():
                item = actual['output/' + name]
                self.assertEqual(item.mode, int(row['mode'], 8))
                if row['kind'] == 'file':
                    with stream.extractfile(item) as source:
                        self.assertEqual(hashlib.sha256(source.read()).hexdigest(), row['sha256'])

    def test_existing_archive_cannot_be_overwritten(self):
        archive = self.root / 'existing-archive'
        archive.write_bytes(b'preserve prior failed/successful attempt')
        digest = export.sha(archive)
        with self.assertRaisesRegex(RuntimeError, 'Archive already exists'):
            export.archive_output(self.source, export.inventory(self.source), archive)
        self.assertEqual(export.sha(archive), digest)

    def test_existing_export_record_cannot_be_overwritten(self):
        path = self.root / 'existing-record.json'
        path.write_bytes(b'{"prior_receipt":true}\n')
        digest = export.sha(path)
        with self.assertRaises(FileExistsError):
            export.save_new(path, {'replacement': True})
        self.assertEqual(export.sha(path), digest)

    def test_raw_log_and_portable_json_have_distinct_preservation_identities(self):
        public = self.root / 'tiny-public'
        public.mkdir()
        original = self.root / 'command.log'
        original.write_bytes(b'exact original fixture\x00\r\n')
        original.chmod(0o640)
        records = []
        export.publish_record(original, public, 'fixture', 'command.log', [], records)
        self.assertEqual(records[0]['raw_original_sha256'], export.sha(original))
        self.assertEqual(records[0]['encoding'], 'lossless_gzip_of_exact_raw_bytes')
        metadata = self.root / 'receipt.json'
        metadata.write_text(json.dumps({'source': str(self.source), 'status': 'synthetic_fixture_only'}) + '\n')
        export.publish_record(metadata, public, 'fixture', 'receipt.json',
                              [(str(self.source), '<FROZEN_SOURCE>')], records)
        row = records[1]
        self.assertEqual(row['raw_original_sha256'], export.sha(public / row['public_path']))
        self.assertNotEqual(row['raw_original_sha256'], row['portable_derivative']['sha256'])
        self.assertEqual(export.load(public / row['portable_derivative']['path'])['source'], '<FROZEN_SOURCE>')
        self.assertEqual(export.load(metadata)['source'], str(self.source))

    def identities(self):
        workspace = {'parents': export.PARENTS, 'immutable_runner_sha256': export.RUNNER_SHA,
                     'execution_id': 'synthetic-fixture', 'source': str(self.source),
                     'execution_root': str(self.root / 'synthetic-execution')}
        terminal = {**workspace, 'terminal_success_and_integrity_verified': True, 'owned_descendants_drained': True,
                    'global_nonblocking_slot_free_at_verification': True, 'unit_tests': 362}
        comparison = {'status': 'pass_evidence_comparison', 'independent_review_or_acceptance': False,
                      'source': str(self.source), 'retained_source_bindings': {}}
        for key, count in [('prepared_219', 219), ('program_sequence_73', 73)]:
            comparison['retained_source_bindings'][key] = {'count': count, 'unchanged_count': count,
                                                          'all_unchanged': True, 'mismatches': {}}
        for key, rtl, mapped, name in [('regfile', 18, 17, 'combined-regfile'),
                                       ('finalizer', 41, 19, 'combined-finalization')]:
            comparison[key] = {'rtl_modes': rtl, 'mapped_modes': mapped, 'actual_synthesis_count': 3,
                               'all_fresh_and_retained_logged_records_equal': True,
                               'fresh_output': str(Path(workspace['execution_root']) / name)}
        return workspace, terminal, comparison

    def test_exact_synthetic_terminal_comparison_identities_pass(self):
        export.gates(*self.identities())

    def test_terminal_identity_or_success_changes_are_rejected(self):
        changes = {'execution_id': 'different', 'source': str(self.root / 'different-source'),
                   'execution_root': str(self.root / 'different-execution'), 'unit_tests': 361,
                   'owned_descendants_drained': False, 'terminal_success_and_integrity_verified': False,
                   'global_nonblocking_slot_free_at_verification': False, 'immutable_runner_sha256': '0' * 64}
        for key, value in changes.items():
            workspace, terminal, comparison = self.identities()
            terminal[key] = value
            with self.subTest(field=key), self.assertRaises(RuntimeError):
                export.gates(workspace, terminal, comparison)

    def test_comparison_identity_status_scope_or_retention_changes_are_rejected(self):
        cases = [(['status'], 'failed_evidence_comparison'), (['source'], str(self.root / 'different-source')),
                 (['independent_review_or_acceptance'], True),
                 (['regfile', 'fresh_output'], str(self.root / 'different-output')),
                 (['finalizer', 'rtl_modes'], 40), (['regfile', 'mapped_modes'], 16),
                 (['regfile', 'actual_synthesis_count'], 2),
                 (['finalizer', 'all_fresh_and_retained_logged_records_equal'], False),
                 (['retained_source_bindings', 'prepared_219', 'unchanged_count'], 218),
                 (['retained_source_bindings', 'program_sequence_73', 'mismatches'], {'changed': True})]
        for path, value in cases:
            workspace, terminal, comparison = self.identities()
            target = comparison
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(field=path), self.assertRaises(RuntimeError):
                export.gates(workspace, terminal, comparison)

    def test_parent_and_runner_identity_changes_are_rejected(self):
        for key, value in [('parents', ['0' * 40, '1' * 40]), ('immutable_runner_sha256', '0' * 64)]:
            workspace, terminal, comparison = self.identities()
            workspace[key] = value
            with self.subTest(field=key), self.assertRaises(RuntimeError):
                export.gates(workspace, terminal, comparison)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, default=E / 'export-combination01-fixtures-result.json')
    parser.add_argument('--log', type=Path, default=E / 'export-combination01-fixtures.log')
    args = parser.parse_args()
    require_new = [args.result.resolve(), args.log.resolve()]
    if len(set(require_new)) != len(require_new) or any(path.exists() or path.parent != E for path in require_new):
        parser.error('fresh external E result/log paths required')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ExportPreservationFixtures)
    with args.log.open('x') as stream:
        outcome = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    result = {'status': 'pass_coauthor_helper_fixtures' if outcome.wasSuccessful() else 'failed_coauthor_helper_fixtures',
              'created_utc': datetime.now(timezone.utc).isoformat(), 'tests': outcome.testsRun,
              'failures': len(outcome.failures), 'errors': len(outcome.errors),
              'helper_path': str(HELPER), 'helper_sha256': hashlib.sha256(HELPER.read_bytes()).hexdigest(),
              'fixture_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'fixture_log': str(args.log.resolve()), 'fixture_log_sha256': hashlib.sha256(args.log.read_bytes()).hexdigest(),
              'scope': 'Tiny temporary synthetic files/archives only; no real evidence/archive IO, scientific execution or independent review.'}
    with args.result.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(result, indent=2))
    return 0 if outcome.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
