"""Host-only controls for durable execution; never launch gem5 or RandomX."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from scripts import local_execution as runner


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = runner.init(self.base / "store")
        self.payload = self.base / "payload.py"
        self.payload.write_text("print('synthetic output', flush=True)\n")
        self.manager = mock.patch.object(runner, "manager_ready")
        self.manager.start()
        self.addCleanup(self.manager.stop)

    def submit(self, key="test-request", kind="validation"):
        result = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(runner.subprocess, "run", return_value=result):
            return runner.submit(self.root, key, kind, self.base,
                                 [sys.executable, str(self.payload)], [self.payload],
                                 validation_scope="lifecycle" if kind == "validation" else None)

    def directory(self, execution_id):
        return runner.execution_dir(self.root, execution_id)

    def launch_worker(self, execution_id):
        code = "from scripts.local_execution import worker; import sys; sys.exit(worker(sys.argv[1],sys.argv[2]))"
        process = subprocess.Popen([sys.executable, "-c", code, str(self.root), execution_id],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.cleanup_process, process)
        return process

    @staticmethod
    def cleanup_process(process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=5)

    def wait_event(self, execution_id, status):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            records = runner.events(self.directory(execution_id) / "events.jsonl")
            if any(record.get("status") == status for record in records):
                return
            time.sleep(0.02)
        self.fail(f"Missing {status} event")

    def test_init_never_overwrites_and_evidence_event_chain_detects_corruption(self):
        marker = self.root / "preserved-checkpoint"
        marker.write_bytes(b"scientific checkpoint")
        before = (self.root / "state" / "events.jsonl").read_bytes()
        runner.init(self.root)
        self.assertEqual(marker.read_bytes(), b"scientific checkpoint")
        self.assertEqual(before, (self.root / "state" / "events.jsonl").read_bytes())
        path = self.root / "state" / "events.jsonl"
        path.write_bytes(before.replace(b"INVENTORY", b"LOCAL_ACTIVE"))
        with self.assertRaisesRegex(ValueError, "event chain"):
            runner.current_state(self.root)

    def test_existing_file_cannot_be_replaced(self):
        path = self.base / "results"
        runner.write_new(path, b"original")
        with self.assertRaises(FileExistsError):
            runner.write_new(path, b"replacement")
        self.assertEqual(path.read_bytes(), b"original")

    def test_simulation_denied_without_evidence_backed_cutover(self):
        with self.assertRaisesRegex(ValueError, "admission denied"):
            self.submit(kind="simulation")
        self.assertEqual(list((self.root / "executions").iterdir()), [])

    def test_active_transition_requires_all_gates_and_hashed_evidence(self):
        evidence = self.base / "evidence.json"
        evidence.write_text('{}')
        for state in ("STAGING", "LOCAL_VALIDATING", "CUTOVER_PENDING"):
            runner.transition(self.root, state, evidence, "synthetic test only")
        with self.assertRaisesRegex(ValueError, "requires openrx"):
            runner.transition(self.root, "LOCAL_ACTIVE", evidence, "a message is insufficient")
        receipt = {"schema": "openrx.local.acceptance.v1", "gates": {
            name: {"passed": True, "evidence": [runner.digest(evidence)]} for name in runner.GATES},
            "reviewed_merge": {"commit": "a" * 40, "pr_url": "https://example.test/pr",
                               "review_url": "https://example.test/review"}}
        acceptance = self.base / "acceptance.json"
        acceptance.write_text(json.dumps(receipt))
        evidence.write_text('{"modified":true}')
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            runner.transition(self.root, "LOCAL_ACTIVE", acceptance, "reject changed evidence")
        self.assertEqual(runner.current_state(self.root), "CUTOVER_PENDING")

    def test_dedup_survives_reinitialization_and_uses_unique_directories(self):
        first = self.submit()
        runner.init(self.root)
        with self.assertRaisesRegex(ValueError, first):
            self.submit()
        second = self.submit("second-request")
        self.assertNotEqual(first, second)
        self.assertEqual(len(list((self.root / "executions").iterdir())), 2)

    def test_secret_environment_is_rejected_before_persistence(self):
        with self.assertRaisesRegex(ValueError, "not explicitly allowed"):
            runner.submit(self.root, "secret", "validation", self.base,
                          [sys.executable], [self.payload], env_items=["GITHUB_TOKEN=do-not-store"],
                          validation_scope="lifecycle")
        self.assertEqual(list((self.root / "executions").iterdir()), [])

    def test_systemd_limits_cgroup_cleanup_and_no_session_coupling(self):
        execution_id = self.submit()
        command = runner.read_json(self.directory(execution_id) / "submission-command.json")["argv"]
        self.assertIn("--property=MemoryMax=6G", command)
        self.assertIn("--property=CPUQuota=200%", command)
        self.assertIn("--property=TasksMax=256", command)
        self.assertIn("--property=MemorySwapMax=1G", command)
        self.assertIn("--property=Nice=10", command)
        self.assertIn("--property=NoNewPrivileges=yes", command)
        self.assertIn("--property=KillMode=mixed", command)
        self.assertIn("--property=Restart=no", command)
        self.assertTrue(any(item.startswith("--property=ExecStopPost=") for item in command))
        self.assertNotIn("--scope", command)
        self.assertNotIn("--pipe", command)

    def test_changed_input_is_rejected_without_child_launch(self):
        execution_id = self.submit()
        self.payload.write_text("print('different scientific inputs')\n")
        self.assertEqual(runner.worker(self.root, execution_id), 1)
        directory = self.directory(execution_id)
        self.assertFalse((directory / "stdout.log").exists())
        self.assertEqual(runner.read_json(directory / "process-result.json")["status"], "ADMISSION_FAILED")

    def test_exit_zero_does_not_claim_science_and_output_digest_detects_tampering(self):
        execution_id = self.submit()
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        self.assertEqual(receipt["scientific_acceptance"], "unverified")
        self.assertEqual(receipt["process"]["returncode"], 0)
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])
        before = (self.directory(execution_id) / "receipt.json").read_bytes()
        runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "changed"})
        self.assertEqual(before, (self.directory(execution_id) / "receipt.json").read_bytes())
        (self.directory(execution_id) / "stdout.log").write_bytes(b"fabricated")
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            runner.verify(self.root, execution_id)

    def test_directory_inputs_with_unbound_symlinks_are_rejected(self):
        source = self.base / "source"
        source.mkdir()
        (source / "linked-code.py").symlink_to(self.payload)
        with self.assertRaisesRegex(ValueError, "unbound symlink"):
            runner.identity(source)

    def test_output_symlinks_fail_finalization_and_late_links_fail_verification(self):
        external = self.base / "external-scientific-data"
        external.mkdir()
        (external / "result.dat").write_bytes(b"preserved external results")
        for target in (external, external / "result.dat"):
            execution_id = self.submit("output-link-" + target.name)
            self.assertEqual(runner.worker(self.root, execution_id), 0)
            directory = self.directory(execution_id)
            (directory / "linked-output").symlink_to(target, target_is_directory=target.is_dir())
            with self.assertRaisesRegex(ValueError, "symlink must be preserved"):
                runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
            self.assertFalse((directory / "receipt.json").exists())
            self.assertEqual(runner.events(directory / "events.jsonl")[-1]["status"], "PROCESS_EXITED")
        self.assertEqual((external / "result.dat").read_bytes(), b"preserved external results")
        execution_id = self.submit("late-output-link")
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        (self.directory(execution_id) / "late-linked-directory").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink must be preserved"):
            runner.verify(self.root, execution_id)

    def test_nonregular_output_fails_without_reading_or_discarding_it(self):
        execution_id = self.submit("nonregular-output")
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        directory = self.directory(execution_id)
        fifo = directory / "scientific-output.fifo"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, "nonregular artifact must be preserved"):
            runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        self.assertTrue(fifo.exists())
        self.assertFalse((directory / "receipt.json").exists())

    def test_nested_output_flush_failure_cannot_publish_receipt_or_discard_data(self):
        execution_id = self.submit("flush-failure")
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        directory = self.directory(execution_id)
        nested = directory / "payload" / "nested"
        nested.mkdir(parents=True)
        output = nested / "scientific-result.dat"
        output.write_bytes(b"retained output requiring durable flush")
        expected_stat = output.stat()
        original_fsync = os.fsync
        def fail_output_fsync(fd):
            actual = os.fstat(fd)
            if (actual.st_dev, actual.st_ino) == (expected_stat.st_dev, expected_stat.st_ino):
                raise OSError("synthetic storage failure while flushing nested output")
            return original_fsync(fd)
        with mock.patch.object(runner.os, "fsync", side_effect=fail_output_fsync):
            with self.assertRaisesRegex(OSError, "storage failure"):
                runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        self.assertEqual(output.read_bytes(), b"retained output requiring durable flush")
        self.assertFalse((directory / "receipt.json").exists())
        self.assertEqual(runner.events(directory / "events.jsonl")[-1]["status"], "PROCESS_EXITED")
        # A new finalization attempt preserves every file and records honest process status.
        runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

    def test_validation_needs_explicit_allowed_scope(self):
        with self.assertRaisesRegex(ValueError, "validation scope"):
            runner.submit(self.root, "unscoped", "validation", self.base,
                          [sys.executable], [self.payload])

    def test_manifest_and_runner_snapshot_tamper_deny_child_launch(self):
        for component in ("manifest.json", "runner.py"):
            execution_id = self.submit("tamper-" + component)
            path = self.directory(execution_id) / component
            if component == "manifest.json":
                manifest = runner.read_json(path)
                manifest["argv"] = [sys.executable, "-c", "print('unbound command')"]
                path.write_text(json.dumps(manifest))
            else:
                path.write_text("# unbound runner replacement\n")
            self.assertEqual(runner.worker(self.root, execution_id), 1)
            self.assertFalse((self.directory(execution_id) / "stdout.log").exists())
            self.assertEqual(runner.read_json(self.directory(execution_id) / "process-result.json")["status"], "ADMISSION_FAILED")

    def test_submission_failure_keeps_request_claim_and_finalized_evidence(self):
        failed = subprocess.CompletedProcess([], 1, "", "synthetic manager failure")
        with mock.patch.object(runner.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(ValueError, "submission failed"):
                runner.submit(self.root, "manager-failure", "validation", self.base,
                              [sys.executable], [self.payload], validation_scope="lifecycle")
        execution_id = next((self.root / "executions").iterdir()).name
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])
        with self.assertRaisesRegex(ValueError, "already claimed"):
            self.submit("manager-failure")

    def test_crash_between_receipt_and_journal_recovers_without_overwrite(self):
        execution_id = self.submit()
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        original = runner.append_event
        def fail_binding(path, event):
            if Path(path).name == "execution-receipts.jsonl":
                raise OSError("synthetic power-loss before journal binding")
            return original(path, event)
        with mock.patch.object(runner, "append_event", side_effect=fail_binding):
            with self.assertRaises(OSError):
                runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        path = self.directory(execution_id) / "receipt.json"
        original_receipt = path.read_bytes()
        with self.assertRaisesRegex(ValueError, "missing durable receipt binding"):
            runner.verify(self.root, execution_id)
        self.assertTrue(runner.recover(self.root, execution_id)["integrity_verified"])
        self.assertEqual(path.read_bytes(), original_receipt)
        self.assertTrue(runner.events(self.root / "state" / "execution-receipts.jsonl")[-1]["recovered_binding"])

    def test_signal_stop_reaps_child_preserves_partial_logs_and_forbids_resume(self):
        self.payload.write_text("import time\nprint('partial evidence', flush=True)\ntime.sleep(60)\n")
        execution_id = self.submit()
        worker = self.launch_worker(execution_id)
        self.wait_event(execution_id, "CHILD_STARTED")
        path = self.directory(execution_id) / "stdout.log"
        deadline = time.monotonic() + 5
        while not path.read_text() and time.monotonic() < deadline:
            time.sleep(0.01)
        worker.send_signal(signal.SIGINT)
        worker.communicate(timeout=10)
        self.assertEqual(worker.returncode, 130)
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "exit-code", "EXIT_STATUS": "130"})
        self.assertEqual(receipt["status"], "INTERRUPTED")
        self.assertEqual(receipt["process"]["signals"], [signal.SIGINT])
        self.assertIn("partial evidence", path.read_text())
        self.assertFalse(receipt["resume_allowed"])
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

    def test_global_lock_serializes_jobs_and_queued_stop_never_launches_child(self):
        self.payload.write_text("import time\nprint('running', flush=True)\ntime.sleep(60)\n")
        first = self.submit("first")
        second = self.submit("second")
        first_worker = self.launch_worker(first)
        self.wait_event(first, "CHILD_STARTED")
        second_worker = self.launch_worker(second)
        time.sleep(0.2)
        self.assertFalse((self.directory(second) / "stdout.log").exists())
        second_worker.send_signal(signal.SIGINT)
        second_worker.communicate(timeout=10)
        self.assertEqual(second_worker.returncode, 130)
        self.assertFalse((self.directory(second) / "stdout.log").exists())
        first_worker.send_signal(signal.SIGINT)
        first_worker.communicate(timeout=10)

    def test_recovery_requires_inactive_empty_cgroup_and_never_reexecutes(self):
        execution_id = self.submit()
        with mock.patch.object(runner, "unit_status", return_value={"query_returncode": 0, "ActiveState": "active"}):
            with self.assertRaisesRegex(ValueError, "still active"):
                runner.recover(self.root, execution_id)
        state = {"query_returncode": 0, "ActiveState": "failed", "ExecMainCode": "killed", "ExecMainStatus": "9"}
        with mock.patch.object(runner, "unit_status", return_value=state):
            receipt = runner.recover(self.root, execution_id)
        self.assertEqual(receipt["status"], "INTERRUPTED_UNREAPED")
        self.assertEqual(receipt["systemd"]["EXIT_STATUS"], "9")
        self.assertFalse((self.directory(execution_id) / "stdout.log").exists())
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

    def test_oom_manager_result_never_becomes_process_success(self):
        execution_id = self.submit()
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "oom-kill", "EXIT_STATUS": "9"})
        self.assertEqual(receipt["status"], "SERVICE_FAILED")
        self.assertEqual(receipt["scientific_acceptance"], "unverified")

    def test_nested_payload_output_is_expanded_and_integrity_bound(self):
        self.payload.write_text("import pathlib,sys\np=pathlib.Path(sys.argv[1])\np.mkdir()\n(p/'result.dat').write_bytes(b'scientific toy output')\n(p/'scientific.lock').write_text('provenance')\n(p/'receipt.json').write_text('scientific receipt')\n")
        result = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(runner.subprocess, "run", return_value=result):
            execution_id = runner.submit(self.root, "nested-output", "validation", self.base,
                [sys.executable, str(self.payload), "{execution_dir}/payload"], [self.payload],
                validation_scope="lifecycle")
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        output = self.directory(execution_id) / "payload" / "result.dat"
        self.assertIn(runner.digest(output), receipt["artifacts"])
        self.assertIn(runner.digest(output.parent / "scientific.lock"), receipt["artifacts"])
        self.assertIn(runner.digest(output.parent / "receipt.json"), receipt["artifacts"])
        output.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            runner.verify(self.root, execution_id)

    def test_new_output_and_receipt_tampering_are_detected(self):
        execution_id = self.submit()
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        directory = self.directory(execution_id)
        (directory / "unrecorded-output").write_text("late scientific data")
        with self.assertRaisesRegex(ValueError, "artifact set changed"):
            runner.verify(self.root, execution_id)
        receipt_path = directory / "receipt.json"
        receipt = runner.read_json(receipt_path)
        receipt["scientific_acceptance"] = "fabricated-pass"
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "Receipt integrity mismatch"):
            runner.verify(self.root, execution_id)


if __name__ == "__main__":
    unittest.main()
