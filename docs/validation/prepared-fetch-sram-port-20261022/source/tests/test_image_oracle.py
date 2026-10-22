"""Twelve mutation checks for the independently reconstructed image oracle; UNRUN."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from export_image import export_image
from check_image import verify


class ImageOracleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        shutil.copytree(Path(__file__).resolve().parents[1] / "inputs", self.source)
        self.image = self.root / "image"
        export_image(self.source, self.image)
        self.report = self.root / "oracle.json"

    def corrupt_row(self, bit, slot=0):
        path = self.image / "rows.mem"
        rows = path.read_text().splitlines()
        rows[slot] = f"{int(rows[slot], 16) ^ (1 << bit):064x}"
        path.write_text("\n".join(rows) + "\n")

    def rejects_row(self):
        with self.assertRaisesRegex(ValueError, "SRAM row differs"):
            verify(self.source, self.image, self.report)

    def test_01_independent_full_roundtrip_and_scope(self):
        result = verify(self.source, self.image, self.report)
        self.assertEqual(result["active_rows"], 3563)
        self.assertEqual(result["reciprocal_rows"], 239)
        self.assertFalse(result["oracle_imports_exporter"])
        self.assertFalse(result["physical_sram_characterized"])
        self.assertIsNone(result["achievable_frequency_hz"])
        self.assertEqual(len((self.image / "gold-payload.mem").read_bytes()), 4096 * 42)

    def test_02_instruction_corruption(self):
        self.corrupt_row(0)
        self.rejects_row()

    def test_03_reciprocal_corruption(self):
        self.corrupt_row(64)
        self.rejects_row()

    def test_04_global_index_corruption(self):
        self.corrupt_row(128)
        self.rejects_row()

    def test_05_reciprocal_valid_corruption(self):
        self.corrupt_row(160)
        self.rejects_row()

    def test_06_padding_cannot_execute(self):
        self.corrupt_row(0, 447)
        self.rejects_row()

    def test_07_reserved_bits_cannot_hide_data(self):
        self.corrupt_row(255)
        self.rejects_row()

    def test_08_counts_are_independent_metadata(self):
        path = self.image / "counts.mem"
        rows = path.read_text().splitlines()
        rows[0] = "1be"
        path.write_text("\n".join(rows) + "\n")
        with self.assertRaisesRegex(ValueError, "count metadata differs"):
            verify(self.source, self.image, self.report)

    def test_09_existing_gold_preserved(self):
        path = self.image / "gold-payload.mem"
        path.write_text("keep")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            verify(self.source, self.image, self.report)
        self.assertEqual(path.read_text(), "keep")

    def test_10_existing_report_preserved(self):
        self.report.write_text("keep")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            verify(self.source, self.image, self.report)
        self.assertEqual(self.report.read_text(), "keep")

    def test_11_truncated_image_rejected(self):
        path = self.image / "rows.mem"
        path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
        with self.assertRaisesRegex(ValueError, "wrong row count"):
            verify(self.source, self.image, self.report)

    def test_12_source_metadata_not_inferred_from_export(self):
        path = self.source / "case-000/metadata.json"
        meta = json.loads(path.read_text())
        meta["kind"] = "synthetic"
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError, "case metadata differs"):
            verify(self.source, self.image, self.report)


if __name__ == "__main__":
    unittest.main()
