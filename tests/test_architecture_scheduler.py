"""Small exact schedules test constraints, not a claimed RandomX speedup."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.architecture.scheduler import Config, MemoryAccess, MemorySpec, MicroOp, UnitSpec, simulate


def replay(ops, **overrides):
    values = {"blocking_context": False, "issue_window": 8,
              "units": {"integer": UnitSpec(count=2), "float": UnitSpec()}}
    values.update(overrides)
    return simulate(ops, Config(**values), capture_schedule=True)


def issue_times(result, context=0):
    return {row["index"]: row["issue"] for row in result["schedule"] if row["context"] == context}


class SchedulerTests(unittest.TestCase):
    def test_empty_program_and_json_round_trip(self):
        result = simulate([], Config(contexts=4))
        self.assertEqual((result["cycles"], result["operations"]), (0, 0))
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_blocking_context_is_not_hidden_pipeline(self):
        ops = [MicroOp(latency=5), MicroOp(latency=3)]
        result = replay(ops, blocking_context=True)
        self.assertEqual(issue_times(result), {0: 0, 1: 5})
        self.assertEqual(result["cycles"], 8)

    def test_raw_waw_war_wait_for_completion(self):
        hazards = [(MicroOp(writes=("r0",), latency=5), MicroOp(reads=("r0",))),
                   (MicroOp(writes=("r0",), latency=5), MicroOp(writes=("r0",))),
                   (MicroOp(reads=("r0",), latency=5), MicroOp(writes=("r0",)))]
        for older, younger in hazards:
            with self.subTest(older=older, younger=younger):
                result = replay([older, younger], issue_width=2)
                self.assertEqual(issue_times(result), {0: 0, 1: 5})

    def test_unissued_older_writer_cannot_be_bypassed_by_dependent(self):
        ops = [MicroOp(writes=("gate",), latency=5),
               MicroOp(reads=("gate",), writes=("r0",)),
               MicroOp(reads=("r0",)), MicroOp(writes=("independent",))]
        result = replay(ops, issue_width=2)
        self.assertEqual(issue_times(result), {0: 0, 3: 0, 1: 5, 2: 6})

    def test_issue_window_bounds_ready_lookahead(self):
        ops = [MicroOp(writes=("gate",), latency=5),
               MicroOp(reads=("gate",)), MicroOp()]
        result = replay(ops, issue_width=2, issue_window=1)
        self.assertEqual(issue_times(result), {0: 0, 1: 5, 2: 5})
        # Window=1 permits in-order dual issue, but never bypasses index 1.

    def test_issued_holes_still_consume_window_trace_positions(self):
        ops = [MicroOp(writes=("gate",), latency=5), MicroOp(reads=("gate",)),
               MicroOp(), MicroOp()]
        result = replay(ops, issue_width=3, issue_window=2)
        self.assertEqual(issue_times(result), {0: 0, 2: 0, 1: 5, 3: 5})

    def test_context_registers_are_isolated_and_issue_is_shared(self):
        ops = [MicroOp(reads=("r0",), writes=("r0",), latency=5)]
        result = replay(ops, contexts=2, issue_width=2)
        self.assertEqual(result["cycles"], 5)
        self.assertEqual([r["issue"] for r in result["schedule"]], [0, 0])
        self.assertEqual(result["cycles_per_job"], 2.5)
        limited = replay(ops, contexts=2, issue_width=1)
        self.assertEqual(limited["cycles"], 6)

    def test_latency_and_initiation_interval_are_distinct(self):
        ops = [MicroOp(latency=5) for _ in range(3)]
        pipelined = replay(ops, units={"integer": UnitSpec(initiation_interval=2)})
        nonpipelined = replay(ops, units={"integer": UnitSpec(nonpipelined=True)})
        self.assertEqual(issue_times(pipelined), {0: 0, 1: 2, 2: 4})
        self.assertEqual(pipelined["cycles"], 9)
        self.assertEqual(issue_times(nonpipelined), {0: 0, 1: 5, 2: 10})
        self.assertEqual(nonpipelined["cycles"], 15)

    def test_functional_unit_counts_are_enforced(self):
        ops = [MicroOp(latency=4), MicroOp(latency=4), MicroOp(latency=4)]
        result = replay(ops, issue_width=3, units={"integer": UnitSpec(count=2, nonpipelined=True)})
        self.assertEqual(issue_times(result), {0: 0, 1: 0, 2: 4})

    def test_barriers_drain_and_hold_younger_work(self):
        ops = [MicroOp(latency=5), MicroOp(unit="float", latency=2, barrier=True), MicroOp()]
        result = replay(ops, issue_width=2)
        self.assertEqual(issue_times(result), {0: 0, 1: 5, 2: 7})

    def test_strict_memory_order_serializes_even_nonalias_reads(self):
        ops = [MicroOp(memory=MemoryAccess("scratchpad", x, 8)) for x in (0, 8)]
        spec = MemorySpec(banks=2, latency=5, max_outstanding=2, bytes_per_cycle=16)
        result = replay(ops, issue_width=2, memory={"scratchpad": spec})
        self.assertEqual(issue_times(result), {0: 0, 1: 6})
        relaxed = replay(ops, issue_width=2, memory={"scratchpad": spec}, memory_order="address")
        self.assertEqual(issue_times(relaxed), {0: 0, 1: 0})

    def test_address_memory_order_preserves_aliases_and_unknowns(self):
        spec = MemorySpec(banks=2, ports_per_bank=2, latency=5, max_outstanding=4, bytes_per_cycle=32)
        for address in (4, None):
            ops = [MicroOp(memory=MemoryAccess("scratchpad", 0, 8, write=True)),
                   MicroOp(memory=MemoryAccess("scratchpad", address, 8)),
                   MicroOp(memory=MemoryAccess("scratchpad", 16, 8))]
            result = replay(ops, issue_width=3, memory={"scratchpad": spec}, memory_order="address")
            self.assertEqual(issue_times(result), {0: 0, 2: 0, 1: 6})

    def test_load_before_aliasing_store_preserves_memory_war(self):
        ops = [MicroOp(memory=MemoryAccess("scratchpad", 0, 8)),
               MicroOp(memory=MemoryAccess("scratchpad", 0, 8, write=True))]
        result = replay(ops, issue_width=2, memory_order="address",
                        memory={"scratchpad": MemorySpec(latency=5, max_outstanding=2)})
        self.assertEqual(issue_times(result), {0: 0, 1: 6})

    def test_mutable_address_zero_is_isolated_across_contexts(self):
        ops = [MicroOp(memory=MemoryAccess("scratchpad", 0, 8, write=True))]
        spec = MemorySpec(ports_per_bank=2, bytes_per_cycle=16, latency=5, max_outstanding=2)
        result = replay(ops, contexts=2, issue_width=2, memory={"scratchpad": spec})
        self.assertEqual(result["cycles"], 6)
        self.assertEqual([r["issue"] for r in result["schedule"]], [0, 0])

    def test_bank_ports_are_a_constraint_independent_of_bytes(self):
        spec = MemorySpec(banks=2, bytes_per_cycle=16, max_outstanding=4)
        same = [MicroOp(memory=MemoryAccess("scratchpad", x, 8)) for x in (0, 16)]
        different = [MicroOp(memory=MemoryAccess("scratchpad", x, 8)) for x in (0, 8)]
        kwargs = {"issue_width": 2, "memory": {"scratchpad": spec}, "memory_order": "address"}
        self.assertEqual(issue_times(replay(same, **kwargs)), {0: 0, 1: 1})
        self.assertEqual(issue_times(replay(different, **kwargs)), {0: 0, 1: 0})

    def test_bandwidth_reservations_cover_future_transfer_cycles(self):
        spec = MemorySpec(banks=2, bytes_per_cycle=8, latency=2, max_outstanding=4)
        ops = [MicroOp(memory=MemoryAccess("scratchpad", 0, 16)),
               MicroOp(memory=MemoryAccess("scratchpad", 24, 8))]
        result = replay(ops, issue_width=2, memory={"scratchpad": spec}, memory_order="address")
        self.assertEqual(issue_times(result), {0: 0, 1: 2})
        self.assertEqual(result["cycles"], 5)
        self.assertEqual(result["memory_bytes_by_space"], {"scratchpad": 24})

    def test_queue_capacity_includes_response_latency(self):
        ops = [MicroOp(memory=MemoryAccess("dataset", x, 8)) for x in (0, 8)]
        spec = MemorySpec(banks=2, bytes_per_cycle=16, latency=10, max_outstanding=1)
        result = replay(ops, issue_width=2, memory={"dataset": spec}, memory_order="address")
        self.assertEqual(issue_times(result), {0: 0, 1: 11})
        self.assertEqual(result["cycles"], 22)

    def test_load_dependent_compute_starts_after_memory_response(self):
        ops = [MicroOp(latency=5, memory=MemoryAccess("scratchpad", 0, 8),
                       memory_then_compute=True), MicroOp()]
        spec = MemorySpec(latency=10, max_outstanding=2)
        result = replay(ops, issue_width=2, units={"integer": UnitSpec()},
                        memory={"scratchpad": spec})
        self.assertEqual(issue_times(result), {0: 0, 1: 16})
        self.assertEqual(result["schedule"][0]["complete"], 16)
        self.assertEqual(result["cycles"], 17)

    def test_private_fabrics_do_not_accidentally_share_bandwidth(self):
        ops = [MicroOp(memory=MemoryAccess("scratchpad", 0, 8))]
        private = MemorySpec(shared=False)
        shared = MemorySpec(shared=True)
        kwargs = {"contexts": 2, "issue_width": 2}
        self.assertEqual(replay(ops, memory={"scratchpad": private}, **kwargs)["cycles"], 1)
        self.assertEqual(replay(ops, memory={"scratchpad": shared}, **kwargs)["cycles"], 2)

    def test_json_input_and_rejection_guards(self):
        op = MicroOp.from_dict({"reads": ["r0"], "memory": {"space": "dataset", "address": 0, "size": 64}})
        cfg = Config.from_dict({"units": {"integer": {}}, "memory": {"dataset": {"bytes_per_cycle": 8}}})
        self.assertEqual(simulate([op], cfg)["cycles"], 8)
        with self.assertRaisesRegex(ValueError, "read-only"):
            MemoryAccess("dataset", 0, 8, write=True)
        with self.assertRaisesRegex(ValueError, "shared"):
            Config(memory={"dataset": MemorySpec(shared=False)})
        with self.assertRaisesRegex(ValueError, "missing unit"):
            simulate([MicroOp(unit="unknown")], Config())
        with self.assertRaisesRegex(ValueError, "missing memory"):
            simulate([op], Config())
        with self.assertRaisesRegex(ValueError, "integer"):
            UnitSpec(initiation_interval=0)
        with self.assertRaisesRegex(ValueError, "integer"):
            MemorySpec(bytes_per_cycle=True)
        with self.assertRaisesRegex(ValueError, "integer"):
            MicroOp(latency=0)
        with self.assertRaisesRegex(ValueError, "requires"):
            MicroOp(memory_then_compute=True)


if __name__ == "__main__":
    unittest.main()
