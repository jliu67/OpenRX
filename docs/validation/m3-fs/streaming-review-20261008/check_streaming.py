#!/usr/bin/env python3
"""Host-only synthetic generated-Bash controls; never execute gem5 or guest ELFs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.repo))
    from simulator.gem5 import run
    audit = {"scope": "host-only synthetic pipeline/control evidence; no gem5 boot or ELF execution",
             "argv": [sys.executable, *sys.argv], "cases": [], "inputs": {},
             "synthetic_adaptations": "relocate guest scratch directory; omit host/guest inventory commands; retain generated injection, pipeline, statuses, frame and completion commands"}
    for path in (args.repo / "simulator/gem5/run.py", args.repo / "tests/test_gem5_fs.py"):
        data = path.read_bytes()
        audit["inputs"][str(path)] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    cases = [
        ("complete-success", "printf '%s\\n' '{\"synthetic\":\"complete\"}'\nexit 0\n", False, False, 0),
        ("producer-exit-42", "printf '%s\\n' '{\"synthetic\":\"producer-failure\"}'\nexit 42\n", False, False, 42),
        ("capture-write-failure", "printf '%s\\n' '{\"synthetic\":\"capture-failure\"}'\nexit 0\n", True, False, 1),
        ("both-producer-capture-fail", "printf '%s\\n' '{\"synthetic\":\"both-fail\"}'\nexit 42\n", True, False, 1),
        ("producer-stderr", "printf '%s\\n' '{\"synthetic\":\"stderr\"}'\nprintf 'synthetic error\\n' >&2\nexit 0\n", False, False, 0),
        ("killed-incomplete-stream", "printf '%s\\n' '{\"synthetic\":\"before-kill\"}'\nread -r release\n", False, True, -9),
    ]
    for name, payload, capture_fail, kill, expected_exit in cases:
        result = {"name": name, "payload": payload, "capture_failure": capture_fail,
                  "killed_after_observed_record": kill}
        with tempfile.TemporaryDirectory(prefix="openrx-stream-review-") as temporary:
            root = Path(temporary)
            guest = root / "guest"
            guest.mkdir()
            synthetic = root / "payload.sh"
            synthetic.write_text("#!/bin/bash\n" + payload)
            script = run.guest_script({"runtime": synthetic}).replace("/tmp/openrx", str(guest))
            inventory = "uname -a\ncat /proc/cpuinfo\ncat /proc/meminfo\ncat /etc/os-release\n"
            assert inventory in script
            script = script.replace(inventory, ": # synthetic review omits inventory output\n")
            (root / "guest.sh").write_text(script)
            (args.output / (name + ".guest.sh")).write_text(script)
            if capture_fail:
                (guest / "runtime.jsonl").mkdir()
            with (root / "serial.log").open("wb") as serial, (root / "stderr.log").open("wb") as errors:
                process = subprocess.Popen(["bash", str(root / "guest.sh")], stdin=subprocess.PIPE,
                                           stdout=serial, stderr=errors, start_new_session=True)
                try:
                    if kill:
                        deadline = time.monotonic() + 5
                        first = b'{"synthetic":"before-kill"}\n'
                        capture = guest / "runtime.jsonl"
                        while not (first in (root / "serial.log").read_bytes() and capture.is_file() and capture.read_bytes() == first):
                            if time.monotonic() > deadline or process.poll() is not None:
                                raise AssertionError("No flushed record while producer was still active")
                            time.sleep(0.01)
                        assert process.poll() is None
                        result["partial_record_seen_while_active"] = True
                        assert (guest / "runtime.jsonl").read_text() == '{"synthetic":"before-kill"}\n'
                        os.killpg(process.pid, signal.SIGKILL)
                    result["returncode"] = process.wait(timeout=5)
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                    process.stdin.close()
            stdout = (root / "serial.log").read_text()
            stderr = (root / "stderr.log").read_text()
            (args.output / (name + ".stdout.log")).write_text(stdout)
            (args.output / (name + ".stderr.log")).write_text(stderr)
            result["stdout_sha256"] = hashlib.sha256(stdout.encode()).hexdigest()
            result["stderr_sha256"] = hashlib.sha256(stderr.encode()).hexdigest()
            capture = guest / "runtime.jsonl"
            if capture.is_file():
                (args.output / (name + ".capture.jsonl")).write_bytes(capture.read_bytes())
            assert result["returncode"] == expected_exit
            try:
                body, errors = run.extract_probe(stdout, "runtime")
                result["frame_accepted"] = True
                assert name == "complete-success" and errors == ""
                assert body == capture.read_text()
            except ValueError as exc:
                result["frame_accepted"] = False
                result["frame_error"] = str(exc)
                assert name != "complete-success"
            if capture_fail or kill:
                assert "OPENRX_RUNTIME_END" not in stdout and "OPENRX_GUEST_COMPLETE" not in stdout
            elif name == "producer-exit-42":
                assert "OPENRX_RUNTIME_END status=42\n" in stdout and "OPENRX_GUEST_COMPLETE" not in stdout
            result["status"] = "pass"
            audit["cases"].append(result)
    audit["status"] = "pass"
    (args.output / "controls.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
