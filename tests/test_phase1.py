"""Tooling regression tests. Fake benchmark outputs are NOT mining evidence."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench = load('benchmark')
workload = load('workload_profile')


def output(version='v1', value='100', unit='hashes per second', reference=True):
    digest = bench.REFERENCES[version]
    return (f'Calculated result: {digest}\n'
            + (f'Reference result: {digest}\n' if reference else '')
            + f'Performance: {value} {unit}\n')


class OutputTests(unittest.TestCase):
    def parse(self, raw, **kwargs):
        options = dict(mode='mine', version='v1', nonces=1000, seed=0)
        options.update(kwargs)
        return bench.parse_output(raw, **options)

    def test_both_known_references(self):
        for version in ('v1', 'v2'):
            with self.subTest(version=version):
                result = self.parse(output(version), version=version)
                self.assertEqual([], result['validation_errors'])
                self.assertTrue(result['known_reference_matches'])
                self.assertEqual(10, result['hashing_seconds_approx'])

    def test_missing_calculated(self):
        self.assertTrue(self.parse('Performance: 100 hashes per second\n')['validation_errors'])

    def test_duplicate_calculated(self):
        self.assertTrue(self.parse(output() + 'Calculated result: ' + bench.REFERENCES['v1'])['validation_errors'])

    def test_missing_performance(self):
        self.assertTrue(self.parse('Calculated result: ' + bench.REFERENCES['v1'])['validation_errors'])

    def test_duplicate_performance(self):
        self.assertTrue(self.parse(output() + 'Performance: 200 hashes per second\n')['validation_errors'])

    def test_missing_known_reference(self):
        self.assertTrue(self.parse(output(reference=False))['validation_errors'])

    def test_both_printed_hashes_wrong(self):
        self.assertTrue(self.parse(output().replace(bench.REFERENCES['v1'], '0' * 64))['validation_errors'])

    def test_nonreference_smoke_allowed_but_not_verified(self):
        result = self.parse(output(reference=False), nonces=2)
        self.assertEqual([], result['validation_errors'])
        self.assertIsNone(result['known_reference_matches'])

    def test_printed_reference_mismatch(self):
        raw = output().replace('Reference result: ' + bench.REFERENCES['v1'], 'Reference result: ' + '0' * 64)
        self.assertTrue(self.parse(raw, nonces=2)['validation_errors'])

    def test_reject_invalid_rates(self):
        for value in ('0', '-1', 'nan', 'inf', '1e999', 'garbage'):
            with self.subTest(value=value):
                self.assertTrue(self.parse(output(value=value))['validation_errors'])

    def test_reject_overflowing_interval(self):
        self.assertTrue(self.parse(output(value='5e-324'))['validation_errors'])

    def test_scientific_notation(self):
        self.assertEqual(125, self.parse(output(value='1.25e2'))['performance_value'])

    def test_wrong_units(self):
        self.assertTrue(self.parse(output(unit='ms per hash'))['validation_errors'])

    def test_light_mode_interval(self):
        result = self.parse(output(value='5', unit='ms per hash'), mode='verify')
        self.assertEqual([], result['validation_errors'])
        self.assertEqual(5, result['hashing_seconds_approx'])

    def test_reported_upstream_errors(self):
        for message in ('ERROR: Cannot create VM', 'Failed to set thread affinity for thread 0'):
            with self.subTest(message=message):
                self.assertTrue(self.parse(output() + message)['validation_errors'])

    def test_duplicate_reference(self):
        self.assertTrue(self.parse(output() + 'Reference result: ' + bench.REFERENCES['v1'])['validation_errors'])


class ArgumentTests(unittest.TestCase):
    def reject(self, argv):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            bench.parse_args(argv)
        self.assertEqual(2, exc.exception.code)

    def test_defaults(self):
        args = bench.parse_args([])
        self.assertEqual(0, args.warmups)
        self.assertEqual(3, args.repeats)

    def test_bounded_upstream_integer_options(self):
        for option in ('--threads', '--init-threads', '--nonces', '--seed'):
            with self.subTest(option=option):
                self.reject([option, str(1 << 31)])

    def test_negative_seed(self):
        self.reject(['--seed', '-1'])

    def test_zero_threads(self):
        self.reject(['--threads', '0'])

    def test_negative_warmups(self):
        self.reject(['--warmups', '-1'])

    def test_invalid_min_duration(self):
        for value in ('nan', 'inf', '-1'):
            self.reject(['--min-run-seconds', value])

    def test_duplicate_versions(self):
        self.reject(['--versions', 'v1', 'v1'])

    def test_verify_requires_one_thread(self):
        self.reject(['--mode', 'verify', '--threads', '2'])

    def test_single_thread_upstream_affinity_ignored(self):
        self.reject(['--affinity', '1'])

    def test_affinity_bounds(self):
        for value in ('0', str(1 << 64)):
            self.reject(['--threads', '2', '--affinity', value])

    def test_affinity_needs_enough_cpus(self):
        self.reject(['--threads', '2', '--affinity', '1'])

    def test_affinity_checks_process_cpu_set(self):
        with patch.object(bench.os, 'sched_getaffinity', return_value={0, 1}):
            self.assertEqual(3, bench.parse_args(['--threads', '2', '--affinity', '3']).affinity)
            self.reject(['--threads', '2', '--affinity', '6'])

    def test_nonce_count_must_cover_threads(self):
        self.reject(['--threads', '4', '--nonces', '2'])


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configuration = ROOT / 'vendor/randomx/src/configuration.h'
        cls.content = cls.configuration.read_text()

    def test_exact_source_blob(self):
        self.assertEqual('aac8914e0e8a52319600169bcc64b6cd9c967565',
                         workload.profile(self.configuration)['configuration_git_blob_sha1'])

    def test_expected_static_work(self):
        result = workload.analyze(self.content)
        self.assertEqual({'v1': 4194304, 'v2': 6291456}, result['nominal_vm_slots_per_hash'])
        self.assertEqual(2181038016, result['dataset_bytes'])
        self.assertEqual(268435456, result['cache_bytes'])
        self.assertEqual(256, sum(result['opcode_groups_per_256'].values()))
        self.assertEqual(94, result['opcode_groups_per_256']['floating_point'])

    def test_committed_snapshot(self):
        expected = json.loads((ROOT / 'benchmarks/profiles/pinned-v2.0.1.json').read_text())
        self.assertEqual(expected, workload.profile(self.configuration))

    def test_missing_macro(self):
        with self.assertRaises(ValueError):
            workload.analyze(self.content.replace('RANDOMX_PROGRAM_COUNT', 'IGNORED_PROGRAM_COUNT'))

    def test_duplicate_macro(self):
        with self.assertRaises(ValueError):
            workload.analyze(self.content + '\n#define RANDOMX_PROGRAM_COUNT 8\n')

    def test_expression_not_silently_evaluated(self):
        with self.assertRaises(ValueError):
            workload.analyze(self.content.replace('RANDOMX_PROGRAM_COUNT      8', 'RANDOMX_PROGRAM_COUNT (4*2)'))

    def test_invalid_frequency_total(self):
        with self.assertRaises(ValueError):
            workload.analyze(self.content.replace('RANDOMX_FREQ_NOP            0', 'RANDOMX_FREQ_NOP 1'))

    def test_unknown_opcode_rejected(self):
        with self.assertRaises(ValueError):
            workload.analyze(self.content.replace('RANDOMX_FREQ_NOP', 'RANDOMX_FREQ_UNCLASSIFIED'))

    def test_invalid_scratchpad_size(self):
        with self.assertRaises(ValueError):
            workload.analyze(self.content.replace('RANDOMX_SCRATCHPAD_L1      16384', 'RANDOMX_SCRATCHPAD_L1 16000'))


class RunnerIntegrationTests(unittest.TestCase):
    """Temporary fixture scripts, not a RandomX implementation or vendor check."""
    def run_fixture(self, options, suffix=''):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ('scripts', 'vendor', 'build/randomx'):
                (root / directory).mkdir(parents=True)
            (root / 'scripts/verify_vendor.py').write_text('# synthetic fixture only\n')
            (root / 'vendor/randomx.lock.json').write_text('{"synthetic_fixture": true}')
            binary = root / 'build/randomx/randomx-benchmark'
            binary.write_text(f'#!{sys.executable}\nimport sys, time\n'
                              "v = 'v2' if '--v2' in sys.argv else 'v1'\n"
                              f'digest = {bench.REFERENCES!r}[v]\n'
                              "print('Calculated result: ' + digest)\n"
                              "print('Reference result: ' + digest)\n"
                              "print('Performance: 100 hashes per second', flush=True)\n" + suffix)
            binary.chmod(0o755)
            with patch.object(bench, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                code = bench.main(options)
            report_path, = (root / 'benchmarks/results').glob('*/results.json')
            report = json.loads(report_path.read_text())
            self.assertTrue(all((report_path.parent / run['log']).exists() for run in report['runs']))
            return code, report

    def test_warmups_separated_and_versions_alternate(self):
        code, report = self.run_fixture(['--nonces', '1000', '--warmups', '1', '--repeats', '2'])
        self.assertEqual(0, code)
        self.assertEqual(['v1', 'v2', 'v1', 'v2', 'v2', 'v1'], [r['version'] for r in report['runs']])
        self.assertEqual(6, len(report['runs']))
        self.assertEqual(2, report['summary']['v1']['measured_runs'])
        self.assertEqual(100, report['summary']['v2']['median'])
        self.assertIsNone(report['power_watts'])
        self.assertIsNone(report['hashes_per_joule'])

    def test_too_short_measurement_rejected(self):
        code, report = self.run_fixture(['--versions', 'v1', '--repeats', '1', '--min-run-seconds', '11'])
        self.assertEqual(1, code)
        self.assertEqual('too-short', report['runs'][0]['status'])
        self.assertEqual(0, report['summary']['v1']['valid_runs'])
        self.assertIsNone(report['summary']['v1']['median'])

    def test_nonzero_exit_retained(self):
        code, report = self.run_fixture(['--versions', 'v1', '--repeats', '1'], 'sys.exit(9)\n')
        self.assertEqual(1, code)
        self.assertEqual(9, report['runs'][0]['returncode'])
        self.assertEqual('failed', report['runs'][0]['status'])

    def test_timeout_retained(self):
        code, report = self.run_fixture(['--versions', 'v1', '--repeats', '1', '--timeout', '1'], 'time.sleep(3)\n')
        self.assertEqual(1, code)
        self.assertEqual('timeout', report['runs'][0]['status'])


if __name__ == '__main__':
    unittest.main()
