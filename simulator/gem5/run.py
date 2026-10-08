#!/usr/bin/env python3
"""Run a real gem5 Linux boot and validate guest runtime/hash controls."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
import platform
import re
import resource
import signal
import subprocess
import time
from pathlib import Path

if __package__:
    from . import prepare
else:
    import prepare

ROOT = Path(__file__).resolve().parents[2]


def load_validator(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_output


def elf_info(path):
    data = path.read_bytes()
    if len(data) < 20 or data[:6] != b"\x7fELF\x02\x01" or int.from_bytes(data[18:20], "little") != 243:
        raise ValueError("Guest probe must be ELF64 little-endian RISC-V")
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def guest_script(binaries):
    lines = ["#!/bin/bash", "set -eu", "umask 077", "mkdir -p /tmp/openrx", "cd /tmp/openrx",
             "uname -a", "cat /proc/cpuinfo", "cat /proc/meminfo", "cat /etc/os-release"]
    for name, path in binaries.items():
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        # A quoted heredoc avoids command-substitution/argument-length issues.
        lines += [f"base64 -d > {name} <<'OPENRX_BINARY_BASE64'", encoded, "OPENRX_BINARY_BASE64",
                  f"printf '%s  %s\\n' '{digest}' '{name}' | sha256sum -c -", f"chmod 700 {name}",
                  f"printf 'OPENRX_{name.upper()}_BEGIN\\n'", "set +e",
                  f"./{name} 2> {name}.stderr | tee {name}.jsonl",
                  'statuses=("${PIPESTATUS[@]}")', 'status=${statuses[0]}',
                  'capture_status=${statuses[1]}', "set -e",
                  'if [ "$capture_status" -ne 0 ]; then exit "$capture_status"; fi',
                  f"printf 'OPENRX_{name.upper()}_END status=%s\\n' \"$status\"",
                  f"printf 'OPENRX_{name.upper()}_STDERR_BEGIN\\n'", f"cat {name}.stderr",
                  f"printf 'OPENRX_{name.upper()}_STDERR_END\\n'",
                  'if [ "$status" -ne 0 ]; then exit "$status"; fi']
    lines += ["printf 'OPENRX_GUEST_COMPLETE\\n'"]
    return "\n".join(lines) + "\n"


def extract_probe(raw, name):
    raw = raw.replace("\r", "")
    prefix = "OPENRX_" + name.upper()
    pattern = re.escape(prefix + "_BEGIN\n") + r"(.*?)" + re.escape(prefix + "_END status=") + r"(\d+)\n"
    matches = re.findall(pattern, raw, flags=re.S)
    errors = re.findall(re.escape(prefix + "_STDERR_BEGIN\n") + r"(.*?)" + re.escape(prefix + "_STDERR_END\n"), raw, flags=re.S)
    if len(matches) != 1 or len(errors) != 1:
        raise ValueError(f"Missing or duplicate framed {name} guest output")
    body, status = matches[0]
    if int(status) != 0 or errors[0].strip():
        raise ValueError(f"Guest {name} failed or wrote stderr")
    return body, errors[0]


def run_process(command, *, stdout, stderr, timeout):
    """Wait for our new session, stopping its whole group on early exit.

    Signals during Popen are recorded until the child object is available, so
    an interruption cannot escape the launch window without cleaning up.
    Restore the caller's handlers before validating the retained guest output.
    """
    process = None
    interrupted_signal = None
    handlers = {}
    result = {"returncode": None}

    def interrupt(signum, _frame):
        nonlocal interrupted_signal
        if interrupted_signal is None:
            interrupted_signal = signum
        result.update(returncode=None, interrupted=True,
                      interruption_signal=signal.Signals(interrupted_signal).name)
        # Never raise into arbitrary launch/wait/cleanup bytecode. Killing an
        # unreaped session leader's group also wakes wait(), and its PID cannot
        # have been reused. Before Popen returns, remember the signal instead.
        if process is not None and process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError as exc:
                result["signal_cleanup_error"] = str(exc)

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            handlers[signum] = signal.signal(signum, interrupt)
        completed = False
        try:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
            if interrupted_signal is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            result["returncode"] = process.wait(timeout=timeout or None)
            completed = True
        except subprocess.TimeoutExpired:
            result["timed_out"] = True
        finally:
            # A normal reaped child must not trigger a kill against a potentially
            # reused PID. Early exit also stops descendants ignoring SIGTERM.
            if process is not None:
                if not completed:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait()
        if result.get("interrupted"):
            result["returncode"] = None
        if result.get("timed_out") or result.get("interrupted"):
            result["child_returncode"] = process.returncode
        return result
    finally:
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gem5", type=Path, required=True)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--runtime-binary", type=Path, required=True)
    parser.add_argument("--hash-binary", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=0,
                        help="Optional positive wall-clock limit in seconds; 0 (default) disables the limit")
    parser.add_argument("--max-ticks", type=int, default=10**13)
    args = parser.parse_args()
    if args.timeout < 0 or args.max_ticks <= 0:
        parser.error("timeout must be nonnegative and max-ticks must be positive")
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = {"schema_version": 1, "evidence_class": "full-system-functional",
              "status": "fail", "boot_observed": False, "runtime_validated": False,
              "hash_controls_requested": bool(args.hash_binary), "full_dataset": False,
              "timing_calibrated": False, "power_measured": False,
              "host": platform.platform(), "timeout_seconds": args.timeout or None,
              "gem5_source_commit_expected": "c8222cc67a399bfc01e8658dd14b30d5bfd634f9",
              "source_build_provenance_required_separately": True,
              "max_ticks_per_simulate_call": args.max_ticks}
    started = time.monotonic()
    try:
        args.gem5 = args.gem5.resolve(strict=True)
        args.resources = args.resources.resolve(strict=True)
        binaries = {"runtime": args.runtime_binary.resolve(strict=True)}
        if args.hash_binary:
            binaries["hash"] = args.hash_binary.resolve(strict=True)
        report["guest_binaries"] = {name: elf_info(path) for name, path in binaries.items()}
        report["gem5_binary_sha256"] = prepare.hashes(args.gem5)["sha256"]
        config = Path(__file__).with_name("fs.py").resolve()
        manifest_path = Path(__file__).with_name("resources.json")
        manifest = json.loads(manifest_path.read_text())
        report["config_sha256"] = hashlib.sha256(config.read_bytes()).hexdigest()
        report["resource_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        report["resources"] = [dict(resource, observed=prepare.verify(args.resources / resource["filename"], resource))
                               for resource in manifest["resources"]]
        readfile = args.output_dir / "guest.sh"
        readfile.write_text(guest_script(binaries))
        report["readfile_sha256"] = hashlib.sha256(readfile.read_bytes()).hexdigest()
        outdir = args.output_dir / "m5out"
        outdir.mkdir()
        command = [str(args.gem5), "--outdir=" + str(outdir), str(config),
                   "--resources", str(args.resources), "--readfile", str(readfile),
                   "--max-ticks", str(args.max_ticks)]
        report["command"] = command
        with (args.output_dir / "stdout.log").open("wb") as stdout, (args.output_dir / "stderr.log").open("wb") as stderr:
            report.update(run_process(command, stdout=stdout, stderr=stderr, timeout=args.timeout))
        simulation_path = outdir / "simulation.json"
        if simulation_path.exists():
            report["simulation"] = json.loads(simulation_path.read_text())
            report["boot_observed"] = any(x["hypercall"] == 1 for x in report["simulation"]["events"])
        terminals = list(outdir.glob("*terminal*"))
        if len(terminals) != 1 or terminals[0].stat().st_size > 32 * 1024**2:
            raise ValueError("Missing, ambiguous or oversized guest serial log")
        raw = terminals[0].read_text()
        report["boot_observed"] = report["boot_observed"] or "Kernel booted, In gem5 init..." in raw
        report["guest_serial_sha256"] = hashlib.sha256(terminals[0].read_bytes()).hexdigest()
        # Bind partial controls too: a timeout must not bypass input identity.
        if report["config_sha256"] != hashlib.sha256(config.read_bytes()).hexdigest():
            raise ValueError("Simulation config changed during execution")
        if report["resource_manifest_sha256"] != hashlib.sha256(manifest_path.read_bytes()).hexdigest():
            raise ValueError("Resource manifest changed during execution")
        if report["readfile_sha256"] != hashlib.sha256(readfile.read_bytes()).hexdigest():
            raise ValueError("Guest readfile changed during execution")
        for resource_info in manifest["resources"]:
            prepare.verify(args.resources / resource_info["filename"], resource_info)
        if report["gem5_binary_sha256"] != prepare.hashes(args.gem5)["sha256"]:
            raise ValueError("gem5 binary changed during execution")
        for name, path in binaries.items():
            if report["guest_binaries"][name] != elf_info(path):
                raise ValueError("Guest binary changed during execution")
        # Extract and validate completed controls even if a later hash attempt
        # times out or is interrupted; neither cancellation nor partial hashes pass.
        validations = {}
        for name in binaries:
            body, errors = extract_probe(raw, name)
            (args.output_dir / (name + ".jsonl")).write_text(body)
            (args.output_dir / (name + "-stderr.log")).write_text(errors)
            validator = load_validator("native_runtime_probe" if name == "runtime" else "native_riscv_probe")
            validations[name] = validator(body, **({"expect_architecture": "riscv64"} if name == "runtime" else {"expect_riscv": True}))
            report["validated"] = validations
            if name == "runtime":
                report["runtime_validated"] = True
        if report.get("returncode") != 0 or report.get("interrupted") or "OPENRX_GUEST_COMPLETE" not in raw:
            raise ValueError("gem5 failed/timed out/interrupted or guest script did not complete")
        if [x["hypercall"] for x in report.get("simulation", {}).get("events", [])] != [1, 2, 3]:
            raise ValueError("Incomplete Linux/after-boot event sequence")
        report["status"] = "pass"
    except (OSError, ValueError, UnicodeError) as exc:
        report["error"] = str(exc)
        if report.get("interrupted"):
            report["error"] = "Simulator interrupted by " + report["interruption_signal"] + "; " + report["error"]
    finally:
        report["host_elapsed_seconds"] = time.monotonic() - started
        report["host_child_max_rss_kib"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
