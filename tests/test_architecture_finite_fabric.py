"""Finite component evidence contracts; these do not validate a physical service."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.architecture import finite_fabric as model
from tools.architecture import hardware_dataset

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "tools/architecture/fixtures/accepted_finite_fabric_v1.json"
OLD_FIXTURE = ROOT / "tools/architecture/fixtures/accepted_hardware_dataset_v2.json"
OLD_GOLD = ROOT / "docs/validation/hardware-dataset-service-profile-20261021"


class FiniteFabricProfileTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text())
        self.records = {name: json.loads((ROOT / model.PREFIX / name).read_text())
                        for name in model.ARTIFACT_NAMES}

    def test_bound_component_report_preserves_domain_and_physical_unknowns(self):
        report = model.build_report(REGISTRY)
        provenance = report["provenance"]
        self.assertEqual(provenance["accepted_source"], model.ACCEPTED_SOURCE)
        self.assertEqual(provenance["actual_registry_sha256"], hashlib.sha256(REGISTRY.read_bytes()).hexdigest())
        self.assertEqual(len(provenance["actual_artifact_sha256"]), 22)
        self.assertEqual(report["interface_width_source"]["sha256"], self.registry["fabric_sha256"])
        self.assertEqual(set(report["profiles"]), set(model.PROFILES))
        self.assertEqual(report["dataset_item_clients"], 2)
        self.assertFalse(report["vm_contexts_validated"])
        self.assertEqual(report["independent_vm_scratchpads_validated"], 0)
        for key in ("achieved_hashes_per_second", "alternative_full_hash_cycles", "physical_frequency_hz",
                    "physical_wall_power_w", "aggregate_physical_offchip_bits_per_hash", "engine_count_selected"):
            self.assertIsNone(report[key])
        self.assertFalse(report["demonstrated_asic_feasibility"])
        self.assertFalse(report["full_hash_projection_performed"])
        for gate in report["physical_service_gates"].values():
            self.assertEqual(gate["status"], "unresolved")
            self.assertFalse(gate["demonstrated_asic_feasibility"])

    def test_descriptor_counts_include_owned_cancelled_replies_and_keep_links_separate(self):
        report = model.build_report(REGISTRY)
        ideal = report["profiles"]["concurrent-ideal"]
        fetch, cache = ideal["interfaces"]["fetch"], ideal["interfaces"]["cache"]
        self.assertEqual((fetch["request_descriptor_bits"], fetch["response_descriptor_bits"]), (93, 255))
        self.assertEqual((cache["request_descriptor_bits"], cache["response_descriptor_bits"]), (106, 619))
        self.assertEqual((fetch["request_descriptor_bits_per_batch"], fetch["response_descriptor_bits_per_batch"]),
                         (662718, 1817130))
        self.assertEqual((cache["request_descriptor_bits_per_batch"], cache["response_descriptor_bits_per_batch"]),
                         (1696, 9904))
        cancelled = report["profiles"]["cancel0"]["interfaces"]["fetch"]
        self.assertEqual(cancelled["response_descriptor_bits_per_batch"], 7128 * 255)
        self.assertEqual(cancelled["delivered_by_client"], [3564, 3563])
        self.assertEqual(cancelled["cancelled_responses"], 1)
        self.assertEqual(fetch["owner_credit_occupied_fraction"], {"numerator": 14252, "denominator": 61595})
        self.assertEqual(report["observed_batch_comparisons"]["ideal"]["observed_two_item_batch_ratio"],
                         {"numerator": 113953, "denominator": 61595})
        self.assertEqual(ideal["batch_elapsed_cycles"], 61595)
        self.assertGreater(sum(ideal["client_availability_nested_cycles"]), ideal["batch_elapsed_cycles"])
        self.assertIsNone(fetch["physical_offchip_traffic_bits"])
        self.assertIsNone(cache["characterized_physical_service_latency_seconds"])

    def test_channel_conservation_does_not_allow_unowned_or_multiple_credit_traffic(self):
        original = self.records["prefix/native-concurrent-ideal.json"]["fetch"]
        mutations = []
        for key in ("backend_requests", "backend_responses", "cancelled_responses", "orphan_responses", "high_water"):
            row = copy.deepcopy(original); row[key] += 1; mutations.append(row)
        row = copy.deepcopy(original); row["delivered"][0] += 1; mutations.append(row)
        row = copy.deepcopy(original); row["occupied_cycles"] = 61596; mutations.append(row)
        row = copy.deepcopy(original); row["arbitration_wait_cycles"][0] = 61596; mutations.append(row)
        for row in mutations:
            with self.subTest(row=row), self.assertRaises(ValueError):
                model._channel(row, 61595, "fetch")

    def test_native_error_cancel_phase_work_and_namespace_domains_are_source_specific(self):
        mutations = []
        for name in ("concurrent-ideal", "cancel0", "cancel1", "malformed-fetch0", "exhaustion"):
            prefix = "prefix" if name == "concurrent-ideal" else "matrix"
            original = self.records[prefix + "/native-" + name + ".json"]
            row = copy.deepcopy(original)
            bins = row["item_rows"][0]["item_phase_cycles"]
            bins[1], bins[2] = bins[2], bins[1]  # Sum stays unchanged.
            mutations.append((name, row))
            row = copy.deepcopy(original); row["item_rows"][0]["namespace"] += 1; mutations.append((name, row))
            row = copy.deepcopy(original); row["clock_scope"] = "old full-hash clocks"; mutations.append((name, row))
        row = copy.deepcopy(self.records["matrix/native-cancel0.json"])
        row["item_rows"][0]["commits"] += 1; row["commits"] += 1
        mutations.append(("cancel0", row))
        row = copy.deepcopy(self.records["matrix/native-malformed-fetch0.json"])
        row["client_availability_cycles"][0] = 0  # The returned error contributes 44 clocks.
        mutations.append(("malformed-fetch0", row))
        row = copy.deepcopy(self.records["matrix/native-cancel1.json"])
        row["client_availability_cycles"][1] += 88  # Cancelled partial clocks are not returned availability.
        mutations.append(("cancel1", row))
        row = copy.deepcopy(self.records["matrix/native-malformed-fetch0.json"])
        row["fetch"]["accepted"][0] += 1; row["fetch"]["delivered"][0] += 1
        row["fetch"]["backend_requests"] += 1; row["fetch"]["backend_responses"] += 1
        mutations.append(("malformed-fetch0", row))  # Conserves traffic but does not match work.
        row = copy.deepcopy(self.records["matrix/native-exhaustion.json"])
        row["item_rows"][0], row["item_rows"][4] = row["item_rows"][4], row["item_rows"][0]
        mutations.append(("exhaustion", row))  # All counts stay equal; namespaces must still be monotonic.
        for name, row in mutations:
            with self.subTest(profile=name, row=row), self.assertRaises(ValueError):
                model._native(row, name)

    def test_registry_semantics_bind_source_ports_binary_and_exact_artifact_set(self):
        mutations = []
        for key in ("fabric_sha256", "changed_channel_sha256", "source_manifest_sha256"):
            data = copy.deepcopy(self.registry); data[key] = "0" * 64; mutations.append(data)
        data = copy.deepcopy(self.registry); data["prepared_binaries"]["native.vvp"] = "0" * 64; mutations.append(data)
        data = copy.deepcopy(self.registry); data["interfaces"]["fetch"]["request_payload_bits"] = 29; mutations.append(data)
        data = copy.deepcopy(self.registry); data["interfaces"]["fetch"]["backend_client_id_bits"] = True; mutations.append(data)
        data = copy.deepcopy(self.registry); data["extra"] = True; mutations.append(data)
        data = copy.deepcopy(self.registry)
        data["artifacts"]["../outside.json"] = data["artifacts"].pop(next(iter(data["artifacts"])))
        mutations.append(data)
        for data in mutations:
            with self.subTest(data=data), self.assertRaises(ValueError):
                model.validate_evidence(data, self.records)

    def test_forged_registry_or_accepted_claims_never_receive_attribution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            for raw in (REGISTRY.read_bytes() + b"\n", b'{"identity_status":"accepted_input_verified"}'):
                path.write_bytes(raw)
                with self.assertRaises(model.EvidenceError) as caught:
                    model.build_report(path)
                self.assertEqual(caught.exception.provenance["identity_status"], "untrusted_input")
                self.assertIsNone(caught.exception.provenance["accepted_source"])

    def test_actual_artifact_content_and_size_must_match_before_attribution(self):
        first = sorted(self.registry["artifacts"])[0]
        original = (ROOT / first).read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / first
            target.parent.mkdir(parents=True)
            for raw in (original + b"\n", bytes([original[0] ^ 1]) + original[1:]):
                target.write_bytes(raw)
                with self.assertRaises(model.EvidenceError) as caught:
                    model.build_report(REGISTRY, artifact_root=directory)
                self.assertIsNone(caught.exception.provenance["accepted_source"])

    def test_missing_oversized_and_escaping_artifacts_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(model.EvidenceError):
                model.build_report(REGISTRY, artifact_root=root)
            target = root / sorted(self.registry["artifacts"])[0]
            target.parent.mkdir(parents=True)
            target.write_bytes(b"x" * (model.MAX_ARTIFACT_BYTES + 1))
            with self.assertRaises(model.EvidenceError):
                model.build_report(REGISTRY, artifact_root=root)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            target = Path(directory) / sorted(self.registry["artifacts"])[0]
            target.parent.mkdir(parents=True)
            source = Path(outside) / "copied.json"; source.write_text("{}")
            target.symlink_to(source)
            with self.assertRaises(model.EvidenceError):
                model.build_report(REGISTRY, artifact_root=directory)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_bytes(b"x" * (model.MAX_REGISTRY_BYTES + 1))
            with self.assertRaises(model.EvidenceError):
                model.build_report(path)

    def test_duplicate_nonfinite_and_invalid_integer_counters_are_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                model._parse(raw)
        for value in (True, False, -1, 1.0, 2**64, None, "1"):
            row = copy.deepcopy(self.records["prefix/native-concurrent-ideal.json"])
            row["fetch"]["backend_requests"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                model._native(row, "concurrent-ideal")
        row = copy.deepcopy(self.records["prefix/native-concurrent-ideal.json"]); row["unknown"] = 0
        with self.assertRaises(ValueError):
            model._native(row, "concurrent-ideal")

    def test_stage_admission_raw_flags_and_mapped_source_cannot_be_substituted(self):
        mutations = []
        for path, key, value in (
            ("prefix/verification-summary.json", "same_source_new_binaries", {"native.vvp": "0" * 64}),
            ("matrix/verification-summary.json", "execution_id", "historical-prefix"),
            ("matrix/public-summary.json", "scientific_acceptance", "accepted"),
            ("synthesis/public-summary.json", "mapped_parity_byte_exact", {"protocol": True, "native_concurrent_ideal": False}),
            ("synthesis/public-summary.json", "new_full_hash_executed", True),
            ("source-bindings.json", "prepared_manifest_sha256", "0" * 64),
        ):
            records = copy.deepcopy(self.records); records[path][key] = value; mutations.append(records)
        records = copy.deepcopy(self.records)
        records["matrix/independent-result-review.json"]["reuse"]["only_new_same_source_prefix_binary_used_for_all_seven_profiles"] = False
        mutations.append(records)
        records = copy.deepcopy(self.records)
        records["synthesis/mapped-native-concurrent-ideal.json"]["batch_elapsed_cycles"] += 1
        mutations.append(records)
        for records in mutations:
            with self.subTest(records=records), self.assertRaises(ValueError):
                model.validate_evidence(self.registry, records)

    def test_mapping_scopes_are_separate_and_semantics_alone_grant_no_attribution(self):
        facts = model.validate_evidence(self.registry, self.records)
        self.assertNotIn("provenance", facts)
        self.assertEqual(facts["mapping"]["fabric"]["generic_cells"], 14498)
        self.assertEqual(facts["mapping"]["channel"]["generic_cells"], 6581)
        for key, value in (("generic_cells", 14499), ("DFF_cells", 1616), ("latch_cells", 1)):
            records = copy.deepcopy(self.records)
            records["synthesis/mapping-statistics.json"]["mapping"]["fabric"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                model.validate_evidence(self.registry, records)

    def test_output_cli_index_failures_and_unchanged_legacy_gold(self):
        preserved = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            ROOT / "tools/architecture/hardware_dataset.py", OLD_FIXTURE,
            OLD_GOLD / "service-demand.json", OLD_GOLD / "provenance.json")}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report"
            model.run(REGISTRY, output)
            index = json.loads((output / "artifacts.sha256.json").read_text())
            self.assertEqual(set(index), {"finite-fabric-service-profile.json", "provenance.json"})
            for name, digest in index.items():
                self.assertEqual(digest, hashlib.sha256((output / name).read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                model.run(REGISTRY, output)
            cli_output = Path(directory) / "cli"
            result = subprocess.run([sys.executable, "-B", "-m", "tools.architecture.finite_fabric", "--evidence",
                                     str(REGISTRY), "--output", str(cli_output)], cwd=ROOT,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "analytical_component_only")
            bad = Path(directory) / "bad.json"; bad.write_bytes(REGISTRY.read_bytes() + b"\n")
            with self.assertRaises(model.EvidenceError):
                model.run(bad, Path(directory) / "rejected")
            self.assertEqual({p.name for p in (Path(directory) / "rejected").iterdir()}, {"provenance.json"})
            old = Path(directory) / "old"
            hardware_dataset.run(OLD_FIXTURE, old)
            for name in ("service-demand.json", "provenance.json"):
                self.assertEqual((old / name).read_bytes(), (OLD_GOLD / name).read_bytes())
        for path, digest in preserved.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
