"""Actual accepted short native/RTL input, without host-only data or simulation."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.architecture import native_trace
from tools.architecture.run import compare, provenance

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools/architecture/fixtures/successor-first-iterations"


class PortableTraceTests(unittest.TestCase):
    def test_actual_windows_match_native_routes_and_memory_addresses(self):
        trace = native_trace.extract(FIXTURE / "trace.csv", FIXTURE / "native",
                                    max_iterations=8, first_iteration_per_program=True)
        self.assertEqual(trace["operation_count"], 3081)
        self.assertEqual([w["program"] for w in trace["windows"]], list(range(8)))
        self.assertTrue(all(i["route_verified"] and i["memory_addresses_verified"] for i in trace["iterations"]))
        self.assertEqual({op["unit"] for op in trace["operations"]},
                         {"integer", "float", "multiply", "control", "divsqrt"})

    def test_cli_comparison_contract_does_not_promote_windows_to_hashes(self):
        small = {"windows": [{"program": 0, "iteration": 0, "operations": [
            {"unit": "integer", "writes": ["r0"], "latency": 5},
            {"unit": "integer", "reads": ["r0"], "latency": 1}]}]}
        output = compare(small)
        self.assertIsNone(output["full_hash_cycles"])
        self.assertIsNone(output["hashes_per_second"])
        self.assertFalse(output["demonstrated_asic_performance"])
        scalar = next(r for r in output["results"] if r["configuration"] == "single_issue_blocking")
        self.assertEqual(scalar["cycles"], 6)
        self.assertEqual(len(output["results"]), 61)

    def test_unknown_evidence_never_gets_accepted_workload_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "unrecognized.json"
            p.write_text(json.dumps({"trace": {"trace_sha256": "wrong"}}))
            result = provenance(json.loads(p.read_text()), p, {}, FIXTURE)
            self.assertFalse(result["input_bindings"]["full_accepted_trace_recognized"])
            self.assertTrue(result["measured_simulation"]["full_workload"].startswith("unrecognized"))


if __name__ == "__main__":
    unittest.main()
