"""Twenty-four focused checks; prepared, not executed."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from export_image import COUNTS, export_image, read_image


class ExportImageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        shutil.copytree(Path(__file__).resolve().parents[1] / "inputs", self.source)

    def change_json(self, name, key, value):
        path = self.source / name
        data = json.loads(path.read_text())
        data[key] = value
        path.write_text(json.dumps(data))

    def change_row(self, stem, pc, value, program=0):
        for case in (0, 1):
            path = self.source / f"case-{case:03d}/{stem}-{program}.mem"
            rows = path.read_text().splitlines()
            rows[pc] = value
            path.write_text("\n".join(rows) + "\n")

    def rejects(self, message):
        with self.assertRaisesRegex(ValueError, message):
            read_image(self.source)

    def first_reciprocal(self):
        rows = (self.source / "case-000/rcp-valid-0.mem").read_text().splitlines()
        return rows.index("1")

    def test_01_retained_image_counts_and_dimensions(self):
        rows, counts = read_image(self.source)
        self.assertEqual(counts, COUNTS)
        self.assertEqual(len(rows), 4096)
        self.assertEqual(sum(counts), 3563)
        self.assertEqual(sum((x >> 160) & 1 for x in rows), 239)

    def test_02_packing_field_boundaries(self):
        rows, _ = read_image(self.source)
        pc = self.first_reciprocal()
        instruction = int((self.source / "case-000/program-0.mem").read_text().splitlines()[pc], 16)
        reciprocal = int((self.source / "case-000/reciprocals-0.mem").read_text().splitlines()[pc], 16)
        index = int((self.source / "case-000/rcp-index-0.mem").read_text().splitlines()[pc], 16)
        self.assertEqual(rows[pc], (1 << 160) + (index << 128) + (reciprocal << 64) + instruction)

    def test_03_reserved_and_padding_are_zero(self):
        rows, counts = read_image(self.source)
        self.assertTrue(all(row >> 161 == 0 for row in rows))
        self.assertEqual(sum(512 - c for c in counts), 533)
        for i, count in enumerate(counts):
            self.assertEqual(rows[i * 512 + count:(i + 1) * 512], [0] * (512 - count))

    def test_04_export_exact_text_width_and_counts(self):
        out = self.root / "image"
        report = export_image(self.source, out)
        self.assertEqual(len((out / "rows.mem").read_bytes()), 4096 * 65)
        self.assertEqual((out / "counts.mem").read_text(), "".join(f"{n:03x}\n" for n in COUNTS))
        self.assertFalse(report["physical_acceptance"])

    def test_05_existing_output_cannot_reload(self):
        out = self.root / "image"
        out.mkdir()
        (out / "sentinel").write_text("keep")
        with self.assertRaisesRegex(ValueError, "output already exists"):
            export_image(self.source, out)
        self.assertEqual((out / "sentinel").read_text(), "keep")

    def test_06_wrong_image_kind(self):
        self.change_json("case-000/metadata.json", "kind", "synthetic")
        self.rejects("image kind")

    def test_07_native_preparation_flag_required(self):
        self.change_json("case-000/metadata.json", "native_generated_programs", False)
        self.rejects("image kind")

    def test_08_wrong_case_identity(self):
        self.change_json("case-000/metadata.json", "case_id", 1)
        self.rejects("case identity")

    def test_09_wrong_cache_descriptor(self):
        self.change_json("cache-0-metadata.json", "cache_id", 1)
        self.rejects("cache descriptor")

    def test_10_wrong_retired_total(self):
        self.change_json("case-000/metadata.json", "retired", 3562)
        self.rejects("case identity")

    def test_11_case_descriptor_binding(self):
        path = self.source / "cases.hex"
        rows = path.read_text().splitlines()
        fields = rows[0].split()
        fields[3] = "000000ee"
        rows[0] = " ".join(fields)
        path.write_text("\n".join(rows) + "\n")
        self.rejects("case descriptor")

    def test_12_exact_admitted_counts(self):
        path = self.source / "cases.hex"
        rows = path.read_text().splitlines()
        fields = rows[0].split()
        fields[4] = f"{int(fields[4], 16) ^ 1:020x}"
        rows[0] = " ".join(fields)
        path.write_text("\n".join(rows) + "\n")
        self.rejects("admitted counts")

    def test_13_truncated_rows(self):
        path = self.source / "case-000/program-0.mem"
        path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
        self.rejects("row count")

    def test_14_wide_instruction(self):
        self.change_row("program", 0, "10000000000000000")
        self.rejects("hex width/value")

    def test_15_nonhex_instruction(self):
        self.change_row("program", 0, "z000000000000303")
        self.rejects("hex width/value")

    def test_16_reciprocal_flag_range(self):
        self.change_row("rcp-valid", 0, "2")
        self.rejects("reciprocal flag")

    def test_17_opcode_requires_reciprocal_flag(self):
        self.change_row("rcp-valid", self.first_reciprocal(), "0")
        self.rejects("reciprocal opcode flag")

    def test_18_index_must_match_instruction_and_global_table(self):
        self.change_row("rcp-index", self.first_reciprocal(), "000000ef")
        self.rejects("reciprocal index binding")

    def test_19_row_reciprocal_value_binding(self):
        self.change_row("reciprocals", self.first_reciprocal(), "0000000000000000")
        self.rejects("row reciprocal value")

    def test_20_nonreciprocal_metadata_zero(self):
        self.change_row("rcp-index", 0, "00000001")
        self.rejects("nonreciprocal metadata")

    def test_21_source_padding_zero(self):
        self.change_row("program", COUNTS[0], "0000000000000001")
        self.rejects("source padding")

    def test_22_shared_image_pair_identical(self):
        path = self.source / "case-001/program-0.mem"
        rows = path.read_text().splitlines()
        rows[0] = "0000000000000003"
        path.write_text("\n".join(rows) + "\n")
        self.rejects("shared image differs")

    def test_23_reciprocal_table_integer_identity(self):
        path = self.source / "cache-0-reciprocals.mem"
        rows = path.read_text().splitlines()
        rows[0] = "0000000000000000"
        path.write_text("\n".join(rows) + "\n")
        self.rejects("reciprocal table value")

    def test_24_reciprocal_namespace_index_and_divisor(self):
        path = self.source / "cache-0-reciprocal-metadata.json"
        original = json.loads(path.read_text())
        changed = json.loads(json.dumps(original))
        changed["entries"][0]["index"] = 1
        path.write_text(json.dumps(changed))
        self.rejects("reciprocal entry index")
        original["entries"][0]["divisor"] = 0
        path.write_text(json.dumps(original))
        self.rejects("reciprocal divisor")


if __name__ == "__main__":
    unittest.main()
