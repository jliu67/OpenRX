#!/usr/bin/env python3
"""Synthetic wrapper fault controls; never executes gem5, Linux or RV64.

The runner receives a disposable host Python stub, an intentionally invalid
40-byte ELF-shaped payload, mocked resource verification and a replayed JSONL
fixture. Successful synthetic framing is not boot or guest-execution evidence.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import platform
from pathlib import Path
import sys
import tempfile
import textwrap
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "simulator/gem5"))
import run


CASES = [
    "baseline-synthetic", "guest-exit", "guest-stderr", "truncated",
    "missing-completion", "incomplete-events", "simulator-exit", "timeout",
    "later-hash-missing", "timeout-readfile-mutated",
]
LABEL = "synthetic-wrapper-fault-injection-only"
STUB = "#!/usr/bin/env python3\n" + textwrap.dedent("""
    import json, os, sys, time
    from pathlib import Path
    out = Path(next(x.split('=', 1)[1] for x in sys.argv if x.startswith('--outdir=')))
    case = os.environ['OPENRX_REVIEW_CASE']
    body = json.loads(os.environ['OPENRX_REVIEW_FIXTURE'])
    serial = ('Kernel booted, In gem5 init...\\nOPENRX_RUNTIME_BEGIN\\n' + body
              + 'OPENRX_RUNTIME_END status=' + ('1' if case == 'guest-exit' else '0')
              + '\\nOPENRX_RUNTIME_STDERR_BEGIN\\n'
              + ('failure\\n' if case == 'guest-stderr' else '')
              + 'OPENRX_RUNTIME_STDERR_END\\n')
    if case == 'truncated':
        serial = serial.split('OPENRX_RUNTIME_END')[0]
    if case not in ['missing-completion', 'timeout', 'timeout-readfile-mutated', 'later-hash-missing']:
        serial += 'OPENRX_GUEST_COMPLETE\\n'
    (out / 'board.platform.terminal').write_text(serial)
    if case == 'timeout-readfile-mutated':
        Path(sys.argv[sys.argv.index('--readfile') + 1]).write_text('altered guest script')
    if case in ['timeout', 'timeout-readfile-mutated']:
        time.sleep(60)
    events = [{'hypercall': i} for i in ([1, 2] if case == 'incomplete-events' else [1, 2, 3])]
    (out / 'simulation.json').write_text(json.dumps({'events': events}))
    sys.exit(1 if case == 'simulator-exit' else 0)
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1)
    args = parser.parse_args()
    if args.timeout <= 0 or args.timeout >= 60:
        parser.error("timeout must be between 1 and 59 seconds")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    fixture_path = Path(__file__).with_name("runtime-fixture.jsonl")
    fixture = fixture_path.read_text()
    metadata = {
        "schema_version": 1, "evidence_class": LABEL,
        "linux_boot_executed": False, "rv64_executed": False,
        "gem5_executed": False, "resource_verification_mocked": True,
        "payload": "40-byte ELF-shaped invalid dummy; never executed",
        "fixture_path": str(fixture_path.relative_to(ROOT)),
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "stub_sha256": hashlib.sha256(STUB.encode()).hexdigest(),
        "host": platform.platform(), "python": sys.version,
        "invocation": [sys.executable] + sys.argv,
        "timeout_seconds": args.timeout, "results": [], "status": "fail",
        "reviewed_inputs": {},
    }
    for relative in ["simulator/gem5/run.py", "simulator/gem5/fs.py",
                     "simulator/gem5/prepare.py", "simulator/gem5/resources.json",
                     "tests/native_runtime_probe.py", "tests/native_riscv_probe.py"]:
        metadata["reviewed_inputs"][relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    try:
        with tempfile.TemporaryDirectory(prefix="openrx-synthetic-review-") as directory:
            base = Path(directory)
            resources = base / "resources"
            resources.mkdir()
            binary = base / "dummy-payload"
            binary.write_bytes(b"\x7fELF\x02\x01" + bytes(12) + (243).to_bytes(2, "little") + bytes(20))
            stub = base / "synthetic-simulator-stub.py"
            stub.write_text(STUB)
            stub.chmod(0o755)
            for case in CASES:
                output = base / case
                argv = ["run.py", "--gem5", str(stub), "--resources", str(resources),
                        "--runtime-binary", str(binary), "--output-dir", str(output),
                        "--timeout", str(args.timeout)]
                if case == "later-hash-missing":
                    argv += ["--hash-binary", str(binary)]
                captured = io.StringIO()
                with (patch.object(sys, "argv", argv),
                      patch.dict(os.environ, {"OPENRX_REVIEW_CASE": case,
                                              "OPENRX_REVIEW_FIXTURE": json.dumps(fixture)}),
                      patch.object(run.prepare, "verify", return_value={"synthetic": True}),
                      contextlib.redirect_stdout(captured)):
                    code = run.main()
                report = json.loads((output / "report.json").read_text())
                expected_code = 0 if case == "baseline-synthetic" else 1
                expected_status = "pass" if expected_code == 0 else "fail"
                assert code == expected_code and report["status"] == expected_status, (case, report)
                if case in ["timeout", "later-hash-missing"]:
                    assert report["runtime_validated"] is True, (case, report)
                if case == "timeout-readfile-mutated":
                    assert not report["runtime_validated"] and "readfile changed" in report["error"], report
                case_dir = args.output_dir / case
                case_dir.mkdir()
                # Label before raw captured output: embedded runner boot fields
                # refer solely to supplied synthetic serial markers.
                (case_dir / "runner-stdout.log").write_text(
                    "SYNTHETIC WRAPPER CONTROL: NO GEM5, LINUX BOOT OR RV64 EXECUTION\n" + captured.getvalue())
                for source_name, target_name in [("stdout.log", "stub-stdout.log"),
                                                 ("stderr.log", "stub-stderr.log")]:
                    (case_dir / target_name).write_bytes((output / source_name).read_bytes())
                metadata["results"].append({
                    "case": case, "exit": code, "status": report["status"],
                    "runtime_validated": report["runtime_validated"],
                    "error": report.get("error"), "runner_argv": argv,
                    "stub_case_env": case, "evidence_class": LABEL,
                })
        metadata["status"] = "pass"
    except Exception as exc:
        metadata["error"] = str(exc)
        raise
    finally:
        (args.output_dir / "results.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("10 synthetic wrapper cases passed; gem5/Linux/RV64 were not executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
