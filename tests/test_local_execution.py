"""Host-only controls for durable execution; never launch gem5 or RandomX."""
import hashlib
import fcntl
import copy
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
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
        self.resource_observation = {
            "at": "2026-10-10T00:00:00+00:00", "logical_cpus": 6, "allowed_cpus": list(range(6)),
            "memory_bytes": {"MemTotal": 16 * runner.GIB,
                             "MemAvailable": 9 * runner.GIB + 128 * 1024 ** 2,
                             "SwapTotal": 4 * runner.GIB, "SwapFree": 4 * runner.GIB}}
        self.original_host_resources = runner.host_resources
        resources = mock.patch.object(runner, "host_resources", return_value=self.resource_observation)
        resources.start()
        self.addCleanup(resources.stop)

    def submit(self, key="test-request", kind="validation", **resource_options):
        result = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(runner.subprocess, "run", return_value=result):
            return runner.submit(self.root, key, kind, self.base,
                                 [sys.executable, str(self.payload)], [self.payload],
                                 validation_scope="lifecycle" if kind == "validation" else None,
                                 **resource_options)

    def directory(self, execution_id):
        return runner.execution_dir(self.root, execution_id)

    def launch_worker(self, execution_id):
        code = ("from scripts import local_execution as runner; import sys; "
                f"runner.host_resources = lambda: {self.resource_observation!r}; "
                "sys.exit(runner.worker(sys.argv[1],sys.argv[2]))")
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
        self.assertIn("--property=MemoryMax=8589934592", command)
        self.assertIn("--property=CPUQuota=600%", command)
        self.assertIn("--property=TasksMax=256", command)
        self.assertIn("--property=MemorySwapMax=2G", command)
        self.assertIn("--property=Nice=10", command)
        self.assertIn("--property=NoNewPrivileges=yes", command)
        self.assertIn("--property=KillMode=mixed", command)
        self.assertIn("--property=Restart=no", command)
        self.assertIn("--property=NotifyAccess=exec", command)
        self.assertTrue(any(item.startswith("--property=ExecStopPost=") for item in command))
        self.assertNotIn("--scope", command)
        self.assertNotIn("--pipe", command)

    def test_actual_meminfo_parser_records_bytes_and_rejects_missing_or_invalid_headroom(self):
        path = self.base / "synthetic-meminfo"
        valid = "MemTotal: 16777216 kB\nMemAvailable: 9568256 kB\nSwapTotal: 4194304 kB\nSwapFree: 3145728 kB\n"
        path.write_text(valid)
        observed = self.original_host_resources(path)
        self.assertEqual(observed["memory_bytes"]["MemTotal"], 17179869184)
        self.assertEqual(observed["memory_bytes"]["MemAvailable"], 9797894144)
        self.assertEqual(observed["memory_bytes"]["SwapFree"], 3221225472)
        self.assertEqual(observed["allowed_cpus"], sorted(os.sched_getaffinity(0)))
        for invalid in (valid.replace("MemAvailable: 9568256 kB\n", ""),
                        valid.replace("9568256 kB", "9568256 bytes"),
                        valid.replace("9568256", "16777217"),
                        valid.replace("3145728", "4194305")):
            path.write_text(invalid)
            with self.assertRaisesRegex(ValueError, "available host RAM/swap"):
                self.original_host_resources(path)

    def test_dynamic_memory_uses_measured_headroom_above_prior_cap_and_bound_manifest(self):
        def admitted_under_lock():
            with (self.root / "locks" / "admission.lock").open("a+") as handle:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return self.resource_observation
        with mock.patch.object(runner, "host_resources", side_effect=admitted_under_lock):
            execution_id = self.submit("dynamic-resources")
        manifest = runner.read_json(self.directory(execution_id) / "manifest.json")
        profile = manifest["resource_profile"]
        self.assertEqual(manifest["resources"]["MemoryMax"], "8589934592")
        self.assertEqual(profile["safe_ceiling_bytes"], 8724152320)
        self.assertEqual(profile["allocation_slack_bytes"], 134217728)
        self.assertEqual(profile["memory_margin_bytes"], 1073741824)
        self.assertEqual(profile["default_rounding_bytes"], 268435456)
        self.assertEqual(profile["admission"], self.resource_observation)
        self.assertEqual(manifest["resources"]["CPUQuota"], "600%")
        self.assertEqual(manifest["resources"]["global_slots"], 1)
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        check = runner.read_json(self.directory(execution_id) / "prelaunch-resource-check.json")
        self.assertTrue(check["safe"])
        self.assertEqual(check["required_available_bytes"], 9663676416)
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        self.assertIn(runner.digest(self.directory(execution_id) / "prelaunch-resource-check.json"), receipt["artifacts"])
        self.assertEqual(receipt["scientific_acceptance"], "unverified")
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

    @staticmethod
    def kernel_observation(memory="8589934592"):
        unlimited = {"cpu.max": "max 100000", "memory.max": "max", "memory.high": "max",
                     "memory.swap.max": "max", "pids.max": "max",
                     "cgroup.controllers": "cpu memory pids", "cgroup.subtree_control": "cpu memory pids",
                     "cpuset.cpus.effective": None}
        own = {**unlimited, "cpu.max": "600000 100000", "memory.max": memory,
               "memory.swap.max": "2147483648", "pids.max": "256"}
        return {"at": "2026-10-10T00:00:00+00:00", "service_cgroup": "/user/toy.service",
                "worker_allowed_cpus": list(range(6)), "groups": [
                    {"path": "/sys/fs/cgroup/user/toy.service", "is_root": False, "files": own},
                    {"path": "/sys/fs/cgroup/user", "is_root": False, "files": unlimited},
                    {"path": "/sys/fs/cgroup", "is_root": True, "files": {
                        **unlimited, "cpu.max": None, "memory.max": None, "memory.high": None,
                        "memory.swap.max": None, "pids.max": None, "cpuset.cpus.effective": "0-5"}}]}

    def test_kernel_reader_captures_actual_file_constraints_for_every_visible_ancestor(self):
        base = self.base / "synthetic-cgroup"
        unit = "toy.service"
        service = base / "user" / unit
        service.mkdir(parents=True)
        (service / "cpu.max").write_text("600000 100000\n")
        (service.parent / "cpu.max").write_text("max 100000\n")
        (base / "cpuset.cpus.effective").write_text("0-5\n")
        with mock.patch.object(runner, "own_cgroup", return_value=("/user/" + unit, service)):
            observed = runner.kernel_resources(unit, base)
        self.assertEqual([row["path"] for row in observed["groups"]], [str(service), str(service.parent), str(base)])
        self.assertEqual(observed["groups"][0]["files"]["cpu.max"], "600000 100000")
        self.assertEqual(observed["groups"][1]["files"]["cpu.max"], "max 100000")
        self.assertIsNone(observed["groups"][0]["files"]["memory.max"])
        self.assertEqual(observed["groups"][-1]["files"]["cpuset.cpus.effective"], "0-5")

    def test_missing_or_tighter_kernel_and_ancestor_constraints_deny_payload_with_retained_evidence(self):
        mutations = [(0, "cpu.max", None), (0, "cpu.max", "max 100000"),
                     (0, "memory.max", "max"), (0, "memory.swap.max", "1073741824"),
                     (0, "pids.max", "128"), (1, "cpu.max", "200000 100000"),
                     (1, "memory.max", "8589934591"), (1, "memory.high", "8589934591"),
                     (1, "memory.swap.max", "0"), (1, "pids.max", "255"),
                     (1, "cpuset.cpus.effective", "0-4"), (1, "cpuset.cpus.effective", ""),
                     (1, "cpu.max", "invalid")]
        for number, (index, name, value) in enumerate(mutations):
            execution_id = self.submit("denied-kernel-" + str(number))
            observed = self.kernel_observation()
            observed["groups"][index]["files"][name] = value
            with mock.patch.object(runner, "kernel_resources", return_value=observed):
                self.assertEqual(runner.worker(self.root, execution_id), 1, (index, name, value))
            directory = self.directory(execution_id)
            self.assertFalse((directory / "stdout.log").exists())
            self.assertFalse(any(item.get("status") == "CHILD_STARTED" for item in runner.events(directory / "events.jsonl")))
            proof = runner.read_json(directory / "prelaunch-kernel-check.json")
            self.assertFalse(proof["safe"])
            self.assertFalse(proof["production_enforced"])
            self.assertTrue(proof["errors"])
            receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "exit-code"})
            self.assertEqual(receipt["scientific_acceptance"], "unverified")
            self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

    def test_kernel_accepts_full_profile_and_exact_requests_only_with_page_rounding_and_six_cpus(self):
        execution_id = self.submit("valid-kernel", memory_bytes=3221225489)
        manifest = runner.read_json(self.directory(execution_id) / "manifest.json")
        self.assertEqual(manifest["resource_profile"]["kernel_memory_max_bytes"], 3221225472)
        observed = self.kernel_observation("3221225472")
        with mock.patch.object(runner, "kernel_resources", return_value=observed):
            self.assertEqual(runner.worker(self.root, execution_id), 0)
        proof = runner.read_json(self.directory(execution_id) / "prelaunch-kernel-check.json")
        self.assertTrue(proof["production_enforced"])
        self.assertEqual(proof["errors"], [])
        profile = manifest["resource_profile"]
        fewer_cpus = copy.deepcopy(observed)
        fewer_cpus["worker_allowed_cpus"] = list(range(5))
        self.assertTrue(runner.kernel_resource_errors(fewer_cpus, profile))
        no_groups = copy.deepcopy(observed)
        no_groups["groups"] = []
        self.assertTrue(runner.kernel_resource_errors(no_groups, profile))
        wrong_rounding = copy.deepcopy(observed)
        wrong_rounding["groups"][0]["files"]["memory.max"] = "3221225489"
        self.assertTrue(runner.kernel_resource_errors(wrong_rounding, profile))

    def test_kernel_read_failure_records_truthful_proof_without_starting_payload(self):
        execution_id = self.submit("kernel-read-failed")
        with mock.patch.object(runner, "kernel_resources", side_effect=OSError("synthetic missing controller mount")):
            self.assertEqual(runner.worker(self.root, execution_id), 1)
        directory = self.directory(execution_id)
        self.assertFalse((directory / "stdout.log").exists())
        proof = runner.read_json(directory / "prelaunch-kernel-check.json")
        self.assertFalse(proof["production_enforced"])
        self.assertEqual(proof["errors"], ["synthetic missing controller mount"])

    def test_private_cli_rechecks_named_service_before_child_and_cannot_use_fixture_bypass(self):
        execution_id = self.submit("late-named-service-loss")
        manifest = runner.read_json(self.directory(execution_id) / "manifest.json")
        original_group = ("/synthetic/" + manifest["unit"], self.base / "synthetic" / manifest["unit"])
        with mock.patch.object(runner, "own_cgroup", return_value=original_group), mock.patch.object(
                runner, "kernel_resources", return_value=None):
            self.assertEqual(runner.main(["--root", str(self.root), "_worker", execution_id]), 1)
        directory = self.directory(execution_id)
        self.assertFalse((directory / "stdout.log").exists())
        proof = runner.read_json(directory / "prelaunch-kernel-check.json")
        self.assertFalse(proof["safe"])
        self.assertTrue(proof["production_required"])
        self.assertFalse(proof["production_enforced"])
        self.assertEqual(proof["errors"], ["Current named production service cgroup is missing"])

    def test_known_memory_request_is_exact_and_unsafe_or_unknown_profiles_never_claim_id(self):
        for kwargs in ({"memory_bytes": 8724152321}, {"memory_bytes": 0},
                       {"memory_bytes": -1}, {"memory_bytes": True},
                       {"resource_profile": "unreviewed"}):
            with self.assertRaises(ValueError):
                self.submit("invalid-budget", **kwargs)
            self.assertEqual(list((self.root / "executions").iterdir()), [])
            self.assertEqual(list((self.root / "requests").iterdir()), [])
        execution_id = self.submit("known-budget", memory_bytes=3221225489)
        manifest = runner.read_json(self.directory(execution_id) / "manifest.json")
        self.assertEqual(manifest["resources"]["MemoryMax"], "3221225489")
        self.assertEqual(manifest["resource_profile"]["requested_memory_bytes"], 3221225489)
        self.assertEqual(manifest["resource_profile"]["selected_memory_bytes"], 3221225489)

    def test_high_available_ram_keeps_minimal_os_headroom_and_documented_host_ceiling(self):
        observation = {**self.resource_observation, "memory_bytes": {
            "MemTotal": 32 * runner.GIB, "MemAvailable": 24 * runner.GIB,
            "SwapTotal": 4 * runner.GIB, "SwapFree": 4 * runner.GIB}}
        with mock.patch.object(runner, "host_resources", return_value=observation):
            resources, profile = runner.select_resources(runner.RESOURCE_PROFILE)
            self.assertEqual(resources["MemoryMax"], "15032385536")
            self.assertEqual(profile["safe_ceiling_bytes"], 15032385536)
        observation["memory_bytes"]["MemAvailable"] = runner.GIB + 100
        with mock.patch.object(runner, "host_resources", return_value=observation):
            with self.assertRaisesRegex(ValueError, "Insufficient available RAM"):
                self.submit("no-safe-ram")
        self.assertEqual(list((self.root / "executions").iterdir()), [])

    def test_headroom_decline_is_checked_under_global_lock_and_preserves_failed_receipt(self):
        execution_id = self.submit("headroom-declined")
        observation = {**self.resource_observation, "memory_bytes": {
            **self.resource_observation["memory_bytes"], "MemAvailable": 9663676415}}
        lock_observed = []
        def fresh_under_lock():
            with (self.root / "locks" / "execution.lock").open("a+") as handle:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_observed.append(True)
            return observation
        with mock.patch.object(runner, "host_resources", side_effect=fresh_under_lock):
            self.assertEqual(runner.worker(self.root, execution_id), 1)
        self.assertEqual(lock_observed, [True])
        directory = self.directory(execution_id)
        self.assertFalse((directory / "stdout.log").exists())
        self.assertFalse(any(item.get("status") == "CHILD_STARTED" for item in runner.events(directory / "events.jsonl")))
        check = runner.read_json(directory / "prelaunch-resource-check.json")
        self.assertFalse(check["safe"])
        result = runner.read_json(directory / "process-result.json")
        self.assertEqual(result["status"], "ADMISSION_FAILED")
        self.assertIn("no child launched", result["error"])
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "exit-code"})
        self.assertEqual(receipt["scientific_acceptance"], "unverified")
        self.assertFalse(receipt["resume_allowed"])
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

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

    def test_completed_child_never_signals_a_potentially_reused_process_group(self):
        execution_id = self.submit("completed-leader-reuse")
        with mock.patch.object(runner.os, "killpg", side_effect=AssertionError("Reaped leader PID may now identify another process group")):
            self.assertEqual(runner.worker(self.root, execution_id), 0)
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "success"})
        self.assertEqual(receipt["process"]["returncode"], 0)
        self.assertTrue(runner.verify(self.root, execution_id)["integrity_verified"])

    def test_signal_during_real_child_reap_does_not_reenter_poll_or_signal_stale_pid(self):
        execution_id = self.submit("signal-during-reap")
        original_popen = subprocess.Popen
        observation = {"signal_delivered": False}
        def launch(*args, **kwargs):
            child = original_popen(*args, **kwargs)
            original_poll = child.poll
            in_poll = False
            def poll():
                nonlocal in_poll
                if in_poll:
                    raise AssertionError("Signal handler reentered the child poll/reap path")
                in_poll = True
                try:
                    result = original_poll()
                    if result is not None and not observation["signal_delivered"]:
                        observation["signal_delivered"] = True
                        signal.raise_signal(signal.SIGINT)
                    return result
                finally:
                    in_poll = False
            child.poll = poll
            return child
        with mock.patch.object(runner.subprocess, "Popen", side_effect=launch), mock.patch.object(
                runner.os, "killpg", side_effect=AssertionError("Reaped PID must not be signaled")):
            self.assertEqual(runner.worker(self.root, execution_id), 130)
        self.assertTrue(observation["signal_delivered"])
        receipt = runner.finalize(self.root, execution_id, {"SERVICE_RESULT": "exit-code"})
        self.assertEqual(receipt["status"], "INTERRUPTED")
        self.assertEqual(receipt["process"]["returncode"], 0)
        self.assertEqual(receipt["process"]["signals"], [signal.SIGINT])

    def test_finalizer_timeout_protocol_handles_path_and_abstract_socket_and_joins_thread(self):
        for address in (str(self.base / "notify.sock"), "@openrx-test-" + uuid.uuid4().hex):
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as server:
                server.bind("\0" + address[1:] if address.startswith("@") else address)
                server.settimeout(2)
                with mock.patch.dict(os.environ, {"NOTIFY_SOCKET": address}):
                    with runner.finalizer_timeout_extension() as health_check:
                        self.assertEqual(server.recv(1024), b"EXTEND_TIMEOUT_USEC=45000000")
                        health_check()
                    self.assertFalse(any(t.name == "openrx-finalizer-heartbeat" for t in threading.enumerate()))

    def test_private_finalizer_notification_startup_failure_never_publishes_receipt(self):
        execution_id = self.submit("notify-startup-failure")
        self.assertEqual(runner.worker(self.root, execution_id), 0)
        with mock.patch.dict(os.environ, {"NOTIFY_SOCKET": str(self.base / "nonexistent-notify-socket")}):
            with mock.patch.object(sys, "stderr"):
                self.assertEqual(runner.main(["--root", str(self.root), "_finalize", execution_id]), 1)
        directory = self.directory(execution_id)
        self.assertFalse((directory / "receipt.json").exists())
        self.assertEqual(len(list(directory.glob("finalizer-timeout-error-*.json"))), 1)
        self.assertIn("synthetic output", (directory / "stdout.log").read_text())

    def test_manual_finalization_without_notify_socket_is_a_noop_for_extension(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with runner.finalizer_timeout_extension() as health_check:
                health_check()
        self.assertFalse(any(t.name == "openrx-finalizer-heartbeat" for t in threading.enumerate()))

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
