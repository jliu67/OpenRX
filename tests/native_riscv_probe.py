#!/usr/bin/env python3
"""Run and independently validate the bounded native/RISC-V functional probe.

Raw streams and failure reports are preserved. This never measures throughput,
simulated cycles, energy, or the full-dataset mining path.
"""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HASHES = {
    ("v1", "a"): "639183aae1bf4c9a35884cb46b09cad9175f04efd7684e7262a0ac1c2f0b4e3f",
    ("v1", "b"): "300a0adb47603dedb42228ccb2b211104f4da45af709cd7547cd049e9489c969",
    ("v2", "a"): "22ec6b861b3eb23686b2efbad69513c967ecfce80983df66c9c5b4fbfb4cdb6f",
    ("v2", "b"): "9e2c772c12fd48f93c14c97fdc89d556264d9100597023f44d9163e279012ecf",
}

SEMANTICS = {
    "integer/add-wrap": "0000000000000000",
    "integer/sub-wrap": "ffffffffffffffff",
    "integer/mul-low-wrap": "fffffffffffffffe",
    "integer/mul-unsigned-high-max": "fffffffffffffffe",
    "integer/mul-unsigned-high-carry": "0000000000000001",
    "integer/mul-signed-high-negative": "ffffffffffffffff",
    "integer/mul-signed-high-positive": "4000000000000000",
}
for mode, number, values in (
    ("nearest", "0", ("3ff0000000000000", "bff0000000000000", "3ff0000000000002", "3fb999999999999a", "3ff6a09e667f3bcd")),
    ("down", "1", ("3ff0000000000000", "bff0000000000001", "3ff0000000000002", "3fb9999999999999", "3ff6a09e667f3bcc")),
    ("up", "2", ("3ff0000000000001", "bff0000000000000", "3ff0000000000003", "3fb999999999999a", "3ff6a09e667f3bcd")),
    ("zero", "3", ("3ff0000000000000", "bff0000000000000", "3ff0000000000002", "3fb9999999999999", "3ff6a09e667f3bcc")),
):
    SEMANTICS[f"fp/{mode}/mode"] = number
    for operation, value in zip(("add-positive", "subtract-negative", "multiply", "divide", "sqrt"), values):
        SEMANTICS[f"fp/{mode}/{operation}"] = value


def validate_output(raw, *, expect_riscv=False):
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not records or records[0].get("type") != "config" or records[-1].get("type") != "summary":
        raise ValueError("Missing initial config or final summary")
    config, summary = records[0], records[-1]
    if config.get("schema_version") != 1 or config.get("full_dataset") is not False:
        raise ValueError("Wrong probe schema or measurement scope")
    if expect_riscv and config.get("compiled_architecture") != "riscv64":
        raise ValueError("QEMU run must report a RISC-V compiled probe")
    middle = records[1:-1]
    if any(x.get("type") not in ("check", "stage") for x in middle):
        raise ValueError("Unexpected intermediate record")
    stages = [x for x in middle if x.get("type") == "stage"]
    if [(x.get("name"), x.get("engine"), x.get("status")) for x in stages] != [
        ("cache-init", e, s) for e in ("interpreter", "jit") for s in ("begin", "pass")
    ]:
        raise ValueError("Missing or inconsistent cache initialization stages")
    checks = [x for x in middle if x.get("type") == "check"]
    names = [x.get("name") for x in checks]
    if len(set(names)) != len(names) or any(not isinstance(n, str) or not n for n in names):
        raise ValueError("Duplicate or missing check identity")
    if any(x.get("status") not in ("pass", "skip") for x in checks):
        raise ValueError("Failed or unknown check outcome")
    required = [x for x in checks if x.get("required") is True]
    if len(required) != 39 or any(x.get("status") != "pass" for x in required):
        raise ValueError("All 39 required semantic/hash checks must pass")
    if any(x.get("expected") != x.get("actual") for x in required):
        raise ValueError("Required actual value differs from expected")
    semantics = [x for x in checks if not x.get("name", "").startswith("hash/") and x.get("required") is True]
    if {x["name"] for x in semantics} != set(SEMANTICS):
        raise ValueError("Incomplete or unknown integer/FP semantic checks")
    for x in semantics:
        if x.get("expected") != SEMANTICS[x["name"]] or x.get("actual") != SEMANTICS[x["name"]]:
            raise ValueError("Semantic result differs from independent exact oracle")
    seen = set()
    for x in checks:
        if x.get("aes") != "software" or "algorithm" not in x:
            continue
        key = (x.get("algorithm"), x.get("engine"), x.get("vector"))
        if key in seen or key[1] not in ("interpreter", "jit"):
            raise ValueError("Duplicate/unknown software hash case")
        expected = HASHES.get((key[0], key[2]))
        if (not expected or x.get("name") != "hash/" + "/".join((key[0], key[1], "software", key[2]))
                or x.get("expected") != expected or x.get("actual") != expected or x.get("required") is not True):
            raise ValueError("Hash does not match independent pinned upstream vector")
        seen.add(key)
    expected_cases = {(v, e, n) for v in ("v1", "v2") for e in ("interpreter", "jit") for n in ("a", "b")}
    if seen != expected_cases:
        raise ValueError("Incomplete v1/v2 interpreter/JIT matrix")
    passed = sum(x.get("status") == "pass" for x in checks)
    skipped = sum(x.get("status") == "skip" for x in checks)
    if (summary.get("status") != "pass" or summary.get("failures") != 0
            or summary.get("checks") != len(checks) or summary.get("skips") != skipped
            or summary.get("required_checks") != 39 or summary.get("required_passed") != 39
            or passed + skipped != len(checks)):
        raise ValueError("Summary inconsistent with complete record stream")
    return {"required_checks_passed": 39, "optional_skips": skipped, "software_hash_cases": len(seen),
            "compiled_architecture": config["compiled_architecture"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--qemu")
    p.add_argument("--sysroot", type=Path, default=Path("/usr/riscv64-linux-gnu"))
    p.add_argument("--timeout", type=int, default=600)
    a = p.parse_args()
    if a.timeout <= 0:
        p.error("timeout must be positive")
    binary = a.binary.resolve(strict=True)
    elf = binary.read_bytes()
    if a.qemu and (elf[:6] != b"\x7fELF\x02\x01" or int.from_bytes(elf[18:20], "little") != 243):
        p.error("QEMU input must be an ELF64 little-endian RISC-V binary")
    command = [str(binary)]
    if a.qemu:
        emulator = shutil.which(a.qemu)
        if not emulator:
            p.error("QEMU executable unavailable")
        command = [emulator, "-cpu", "rv64,v=false", "-L", str(a.sysroot.resolve()), str(binary)]
    a.output_dir.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "evidence_class": "functional-emulation" if a.qemu else "native-functional",
              "full_dataset": False, "timing_calibrated": False, "power_measured": False,
              "command": command, "timeout_seconds": a.timeout, "host": platform.platform(),
              "binary_sha256": hashlib.sha256(elf).hexdigest(), "binary": str(binary)}
    stdout = stderr = b""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=a.timeout)
        stdout, stderr = result.stdout, result.stderr
        report["returncode"] = result.returncode
        if result.returncode:
            raise ValueError("Probe exited unsuccessfully")
        report["validated"] = validate_output(stdout.decode("utf-8"), expect_riscv=bool(a.qemu))
        report["status"] = "pass"
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        report.update(status="fail", error="Probe timeout", returncode=None)
    except (OSError, ValueError, UnicodeError) as exc:
        report.update(status="fail", error=str(exc))
    finally:
        (a.output_dir / "probe.jsonl").write_bytes(stdout)
        (a.output_dir / "stderr.log").write_bytes(stderr)
        (a.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
