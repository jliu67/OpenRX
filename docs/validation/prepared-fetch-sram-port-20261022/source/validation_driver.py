#!/usr/bin/env python3
"""PREPARED / UNRUN. Four commands require a fresh specifically approved admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    require(not output.is_relative_to(source), "output must be outside frozen source")
    require(args.source_manifest.resolve(strict=True) == source / "SOURCE-MANIFEST01.json",
            "exact source manifest required")
    admitted = json.loads((output.parent / "manifest.json").read_text())
    execution_id = admitted.get("execution_id")
    require(type(execution_id) is str and
            re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}", execution_id) is not None,
            "canonical execution identity required")
    require(output == Path("/home/server/openrx-local/v1/executions") / execution_id / "results",
            "output must be the canonical fresh execution/results child")
    require(admitted.get("schema") == "openrx.local.execution.v1" and
            admitted.get("migration_state") == "LOCAL_ACTIVE" and
            admitted.get("cwd") == str(source), "fresh active admission required")
    require(admitted.get("kind") == "simulation" and admitted.get("validation_scope") is None and
            admitted.get("request_key") == "issue72-prepared-fetch-sram-20261022-01",
            "exact future request admission required")
    require(admitted.get("runner", {}).get("sha256") ==
            "657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b",
            "pinned immutable runner required")
    argv, driver = admitted.get("argv", []), str(Path(__file__).resolve())
    require(driver in argv and argv[argv.index(driver) + 1:] == sys.argv[1:] and
            Path(argv[0]).resolve() == Path(sys.executable).resolve() and sys.dont_write_bytecode,
            "live Python/driver argv differs")
    unit = admitted.get("unit")
    require(unit == "openrx-" + execution_id + ".service" and any(unit in row.split(":", 2)[-1].split("/")
            for row in Path("/proc/self/cgroup").read_text().splitlines()), "outside admitted cgroup")
    caps = admitted.get("resources", {})
    require(caps.get("CPUQuota") == "600%" and caps.get("MemoryMax") == "1073741824" and
            caps.get("MemorySwapMax") == "2G" and caps.get("TasksMax") == 256 and
            caps.get("global_slots") == 1 and
            admitted.get("resource_profile", {}).get("name") == "owner-local-max-v1",
            "resource scope changed; outer runner must check fresh kernel/ancestors/headroom")
    manifest_pin = sha(args.source_manifest)
    frozen = json.loads(args.source_manifest.read_text())
    require(frozen.get("schema") == "openrx.prepared-fetch-sram.preparation.v1" and
            frozen.get("expected_timed_commands") == 4 and frozen.get("expected_unit_methods") == 36,
            "frozen command/test scope differs")
    admitted_files = {}
    for group in (admitted.get("sources", []), admitted.get("inputs", [])):
        for entry in group:
            require(type(entry) is dict and type(entry.get("path")) is str, "malformed admitted binding")
            root = Path(entry["path"])
            children = entry.get("files", []) if entry.get("kind") == "directory" else [entry]
            for item in children:
                path = root / item["relative"] if entry.get("kind") == "directory" else root
                pin = {"bytes": item["bytes"], "sha256": item["sha256"]}
                key = str(path.resolve(strict=True))
                require(key not in admitted_files or admitted_files[key] == pin, "conflicting admitted binding")
                admitted_files[key] = pin

    def require_admitted_file(path, pin):
        require(admitted_files.get(str(path.resolve(strict=True))) ==
                {"bytes": pin["bytes"], "sha256": pin["sha256"]}, "file not bound by admission: " + str(path))

    require_admitted_file(args.source_manifest, {"bytes": args.source_manifest.stat().st_size,
                                                "sha256": manifest_pin})

    def check_source():
        require(sha(args.source_manifest) == manifest_pin, "source manifest changed")
        physical = set()
        for path in source.rglob("*"):
            require(not path.is_symlink(), "symlink in frozen source")
            if path.is_file():
                physical.add(str(path.relative_to(source)))
        require(physical == set(frozen["files"]) | {"SOURCE-MANIFEST01.json"}, "source file set changed")
        for rel, pin in frozen["files"].items():
            path = source / rel
            require_admitted_file(path, pin)
            require(path.resolve(strict=True).is_relative_to(source) and
                    path.stat().st_size == pin["bytes"] and sha(path) == pin["sha256"],
                    "frozen source changed: " + rel)

    def check_tools():
        for name, pin in json.loads((source / "tool-bindings.json").read_text())["files"].items():
            path = Path(name)
            require_admitted_file(path, pin)
            require(str(path.resolve(strict=True)) == pin["resolved_path"] and
                    path.stat().st_size == pin["bytes"] and sha(path) == pin["sha256"], "tool changed: " + name)

    check_source()
    check_tools()
    output.mkdir(parents=True, exist_ok=False)
    summary = {"schema": "openrx.prepared-fetch-sram.validation.v1", "status": "running",
               "scientific_acceptance": "unverified_pending_independent_review", "physical_acceptance": False,
               "commands_planned": 4, "commands": [], "source_manifest_sha256": manifest_pin,
               "full_hash_or_cacti_or_native_generation_or_mapping": False}
    # Controlled environment; explicit backend paths are also bound in tool-bindings.
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"}
    plan = json.loads((source / "validation-plan.json").read_text())
    require(len(plan["commands"]) == 4, "exact four-command plan required")

    def group_alive(process):
        process.poll()  # Nonblocking reap of our direct child if it has exited.
        try:
            os.killpg(process.pid, 0)
            return True
        except ProcessLookupError:
            return False

    def stop_group(process, row):
        # GNU time can exit before a descendant. Supervise the entire session
        # group, not just its leader, for one total five-second cleanup budget.
        old_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
        deadline = time.monotonic() + 5
        kill_at = deadline - 1
        killed = False
        try:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            while group_alive(process) and time.monotonic() < deadline:
                if not killed and time.monotonic() >= kill_at:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    killed = True
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
            row["process_group_drained"] = not group_alive(process)
            row["sigkill_sent"] = killed
            row["returncode"] = process.poll()
            # No blocking wait after the deadline. If still alive, the immutable
            # outer runner retains cgroup/slot ownership for failure cleanup.
        finally:
            signal.signal(signal.SIGINT, old_sigint)

    def run(entry):
        name = entry["name"]
        command = [part.replace("{SOURCE}", str(source)).replace("{OUTPUT}", str(output))
                   for part in entry["argv"]]
        directory = output / name
        directory.mkdir()
        row = {"name": name, "argv": command, "cwd": str(source), "returncode": None, "timed_out": False}
        summary["commands"].append(row)
        started = time.monotonic()
        try:
            with (directory / "stdout.txt").open("x") as stdout, (directory / "stderr.txt").open("x") as stderr:
                process = subprocess.Popen(["/usr/bin/time", "-v", "-o", str(directory / "time.txt"), *command],
                                           cwd=source, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                try:
                    row["returncode"] = process.wait(timeout=120)
                except BaseException as exc:
                    row["timed_out"] = isinstance(exc, subprocess.TimeoutExpired)
                    stop_group(process, row)
                    raise
                if group_alive(process):
                    stop_group(process, row)
                    raise RuntimeError("descendants outlived command leader; no later command permitted")
                row["process_group_drained"] = True
        finally:
            row["wall_seconds"] = time.monotonic() - started
            save(directory / "status.json", row)
            print(json.dumps(row), flush=True)
        require(row["returncode"] == 0, name + " failed; stop with later commands unrun")

    try:
        run(plan["commands"][0])
        log = (output / "units/stderr.txt").read_text()
        count = re.findall(r"^Ran (\d+) tests? in ", log, re.MULTILINE)
        require(count == ["36"] and re.search(r"^OK\s*$", log, re.MULTILINE) and
                not re.search(r"\b(skipped|FAILED|ERROR)\b", log), "actual unit count/results differ")
        summary["actual_unit_tests"] = 36
        run(plan["commands"][1])
        image_report = json.loads((output / "image/oracle.json").read_text())
        require(image_report.get("outcome") == "PASS_CONDITIONAL_IMAGE_PACKING_ONLY" and
                image_report.get("active_rows") == 3563 and image_report.get("padding_rows") == 533 and
                image_report.get("oracle_imports_exporter") is False and
                image_report.get("independent_gold_from_original_fields") is True and
                image_report.get("physical_sram_characterized") is False, "image scope/oracle differs")
        run(plan["commands"][2])
        require((output / "bench.vvp").is_file(), "compiled bench missing")
        run(plan["commands"][3])
        result = json.loads((output / "simulation.json").read_text())
        require(result.get("status") == "pass" and result.get("scenarios") == 12 and
                result.get("scope") == "behavioral_prepared_fetch_port_only" and
                result.get("active_row_queries_both_clients") == 7126 and
                result.get("active_requests") == result.get("row_reads") == 7167 and
                result.get("error_requests") == 32 and
                result.get("backend_requests") == result.get("backend_responses") == 7199 and
                result.get("cancelled_responses") == 3 and
                result.get("physical_acceptance") is False and result.get("full_hash_run") is False and
                type(result.get("modeled_clocks")) is int and 0 < result["modeled_clocks"] <= 100000,
                "simulation coverage/ledger/scope differs")
        require(result.get("controller_cadence") == {"capture_to_read_edges": 1,
                "capture_to_consume_edges": 2, "capture_spacing": 3, "captures": 32,
                "intervals": 31, "interval_clocks": 93}, "controller-specific cadence differs")
        ledger = result.get("clock_ledger", {})
        require(all(type(ledger.get(name)) is int and ledger[name] >= 0 for name in
                    ("total_modeled_clocks", "cumulative_channel_occupied_clocks",
                     "before_last_reset_occupied_clocks", "after_last_reset_occupied_clocks",
                     "cadence_interval_clocks")) and
                ledger["total_modeled_clocks"] == result["modeled_clocks"] and
                ledger["cumulative_channel_occupied_clocks"] ==
                    ledger["before_last_reset_occupied_clocks"] + ledger["after_last_reset_occupied_clocks"] and
                ledger["cumulative_channel_occupied_clocks"] <= result["modeled_clocks"] and
                ledger["cadence_interval_clocks"] == 93, "emitted occupied-clock ledger differs")
        summary.update(status="pass_functional_behavioral_port_only", commands_completed=4)
    except BaseException as exc:
        summary.update(status="interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed",
                       failure_type=type(exc).__name__, failure=str(exc))
        raise
    finally:
        try:
            check_source()
            check_tools()
            summary["bound_source_tools_unchanged"] = True
        except Exception as exc:
            summary.update(status="failed", bound_source_tools_unchanged=False, postcheck_failure=str(exc))
            raise
        finally:
            save(output / "validation-summary.json", summary)


if __name__ == "__main__":
    main()
