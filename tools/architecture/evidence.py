"""Stream preserved connected RTL evidence; never run RandomX or an HDL simulator.

The accepted c96 event trace retains outer transitions and accepted transactions.
Its iteration/executor columns are sampled, not transition complete. Only outer
durations belong to the preceding row; flags count once at their row. The final
duration closes against the separately recorded clock count.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path

SCRATCHPAD_BYTES = 2 * 1024**2
PREFIXES = (16384, 65536, 262144, 524288, SCRATCHPAD_BYTES)
STAGES = {1: "initialization_transport", 2: "control_and_metadata",
          3: "program_preparation", 4: "execution", 5: "interprogram_seed",
          6: "finalization", 8: "held_return"}
HEADER = "cycle,outer_phase,iteration_phase,execute_phase,commit,pc,sp_read,sp_addr,sp_write,write_addr,write_strb,dataset,dataset_addr"
FAMILIES = tuple(zip(
    (16, 23, 39, 46, 62, 66, 70, 71, 75, 76, 84, 86, 101, 106,
     114, 116, 120, 124, 140, 145, 161, 166, 172, 204, 208, 214, 239, 240, 256),
    ("IADD_RS", "IADD_M", "ISUB_R", "ISUB_M", "IMUL_R", "IMUL_M", "IMULH_R",
     "IMULH_M", "ISMULH_R", "ISMULH_M", "IMUL_RCP", "INEG_R", "IXOR_R", "IXOR_M",
     "IROR_R", "IROL_R", "ISWAP_R", "FSWAP_R", "FADD_R", "FADD_M", "FSUB_R",
     "FSUB_M", "FSCAL_R", "FMUL_R", "FDIV_M", "FSQRT_R", "CBRANCH", "CFROUND", "ISTORE")))
SOURCE_FILES = (
    "rtl/hash/tests/tb_prepared_hash_lifecycle.v",
    "rtl/hash/randomx_prepared_hash_lifecycle.v",
    "rtl/execute/randomx_program_reciprocals.v",
    "rtl/execute/randomx_reciprocal32.v",
    "rtl/execute/randomx_integer_execute.v",
    "rtl/engine/randomx_iteration_engine.v",
    "rtl/hash/randomx_program_seed.v",
    "rtl/hash/randomx_regfile_blake2b.v",
    "rtl/hash/randomx_blake2b_chain_core.v",
    "rtl/hash/randomx_scratchpad_aes_hash.v",
    "rtl/hash/randomx_scratchpad_finalizer.v",
    "rtl/execute/tests/program_sequence_oracle.cpp",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def family(word):
    opcode = word & 255
    return next(name for ceiling, name in FAMILIES if opcode < ceiling)


def active_reciprocal(word):
    divisor = word >> 32
    return family(word) == "IMUL_RCP" and divisor != 0 and divisor & (divisor - 1) != 0


def read_programs(directory, programs):
    return [[int(line, 16) for line in (Path(directory) / f"program-{p}.mem").read_text().splitlines()]
            for p in range(programs)]


def stream_trace(path, total_cycles, programs, sample_trace_output=None, sample_iterations_per_program=1):
    """Read the full CSV once, binding its bytes while deriving exact counters.

    Optional samples contain the first complete iteration of each program, plus
    preparation and terminal sentinels. Added columns identify discontinuous
    slices; sample timestamps MUST NOT be integrated across those gaps.
    """
    require(type(total_cycles) is int and total_cycles > 0, "positive integer total cycles required")
    require(type(sample_iterations_per_program) is int and sample_iterations_per_program > 0, "positive sample iteration count required")
    outer, iteration_rows, executor_rows = Counter(), [0] * 12, [0] * 18
    events, op_counts, active_ops = Counter(), Counter(), Counter()
    digest = hashlib.sha256()
    previous = None
    rows = 0
    program = -1
    global_iteration = -1
    program_iteration = -1
    dataset_seen = False
    sample_rows = 0
    sample_context = Path(sample_trace_output).open("x") if sample_trace_output else nullcontext(None)
    with Path(path).open("rb") as stream, sample_context as sample:
        header = stream.readline()
        digest.update(header)
        require(header.decode().strip() == HEADER, "unsupported trace header")
        if sample:
            sample.write(HEADER + ",program,global_iteration\n")

        def account(row, duration):
            outer[row[1]] += duration

        for raw in stream:
            digest.update(raw)
            cells = raw.rstrip().split(b",")
            require(len(cells) == 13, f"malformed trace row {rows + 2}")
            row = tuple(int(value, 16 if i in (7, 9, 10, 12) else 10) for i, value in enumerate(cells))
            cycle, phase, ip, ep, commit, pc, read, _, write, _, strobe, dataset, _ = row
            require(phase in STAGES and 0 <= ip < 12 and 0 <= ep < 18, "invalid trace phase")
            require(all(value in (0, 1) for value in (commit, read, write, dataset)), "invalid event flag")
            require(0 <= strobe <= 65535, "invalid write strobes")
            for enabled, address in ((read, row[7]), (write, row[9])):
                require(not enabled or 0 <= address < SCRATCHPAD_BYTES and address % 16 == 0,
                        "accepted scratchpad address outside aligned image")
            require(not dataset or row[12] >= 0 and row[12] % 64 == 0,
                    "unaligned dataset request")
            if phase == 4:
                iteration_rows[ip] += 1
                if ip == 7:
                    executor_rows[ep] += 1
            if previous is None:
                require(cycle == 0, "trace must start at clock zero")
            else:
                require(cycle > previous[0], "trace timestamps must strictly increase")
                account(previous, cycle - previous[0])
            require(cycle < total_cycles, "trace row exceeds total clock count")
            if phase == 3 and (previous is None or previous[1] != 3):
                program += 1
                program_iteration = -1
                dataset_seen = False
            # One accepted dataset request closes bytecode each iteration.
            # The next controller IDLE observation or first accepted entry read
            # identifies the following iteration without inventing durations.
            new_iteration = phase == 4 and (program_iteration < 0 or
                dataset_seen and (ip == 0 or ip == 1 and read))
            if new_iteration:
                global_iteration += 1
                program_iteration += 1
                dataset_seen = False
            if commit:
                require(phase == 4 and ip == 7, "commit outside bytecode execution")
                require(0 <= program < len(programs) and pc < len(programs[program]), "commit PC/program outside image")
                word = programs[program][pc]
                name = family(word)
                op_counts[name] += 1
                if name == "IMUL_RCP" and active_reciprocal(word):
                    active_ops["IMUL_RCP"] += 1
            events["instruction_commits"] += commit
            events["scratchpad_reads16"] += read
            events["scratchpad_write_bus16"] += write
            events["scratchpad_strobed_write_bytes"] += strobe.bit_count() * write
            events["dataset_requests64"] += dataset
            if dataset:
                dataset_seen = True
            # Keep the next iteration's initial row as a closing sentinel too.
            selected = phase == 3 and (previous is None or previous[1] != 3)
            selected |= phase == 4 and 0 <= program_iteration < sample_iterations_per_program
            selected |= new_iteration and program_iteration == sample_iterations_per_program
            if sample and selected:
                sample.write(raw.decode().rstrip() + f",{program},{global_iteration}\n")
                sample_rows += 1
            previous = row
            rows += 1
        require(previous is not None, "empty trace")
        account(previous, total_cycles - previous[0])
    return {"trace_sha256": digest.hexdigest(), "trace_rows": rows,
            "total_cycles": total_cycles, "stage_cycles": {name: outer[key] for key, name in STAGES.items()},
            "nested_iteration_phases": None,
            "sampled_iteration_state_row_counts": iteration_rows,
            "iteration_state_coverage": "not reconstructed by this extractor; c96 CSV omits iteration transitions; richer successor is analyzed separately",
            "sampled_executor_state_row_counts": executor_rows,
            "executor_state_durations": None,
            "executor_state_coverage": "not reconstructed by this extractor; c96 CSV omits executor transitions; richer successor is analyzed separately",
            "events": dict(events), "instruction_families": dict(sorted(op_counts.items())),
            "programs_observed": program + 1, "iterations_observed": events["dataset_requests64"],
            "iteration_count_basis": "one accepted dataset request per iteration; no duration inference",
            "active_reciprocal_commits": active_ops["IMUL_RCP"],
            "sample_rows": sample_rows,
            "sample_scope": "first whole iteration per program; discontinuous clocks" if sample_trace_output else None}


def extract_native_locality(directory):
    """Use accepted native events and actual per-iteration addresses, not a cache model."""
    directory = Path(directory)
    counts = Counter({name: 0 for name in ("bytecode_read8", "bytecode_write8", "outer_read64", "outer_write64")})
    hot = {size: Counter(counts) for size in PREFIXES}
    touched, dirty, dataset_lines = set(), set(), set()
    bindings = {}
    iterations = steps = 0
    for name in ("accesses.hex", "iterations.hex"):
        digest = hashlib.sha256()
        with (directory / name).open("rb") as stream:
            for raw in stream:
                digest.update(raw)
                row = raw.split()
                if name == "accesses.hex":
                    require(len(row) == 2, "malformed native access")
                    token = int(row[0], 16)
                    address, write = token & (SCRATCHPAD_BYTES - 1), token >> 21
                    require(write in (0, 1) and address % 8 == 0, "invalid native access")
                    accesses = [(address, "bytecode_write8" if write else "bytecode_read8")]
                else:
                    require(len(row) == 19, "malformed native iteration")
                    iterations += 1
                    steps += int(row[4])
                    dataset_address = int(row[16], 16)
                    require(dataset_address % 64 == 0, "unaligned native dataset address")
                    dataset_lines.add(dataset_address // 64)
                    accesses = [(int(row[index], 16), kind) for index in (14, 15)
                                for kind in ("outer_read64", "outer_write64")]
                for address, kind in accesses:
                    require(0 <= address < SCRATCHPAD_BYTES and address % (64 if "64" in kind else 8) == 0,
                            "native address outside scratchpad/alignment")
                    counts[kind] += 1
                    touched.add(address // 64)
                    if "write" in kind:
                        dirty.add(address // 64)
                    for size in PREFIXES:
                        if address < size:
                            hot[size][kind] += 1
        bindings[name] = digest.hexdigest()
    return {"iterations": iterations, "instruction_steps": steps, "counts": dict(counts),
            "unique_touched_64B_lines": len(touched), "unique_written_64B_lines": len(dirty),
            "unique_dataset_64B_lines": len(dataset_lines), "dataset_bytes_per_hash": iterations * 64,
            "native_input_sha256": bindings,
            "prefixes": [{"hot_prefix_bytes": size, "hot_counts": dict(hot[size]),
                          "cold_counts": {kind: count - hot[size][kind] for kind, count in counts.items()}}
                         for size in PREFIXES]}


def source_cycle_equations(trace, programs, iterations, static_reciprocals, words_per_program=384,
                           iteration_counters=None):
    """Default ideal RTL state equations with an explicit measured executor term.

    This is a source-state replay/calibration, not an independently predictive
    instruction timing model. The full c96 CSV cannot resolve executor states.
    """
    require(iteration_counters is not None and len(iteration_counters) == 12,
            "accepted per-clock iteration ledger counters required")
    executor_wait = iteration_counters[7]
    iteration_costs = {"controller_idle": 1, "entry_read_requests": 8,
                       "entry_read_replies": 8, "executor_admission": 1,
                       "dataset_request": 1, "dataset_reply": 1,
                       "tail_admission": 1, "tail_eight_writes_and_return": 9}
    nonexecutor = sum(iteration_costs.values()) * iterations
    beats = SCRATCHPAD_BYTES // 16
    regfile_hash = 2 * (1 + 1 + 2 * 12 + 1 + 1)
    expected = {
        "initialization_transport": beats + 2,
        "control_and_metadata": 4 * programs + 2,
        "program_preparation": programs * (2 * words_per_program + 2) + 66 * static_reciprocals,
        "execution": nonexecutor + executor_wait,
        "interprogram_seed": (programs - 1) * (regfile_hash + 3) + 1,
        "finalization": 3 * beats + 8 + (1 + 1 + 1 + 1 + (regfile_hash + 1) + 1),
        "held_return": 1,
    }
    residuals = {name: trace["stage_cycles"][name] - value for name, value in expected.items()}
    expected_iteration = [iterations, 4 * iterations, 4 * iterations, 4 * iterations, 4 * iterations,
                          0, iterations, executor_wait, iterations, iterations, iterations, 9 * iterations]
    return {"classification": "partial_source_state_equation_replay_with_unpredicted_measured_executor_aggregate",
            "assumptions": ["ideal accepted replies, no stalls", "default parallel direct multiply/FP/divsqrt", "eight scratchpad entry beats and eight tail beats each iteration"],
            "formulas": {"initialization_transport": "scratchpad_bytes/16 + 2 request/return clocks",
                         "control_and_metadata": "4*programs + 2 lifecycle admission/return clocks",
                         "program_preparation": "programs*(2*words_per_program + 2 admission/return) + active_static_reciprocals*(1 request + 64 iterations + 1 response)",
                         "execution": "iterations*(IDLE1 + entry_requests8 + entry_replies8 + EX_REQ1 + DS_REQ1 + DS_RSP1 + TAIL_REQ1 + TAIL_WAIT9) + measured_EX_WAIT",
                         "interprogram_seed": "(programs-1)*(regfile_hash56 + 3 seed states) + 1 last-program bypass",
                         "finalization": "3*scratchpad_beats + 8 extra AES rounds + IDLE1 + AES_START1 + AES_return1 + HASH_START1 + HASH_WAIT57 + RETURN1",
                         "regfile_hash": "2 blocks*(request1 + core_init1 + 12 rounds*2 + finalize1 + response1) = 56"},
            "measured_unpredicted_inputs": {"executor_EX_WAIT_aggregate_cycles": executor_wait},
            "iteration_counter_provenance": "accepted testbench per-clock ledger counters; not reconstructed from sampled CSV",
            "iteration_nonexecutor_cycles_per_iteration": iteration_costs,
            "expected_iteration_phases": expected_iteration,
            "iteration_phase_residuals": [a - b for a, b in zip(iteration_counters, expected_iteration)],
            "executor_phase_residuals": None,
            "expected_stage_cycles": expected, "stage_cycle_residuals": residuals,
            "total_cycle_residual": trace["total_cycles"] - sum(expected.values()),
            "unexplained_fitted_cycles": 0}


def extract_evidence(summary_path, trace_path, native_reference, output=None, sample_trace_output=None, source_root=None,
                     sample_iterations_per_program=1, diagnostic_output=None):
    summary_path, trace_path, native_reference = map(Path, (summary_path, trace_path, native_reference))
    summary = json.loads(summary_path.read_text())
    require(summary.get("status") == "pass_connected_native_reference", "reference-correct connected summary required")
    profile = summary["profiles"]["prepared-ideal"]
    ledger, provider = profile["ledger"], profile["host_provider"]
    require(provider["provider_device_cycles"] is None and ledger["untimed_provider_device_cycles"] is None,
            "untimed host providers cannot acquire invented device clocks")
    programs = read_programs(native_reference, summary["programs"])
    trace = stream_trace(trace_path, ledger["cycles"], programs, sample_trace_output, sample_iterations_per_program)
    if diagnostic_output:
        with Path(diagnostic_output).open("x") as stream:
            json.dump({"classification": "prevalidation_scan_diagnostics_not_accepted_results",
                       "trace": trace, "accepted_ledger": ledger,
                       "summary_sha256": sha256_file(summary_path)}, stream, indent=2, sort_keys=True)
            stream.write("\n")
    require(trace["trace_sha256"] == profile["trace_sha256"], "trace SHA256 differs from accepted summary")
    require(trace["stage_cycles"] == ledger["stage_cycles"], "trace/ledger mismatch: stage_cycles")
    require(sum(ledger["nested_iteration_phases"]) == ledger["stage_cycles"]["execution"],
            "accepted nested iteration ledger does not close execution stage")
    locality = extract_native_locality(native_reference)
    native = summary["native_reference"]
    require(locality["iterations"] == native["total_iterations"] and locality["instruction_steps"] == native["instruction_steps"], "native workload count mismatch")
    require(trace["events"]["instruction_commits"] == native["instruction_steps"], "retirement count mismatch")
    require(trace["programs_observed"] == summary["programs"] and trace["iterations_observed"] == native["total_iterations"],
            "trace program/iteration boundary count mismatch")
    require(trace["events"]["dataset_requests64"] == native["total_iterations"], "dataset request count mismatch")
    require(sum(locality["counts"][name] for name in ("bytecode_read8", "bytecode_write8")) == native["bytecode_events"], "bytecode event count mismatch")
    comparisons = {"physical_port_read_bytes": trace["events"]["scratchpad_reads16"] * 16,
                   "physical_port_write_bus_bytes": trace["events"]["scratchpad_write_bus16"] * 16,
                   "strobed_write_bytes": trace["events"]["scratchpad_strobed_write_bytes"],
                   "dataset_logical_bytes": trace["events"]["dataset_requests64"] * 64}
    for field, value in comparisons.items():
        require(value == ledger[field], f"accepted transaction/ledger mismatch: {field}")
    static_reciprocals = sum(active_reciprocal(word) for image in programs for word in image)
    require(static_reciprocals == ledger["preparation_reciprocals"], "static prepared reciprocal count mismatch")
    calibration = source_cycle_equations(trace, summary["programs"], locality["iterations"], static_reciprocals,
                                         len(programs[0]), iteration_counters=ledger["nested_iteration_phases"])
    require(calibration["total_cycle_residual"] == 0 and not any(calibration["stage_cycle_residuals"].values())
            and not any(calibration["iteration_phase_residuals"]), "source-state replay has unexplained fixed-stage cycles")
    source_root = Path(source_root) if source_root else Path(__file__).resolve().parents[2]
    input_path = summary_path.parent / "inputs.json"
    executed_bindings = json.loads(input_path.read_text()) if input_path.exists() else {}
    source_bindings = {name: {"current_sha256": sha256_file(source_root / name),
                             "executed_input_sha256": executed_bindings.get(name)}
                       for name in SOURCE_FILES if (source_root / name).is_file()}
    for binding in source_bindings.values():
        binding["identical_to_executed_input"] = binding["current_sha256"] == binding["executed_input_sha256"] if binding["executed_input_sha256"] else None
    report = {"schema": "openrx.architecture.evidence.v1", "classification": "measured_one_connected_native_v2_workload",
              **locality, "trace": trace, "calibration": calibration,
              "accepted_nested_iteration_counters": ledger["nested_iteration_phases"],
              "accepted_nested_iteration_counter_source": "summary profiles.prepared-ideal.ledger; direct per-clock testbench counters",
              "summary_sha256": sha256_file(summary_path), "source_bindings": source_bindings,
              "program_sha256": {f"program-{p}.mem": sha256_file(native_reference / f"program-{p}.mem") for p in range(len(programs))},
              "provider": provider,
              "provenance": {"measured": ["accepted outer clock partitions and transaction flags from CSV",
                                          "nested iteration clock partitions from accepted direct testbench ledger counters",
                                          "native bytecode/outer scratchpad and dataset addresses for one workload",
                                          "dynamic commit PCs decoded against bound immutable program images"],
                             "source_derived": ["fixed ideal RTL stage/state equations; default parameters"],
                             "assumed": ["scenario use beyond the single measured workload"],
                             "unknown": ["iteration/executor-state durations from c96 sampled CSV", "untimed provider device costs",
                                         "physical clock, memory service/traffic, area and full-system energy"]},
              "limitations": ["one accepted workload is not a distribution or physical performance measurement",
                              "native dataset generated in light mode from 256 MiB cache; no materialized full dataset or DRAM timing",
                              "input hashing, initial fill, program generation and dataset generation have unknown untimed device costs",
                              "General extractor does not reconstruct nested CSV timing: c96 lacks transitions; richer successor timing is analyzed separately",
                              "CSV lacks operand values, reply flags and detailed readiness; reordered comparisons require explicit assumptions",
                              "source equations replay measured entire executor wait aggregate; not independent full-hash timing prediction"],
              "device_frequency_hz": None, "physical_power_watts": None, "demonstrated_asic_feasibility": False}
    if output:
        with Path(output).open("x") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--native-reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-trace-output", type=Path)
    parser.add_argument("--sample-iterations-per-program", type=int, default=1)
    parser.add_argument("--diagnostic-output", type=Path)
    args = parser.parse_args()
    report = extract_evidence(args.summary, args.trace, args.native_reference, args.output, args.sample_trace_output,
                              sample_iterations_per_program=args.sample_iterations_per_program,
                              diagnostic_output=args.diagnostic_output)
    print(json.dumps({"output": str(args.output), "trace_sha256": report["trace"]["trace_sha256"],
                      "cycles": report["trace"]["total_cycles"], "cycle_residual": report["calibration"]["total_cycle_residual"]}))


if __name__ == "__main__":
    main()
