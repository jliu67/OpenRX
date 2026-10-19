"""Cheap synthetic identity checks; no native cache/program execution or tools.

Only the provenance representation is synthetic: the seven tiny files deliberately
are not a runnable RandomX cache. Strict identity, 181-source and 8-IP cardinality
checks are exercised without allocating a256MiB image or weakening production code.
"""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from dataset_lifecycle_support import load, save, sha, verify_assets


class PreparedAssetIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='dataset-lifecycle-identity-')
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.source, self.assets = base / 'source', base / 'runtime-assets'
        self.execution = base / 'old-execution'
        self.originals = self.execution / 'output/fixtures'
        self.source.mkdir(); self.assets.mkdir(); self.originals.mkdir(parents=True)
        self.lock_path = self.source / 'rtl/dataset_service/dataset-context.lock.json'
        self.lock_path.parent.mkdir(parents=True)
        core = ['rtl/dataset/randomx_dataset_item.v', 'rtl/execute/randomx_superscalar_execute.v',
                'rtl/execute/randomx_mul64.v']
        source_names = core + [f'synthetic/source-{n:03d}.txt' for n in range(178)]
        self.source_inputs = {}
        for n, relative in enumerate(source_names):
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f'synthetic accepted source {n}\n'.encode())
            self.source_inputs[relative] = self.identity(path)
        old = ['rtl/hash/randomx_prepared_hash_lifecycle.v', 'rtl/hash/tests/lifecycle_native.hpp',
               'rtl/hash/tests/lifecycle_reference.cpp', 'rtl/hash/tests/lifecycle_source_vpi.cpp',
               'rtl/hash/tests/lifecycle_source_dpi.cpp']
        self.accepted = {relative: self.source_inputs[relative] for relative in core}
        for relative in old:
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic unchanged accepted body\n')
            self.accepted[relative] = self.identity(path)
        self.asset_names = ['cache-0.bin', 'cache-0-metadata.json', 'cache-0-original-programs.mem',
            'cache-0-prepared-programs.mem', 'cache-0-reciprocal-metadata.json',
            'cache-0-reciprocals.mem', 'cases-real.hex']
        self.files = {}
        for relative in self.asset_names:
            data = (b'{"count":8,"timing":1,"claimed_sha256":"' + b'0'*64 + b'"}\n'
                    if relative == 'cache-0-metadata.json' else ('synthetic '+relative+'\n').encode())
            original = self.originals / relative
            original.write_bytes(data); shutil.copyfile(original, self.assets / relative)
            self.files[relative] = self.identity(original)
        self.manifest = {'execution_id': 'synthetic-accepted-run',
                         'sources': [{'kind': 'directory', 'path': str(self.source),
                                      'files': [{'relative': relative, **row} for relative, row in
                                                sorted({**self.source_inputs, **self.accepted}.items())]}]}
        self.verify_path = base / 'root-verify.json'
        save(self.verify_path, {'execution_id': 'synthetic-accepted-run', 'status': 'PROCESS_EXITED',
                                'integrity_verified': True, 'scientific_acceptance': 'unverified'})
        self.lock = {'schema': 'openrx.dataset-lifecycle.prepared-cache-lock.v1',
            'cache_id': 0, 'cache_bytes': 268435456, 'key_hex': '74657374206b657920303030',
            'prepared_programs': 8, 'global_reciprocal_entries': 239,
            'native_pin': 'aaafe71322df6602c21a5c72937ac284724ae561',
            'execution_id': 'synthetic-accepted-run', 'files': self.files,
            'source_inputs': self.source_inputs, 'accepted_ip': self.accepted}
        self.rebind_journal()

    @staticmethod
    def identity(path):
        return {'bytes': path.stat().st_size, 'sha256': sha(path)}

    def rebind_journal(self):
        """Build fresh synthetic trusted anchors, with no self-referential hashes."""
        manifest_path = self.execution / 'manifest.json'
        save(manifest_path, self.manifest)
        artifacts = [{'path': str(self.originals / relative), **row} for relative, row in self.files.items()]
        artifacts.append({'path': str(manifest_path), **self.identity(manifest_path)})
        self.receipt_path = self.execution / 'receipt.json'
        save(self.receipt_path, {'execution_id': 'synthetic-accepted-run', 'status': 'PROCESS_EXITED',
             'process': {'returncode': 0}, 'scientific_acceptance': 'unverified', 'artifacts': artifacts})
        self.lock.update({'receipt_sha256': sha(self.receipt_path), 'manifest_sha256': sha(manifest_path),
                          'root_verify_sha256': sha(self.verify_path)})
        save(self.lock_path, self.lock)

    def check(self, raw=False):
        kwargs = {'receipt': self.receipt_path, 'receipt_sha': self.lock['receipt_sha256'],
                  'verify': self.verify_path} if raw else {}
        return verify_assets(self.assets, self.lock_path, self.source, **kwargs)

    def test_lock_only_reports_identity_without_raw_journal_claim(self):
        result = self.check()
        self.assertTrue(result['identity_verified_by_trusted_lock'])
        self.assertFalse(result['raw_journal_verified'])
        self.assertEqual(result['verification_mode'], 'trusted_committed_lock_only')
        self.assertEqual(result['selected_fixture_files_verified'], 7)
        self.assertEqual(result['source_inputs_verified'], 181)
        self.assertEqual(result['accepted_ip_verified'], 8)

    def test_actual_raw_journal_and_source_rows_are_verified(self):
        result = self.check(raw=True)
        self.assertTrue(result['raw_journal_verified'])
        self.assertEqual(result['actual_prior_fixture_artifact_rows_verified'], 7)
        self.assertEqual(result['actual_prior_source_inputs_verified'], 181)
        self.assertEqual(result['actual_prior_manifest_source_rows_verified'], 186)
        self.assertEqual(result['original_runner_scientific_acceptance'], 'unverified')

    def test_mutated_asset_bytes_reject_stale_identity(self):
        path = self.assets / 'cache-0.bin'
        path.write_bytes(path.read_bytes().replace(b'synthetic', b'SYNTHETIC'))
        with self.assertRaises(AssertionError): self.check()

    def test_mutated_embedded_count_and_timing_reject_even_with_stale_claim(self):
        path = self.assets / 'cache-0-metadata.json'
        original = path.read_bytes()
        for old, new in [(b'"count":8', b'"count":9'), (b'"timing":1', b'"timing":2')]:
            with self.subTest(field=old):
                path.write_bytes(original.replace(old, new))
                with self.assertRaises(AssertionError): self.check()
        path.write_bytes(original)

    def test_stale_asset_byte_count_is_rejected(self):
        self.lock['files']['cache-0.bin']['bytes'] += 1
        save(self.lock_path, self.lock)
        with self.assertRaises(AssertionError): self.check()

    def test_mutated_source_bytes_reject_stale_lock_claim(self):
        path = self.source / 'rtl/execute/randomx_mul64.v'
        path.write_bytes(path.read_bytes().replace(b'accepted', b'ACCEPTED'))
        with self.assertRaises(AssertionError): self.check()

    def test_mutated_accepted_legacy_body_is_rejected(self):
        path = self.source / 'rtl/hash/tests/lifecycle_native.hpp'
        path.write_bytes(path.read_bytes().replace(b'unchanged', b'UNCHANGED'))
        with self.assertRaises(AssertionError): self.check()

    def test_actual_manifest_claim_cannot_substitute_current_source_identity(self):
        # All journal hashes are coherently rebound, but this actual source row
        # disagrees with the trusted lock/current bytes. An inputs.json-style
        # embedded report cannot make it pass.
        self.manifest['sources'][0]['files'][0]['sha256'] = 'f'*64
        self.rebind_journal()
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_mutated_original_artifact_is_rejected_even_when_runtime_copy_matches(self):
        path = self.originals / 'cache-0-prepared-programs.mem'
        path.write_bytes(path.read_bytes().replace(b'synthetic', b'SYNTHETIC'))
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_failed_root_verification_is_rejected_even_when_its_hash_matches(self):
        record = load(self.verify_path); record['integrity_verified'] = False
        save(self.verify_path, record); self.rebind_journal()
        with self.assertRaises(AssertionError): self.check(raw=True)

    def test_symlink_asset_rejected(self):
        path = self.assets / 'cache-0-reciprocals.mem'
        path.unlink(); path.symlink_to(self.originals / path.name)
        with self.assertRaises(AssertionError): self.check()


if __name__ == '__main__':
    unittest.main()
