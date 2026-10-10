"""Fail-closed resource identity and guest-output evidence controls."""
import json
import inspect
import ctypes
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

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


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux process-group controls")
class RunnerCancellationTests(unittest.TestCase):
    """Real host processes and synthetic inputs; these never execute gem5."""

    def setUp(self):
        # /proc may be mounted from a different PID namespace. Adopt orphaned
        # descendants in this test process and verify termination with waitpid.
        self.libc = ctypes.CDLL(None, use_errno=True)
        previous = ctypes.c_int()
        if self.libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "PR_GET_CHILD_SUBREAPER failed")
        self.set_subreaper(1)
        self.addCleanup(self.set_subreaper, previous.value)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runner = self.root / "simulator" / "gem5"
        self.runner.mkdir(parents=True)
        for name in ("run.py", "prepare.py", "fs.py"):
            shutil.copyfile(HERE / name, self.runner / name)
        (self.root / "tests").mkdir()
        shutil.copyfile(HERE.parents[1] / "tests" / "native_runtime_probe.py",
                        self.root / "tests" / "native_runtime_probe.py")
        resources = self.root / "resources"
        resources.mkdir()
        manifest = {"resources": []}
        for name in ("opensbi", "vmlinux", "ubuntu.img"):
            path = resources / name
            path.write_bytes(("synthetic-" + name).encode())
            identity = prepare.hashes(path)
            identity["upstream_md5"] = identity.pop("md5")
            manifest["resources"].append(dict(identity, id=name, filename=name))
        (self.runner / "resources.json").write_text(json.dumps(manifest))
        self.payload = self.root / "synthetic-riscv-elf"
        self.payload.write_bytes(b"\x7fELF\x02\x01" + b"\0" * 12 + b"\xf3\0" + b"\0" * 44)
        # Reuse the independent runtime oracle on a clearly synthetic stream.
        rows = [json.loads(line) for line in
                (HERE.parents[1] / "docs/validation/m3-fs/runtime-native.jsonl").read_text().splitlines()]
        rows[0].update(architecture="riscv64", flush_path="linux-riscv-flush-icache")
        self.runtime_body = "".join(json.dumps(row) + "\n" for row in rows)
        (self.root / "runtime-body.jsonl").write_text(self.runtime_body)
        self.pids = self.root / "pids.json"
        self.fake = self.root / "synthetic-simulator"
        self.fake.write_text("#!" + sys.executable + "\n" + '''
import json, os, signal, subprocess, sys, time
from pathlib import Path
root = Path(__file__).parent
out = Path(next(arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--outdir=")))
body = (root / "runtime-body.jsonl").read_text()
serial = ("Kernel booted, In gem5 init...\\nOPENRX_RUNTIME_BEGIN\\n" + body +
          "OPENRX_RUNTIME_END status=0\\nOPENRX_RUNTIME_STDERR_BEGIN\\nOPENRX_RUNTIME_STDERR_END\\n")
complete = (root / "complete").exists()
serial += "OPENRX_GUEST_COMPLETE\\n" if complete else "OPENRX_HASH_BEGIN\\n"
(out / "system.terminal").write_text(serial)
events = [{"hypercall": n} for n in ((1, 2, 3) if complete else (1, 2))]
(out / "simulation.json").write_text(json.dumps({"events": events}))
if complete:
    sys.exit(0)
child = subprocess.Popen([sys.executable, "-c",
    "import os, signal, sys, time; from pathlib import Path; "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)",
    str(root / "descendant-ready")])
while not (root / "descendant-ready").exists():
    time.sleep(0.01)
(root / "pids.json").write_text(json.dumps({"leader": os.getpid(), "descendant": child.pid}))
print("synthetic simulator running", flush=True)
time.sleep(60)
''')
        self.fake.chmod(0o700)
        self.output = self.root / "attempt"
        self.command = [sys.executable, str(self.runner / "run.py"), "--gem5", str(self.fake),
                        "--resources", str(resources), "--runtime-binary", str(self.payload),
                        "--hash-binary", str(self.payload), "--output-dir", str(self.output)]
        self.addCleanup(self.stop_simulator)

    def set_subreaper(self, enabled):
        if self.libc.prctl(36, enabled, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER failed")

    def stop_simulator(self):
        if self.pids.exists():
            pids = json.loads(self.pids.read_text())
            try:
                os.killpg(pids["leader"], signal.SIGKILL)
            except ProcessLookupError:
                pass
            for pid in pids.values():
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass

    def start_runner(self, *extra):
        process = subprocess.Popen(self.command + list(extra), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)

        def cleanup():
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
        self.addCleanup(cleanup)
        return process

    def wait_ready(self, process):
        deadline = time.monotonic() + 5
        while not self.pids.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(self.pids.exists(), "Synthetic simulator failed to reach its ready marker")
        self.assert_group_live()

    def assert_group_live(self):
        for pid in json.loads(self.pids.read_text()).values():
            os.kill(pid, 0)

    def assert_reaped(self, pid):
        with self.assertRaises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def assert_group_stopped(self):
        pids = json.loads(self.pids.read_text())
        self.assert_reaped(pids["leader"])
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            pid, status = os.waitpid(pids["descendant"], os.WNOHANG)
            if pid:
                self.assertTrue(os.WIFSIGNALED(status))
                self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
                self.assert_reaped(pid)
                return
            time.sleep(0.01)
        self.fail("Simulator descendant remained alive after cancellation")

    def assert_partial_failure(self, process):
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 1, stderr.decode())
        report = json.loads((self.output / "report.json").read_text())
        self.assertEqual(json.loads(stdout), report)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(report["boot_observed"])
        self.assertTrue(report["runtime_validated"])
        self.assertEqual(report["validated"]["runtime"]["checks_passed"], 9)
        self.assertEqual((self.output / "runtime.jsonl").read_text(), self.runtime_body)
        self.assertFalse((self.output / "hash.jsonl").exists())
        self.assertIn("framed hash", report["error"])
        self.assertIsNone(report["returncode"])
        self.assertEqual(report["child_returncode"], -signal.SIGKILL)
        self.assert_group_stopped()
        return report

    def test_sigint_cleans_group_and_retains_completed_runtime(self):
        process = self.start_runner()
        self.wait_ready(process)
        process.send_signal(signal.SIGINT)
        report = self.assert_partial_failure(process)
        self.assertTrue(report["interrupted"])
        self.assertEqual(report["interruption_signal"], "SIGINT")
        self.assertIsNone(report["timeout_seconds"])
        self.assertNotIn("timed_out", report)

    def test_sigterm_cleans_group_and_retains_completed_runtime(self):
        process = self.start_runner()
        self.wait_ready(process)
        process.send_signal(signal.SIGTERM)
        report = self.assert_partial_failure(process)
        self.assertTrue(report["interrupted"])
        self.assertEqual(report["interruption_signal"], "SIGTERM")
        self.assertNotIn("timed_out", report)

    def test_opt_in_timeout_cleans_group_and_retains_completed_runtime(self):
        stop_file = self.root / "unused-stop-request"
        process = self.start_runner("--timeout", "2", "--stop-file", str(stop_file))
        self.wait_ready(process)
        report = self.assert_partial_failure(process)
        self.assertTrue(report["timed_out"])
        self.assertNotIn("interrupted", report)
        self.assertNotIn("stop_file_observed", report)
        self.assertFalse(stop_file.exists())

    def test_stop_file_requests_cleanup_and_retains_completed_runtime(self):
        stop_file = self.root / "stop-request"
        process = self.start_runner("--stop-file", str(stop_file))
        self.wait_ready(process)
        stop_file.write_text("stop requested by test\n")
        report = self.assert_partial_failure(process)
        self.assertTrue(report["interrupted"])
        self.assertEqual(report["interruption_signal"], "SIGINT")
        self.assertEqual(report["interruption_source"], "stop-file")
        self.assertEqual(report["stop_file"], str(stop_file))
        self.assertTrue(report["stop_file_observed"])
        self.assertIsNone(report["timeout_seconds"])
        self.assertNotIn("timed_out", report)
        self.assertEqual(stop_file.read_text(), "stop requested by test\n")

    def test_stale_stop_file_or_dangling_symlink_rejected_without_launch(self):
        for kind in ("file", "dangling-symlink"):
            with self.subTest(kind=kind):
                stop_file = self.root / ("stale-" + kind)
                if kind == "file":
                    stop_file.write_text("stale request\n")
                else:
                    stop_file.symlink_to(self.root / "missing-target")
                self.output = self.root / ("attempt-" + kind)
                self.command[self.command.index("--output-dir") + 1] = str(self.output)
                process = self.start_runner("--stop-file", str(stop_file))
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 1, stderr.decode())
                report = json.loads(stdout)
                self.assertEqual(report, json.loads((self.output / "report.json").read_text()))
                self.assertEqual(report["status"], "fail")
                self.assertEqual(report["stop_file"], str(stop_file))
                self.assertIn("already exists at launch", report["error"])
                self.assertFalse(self.pids.exists())
                self.assertNotIn("command", report)
                self.assertNotIn("interrupted", report)
                self.assertNotIn("timed_out", report)
                self.assertTrue(os.path.lexists(stop_file))
                if kind == "file":
                    self.assertEqual(stop_file.read_text(), "stale request\n")
                else:
                    self.assertEqual(stop_file.readlink(), self.root / "missing-target")

    def test_successful_runtime_keeps_default_unlimited_and_strict_completion(self):
        (self.root / "complete").touch()
        index = self.command.index("--hash-binary")
        del self.command[index:index + 2]
        process = self.start_runner()
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, stderr.decode())
        report = json.loads(stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["returncode"], 0)
        self.assertIsNone(report["timeout_seconds"])
        self.assertNotIn("interrupted", report)
        self.assertNotIn("timed_out", report)

    def test_successful_runtime_with_stop_watch_leaves_marker_absent(self):
        (self.root / "complete").touch()
        stop_file = self.root / "unused-stop-request"
        index = self.command.index("--hash-binary")
        del self.command[index:index + 2]
        process = self.start_runner("--stop-file", str(stop_file))
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, stderr.decode())
        report = json.loads(stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["stop_file"], str(stop_file))
        self.assertIsNone(report["timeout_seconds"])
        self.assertNotIn("stop_file_observed", report)
        self.assertNotIn("interrupted", report)
        self.assertNotIn("timed_out", report)
        self.assertFalse(stop_file.exists())

    def test_late_marker_does_not_relabel_already_completed_child(self):
        (self.root / "complete").touch()
        self.output.mkdir()
        stop_file = self.root / "late-stop-request"
        original_popen = subprocess.Popen
        child = None

        def completed_launch(*args, **kwargs):
            nonlocal child
            child = original_popen(*args, **kwargs)
            self.assertEqual(child.wait(timeout=5), 0)
            stop_file.write_text("request after child exit\n")
            return child

        with mock.patch.object(run.subprocess, "Popen", side_effect=completed_launch):
            result = run.run_process([str(self.fake), "--outdir=" + str(self.output)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     timeout=0, stop_file=stop_file)
        self.assertEqual(result, {"returncode": 0})
        self.assert_reaped(child.pid)
        self.assertEqual(stop_file.read_text(), "request after child exit\n")

    def test_signal_during_launch_is_cleaned_and_handlers_restored(self):
        original_handlers = {n: signal.getsignal(n) for n in (signal.SIGINT, signal.SIGTERM)}
        original_popen = subprocess.Popen
        child = None

        def interrupted_launch(*args, **kwargs):
            nonlocal child
            child = original_popen(*args, **kwargs)
            os.kill(os.getpid(), signal.SIGTERM)
            return child

        with mock.patch.object(run.subprocess, "Popen", side_effect=interrupted_launch):
            result = run.run_process([sys.executable, "-c", "import time; time.sleep(60)"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0)
        self.assertTrue(result["interrupted"])
        self.assertEqual(result["interruption_signal"], "SIGTERM")
        self.assertEqual(child.returncode, -signal.SIGKILL)
        self.assert_reaped(child.pid)
        self.assertEqual({n: signal.getsignal(n) for n in original_handlers}, original_handlers)

    def test_signal_after_actual_waitpid_reap_cannot_signal_reused_group(self):
        original_popen = subprocess.Popen
        observation = {"reaped": False, "signal_injected": False}

        def launch(*args, **kwargs):
            child = original_popen(*args, **kwargs)
            original_try_wait = child._try_wait
            original_poll = child.poll
            first_poll = True

            def poll():
                nonlocal first_poll
                if first_poll:
                    # Leave the real child unreaped so wait() must exercise
                    # the precise waitpid/returncode assignment boundary.
                    first_poll = False
                    return None
                return original_poll()

            def try_wait(flags):
                result = original_try_wait(flags)
                if result[0] == child.pid and not observation["signal_injected"]:
                    observation.update(reaped=True, signal_injected=True)
                    self.assertIsNone(child.returncode)
                    signal.raise_signal(signal.SIGINT)
                return result

            child._try_wait = try_wait
            child.poll = poll
            return child

        for stop_file in (None, self.root / "absent-stop-marker"):
            with self.subTest(stop_file=stop_file):
                observation.update(reaped=False, signal_injected=False)
                with mock.patch.object(run.subprocess, "Popen", side_effect=launch), mock.patch.object(
                        run.os, "killpg", side_effect=AssertionError("Already-reaped process group must never be signaled")):
                    result = run.run_process(["/usr/bin/true"], stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL, timeout=0, stop_file=stop_file)
                self.assertTrue(observation["reaped"])
                self.assertTrue(result["interrupted"])
                self.assertEqual(result["interruption_source"], "host-signal")
                self.assertIsNone(result["returncode"])
                self.assertEqual(result["child_returncode"], 0)

    def test_signal_after_completed_poll_cannot_reset_process_ownership_guard(self):
        source, first_line = inspect.getsourcelines(run.run_process)
        target = first_line + next(i for i, line in enumerate(source)
                                   if line.strip() == "if observed_returncode is not None:")
        original_popen = subprocess.Popen

        for stop_file in (None, self.root / "absent-poll-stop-marker"):
            with self.subTest(stop_file=stop_file):
                child = None
                injected = False

                def launch(*args, **kwargs):
                    nonlocal child
                    child = original_popen(*args, **kwargs)
                    self.assertEqual(child.wait(timeout=5), 0)
                    return child

                def trace(frame, event, _arg):
                    nonlocal injected
                    if (not injected and frame.f_code is run.run_process.__code__
                            and event == "line" and frame.f_lineno == target):
                        self.assertEqual(child.returncode, 0)
                        injected = True
                        signal.raise_signal(signal.SIGINT)
                    return trace

                previous_trace = sys.gettrace()
                try:
                    sys.settrace(trace)
                    with mock.patch.object(run.subprocess, "Popen", side_effect=launch), mock.patch.object(
                            run.os, "killpg", side_effect=AssertionError("Completed poll cannot authorize a group signal")):
                        result = run.run_process(["/usr/bin/true"], stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL, timeout=0, stop_file=stop_file)
                finally:
                    sys.settrace(previous_trace)
                self.assertTrue(injected)
                self.assertTrue(result["interrupted"])
                self.assertIsNone(result["returncode"])
                self.assertEqual(result["child_returncode"], 0)

    def signal_at_transition(self, statement, signum):
        # A real signal at the specified bytecode boundary reproduces exception
        # handler/finally races deterministically, without timing a second thread.
        source, first_line = inspect.getsourcelines(run.run_process)
        target = first_line + next(i for i, line in enumerate(source)
                                   if line.strip() == statement)
        injected = False

        def trace(frame, event, _arg):
            nonlocal injected
            if (not injected and frame.f_code is run.run_process.__code__
                    and event == "line" and frame.f_lineno == target):
                injected = True
                self.assert_group_live()
                os.kill(os.getpid(), signum)
            return trace

        self.output.mkdir()
        original_handlers = {n: signal.getsignal(n) for n in (signal.SIGINT, signal.SIGTERM)}
        previous_trace = sys.gettrace()
        sys.settrace(trace)
        try:
            result = run.run_process([str(self.fake), "--outdir=" + str(self.output)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
        finally:
            sys.settrace(previous_trace)
        self.assertTrue(injected)
        self.assertTrue(result["interrupted"])
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["interruption_signal"], signal.Signals(signum).name)
        self.assertIsNone(result["returncode"])
        self.assertEqual(result["child_returncode"], -signal.SIGKILL)
        self.assert_group_stopped()
        self.assertEqual({n: signal.getsignal(n) for n in original_handlers}, original_handlers)

    def test_signal_during_timeout_handler_cannot_escape_cleanup(self):
        self.signal_at_transition('result["timed_out"] = True', signal.SIGTERM)

    def test_signal_at_cleanup_entry_cannot_skip_group_termination(self):
        self.signal_at_transition("if process is not None:", signal.SIGINT)


if __name__ == "__main__":
    unittest.main()
