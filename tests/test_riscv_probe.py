"""Evidence-validator regressions using an actual native probe capture.

Mutations test rejection behavior; these fixtures are not RISC-V measurements.
"""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("native_riscv_probe", ROOT / "tests/native_riscv_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / "docs/validation/m3/local-native.jsonl").read_text()
        cls.records = [json.loads(line) for line in cls.raw.splitlines()]

    def mutated(self, change):
        rows = copy.deepcopy(self.records)
        change(rows)
        return "\n".join(json.dumps(x) for x in rows) + "\n"

    def rejected(self, change):
        with self.assertRaises(ValueError):
            probe.validate_output(self.mutated(change))

    def test_actual_native_capture(self):
        self.assertEqual(probe.validate_output(self.raw)["software_hash_cases"], 8)

    def test_native_is_not_riscv_evidence(self):
        with self.assertRaises(ValueError):
            probe.validate_output(self.raw, expect_riscv=True)

    def test_missing_summary(self):
        self.rejected(lambda rows: rows.pop())

    def test_truncated_hash_matrix(self):
        self.rejected(lambda rows: rows.pop(-3))

    def test_duplicate_check(self):
        self.rejected(lambda rows: rows.insert(2, copy.deepcopy(rows[1])))

    def test_self_consistent_wrong_semantic_value(self):
        def wrong(rows):
            rows[1]["expected"] = rows[1]["actual"] = "ffffffffffffffff"
        self.rejected(wrong)

    def test_semantic_check_replacement(self):
        self.rejected(lambda rows: rows[1].update(name="integer/unverified"))

    def test_self_consistent_wrong_hash(self):
        def wrong(rows):
            row = next(x for x in rows if x.get("algorithm"))
            row["expected"] = row["actual"] = "0" * 64
        self.rejected(wrong)

    def test_mislabeled_full_dataset_flags(self):
        def wrong(rows):
            row = next(x for x in rows if x.get("algorithm"))
            row["vm_flags"] |= 4
        self.rejected(wrong)

    def test_pinned_configuration_identity(self):
        for field, value in (("key", "other key"), ("vendor_revision", "0" * 40),
                             ("cache_size_bytes", 1), ("key_bytes", 13)):
            with self.subTest(field=field):
                self.rejected(lambda rows: rows[0].update({field: value}))

    def test_skipped_required_check(self):
        self.rejected(lambda rows: rows[1].update(status="skip"))

    def test_wrong_required_passed_total(self):
        self.rejected(lambda rows: rows[-1].update(required_passed=38))

    def test_missing_cache_initialization(self):
        self.rejected(lambda rows: rows.remove(next(x for x in rows if x.get("type") == "stage")))

    def test_non_object_record(self):
        self.rejected(lambda rows: rows.insert(2, []))

    def test_malformed_check_name(self):
        self.rejected(lambda rows: rows[1].update(name=[]))

    def test_unknown_optional_skip(self):
        self.rejected(lambda rows: rows[-2].update(name="unknown-optional"))

    def test_boolean_counter(self):
        self.rejected(lambda rows: rows[-1].update(failures=False))


if __name__ == "__main__":
    unittest.main()
