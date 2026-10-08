"""Reject misleading, incomplete or modified runtime evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_runtime_probe', ROOT / 'tests/native_runtime_probe.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / 'docs/validation/m3-fs/runtime-native.jsonl').read_text()
        cls.rows = [json.loads(x) for x in cls.raw.splitlines()]

    def reject(self, change):
        rows = copy.deepcopy(self.rows)
        change(rows)
        with self.assertRaises(ValueError):
            runtime.validate_output('\n'.join(json.dumps(x) for x in rows))

    def test_actual_native_capture(self):
        self.assertEqual(runtime.validate_output(self.raw)['checks_passed'], 9)

    def test_native_capture_not_riscv(self):
        with self.assertRaises(ValueError):
            runtime.validate_output(self.raw, expect_architecture='riscv64')

    def test_missing_or_duplicate_control(self):
        self.reject(lambda rows: rows.pop(3))
        self.reject(lambda rows: rows.__setitem__(3, rows[2]))

    def test_self_consistent_wrong_return(self):
        self.reject(lambda rows: rows[4].update(actual=99, expected=99))

    def test_ignored_flush_failure(self):
        self.reject(lambda rows: rows[3].update(actual=-1, status='pass'))

    def test_wrong_protection_signal(self):
        self.reject(lambda rows: rows[2].update(actual=0, expected=0))

    def test_fabricated_flush_path(self):
        self.reject(lambda rows: rows[0].update(flush_path='linux-riscv-flush-icache'))

    def test_boolean_counter_and_extra_record(self):
        self.reject(lambda rows: rows[-1].update(checks=True))
        self.reject(lambda rows: rows.append(rows[-1]))

    def test_duplicate_json_field(self):
        with self.assertRaises(ValueError):
            runtime.validate_output(self.raw.replace('"checks":9', '"checks":9,"checks":9'))
