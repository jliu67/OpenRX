"""Deterministic, dependency-constrained architectural trace replay.

This is an analytical scheduler, not a circuit simulator.  All instruction
latencies, functional-unit initiation intervals, and memory parameters are
inputs.  A concrete dynamic trace fixes control flow and addresses; replay does
not predict branches or prove that a wider implementation is correct.

Time is integral cycles.  An operation issued at t with latency L makes its
register results available at t+L.  Memory transfers reserve a shared byte
budget in each service cycle and the touched bank ports through the end of
transfer.  MemorySpec.latency is *additional* response latency after transfer;
completion is max(t+L, transfer_end+response_latency).  Thus neither request
service nor response latency is silently fitted into the instruction latency.
For a memory_then_compute macro-operation, completion is instead
transfer_end+response_latency+L and its functional unit is conservatively held
for the entire macro-operation.  This prevents load-dependent arithmetic from
executing before the response or using an unreserved unit after it arrives.

Register names and mutable memory are isolated per context.  Fabric resources
are shared unless MemorySpec.shared=False; dataset is always shared/read-only.
Unknown addresses conservatively alias every address in the same space.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import heapq
from typing import Any, Mapping, Sequence


def _integer(name: str, value: int, minimum: int = 1) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


@dataclass(frozen=True)
class MemoryAccess:
    space: str
    address: int | None
    size: int
    write: bool = False

    def __post_init__(self) -> None:
        if not self.space:
            raise ValueError("memory space must be nonempty")
        _integer("memory size", self.size)
        if self.address is not None:
            _integer("memory address", self.address, 0)
        if self.space == "dataset" and self.write:
            raise ValueError("dataset is read-only")


@dataclass(frozen=True)
class MicroOp:
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    unit: str = "integer"
    latency: int = 1
    memory: MemoryAccess | None = None
    barrier: bool = False
    name: str = ""
    memory_then_compute: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "reads", tuple(self.reads))
        object.__setattr__(self, "writes", tuple(self.writes))
        if not self.unit or any(not isinstance(r, str) or not r for r in self.reads + self.writes):
            raise ValueError("unit and register names must be nonempty strings")
        _integer("operation latency", self.latency)
        if self.memory is not None and not isinstance(self.memory, MemoryAccess):
            raise ValueError("memory must be a MemoryAccess")
        if self.memory_then_compute and self.memory is None:
            raise ValueError("memory_then_compute requires a memory access")

    @classmethod
    def from_dict(cls, record: Mapping[str, Any]) -> "MicroOp":
        values = dict(record)
        if values.get("memory") is not None:
            values["memory"] = MemoryAccess(**values["memory"])
        return cls(**values)


@dataclass(frozen=True)
class UnitSpec:
    count: int = 1
    initiation_interval: int = 1
    nonpipelined: bool = False

    def __post_init__(self) -> None:
        _integer("unit count", self.count)
        _integer("unit initiation interval", self.initiation_interval)


@dataclass(frozen=True)
class MemorySpec:
    banks: int = 1
    ports_per_bank: int = 1
    bytes_per_cycle: int = 8
    latency: int = 0
    max_outstanding: int = 1
    bank_width: int = 8
    shared: bool = True
    read_only: bool = False

    def __post_init__(self) -> None:
        for name in ("banks", "ports_per_bank", "bytes_per_cycle", "max_outstanding", "bank_width"):
            _integer(f"memory {name}", getattr(self, name))
        _integer("memory latency", self.latency, 0)


@dataclass(frozen=True)
class Config:
    contexts: int = 1
    issue_width: int = 1
    blocking_context: bool = True
    issue_window: int = 1
    units: Mapping[str, UnitSpec] = field(default_factory=lambda: {"integer": UnitSpec()})
    memory: Mapping[str, MemorySpec] = field(default_factory=dict)
    memory_order: str = "strict"

    def __post_init__(self) -> None:
        for name in ("contexts", "issue_width", "issue_window"):
            _integer(name, getattr(self, name))
        if self.memory_order not in ("strict", "address"):
            raise ValueError("memory_order must be strict or address")
        if any(not isinstance(v, UnitSpec) for v in self.units.values()):
            raise ValueError("units must contain UnitSpec values")
        if any(not isinstance(v, MemorySpec) for v in self.memory.values()):
            raise ValueError("memory must contain MemorySpec values")
        if "dataset" in self.memory and not self.memory["dataset"].shared:
            raise ValueError("dataset fabric must be shared")

    @classmethod
    def from_dict(cls, record: Mapping[str, Any]) -> "Config":
        values = dict(record)
        if "units" in values:
            values["units"] = {k: UnitSpec(**v) for k, v in values["units"].items()}
        if "memory" in values:
            values["memory"] = {k: MemorySpec(**v) for k, v in values["memory"].items()}
        return cls(**values)


def _register_conflict(older: MicroOp, younger: MicroOp) -> bool:
    """No renaming: RAW, WAW and WAR all constrain issue until completion."""
    return bool(set(older.writes).intersection(younger.reads + younger.writes)
                or set(older.reads).intersection(younger.writes))


def _memory_conflict(older: MemoryAccess, younger: MemoryAccess, order: str) -> bool:
    if order == "strict":
        return True
    if older.space != younger.space or not (older.write or younger.write):
        return False
    if older.address is None or younger.address is None:
        return True
    return older.address < younger.address + younger.size and younger.address < older.address + older.size


def _banks(access: MemoryAccess, spec: MemorySpec) -> tuple[int, ...]:
    if access.address is None:
        return tuple(range(spec.banks))
    first = access.address // spec.bank_width
    last = (access.address + access.size - 1) // spec.bank_width
    if last - first + 1 >= spec.banks:
        return tuple(range(spec.banks))
    return tuple(i % spec.banks for i in range(first, last + 1))


def simulate(program: Sequence[MicroOp], config: Config, *, capture_schedule: bool = False) -> dict[str, Any]:
    """Replay one fixed dynamic program independently in every context.

    The issue window is a fixed span of trace positions starting at the oldest
    unissued operation; already issued holes within that span count toward its
    bound, while older outstanding operations do not.  There is no
    hidden register renaming, speculative control flow, cache, forwarding or
    unlimited memory queue.  Barriers (e.g. CBRANCH/CFROUND) drain older work and
    hold all younger work until complete.  Stalls are candidate-check counts,
    not disjoint categories of elapsed cycles.
    """
    program = tuple(program)
    if any(not isinstance(op, MicroOp) for op in program):
        raise ValueError("program must contain MicroOp values")
    for op in program:
        if op.unit not in config.units:
            raise ValueError(f"missing unit specification: {op.unit}")
        if op.memory is not None:
            if op.memory.space not in config.memory:
                raise ValueError(f"missing memory specification: {op.memory.space}")
            if op.memory.write and config.memory[op.memory.space].read_only:
                raise ValueError(f"write to read-only space: {op.memory.space}")

    # next[i] is the oldest not-yet-issued operation; ahead holds issued holes.
    frontier = [0] * config.contexts
    ahead: list[set[int]] = [set() for _ in range(config.contexts)]
    inflight: list[dict[int, int]] = [{} for _ in range(config.contexts)]
    last_completion = [0] * config.contexts
    unit_ready = {name: [0] * spec.count for name, spec in config.units.items()}
    # A private fabric has independent ports/byte budget/queue for each context.
    fabrics: dict[tuple[str, int | None], dict[str, Any]] = {}
    for space, spec in config.memory.items():
        for ctx in ([None] if spec.shared else range(config.contexts)):
            fabrics[(space, ctx)] = {"ports": [[0] * spec.ports_per_bank for _ in range(spec.banks)],
                                      "bytes": {}, "outstanding": 0}

    events: list[tuple[int, int, int, int, tuple[str, int | None] | None]] = []
    serial = 0
    cycle = 0
    issued = 0
    completed = 0
    rr_context = 0
    idle_cycles = 0
    max_inflight = 0
    blocked: Counter[str] = Counter()
    by_unit: Counter[str] = Counter()
    by_space: Counter[str] = Counter()
    schedule: list[dict[str, Any]] = []
    total = len(program) * config.contexts

    def candidate(ctx: int, index: int) -> tuple[str | None, Any]:
        op = program[index]
        if config.blocking_context and inflight[ctx]:
            return "context_blocking", None
        older_pending = [program[i] for i in range(frontier[ctx], index) if i not in ahead[ctx]]
        if any(p.barrier for p in older_pending) or any(program[i].barrier for i in inflight[ctx] if i < index):
            return "barrier", None
        if op.barrier and (older_pending or any(i < index for i in inflight[ctx])):
            return "barrier", None
        if any(_register_conflict(p, op) for p in older_pending):
            return "dependency", None
        if any(_register_conflict(program[i], op) for i in inflight[ctx] if i < index):
            return "dependency", None
        # A younger issued op can still be active when an older stalled op
        # becomes ready.  Dependency checks at younger issue prevented aliases;
        # resources remain shared, but no reversed dependency is introduced.
        if op.memory is not None:
            if any(p.memory is not None and _memory_conflict(p.memory, op.memory, config.memory_order)
                   for p in older_pending):
                return "memory_order", None
            if any(program[i].memory is not None
                   and _memory_conflict(program[i].memory, op.memory, config.memory_order)
                   for i in inflight[ctx] if i < index):
                return "memory_order", None
        slots = unit_ready[op.unit]
        slot = min(range(len(slots)), key=slots.__getitem__)
        if slots[slot] > cycle:
            return "unit_initiation_interval", None
        finish = cycle + op.latency
        mem_plan = None
        if op.memory is not None:
            access = op.memory
            spec = config.memory[access.space]
            key = (access.space, None if spec.shared else ctx)
            fabric = fabrics[key]
            if fabric["outstanding"] >= spec.max_outstanding:
                return "memory_outstanding", None
            selected_ports = []
            for bank in _banks(access, spec):
                ports = fabric["ports"][bank]
                port = min(range(len(ports)), key=ports.__getitem__)
                if ports[port] > cycle:
                    return "memory_bank_port", None
                selected_ports.append((bank, port))
            if fabric["bytes"].get(cycle, 0) >= spec.bytes_per_cycle:
                return "memory_bandwidth", None
            # Reserve transfer bytes against *every* cycle, including previously
            # reserved future service.  Partial first/last cycles can be shared.
            remaining = access.size
            service = []
            service_cycle = cycle
            while remaining:
                available = spec.bytes_per_cycle - fabric["bytes"].get(service_cycle, 0)
                take = min(available, remaining)
                if take:
                    service.append((service_cycle, take))
                    remaining -= take
                service_cycle += 1
            response = service_cycle + spec.latency
            finish = response + op.latency if op.memory_then_compute else max(finish, response)
            mem_plan = (key, selected_ports, service, service_cycle)
        return None, (slot, finish, mem_plan)

    while completed < total:
        while events and events[0][0] <= cycle:
            _, _, ctx, index, key = heapq.heappop(events)
            del inflight[ctx][index]
            if key is not None:
                fabrics[key]["outstanding"] -= 1
            completed += 1
        if completed == total:
            break
        issued_this_cycle = 0
        while issued_this_cycle < config.issue_width:
            choice = None
            for offset in range(config.contexts):
                ctx = (rr_context + offset) % config.contexts
                stop = min(len(program), frontier[ctx] + config.issue_window)
                for index in range(frontier[ctx], stop):
                    if index in ahead[ctx]:
                        continue
                    reason, plan = candidate(ctx, index)
                    if reason:
                        blocked[reason] += 1
                        continue
                    choice = (ctx, index, plan)
                    break
                if choice is not None:
                    break
            if choice is None:
                break
            ctx, index, (slot, finish, mem_plan) = choice
            op = program[index]
            spec = config.units[op.unit]
            unit_ready[op.unit][slot] = max(cycle + spec.initiation_interval,
                                          finish if spec.nonpipelined or op.memory_then_compute else cycle)
            key = None
            if mem_plan is not None:
                key, selected_ports, service, transfer_end = mem_plan
                fabric = fabrics[key]
                for bank, port in selected_ports:
                    fabric["ports"][bank][port] = transfer_end
                for t, size in service:
                    fabric["bytes"][t] = fabric["bytes"].get(t, 0) + size
                fabric["outstanding"] += 1
                by_space[op.memory.space] += op.memory.size
            inflight[ctx][index] = finish
            last_completion[ctx] = max(last_completion[ctx], finish)
            ahead[ctx].add(index)
            while frontier[ctx] in ahead[ctx]:
                ahead[ctx].remove(frontier[ctx])
                frontier[ctx] += 1
            serial += 1
            heapq.heappush(events, (finish, serial, ctx, index, key))
            issued += 1
            by_unit[op.unit] += 1
            issued_this_cycle += 1
            rr_context = (ctx + 1) % config.contexts
            max_inflight = max(max_inflight, sum(map(len, inflight)))
            if capture_schedule:
                schedule.append({"context": ctx, "index": index, "name": op.name,
                                 "issue": cycle, "complete": finish})
        if issued_this_cycle:
            cycle += 1
        else:
            # No eligible operation: skip to a real resource/completion change.
            future = [event[0] for event in events]
            future.extend(t for slots in unit_ready.values() for t in slots if t > cycle)
            for fabric in fabrics.values():
                future.extend(t for ports in fabric["ports"] for t in ports if t > cycle)
                if fabric["bytes"].get(cycle, 0):
                    future.append(cycle + 1)
            if not future:
                raise RuntimeError("scheduler deadlock with no future resource event")
            next_cycle = min(t for t in future if t > cycle)
            idle_cycles += next_cycle - cycle
            cycle = next_cycle
        # Service reservations before the current cycle can never be consulted.
        for fabric in fabrics.values():
            stale = [t for t in fabric["bytes"] if t < cycle]
            for t in stale:
                del fabric["bytes"][t]

    result: dict[str, Any] = {
        "cycles": max(last_completion, default=0), "operations": issued,
        "contexts": config.contexts, "jobs_completed": config.contexts,
        "cycles_per_job": max(last_completion, default=0) / config.contexts,
        "per_context_completion_cycles": last_completion,
        "idle_cycles": idle_cycles, "max_inflight": max_inflight,
        "issued_by_unit": dict(sorted(by_unit.items())),
        "memory_bytes_by_space": dict(sorted(by_space.items())),
        "blocked_candidate_checks": dict(sorted(blocked.items())),
        "validation_status": "analytical_replay_requires_external_validation",
    }
    if capture_schedule:
        result["schedule"] = schedule
    return result
