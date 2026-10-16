"""Accepted-run attribution requires actual bytes, not embedded hash claims."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.architecture import run

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools/architecture/fixtures/successor-first-iterations"
EVIDENCE = ROOT / "docs/validation/architecture-feasibility-20261016/full-evidence.json"


class AcceptedInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.evidence = self.directory / "full.json"
        shutil.copyfile(EVIDENCE, self.evidence)
        self.fixture = self.directory / "fixture"
        shutil.copytree(FIXTURE, self.fixture)
        self.full = json.loads(self.evidence.read_text())

    def provenance(self):
        return run.provenance(self.full, self.evidence, None, self.fixture)

    def test_exact_preserved_bytes_receive_accepted_attribution(self):
        result = self.provenance()
        bindings = result["input_bindings"]
        self.assertEqual(bindings["identity_status"], "accepted_inputs_verified")
        self.assertTrue(bindings["full_accepted_trace_recognized"])
        self.assertTrue(bindings["bounded_accepted_trace_recognized"])
        self.assertIn("c96e96ab", result["measured_simulation"]["full_workload"])

    def test_mutated_counts_and_timing_with_stale_trace_hash_are_untrusted(self):
        for section, field in (("counts", "bytecode_read8"), ("trace", "total_cycles")):
            with self.subTest(field=field):
                self.full = json.loads(EVIDENCE.read_text())
                old_claim = self.full["trace"]["trace_sha256"]
                self.full[section][field] += 1
                self.evidence.write_text(json.dumps(self.full))
                result = self.provenance()
                self.assertEqual(result["input_bindings"]["full_source_trace_sha256"], old_claim)
                self.assertFalse(result["input_bindings"]["full_accepted_trace_recognized"])
                self.assertTrue(result["measured_simulation"]["full_workload"].startswith("unrecognized"))

    def test_supplied_object_must_match_the_bound_evidence_file(self):
        self.full["counts"]["bytecode_read8"] += 1
        self.assertFalse(self.provenance()["input_bindings"]["full_accepted_trace_recognized"])

    def test_mutated_fixture_timing_and_native_data_keep_no_accepted_attribution(self):
        for filename in ("trace.csv", "native/accesses.hex", "native/iterations.hex", "native/program-0.mem"):
            with self.subTest(filename=filename):
                path = self.fixture / filename
                original = path.read_bytes()
                if filename == "trace.csv":
                    lines = original.decode().splitlines()
                    fields = lines[-1].split(",")
                    fields[0] = str(int(fields[0]) + 1)
                    lines[-1] = ",".join(fields)
                    path.write_text("\n".join(lines) + "\n")
                else:
                    path.write_bytes(original + b"\n")
                result = self.provenance()
                self.assertFalse(result["input_bindings"]["bounded_accepted_trace_recognized"])
                self.assertTrue(result["measured_simulation"]["bounded_workload"].startswith("unrecognized"))
                path.write_bytes(original)

    def test_rehashing_source_map_cannot_rebind_changed_fixture(self):
        path = self.fixture / "trace.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        source_map_path = self.fixture / "source-map.json"
        source_map = json.loads(source_map_path.read_text())
        source_map["source_inputs"]["trace"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        source_map_path.write_text(json.dumps(source_map))
        self.assertEqual(self.provenance()["input_bindings"]["identity_status"], "untrusted_input")

    def test_missing_or_extra_fixture_files_are_not_the_accepted_bundle(self):
        path = self.fixture / "source-map.json"
        original = path.read_bytes()
        path.unlink()
        self.assertFalse(self.provenance()["input_bindings"]["bounded_accepted_trace_recognized"])
        path.write_bytes(original)
        (self.fixture / "unexpected.txt").write_text("not part of the accepted bundle")
        self.assertFalse(self.provenance()["input_bindings"]["bounded_accepted_trace_recognized"])

    def test_cli_preserves_untrusted_provenance_and_stops_before_replay(self):
        self.full["counts"]["bytecode_write8"] += 1
        self.evidence.write_text(json.dumps(self.full))
        output = self.directory / "output"
        argv = ["run", "reproduce", "--fixture", str(self.fixture),
                "--evidence", str(self.evidence), "--output", str(output)]
        with patch("sys.argv", argv), patch.object(run.native_trace, "extract") as extract, \
                patch.object(run, "compare") as compare:
            with self.assertRaisesRegex(ValueError, "untrusted input"):
                run.main()
        extract.assert_not_called()
        compare.assert_not_called()
        self.assertEqual(json.loads((output / "provenance.json").read_text())
                         ["input_bindings"]["identity_status"], "untrusted_input")
        self.assertFalse((output / "comparisons.json").exists())
        self.assertFalse((output / "sensitivity.json").exists())


if __name__ == "__main__":
    unittest.main()
