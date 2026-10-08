"""Fail-closed resource identity and guest-output evidence controls."""
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1] / "simulator" / "gem5"
from simulator.gem5 import prepare, run


class ResourceTests(unittest.TestCase):
    def test_resource_pins_have_exact_identity(self):
        manifest = json.loads((HERE / "resources.json").read_text())
        self.assertEqual(manifest["gem5_commit"], "c8222cc67a399bfc01e8658dd14b30d5bfd634f9")
        self.assertEqual({r["role"] for r in manifest["resources"]}, {"kernel", "bootloader", "disk_image"})
        for resource in manifest["resources"]:
            self.assertEqual(len(resource["sha256"]), 64)
            self.assertGreater(resource["bytes"], 0)
            self.assertTrue(resource["url"].startswith("https://dist.gem5.org/"))

    def test_changed_resource_rejected_even_with_matching_md5_field(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image"
            path.write_bytes(b"original")
            expected = prepare.hashes(path)
            expected["upstream_md5"] = expected.pop("md5")
            path.write_bytes(b"modified")
            expected["upstream_md5"] = prepare.hashes(path)["md5"]
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                prepare.verify(path, expected | {"id": "test"})


class SerialTests(unittest.TestCase):
    def stream(self, status=0, stderr=""):
        return ("boot messages\nOPENRX_RUNTIME_BEGIN\n{\"type\":\"config\"}\n"
                f"OPENRX_RUNTIME_END status={status}\nOPENRX_RUNTIME_STDERR_BEGIN\n"
                f"{stderr}OPENRX_RUNTIME_STDERR_END\nother serial text\n")

    def test_clean_framing_preserves_only_probe_stream(self):
        body, error = run.extract_probe(self.stream().replace("\n", "\r\n"), "runtime")
        self.assertEqual(body, '{"type":"config"}\n')
        self.assertEqual(error, "")

    def test_script_exit_failure_cannot_pass_as_boot_success(self):
        with self.assertRaises(ValueError):
            run.extract_probe(self.stream(status=139), "runtime")

    def test_guest_stderr_rejected(self):
        with self.assertRaises(ValueError):
            run.extract_probe(self.stream(stderr="Illegal instruction\n"), "runtime")

    def test_truncated_or_duplicate_stream_rejected(self):
        for raw in (self.stream()[:60], self.stream() + self.stream()):
            with self.assertRaises(ValueError):
                run.extract_probe(raw, "runtime")

    def test_wrong_elf_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary"
            path.write_bytes(b"\x7fELF\x02\x01" + b"\0" * 40)
            with self.assertRaises(ValueError):
                run.elf_info(path)


if __name__ == "__main__":
    unittest.main()
