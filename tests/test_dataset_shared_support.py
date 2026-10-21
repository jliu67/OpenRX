"""Negative scientific/provenance contracts; payloads run only after admission."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


# Distinct identity avoids the historical same-named unittest/driver import bug.
DRIVER = Path(__file__).resolve().parents[1] / "scripts/test_dataset_shared.py"
SPEC = importlib.util.spec_from_file_location("openrx_shared_dataset_driver_support", DRIVER)
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)


def channel(accepted, delivered=None, cancelled=0, orphan=0, occupied=20000):
    delivered = list(accepted) if delivered is None else delivered
    return {"accepted": list(accepted), "delivered": list(delivered),
            "backend_requests": sum(accepted), "backend_responses": sum(delivered) + cancelled + orphan,
            "cancelled_responses": cancelled, "orphan_responses": orphan,
            "occupied_cycles": occupied, "arbitration_wait_cycles": [0, 0],
            "high_water": int(bool(sum(accepted)))}


def item(client, namespace=1, status="success"):
    return {"client": client, "namespace": namespace, "status": status,
            "commits": 3563, "multiplies": 1254, "stages": 8,
            "availability_cycles": 65000, "core_cycles": 64999, "executor_cycles": 60000,
            "session_phase_cycles": [0, 1, 64999],
            "item_phase_cycles": [0, 1, 0, 0, 64999, 0, 0, 0, 0]}


def native(profile="concurrent-ideal"):
    return {"schema": shared.NATIVE_SCHEMA, "status": "pass", "profile": profile,
            "mode_serial": profile.startswith("serial-"), "mode_stalled": profile.endswith("-stalled"),
            "fixture_cases": [0, 1], "fixture_item_numbers": [0, 10000000],
            "successful_items": 2, "error_items": 0, "aborted_items": 0, "returned_items": 2,
            "commits": 7126, "multiplies": 2508, "stages": 16, "sessions_used": [1, 1],
            "batch_elapsed_cycles": 140000 if profile.startswith("serial-") else 70000,
            "client_availability_cycles": [65000, 65000], "client_core_cycles": [64999, 64999],
            "client_executor_cycles": [60000, 60000], "client_held_backpressure_cycles": [4, 4],
            "fetch": channel([3563, 3563]), "cache": channel([8, 8], occupied=100),
            "identity_collision_checks": {"fetch": True, "cache": True},
            "quiescent_hard_reset_checked": True, "counters_before_final_quiescent_reset": True,
            "exhaustion_admission_denied": False, "cancelled_identity_retained": False,
            "item_rows": [item(0), item(1)]}


def protocol():
    result = {"schema": shared.PROTOCOL_SCHEMA, "status": "pass", "checks": 1000, "cycles": 200,
              "counter_closure_checks": 200, "fairness_pairs": 8, "identical_tag_pairs": 8,
              "early_reply_hold_cycles": 3, "same_edge_request_response_cases": 2,
              "queued_cancel_cases": 1, "issued_cancel_cases": 1, "held_cancel_cases": 1,
              "foreign_owner_packets": 2, "wrong_low_tag_packets": 1, "idle_orphan_packets": 1,
              "malformed_payload_forwarded": 1, "other_client_progress_cases": 1,
              "nonowner_cancel_cases": 1, "quiescent_reset_cases": 1,
              "descriptor_hold_cycles": 3, "response_hold_cycles": 7,
              "accepted_count": [12, 11], "delivered_count": [10, 10],
              "arbitration_wait_cycles": [1, 2], "backend_request_count": 23,
              "backend_response_count": 27, "cancelled_response_count": 3,
              "orphan_response_count": 4, "occupied_cycles": 100, "high_water_mark": 1,
              "counter_snapshot_scope": "before_final_quiescent_reset"}
    return result


class SharedDatasetSupportTests(unittest.TestCase):
    def test_unique_driver_identity_and_complete_component_pair(self):
        self.assertEqual(shared.__name__, "openrx_shared_dataset_driver_support")
        for name in shared.PROFILES[:4]:
            shared.validate_native(native(name), name)
        shared.validate_protocol(protocol())

    def test_status_alone_partial_pair_and_wrong_case_identity_fail_closed(self):
        for mutation in (lambda x: x.update(successful_items=1),
                         lambda x: x.update(fixture_item_numbers=[0, 1]),
                         lambda x: x["item_rows"].pop(),
                         lambda x: x.update(profile="serial-ideal"),
                         lambda x: x.update(quiescent_hard_reset_checked=False)):
            value = native()
            mutation(value)
            with self.assertRaises((ValueError, KeyError)):
                shared.validate_native(value, "concurrent-ideal")
        with self.assertRaises((ValueError, KeyError)):
            shared.validate_native({"schema": shared.NATIVE_SCHEMA, "status": "pass"}, "concurrent-ideal")

    def test_boolean_float_negative_and_missing_counters_are_not_accepted(self):
        for bad in (True, -1, 7126.0, float("nan")):
            value = native()
            value["commits"] = bad
            with self.assertRaises(ValueError):
                shared.validate_native(value, "concurrent-ideal")
        value = native()
        del value["fetch"]["accepted"]
        with self.assertRaises((ValueError, KeyError)):
            shared.validate_native(value, "concurrent-ideal")

    def test_client_tag_isolation_and_cancelled_or_orphan_ledger_cannot_be_forged(self):
        for mutation in (lambda x: x["fetch"].update(delivered=[3562, 3564]),
                         lambda x: x["fetch"].update(backend_responses=7127),
                         lambda x: x["fetch"].update(cancelled_responses=1),
                         lambda x: x["fetch"].update(high_water=2),
                         lambda x: x["identity_collision_checks"].update(cache=False)):
            value = native()
            mutation(value)
            with self.assertRaises(ValueError):
                shared.validate_native(value, "concurrent-ideal")

    def test_clock_vectors_and_domains_reject_double_addition_and_core_confusion(self):
        for mutation in (lambda x: x["item_rows"][0]["session_phase_cycles"].append(0),
                         lambda x: x["item_rows"][0]["item_phase_cycles"].__setitem__(0, 1),
                         lambda x: x["item_rows"][0].update(core_cycles=65000),
                         lambda x: x["item_rows"][0].update(executor_cycles=0),
                         lambda x: x.update(client_availability_cycles=[130000, 65000]),
                         lambda x: x.update(batch_elapsed_cycles=64000),
                         lambda x: x["fetch"].update(occupied_cycles=7125)):
            value = native()
            mutation(value)
            with self.assertRaises(ValueError):
                shared.validate_native(value, "concurrent-ideal")

    def test_cancelled_prefix_is_not_completed_availability_or_refunded_namespace(self):
        value = native()
        value.update(profile="cancel0", mode_stalled=True, aborted_items=1, sessions_used=[2, 1],
                     commits=7134, multiplies=2510, cancelled_identity_retained=True)
        value["item_rows"][0]["namespace"] = 2
        prefix = {"client": 0, "namespace": 1, "status": "cancelled", "commits": 8,
                  "multiplies": 2, "stages": 0, "partial_elapsed_cycles": 20,
                  "session_phase_cycles": [0, 1, 19], "item_phase_cycles": [0, 1, 0, 0, 19, 0, 0, 0, 0]}
        value["item_rows"].insert(0, prefix)
        value["fetch"] = channel([3572, 3563], [3571, 3563], cancelled=1)
        value["identity_collision_checks"]["cache"] = False
        shared.validate_native(value, "cancel0")
        wrong = copy.deepcopy(value)
        wrong["item_rows"][0]["availability_cycles"] = 20
        with self.assertRaises(ValueError):
            shared.validate_native(wrong, "cancel0")
        wrong = copy.deepcopy(value)
        wrong["sessions_used"] = [1, 1]
        with self.assertRaises(ValueError):
            shared.validate_native(wrong, "cancel0")

    def test_exhaustion_requires_three_distinct_burned_namespaces_and_denied_fourth(self):
        value = native()
        value.update(profile="exhaustion", successful_items=6, returned_items=6,
                     commits=21378, multiplies=7524, stages=48, sessions_used=[3, 3],
                     batch_elapsed_cycles=210000, client_availability_cycles=[195000, 195000],
                     client_core_cycles=[194997, 194997], client_executor_cycles=[180000, 180000],
                     client_held_backpressure_cycles=[12, 12], exhaustion_admission_denied=True)
        value["item_rows"] = [item(client, namespace) for namespace in (1, 2, 3) for client in (0, 1)]
        value["fetch"] = channel([10689, 10689], occupied=60000)
        value["cache"] = channel([24, 24], occupied=300)
        shared.validate_native(value, "exhaustion")
        for mutation in (lambda x: x.update(exhaustion_admission_denied=False),
                         lambda x: x["item_rows"][-1].update(namespace=1)):
            wrong = copy.deepcopy(value)
            mutation(wrong)
            with self.assertRaises(ValueError):
                shared.validate_native(wrong, "exhaustion")

    def test_protocol_requires_actual_coverage_and_pre_reset_ownership_closure(self):
        for mutation in (lambda x: x.update(fairness_pairs=0),
                         lambda x: x.update(early_reply_hold_cycles=0),
                         lambda x: x.update(queued_cancel_cases=0),
                         lambda x: x.update(malformed_payload_forwarded=0),
                         lambda x: x.update(backend_response_count=26),
                         lambda x: x.update(counter_snapshot_scope="after_reset"),
                         lambda x: x.update(accepted_count=[True, 22])):
            value = protocol()
            mutation(value)
            with self.assertRaises(ValueError):
                shared.validate_protocol(value)

    def test_actual_receipt_and_artifact_bytes_are_the_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "execution-1"
            directory.mkdir()
            artifact = directory / "binary.vvp"
            artifact.write_bytes(b"actual compiled bytes")
            row = {"path": str(artifact), **shared.binding(artifact)}
            receipt = {"schema": "openrx.local.receipt.v1", "execution_id": directory.name,
                       "status": "PROCESS_EXITED", "process": {"returncode": 0},
                       "scientific_acceptance": "unverified", "artifacts": [row]}
            path = directory / "receipt.json"
            path.write_text(json.dumps(receipt))
            external = shared.sha(path)
            _, catalogue = shared.completed_receipt(path, external)
            shared.bound_artifact(artifact, catalogue)
            artifact.write_bytes(b"edited compiled bytes")
            with self.assertRaises(ValueError):
                shared.bound_artifact(artifact, catalogue)
            receipt["artifacts"][0]["sha256"] = shared.sha(artifact)
            path.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                shared.completed_receipt(path, external)

    def test_receipt_duplicates_reclassified_flags_and_noninteger_exit_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "execution-2"
            directory.mkdir()
            artifact = directory / "result.json"
            artifact.write_text("{}")
            row = {"path": str(artifact), **shared.binding(artifact)}
            valid = {"schema": "openrx.local.receipt.v1", "execution_id": directory.name,
                     "status": "PROCESS_EXITED", "process": {"returncode": 0},
                     "scientific_acceptance": "unverified", "artifacts": [row]}
            for mutation in (lambda x: x["artifacts"].append(copy.deepcopy(row)),
                             lambda x: x.update(scientific_acceptance="accepted"),
                             lambda x: x["process"].update(returncode=False),
                             lambda x: x["artifacts"][0].update(bytes=True)):
                value = copy.deepcopy(valid)
                mutation(value)
                path = directory / "receipt.json"
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    shared.completed_receipt(path, shared.sha(path))

    def test_json_duplicate_nonfinite_and_oversize_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            for text in ('{"status":"pass","status":"fail"}', '{"cycles":NaN}', '{"cycles":Infinity}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    shared.load_json(path)
            path.write_text('"' + 'a' * 100 + '"')
            with self.assertRaises(ValueError):
                shared.load_json(path, maximum=32)

    def test_source_symlinks_git_checkout_and_changed_files_are_not_silent(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source"
            source.mkdir()
            file = source / "new.v"
            file.write_text("module original; endmodule\n")
            before = shared.fingerprint(source)
            file.write_text("module changed; endmodule\n")
            self.assertNotEqual(before, shared.fingerprint(source))
            link = source / "alias.v"
            link.symlink_to(file)
            with self.assertRaises(ValueError):
                shared.fingerprint(source)
            link.unlink()
            (source / ".git").mkdir()
            with self.assertRaises(ValueError):
                shared.fingerprint(source)

    def test_fixture_selection_is_bounded_to_two_native_cases_and_cache0(self):
        names = shared.selected_fixture_names()
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("cache-0.bin", names)
        self.assertIn("case-000/steps-7.mem", names)
        self.assertIn("case-001/steps-7.mem", names)
        self.assertNotIn("cache-1.bin", names)
        self.assertFalse(any(name.startswith("case-002/") for name in names))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            path.write_text("{}")
            with self.assertRaises(ValueError):
                shared.fixture_bindings(Path(temporary), path)

    def test_reuse_checks_actual_runner_argv_and_receipt_bound_binary_not_embedded_claims(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source, prior = base / "source", base / "prefix-execution"
            source.mkdir()
            (source / "input.v").write_text("module retained; endmodule\n")
            output = prior / "output"
            output.mkdir(parents=True)
            fixtures = base / "fixtures"
            fixtures.mkdir()
            fixture_receipt = base / "fixture-receipt.json"
            fixture_receipt.write_text("{}"); fixture = {"bound-case": {"bytes": 1, "sha256": "a" * 64}}
            sources = shared.fingerprint(source)
            tools = {"python": {"path": "/bound/python", "bytes": 1, "sha256": "b" * 64}}
            summary = {"schema": shared.SUMMARY_SCHEMA, "phase": "prefix", "status": "pass_prefix",
                       "source_before": sources, "source_after": sources,
                       "fixture_before": fixture, "fixture_after": fixture,
                       "tools_before": tools, "tools_after": tools,
                       "source_unchanged": True, "fixtures_unchanged": True,
                       "protocol": protocol(), "native": {"concurrent-ideal": native()}}
            manifest = {"schema": "openrx.local.execution.v1", "migration_state": "LOCAL_ACTIVE",
                        "execution_id": prior.name, "cwd": str(source), "executable": tools["python"],
                        "argv": ["/bound/python", "-B", str(source / "scripts/test_dataset_shared.py"),
                                 "--phase", "prefix", "--source", str(source), "--output", str(output),
                                 "--fixtures", str(fixtures), "--fixture-receipt", str(fixture_receipt)],
                        "sources": [{"path": str(source), "kind": "directory", "files":
                                     [{"relative": name, **row} for name, row in sources.items()]}]}
            for path, value in ((prior / "manifest.json", manifest), (output / "summary.json", summary),
                                (output / "protocol.json", protocol()), (output / "native-concurrent-ideal.json", native())):
                path.write_text(json.dumps(value))
            for name in ("protocol.vvp", "native.vvp"):
                (output / name).write_bytes(b"bound compiled component")

            def write_receipt():
                receipt = {"schema": "openrx.local.receipt.v1", "execution_id": prior.name,
                           "status": "PROCESS_EXITED", "process": {"returncode": 0},
                           "scientific_acceptance": "unverified", "artifacts": [
                               {"path": str(path), **shared.binding(path)} for path in sorted(prior.rglob("*"))
                               if path.is_file() and path.name != "receipt.json"]}
                (prior / "receipt.json").write_text(json.dumps(receipt))
                return shared.sha(prior / "receipt.json")

            proof = base / "verify.json"
            proof.write_text(json.dumps({"execution_id": prior.name, "integrity_verified": True, "status": "PROCESS_EXITED"}))
            args = SimpleNamespace(reuse_execution=prior, reuse_receipt_sha256=write_receipt(),
                                   reuse_verify=proof, reuse_verify_sha256=shared.sha(proof),
                                   fixtures=fixtures, fixture_receipt=fixture_receipt)
            with patch.object(shared, "ROOT", source):
                shared.validate_reuse(args, sources, fixture, tools)
                (output / "native.vvp").write_bytes(b"edited compiled object")
                with self.assertRaises(ValueError):
                    shared.validate_reuse(args, sources, fixture, tools)
                (output / "native.vvp").write_bytes(b"bound compiled component")
                manifest["argv"] = ["/bound/python", "-B", "/foreign/fake.py"]
                (prior / "manifest.json").write_text(json.dumps(manifest))
                args.reuse_receipt_sha256 = write_receipt()
                with self.assertRaises(ValueError):
                    shared.validate_reuse(args, sources, fixture, tools)


if __name__ == "__main__":
    unittest.main()
