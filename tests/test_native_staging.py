"""Lightweight staging/launch fixtures; no compilation or RandomX execution."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from test_steady_records import steady, fixture, encode

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stage_native', ROOT / 'scripts/stage_native.py')
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
spec = importlib.util.spec_from_file_location('native_steady', ROOT / 'tests/native_steady.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

SOURCE_FILES = ('vendor/randomx.lock.json', 'vendor/randomx.sha256.json',
                'scripts/verify_vendor.py', 'scripts/build_steady.sh', 'scripts/stage_native.py',
                'benchmarks/steady/main.cpp', 'benchmarks/steady/CMakeLists.txt')
ARTIFACTS = ('randomx/librandomx.a', 'randomx/randomx-benchmark', 'randomx/randomx-tests',
             'steady/openrx-steady', 'randomx/CMakeCache.txt', 'steady/CMakeCache.txt')


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'retained-source'
        for relative in SOURCE_FILES:
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic source ' + relative)
        self.build = self.base / 'execution/native-build'
        self.output = self.base / 'trial-execution/output'

    def fake_tool(self, command, cwd, stdout, stderr):
        stdout.write('synthetic tool output\n')
        if command[:2] == ['cmake', '--build']:
            for relative in ARTIFACTS:
                path = Path(cwd) / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('synthetic artifact ' + relative)
        return subprocess.CompletedProcess(command, 0)

    def build_fixture(self, tool=None):
        before = {p: p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        with mock.patch.object(stage, 'ROOT', self.source), \
                mock.patch.object(stage.subprocess, 'run', side_effect=tool or self.fake_tool) as run, \
                contextlib.redirect_stdout(io.StringIO()):
            rc = stage.main(['--build-root', str(self.build), '--jobs', '6', '--arch', 'native'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.source.rglob('*') if p.is_file()})
        return rc, json.loads((self.build / 'build.json').read_text()), run

    def launch(self, body=None, **options):
        binary = self.build / 'steady/openrx-steady'
        if body is not None:
            binary.write_text('#!/usr/bin/env python3\n' + body)
            binary.chmod(0o755)
            receipt = json.loads((self.build / 'build.json').read_text())
            receipt['artifacts']['steady/openrx-steady'] = hashlib.sha256(binary.read_bytes()).hexdigest()
            (self.build / 'build.json').write_text(json.dumps(receipt))
        argv = ['--build-root', str(self.build), '--output-dir', str(self.output),
                '--nonces', '17', '--warmup-nonces', '7', '--repeats', '2', '--min-seconds', '1']
        for key, value in options.items():
            argv += ['--' + key.replace('_', '-'), str(value)]
        with mock.patch.object(steady, 'ROOT', self.source), \
                mock.patch.object(steady, 'capture', return_value={'returncode': 0}), \
                mock.patch.object(steady.platform, 'platform', return_value='synthetic fixture platform'), \
                contextlib.redirect_stdout(io.StringIO()):
            rc = steady.main(argv)
        return rc, json.loads((self.output / 'run.json').read_text())

    def test_fresh_build_retains_logs_artifact_binding_and_source_isolation(self):
        rc, report, run = self.build_fixture()
        self.assertEqual(rc, 0)
        self.assertEqual(report['status'], 'built')
        self.assertEqual(report['scientific_acceptance'], 'unverified')
        self.assertEqual(len(report['artifacts']), 6)
        self.assertEqual(len(report['log_sha256']), 7)
        commands = [c.args[0] for c in run.call_args_list]
        self.assertEqual(commands[2], [stage.sys.executable, str(self.source / 'scripts/verify_vendor.py')])
        self.assertIn('-DRANDOMX_LIBRARY=' + str(self.build / 'randomx/librandomx.a'), commands[5])
        self.assertEqual(commands[4][-2:], ['--parallel', '6'])
        self.assertEqual(commands[6][-2:], ['--parallel', '6'])
        self.assertFalse((self.source / 'build').exists())

    def test_existing_build_is_preserved_and_never_reconfigured(self):
        self.build.mkdir(parents=True)
        cache = self.build / 'CMakeCache.txt'
        cache.write_text('retired CMake path retained')
        with mock.patch.object(stage, 'ROOT', self.source), mock.patch.object(stage.subprocess, 'run') as run, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            stage.main(['--build-root', str(self.build)])
        run.assert_not_called()
        self.assertEqual(cache.read_text(), 'retired CMake path retained')

    def test_source_and_symlink_destinations_rejected_before_tool_launch(self):
        link = self.base / 'source-link'
        link.symlink_to(self.source, target_is_directory=True)
        for output in (self.source, self.source / 'build', self.base, link / 'build'):
            with self.subTest(output=output), mock.patch.object(stage, 'ROOT', self.source), \
                    mock.patch.object(stage.subprocess, 'run') as run, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                stage.main(['--build-root', str(output)])
            run.assert_not_called()

    def test_vendor_failure_retains_failure_and_prevents_cmake(self):
        def fail_vendor(command, **kwargs):
            result = self.fake_tool(command, **kwargs)
            return subprocess.CompletedProcess(command, 1 if 'verify_vendor.py' in command[-1] else result.returncode)
        rc, report, run = self.build_fixture(fail_vendor)
        self.assertEqual(rc, 1)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(len(run.call_args_list), 3)
        self.assertEqual((self.build / '02.log').read_text(), 'synthetic tool output\n')

    def test_missing_build_artifacts_fail_instead_of_reporting_success(self):
        rc, report, _ = self.build_fixture(lambda command, **kw: subprocess.CompletedProcess(command, 0))
        self.assertEqual(rc, 1)
        self.assertEqual(report['error'], 'missing required build artifacts')

    def test_staged_launch_consumes_bound_binary_and_copies_caches(self):
        self.build_fixture()
        body = 'import sys\nassert "--build-root" not in sys.argv\nassert "--output-dir" not in sys.argv\nprint(' + repr(encode(fixture())) + ')\n'
        rc, report = self.launch(body, binary=self.build / 'steady/openrx-steady')
        self.assertEqual(rc, 0)
        self.assertEqual(report['status'], 'ok')
        self.assertEqual(report['summary']['controls_passed'], 2)
        self.assertTrue(report['summary']['balanced_version_order'])
        self.assertIsNone(report['hashes_per_joule'])
        self.assertNotIn('build_root', report['configuration'])
        self.assertNotIn('binary', report['configuration'])
        self.assertNotIn('output_dir', report['configuration'])
        for name in ('randomx', 'steady'):
            self.assertEqual((self.output / (name + '-CMakeCache.txt')).read_bytes(),
                             (self.build / name / 'CMakeCache.txt').read_bytes())
        self.assertEqual((self.output / 'build.json').read_bytes(), (self.build / 'build.json').read_bytes())
        self.assertFalse((self.source / 'benchmarks/results').exists())

    def test_invalid_bound_artifact_does_not_launch(self):
        self.build_fixture()
        (self.build / 'randomx/librandomx.a').write_text('altered')
        with mock.patch.object(steady.subprocess, 'Popen') as popen:
            rc, report = self.launch()
        self.assertEqual(rc, 1)
        self.assertIn('staged artifact mismatch', report['error'])
        popen.assert_not_called()

    def test_changed_source_does_not_launch(self):
        self.build_fixture()
        (self.source / 'benchmarks/steady/main.cpp').write_text('altered')
        with mock.patch.object(steady.subprocess, 'Popen') as popen:
            rc, report = self.launch()
        self.assertEqual(rc, 1)
        self.assertIn('staged source mismatch', report['error'])
        popen.assert_not_called()

    def test_missing_receipt_is_retained_failure(self):
        self.build_fixture()
        (self.build / 'build.json').unlink()
        rc, report = self.launch()
        self.assertEqual(rc, 1)
        self.assertIn('FileNotFoundError', report['error'])

    def test_malformed_receipt_is_retained_failure(self):
        self.build_fixture()
        (self.build / 'build.json').write_text('[]')
        rc, report = self.launch()
        self.assertEqual(rc, 1)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('invalid native staging receipt', report['error'])

    def test_missing_explicit_binary_is_retained_failure(self):
        with mock.patch.object(steady, 'ROOT', self.source), \
                mock.patch.object(steady, 'capture', return_value={'returncode': 0}), \
                contextlib.redirect_stdout(io.StringIO()):
            rc = steady.main(['--binary', str(self.base / 'missing'), '--output-dir', str(self.output)])
        report = json.loads((self.output / 'run.json').read_text())
        self.assertEqual(rc, 1)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('build first', report['error'])

    def test_reaped_child_is_never_signalled_on_interruption(self):
        self.build_fixture()
        self.launch('print(' + repr(encode(fixture())) + ')\n')
        self.output = self.base / 'interrupted-output'
        process = mock.MagicMock(pid=12345, returncode=None)
        process.__enter__.return_value = process
        def interrupted_wait(**kwargs):
            if kwargs:
                process.returncode = 0  # wait() reaped before raising KeyboardInterrupt.
                raise KeyboardInterrupt
            return 0
        process.wait.side_effect = interrupted_wait
        with mock.patch.object(steady.subprocess, 'Popen', return_value=process), \
                mock.patch.object(steady.os, 'killpg') as kill:
            rc, report = self.launch()
        self.assertEqual(rc, 1)
        self.assertIn('KeyboardInterrupt', report['error'])
        self.assertEqual(report['returncode'], 0)
        kill.assert_not_called()

    def test_staged_duration_rejection_keeps_raw_and_summary(self):
        self.build_fixture()
        rc, report = self.launch('print(' + repr(encode(fixture(minimum=3))) + ')\nraise SystemExit(2)\n', min_seconds=3)
        self.assertEqual(rc, 1)
        self.assertEqual(report['status'], 'rejected-duration')
        self.assertEqual(report['summary']['rejected_measurements'], 4)
        self.assertTrue((self.output / 'adapter.jsonl').read_text())

    def test_output_overlap_and_existing_evidence_are_preserved(self):
        self.output.mkdir(parents=True)
        sentinel = self.output / 'prior-evidence'
        sentinel.write_text('preserve')
        for output in (self.source / 'results', self.build, self.build / 'trial', self.output):
            with self.subTest(output=output), mock.patch.object(steady, 'ROOT', self.source), \
                    mock.patch.object(steady.subprocess, 'Popen') as popen, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                steady.main(['--build-root', str(self.build), '--output-dir', str(output)])
            popen.assert_not_called()
        self.assertEqual(sentinel.read_text(), 'preserve')

    def test_native_controls_route_trials_and_differential_evidence_externally(self):
        self.build_fixture()
        with mock.patch.object(native, 'ROOT', self.source), mock.patch.object(native.steady, 'ROOT', self.source):
            remaining = native.configure(['--build-root', str(self.build), '--output-dir', str(self.output), '-v'])
        self.assertEqual(remaining, ['-v'])
        self.assertEqual(native.BINARY, self.build / 'steady/openrx-steady')
        self.assertEqual(native.UPSTREAM_BINARY, self.build / 'randomx/randomx-benchmark')
        self.assertEqual(native.EVIDENCE, self.output)
        self.assertEqual(native.TRIAL_OUTPUT, self.output)
        self.assertTrue(native.STAGED_BUILD)
        self.assertFalse((self.source / 'build').exists())

    def test_native_controls_reject_unbound_upstream_binary(self):
        self.build_fixture()
        with mock.patch.object(native, 'ROOT', self.source), mock.patch.object(native.steady, 'ROOT', self.source), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            native.configure(['--build-root', str(self.build), '--output-dir', str(self.output),
                              '--upstream-binary', str(self.base / 'different-benchmark')])


if __name__ == '__main__':
    unittest.main()
