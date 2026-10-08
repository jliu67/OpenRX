#!/usr/bin/env python3
"""Read-only replay of an actual runtime attempt; never launch a simulator."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import sys

ORACLES = {
    "sigill-recovery": 4, "rw-execution-denied": 11, "initial-cache-flush": 0,
    "generated-return": 7, "rx-write-denied": 11, "overwrite-cache-flush": 0,
    "overwritten-return": 19, "restore-cache-flush": 0, "restored-return": 7,
}


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def load(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=strict_object)


def hashes(path):
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            sha.update(block)
            md5.update(block)
            size += len(block)
    return {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--source-binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = load(args.attempt / "report.json")
    audit = {"scope": "independent actual serial/control/input replay; no simulator launch",
             "reviewer": "/root/gem5_review", "command": [sys.executable, *sys.argv],
             "reported_status": report["status"], "bindings_pass": False,
             "guest_runtime_gate_accepted": False, "timing_calibrated": False,
             "power_measured": False, "resource_hashes": {}}
    try:
        binding = load(args.source_binding)
        assert binding["status"] == "pass"
        assert report["gem5_binary_sha256"] == binding["binary"]["sha256"]
        for name, filename in [("config_sha256", "fs.py"),
                               ("resource_manifest_sha256", "resources.json")]:
            assert hashes(args.repo / "simulator/gem5" / filename)["sha256"] == report[name]
        script = args.attempt / "guest.sh"
        assert hashes(script)["sha256"] == report["readfile_sha256"]
        encoded = re.search(r"base64 -d > runtime <<'OPENRX_BINARY_BASE64'\n([A-Za-z0-9+/=]+)\nOPENRX_BINARY_BASE64", script.read_text())[1]
        payload = base64.b64decode(encoded, validate=True)
        guest = report["guest_binaries"]["runtime"]
        assert payload == Path(guest["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == guest["sha256"]
        assert len(payload) == guest["bytes"]
        assert payload[:6] == b"\x7fELF\x02\x01" and int.from_bytes(payload[18:20], "little") == 243
        manifest = load(args.repo / "simulator/gem5/resources.json")
        for expected, retained in zip(manifest["resources"], report["resources"], strict=True):
            actual = hashes(args.resources / expected["filename"])
            assert actual == retained["observed"]
            assert actual["bytes"] == expected["bytes"]
            assert actual["sha256"] == expected["sha256"]
            assert actual["md5"] == expected["upstream_md5"]
            audit["resource_hashes"][expected["filename"]] = actual
        serials = list((args.attempt / "m5out").glob("*terminal*"))
        assert len(serials) == 1
        original = serials[0].read_bytes()
        assert hashlib.sha256(original).hexdigest() == report["guest_serial_sha256"]
        audit["serial_sha256"] = report["guest_serial_sha256"]
        audit["bindings_pass"] = True
        raw = original.decode().replace("\r", "")
        lines = raw.splitlines()
        audit["linux_kernel_console_observed"] = "Linux version 6.8.12" in raw
        audit["init_process_observed"] = "Run /sbin/gem5_init.sh as init process" in raw
        audit["guest_protocol_events"] = report.get("simulation", {}).get("events", [])
        try:
            markers = ["OPENRX_RUNTIME_BEGIN", "OPENRX_RUNTIME_END status=0",
                       "OPENRX_RUNTIME_STDERR_BEGIN", "OPENRX_RUNTIME_STDERR_END"]
            assert all(lines.count(marker) == 1 for marker in markers)
            positions = [lines.index(marker) for marker in markers]
            assert positions == sorted(positions)
            assert positions[3] == positions[2] + 1
            body = "\n".join(lines[positions[0] + 1:positions[1]]) + "\n"
            assert body == (args.attempt / "runtime.jsonl").read_text()
            assert (args.attempt / "runtime-stderr.log").read_text() == ""
            rows = [json.loads(line, object_pairs_hook=strict_object) for line in body.splitlines()]
            assert len(rows) == 11
            assert rows[0] == {"type": "config", "schema_version": 1,
                               "architecture": "riscv64", "flush_path": "linux-riscv-flush-icache",
                               "functional_only": True}
            for row, (name, value) in zip(rows[1:-1], ORACLES.items(), strict=True):
                assert row == {"type": "check", "name": name, "actual": value,
                               "expected": value, "status": "pass"}
                assert type(row["actual"]) is int and type(row["expected"]) is int
            assert rows[-1] == {"type": "summary", "checks": 9, "status": "pass", "functional_only": True}
            assert type(rows[-1]["checks"]) is int
            audit["independent_controls_passed"] = 9
            assert lines.count("OPENRX_GUEST_COMPLETE") == 1
            assert lines.index("OPENRX_GUEST_COMPLETE") > positions[-1]
            assert [event["hypercall"] for event in audit["guest_protocol_events"]] == [1, 2, 3]
            ticks = [event["tick"] for event in audit["guest_protocol_events"]]
            assert ticks == sorted(ticks)
            assert report["returncode"] == 0 and not report.get("timed_out", False)
            assert report["hash_controls_requested"] is False
            assert report["runtime_validated"] is True
            assert report["validated"]["runtime"]["checks_passed"] == 9
            audit["guest_runtime_gate_accepted"] = True
        except (AssertionError, KeyError, ValueError, OSError) as exc:
            audit["guest_gate_error"] = type(exc).__name__ + ": " + str(exc)
        audit["reported_status_matches_replay"] = (report["status"] == "pass") == audit["guest_runtime_gate_accepted"]
        audit["status"] = "pass" if audit["reported_status_matches_replay"] else "fail"
    except (AssertionError, KeyError, ValueError, OSError) as exc:
        audit["status"] = "fail"
        audit["binding_error"] = type(exc).__name__ + ": " + str(exc)
    args.output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
