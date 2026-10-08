#!/usr/bin/env python3
"""Read-only replay of the sole actual gem5 light attempt, including failures."""
import argparse
import base64
import configparser
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame(lines, name):
    prefix = "OPENRX_" + name.upper()
    markers = [prefix + "_BEGIN", prefix + "_END status=0",
               prefix + "_STDERR_BEGIN", prefix + "_STDERR_END"]
    for marker in markers:
        if lines.count(marker) != 1:
            raise ValueError("Expected one exact marker: " + marker)
    positions = [lines.index(marker) for marker in markers]
    if positions != sorted(positions) or positions[3] != positions[2] + 1:
        raise ValueError("Frame order or nonempty framed stderr: " + name)
    return "\n".join(lines[positions[0] + 1:positions[1]]) + "\n", positions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--resources", required=True, type=Path)
    parser.add_argument("--source-binding", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    runtime = import_file("independent_runtime_review", Path(__file__).resolve().parent.parent / "actual-runtime-review-20261008/replay_runtime.py")
    load, hashes = runtime.load, runtime.hashes
    report = load(args.attempt / "report.json")
    audit = {"scope": "independent actual light serial/input/config replay; no ELF or simulator execution",
             "reviewer": "/root/gem5_review", "argv": [sys.executable, *sys.argv],
             "reported_status": report["status"], "bindings_pass": False,
             "runtime_controls_passed": 0, "full_light_gate_accepted": False,
             "timing_calibrated": False, "power_measured": False,
             "resource_hashes": {}, "guest_binary_hashes": {}}
    try:
        binding = load(args.source_binding)
        assert binding["status"] == "pass"
        source_manifest = load(args.attempt / "execution-source/manifest.json")
        audit["executing_source_snapshot"] = []
        for source in source_manifest["files"]:
            snapshot = args.attempt / source["snapshot_path"]
            actual = hashes(snapshot)
            assert actual["bytes"] == source["bytes"] and actual["sha256"] == source["sha256"]
            audit["executing_source_snapshot"].append({"path": source["repository_path"], "bytes": actual["bytes"], "sha256": actual["sha256"]})
        original_runner = hashes(args.attempt / "execution-source/simulator/gem5/run.py")
        assert original_runner["sha256"] == "7ae0fd2c8c3364cd8f3fc8ff2c082c810e112cd9c71395ab04b89c4915dfcd0a"
        audit["current_runner_differs_from_actual_execution"] = hashes(args.repo / "simulator/gem5/run.py")["sha256"] != original_runner["sha256"]
        semantic = import_file("independent_existing_hash_oracles", args.attempt / "execution-source/tests/native_riscv_probe.py")
        actual_simulator = hashes(Path(report["command"][0]))
        assert actual_simulator["sha256"] == report["gem5_binary_sha256"] == binding["binary"]["sha256"]
        audit["simulator_binary"] = actual_simulator
        for key, name in [("config_sha256", "fs.py"), ("resource_manifest_sha256", "resources.json")]:
            assert hashes(args.repo / "simulator/gem5" / name)["sha256"] == report[key]
        script = args.attempt / "guest.sh"
        assert hashes(script)["sha256"] == report["readfile_sha256"]
        for name in ("runtime", "hash"):
            match = re.search(r"base64 -d > " + name + r" <<'OPENRX_BINARY_BASE64'\n([A-Za-z0-9+/=]+)\nOPENRX_BINARY_BASE64", script.read_text())
            assert match
            payload = base64.b64decode(match[1], validate=True)
            guest = report["guest_binaries"][name]
            assert payload == Path(guest["path"]).read_bytes()
            assert hashlib.sha256(payload).hexdigest() == guest["sha256"]
            assert len(payload) == guest["bytes"]
            assert payload[:6] == b"\x7fELF\x02\x01" and int.from_bytes(payload[18:20], "little") == 243
            audit["guest_binary_hashes"][name] = {"bytes": len(payload), "sha256": guest["sha256"]}
        manifest = load(args.repo / "simulator/gem5/resources.json")
        for pin, retained in zip(manifest["resources"], report["resources"], strict=True):
            actual = hashes(args.resources / pin["filename"])
            assert actual == retained["observed"]
            assert actual == {"bytes": pin["bytes"], "sha256": pin["sha256"], "md5": pin["upstream_md5"]}
            audit["resource_hashes"][pin["filename"]] = actual
        ini = configparser.ConfigParser(interpolation=None)
        ini.read(args.attempt / "m5out/config.ini")
        core = "board.processor.cores.core"
        assert [section for section in ini if ini[section].get("type") == "BaseAtomicSimpleCPU"] == [core]
        assert ini[core]["numThreads"] == "1"
        assert ini[core + ".isa"]["riscv_type"] == "RV64" and ini[core + ".isa"]["enable_rvv"] == "false"
        assert ini["board"]["mem_ranges"] == "2147483648:6442450944"
        assert Path(ini["board"]["readfile"]) == script
        assert ini["board.workload"]["command_line"] == "console=ttyS0 root=/dev/vda1 disk_device=/dev/vda rw init=/sbin/gem5_init.sh no_systemd"
        for name, size in {"l1i-cache-0": 16384, "l1d-cache-0": 16384, "l2-cache-0": 262144, "iptw_caches": 8192, "dptw_caches": 8192}.items():
            assert int(ini["board.cache_hierarchy." + name]["size"]) == size
        original = (args.attempt / "m5out/board.platform.terminal").read_bytes()
        audit["serial_sha256"] = hashlib.sha256(original).hexdigest()
        assert audit["serial_sha256"] == report["guest_serial_sha256"]
        lines = original.decode().replace("\r", "").splitlines()
        audit["guest_protocol_events"] = report.get("simulation", {}).get("events", [])
        audit["reported_timeout"] = report.get("timed_out", False)
        audit["reported_returncode"] = report.get("returncode")
        audit["declared_timeout_seconds"] = report["timeout_seconds"]
        audit["bindings_pass"] = True
        runtime_end = None
        try:
            body, positions = frame(lines, "runtime")
            rows = [json.loads(line, object_pairs_hook=runtime.strict_object) for line in body.splitlines()]
            assert body == (args.attempt / "runtime.jsonl").read_text()
            assert (args.attempt / "runtime-stderr.log").read_text() == ""
            assert len(rows) == 11 and rows[0] == {"type": "config", "schema_version": 1, "architecture": "riscv64", "flush_path": "linux-riscv-flush-icache", "functional_only": True}
            for row, (name, value) in zip(rows[1:-1], runtime.ORACLES.items(), strict=True):
                assert row == {"type": "check", "name": name, "actual": value, "expected": value, "status": "pass"}
                assert type(row["actual"]) is int and type(row["expected"]) is int
            assert rows[-1] == {"type": "summary", "checks": 9, "status": "pass", "functional_only": True}
            audit["runtime_controls_passed"] = 9
            runtime_end = positions[-1]
        except (AssertionError, ValueError, KeyError, OSError) as exc:
            audit["runtime_error"] = type(exc).__name__ + ": " + str(exc)
        try:
            body, positions = frame(lines, "hash")
            assert runtime_end is not None and positions[0] > runtime_end
            for line in body.splitlines():
                json.loads(line, object_pairs_hook=runtime.strict_object)
            assert body == (args.attempt / "hash.jsonl").read_text()
            assert (args.attempt / "hash-stderr.log").read_text() == ""
            audit["hash_validation"] = semantic.validate_output(body, expect_riscv=True)
            assert lines.count("OPENRX_GUEST_COMPLETE") == 1 and lines.index("OPENRX_GUEST_COMPLETE") > positions[-1]
            events = audit["guest_protocol_events"]
            assert [event["hypercall"] for event in events] == [1, 2, 3]
            assert [event["tick"] for event in events] == sorted(event["tick"] for event in events)
            assert report["returncode"] == 0 and not report.get("timed_out", False)
            assert report["hash_controls_requested"] is True and report["runtime_validated"] is True
            assert report["validated"]["hash"] == audit["hash_validation"]
            audit["full_light_gate_accepted"] = True
        except (AssertionError, ValueError, KeyError, OSError) as exc:
            audit["hash_gate_error"] = type(exc).__name__ + ": " + str(exc)
        if "OPENRX_HASH_BEGIN" in lines:
            start = lines.index("OPENRX_HASH_BEGIN") + 1
            partial = []
            for line in lines[start:]:
                try:
                    row = json.loads(line, object_pairs_hook=runtime.strict_object)
                    if isinstance(row, dict):
                        partial.append(row)
                except ValueError:
                    break
            audit["observed_hash_records"] = len(partial)
            audit["observed_hash_check_names"] = [row.get("name") for row in partial if row.get("type") == "check"]
            audit["last_observed_hash_record"] = partial[-1] if partial else None
        audit["reported_status_matches_replay"] = (report["status"] == "pass") == audit["full_light_gate_accepted"]
        assert report["runtime_validated"] == (audit["runtime_controls_passed"] == 9)
        audit["status"] = "pass" if audit["reported_status_matches_replay"] else "fail"
    except (AssertionError, ValueError, KeyError, OSError) as exc:
        audit["status"] = "fail"
        audit["binding_error"] = type(exc).__name__ + ": " + str(exc)
    args.output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
