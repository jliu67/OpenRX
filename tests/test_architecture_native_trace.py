# SPDX-License-Identifier: BSD-3-Clause
"""Dependency and evidence-corruption tests, without a native/RTL rerun."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from tools.architecture.native_trace import branch_targets, decode, extract


def instruction(opcode, dst=0, src=1, immediate=0):
    return opcode | (dst << 8) | (src << 16) | (immediate << 32)


def synthetic_fixture(directory):
    """A complete 384-PC path with exact read/store lane and service samples."""
    native = directory / "native"
    native.mkdir()
    program = [instruction(84)] * 384  # INEG_R
    program[0] = instruction(16)      # IADD_M
    program[1] = instruction(240)     # ISTORE
    program[2] = instruction(239)     # CFROUND
    (native / "program-0.mem").write_text("".join(f"{word:016x}\n" for word in program))
    (native / "accesses.hex").write_text("1238 deadbeef\n202340 cafe\n")
    route = 0xCBF29CE484222325
    for pc, word in enumerate(program):
        route = ((route ^ ((pc << 17) | ((word & 255) << 9) | (pc + 1))) * 0x100000001B3) & ((1 << 64) - 1)
    fields = ["0", "0", "0", "2", "384"] + ["0"] * 13 + [f"{route:x}"]
    (native / "iterations.hex").write_text(" ".join(fields) + "\n")
    columns = ["cycle", "outer_phase", "iteration_phase", "execute_phase", "commit", "pc",
               "sp_read", "sp_addr", "sp_write", "write_addr", "write_strb", "dataset", "dataset_addr"]
    rows = []

    def row(cycle, phase, commit=0, pc=0, read=0, write=0, end=False):
        rows.append(dict(zip(columns, [cycle, 4, 8 if end else 7, phase, commit, pc,
                                      read, "1230" if read else "0", write,
                                      "2340" if write else "0", "ff", 0, "0"])))

    cycle = 0
    row(cycle, 1)
    for pc in range(384):
        row(cycle + 1, 2)
        row(cycle + 2, 3)
        if pc == 0:
            row(cycle + 3, 4, read=1)
            row(cycle + 4, 5)
            cycle += 5
        elif pc == 1:
            row(cycle + 3, 6, write=1)
            cycle += 4
        else:
            cycle += 3
        row(cycle, 1, commit=1, pc=pc)
    row(cycle + 1, 0, end=True)
    path = directory / "trace.csv"
    with path.open("w", newline="") as source:
        writer = csv.DictWriter(source, columns)
        writer.writeheader()
        writer.writerows(rows)
    return path, native, rows, columns


class DecodeTests(unittest.TestCase):
    def test_register_immediate_and_high_multiply_dependencies(self):
        self.assertEqual(decode(instruction(23, 3, 3))["reads"], ["r3"])
        self.assertEqual(decode(instruction(0, 3, 3))["reads"], ["r3"])
        self.assertEqual(decode(instruction(66, 3, 3))["reads"], ["r3"])
        op = decode(instruction(66, 3, 4))
        self.assertEqual(op["reads"], ["r3", "r4"])
        self.assertEqual(op["unit"], "multiply")

    def test_reciprocal_and_swap_nops_do_not_create_false_writes(self):
        for immediate in [0, 1, 2, 8, 1 << 31]:
            op = decode(instruction(76, immediate=immediate))
            self.assertTrue(op["nop"])
            self.assertEqual(op["writes"], [])
        self.assertEqual(decode(instruction(76, immediate=3))["writes"], ["r0"])
        self.assertEqual(decode(instruction(116, 2, 2))["writes"], [])
        self.assertEqual(decode(instruction(116, 2, 3))["writes"], ["r2", "r3"])

    def test_floating_register_banks_and_rounding(self):
        self.assertEqual(decode(instruction(120, 6))["writes"], ["e2"])
        self.assertEqual(decode(instruction(120, 2))["writes"], ["f2"])
        self.assertEqual(decode(instruction(172, 6, 7))["reads"], ["a3", "e2", "round_mode"])
        div = decode(instruction(204, 6, 7))
        self.assertEqual(div["writes"], ["e2"])
        self.assertIn("r7", div["reads"])
        self.assertEqual(div["unit"], "divsqrt")
        cf = decode(instruction(239, src=4))
        self.assertEqual(cf["reads"], ["r4", "round_mode"])
        self.assertEqual(cf["writes"], ["round_mode"])
        self.assertTrue(cf["barrier"])

    def test_branch_target_uses_lexical_writes_not_fp_or_nops(self):
        program = [instruction(76, 2, immediate=8),  # reciprocal NOP
                   instruction(116, 2, 2),         # swap NOP
                   instruction(124, 2),            # FADD writes f2
                   instruction(214, 2),            # CBRANCH target zero
                   instruction(84, 2),             # INEG write
                   instruction(214, 2)]
        self.assertEqual(branch_targets(program), {3: 0, 5: 5})
        self.assertTrue(decode(program[3])["barrier"])

    def test_all_opcodes_decode_and_invalid_words_fail(self):
        for opcode in range(256):
            self.assertIn("kind", decode(instruction(opcode)))
        for word in [-1, 1 << 64]:
            with self.assertRaises(ValueError):
                decode(word)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.trace, self.native, self.rows, self.columns = synthetic_fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def rewrite_trace(self, rows):
        with self.trace.open("w", newline="") as sink:
            writer = csv.DictWriter(sink, self.columns)
            writer.writeheader()
            writer.writerows(rows)

    def test_exact_events_service_and_portable_replay(self):
        fixture = self.root / "portable"
        result = extract(self.trace, self.native, fixture_output=fixture)
        self.assertEqual(result["operation_count"], 384)
        self.assertEqual(result["operations"][0]["memory"]["address"], 0x1238)
        self.assertEqual(result["operations"][0]["latency"], 1)
        self.assertEqual(result["operations"][0]["observed_phase_cycles"][4], 1)
        self.assertTrue(result["operations"][0]["memory_then_compute"])
        self.assertTrue(result["operations"][1]["memory_then_compute"])
        self.assertEqual(result["operations"][2]["writes"], ["round_mode"])
        replay = extract(fixture / "trace.csv", fixture / "native")
        self.assertEqual(result["operations"], replay["operations"])
        self.assertTrue(result["iterations"][0]["route_verified"])
        self.assertEqual(len(json.loads((fixture / "source-map.json").read_text())["windows"]), 1)

    def test_wrong_native_route_is_rejected(self):
        path = self.native / "iterations.hex"
        fields = path.read_text().split()
        fields[-1] = "0"
        path.write_text(" ".join(fields) + "\n")
        with self.assertRaisesRegex(ValueError, "route checksum"):
            extract(self.trace, self.native)

    def test_wrong_native_read_address_is_rejected(self):
        (self.native / "accesses.hex").write_text("1240 deadbeef\n202340 cafe\n")
        with self.assertRaisesRegex(ValueError, "address/direction"):
            extract(self.trace, self.native)

    def test_store_lane_is_checked(self):
        rows = [dict(row) for row in self.rows]
        next(row for row in rows if row["sp_write"])["write_strb"] = "ff00"
        self.rewrite_trace(rows)
        with self.assertRaisesRegex(ValueError, "store byte lane"):
            extract(self.trace, self.native)

    def test_sparse_commit_only_csv_cannot_claim_service_latency(self):
        self.rewrite_trace([row for row in self.rows if row["execute_phase"] != 3])
        with self.assertRaisesRegex(ValueError, "missing nonmemory"):
            extract(self.trace, self.native)

    def test_bounds_and_incomplete_iteration_are_explicit(self):
        with self.assertRaisesRegex(ValueError, "row bound"):
            extract(self.trace, self.native, max_rows=20)
        self.rewrite_trace(self.rows[:-1])
        with self.assertRaisesRegex(ValueError, "inside an iteration"):
            extract(self.trace, self.native)

    def test_existing_fixture_or_source_parent_cannot_be_overwritten(self):
        before = (self.native / "program-0.mem").read_bytes()
        for output in [self.root, self.native]:
            with self.assertRaisesRegex(ValueError, "fresh directory"):
                extract(self.trace, self.native, fixture_output=output)
        self.assertEqual(before, (self.native / "program-0.mem").read_bytes())

    def test_disjoint_first_iteration_windows_replay_with_remapped_events(self):
        original = (self.native / "iterations.hex").read_text().split()
        lines = []
        for program, iteration, event_start in [(0, 0, 0), (0, 1, 2), (1, 0, 4)]:
            fields = original[:]
            fields[:3] = map(str, [program, iteration, event_start])
            lines.append(" ".join(fields))
        (self.native / "iterations.hex").write_text("\n".join(lines) + "\n")
        (self.native / "program-1.mem").write_bytes((self.native / "program-0.mem").read_bytes())
        events = (self.native / "accesses.hex").read_text()
        (self.native / "accesses.hex").write_text(events * 3)
        span = self.rows[-1]["cycle"] + 10
        rows = []
        for index in range(3):
            rows.extend({**row, "cycle": row["cycle"] + index * span} for row in self.rows)
        self.rewrite_trace(rows)
        fixture = self.root / "portable"
        result = extract(self.trace, self.native, max_iterations=2,
                         first_iteration_per_program=True, fixture_output=fixture)
        self.assertEqual([(w["program"], w["iteration"]) for w in result["windows"]], [(0, 0), (1, 0)])
        replay = extract(fixture / "trace.csv", fixture / "native", max_iterations=2)
        self.assertEqual(result["operations"], replay["operations"])
        self.assertEqual([record["event_start"] for record in replay["iterations"]], [0, 2])


if __name__ == "__main__":
    unittest.main()
