"""Byte-bound finite dataset-fabric observations, never a physical prediction."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from . import envelope

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_SCHEMA = "openrx.architecture.finite-fabric-evidence.v1"
REPORT_SCHEMA = "openrx.architecture.finite-fabric-service-profile.v1"
TRUSTED_REGISTRY_SHA256 = "b8cc39f65341320c18adb64ab2b2ea05db262938de6de5aca91add7d69ed9828"
MAX_REGISTRY_BYTES, MAX_ARTIFACT_BYTES, MAX_TOTAL_BYTES = 65536, 131072, 1048576
PREFIX = "docs/validation/shared-dataset-fabric-20261021/recovery02/"
ACCEPTED_SOURCE = {
    "public_head": "f495a34fc8a67f69b7f3e407cc4b509b96b84d64",
    "public_tree": "d4455f073c858c7df5bd4d2ea7373fa52650df56",
    "acceptance_review_url": "https://github.com/jliu67/OpenRX/pull/89#pullrequestreview-5607170870",
    "merge_commit": "b6e71b467bc3c51e1c6734853a08b11412c8653a",
}
SOURCE_MANIFEST = "1176a4a2112e364fb6aec674146273d27729388ef7854a8de56388f03524e5ea"
CHANNEL_SHA256 = "0d02318cad0991321fed4a365664d231f90f1968ef2e1fdc733c3b5291d06493"
FABRIC_SHA256 = "4c6c4d5c784ad8c310b20afea5ee62fffa7cd910eb6632a76f6daeb1f171c438"
PREPARED_BINARIES = {
    "native.vvp": "de6ae942026bc2415993cdb9f8937a7f05f4840282f6de5ca5d22d2a20014ca4",
    "protocol.vvp": "33c1d09941393b44f1ab8cc11b54ad7bb3d41e9f91c3ed57084c025380592e03",
}
# Port widths are source-specific facts from the SHA-bound fabric at the accepted public head.
# The 22 JSON files bind that source through source-bindings/reviews, not by containing RTL ports.
INTERFACES = {
    "fetch": {"client_tag_bits": 64, "backend_client_id_bits": 1,
              "request_payload_bits": 28, "response_payload_bits": 190},
    "cache": {"client_tag_bits": 64, "backend_client_id_bits": 1,
              "request_payload_bits": 41, "response_payload_bits": 554},
}
PROFILES = ("concurrent-ideal", "serial-ideal", "serial-stalled", "concurrent-stalled",
            "cancel0", "cancel1", "malformed-fetch0", "exhaustion")
STAGES = {
    "prefix": ("20261021T222437Z-6a260038ca5e", 7, 52, "PASS_PREFIX_ONLY"),
    "matrix": ("20261021T222845Z-8f21db168fd3", 9, 65, "PASS_MATRIX_ONLY"),
    "synthesis": ("20261021T223347Z-bec71d887374", 9, 67,
                  "PASS_SYNTHESIS_AND_MAPPED_PARITY_ONLY"),
}
ARTIFACT_NAMES = frozenset((
    "source-bindings.json", "prefix/public-summary.json", "prefix/protocol.json",
    "prefix/native-concurrent-ideal.json", "prefix/verification-summary.json",
    "prefix/independent-result-review.json", "matrix/public-summary.json",
    "matrix/verification-summary.json", "matrix/independent-result-review.json",
    "synthesis/public-summary.json", "synthesis/mapped-protocol.json",
    "synthesis/mapped-native-concurrent-ideal.json", "synthesis/mapping-statistics.json",
    "synthesis/verification-summary.json", "synthesis/independent-result-review.json",
    *("matrix/native-" + name + ".json" for name in PROFILES[1:]),
))
CHANNEL_FIELDS = frozenset(("accepted", "delivered", "backend_requests", "backend_responses",
                           "cancelled_responses", "orphan_responses", "occupied_cycles",
                           "arbitration_wait_cycles", "high_water"))
NATIVE_FIELDS = frozenset((
    "schema", "profile", "status", "item_rows", "mode_serial", "mode_stalled",
    "fixture_cases", "fixture_item_numbers", "successful_items", "error_items",
    "aborted_items", "returned_items", "commits", "multiplies", "stages", "sessions_used",
    "batch_elapsed_cycles", "client_availability_cycles", "client_core_cycles",
    "client_executor_cycles", "client_held_backpressure_cycles", "fetch", "cache",
    "identity_collision_checks", "cancelled_identity_retained", "exhaustion_admission_denied",
    "clock_scope", "phase_scope", "counters_before_final_quiescent_reset",
    "quiescent_hard_reset_checked"))


class EvidenceError(ValueError):
    def __init__(self, message, provenance):
        super().__init__(message)
        self.provenance = provenance


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _shape(value, fields, name):
    _require(type(value) is dict and set(value) == set(fields), name + " fields differ")


def _integer(value, name, minimum=0):
    _require(type(value) is int and minimum <= value <= 2**64 - 1,
             name + " must be a bounded integer")
    return value


def _vector(value, length, name):
    _require(type(value) is list and len(value) == length, name + " length differs")
    for item in value:
        _integer(item, name)
    return value


def _parse(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("nonfinite JSON value")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def _registry(registry):
    _shape(registry, ("schema", "source", "source_manifest_sha256", "changed_channel_sha256",
                      "fabric_sha256", "prepared_binaries", "interfaces", "artifacts"), "registry")
    _require(registry["schema"] == EVIDENCE_SCHEMA, "unknown registry schema")
    _require(registry["source"] == ACCEPTED_SOURCE, "accepted publication identity differs")
    _require(registry["source_manifest_sha256"] == SOURCE_MANIFEST and
             registry["changed_channel_sha256"] == CHANNEL_SHA256, "executed source differs")
    _require(registry["fabric_sha256"] == FABRIC_SHA256 and
             registry["prepared_binaries"] == PREPARED_BINARIES, "fabric/binary binding differs")
    _require(registry["interfaces"] == INTERFACES, "logical interface widths differ")
    for widths in registry["interfaces"].values():
        for value in widths.values():
            _integer(value, "interface width", 1)
    files = registry["artifacts"]
    _require(type(files) is dict and set(files) == {PREFIX + name for name in ARTIFACT_NAMES},
             "artifact set differs")
    total = 0
    for rel, item in files.items():
        _shape(item, ("bytes", "sha256"), "artifact binding")
        size = _integer(item["bytes"], "artifact bytes", 1)
        _require(size <= MAX_ARTIFACT_BYTES, "artifact exceeds size bound")
        _require(type(item["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", item["sha256"]),
                 "artifact SHA256 is invalid")
        _require(not PurePosixPath(rel).is_absolute() and ".." not in PurePosixPath(rel).parts,
                 "unsafe artifact path")
        total += size
    _require(total <= MAX_TOTAL_BYTES, "artifact bundle exceeds size bound")


def _channel(data, elapsed, name):
    _shape(data, CHANNEL_FIELDS, name)
    accepted = _vector(data["accepted"], 2, name + " accepted")
    delivered = _vector(data["delivered"], 2, name + " delivered")
    waits = _vector(data["arbitration_wait_cycles"], 2, name + " waits")
    for field in CHANNEL_FIELDS - {"accepted", "delivered", "arbitration_wait_cycles"}:
        _integer(data[field], name + "." + field)
    _require(sum(accepted) == data["backend_requests"] ==
             sum(delivered) + data["cancelled_responses"], name + " request ownership does not close")
    _require(data["backend_responses"] == sum(delivered) + data["cancelled_responses"] +
             data["orphan_responses"], name + " response ledger does not close")
    _require(all(a >= d for a, d in zip(accepted, delivered)), name + " client delivery exceeds ownership")
    _require(data["high_water"] == (1 if sum(accepted) else 0), name + " is not single-credit")
    _require(data["backend_requests"] <= data["occupied_cycles"] <= elapsed and
             max(waits) <= elapsed, name + " clocks exceed their enclosing batch")


def _native(data, profile):
    _shape(data, NATIVE_FIELDS, "native profile")
    _require(data["schema"] == "openrx.dataset-shared.native.v1" and
             data["profile"] == profile and data["status"] == "pass", "native profile identity differs")
    _vector(data["fixture_cases"], 2, "fixture case IDs")
    _vector(data["fixture_item_numbers"], 2, "fixture item numbers")
    _require(data["fixture_cases"] == [0, 1] and data["fixture_item_numbers"] == [0, 10000000],
             "native case IDs and item numbers differ")
    _require(data["mode_serial"] is profile.startswith("serial-") and
             data["mode_stalled"] is (profile.endswith("-stalled") or
                                      profile in ("cancel0", "cancel1", "malformed-fetch0")),
             "native service scenario differs")
    _require(data["clock_scope"] == "batch elapsed excludes first acceptance edge; client availability and phase vectors are nested and must not be added to it" and
             data["phase_scope"] == "pre-edge phases are sampled only after descriptor acceptance while the client is owned, stopping at post-edge result availability; session[3] and child item[9] sum to session availability including adapter launch, so child IDLE may include LAUNCH; core availability is separately one clock shorter; these source-specific bins are not the old full-hash observer vector",
             "source-specific clock/phase scope differs")
    for flag in ("quiescent_hard_reset_checked", "counters_before_final_quiescent_reset"):
        _require(data[flag] is True, "native reset/counter domain differs")
    for field in ("successful_items", "error_items", "aborted_items", "returned_items",
                  "commits", "multiplies", "stages"):
        _integer(data[field], field)
    elapsed = _integer(data["batch_elapsed_cycles"], "batch clocks", 1)
    for field in ("sessions_used", "client_availability_cycles", "client_core_cycles",
                  "client_executor_cycles", "client_held_backpressure_cycles"):
        _vector(data[field], 2, field)
    _shape(data["identity_collision_checks"], ("fetch", "cache"), "collision coverage")
    _require(all(type(x) is bool for x in data["identity_collision_checks"].values()),
             "collision coverage is not boolean")
    baseline = profile in PROFILES[:4]
    expected = (2, 0, 0, [1, 1]) if baseline else (
        (2, 0, 1, [2, 1] if profile == "cancel0" else [1, 2]) if profile in ("cancel0", "cancel1") else
        ((1, 1, 0, [1, 1]) if profile == "malformed-fetch0" else (6, 0, 0, [3, 3])))
    _require((data["successful_items"], data["error_items"], data["aborted_items"], data["sessions_used"])
             == expected, "native disposition/namespace budget differs")
    _require(data["returned_items"] == sum(expected[:2]), "returned items differ")
    _require(data["exhaustion_admission_denied"] is (profile == "exhaustion"), "exhaustion denial differs")
    _require(data["cancelled_identity_retained"] is (profile in ("cancel0", "cancel1")),
             "cancelled identity retention differs")
    if baseline or profile == "exhaustion":
        _require(all(data["identity_collision_checks"].values()), "full identity collision coverage absent")
    rows = data["item_rows"]
    _require(type(rows) is list and len(rows) == sum(expected[:3]), "native rows are incomplete")
    totals, namespaces = Counter(), [[], []]
    available, core, executor = [0, 0], [0, 0], [0, 0]
    common = {"client", "namespace", "status", "commits", "multiplies", "stages",
              "session_phase_cycles", "item_phase_cycles"}
    for row in rows:
        _require(type(row) is dict and row.get("status") in ("success", "error", "cancelled"),
                 "unknown native disposition")
        cancelled = row["status"] == "cancelled"
        _shape(row, common | ({"partial_elapsed_cycles"} if cancelled else
                             {"availability_cycles", "core_cycles", "executor_cycles"}), "item row")
        client = _integer(row["client"], "item client")
        _require(client in (0, 1), "unknown item client")
        namespace = _integer(row["namespace"], "namespace", 1)
        namespaces[client].append(namespace)
        status = row["status"]
        wanted = ("error" if client == 0 else "success") if profile == "malformed-fetch0" else (
            "cancelled" if profile in ("cancel0", "cancel1") and client == int(profile[-1]) and
            namespace == 1 else "success")
        _require(status == wanted, "wrong-client error/cancellation disposition")
        totals[status] += 1
        for field in ("commits", "multiplies", "stages"):
            totals[field] += _integer(row[field], field)
        work = row["commits"], row["multiplies"], row["stages"]
        if status == "success":
            _require(work == (3563, 1254, 8), "incomplete native successful item")
        elif status == "error":
            _require(work == (0, 0, 0), "owned first-fetch error did unexpected work")
        else:
            _require(work == (1, 1, 0), "cancelled row differs from the accepted partial prefix")
        if cancelled:
            latency = _integer(row["partial_elapsed_cycles"], "partial clocks", 1)
        else:
            latency = _integer(row["availability_cycles"], "availability", 1)
            child = _integer(row["core_cycles"], "core clocks")
            execute = _integer(row["executor_cycles"], "executor clocks")
            _require(child + 1 == latency and execute <= child, "native clock domains mixed")
            available[client] += latency; core[client] += child; executor[client] += execute
        _require(sum(_vector(row["session_phase_cycles"], 3, "session phases")) == latency and
                 sum(_vector(row["item_phase_cycles"], 9, "item phases")) == latency,
                 "nested phase clocks do not close")
        session = row["session_phase_cycles"]
        phases = row["item_phase_cycles"]
        _require(session == [0, 1, latency - 1], "session phase bins differ")
        _require([phases[i] for i in (0, 1, 2, 8)] == [1, 1, 33, 0],
                 "item IDLE/SEED_REQ/SEED_WAIT/RETURN bins differ")
        if status == "success":
            _require([phases[i] for i in (3, 5, 7)] == [8, 8, 8] and
                     phases[6] == (71 if data["mode_stalled"] else 16) and
                     phases[4] == row["executor_cycles"] + 8, "successful item phase bins differ")
        else:
            execute_wait = 8 if status == "error" else (44 if profile == "cancel0" else 52)
            _require(phases[3:8] == [1, execute_wait, 0, 0, 0], "partial/error item phase bins differ")
    _require([len(x) for x in namespaces] == expected[3] and
             all(x == list(range(1, len(x) + 1)) for x in namespaces),
             "namespace reused, skipped or refunded")
    _require((totals["success"], totals["error"], totals["cancelled"]) == expected[:3] and
             all(totals[f] == data[f] for f in ("commits", "multiplies", "stages")),
             "native work/disposition aggregate differs")
    _require((available, core, executor) == (data["client_availability_cycles"], data["client_core_cycles"],
                                           data["client_executor_cycles"]), "nested client aggregates differ")
    _require(max(available) <= elapsed, "client clocks were added to elapsed batch")
    for client, held in enumerate(data["client_held_backpressure_cycles"]):
        returns = sum(r["client"] == client and r["status"] != "cancelled" for r in rows)
        _require(held == 4 * returns <= elapsed, "source-specific held-result domain differs")
    for name in INTERFACES:
        _channel(data[name], elapsed, name)
    for client in (0, 1):
        client_rows = [r for r in rows if r["client"] == client]
        delivered_fetch = sum(r["commits"] + (1 if r["status"] == "error" else 0) for r in client_rows)
        delivered_cache = sum(r["stages"] for r in client_rows)
        cancelled_fetch = int(profile in ("cancel0", "cancel1") and client == int(profile[-1]))
        _require(data["fetch"]["delivered"][client] == delivered_fetch and
                 data["fetch"]["accepted"][client] == delivered_fetch + cancelled_fetch and
                 data["cache"]["accepted"][client] == data["cache"]["delivered"][client] == delivered_cache,
                 "client service traffic does not match completed/partial work")
    _require(data["fetch"]["cancelled_responses"] == int(profile in ("cancel0", "cancel1")) and
             data["cache"]["cancelled_responses"] == 0 and
             data["fetch"]["orphan_responses"] == data["cache"]["orphan_responses"] == 0,
             "native cancellation/orphan disposition differs")
    if baseline:
        _require((data["commits"], data["multiplies"], data["stages"]) == (7126, 2508, 16),
                 "native pair is incomplete")
        for name, count in (("fetch", 3563), ("cache", 8)):
            _require(data[name]["accepted"] == data[name]["delivered"] == [count, count] and
                     data[name]["cancelled_responses"] == data[name]["orphan_responses"] == 0,
                     "baseline service traffic differs")


def _protocol(data):
    _shape(data, {"schema", "status", "checks", "cycles", "counter_closure_checks", "fairness_pairs",
                  "identical_tag_pairs", "descriptor_hold_cycles", "response_hold_cycles", "early_reply_hold_cycles",
                  "same_edge_request_response_cases", "queued_cancel_cases", "issued_cancel_cases", "held_cancel_cases",
                  "foreign_owner_packets", "wrong_low_tag_packets", "idle_orphan_packets", "malformed_payload_forwarded",
                  "other_client_progress_cases", "nonowner_cancel_cases", "quiescent_reset_cases", "accepted_count",
                  "delivered_count", "arbitration_wait_cycles", "backend_request_count", "backend_response_count",
                  "cancelled_response_count", "orphan_response_count", "occupied_cycles", "high_water_mark",
                  "counter_snapshot_scope"}, "protocol")
    _require(type(data) is dict and data.get("schema") == "openrx.shared-dataset-channel-protocol.v1"
             and data.get("status") == "pass", "directed protocol identity differs")
    _require(data.get("counter_snapshot_scope") == "before_final_quiescent_reset", "protocol reset domain differs")
    for key, value in data.items():
        if key not in ("schema", "status", "counter_snapshot_scope", "accepted_count", "delivered_count",
                       "arbitration_wait_cycles"):
            _integer(value, key, 1)
    _require(data["checks"] == 2045 and data["counter_closure_checks"] == data["cycles"] == 91,
             "directed protocol coverage differs")
    channel = {"accepted": data["accepted_count"], "delivered": data["delivered_count"],
               "arbitration_wait_cycles": data["arbitration_wait_cycles"],
               "backend_requests": data["backend_request_count"],
               "backend_responses": data["backend_response_count"],
               "cancelled_responses": data["cancelled_response_count"],
               "orphan_responses": data["orphan_response_count"],
               "occupied_cycles": data["occupied_cycles"], "high_water": data["high_water_mark"]}
    _channel(channel, data["cycles"], "protocol")
    _require(data["fairness_pairs"] == data["identical_tag_pairs"] == 8 and
             channel["cancelled_responses"] == 3 and channel["orphan_responses"] == 4,
             "directed cancellation/orphan evidence absent")


def validate_evidence(registry, records):
    """Check semantics only. No byte identity or accepted attribution is granted."""
    _registry(registry)
    _require(type(records) is dict and set(records) == ARTIFACT_NAMES, "decoded artifact set differs")
    source = records["source-bindings.json"]
    _require(source.get("schema") == "openrx.dataset-shared.executed-source-bindings.v1" and
             source.get("prepared_manifest_sha256") == SOURCE_MANIFEST, "source binding differs")
    _require(source.get("changed_files") == ["rtl/dataset_shared/randomx_dataset_shared_channel.v"] and
             len(source.get("files", {})) == 15 and
             source["files"]["rtl/dataset_shared/randomx_dataset_shared_channel.v"]["sha256"] == CHANNEL_SHA256 and
             source["files"]["rtl/dataset_shared/randomx_dataset_shared_fabric.v"]["sha256"] == FABRIC_SHA256 and
             source.get("publication_parent_commit") == "5258f16a2f4425980fe2cb744e570e00fc546512" and
             source.get("physical_acceptance") is False,
             "executed source scope differs")
    for stage, (execution, commands, artifacts, classification) in STAGES.items():
        verify = records[stage + "/verification-summary.json"]
        review = records[stage + "/independent-result-review.json"]
        summary = records[stage + "/public-summary.json"]
        _require(verify.get("source_manifest_sha256") == SOURCE_MANIFEST and
                 verify.get("changed_channel_sha256") == CHANNEL_SHA256 and
                 review.get("source_manifest_sha256") == SOURCE_MANIFEST and
                 review.get("tested_channel_sha256") == CHANNEL_SHA256, "mixed executed source")
        _require(verify.get("execution_id") == review.get("execution_id") == execution and
                 source["executions"].get(stage) == execution, "mixed stage execution")
        _require(verify.get("actual_commands") == commands and verify.get("receipt_artifact_count") == artifacts
                 and verify.get("all_command_returncodes_zero") is True, "partial stage")
        _require(verify.get("root_integrity_verified") is True and verify.get("actual_kernel_safe") is True
                 and verify.get("production_enforced") is True, "stage enforcement/integrity absent")
        _require(verify.get("raw_status") == review.get("process_status") == "PROCESS_EXITED" and
                 verify.get("raw_scientific_acceptance") == review.get("raw_receipt_scientific_acceptance") == "unverified"
                 and summary.get("scientific_acceptance") == "unverified_pending_independent_review",
                 "raw scientific classifications changed")
        _require(verify.get("independent_acceptance") == review.get("independent_classification") == classification,
                 "independent scoped acceptance differs")
        _require(verify.get("receipt_sha256") == review.get("receipt_sha256") and
                 verify.get("request_sha256") == review.get("request_sha256"), "receipt/request identity differs")
        bound_review = registry["artifacts"][PREFIX + stage + "/independent-result-review.json"]["sha256"]
        _require(verify.get("independent_review_sha256") == bound_review, "review binding differs")
        _require(summary.get("phase") == stage and summary.get("status") == "pass_" + stage and
                 summary.get("source_unchanged") is True and summary.get("fixtures_unchanged") is True and
                 summary.get("workers_requested") == 1 and summary.get("command_timeout_seconds") == 120,
                 "summary execution scope differs")
        _require(summary.get("new_full_hash_executed") is False and
                 summary.get("native_reference_or_cache_regenerated") is False and
                 summary.get("demonstrated_asic_feasibility") is False, "workload/physical scope differs")
        _require(type(summary.get("commands")) is list and len(summary["commands"]) == commands and
                 all(c.get("returncode") == 0 and c.get("timeout_or_signal_exit") is False
                     for c in summary["commands"]), "failed or skipped command")
    prefix_verify = records["prefix/verification-summary.json"]
    _require(prefix_verify.get("same_source_new_binaries") == PREPARED_BINARIES, "prepared binary identity differs")
    matrix_reuse = records["matrix/independent-result-review.json"]["reuse"]
    synth_reuse = records["synthesis/independent-result-review.json"]["reuse_and_stage_admission"]
    _require(matrix_reuse.get("execution_id") == synth_reuse.get("new_prefix_execution_id") == STAGES["prefix"][0]
             and matrix_reuse.get("receipt_sha256") == synth_reuse.get("new_prefix_receipt_sha256") == prefix_verify["receipt_sha256"]
             and matrix_reuse.get("root_verify_sha256") == synth_reuse.get("new_prefix_root_verify_sha256") == prefix_verify["root_verify_sha256"],
             "old or mismatched prefix reuse")
    _require(matrix_reuse.get("native_binary_sha256") == prefix_verify["same_source_new_binaries"]["native.vvp"] and
             matrix_reuse.get("only_new_same_source_prefix_binary_used_for_all_seven_profiles") is True and
             matrix_reuse.get("old_prefix_or_old_binaries_used_as_recovery_source_acceptance") is False and
             synth_reuse.get("only_new_same_source_prefix_reused") is True and
             synth_reuse.get("historical_old_source_acceptance_or_binaries_transferred") is False,
             "source acceptance/binary reuse differs")
    _require(synth_reuse.get("new_matrix_execution_id") == STAGES["matrix"][0] and
             synth_reuse.get("new_matrix_receipt_sha256") == records["matrix/verification-summary.json"]["receipt_sha256"] and
             synth_reuse.get("both_current_independent_prior_stage_acceptances_preceded_synthesis_admission") is True,
             "conditional stage admission differs")
    protocol = records["prefix/protocol.json"]
    _protocol(protocol)
    profiles = {name: records[("prefix" if name == "concurrent-ideal" else "matrix") +
                              "/native-" + name + ".json"] for name in PROFILES}
    for name, profile in profiles.items():
        _native(profile, name)
    _require(records["prefix/public-summary.json"].get("protocol") == protocol and
             records["prefix/public-summary.json"].get("native", {}).get("concurrent-ideal") == profiles["concurrent-ideal"] and
             records["matrix/public-summary.json"].get("native") == profiles, "summary/results disagree")
    _require(records["synthesis/mapped-protocol.json"] == protocol and
             records["synthesis/mapped-native-concurrent-ideal.json"] == profiles["concurrent-ideal"] and
             records["synthesis/public-summary.json"].get("mapped_protocol") == protocol and
             records["synthesis/public-summary.json"].get("mapped_native") == profiles["concurrent-ideal"] and
             records["synthesis/public-summary.json"].get("mapped_parity_byte_exact") ==
             {"protocol": True, "native_concurrent_ideal": True},
             "mapped/native results disagree")
    _require(registry["artifacts"][PREFIX + "prefix/protocol.json"]["sha256"] ==
             registry["artifacts"][PREFIX + "synthesis/mapped-protocol.json"]["sha256"] and
             registry["artifacts"][PREFIX + "prefix/native-concurrent-ideal.json"]["sha256"] ==
             registry["artifacts"][PREFIX + "synthesis/mapped-native-concurrent-ideal.json"]["sha256"],
             "mapped files are not byte-identical")
    mapping = records["synthesis/mapping-statistics.json"]
    _require(mapping.get("source_manifest_sha256") == SOURCE_MANIFEST and
             mapping.get("physical_acceptance") is False, "mapping source/physical scope differs")
    for name, expected in (("channel", (6581, 801)), ("fabric", (14498, 1615))):
        item = mapping["mapping"][name]
        for field in ("generic_cells", "DFF_cells", "latch_cells"):
            _integer(item[field], field)
        counts = item["by_cell_type"]
        _require(type(counts) is dict, "cell counts missing")
        for count in counts.values():
            _integer(count, "cell count")
        _require(sum(counts.values()) == item["generic_cells"] == expected[0] and
                 sum(v for k, v in counts.items() if "DFF" in k) == item["DFF_cells"] == expected[1] and
                 item["latch_cells"] == sum(v for k, v in counts.items() if "LATCH" in k) == 0,
                 "generic cell scope/counts differ")
    stages = {name: {key: records[name + "/verification-summary.json"][key]
                     for key in ("execution_id", "receipt_sha256", "raw_status", "raw_scientific_acceptance",
                                 "raw_driver_scientific_acceptance", "independent_acceptance",
                                 "independent_review_sha256")} for name in STAGES}
    return {"profiles": profiles, "protocol": protocol, "mapping": mapping["mapping"], "stages": stages}


def _load_bound(registry_path, artifact_root):
    provenance = {"schema": "openrx.architecture.finite-fabric-provenance.v1",
                  "identity_status": "untrusted_input", "actual_registry_sha256": None,
                  "trusted_registry_sha256": TRUSTED_REGISTRY_SHA256,
                  "accepted_source": None, "actual_artifact_sha256": {}, "physical_measurement": False}
    try:
        with Path(registry_path).open("rb") as stream:
            raw = stream.read(MAX_REGISTRY_BYTES + 1)
        _require(len(raw) <= MAX_REGISTRY_BYTES, "registry exceeds size bound")
        provenance["actual_registry_sha256"] = hashlib.sha256(raw).hexdigest()
        _require(provenance["actual_registry_sha256"] == TRUSTED_REGISTRY_SHA256,
                 "untrusted input: actual registry bytes differ")
        registry = _parse(raw)
        _registry(registry)
        root = Path(artifact_root).resolve(strict=True)
        records, total = {}, 0
        for rel, info in sorted(registry["artifacts"].items()):
            path = (root / rel).resolve(strict=True)
            _require(path.is_relative_to(root), "artifact escapes root")
            with path.open("rb") as stream:
                content = stream.read(MAX_ARTIFACT_BYTES + 1)
            _require(len(content) == info["bytes"] <= MAX_ARTIFACT_BYTES, "artifact size differs")
            total += len(content)
            _require(total <= MAX_TOTAL_BYTES, "artifact bundle exceeds size bound")
            actual = hashlib.sha256(content).hexdigest()
            provenance["actual_artifact_sha256"][rel] = actual
            _require(actual == info["sha256"], "untrusted input: actual artifact bytes differ")
            records[rel[len(PREFIX):]] = _parse(content)
        facts = validate_evidence(registry, records)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        message = "cannot read bound input" if isinstance(exc, OSError) else str(exc)
        raise EvidenceError(message, provenance) from exc
    provenance["identity_status"] = "accepted_input_verified"
    provenance["accepted_source"] = dict(ACCEPTED_SOURCE)
    return facts, provenance


def _fraction(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator}


def _derive_report(facts, provenance):
    rows = {}
    for name, profile in facts["profiles"].items():
        elapsed = profile["batch_elapsed_cycles"]
        links = {}
        for link, widths in INTERFACES.items():
            channel = profile[link]
            tag = widths["client_tag_bits"] + widths["backend_client_id_bits"]
            request, response = tag + widths["request_payload_bits"], tag + widths["response_payload_bits"]
            links[link] = {"request_descriptor_bits": request, "response_descriptor_bits": response,
                           "request_descriptor_bits_per_batch": request * channel["backend_requests"],
                           "response_descriptor_bits_per_batch": response * channel["backend_responses"],
                           "backend_requests": channel["backend_requests"], "backend_responses": channel["backend_responses"],
                           "cancelled_responses": channel["cancelled_responses"], "orphan_responses": channel["orphan_responses"],
                           "accepted_by_client": channel["accepted"], "delivered_by_client": channel["delivered"],
                           "arbitration_wait_cycles_by_client": channel["arbitration_wait_cycles"],
                           "aggregate_owner_credit_high_water": channel["high_water"],
                           "request_rate_per_observed_batch_clock": _fraction(channel["backend_requests"], elapsed),
                           "owner_credit_occupied_fraction": _fraction(channel["occupied_cycles"], elapsed),
                           "owner_credit_occupied_clocks_per_request": _fraction(channel["occupied_cycles"], channel["backend_requests"]),
                           "physical_offchip_traffic_bits": None, "characterized_physical_service_latency_seconds": None}
        rows[name] = {"batch_elapsed_cycles": elapsed, "item_rows": profile["item_rows"],
                      "clock_scope": profile["clock_scope"], "phase_scope": profile["phase_scope"],
                      "successful_items": profile["successful_items"], "error_items": profile["error_items"],
                      "aborted_items": profile["aborted_items"], "sessions_used": profile["sessions_used"],
                      "client_availability_nested_cycles": profile["client_availability_cycles"],
                      "client_held_nested_cycles": profile["client_held_backpressure_cycles"], "interfaces": links}
    ratios = {mode: {"serial_batch_cycles": rows["serial-" + mode]["batch_elapsed_cycles"],
                     "concurrent_batch_cycles": rows["concurrent-" + mode]["batch_elapsed_cycles"],
                     "observed_two_item_batch_ratio": _fraction(rows["serial-" + mode]["batch_elapsed_cycles"],
                                                                rows["concurrent-" + mode]["batch_elapsed_cycles"])}
              for mode in ("ideal", "stalled")}
    return {"schema": REPORT_SCHEMA, "classification": "accepted_bounded_component_transport_observations",
            "provenance": provenance, "dataset_item_clients": 2, "distinct_native_item_numbers": [0, 10000000],
            "vm_contexts_validated": False, "independent_vm_scratchpads_validated": 0,
            "interface_width_source": {"path": "rtl/dataset_shared/randomx_dataset_shared_fabric.v",
                                       "sha256": FABRIC_SHA256, "public_head": ACCEPTED_SOURCE["public_head"]},
            "routing_correctness_attribution": "Pinned RTL/testbench assertions and accepted independent reviews; aggregate counters alone are not packet-level proof.",
            "interfaces": INTERFACES, "profiles": rows, "observed_batch_comparisons": ratios,
            "accepted_stage_attribution": facts["stages"],
            "protocol_coverage": facts["protocol"], "generic_mapping_separate_scopes": facts["mapping"],
            "scope_notes": ["Descriptor widths exclude ready/valid/cancel/diagnostic wires; no byte rounding or physical encoding is assumed.",
                            "Distinct links and nested client/channel clocks are not added as physical traffic or wall time.",
                            "Credit ownership includes protocol/held time and is not provider-only latency.",
                            "Two prepared dataset items are not two complete VM contexts or a full-hash workload.",
                            "Standalone channel is contained in fabric; generic diagnostics/payload counts are not physical area."],
            "physical_service_gates": {name: envelope.rejection_gate() for name in INTERFACES},
            "achieved_hashes_per_second": None, "alternative_full_hash_cycles": None,
            "physical_frequency_hz": None, "physical_wall_power_w": None,
            "aggregate_physical_offchip_bits_per_hash": None, "engine_count_selected": None,
            "demonstrated_asic_feasibility": False, "full_hash_projection_performed": False,
            "legacy_full_hash_evidence_modified": False}


def build_report(evidence_path, *, artifact_root=ROOT):
    facts, provenance = _load_bound(evidence_path, artifact_root)
    return _derive_report(facts, provenance)


def _dump(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def run(evidence_path, output_directory, *, artifact_root=ROOT):
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = build_report(evidence_path, artifact_root=artifact_root)
    except EvidenceError as exc:
        _dump(output / "provenance.json", exc.provenance)
        raise
    _dump(output / "provenance.json", report["provenance"])
    _dump(output / "finite-fabric-service-profile.json", report)
    index = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    _dump(output / "artifacts.sha256.json", index)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.evidence, args.output)
    print(json.dumps({"status": "analytical_component_only", "identity_status": "accepted_input_verified",
                      "report": "finite-fabric-service-profile.json", "physical_feasibility": "unresolved"}))


if __name__ == "__main__":
    main()
