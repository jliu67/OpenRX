"""Bound hardware-dataset service demands, not physical performance predictions.

The reviewed compact fixture is a projection of an accepted modeled full hash.
The old PR74 evidence, fixtures and scheduler remain separate. Only actual file
bytes matching the independent trusted binding receive accepted attribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import envelope


ACCEPTED_EVIDENCE_SHA256 = "fb6a6302dd6c57e835515c9e23ad39e2462e41885dc92bc49b48b056e0e96130"
EVIDENCE_SCHEMA = "openrx.architecture.hardware-dataset-evidence.v1"
ACCEPTED_SOURCE = {
    "public_head": "e8277c63504ef035bb82791263b6842c0cc51f51",
    "public_tree": "cb3e0615f9df861a081ba2cbb1d47c65603b84cd",
    "acceptance_review_url": "https://github.com/jliu67/OpenRX/pull/86#pullrequestreview-5588318967",
}
MAX_EVIDENCE_BYTES = 65536
STAGES = frozenset((
    "initialization_hardware_fill", "program_generation", "input_hash",
    "control_and_metadata", "program_preparation", "execution",
    "interprogram_seed", "finalization", "held_return",
))
DATASET_FIELDS = frozenset((
    "demands", "responses", "items", "item_returns", "stages", "retirements",
    "cache_requests", "cache_responses", "instruction_requests", "instruction_responses",
    "item_availability_clocks", "core_item_availability_clocks", "executor_clocks",
    "session_launch_extra_clocks", "service_phase_cycles", "session_phase_cycles",
    "item_phase_cycles", "program_service_extra_clocks", "cache_service_extra_clocks",
))


class EvidenceError(ValueError):
    """Failed input with provenance that the CLI can preserve without a report."""

    def __init__(self, message, provenance):
        super().__init__(message)
        self.provenance = provenance


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _fields(value, keys, name):
    _require(type(value) is dict and set(value) == set(keys),
             f"{name} must contain exactly the declared fields")


def _integer(value, name, minimum=0):
    _require(type(value) is int and value >= minimum,
             f"{name} must be an integer >= {minimum}")


def _vector(value, length, name):
    _require(type(value) is list and len(value) == length,
             f"{name} must contain exactly {length} counters")
    for item in value:
        _integer(item, name)


def _equal(actual, expected, name):
    _require(actual == expected, f"{name} does not match the accepted-profile relationship")


def validate_evidence(data):
    """Check counter semantics only; this function grants no input attribution."""
    _fields(data, ("schema", "source", "workload", "functional", "ledger", "dataset", "preparation"), "evidence")
    _equal(data["schema"], EVIDENCE_SCHEMA, "schema")
    _fields(data["source"], ACCEPTED_SOURCE, "source")
    _equal(data["source"], ACCEPTED_SOURCE, "source")

    workload = data["workload"]
    _fields(workload, ("programs", "iterations_per_program", "scratchpad_bytes"), "workload")
    for name, value in workload.items():
        _integer(value, "workload." + name, 1)
    _equal(workload, {"programs": 8, "iterations_per_program": 2048, "scratchpad_bytes": 2097152}, "workload")
    iterations = workload["programs"] * workload["iterations_per_program"]

    functional = data["functional"]
    _fields(functional, ("native_digest_equal", "full_scratchpad_boundaries", "hardware_seed_transitions", "live_software_provider_calls"), "functional")
    _require(functional["native_digest_equal"] is True, "native digest equality must be true")
    for name in ("full_scratchpad_boundaries", "hardware_seed_transitions"):
        _integer(functional[name], "functional." + name)
    _equal(functional["full_scratchpad_boundaries"], workload["programs"], "scratchpad boundaries")
    _equal(functional["hardware_seed_transitions"], workload["programs"] - 1, "seed transitions")
    providers = functional["live_software_provider_calls"]
    _fields(providers, ("input", "fill", "program", "dataset"), "live software providers")
    for name, value in providers.items():
        _integer(value, "live_software_provider_calls." + name)
        _equal(value, 0, "live software provider " + name)

    preparation = data["preparation"]
    _fields(preparation, ("cache_bytes", "program_slots", "instructions_per_program_capacity",
                          "instruction_word_bytes", "reciprocal_count", "reciprocal_word_bytes"), "preparation")
    for name, value in preparation.items():
        _integer(value, "preparation." + name, 0 if name == "reciprocal_count" else 1)
    for name, value in (("cache_bytes", 268435456), ("program_slots", 8),
                        ("instructions_per_program_capacity", 512),
                        ("instruction_word_bytes", 8), ("reciprocal_word_bytes", 8)):
        _equal(preparation[name], value, "preparation." + name)
    _require(preparation["reciprocal_count"] <= 0xffffffff, "reciprocal count exceeds the interface")

    ledger = data["ledger"]
    _fields(ledger, ("outer_cycles", "stage_cycles", "nested_iteration_phases", "nested_executor_phases"), "ledger")
    _integer(ledger["outer_cycles"], "outer_cycles", 1)
    _fields(ledger["stage_cycles"], STAGES, "stage_cycles")
    for name, value in ledger["stage_cycles"].items():
        _integer(value, "stage_cycles." + name)
    _vector(ledger["nested_iteration_phases"], 12, "nested_iteration_phases")
    _vector(ledger["nested_executor_phases"], 18, "nested_executor_phases")
    outer, stages = ledger["outer_cycles"], ledger["stage_cycles"]
    iteration, vm_executor = ledger["nested_iteration_phases"], ledger["nested_executor_phases"]
    _equal(sum(stages.values()), outer, "outer/stage closure")
    _equal(sum(iteration), stages["execution"], "execution/iteration closure")
    _equal(sum(vm_executor), iteration[7], "VM executor/iteration closure")
    for index, value in ((0, iterations), (1, 4 * iterations), (2, 4 * iterations),
                         (3, 4 * iterations), (4, 4 * iterations), (5, 0),
                         (6, iterations), (8, iterations), (10, iterations), (11, 9 * iterations)):
        _equal(iteration[index], value, "ideal iteration phase " + str(index))

    dataset = data["dataset"]
    _fields(dataset, DATASET_FIELDS, "dataset")
    for name in DATASET_FIELDS - {"service_phase_cycles", "session_phase_cycles", "item_phase_cycles"}:
        _integer(dataset[name], "dataset." + name)
    for name, length in (("service_phase_cycles", 3), ("session_phase_cycles", 3), ("item_phase_cycles", 9)):
        _vector(dataset[name], length, "dataset." + name)
    for name in ("demands", "responses", "items", "item_returns", "session_launch_extra_clocks"):
        _equal(dataset[name], iterations, "dataset." + name)
    for name in ("program_service_extra_clocks", "cache_service_extra_clocks"):
        _equal(dataset[name], 0, "ideal dataset." + name)
    _equal(dataset["stages"], iterations * preparation["program_slots"], "dataset stages")
    for name in ("cache_requests", "cache_responses"):
        _equal(dataset[name], dataset["stages"], "dataset." + name)
    for name in ("instruction_requests", "instruction_responses"):
        _equal(dataset[name], dataset["retirements"], "dataset." + name)
    _require(dataset["retirements"] > 0 and dataset["retirements"] % iterations == 0,
             "dataset retirements must be complete repeated prepared programs")
    instructions_per_item = dataset["retirements"] // iterations
    _require(instructions_per_item <= preparation["program_slots"] * preparation["instructions_per_program_capacity"],
             "prepared instruction count exceeds image capacity")

    availability = dataset["item_availability_clocks"]
    _equal(dataset["core_item_availability_clocks"] + dataset["session_launch_extra_clocks"],
           availability, "core plus session launch")
    _equal(sum(dataset["item_phase_cycles"]), availability, "item phase/availability closure")
    _require(0 < dataset["executor_clocks"] <= dataset["core_item_availability_clocks"] <= availability <= stages["execution"] <= outer,
             "dataset clock nesting is invalid")
    _equal(iteration[9], availability + dataset["responses"], "dataset iteration reply wait")
    service, session, item = (dataset[name] for name in ("service_phase_cycles", "session_phase_cycles", "item_phase_cycles"))
    _equal(sum(service), stages["execution"], "service/execution closure")
    _equal(sum(session), stages["execution"], "session/execution closure")
    _equal(service, [stages["execution"] - iteration[9], iteration[9], 0], "service phase vector")
    _equal(session, [service[0], dataset["session_launch_extra_clocks"], availability], "session phase vector")
    _equal(item, [0, iterations, 33 * iterations, dataset["stages"],
                  dataset["executor_clocks"] + dataset["stages"], dataset["stages"],
                  dataset["stages"], dataset["stages"], iterations], "item phase vector")
    return {"iterations": iterations, "prepared_instructions_per_item": instructions_per_item}


def _parse_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON field")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("nonfinite JSON value")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def _load_bound(path):
    path = Path(path)
    provenance = {"schema": "openrx.architecture.hardware-dataset-provenance.v1",
                  "identity_status": "untrusted_input", "actual_input_sha256": None,
                  "trusted_input_sha256": ACCEPTED_EVIDENCE_SHA256,
                  "trusted_binding_source": "reviewed_public_hardware_dataset_fixture",
                  "accepted_source": None, "physical_measurement": False}
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_EVIDENCE_BYTES + 1)
        _require(len(raw) <= MAX_EVIDENCE_BYTES, "compact evidence size limit exceeded")
        provenance["actual_input_sha256"] = hashlib.sha256(raw).hexdigest()
        provenance["input_bytes"] = len(raw)
        _require(provenance["actual_input_sha256"] == ACCEPTED_EVIDENCE_SHA256,
                 "untrusted input: actual evidence bytes differ from the trusted binding")
        data = _parse_json(raw)
        validate_evidence(data)
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceError(str(exc), provenance) from exc
    provenance["identity_status"] = "accepted_input_verified"
    provenance["accepted_source"] = dict(ACCEPTED_SOURCE)
    return data, provenance


def _derive_report(data, provenance):
    ledger, dataset, preparation = (data[name] for name in ("ledger", "dataset", "preparation"))
    target = envelope.TARGET_HPS
    interfaces = {}
    for name, responses, width, scope in (
        ("vm_dataset_response", dataset["responses"], 64, "Logical dataset item output to the VM; not an extra physical-cache read."),
        ("prepared_cache_response", dataset["cache_responses"], 64, "Cache-line data on the prepared service interface; cache placement/reuse and physical traffic are unknown."),
        ("prepared_instruction_response", dataset["instruction_responses"], 8, "Minimum raw 64-bit instruction words only; replies also bundle optional reciprocal fields and transport metadata."),
    ):
        payload = responses * width
        interfaces[name] = {
            "responses_per_hash": responses, "minimum_data_payload_bytes_per_response": width,
            "minimum_data_payload_bytes_per_hash": payload,
            "required_responses_per_second_at_target": responses * target,
            "minimum_data_payload_bytes_per_second_at_target": payload * target,
            "payload_scope": scope, "physical_offchip_bytes_per_hash": None,
            "wire_bytes_per_hash": None, "characterized_service_latency_seconds": None,
            "characterized_sustainable_responses_per_second": None,
            "characterized_energy_j_per_hash": None,
        }
    latency_sweep = []
    for name, service in interfaces.items():
        for latency_ns in (1, 10, 100, 300):
            for ready in (1, 2, 4):
                latency_sweep.append({"interface": name, "assumed_response_latency_ns": latency_ns,
                    **envelope.latency_requirement(target, service["responses_per_hash"], latency_ns * 1e-9, ready),
                    "readiness_is_assumed_not_established_by_issue_width": True})
    gates = {name: envelope.rejection_gate(
        required_bandwidth=service["minimum_data_payload_bytes_per_second_at_target"],
        required_transactions_per_s=service["required_responses_per_second_at_target"])
        for name, service in interfaces.items()}
    return {
        "schema": "openrx.architecture.hardware-dataset-service-demand.v1",
        "classification": "accepted_modeled_service_counts_and_necessary_conditional_bounds",
        "provenance": provenance, "target_hashes_per_second": target,
        "achieved_hashes_per_second": None, "alternative_full_hash_cycles": None,
        "physical_frequency_hz": None, "physical_wall_power_w": None,
        "demonstrated_asic_feasibility": False,
        "modeled_clock_ledger": {
            "outer_baseline_cycles": ledger["outer_cycles"],
            "stage_cycles": ledger["stage_cycles"],
            "vm_executor_nested_cycles": sum(ledger["nested_executor_phases"]),
            "dataset_availability_nested_cycles": dataset["item_availability_clocks"],
            "dataset_core_nested_cycles": dataset["core_item_availability_clocks"],
            "dataset_executor_nested_cycles": dataset["executor_clocks"],
            "session_launch_nested_cycles": dataset["session_launch_extra_clocks"],
            "dataset_costs_added_to_outer_twice": False,
            "classification": "modeled_baseline_clocks_not_a_physical_frequency_measurement",
        },
        "interfaces": interfaces,
        "aggregate_physical_offchip_bytes_per_hash": None,
        "independent_link_payloads_must_not_be_summed_as_offchip_traffic": True,
        "reciprocal_transport": {
            "separate_logical_request_interface": False,
            "response_fields": "instruction replies bundle reciprocal valid, 32-bit index and 64-bit value",
            "independent_physical_transactions_per_hash": None,
            "additional_wire_bytes_per_hash": None,
            "table_entries_are_not_request_counts": True,
        },
        "retained_preparation": {
            "cache_image_bytes": preparation["cache_bytes"],
            "prepared_instruction_capacity_bytes": preparation["program_slots"] * preparation["instructions_per_program_capacity"] * preparation["instruction_word_bytes"],
            "reciprocal_table_data_bytes": preparation["reciprocal_count"] * preparation["reciprocal_word_bytes"],
            "mutable_scratchpad_bytes_per_context": data["workload"]["scratchpad_bytes"],
            "metadata_ecc_queues_physical_macro_overhead_bytes": None,
            "autonomous_preparation_validated": False,
        },
        "latency_sweep": latency_sweep, "physical_service_gates": gates,
        "strict_wall_energy_ceiling_j_per_hash": envelope.WALL_LIMIT_W / target,
        "power": envelope.full_wall_power(target, {}, {}, None, None),
        "complete_machine_gate": envelope.rejection_gate(),
        "assumptions": [
            "The requested throughput is a target, never an achieved rate.",
            "Latency and independent ready requests per context are scenario inputs, not characterized service or demonstrated overlap.",
            "Cache/program placement, reuse, bank mapping, controller timing/refresh/tails, wire overhead and energy are uncharacterized.",
            "Per-interface payloads describe distinct nested links; no aggregate off-chip traffic is inferred.",
            "VM bytecode windows and their prior scheduler results remain separate; no full-hash speedup is inferred.",
            "Earlier failed runs and historical scientific flags retain their original status.",
        ],
    }


def build_report(evidence_path):
    """Read and bind actual fixture bytes before deriving any accepted report."""
    data, provenance = _load_bound(evidence_path)
    return _derive_report(data, provenance)


def _dump(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def run(evidence_path, output_directory):
    """Create a new result directory; failures retain provenance, never a report."""
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    try:
        report = build_report(evidence_path)
    except EvidenceError as exc:
        _dump(output / "provenance.json", exc.provenance)
        raise
    _dump(output / "provenance.json", report["provenance"])
    _dump(output / "service-demand.json", report)
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(output.iterdir()) if p.is_file()}
    _dump(output / "artifacts.sha256.json", files)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.evidence, args.output)
    print(json.dumps({"status": "analytical_only", "identity_status": "accepted_input_verified",
                      "report": "service-demand.json", "physical_feasibility": "unresolved"}))


if __name__ == "__main__":
    main()
