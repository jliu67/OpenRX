"""Synthetic record/process fixtures test the harness, NOT RandomX performance."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('steady_benchmark', ROOT / 'scripts/steady_benchmark.py')
steady = importlib.util.module_from_spec(spec)
spec.loader.exec_module(steady)


def fixture(warmup=7, repeats=2, minimum=1, nonces=17, versions=None):
    versions = versions or ['v1', 'v2']
    c = dict(type='config', schema_version=1, pid=123, threads=1, init_threads=2,
             nonces=nonces, warmup_nonces=warmup, repeats=repeats, min_seconds=minimum,
             aes='hardware', flags=14, seed=0, versions=versions,
             scheduler='static-stride-batch-first-next-last', power_watts=None,
             monotonic_resolution_ns=1, realtime_resolution_ns=1)
    plan = [('control', v, 0, 1000) for v in versions]
    for r in range(1, repeats + 1):
        for v in versions if r % 2 else list(reversed(versions)):
            if warmup:
                plan.append(('warmup', v, r, warmup))
            plan.append(('measurement', v, r, nonces))
    result, mono, rejected = [c], 10**12, 0
    for index, (phase, version, repeat, count) in enumerate(plan, 1):
        start = dict(mono_before_ns=mono, unix_ns=mono + 10**18, mono_after_ns=mono+10)
        mono += 2000000010
        end = dict(mono_before_ns=mono, unix_ns=mono + 10**18, mono_after_ns=mono+10)
        short = phase == 'measurement' and 2 < minimum
        rejected += int(short)
        result.append(dict(type='interval', sequence=index, phase=phase, version=version,
                           repeat=repeat, hashes=count, digest=steady.REFERENCES[version] if count == 1000
                           else ('a' if version == 'v1' else 'b') * 64,
                           reference_matches=True if count == 1000 else None,
                           status='too-short' if short else 'ok', start=start, end=end, elapsed_ns=2000000000))
        mono += 100
    result.append(dict(type='complete', intervals=len(plan), invalid_intervals=rejected))
    return result


def encode(records):
    return '\n'.join(json.dumps(r) for r in records) + '\n'


class RecordTests(unittest.TestCase):
    def rejected(self, change):
        records = fixture()
        change(records)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            steady.validate(encode(records))

    def test_valid_summary_excludes_controls_and_warmups(self):
        out = steady.validate(encode(fixture()))
        self.assertTrue(out['accepted'])
        self.assertEqual(out['measurements']['v1']['accepted'], 2)
        self.assertEqual(out['measurements']['v1']['median_hps'], 8.5)  # SYNTHETIC
        self.assertIsNone(out['hashes_per_joule'])
        self.assertFalse(out['wall_clock_alignment_verified'])

    def test_zero_warmup_and_single_version(self):
        self.assertTrue(steady.validate(encode(fixture(warmup=0, versions=['v2'])))['accepted'])

    def test_odd_order_flag(self):
        self.assertFalse(steady.validate(encode(fixture(repeats=3)))['balanced_version_order'])

    def test_reversed_version_order(self):
        self.assertTrue(steady.validate(encode(fixture(versions=['v2', 'v1'])))['accepted'])

    def test_duration_rejection_is_preserved(self):
        summary = steady.validate(encode(fixture(minimum=3)))
        self.assertEqual(summary['expected_returncode'], 2)
        self.assertEqual(summary['rejected_measurements'], 4)
        self.assertIsNone(summary['measurements']['v1']['median_hps'])

    def test_known_controls_independent_of_claimed_match(self):
        self.rejected(lambda r: r[1].update(digest='f' * 64))
        self.rejected(lambda r: r[1].update(reference_matches=False))

    def test_reference_applies_to_all_1000_nonce_phases(self):
        r = fixture(warmup=1000, nonces=1000)
        self.assertTrue(steady.validate(encode(r))['accepted'])
        r[3]['digest'] = 'f' * 64
        with self.assertRaises(ValueError):
            steady.validate(encode(r))

    def test_unknown_reference_cannot_be_invented(self):
        self.rejected(lambda r: r[3].update(reference_matches=True))

    def test_truncation_extra_records_and_duplicates(self):
        for change in (lambda r: r.pop(), lambda r: r.pop(3),
                       lambda r: r.insert(3, copy.deepcopy(r[3]))):
            self.rejected(change)

    def test_wrong_order_version_count_and_boolean_count(self):
        for change in (dict(sequence=9), dict(version='v3'), dict(phase='measurement'),
                       dict(hashes=999), dict(hashes=True), dict(repeat=True)):
            self.rejected(lambda r, c=change: r[1].update(c))

    def test_strict_json(self):
        for text in ('{}\n', encode(fixture()).replace('"pid": 123', '"pid": 123, "pid": 124'),
                     encode(fixture()).replace('"min_seconds": 1', '"min_seconds": NaN')):
            with self.assertRaises(ValueError):
                steady.validate(text)

    def test_configuration_binding(self):
        with self.assertRaises(ValueError):
            steady.validate(encode(fixture()), {'threads': 2})
        self.assertTrue(steady.validate(encode(fixture()), {'threads': 1})['accepted'])

    def test_unsupported_configuration(self):
        for change in (dict(seed=1), dict(flags=12), dict(aes='auto'), dict(threads=0),
                       dict(min_seconds=-1), dict(schema_version=True), dict(scheduler='unknown'), dict(power_watts=100),
                       dict(versions=['v1', 'v1'])):
            self.rejected(lambda r, c=change: r[0].update(c))

    def test_clock_brackets_and_elapsed(self):
        self.rejected(lambda r: r[1]['start'].update(mono_after_ns=1))
        self.rejected(lambda r: r[1].update(elapsed_ns=1))
        self.rejected(lambda r: r[2]['start'].update(mono_before_ns=2))
        self.rejected(lambda r: r[1]['start'].update(unix_ns=True))

    def test_clock_jump_is_reported_not_called_calibrated(self):
        r = fixture(); r[1]['end']['unix_ns'] += 10**9
        out = steady.validate(encode(r))
        self.assertEqual(out['max_abs_clock_delta_ns'], 10**9)
        self.assertFalse(out['wall_clock_alignment_verified'])

    def test_repeated_inputs_must_be_deterministic(self):
        self.rejected(lambda r: r[8].update(digest='f' * 64))

    def test_completion_and_quality_must_agree(self):
        self.rejected(lambda r: r[-1].update(intervals=999))
        self.rejected(lambda r: r[-1].update(invalid_intervals=1))
        self.rejected(lambda r: r[4].update(status='too-short'))


class ProcessTests(unittest.TestCase):
    def run_fixture(self, body, minimum=1, timeout=5):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); binary = root / 'build/steady/openrx-steady'
            binary.parent.mkdir(parents=True)
            binary.write_text('#!/usr/bin/env python3\n' + body)
            binary.chmod(0o755)
            argv = ['steady', '--nonces', '17', '--warmup-nonces', '7', '--repeats', '2',
                    '--timeout', str(timeout), '--min-seconds', str(minimum)]
            with mock.patch.object(steady, 'ROOT', root), mock.patch.object(steady.sys, 'argv', argv), \
                    mock.patch.object(steady, 'capture', return_value={'returncode': 0}), \
                    contextlib.redirect_stdout(io.StringIO()):
                rc = steady.main()
            reports = list((root / 'benchmarks/results').glob('*/run.json'))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text())
            self.assertIn('adapter.jsonl', report['raw_sha256'])
            return rc, report

    def test_success_and_evidence(self):
        rc, report = self.run_fixture('print(' + repr(encode(fixture())) + ')\n')
        self.assertEqual(rc, 0)
        self.assertEqual(report['status'], 'ok')
        self.assertIn('binary_sha256', report)
        self.assertIn('resources_after', report)

    def test_nonzero_exit_is_not_success(self):
        rc, report = self.run_fixture('print(' + repr(encode(fixture())) + ')\nraise SystemExit(9)\n')
        self.assertEqual(rc, 1)
        self.assertEqual(report['returncode'], 9)

    def test_timeout_is_retained(self):
        rc, report = self.run_fixture('import time\ntime.sleep(5)\n', timeout=1)
        self.assertEqual(rc, 1)
        self.assertIn('TimeoutExpired', report['error'])
        self.assertEqual(report['returncode'], -9)

    def test_malformed_output_is_retained(self):
        rc, report = self.run_fixture('print("not json")\n')
        self.assertEqual(rc, 1)
        self.assertEqual(report['status'], 'failed')

    def test_duration_failure_keeps_structured_result(self):
        rc, report = self.run_fixture('print(' + repr(encode(fixture(minimum=3))) + ')\nraise SystemExit(2)\n', minimum=3)
        self.assertEqual(rc, 1)
        self.assertEqual(report['status'], 'rejected-duration')


if __name__ == '__main__':
    unittest.main()
