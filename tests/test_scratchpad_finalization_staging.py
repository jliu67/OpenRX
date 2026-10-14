"""Fail-closed preparation and dependency coverage; no native/HDL payload runs."""
import fnmatch
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('scratchpad_fixture', ROOT / 'scripts/scratchpad_finalization_fixture.py')
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
DRIVER_SPEC = importlib.util.spec_from_file_location('scratchpad_driver', ROOT / 'scripts/test_scratchpad_finalization.py')
DRIVER = importlib.util.module_from_spec(DRIVER_SPEC)
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    DRIVER_SPEC.loader.exec_module(DRIVER)
finally:
    sys.path.pop(0)


class FinalizationStagingTests(unittest.TestCase):
    def test_existing_output_rejected_before_source_or_native_access(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(FIXTURE, '_sources') as source, \
                patch.object(FIXTURE.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'fresh'):
                FIXTURE.prepare(ROOT, directory, '/missing-native-oracle')
            source.assert_not_called()
            process.assert_not_called()

    def test_source_contained_output_rejected_before_payload(self):
        with patch.object(FIXTURE, '_sources') as source, patch.object(FIXTURE.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'outside source'):
                FIXTURE.prepare(ROOT, ROOT / 'uncreated-finalization-test-output', '/missing-native-oracle')
            source.assert_not_called()
            process.assert_not_called()

    def test_source_contained_or_missing_executable_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(FIXTURE, '_sources') as source, \
                patch.object(FIXTURE.subprocess, 'run') as process:
            for executable in [ROOT / 'scripts/scratchpad_finalization_fixture.py', Path(directory) / 'missing']:
                with self.assertRaisesRegex(ValueError, 'outside source'):
                    FIXTURE.prepare(ROOT, Path(directory) / 'output', executable)
            source.assert_not_called()
            process.assert_not_called()

    def test_native_source_integrity_checked_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(FIXTURE, '_sources',
                side_effect=ValueError('pinned native source changed')), patch.object(FIXTURE.subprocess, 'run') as process:
            executable = Path(directory) / 'oracle'
            executable.write_bytes(b'not executed')
            output = Path(directory) / 'output'
            with self.assertRaisesRegex(ValueError, 'native source changed'):
                FIXTURE.prepare(ROOT, output, executable)
            self.assertFalse(output.exists())
            process.assert_not_called()

    def test_wrong_accepted_memory_rejected_without_replacing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'final-7.hex'
            path.write_bytes(b'not the accepted scratchpad\n')
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'raw final-7 identity'):
                FIXTURE._accepted(ROOT, path, None)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_wrong_accepted_registers_rejected_without_replacing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'program-registers.hex'
            path.write_bytes(b'not the accepted register file\n')
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'register-file artifact identity'):
                FIXTURE._accepted(ROOT, None, path)
            self.assertEqual(path.read_bytes(), before)

    def test_native_sources_match_all_pinned_bindings(self):
        sources = FIXTURE._sources(ROOT)
        manifest = json.loads((ROOT / 'vendor/randomx.sha256.json').read_text())
        self.assertEqual(len(manifest), 171)
        self.assertTrue({'vendor/randomx/' + path for path in manifest} <= set(sources))

    def test_connected_workflow_triggers_cover_every_inherited_input(self):
        inherited = json.loads((ROOT / 'docs/validation/regfile-blake2b-20261013/server/inputs.json').read_text())
        self.assertEqual(len(inherited), 246)
        for workflow in ['regfile-blake2b.yml', 'scratchpad-finalization.yml']:
            text = (ROOT / '.github/workflows' / workflow).read_text()
            patterns = re.findall(r"^\s+- '([^']+)'", text, re.M)
            missing = [name for name in inherited if not any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)]
            self.assertEqual(missing, [], workflow)
        final = (ROOT / '.github/workflows/scratchpad-finalization.yml').read_text()
        patterns = re.findall(r"^\s+- '([^']+)'", final, re.M)
        for path in ['rtl/hash/randomx_scratchpad_finalizer.v', 'rtl/hash/randomx_scratchpad_aes_hash.v',
                     'rtl/hash/tests/tb_scratchpad_finalization.v', 'scripts/scratchpad_finalization_fixture.py',
                     'scripts/test_scratchpad_finalization.py', 'tests/test_scratchpad_finalization_staging.py',
                     'docs/validation/program-sequence-20261013/full-v2-8x2048/final-7.hex.gz']:
            self.assertTrue(any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns), path)

    def test_mapping_metadata_distinguishes_aes_reduction_from_digest(self):
        self.assertEqual(DRIVER.mapping_output_metadata('randomx_scratchpad_aes_hash'),
                         {'aes_output_bytes': 64})
        self.assertEqual(DRIVER.mapping_output_metadata('randomx_scratchpad_finalizer'),
                         {'aes_output_bytes': 64, 'digest_bytes': 32})
        with self.assertRaisesRegex(ValueError, 'unknown'):
            DRIVER.mapping_output_metadata('unsupported')

    def test_tool_version_retains_both_streams_and_returncode(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'tool'
            binary.write_bytes(b'not executed')
            version = SimpleNamespace(stdout='stdout version', stderr='stderr version', returncode=7)
            with patch.object(DRIVER.shutil, 'which', return_value=str(binary)), \
                    patch.object(DRIVER.subprocess, 'run', return_value=version) as process:
                record = DRIVER.tool_metadata('tool', '-V')
            self.assertEqual(record['version_stdout'], version.stdout)
            self.assertEqual(record['version_stderr'], version.stderr)
            self.assertEqual(record['version_returncode'], 7)
            self.assertEqual(record['sha256'], DRIVER.sha(binary))
            process.assert_called_once_with(['tool', '-V'], capture_output=True, text=True)

    def test_consumed_program_manifest_has_exact_binding(self):
        self.assertEqual(DRIVER.sha(ROOT / DRIVER.FULL_MANIFEST), DRIVER.FULL_MANIFEST_SHA)


if __name__ == '__main__':
    unittest.main()
