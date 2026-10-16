"""Invalid launch requests must fail before writing source or existing output."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / 'scripts/test_prepared_hash_lifecycle.py'


class StagingTest(unittest.TestCase):
    def setUp(self):
        # Retain these tiny rejection fixtures under the admitted TMPDIR.
        self.directory = Path(tempfile.mkdtemp(prefix='lifecycle-staging-'))
        self.fresh = self.directory / 'fresh'

    def reject(self, *args, output=None):
        result = subprocess.run([sys.executable, '-B', str(DRIVER), '--output',
            str(output or self.fresh), *args], capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), timeout=15)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('error:', result.stderr)
        if output is None:
            self.assertFalse(self.fresh.exists())

    def test_source_tree_output_is_rejected_without_mutation(self):
        target = ROOT / ('.lifecycle-rejection-' + uuid.uuid4().hex)
        self.assertFalse(target.exists())
        self.reject(output=target)
        self.assertFalse(target.exists())

    def test_existing_output_is_preserved(self):
        target = self.directory / 'existing'
        target.mkdir()
        sentinel = target / 'original-receipt'
        sentinel.write_bytes(b'preserve original bytes\n')
        self.reject(output=target)
        self.assertEqual(list(target.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'preserve original bytes\n')

    def test_duplicate_profiles_do_not_alias_output(self):
        self.reject('--profiles', 'ideal', 'ideal')

    def test_duplicate_variants_do_not_alias_output(self):
        self.reject('--variants', 'prepared', 'prepared')

    def test_duplicate_recovery_selections_do_not_alias_output(self):
        self.reject('--cancellation-phases', '1', '1')
        self.reject('--error-ports', '1', '1')

    def test_recovery_selections_stay_in_documented_range(self):
        self.reject('--cancellation-phases', '7')
        self.reject('--error-ports', '9')

    def test_malformed_input_is_rejected(self):
        self.reject('--input-hex', 'not-hex')

    def test_oversized_input_is_rejected(self):
        self.reject('--input-hex', 'ab' * 81)

    def test_library_reuse_requires_provenance(self):
        self.reject('--native-library', str(self.directory / 'unproven.a'))

    def test_compiled_backend_requires_retained_tool(self):
        self.reject('--backend', 'verilator')

    def test_nonpositive_duration_is_rejected(self):
        self.reject('--timeout', '0')

    def test_interface_only_cannot_claim_a_full_hash(self):
        self.reject('--interfaces-only', '--full-v2', '--capacity-checks')

    def test_interface_only_requires_an_actual_test(self):
        self.reject('--interfaces-only')


if __name__ == '__main__':
    unittest.main()
