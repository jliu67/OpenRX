#!/usr/bin/env python3
"""Validate retained CACTI 6.5 outputs for one conditional SRAM experiment.

This adapter never launches CACTI or gem5. Its outputs are conditional model
observations, not characterized hardware, accepted RTL timing, or wall power.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path, PurePosixPath


SCHEMA = "openrx.conditional-memory-baseline.v1"
HARDWARE_DEMAND_SHA256 = "694b153e2220218c95c84579dfba930707abb439fa1cadce4d42195148f7c42a"
FINITE_FABRIC_SHA256 = "d6baa3de036273b1ac3918ffb5c3418b98f0130acdb43652380c06648eea81ce"
FETCHES_PER_HASH = 58_376_192
TARGET_HASHES_PER_SECOND = 1_000_000
PARTITION = {"Ndwl": 2, "Ndbl": 2, "Nspd": 1, "Ndcm": 1,
             "Ndsam_level_1": 2, "Ndsam_level_2": 1}
CSV_HEADERS = (
    "Tech node (nm)", "Capacity (bytes)", "Number of banks", "Associativity",
    "Output width (bits)", "Access time (ns)", "Random cycle time (ns)",
    "Dynamic search energy (nJ)", "Dynamic read energy (nJ)",
    "Dynamic write energy (nJ)", "Standby leakage per bank(mW)", "Area (mm2)",
    "Ndwl", "Ndbl", "Nspd", "Ndcm", "Ndsam_level_1", "Ndsam_level_2",
    "Data arrary area efficiency %", "Ntwl", "Ntbl", "Ntspd", "Ntcm",
    "Ntsam_level_1", "Ntsam_level_2", "Tag arrary area efficiency %",
)
BANNER = "---------- CACTI version 6.5, Uniform Cache Access SRAM Model ----------"
BAD_OUTPUT = re.compile(r"\b(?:error|invalid|nan|inf(?:inity)?)\b|could not", re.I)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MAX_SOURCE_FILES = 128
MAX_SOURCE_BYTES = 8 * 1024 * 1024
CASE_LIMITS = {"input.cfg": 32768, "stdout.txt": 1024 * 1024,
               "stderr.txt": 65536, "out.csv": 65536, "status.json": 65536}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_):
        raise ValueError("nonfinite JSON number")

    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def integer(value, minimum=0):
    require(type(value) is int and value >= minimum, "expected bounded integer")
    return value


def finite(value, positive=False):
    require(not isinstance(value, bool), "boolean is not numeric")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid model number") from exc
    require(math.isfinite(number), "nonfinite model number")
    require(number > 0 if positive else number >= 0, "invalid model number sign")
    return number


def safe_relative(name):
    require(type(name) is str and name != "", "empty relative path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and all(p not in ("", ".", "..") for p in path.parts)
            and str(path) == name and "\\" not in name,
            "unsafe relative path")
    return path


def read_file(root, name, limit):
    rel = safe_relative(name)
    root = Path(root).resolve(strict=True)
    current = root
    for part in rel.parts:
        current = current / part
        require(not current.is_symlink(), "symlink input forbidden")
    path = current.resolve(strict=True)
    require(root in path.parents and path.is_file(), "input escapes root")
    require(path.stat().st_size <= limit, "input too large")
    data = path.read_bytes()
    require(len(data) <= limit, "input grew beyond bound")
    return data


def validate_contract(contract):
    require(type(contract) is dict and contract.get("schema") == SCHEMA,
            "unsupported contract")
    require(contract.get("status") == "UNRUN_CONDITIONAL_CANDIDATE",
            "contract must retain preparation status")
    expected_model = {"node_nm": 45, "voltage_v": 1.0, "temperature_k": 360,
                      "cell_type": "itrs-hp", "peripheral_type": "itrs-hp",
                      "foundry_corner": None, "physical_characterization": False}
    model = contract.get("model", {})
    for key, value in expected_model.items():
        require(key in model and model[key] == value, "unexpected model assumption: " + key)
    for key in ("node_nm", "temperature_k"):
        integer(model[key], 1)
    require(type(model["voltage_v"]) in (int, float), "invalid voltage type")
    require(model["physical_characterization"] is False, "physical claim forbidden")
    expected_org = {"capacity_bytes": 131072, "rows": 4096, "row_bits": 256,
                    "stored_content_bits": 161, "padding_bits": 95,
                    "echo_bits": 29, "tag_owner_bits": 65,
                    "rw_ports_per_bank": 1, "global_credits": 1,
                    "modeled_reads_per_fetch": 1, "ecc": False}
    org = contract.get("organization", {})
    for key, value in expected_org.items():
        require(key in org and org[key] == value, "unexpected organization: " + key)
        if key != "ecc":
            integer(org[key], 1)
    require(org["ecc"] is False, "ECC changes storage and demand")
    require(org["rows"] * org["row_bits"] == org["capacity_bytes"] * 8,
            "row capacity mismatch")
    require(org["stored_content_bits"] + org["padding_bits"] == org["row_bits"],
            "record packing mismatch")
    for key in ("exclusive_read_ports", "exclusive_write_ports", "single_ended_ports"):
        require(type(org.get(key)) is int and org[key] == 0, "extra memory port")
    require(org.get("partition") == {"Ndwl": 2, "Ndbl": 2, "Nspd": 1,
                                      "Ndcm": 1, "Ndsam1": 2, "Ndsam2": 1},
            "changed forced organization")
    cases = contract.get("cases")
    require(type(cases) is list and len(cases) == 2, "exactly two cases required")
    for case, name, banks in zip(cases, ("bank1", "bank4"), (1, 4)):
        require(type(case) is dict and case.get("name") == name and
                type(case.get("banks")) is int and case["banks"] == banks,
                "case identity mismatch")
        require(type(case.get("input_sha256")) is str and
                SHA256.fullmatch(case["input_sha256"]) is not None,
                "invalid config digest")
        integer(case.get("input_bytes"), 1)
        require(case["input_bytes"] <= CASE_LIMITS["input.cfg"], "config too large")
        echoes = case.get("expected_input_echo")
        require(type(echoes) is dict and bool(echoes), "missing input echo contract")
        for key, value in expected_echo(banks).items():
            require(key in echoes and echoes[key] == value, "incomplete input echo contract")
    source_files = contract.get("source_files")
    require(type(source_files) is dict and 0 < len(source_files) <= MAX_SOURCE_FILES,
            "invalid source manifest")
    total = 0
    for name, pin in source_files.items():
        safe_relative(name)
        require(type(pin) is dict, "invalid source pin")
        total += integer(pin.get("bytes"))
        require(type(pin.get("sha256")) is str and SHA256.fullmatch(pin["sha256"]),
                "invalid source digest")
    require(total <= MAX_SOURCE_BYTES, "source manifest exceeds byte bound")
    accepted = contract.get("accepted_inputs", {})
    require(type(accepted) is dict, "accepted input mapping missing")
    for key in ("hardware_dataset_report", "finite_fabric_report", "gem5_draminterface"):
        require(accepted.get(key) in source_files, "unbound accepted input: " + key)
    for case in cases:
        pin = source_files.get("configs/" + case["name"] + ".cfg")
        require(pin == {"bytes": case["input_bytes"], "sha256": case["input_sha256"]},
                "case config not bound in source manifest")
    limits = contract.get("scientific_limits", {})
    require(limits.get("conditional_only") is True, "conditional label missing")
    for key in ("protocol_overhead_for_ceiling_seconds",
                "response_assembly_overhead_for_ceiling_seconds",
                "held_reply_overhead_for_ceiling_seconds"):
        require(type(limits.get(key)) in (int, float) and limits[key] == 0,
                "optimistic overhead assumption changed")
    for key in ("physical_frequency_hz", "physical_area_mm2", "complete_wall_power_watts",
                "controller_phy_power_watts", "achieved_hashes_per_second",
                "selected_engine_count", "alternative_full_hash_cycles",
                "sram_macro_characterization"):
        require(key in limits and limits[key] is None, "unknown physical gate filled")
    annotation = contract.get("gem5_annotation", {})
    require(annotation.get("status") == "STATIC_SOURCE_ANNOTATION_ONLY_NOT_EXECUTED"
            and annotation.get("source_class") == "DDR4_2400_8x8",
            "gem5 annotation scope changed")
    for key in ("sustainable_random_transactions_per_second", "sustainable_random_bytes_per_second",
                "latency_tails", "controller_phy_power_watts"):
        require(key in annotation and annotation[key] is None, "static DRAM data made supply claim")
    return contract


def verify_source_files(contract, root):
    facts = {}
    for name, pin in contract["source_files"].items():
        data = read_file(root, name, MAX_SOURCE_BYTES)
        require(len(data) == pin["bytes"] and digest(data) == pin["sha256"],
                "source identity mismatch: " + name)
        facts[name] = {"bytes": len(data), "sha256": digest(data)}
    accepted = contract["accepted_inputs"]
    demand_bytes = read_file(root, accepted["hardware_dataset_report"], MAX_SOURCE_BYTES)
    fabric_bytes = read_file(root, accepted["finite_fabric_report"], MAX_SOURCE_BYTES)
    require(digest(demand_bytes) == HARDWARE_DEMAND_SHA256,
            "accepted hardware demand substituted")
    require(digest(fabric_bytes) == FINITE_FABRIC_SHA256,
            "accepted finite-fabric report substituted")
    demand, fabric = strict_json(demand_bytes), strict_json(fabric_bytes)
    instruction = demand["interfaces"]["prepared_instruction_response"]
    require(demand.get("schema") == "openrx.architecture.hardware-dataset-service-demand.v1"
            and demand.get("target_hashes_per_second") == TARGET_HASHES_PER_SECOND
            and instruction.get("responses_per_hash") == FETCHES_PER_HASH
            and instruction.get("minimum_data_payload_bytes_per_response") == 8,
            "accepted instruction demand domain changed")
    require(fabric.get("schema") == "openrx.architecture.finite-fabric-service-profile.v1"
            and fabric["interfaces"]["fetch"] == {
                "backend_client_id_bits": 1, "client_tag_bits": 64,
                "request_payload_bits": 28, "response_payload_bits": 190},
            "accepted fetch interface changed")
    require(demand["retained_preparation"]["cache_image_bytes"] == 268435456 and
            demand["retained_preparation"]["mutable_scratchpad_bytes_per_context"] == 2097152
            and demand["retained_preparation"]["reciprocal_table_data_bytes"] == 1912,
            "retained storage domain changed")
    return facts


def parse_csv(data, banks):
    rows = list(csv.reader(io.StringIO(data.decode("utf-8")), skipinitialspace=True))
    require(len(rows) == 2, "CSV must have one header and exactly one result")
    normalized = []
    for row in rows:
        row = [x.strip() for x in row]
        if row and row[-1] == "":
            row = row[:-1]  # CACTI emits one deliberate trailing comma.
        require(len(row) == len(CSV_HEADERS), "CSV field count mismatch")
        normalized.append(row)
    require(tuple(normalized[0]) == CSV_HEADERS, "unexpected CACTI CSV header")
    fields = dict(zip(CSV_HEADERS, normalized[1]))
    require(fields["Dynamic search energy (nJ)"] == "N/A", "not a pure SRAM case")
    for key in CSV_HEADERS[19:]:
        require(fields[key] == "N/A", "unexpected tag-array result")
    expected = {"Tech node (nm)": 45, "Capacity (bytes)": 131072,
                "Number of banks": banks, "Associativity": 1, "Output width (bits)": 256,
                **PARTITION}
    values = {key: finite(value) for key, value in fields.items() if value != "N/A"}
    for key, value in expected.items():
        require(values[key] == value, "CACTI CSV input/partition mismatch: " + key)
    for key in ("Access time (ns)", "Random cycle time (ns)", "Dynamic read energy (nJ)",
                "Dynamic write energy (nJ)", "Area (mm2)"):
        finite(values[key], positive=True)
    efficiency = values["Data arrary area efficiency %"]
    require(0 < efficiency <= 100, "invalid modeled area efficiency")
    return values


def stdout_field(text, label):
    matches = re.findall(r"^\s*" + re.escape(label) + r"\s*:\s*(.*?)\s*$", text, re.M)
    require(len(matches) == 1, "missing or duplicate stdout field: " + label)
    return matches[0]


def expected_echo(banks):
    return {"Cache size": 131072, "Block size": 32, "Associativity": 1,
            "Read only ports": 0, "Write only ports": 0, "Read write ports": 1,
            "Single ended read ports": 0, "Cache banks (UCA)": banks,
            "Technology": 0.045, "Temperature": 360, "array type": "Scratch RAM",
            "Model as memory": 0, "Access mode": 0, "Data array cell type": 0,
            "Data array peripheral type": 0, "Tag array cell type": 0,
            "Tag array peripheral type": 0, "Optimization target": 0,
            "Cache model": 0, "Wire inside mat": 1, "Wire outside mat": 1,
            "Interconnect projection": 1, "Wire signalling": 1, "ECC overhead": 0,
            "Force cache config": 1, "Ndwl": 2, "Ndbl": 2, "Nspd": 1,
            "Ndcm": 1, "Ndsam1": 2, "Ndsam2": 1}


def parse_stdout(data, case, csv_values):
    text = data.decode("utf-8")
    require(not BAD_OUTPUT.search(text), "CACTI diagnostic indicates failure")
    require(text.count(BANNER) == 1, "expected one SRAM model result")
    inputs, results = text.split(BANNER)
    echo = expected_echo(case["banks"])
    extra = case.get("expected_input_echo", {})
    for key, value in extra.items():
        if key in echo:
            require(str(value) == str(echo[key]) or value == echo[key],
                    "extra echo cannot override required assumption")
        else:
            echo[key] = value
    for key, value in echo.items():
        observed = stdout_field(inputs, key)
        if isinstance(value, str):
            require(observed == value, "input echo mismatch: " + key)
        else:
            require(finite(observed) == value, "input echo mismatch: " + key)
    integer_fields = {"Total cache size (bytes)": 131072,
                      "Number of banks": case["banks"], "Block size (bytes)": 32,
                      "Read/write Ports": 1, "Read ports": 0, "Write ports": 0,
                      "Technology size (nm)": 45, "Best Ndwl": 2, "Best Ndbl": 2,
                      "Best Nspd": 1, "Best Ndcm": 1, "Best Ndsam L1": 2,
                      "Best Ndsam L2": 1}
    for key, value in integer_fields.items():
        require(finite(stdout_field(results, key)) == value, "result echo mismatch: " + key)
    require(stdout_field(results, "Associativity") == "direct mapped", "unexpected associativity")
    require(stdout_field(results, "Data array, H-tree wire type") ==
            "Delay optimized global wires", "unexpected wire model")
    pairs = {"Access time (ns)": "Access time (ns)",
             "Cycle time (ns)": "Random cycle time (ns)",
             "Total dynamic read energy per access (nJ)": "Dynamic read energy (nJ)",
             "Total dynamic write energy per access (nJ)": "Dynamic write energy (nJ)"}
    for label, key in pairs.items():
        observed = finite(stdout_field(results, label), positive=True)
        require(math.isclose(observed, csv_values[key], rel_tol=5e-5, abs_tol=1e-12),
                "stdout/CSV model mismatch: " + key)
    leakage = finite(stdout_field(results, "Total leakage power of a bank (mW)"))
    gate = finite(stdout_field(results, "Total gate leakage power of a bank (mW)"))
    require(math.isclose(leakage + gate, csv_values["Standby leakage per bank(mW)"],
                         rel_tol=5e-5, abs_tol=1e-12), "leakage component mismatch")
    dimensions = stdout_field(results, "Cache height x width (mm)").split(" x ")
    require(len(dimensions) == 2, "invalid model dimensions")
    height = finite(dimensions[0], positive=True)
    width = finite(dimensions[1], positive=True)
    # The retained uca_org_t::find_area() sets area=cache_ht*cache_len.
    # Each stdout dimension and CSV area has default stream precision;
    # tolerate their independent decimal rounding, not a different area.
    require(math.isclose(height * width, csv_values["Area (mm2)"],
                         rel_tol=5e-5, abs_tol=1e-12),
            "stdout dimensions/CSV organization area mismatch")
    return {"height_mm": height,
            "width_mm": width,
            "subthreshold_leakage_per_bank_mw": leakage,
            "gate_leakage_per_bank_mw": gate}


def parse_case(root, case):
    root = Path(root)
    data = {name: read_file(root, case["name"] + "/" + name, bound)
            for name, bound in CASE_LIMITS.items()}
    status = strict_json(data["status.json"])
    require(type(status) is dict and type(status.get("returncode")) is int and
            status["returncode"] == 0 and status.get("timed_out") is False,
            "case failed or timed out")
    binary_sha = status.get("model_binary_sha256")
    require(type(binary_sha) is str and SHA256.fullmatch(binary_sha),
            "model binary identity missing")
    require(not data["stderr.txt"].strip(), "unexpected CACTI stderr; review required")
    require(len(data["input.cfg"]) == case["input_bytes"] and
            digest(data["input.cfg"]) == case["input_sha256"], "case config substituted")
    values = parse_csv(data["out.csv"], case["banks"])
    detail = parse_stdout(data["stdout.txt"], case, values)
    period_ns = max(values["Access time (ns)"], values["Random cycle time (ns)"])
    transactions = finite(1e9 / period_ns, positive=True)
    local_bytes = finite(transactions * 32, positive=True)
    return {"name": case["name"], "banks": case["banks"],
            "model_binary_sha256": binary_sha,
            "modeled_access_ns": values["Access time (ns)"],
            "modeled_random_cycle_ns": values["Random cycle time (ns)"],
            "modeled_read_energy_nj": values["Dynamic read energy (nJ)"],
            "modeled_write_energy_nj": values["Dynamic write energy (nJ)"],
            "modeled_standby_leakage_per_bank_mw": values["Standby leakage per bank(mW)"],
            "modeled_organization_area_mm2": values["Area (mm2)"],
            "modeled_data_array_efficiency_percent": values["Data arrary area efficiency %"],
            "partition": dict(PARTITION), "dimensions_and_leakage": detail,
            "optimistic_global_one_credit_period_ns": period_ns,
            "optimistic_global_one_credit_transactions_per_second": transactions,
            "optimistic_local_sram_row_bytes_per_second": local_bytes,
            "artifact_bindings": {name: {"bytes": len(raw), "sha256": digest(raw)}
                                  for name, raw in data.items()}}


def validate_case(case_dir, case_spec, contract):
    """Fail closed after one admitted model command, before a later case starts."""
    validate_contract(contract)
    require(case_spec in contract["cases"], "case is not in admitted contract")
    case_dir = Path(case_dir)
    require(case_dir.name == case_spec["name"], "case directory identity mismatch")
    return parse_case(case_dir.parent, case_spec)


def assemble_report(contract, cases, source_facts):
    require([case["name"] for case in cases] == ["bank1", "bank4"], "case order mismatch")
    require(cases[0]["model_binary_sha256"] == cases[1]["model_binary_sha256"],
            "cases used different model binaries")
    one, four = cases
    return {
        "schema": "openrx.conditional-memory-baseline-report.v1",
        "classification": "conditional_analytic_model_observations_only",
        "scientific_acceptance": "unverified_pending_independent_review",
        "physical_characterization": False, "physical_ppa_accepted": False,
        "full_hash_projection_performed": False,
        "model_assumptions": contract["model"],
        "storage_organization_assumption": contract["organization"],
        "placement_annotation": contract.get("placement", {}),
        "gem5_annotation": contract.get("gem5_annotation", {}),
        "cases": cases,
        "bank4_divided_by_bank1_model_ratios": {
            "access_time": four["modeled_access_ns"] / one["modeled_access_ns"],
            "cycle_time": four["modeled_random_cycle_ns"] / one["modeled_random_cycle_ns"],
            "read_energy": four["modeled_read_energy_nj"] / one["modeled_read_energy_nj"],
            "organization_area": four["modeled_organization_area_mm2"] / one["modeled_organization_area_mm2"],
            "optimistic_one_credit_service_rate":
                four["optimistic_global_one_credit_transactions_per_second"] /
                one["optimistic_global_one_credit_transactions_per_second"],
        },
        "required_demand_only": {
            "accepted_fetch_responses_per_hash": FETCHES_PER_HASH,
            "assumed_local_sram_reads_per_fetch": 1,
            "assumed_local_sram_row_bytes": 32,
            "local_sram_row_bytes_per_hash_under_this_mapping": FETCHES_PER_HASH * 32,
            "target_hashes_per_second_not_achieved": TARGET_HASHES_PER_SECOND,
            "required_aggregate_transactions_per_second_at_target": FETCHES_PER_HASH * TARGET_HASHES_PER_SECOND,
            "required_aggregate_local_sram_row_bytes_per_second_at_target":
                FETCHES_PER_HASH * TARGET_HASHES_PER_SECOND * 32,
            "logical_fetch_response_payload_bits": 190,
            "logical_fetch_response_tag_and_owner_bits": 65,
            "aggregate_offchip_bytes_per_hash": None,
        },
        "unknown": {
            "physical_process_corner": None, "physical_frequency_hz": None,
            "physical_sram_latency_seconds": None, "physical_sram_energy_j": None,
            "sustainable_physical_transactions_per_second": None,
            "cache_service_latency_seconds": None, "cache_sustainable_random_bytes_per_second": None,
            "cache_sustainable_random_transactions_per_second": None,
            "controller_phy_power_w": None, "whole_machine_wall_power_w": None,
            "achieved_hashes_per_second": None, "alternative_full_hash_cycles": None,
            "engine_count_selected": None,
        },
        "scope_notes": [
            "ITRS analytical projections are not a selected foundry/PVT or SRAM macro characterization.",
            "One global credit is retained: rate is 1/max(access,cycle); bank count is not a multiplier.",
            "Zero protocol, queue, response-hold and clock-quantization overhead makes the rate an optimistic model ceiling only.",
            "The row mapping is a proposed denormalized SRAM organization; it is not implemented or physically validated RTL storage.",
            "Per-bank modeled leakage is preserved; no complete organization or wall-power total is inferred.",
            "gem5 DDR4 metadata is static annotation only; no gem5/DRAM/controller simulation or sustainable-service claim follows.",
            "Required target traffic is an aggregate demand, never achieved hashes/s or a selected architecture.",
            "The 256 MiB prepared cache, 2 MiB scratchpads/context and on-demand dataset generation are outside the modeled SRAM array.",
        ],
        "source_bindings": source_facts,
    }


def build_report(contract_path, inputs, cases_root):
    contract_path = Path(contract_path)
    require(not contract_path.is_symlink() and contract_path.stat().st_size <= 1024 * 1024,
            "contract missing, symlinked or too large")
    contract_bytes = contract_path.read_bytes()
    contract = validate_contract(strict_json(contract_bytes))
    facts = verify_source_files(contract, inputs)
    cases = [validate_case(Path(cases_root) / case["name"], case, contract)
             for case in contract["cases"]]
    report = assemble_report(contract, cases, facts)
    provenance = {"schema": "openrx.conditional-memory-baseline-provenance.v1",
                  "contract_sha256": digest(contract_bytes),
                  "source_bindings": facts,
                  "case_artifact_bindings": {case["name"]: case["artifact_bindings"] for case in cases},
                  "classification": "conditional_analytic_model_observations_only",
                  "scientific_acceptance": "unverified_pending_independent_review",
                  "physical_characterization": False}
    return report, provenance


def write_outputs(output, report, provenance):
    output = Path(output)
    require(not output.exists() and not output.is_symlink(), "output path already exists")
    encoded = {}
    for name, value in (("memory-baseline.json", report), ("provenance.json", provenance)):
        data = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        require(not any(token in data for token in (b"/home/", b"/tmp/", b"file://")),
                "host path in portable scientific output")
        encoded[name] = data
    output.mkdir(parents=True, exist_ok=False)
    digests = {}
    for name, data in encoded.items():
        with (output / name).open("xb") as stream:
            stream.write(data)
        digests[name] = digest(data)
    with (output / "artifacts.sha256.json").open("x") as stream:
        json.dump(digests, stream, sort_keys=True, indent=2)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report, provenance = build_report(args.contract, args.inputs, args.cases)
    write_outputs(args.output, report, provenance)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
