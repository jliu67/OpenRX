"""Evidence parsing rejects invented spans, traffic and fitted stage clocks."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "architecture"))
import evidence


class TraceTests(unittest.TestCase):
    def trace(self, rows):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "trace.csv"
        path.write_text(evidence.HEADER + "\n" + "\n".join(rows) + "\n")
        return path

    def test_sparse_durations_and_one_shot_transaction_flags(self):
        path = self.trace([
            "0,3,0,0,0,0,0,0,0,0,ffff,0,0",
            "2,4,0,0,0,0,0,0,0,0,ffff,0,0",
            "3,4,7,1,0,0,0,0,0,0,ffff,0,0",
            "7,4,7,1,1,0,1,10,0,0,ffff,0,0",
            "12,4,8,0,0,0,0,0,1,20,ff,1,40",
            "13,8,0,0,0,0,0,0,0,0,ffff,0,0"])
        result = evidence.stream_trace(path, 14, [[0]])
        self.assertEqual(result["stage_cycles"]["execution"], 11)
        self.assertEqual(result["nested_iteration_phases"][7], 9)
        self.assertEqual(result["events"]["scratchpad_reads16"], 1)
        self.assertEqual(result["events"]["scratchpad_strobed_write_bytes"], 8)
        self.assertEqual(result["events"]["dataset_requests64"], 1)
        self.assertEqual(result["instruction_families"], {"IADD_RS": 1})
        self.assertEqual(result["trace_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        # The CSV can skip EXEC, MUL_WAIT and DIV_WAIT entirely. Clock spans
        # for its sampled executor-state column must remain unavailable.
        self.assertIsNone(result["executor_state_durations"])
        self.assertNotIn("nested_executor_phases", result)

    def test_duplicate_or_out_of_range_timestamp_rejected(self):
        for cycles, total in (([0, 0], 1), ([0, 2], 2), ([1, 2], 3)):
            path = self.trace([f"{cycle},1,0,0,0,0,0,0,0,0,ffff,0,0" for cycle in cycles])
            with self.subTest(cycles=cycles), self.assertRaises(ValueError):
                evidence.stream_trace(path, total, [])

    def test_invalid_event_phase_pc_and_strobes_rejected(self):
        for row in ("0,7,0,0,0,0,0,0,0,0,ffff,0,0",
                    "0,3,0,0,2,0,0,0,0,0,ffff,0,0",
                    "0,3,0,0,1,1,0,0,0,0,ffff,0,0",
                    "0,3,0,0,0,0,0,0,0,0,10000,0,0"):
            with self.subTest(row=row), self.assertRaises(ValueError):
                evidence.stream_trace(self.trace([row]), 1, [[0]])

    def test_output_cannot_overwrite_previous_sample(self):
        path = self.trace(["0,1,0,0,0,0,0,0,0,0,ffff,0,0"])
        with self.assertRaises(FileExistsError):
            evidence.stream_trace(path, 1, [], sample_trace_output=path)


class NativeLocalityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        (self.directory / "accesses.hex").write_text("8 ff\n240000 aa\n")
        # program, iteration, event offset/count, retired steps, R/F/E/A,
        # rounding/mx/ma/sp0/sp1, actual outer addresses, dataset/prefetch, route.
        (self.directory / "iterations.hex").write_text("0 0 0 2 4 0 0 0 0 0 0 0 0 0 0 100000 40 80 0\n")

    def test_real_address_prefixes_and_dataset_are_separate(self):
        result = evidence.extract_native_locality(self.directory)
        self.assertEqual(result["counts"], {"bytecode_read8": 1, "bytecode_write8": 1,
                                            "outer_read64": 2, "outer_write64": 2})
        self.assertEqual(result["dataset_bytes_per_hash"], 64)
        cold = result["prefixes"][0]["cold_counts"]
        self.assertEqual(cold["bytecode_write8"], 1)
        self.assertEqual(cold["outer_read64"], 1)
        self.assertEqual(result["prefixes"][-1]["cold_counts"], dict.fromkeys(result["counts"], 0))

    def test_unaligned_or_invalid_native_address_rejected(self):
        for token in ("1", "400000"):
            (self.directory / "accesses.hex").write_text(token + " ff\n")
            with self.subTest(token=token), self.assertRaises(ValueError):
                evidence.extract_native_locality(self.directory)


class EquationTests(unittest.TestCase):
    def test_retained_full_hash_fixed_stages_close_without_fitting(self):
        fixture = json.loads((ROOT / "tools/architecture/fixtures/accepted_full_v2.json").read_text())
        trace = {"instruction_families": {}, "active_reciprocal_commits": 0,
                 "nested_iteration_phases": fixture["nested_iteration_phases"],
                 "stage_cycles": fixture["stage_cycles"], "total_cycles": fixture["cycles"]}
        result = evidence.source_cycle_equations(trace, 8, 16384, 92)
        self.assertEqual(result["total_cycle_residual"], 0)
        self.assertFalse(any(result["stage_cycle_residuals"].values()))
        self.assertFalse(any(result["iteration_phase_residuals"]))
        self.assertEqual(sum(result["iteration_nonexecutor_cycles_per_iteration"].values()), 30)
        self.assertEqual(result["measured_unpredicted_inputs"], {"executor_EX_WAIT_aggregate_cycles": 39946977})
        self.assertIsNone(result["executor_phase_residuals"])
        self.assertEqual(result["unexplained_fitted_cycles"], 0)

    def test_fixed_stage_error_is_visible_not_absorbed(self):
        trace = {"instruction_families": {}, "active_reciprocal_commits": 0,
                 "nested_iteration_phases": [0] * 12,
                 "stage_cycles": dict.fromkeys(evidence.STAGES.values(), 0), "total_cycles": 0}
        first = evidence.source_cycle_equations(trace, 1, 1, 0)
        trace["stage_cycles"]["program_preparation"] = first["expected_stage_cycles"]["program_preparation"] + 1
        second = evidence.source_cycle_equations(trace, 1, 1, 0)
        self.assertEqual(second["stage_cycle_residuals"]["program_preparation"], 1)

    def test_opcode_boundaries_and_reciprocal_nops(self):
        self.assertEqual(evidence.family(15), "IADD_RS")
        self.assertEqual(evidence.family(16), "IADD_M")
        self.assertEqual(evidence.family(255), "ISTORE")
        self.assertFalse(evidence.active_reciprocal((8 << 32) | 76))
        self.assertTrue(evidence.active_reciprocal((3 << 32) | 76))


class EndToEndEvidenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.native = self.directory / "native"
        self.native.mkdir()
        (self.native / "program-0.mem").write_text("0000000000000000\n")
        (self.native / "accesses.hex").write_text("")
        (self.native / "iterations.hex").write_text("0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 40 0 40 0\n")
        rows = [(0, 1, 0, 0, 0), (131074, 2, 0, 0, 0), (131080, 3, 0, 0, 0),
                (131084, 4, 0, 0, 0), (131085, 4, 1, 0, 0), (131089, 4, 2, 0, 0),
                (131093, 4, 3, 0, 0), (131097, 4, 4, 0, 0), (131101, 4, 6, 0, 0),
                (131102, 4, 7, 1, 0), (131105, 4, 7, 8, 1), (131106, 4, 8, 0, 0),
                (131107, 4, 9, 0, 0), (131108, 4, 10, 0, 0), (131109, 4, 11, 0, 0),
                (131118, 5, 0, 0, 0), (131119, 6, 0, 0, 0), (524405, 8, 0, 0, 0)]
        self.trace = self.directory / "trace.csv"
        self.trace.write_text(evidence.HEADER + "\n" + "\n".join(
            f"{cycle},{outer},{iteration},{execute},{commit},0,0,0,0,0,ffff,{int(iteration == 8 and outer == 4)},0"
            for cycle, outer, iteration, execute, commit in rows) + "\n")
        self.summary = {"status": "pass_connected_native_reference", "programs": 1,
                        "native_reference": {"total_iterations": 1, "instruction_steps": 1, "bytecode_events": 0},
                        "profiles": {"prepared-ideal": {
                            "trace_sha256": evidence.sha256_file(self.trace),
                            "host_provider": {"provider_device_cycles": None},
                            "ledger": {"cycles": 524406,
                                       "stage_cycles": {"initialization_transport": 131074, "control_and_metadata": 6,
                                                        "program_preparation": 4, "execution": 34, "interprogram_seed": 1,
                                                        "finalization": 393286, "held_return": 1},
                                       "nested_iteration_phases": [1, 4, 4, 4, 4, 0, 1, 4, 1, 1, 1, 9],
                                       "nested_executor_phases": [0, 1, 1, 1, 0, 0, 0, 0, 1] + [0] * 9,
                                       "untimed_provider_device_cycles": None,
                                       "physical_port_read_bytes": 0, "physical_port_write_bus_bytes": 0,
                                       "strobed_write_bytes": 0, "dataset_logical_bytes": 64,
                                       "preparation_reciprocals": 0}}}}
        self.summary_path = self.directory / "summary.json"

    def run_extract(self):
        self.summary_path.write_text(json.dumps(self.summary))
        return evidence.extract_evidence(self.summary_path, self.trace, self.native)

    def test_richer_ledger_does_not_invent_executor_trace_coverage(self):
        report = self.run_extract()
        self.assertEqual(report["calibration"]["total_cycle_residual"], 0)
        self.assertIsNone(report["trace"]["executor_state_durations"])

    def test_unknown_host_provider_device_cycles_remain_unknown(self):
        self.summary["profiles"]["prepared-ideal"]["host_provider"]["provider_device_cycles"] = 1
        with self.assertRaisesRegex(ValueError, "invented device clocks"):
            self.run_extract()

    def test_summary_trace_digest_is_binding(self):
        self.summary["profiles"]["prepared-ideal"]["trace_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "trace SHA256"):
            self.run_extract()


if __name__ == "__main__":
    unittest.main()
