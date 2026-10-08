"""Fail-closed resource identity and guest-output evidence controls."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
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
    def test_simulator_wall_timeout_default_disabled(self):
        import ast
        source = (HERE / "run.py").read_text()
        tree = ast.parse(source)
        argument_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                          and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
                          and node.args and isinstance(node.args[0], ast.Constant)
                          and node.args[0].value == "--timeout"]
        self.assertEqual(len(argument_calls), 1)
        defaults = [kw.value.value for kw in argument_calls[0].keywords
                    if kw.arg == "default" and isinstance(kw.value, ast.Constant)]
        self.assertEqual(defaults, [0])
        self.assertIn('process.wait(timeout=args.timeout or None)', source)

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


class GuestStreamingTests(unittest.TestCase):
    """Execute generated Bash on host-only synthetic payloads, never gem5."""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.guest = self.root / "guest"
        self.guest.mkdir()
        self.serial = self.root / "serial.log"
        self.stderr = self.root / "stderr.log"

    def start(self, payload):
        binary = self.root / "synthetic-payload"
        binary.write_text("#!/bin/bash\n" + payload)
        # Keep the complete generated script, relocating its scratch directory
        # so independent tests do not share the real guest's /tmp/openrx path.
        script = self.root / "guest.sh"
        script.write_text(run.guest_script({"runtime": binary}).replace("/tmp/openrx", str(self.guest)))
        stdout, stderr = self.serial.open("wb"), self.stderr.open("wb")
        self.addCleanup(stdout.close)
        self.addCleanup(stderr.close)
        process = subprocess.Popen(["bash", str(script)], stdin=subprocess.PIPE,
            stdout=stdout, stderr=stderr, start_new_session=True)

        def cleanup():
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
        self.addCleanup(cleanup)
        return process

    def test_flushed_record_reaches_serial_and_capture_before_child_exit(self):
        first, last = '{"test":"before-exit"}\n', '{"test":"after-release"}\n'
        process = self.start("printf '%s\\n' '{\"test\":\"before-exit\"}'\n"
            "read -r release\n"
            "printf '%s\\n' '{\"test\":\"after-release\"}'\n")
        capture = self.guest / "runtime.jsonl"
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if (first in self.serial.read_text() and capture.exists()
                    and first in capture.read_text()):
                break
            time.sleep(0.01)
        partial = self.serial.read_text()
        self.assertIn(first, partial)
        self.assertIsNone(process.poll())
        self.assertEqual(capture.read_text(), first)
        self.assertNotIn("OPENRX_GUEST_COMPLETE", partial)
        with self.assertRaises(ValueError):
            run.extract_probe(partial, "runtime")
        process.stdin.write(b"release\n")
        process.stdin.flush()
        self.assertEqual(process.wait(timeout=5), 0)
        complete = self.serial.read_text()
        body, error = run.extract_probe(complete, "runtime")
        self.assertEqual(body, first + last)
        self.assertEqual(body, capture.read_text())
        self.assertEqual(error, "")
        self.assertEqual(complete.count(first), 1)
        self.assertIn("OPENRX_GUEST_COMPLETE\n", complete)

    def test_failed_producer_keeps_exact_exit_status_despite_successful_tee(self):
        process = self.start("printf '%s\\n' '{\"test\":\"child-failure\"}'\nexit 42\n")
        self.assertEqual(process.wait(timeout=5), 42)
        serial = self.serial.read_text()
        self.assertIn("OPENRX_RUNTIME_END status=42\n", serial)
        self.assertNotIn("OPENRX_GUEST_COMPLETE", serial)
        self.assertEqual((self.guest / "runtime.jsonl").read_text(), '{"test":"child-failure"}\n')
        with self.assertRaises(ValueError):
            run.extract_probe(serial, "runtime")

    def test_real_capture_write_failure_cannot_complete_or_close_frame(self):
        # GNU tee cannot replace a directory with its capture file. The child
        # succeeds and emits stdout; capture failure must still reject the run.
        (self.guest / "runtime.jsonl").mkdir()
        process = self.start("printf '%s\\n' '{\"test\":\"capture-failure\"}'\nexit 0\n")
        self.assertNotEqual(process.wait(timeout=5), 0)
        serial = self.serial.read_text()
        self.assertIn('{"test":"capture-failure"}\n', serial)
        self.assertNotIn("OPENRX_RUNTIME_END", serial)
        self.assertNotIn("OPENRX_GUEST_COMPLETE", serial)
        self.assertIn("runtime.jsonl", self.stderr.read_text())
        with self.assertRaises(ValueError):
            run.extract_probe(serial, "runtime")


if __name__ == "__main__":
    unittest.main()
