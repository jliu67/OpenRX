"""Contracts for the separately bound accepted hardware-dataset service profile."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.architecture import hardware_dataset as model


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tools/architecture/fixtures/accepted_hardware_dataset_v2.json"


class HardwareDatasetProfileTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())

    def test_exact_fixture_binds_actual_bytes_and_keeps_clock_domains_separate(self):
        report = model.build_report(FIXTURE)
        self.assertEqual(report["provenance"]["identity_status"], "accepted_input_verified")
        self.assertEqual(report["provenance"]["actual_input_sha256"], hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(report["provenance"]["accepted_source"], model.ACCEPTED_SOURCE)
        clocks = report["modeled_clock_ledger"]
        self.assertEqual(clocks["outer_baseline_cycles"], 918672902)
        self.assertEqual(clocks["vm_executor_nested_cycles"], 42731239)
        self.assertEqual(clocks["dataset_executor_nested_cycles"], 873676800)
        self.assertEqual(clocks["dataset_availability_nested_cycles"], 874905600)
        self.assertFalse(clocks["dataset_costs_added_to_outer_twice"])
        self.assertEqual(sum(clocks["stage_cycles"].values()), clocks["outer_baseline_cycles"])

    def test_distinct_interfaces_do_not_become_aggregate_offchip_traffic(self):
        report = model.build_report(FIXTURE)
        expected = {
            "vm_dataset_response": (16384, 1048576),
            "prepared_cache_response": (131072, 8388608),
            "prepared_instruction_response": (58376192, 467009536),
        }
        for name, (requests, payload) in expected.items():
            with self.subTest(interface=name):
                row = report["interfaces"][name]
                self.assertEqual(row["responses_per_hash"], requests)
                self.assertEqual(row["minimum_data_payload_bytes_per_hash"], payload)
                self.assertEqual(row["required_responses_per_second_at_target"], requests * 1000000)
                self.assertEqual(row["minimum_data_payload_bytes_per_second_at_target"], payload * 1000000)
                self.assertIsNone(row["physical_offchip_bytes_per_hash"])
                self.assertIsNone(row["wire_bytes_per_hash"])
                self.assertIsNone(row["characterized_service_latency_seconds"])
                self.assertIsNone(row["characterized_sustainable_responses_per_second"])
        self.assertIsNone(report["aggregate_physical_offchip_bytes_per_hash"])
        self.assertTrue(report["independent_link_payloads_must_not_be_summed_as_offchip_traffic"])
        reciprocal = report["reciprocal_transport"]
        self.assertFalse(reciprocal["separate_logical_request_interface"])
        self.assertIsNone(reciprocal["independent_physical_transactions_per_hash"])
        self.assertIsNone(reciprocal["additional_wire_bytes_per_hash"])
        self.assertTrue(reciprocal["table_entries_are_not_request_counts"])
        self.assertEqual(report["retained_preparation"]["cache_image_bytes"], 268435456)
        self.assertEqual(report["retained_preparation"]["prepared_instruction_capacity_bytes"], 32768)
        self.assertEqual(report["retained_preparation"]["reciprocal_table_data_bytes"], 1912)
        self.assertEqual(report["retained_preparation"]["mutable_scratchpad_bytes_per_context"], 2097152)

    def test_latency_rows_are_conditional_average_bounds_not_observed_overlap(self):
        report = model.build_report(FIXTURE)
        self.assertEqual(len(report["latency_sweep"]), 36)
        expected = {"vm_dataset_response": 1639,
                    "prepared_cache_response": 13108,
                    "prepared_instruction_response": 5837620}
        for row in report["latency_sweep"]:
            self.assertTrue(row["readiness_is_assumed_not_established_by_issue_width"])
            if row["assumed_response_latency_ns"] == 100 and row["ready_per_context"] == 1:
                self.assertEqual(row["necessary_outstanding_requests"], expected[row["interface"]])
                self.assertEqual(row["necessary_contexts_if_ready_limit_is_valid"], expected[row["interface"]])
        for gate in report["physical_service_gates"].values():
            self.assertEqual(gate["status"], "unresolved")
            self.assertIn("sustainable_transactions_per_s", gate["unknown"])
            self.assertIn("bank_port_operations_per_s", gate["unknown"])
            self.assertIn("controller_bank_timing_turnaround_refresh_tail_latency", gate["unknown"])
            self.assertIn("complete_path_throughput", gate["unknown"])
            self.assertFalse(gate["demonstrated_asic_feasibility"])

    def test_unknown_power_and_alternative_performance_remain_unknown(self):
        report = model.build_report(FIXTURE)
        self.assertEqual(report["strict_wall_energy_ceiling_j_per_hash"], 0.0025)
        for name in ("achieved_hashes_per_second", "alternative_full_hash_cycles",
                     "physical_frequency_hz", "physical_wall_power_w"):
            self.assertIsNone(report[name])
        self.assertFalse(report["demonstrated_asic_feasibility"])
        self.assertEqual(report["power"]["status"], "unresolved")
        self.assertIsNone(report["power"]["wall_power_w"])
        self.assertIsNone(report["power"]["wall_j_per_hash"])
        for term in ("dynamic.compute", "dynamic.controllers_phy", "static.fans", "psu_efficiency", "ac_auxiliary_w"):
            self.assertIn(term, report["power"]["missing"])
        self.assertEqual(report["complete_machine_gate"]["status"], "unresolved")

    def test_semantic_validation_does_not_grant_input_attribution(self):
        facts = model.validate_evidence(self.data)
        self.assertEqual(facts, {"iterations": 16384, "prepared_instructions_per_item": 3563})
        self.assertNotIn("identity_status", facts)
        with self.assertRaises(TypeError):
            model.build_report(self.data)

    def test_unknown_or_missing_fields_and_forged_source_are_rejected(self):
        mutations = []
        data = copy.deepcopy(self.data); data["trace_sha256"] = model.ACCEPTED_EVIDENCE_SHA256; mutations.append(data)
        data = copy.deepcopy(self.data); del data["source"]["public_tree"]; mutations.append(data)
        data = copy.deepcopy(self.data); data["source"]["public_head"] = "0" * 40; mutations.append(data)
        data = copy.deepcopy(self.data); data["source"]["acceptance_review_url"] = "https://example.invalid/approved"; mutations.append(data)
        data = copy.deepcopy(self.data); data["ledger"]["stage_cycles"]["extra_dataset_cost"] = 1; mutations.append(data)
        data = copy.deepcopy(self.data); del data["dataset"]["service_phase_cycles"]; mutations.append(data)
        for data in mutations:
            with self.subTest(data=data), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_boolean_negative_float_and_nonfinite_counters_are_rejected(self):
        for invalid in (True, False, -1, 1.0, float("nan"), float("inf"), "1", None):
            for section, field in (("dataset", "demands"), ("ledger", "outer_cycles"),
                                   ("preparation", "reciprocal_count"), ("workload", "programs")):
                data = copy.deepcopy(self.data); data[section][field] = invalid
                with self.subTest(section=section, field=field, invalid=invalid), self.assertRaises(ValueError):
                    model.validate_evidence(data)
            data = copy.deepcopy(self.data); data["ledger"]["nested_executor_phases"][0] = invalid
            with self.subTest(vector_value=invalid), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_functional_completeness_and_zero_live_provider_contract(self):
        for value in (False, 1, "true", None):
            data = copy.deepcopy(self.data); data["functional"]["native_digest_equal"] = value
            with self.subTest(digest_flag=value), self.assertRaises(ValueError):
                model.validate_evidence(data)
        for field, value in (("full_scratchpad_boundaries", 7), ("hardware_seed_transitions", 8)):
            data = copy.deepcopy(self.data); data["functional"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                model.validate_evidence(data)
        for name in ("input", "fill", "program", "dataset"):
            data = copy.deepcopy(self.data); data["functional"]["live_software_provider_calls"][name] = 1
            with self.subTest(provider=name), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_request_response_retirement_and_stage_counts_must_close(self):
        for name in ("demands", "responses", "items", "item_returns", "stages",
                     "cache_requests", "cache_responses", "instruction_requests",
                     "instruction_responses", "session_launch_extra_clocks"):
            data = copy.deepcopy(self.data); data["dataset"][name] += 1
            with self.subTest(counter=name), self.assertRaises(ValueError):
                model.validate_evidence(data)
        for name in ("program_service_extra_clocks", "cache_service_extra_clocks"):
            data = copy.deepcopy(self.data); data["dataset"][name] = 1
            with self.subTest(counter=name), self.assertRaises(ValueError):
                model.validate_evidence(data)
        data = copy.deepcopy(self.data)
        for name in ("retirements", "instruction_requests", "instruction_responses"):
            data["dataset"][name] += 1
        with self.assertRaisesRegex(ValueError, "complete repeated"):
            model.validate_evidence(data)
        data = copy.deepcopy(self.data)
        for name in ("retirements", "instruction_requests", "instruction_responses"):
            data["dataset"][name] = 16384 * 4097
        with self.assertRaisesRegex(ValueError, "capacity"):
            model.validate_evidence(data)

    def test_vector_lengths_and_individual_phase_relationships_are_checked(self):
        for section, name in (("dataset", "service_phase_cycles"), ("dataset", "session_phase_cycles"),
                              ("dataset", "item_phase_cycles"), ("ledger", "nested_iteration_phases"),
                              ("ledger", "nested_executor_phases")):
            for action in ("short", "long", "negative"):
                data = copy.deepcopy(self.data); vector = data[section][name]
                if action == "short": vector.pop()
                elif action == "long": vector.append(0)
                else: vector[0] = -1
                with self.subTest(vector=name, action=action), self.assertRaises(ValueError):
                    model.validate_evidence(data)
        for name in ("service_phase_cycles", "session_phase_cycles", "item_phase_cycles"):
            data = copy.deepcopy(self.data)
            # Preserve the total; a wrong phase allocation must still fail.
            data["dataset"][name][0] += 1; data["dataset"][name][1] -= 1
            with self.subTest(vector=name), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_outer_nested_and_vm_dataset_executor_domains_cannot_be_interchanged(self):
        mutations = []
        data = copy.deepcopy(self.data); data["ledger"]["outer_cycles"] += 1; mutations.append(data)
        data = copy.deepcopy(self.data); data["ledger"]["stage_cycles"]["execution"] += 1; mutations.append(data)
        data = copy.deepcopy(self.data); data["ledger"]["nested_executor_phases"][1] += 1; mutations.append(data)
        data = copy.deepcopy(self.data); data["dataset"]["core_item_availability_clocks"] += 1; mutations.append(data)
        data = copy.deepcopy(self.data); data["dataset"]["executor_clocks"] = sum(data["ledger"]["nested_executor_phases"]); mutations.append(data)
        for data in mutations:
            with self.subTest(data=data), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_dataset_availability_must_not_be_added_to_outer_twice(self):
        for adjust_execution in (False, True):
            data = copy.deepcopy(self.data); cost = data["dataset"]["item_availability_clocks"]
            data["ledger"]["outer_cycles"] += cost
            if adjust_execution: data["ledger"]["stage_cycles"]["execution"] += cost
            with self.subTest(adjust_execution=adjust_execution), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_prepared_image_contract_does_not_accept_a_different_interface_width(self):
        for name, value in (("instruction_word_bytes", 16), ("reciprocal_word_bytes", 4),
                            ("cache_bytes", 0), ("instructions_per_program_capacity", 1024),
                            ("program_slots", 4), ("reciprocal_count", 2**32)):
            data = copy.deepcopy(self.data); data["preparation"][name] = value
            with self.subTest(field=name), self.assertRaises(ValueError):
                model.validate_evidence(data)

    def test_stale_embedded_claims_and_semantically_valid_mutation_are_untrusted(self):
        for kind in ("claims", "consistent_counter_change", "extra_newline"):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "evidence.json"
                data = copy.deepcopy(self.data)
                if kind == "claims": data["claimed_sha256"] = model.ACCEPTED_EVIDENCE_SHA256
                if kind == "consistent_counter_change":
                    # This can be a structurally valid different program image,
                    # but is not the byte-bound accepted workload.
                    for name in ("retirements", "instruction_requests", "instruction_responses"):
                        data["dataset"][name] += 16384
                    model.validate_evidence(data)
                raw = FIXTURE.read_bytes() + b"\n" if kind == "extra_newline" else json.dumps(data).encode()
                path.write_bytes(raw)
                with self.subTest(kind=kind), self.assertRaises(model.EvidenceError) as error:
                    model.build_report(path)
                self.assertEqual(error.exception.provenance["identity_status"], "untrusted_input")
                self.assertIsNone(error.exception.provenance["accepted_source"])

    def test_duplicate_fields_nonfinite_json_and_invalid_bound_semantics_fail_closed(self):
        valid = FIXTURE.read_bytes()
        bad_inputs = [b'{"schema":"first","schema":"second"}',
                      b'{"schema":NaN}', b'{"schema":Infinity}', b'{"schema":-Infinity}',
                      b'{}', b'\xff', b'not json']
        for raw in bad_inputs:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "evidence.json"; path.write_bytes(raw)
                # Exercise parsing/semantic failure independently of byte
                # identity, as if a future registry update bound bad bytes.
                with patch.object(model, "ACCEPTED_EVIDENCE_SHA256", hashlib.sha256(raw).hexdigest()):
                    with self.assertRaises(model.EvidenceError) as error:
                        model.build_report(path)
                self.assertEqual(error.exception.provenance["identity_status"], "untrusted_input")
                self.assertIsNone(error.exception.provenance["accepted_source"])
        self.assertEqual(FIXTURE.read_bytes(), valid)

    def test_missing_or_oversized_input_retains_no_accepted_attribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("missing.json", "oversized.json"):
                path = Path(tmp) / name
                if name.startswith("oversized"):
                    path.write_bytes(b" " * (model.MAX_EVIDENCE_BYTES + 1))
                with self.subTest(name=name), self.assertRaises(model.EvidenceError) as error:
                    model.build_report(path)
                self.assertEqual(error.exception.provenance["identity_status"], "untrusted_input")
                self.assertIsNone(error.exception.provenance["accepted_source"])

    def test_new_output_is_complete_and_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "new"
            report = model.run(FIXTURE, output)
            self.assertEqual(json.loads((output / "service-demand.json").read_text()), report)
            index = json.loads((output / "artifacts.sha256.json").read_text())
            self.assertEqual(set(index), {"provenance.json", "service-demand.json"})
            for name, expected in index.items():
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), expected)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            with self.assertRaises(FileExistsError): model.run(FIXTURE, output)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_cli_untrusted_input_keeps_provenance_and_never_creates_an_accepted_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); path = tmp / "bad.json"; output = tmp / "result"
            path.write_bytes(FIXTURE.read_bytes() + b"\n")
            result = subprocess.run([sys.executable, "-B", "-m", "tools.architecture.hardware_dataset",
                                     "--evidence", str(path), "--output", str(output)],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("untrusted input", result.stderr)
            self.assertEqual({p.name for p in output.iterdir()}, {"provenance.json"})
            provenance = json.loads((output / "provenance.json").read_text())
            self.assertEqual(provenance["identity_status"], "untrusted_input")
            self.assertIsNone(provenance["accepted_source"])

    def test_cli_success_keeps_legacy_fixtures_pins_and_modules_exact(self):
        from tools.architecture import run as legacy
        self.assertEqual(legacy.ACCEPTED_FULL_EVIDENCE_SHA256,
                         "33f4cbe95805d33068fa9eceee90820f230cd0457d06f35407f9323d1d547ecf")
        self.assertEqual(len(legacy.ACCEPTED_FIXTURE_SHA256), 12)
        architecture = ROOT / "tools/architecture"
        paths = [architecture / name for name in ("run.py", "evidence.py", "baseline.py", "envelope.py", "scheduler.py", "native_trace.py")]
        paths += [architecture / "fixtures/successor-first-iterations" / name
                  for name in legacy.ACCEPTED_FIXTURE_SHA256]
        paths.append(FIXTURE)
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "new"
            result = subprocess.run([sys.executable, "-B", "-m", "tools.architecture.hardware_dataset",
                                     "--evidence", str(FIXTURE), "--output", str(output)],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["physical_feasibility"], "unresolved")
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__ == "__main__":
    unittest.main()
