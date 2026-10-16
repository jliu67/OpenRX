#!/usr/bin/env python3
"""Extract bounded, evidence-bound RandomX bytecode scheduling inputs.

This is not an instruction interpreter.  The committed PC path and service
spans come from the accepted RTL event CSV; instruction words, byte addresses
and the per-iteration route checksum come from its native-reference files.
No future control outcome or data-dependent execution latency is predicted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Iterable, TextIO


CEILINGS = (
    (16, "IADD_RS"), (23, "IADD_M"), (39, "ISUB_R"),
    (46, "ISUB_M"), (62, "IMUL_R"), (66, "IMUL_M"),
    (70, "IMULH_R"), (71, "IMULH_M"), (75, "ISMULH_R"),
    (76, "ISMULH_M"), (84, "IMUL_RCP"), (86, "INEG_R"),
    (101, "IXOR_R"), (106, "IXOR_M"), (114, "IROR_R"),
    (116, "IROL_R"), (120, "ISWAP_R"), (124, "FSWAP_R"),
    (140, "FADD_R"), (145, "FADD_M"), (161, "FSUB_R"),
    (166, "FSUB_M"), (172, "FSCAL_R"), (204, "FMUL_R"),
    (208, "FDIV_M"), (214, "FSQRT_R"), (239, "CBRANCH"),
    (240, "CFROUND"), (256, "ISTORE"),
)
MEMORY_KINDS = {
    "IADD_M", "ISUB_M", "IMUL_M", "IMULH_M", "ISMULH_M",
    "IXOR_M", "FADD_M", "FSUB_M", "FDIV_M", "ISTORE",
}
# See randomx_integer_execute.v state constants.  Fetch and memory transport
# cycles are deliberately not folded into functional-unit service latency.
SERVICE_PHASES = {3, 7, 10, 11, 12, 13, 14, 15, 16, 17}
MASK64 = (1 << 64) - 1
TRACE_COLUMNS = {
    "cycle", "outer_phase", "iteration_phase", "execute_phase", "commit",
    "pc", "sp_read", "sp_addr", "sp_write", "write_addr", "write_strb",
    "dataset", "dataset_addr",
}


def open_text(path: Path) -> TextIO:
    return gzip.open(path, "rt") if path.suffix == ".gz" else path.open()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode(word: int) -> dict:
    """Decode pinned-v2 register dependencies, including immediate/NOP cases.

    CFROUND is a conservative read-modify-write of rounding mode: v2 can leave
    the old mode unchanged based on source bits absent from the event CSV.
    Both CFROUND and CBRANCH serialize a context without branch speculation.
    """
    if not 0 <= word <= MASK64:
        raise ValueError("instruction is not a 64-bit word")
    opcode = word & 255
    kind = next(kind for ceil, kind in CEILINGS if opcode < ceil)
    dst, src = (word >> 8) & 7, (word >> 16) & 7
    immediate = word >> 32
    rd, rs = f"r{dst}", f"r{src}"
    fd, ed, ar = f"f{dst % 4}", f"e{dst % 4}", f"a{src % 4}"
    reads: list[str] = []
    writes: list[str] = []
    unit, barrier, nop = "integer", False, False
    if kind == "IADD_RS":
        reads, writes = [rd, rs], [rd]
    elif kind in {"ISUB_R", "IXOR_R", "IMUL_R", "IROR_R", "IROL_R"}:
        reads, writes = [rd] + ([rs] if dst != src else []), [rd]
    elif kind in {"IMULH_R", "ISMULH_R"}:
        reads, writes = [rd, rs], [rd]
    elif kind == "INEG_R":
        reads, writes = [rd], [rd]
    elif kind == "ISWAP_R":
        if dst == src:
            nop = True
        else:
            reads, writes = [rd, rs], [rd, rs]
    elif kind == "IMUL_RCP":
        nop = immediate == 0 or immediate & (immediate - 1) == 0
        if not nop:
            reads, writes = [rd], [rd]
    elif kind in {"IADD_M", "ISUB_M", "IXOR_M", "IMUL_M", "IMULH_M", "ISMULH_M"}:
        reads, writes = [rd] + ([rs] if dst != src else []), [rd]
    elif kind == "ISTORE":
        reads = [rd, rs]
    elif kind == "FSWAP_R":
        target = fd if dst < 4 else ed
        reads, writes = [target], [target]
    elif kind == "FSCAL_R":
        reads, writes = [fd], [fd]
    elif kind in {"FADD_R", "FSUB_R"}:
        reads, writes, unit = [fd, ar, "round_mode"], [fd], "float"
    elif kind in {"FADD_M", "FSUB_M"}:
        reads, writes, unit = [fd, rs, "round_mode"], [fd], "float"
    elif kind == "FMUL_R":
        reads, writes, unit = [ed, ar, "round_mode"], [ed], "float"
    elif kind == "FDIV_M":
        reads, writes, unit = [ed, rs, "round_mode", "emask"], [ed], "divsqrt"
    elif kind == "FSQRT_R":
        reads, writes, unit = [ed, "round_mode"], [ed], "divsqrt"
    elif kind == "CBRANCH":
        reads, writes, unit, barrier = [rd], [rd], "control", True
    elif kind == "CFROUND":
        reads, writes, unit, barrier = [rs, "round_mode"], ["round_mode"], "control", True
    else:
        raise AssertionError(kind)
    if kind.startswith(("IMUL", "ISMUL")) and not nop:
        unit = "multiply"
    return {
        "kind": kind, "opcode": opcode, "dst": dst, "src": src,
        "reads": sorted(set(reads)), "writes": sorted(set(writes)),
        "unit": unit, "barrier": barrier, "nop": nop,
    }


def branch_targets(program: list[int]) -> dict[int, int]:
    """Reproduce lexical integer-register usage from the pinned compiler/RTL."""
    usage = [0] * 8
    targets = {}
    for pc, word in enumerate(program):
        op = decode(word)
        if op["kind"] == "CBRANCH":
            targets[pc] = usage[op["dst"]]
            usage = [pc + 1] * 8
        else:
            for reg in op["writes"]:
                if reg.startswith("r") and reg[1:].isdigit():
                    usage[int(reg[1:])] = pc + 1
    return targets


def _records(path: Path) -> Iterable[dict]:
    with open_text(path) as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or not TRACE_COLUMNS <= set(reader.fieldnames):
            raise ValueError("event CSV is missing required columns")
        for row in reader:
            yield {key: int(value, 16 if key in {
                "sp_addr", "write_addr", "write_strb", "dataset_addr"
            } else 10) for key, value in row.items() if value != ""}


def _iteration_records(path: Path) -> list[dict]:
    result = []
    with open_text(path) as source:
        for line in source:
            fields = line.split()
            if len(fields) != 19:
                raise ValueError("native iterations.hex must have 19 fields")
            p, i, start, count, steps = map(int, fields[:5])
            result.append({"program": p, "iteration": i, "event_start": start,
                           "event_count": count, "steps": steps,
                           "route": int(fields[18], 16), "_fields": fields})
    return result


def extract(trace_path: Path, native_directory: Path, *,
            max_iterations: int = 1, max_rows: int = 500_000,
            fixture_output: Path | None = None,
            first_iteration_per_program: bool = False) -> dict:
    """Read a bounded prefix, or a compact CSV with explicit global_iteration.

    max_rows is a hard bound, including initialization rows.  An incomplete
    last iteration is rejected instead of silently treating a prefix as whole.
    A sampled CSV may have gaps only between complete iterations; its optional
    program/global_iteration columns identify corresponding native gold rows.
    """
    if max_iterations <= 0 or max_rows <= 0:
        raise ValueError("positive iteration and row bounds are required")
    if fixture_output is not None and fixture_output.exists():
        raise ValueError("fixture output must be a fresh directory; existing artifacts are preserved")
    iteration_path = native_directory / "iterations.hex"
    if not iteration_path.exists():
        iteration_path = native_directory / "iterations.hex.gz"
    event_path = native_directory / "accesses.hex"
    if not event_path.exists():
        event_path = native_directory / "accesses.hex.gz"
    gold = _iteration_records(iteration_path)
    programs = {}
    files = {"iterations": {"path": str(iteration_path), "sha256": sha256(iteration_path)}}
    # The detailed successor trace is small; the full-hash trace is multi-GB.
    # Never turn bounded extraction into a second unadmitted whole-file scan.
    for label, path in (("trace", trace_path), ("accesses", event_path)):
        size = path.stat().st_size
        files[label] = {"path": str(path), "bytes": size,
                        "sha256": sha256(path) if size <= 32 * 1024 * 1024 else None,
                        "hash_policy": "whole file only when <=32MiB; otherwise use accepted manifest"}
    operations, completed, windows, current = [], [], [], None
    fixture_rows, fixture_events, fixture_iterations, fixture_mapping = [], [], [], []
    previous = None
    read_rows, sequential_iteration, event_cursor = 0, 0, 0
    # Only native events needed for a selected iteration are streamed.  This
    # handles sampled program slices without retaining the full event stream.
    with open_text(event_path) as event_source:
        def native_event(index: int) -> tuple[bool, int, str]:
            nonlocal event_cursor
            if index < event_cursor:
                raise ValueError("native event indices must be monotonic")
            while event_cursor <= index:
                line = event_source.readline()
                if not line:
                    raise ValueError("native event stream ended early")
                packed = int(line.split()[0], 16)
                event_cursor += 1
            return bool(packed >> 21), packed & ((1 << 21) - 1), line.strip()

        def finish() -> None:
            nonlocal current, sequential_iteration
            if current is None:
                return
            reference = current["gold"]
            ops = current["ops"]
            if len(ops) != reference["steps"]:
                raise ValueError("incomplete iteration or native instruction-count mismatch")
            if current["event_count"] != reference["event_count"]:
                raise ValueError("native bytecode event-count mismatch")
            route = 0xCBF29CE484222325
            targets = branch_targets(current["program"])
            for index, op in enumerate(ops):
                next_pc = ops[index + 1]["pc"] if index + 1 < len(ops) else len(current["program"])
                if op["kind"] == "CBRANCH":
                    if next_pc not in {op["pc"] + 1, targets[op["pc"]]}:
                        raise ValueError("illegal dynamic branch target")
                elif next_pc != op["pc"] + 1:
                    raise ValueError("nonbranch PC path discontinuity")
                word = (op["pc"] << 17) | (op["opcode"] << 9) | next_pc
                route = ((route ^ word) * 0x100000001B3) & MASK64
            if route != reference["route"]:
                raise ValueError("native route checksum mismatch")
            if first_iteration_per_program and reference["iteration"] != 0:
                sequential_iteration += 1
                current = None
                return
            public_reference = {key: value for key, value in reference.items() if not key.startswith("_")}
            completed.append({**public_reference, "first_cycle": current["first_cycle"],
                              "last_cycle": current["last_cycle"],
                              "route_verified": True, "memory_addresses_verified": True})
            windows.append({"program": reference["program"], "iteration": reference["iteration"],
                            "operations": ops, "operation_count": len(ops)})
            if fixture_output is not None:
                sample_index = len(fixture_iterations)
                fields = reference["_fields"][:]
                fields[2] = str(len(fixture_events))
                fixture_iterations.append(" ".join(fields))
                fixture_mapping.append({"sample_global_iteration": sample_index,
                                        "source_global_iteration": current["global_iteration"],
                                        "source_event_start": reference["event_start"],
                                        "source_event_count": reference["event_count"]})
                fixture_events.extend(current["native_events"])
                for sampled_row in current["rows"]:
                    fixture_rows.append({**sampled_row, "program": reference["program"],
                                         "global_iteration": sample_index})
            operations.extend(ops)
            sequential_iteration += 1
            current = None

        for row in _records(trace_path):
            read_rows += 1
            if read_rows > max_rows:
                raise ValueError("row bound reached before requested complete iterations")
            cycle = row["cycle"]
            if previous and cycle <= previous["cycle"]:
                raise ValueError("trace cycles must increase strictly")
            in_kernel = row["outer_phase"] == 4 and row["iteration_phase"] == 7
            # A phase span is [previous.cycle, row.cycle).  Commit rows already
            # show the next fetch/return state, so assign the previous span to
            # the operation being retired on this row.
            if current is not None and previous is not None:
                if previous["outer_phase"] == 4 and previous["iteration_phase"] == 7:
                    current["phases"][previous["execute_phase"]] += cycle - previous["cycle"]
            if not in_kernel and current is not None:
                current["rows"].append(row)
                finish()
                if len(completed) >= max_iterations:
                    break
            if in_kernel and current is None:
                index = row.get("global_iteration", sequential_iteration)
                if not 0 <= index < len(gold):
                    raise ValueError("global iteration outside native reference")
                reference = gold[index]
                p = row.get("program", reference["program"])
                if p != reference["program"]:
                    raise ValueError("sample program does not match native reference")
                if p not in programs:
                    path = native_directory / f"program-{p}.mem"
                    with open_text(path) as source:
                        program = [int(line.strip(), 16) for line in source if line.strip()]
                    if len(program) != 384:
                        raise ValueError("only pinned-v2 384-instruction programs are supported")
                    programs[p] = program
                    files[f"program-{p}"] = {"path": str(path), "sha256": sha256(path)}
                current = {"gold": reference, "program": programs[p], "ops": [],
                           "phases": Counter(), "events": [], "event_count": 0,
                           "first_cycle": cycle, "last_cycle": cycle,
                           "rows": [], "native_events": [], "global_iteration": index}
            if current is not None and in_kernel:
                current["rows"].append(row)
                current["last_cycle"] = cycle
                if row["sp_read"]:
                    current["events"].append((False, row["sp_addr"], None))
                if row["sp_write"]:
                    current["events"].append((True, row["write_addr"], row["write_strb"]))
                if row["commit"]:
                    pc = row["pc"]
                    if not 0 <= pc < len(current["program"]):
                        raise ValueError("committed PC outside program")
                    decoded = decode(current["program"][pc])
                    is_memory = decoded["kind"] in MEMORY_KINDS
                    if len(current["events"]) != int(is_memory):
                        raise ValueError("instruction memory-handshake count mismatch")
                    memory = None
                    if is_memory:
                        observed_write, observed_address, strobe = current["events"][0]
                        write, address, native_line = native_event(reference["event_start"] + current["event_count"])
                        if write != observed_write or address // 16 * 16 != observed_address:
                            raise ValueError("native memory event address/direction mismatch")
                        if write != (decoded["kind"] == "ISTORE"):
                            raise ValueError("native event does not match decoded instruction")
                        if write and strobe != (0xFF00 if address & 8 else 0x00FF):
                            raise ValueError("native store byte lane mismatch")
                        memory = {"space": "scratchpad", "address": address, "size": 8, "write": write}
                        current["native_events"].append(native_line)
                        current["event_count"] += 1
                    phases = dict(sorted(current["phases"].items()))
                    service = sum(count for phase, count in phases.items() if phase in SERVICE_PHASES)
                    if service < 1:
                        raise ValueError("missing nonmemory execution service span")
                    current["ops"].append({
                        **decoded, "program": reference["program"], "iteration": reference["iteration"],
                        "pc": pc, "commit_cycle": cycle, "latency": service, "memory": memory,
                        "memory_then_compute": memory is not None,
                        "name": decoded["kind"], "observed_phase_cycles": phases,
                    })
                    current["phases"], current["events"] = Counter(), []
            previous = row
        else:
            if current is not None:
                raise ValueError("trace ended inside an iteration")
        if len(completed) != max_iterations:
            raise ValueError("not enough complete iterations in trace")
    if fixture_output is not None:
        fixture_output.mkdir(parents=True, exist_ok=False)
        fixture_native = fixture_output / "native"
        fixture_native.mkdir()
        (fixture_native / "iterations.hex").write_text("\n".join(fixture_iterations) + "\n")
        (fixture_native / "accesses.hex").write_text("\n".join(fixture_events) + "\n")
        for p, program in programs.items():
            (fixture_native / f"program-{p}.mem").write_text("".join(f"{word:016x}\n" for word in program))
        columns = ["cycle", "outer_phase", "iteration_phase", "execute_phase", "commit", "pc",
                   "sp_read", "sp_addr", "sp_write", "write_addr", "write_strb", "dataset", "dataset_addr",
                   "program", "global_iteration"]
        with (fixture_output / "trace.csv").open("w", newline="") as sink:
            writer = csv.DictWriter(sink, fieldnames=columns)
            writer.writeheader()
            for sampled_row in fixture_rows:
                writer.writerow({key: format(sampled_row[key], "x") if key in {
                    "sp_addr", "write_addr", "write_strb", "dataset_addr"
                } else sampled_row[key] for key in columns})
        (fixture_output / "source-map.json").write_text(json.dumps({
            "source_trace": str(trace_path), "source_native_directory": str(native_directory),
            "source_inputs": files, "windows": fixture_mapping,
            "note": "Exact bounded input slices. Small source digests are included; any null large-file digest must be bound through its accepted manifest.",
        }, indent=2, sort_keys=True) + "\n")
    # Do not reread a multi-GB trace just to hash a bounded prefix.
    return {
        "schema_version": 1, "scope": "bounded_actual_bytecode_only",
        "demonstrated_asic_performance": False, "trace_path": str(trace_path),
        "trace_rows_consumed": read_rows, "native_event_rows_consumed": event_cursor,
        "inputs": files, "iterations": completed, "operations": operations, "windows": windows,
        "operation_count": len(operations),
        "latency_provenance": "measured retained RTL nonmemory service phases 3,7,10..17 per dynamic instruction",
        "validation": {
            "actual_committed_pc_path": True, "native_route_checksums": True,
            "native_memory_event_order_addresses": True,
            "register_dependencies": "source-derived pinned-v2 decoder; CFROUND conditional write conservatively serialized",
            "alternative_microarchitecture": "unvalidated analytical scenarios",
        },
        "limitations": [
            "Bytecode only: excludes iteration entry/mixer/tail, dataset, program preparation and hash lifecycle costs.",
            "Samples the requested actual iterations; does not establish population representativeness or full-hash throughput.",
            "Exact byte addresses are trace replay inputs; dependence readiness is enforced but address-generation circuitry is not modeled.",
            "Macro-operations reserve their functional unit at issue, including memory operations; no split load/FU pipeline is validated.",
            "Memory macro-operations add measured nonmemory service and transfer/response service serially; this conservatively accounts for address EXEC without predicting phase placement.",
            "CBRANCH and CFROUND are context barriers; speculation and more precise conditional-rounding overlap are unsupported.",
            "Observed service times are those of accepted RTL on this path; new FU latencies/initiation intervals are assumptions.",
            "No register values or arithmetic results are recomputed; native route/address checks supplement existing accepted RTL equivalence.",
            "Initial hash, fill, program generation and light-dataset host provider device costs remain unknown and excluded.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--native-directory", required=True, type=Path)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--max-rows", type=int, default=500_000)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-output", type=Path)
    parser.add_argument("--first-iteration-per-program", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file; existing artifacts are preserved")
    result = extract(args.trace, args.native_directory,
                     max_iterations=args.iterations, max_rows=args.max_rows,
                     fixture_output=args.fixture_output,
                     first_iteration_per_program=args.first_iteration_per_program)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as sink:
        sink.write(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
