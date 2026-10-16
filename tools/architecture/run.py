"""Reproducible task #72 comparisons and complete-path necessary bounds.

Run with ``python3 -B -m tools.architecture.run --help`` from the repo root.
No HDL simulator, workload generator, physical technology or frequency is used.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from . import baseline, envelope, evidence, native_trace
from .scheduler import Config, MemorySpec, MicroOp, UnitSpec, simulate


# Trusted bindings from preserved run03 and the reviewed portable fixture at
# 46fa0737. Never infer identity from hash claims inside a supplied input.
ACCEPTED_FULL_EVIDENCE_SHA256 = "33f4cbe95805d33068fa9eceee90820f230cd0457d06f35407f9323d1d547ecf"
ACCEPTED_FIXTURE_SHA256 = {
    "native/accesses.hex": "aa494e27e6ecf52b174721839343708c3e6924583c6d0b993201fc302e7e9582",
    "native/iterations.hex": "19a9b94844998bc7db6442fe7b9116f7ee3039861fe7592803d0f0a82593ce41",
    "native/program-0.mem": "002dc17c9a413e112ff1a15340c4fbb4c67bd17656b4f3e23d09036bd85c08ec",
    "native/program-1.mem": "005108dec03308f65eda8f561497b1d21862c5d67cb11ec8af4d5edf2cf8e384",
    "native/program-2.mem": "ea5f0a410d9845c76dfdd0f5db35360eea0206ea66972a6e7f0e7e0d7030cd3f",
    "native/program-3.mem": "0d4f54ec419bbb4a6c23b357277ab5c382784801ceab70dc5dbfc010829fd6df",
    "native/program-4.mem": "61574ff62cbc22bdc53097779659421c632b9b5923e4bcc4ddf5dac9242ad697",
    "native/program-5.mem": "2d52c7a22773c0bf3d861874d8820ba49714fc50cb9d9329391e698ca403e56c",
    "native/program-6.mem": "96b734f9f0b30a96511668b583eda0ee011176292f3542ac6eae5e96f414dc42",
    "native/program-7.mem": "ccbecd8ddb3f89302733843ae7b16bf401d8677e860fdcce0bab5f0933f16a59",
    "source-map.json": "4c00dc1b5356ec0a05f45cecf8e3075c178a8a31eacb0d52797570f023f0f942",
    "trace.csv": "d8682dcafb9021b4adf2b51abe04b7d2e1da44139e131c767a0fbc2cf001e808",
}


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _window_comparison(window):
    keys = set(MicroOp.__dataclass_fields__)
    ops = [MicroOp.from_dict({k: v for k, v in record.items() if k in keys})
           for record in window["operations"]]
    units = {name: UnitSpec(count=1, initiation_interval=1, nonpipelined=True)
             for name in sorted({op.unit for op in ops})}
    rows = []
    cases = [("single_issue_blocking", 1, 1, True, 1)]
    cases += [(name, contexts, width, blocking, lookahead)
              for name, width, blocking, lookahead in (
                  ("multicontext_blocking", 1, True, 1),
                  ("limited_nonblocking", 1, False, 8),
                  ("dual_issue", 2, False, 8))
              for contexts in (1, 2, 4, 8, 16)]
    for response_cycles in (0, 10, 50):
        for name, contexts, width, blocking, lookahead in cases:
            config = Config(contexts=contexts, issue_width=width, blocking_context=blocking,
                            issue_window=lookahead, units=units,
                            memory={"scratchpad": MemorySpec(banks=8, ports_per_bank=1,
                                bytes_per_cycle=16, latency=response_cycles,
                                max_outstanding=8, bank_width=8, shared=True)},
                            memory_order="strict")
            result = simulate(ops, config)
            rows.append({"program": window["program"], "iteration": window["iteration"],
                         "configuration": name, "parameters": asdict(config), **result})
    # Isolate bank/port, II and outstanding sensitivity from issue-width changes.
    for parameter, values in (("banks", (1, 2, 4, 16)),
                              ("ports_per_bank", (1, 2)),
                              ("bytes_per_cycle", (8, 32)),
                              ("max_outstanding", (1, 2, 4)),
                              ("initiation_interval", (2, 4))):
        for value in values:
            memory_values = dict(banks=8, ports_per_bank=1, bytes_per_cycle=16,
                                 latency=10, max_outstanding=8, bank_width=8, shared=True)
            unit_values = units
            if parameter == "initiation_interval":
                unit_values = {k: UnitSpec(count=1, initiation_interval=value, nonpipelined=True) for k in units}
            else:
                memory_values[parameter] = value
            config = Config(contexts=4, issue_width=2, blocking_context=False,
                            issue_window=8, units=unit_values,
                            memory={"scratchpad": MemorySpec(**memory_values)}, memory_order="strict")
            rows.append({"program": window["program"], "iteration": window["iteration"],
                         "configuration": "resource_sensitivity", "sweep_parameter": parameter,
                         "sweep_value": value, "parameters": asdict(config), **simulate(ops, config)})
    return rows


def compare(trace, workers=1):
    if type(workers) is not int or not 1 <= workers <= 6:
        raise ValueError("workers must be 1..6")
    windows = trace["windows"]
    if workers == 1:
        groups = list(map(_window_comparison, windows))
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            groups = list(pool.map(_window_comparison, windows))
    return {
        "schema": "openrx.architecture.comparison.v1",
        "scope": "disjoint_actual_bytecode_windows_replayed_independently",
        "validation_status": "alternative_hardware_unvalidated",
        "demonstrated_asic_performance": False,
        "full_hash_cycles": None, "hashes_per_second": None, "wall_power_w": None,
        "windows": [{"program": w["program"], "iteration": w["iteration"],
                     "operation_count": len(w["operations"])} for w in windows],
        "input_operation_sha256": hashlib.sha256(json.dumps(windows, sort_keys=True).encode()).hexdigest(),
        "assumptions": [
            "Each context replays an identical dynamic window with distinct mutable state; no independent-hash workload distribution is claimed.",
            "One nonpipelined macro functional unit per unit class, II at least one; bytecode service spans measured on the accepted bounded RTL path.",
            "All memory macroops charge serial nonmemory service plus transfer and response, reserving their FU throughout; store address/transfer phase placement is conservatively abstracted.",
            "An 8-position issue window, no renaming or speculation, conservative CBRANCH/CFROUND barriers and strict per-context memory order.",
            "Eight shared scratchpad banks, one port each, address/8 modulo bank count, 16B/cycle fabric and eight outstanding requests are scenario parameters.",
            "Response latencies 0/10/50 are integral abstract cycles; no physical clock or memory technology maps them to seconds.",
            "No initial hash/fill/program generation, outer entry/AES/tail, dataset, seed, preparation or finalization work in these bytecode-window timings.",
            "A fixed dynamic path preserves observed branch outcomes and addresses; newly designed hardware still needs native value/hash equivalence and timing validation.",
        ],
        "results": [row for group in groups for row in group],
    }


def provenance(full, full_evidence_path, trace, fixture):
    full_bytes = Path(full_evidence_path).read_bytes()
    full_sha = hashlib.sha256(full_bytes).hexdigest()
    fixture_hashes = {str(p.relative_to(fixture)): evidence.sha256_file(p)
                      for p in sorted(fixture.rglob("*")) if p.is_file()}
    full_trace_sha = full.get("trace", {}).get("trace_sha256")
    source_map_path = fixture / "source-map.json"
    source_map = json.loads(source_map_path.read_text()) if source_map_path.is_file() else {}
    short_trace_sha = source_map.get("source_inputs", {}).get("trace", {}).get("sha256")
    full_recognized = (full_sha == ACCEPTED_FULL_EVIDENCE_SHA256
                       and json.loads(full_bytes) == full)
    short_recognized = fixture_hashes == ACCEPTED_FIXTURE_SHA256
    return {
        "input_bindings": {
            "identity_status": "accepted_inputs_verified" if full_recognized and short_recognized else "untrusted_input",
            "trusted_binding_source": "preserved_run03_and_portable_fixture_at_46fa0737",
            "full_evidence_sha256": full_sha,
            "trusted_full_evidence_sha256": ACCEPTED_FULL_EVIDENCE_SHA256,
            "full_accepted_trace_recognized": full_recognized,
            "bounded_accepted_trace_recognized": short_recognized,
            "fixture_files_sha256": fixture_hashes,
            "bounded_source_inputs_sha256": {k: v.get("sha256") for k, v in source_map.get("source_inputs", {}).items()},
            "full_source_trace_sha256": full_trace_sha,
            "bounded_source_trace_sha256": short_trace_sha,
        },
        "measured_simulation": {
            "full_workload": "c96e96ab1eb46cb727b21befffa526e637ebed4a, 8 programs x 2048 iterations, actual light dataset values, canonical digest matched" if full_recognized else "unrecognized input; no accepted-run attribution",
            "bounded_workload": "accepted reviewed successor source d3ed89861b2d8d9c6ea9a938079de6506a81ec21, prepared-ideal 8x2; first iteration per program" if short_recognized else "unrecognized input; no accepted-run attribution",
            "provider_boundary": "input BLAKE2b, initial fill, program generation, native light dataset generation are untimed host providers",
        },
        "source_derived": ["register dependencies and opcode classes", "lifecycle fixed-state equations", "2MiB distinct mutable state per live context", "fill/final scan bytes"],
        "assumed_scenarios": ["issue width/window and live contexts", "FU count and initiation interval", "scratchpad banks/ports/placement/transfer granules", "memory service latency and outstanding request limits"],
        "unknown": ["provider device clocks/energy/internal traffic", "physical frequency/process/area", "qualified SRAM macro timing/leakage", "physical random-memory service/energy", "whole-machine power and PSU/VRM curves", "full-hash timing of alternative hardware"],
        "demonstrated_asic_feasibility": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    reproduce = commands.add_parser("reproduce", help="replay portable bounded fixture and full-derived necessary bounds")
    reproduce.add_argument("--fixture", type=Path, required=True)
    reproduce.add_argument("--evidence", type=Path, required=True)
    reproduce.add_argument("--output", type=Path, required=True)
    reproduce.add_argument("--workers", type=int, default=1)
    bundle = commands.add_parser("extract", help="stream accepted full evidence once and sample accepted richer short trace")
    bundle.add_argument("--full-output", type=Path, required=True)
    bundle.add_argument("--short-output", type=Path, required=True)
    bundle.add_argument("--source-root", type=Path, required=True)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if args.command == "extract":
        full = evidence.extract_evidence(args.full_output / "summary.json", args.full_output / "prepared-ideal/trace.csv",
                args.full_output / "native-reference", source_root=args.source_root,
                diagnostic_output=args.output / "full-scan-diagnostics.json")
        dump(args.output / "full-evidence.json", full)
        short = evidence.extract_evidence(args.short_output / "summary.json", args.short_output / "prepared-ideal/trace.csv",
                args.short_output / "native-reference", source_root=args.source_root,
                diagnostic_output=args.output / "short-scan-diagnostics.json")
        dump(args.output / "short-evidence.json", short)
        trace = native_trace.extract(args.short_output / "prepared-ideal/trace.csv", args.short_output / "native-reference", max_iterations=8,
                first_iteration_per_program=True, fixture_output=args.output / "fixture")
        dump(args.output / "bounded-trace.json", trace)
        full_evidence_path, fixture = args.output / "full-evidence.json", args.output / "fixture"
    else:
        full = json.loads(args.evidence.read_text())
        if full.get("schema") != "openrx.architecture.evidence.v1":
            raise ValueError("full evidence schema required")
        full_evidence_path, fixture = args.evidence, args.fixture
    attribution = provenance(full, full_evidence_path, None, fixture)
    dump(args.output / "provenance.json", attribution)
    if attribution["input_bindings"]["identity_status"] != "accepted_inputs_verified":
        raise ValueError("untrusted input: actual evidence/fixture bytes differ from trusted accepted bindings; see provenance.json")
    if args.command == "reproduce":
        trace = native_trace.extract(fixture / "trace.csv", fixture / "native", max_iterations=8,
                                     first_iteration_per_program=True)
    dump(args.output / "comparisons.json", compare(trace, args.workers))
    dump(args.output / "baseline-calibration.json", baseline.calibrate(trace))
    dump(args.output / "sensitivity.json", envelope.sensitivity(full))
    digest_index = {str(p.relative_to(args.output)): evidence.sha256_file(p)
                    for p in sorted(args.output.rglob("*")) if p.is_file()}
    dump(args.output / "artifacts.sha256.json", digest_index)
    print(json.dumps({"output": str(args.output), "windows": len(trace["windows"]),
                      "operations": trace["operation_count"], "status": "analytical_only", "full_hash_feasibility": "unresolved"}))


if __name__ == "__main__":
    main()
