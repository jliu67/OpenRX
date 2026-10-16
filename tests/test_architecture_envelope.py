import math
import unittest

from tools.architecture import envelope as e


class EnvelopeTests(unittest.TestCase):
    def test_nested_scratchpad_capacity_and_pooling(self):
        v = e.capacity(16, 256 * 1024)
        self.assertEqual(v["logical_state_bytes"], 32 * 1024**2)
        self.assertEqual(v["on_chip_image_bytes"] + v["external_backing_bytes"], v["logical_state_bytes"])
        self.assertIsNone(v["metadata_ecc_queues_registers_program_bytes"])
        self.assertFalse(v["shared_pool_saves_active_image_bits"])

    def test_traffic_counts_outer_and_scan_not_only_bytecode(self):
        cold = dict(bytecode_read8=3, bytecode_write8=2, outer_read64=4, outer_write64=4)
        p = e.external_prefix(cold, 256 * 1024)
        stream = 2 * (2 * 1024**2 - 256 * 1024)
        self.assertEqual(p["external_transfer_bytes_per_hash"], 5 * 64 + 8 * 64 + stream)
        self.assertEqual(p["algorithmic_cold_bytes_per_hash"], 5 * 8 + 8 * 64 + stream)
        rmw = e.external_prefix(cold, 256 * 1024, store_rmw=True)
        self.assertEqual(rmw["external_transfer_bytes_per_hash"] - p["external_transfer_bytes_per_hash"], 2 * 64)
        self.assertEqual(rmw["external_transactions_per_hash"] - p["external_transactions_per_hash"], 2)

    def test_littles_law_and_port_units(self):
        v = e.latency_requirement(1e6, 82003, 100e-9, 2)
        self.assertEqual(v["necessary_outstanding_requests"], 8201)
        self.assertEqual(v["necessary_contexts_if_ready_limit_is_valid"], 4101)
        c = dict(bytecode_read8=1, bytecode_write8=1, outer_read64=2, outer_write64=2)
        self.assertEqual(e.port_operations(c, 16), 2 + 16 + 2 * e.SCRATCHPAD_BYTES // 16)

    def test_unknown_energy_does_not_become_zero(self):
        p = e.full_wall_power(1e6, {"compute": 0}, {}, .9, 0)
        self.assertIsNone(p["wall_power_w"])
        self.assertIn("dynamic.input_hash_fill_program_dataset_generation", p["missing"])

    def test_complete_conditional_power_includes_psu_once(self):
        dynamic = dict.fromkeys(e.ENERGY_TERMS, 0)
        dynamic["compute"] = .001
        static = dict.fromkeys(e.STATIC_TERMS, 0)
        static["fans"] = 80
        p = e.full_wall_power(1e6, dynamic, static, .9, 20)
        self.assertEqual(p["wall_power_w"], 1220)
        self.assertEqual(p["wall_j_per_hash"], .00122)

    def test_rejection_boundaries_are_strict_and_independent(self):
        args = dict(hps=1e6, wall_w=2499, required_bandwidth=2, available_bandwidth=2,
                    required_capacity=2, available_capacity=2, required_outstanding=2,
                    supported_outstanding=2, correctness=True,
                    required_transactions_per_s=2, available_transactions_per_s=2,
                    required_bank_port_operations_per_s=2, available_bank_port_operations_per_s=2,
                    controller_service_constraints_satisfied=True)
        self.assertEqual(e.rejection_gate(**args)["status"], "conditional_inputs_pass")
        self.assertFalse(e.rejection_gate(**args)["demonstrated_asic_feasibility"])
        args["wall_w"] = 2500
        self.assertIn("wall_power_not_below_2500W", e.rejection_gate(**args)["rejections"])
        args["available_capacity"] = 1
        self.assertEqual(len(e.rejection_gate(**args)["rejections"]), 2)

    def test_omitted_memory_service_constraints_stay_unresolved(self):
        args = dict(hps=1e6, wall_w=2499, required_bandwidth=2, available_bandwidth=2,
                    required_capacity=2, available_capacity=2, required_outstanding=2,
                    supported_outstanding=2, correctness=True)
        gate = e.rejection_gate(**args)
        self.assertEqual(gate["status"], "unresolved")
        self.assertEqual(set(gate["unknown"]), {
            "sustainable_transactions_per_s", "bank_port_operations_per_s",
            "controller_bank_timing_turnaround_refresh_tail_latency",
        })
        self.assertFalse(gate["demonstrated_asic_feasibility"])
        for field, value in (
            ("required_transactions_per_s", 2), ("available_transactions_per_s", 2),
            ("required_bank_port_operations_per_s", 2), ("available_bank_port_operations_per_s", 2),
            ("controller_service_constraints_satisfied", True),
        ):
            args[field] = value
        for omitted in ("required_transactions_per_s", "available_transactions_per_s",
                        "required_bank_port_operations_per_s", "available_bank_port_operations_per_s",
                        "controller_service_constraints_satisfied"):
            with self.subTest(omitted=omitted):
                partial = {k: v for k, v in args.items() if k != omitted}
                self.assertEqual(e.rejection_gate(**partial)["status"], "unresolved")

    def test_memory_service_constraints_reject_independently(self):
        args = dict(hps=1e6, wall_w=2499, required_bandwidth=2, available_bandwidth=2,
                    required_capacity=2, available_capacity=2, required_outstanding=2,
                    supported_outstanding=2, correctness=True,
                    required_transactions_per_s=2, available_transactions_per_s=2,
                    required_bank_port_operations_per_s=2, available_bank_port_operations_per_s=2,
                    controller_service_constraints_satisfied=True)
        for field, value, reason in (
            ("available_transactions_per_s", 1, "sustainable_transactions_per_s_exceeded"),
            ("available_bank_port_operations_per_s", 1, "bank_port_operations_per_s_exceeded"),
            ("controller_service_constraints_satisfied", False, "controller_service_constraints_failed"),
        ):
            with self.subTest(field=field):
                gate = e.rejection_gate(**{**args, field: value})
                self.assertEqual(gate["status"], "rejected")
                self.assertEqual(gate["rejections"], [reason])

    def test_invalid_inputs(self):
        for value in (math.nan, math.inf, -1, True):
            with self.assertRaises(ValueError):
                e.positive(value)
        for args in ((0, 0), (1, 1), (1, e.SCRATCHPAD_BYTES + 64)):
            with self.assertRaises(ValueError):
                e.capacity(*args)
        with self.assertRaises(ValueError):
            e.full_wall_power(1e6, {}, {}, 1.1, 0)
        with self.assertRaises(ValueError):
            e.full_wall_power(1e6, {"unbudgeted": 1}, {}, .9, 0)
        with self.assertRaises(ValueError):
            e.rejection_gate(correctness="false")
        for value in (0, 1, "true"):
            with self.subTest(controller_value=value), self.assertRaises(ValueError):
                e.rejection_gate(controller_service_constraints_satisfied=value)
        for field in ("required_transactions_per_s", "available_transactions_per_s",
                      "required_bank_port_operations_per_s", "available_bank_port_operations_per_s"):
            for value in (math.nan, math.inf, -1, True):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    e.rejection_gate(**{field: value})


if __name__ == "__main__":
    unittest.main()
