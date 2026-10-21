#!/usr/bin/env python3
"""Staged, admitted shared-dataset component validation; never a full hash.

Each invocation needs its own immutable local-runner request. Prefix measures
one native pair before a later matrix or mapping admission. Retained native
fixtures are read-only, actual-byte bound inputs, not regenerated references.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_RECEIPT_SHA256 = "f3ced2d4f48eaa7c49359cea893c65666377c7f0a84386c035736357bfb59ad8"
COMMAND_TIMEOUT_SECONDS = 120
PROFILES = ("serial-ideal", "concurrent-ideal", "serial-stalled", "concurrent-stalled",
            "cancel0", "cancel1", "malformed-fetch0", "exhaustion")
ACCEPTED_RTL = ("rtl/execute/randomx_mul64.v", "rtl/execute/randomx_superscalar_execute.v",
                "rtl/dataset/randomx_dataset_item.v", "rtl/dataset_capacity/randomx_dataset_item_session.v")
FABRIC_RTL = ("rtl/dataset_shared/randomx_dataset_shared_channel.v",
              "rtl/dataset_shared/randomx_dataset_shared_fabric.v")
PROTOCOL_BENCH = "rtl/dataset_shared/tests/tb_dataset_shared_channel.v"
NATIVE_BENCH = "rtl/dataset_shared/tests/tb_dataset_shared_native.v"
PROTOCOL_SCHEMA = "openrx.shared-dataset-channel-protocol.v1"
NATIVE_SCHEMA = "openrx.dataset-shared.native.v1"
SUMMARY_SCHEMA = "openrx.dataset-shared.validation.v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"not a regular bound file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def binding(path):
    path = Path(path)
    return {"bytes": path.stat().st_size, "sha256": sha(path)}


def fingerprint(root):
    root = Path(root)
    require(not (root / ".git").exists(), "validation source must be a bounded non-Git materialization")
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "source contains an unbound symlink")
        if path.is_file():
            result[str(path.relative_to(root))] = binding(path)
        else:
            require(path.is_dir(), "source contains a nonregular entry")
    return result


def load_json(path, maximum=4 * 1024 * 1024):
    with Path(path).open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "JSON size limit exceeded")

    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "duplicate JSON key")
            value[key] = item
        return value

    def nonfinite(_):
        raise ValueError("nonfinite JSON value")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def save_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def integer(value, name, minimum=0):
    require(type(value) is int and minimum <= value <= (1 << 64) - 1,
            f"{name} must fit a nonnegative64-bit counter >= {minimum}")
    return value


def vector(value, length, name):
    require(type(value) is list and len(value) == length, f"{name} has the wrong length")
    for item in value:
        integer(item, name)
    return value


def completed_receipt(path, expected_sha):
    require(re.fullmatch(r"[0-9a-f]{64}", expected_sha or "") is not None, "receipt SHA256 required")
    require(sha(path) == expected_sha, "actual receipt bytes differ from external binding")
    receipt = load_json(path)
    require(receipt.get("schema") == "openrx.local.receipt.v1", "unexpected receipt schema")
    require(receipt.get("status") == "PROCESS_EXITED" and
            type(receipt.get("process", {}).get("returncode")) is int and
            receipt["process"]["returncode"] == 0, "prior execution did not exit successfully")
    require(receipt.get("execution_id") == Path(path).resolve().parent.name,
            "receipt execution identity differs from its directory")
    require(receipt.get("scientific_acceptance") == "unverified",
            "raw process receipt scientific flag was reclassified")
    rows = receipt.get("artifacts")
    require(type(rows) is list, "receipt has no artifact catalogue")
    artifacts = {}
    for row in rows:
        require(type(row) is dict and type(row.get("path")) is str, "invalid receipt artifact")
        integer(row.get("bytes"), "receipt artifact bytes")
        require(re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")) is not None,
                "invalid receipt artifact SHA256")
        key = str(Path(row["path"]).resolve())
        require(key not in artifacts, "duplicate receipt artifact")
        artifacts[key] = row
    return receipt, artifacts


def bound_artifact(path, artifacts):
    path = Path(path)
    require(not path.is_symlink(), "artifact path is an unbound symlink")
    path = path.resolve(strict=True)
    require(str(path) in artifacts, f"artifact absent from bound receipt: {path}")
    row = artifacts[str(path)]
    actual = binding(path)
    require(actual == {"bytes": row.get("bytes"), "sha256": row.get("sha256")},
            f"actual artifact differs from bound receipt: {path}")
    return actual


def selected_fixture_names():
    names = ["cases.hex", "cache-0.bin", "cache-0-metadata.json",
             "cache-0-prepared-programs.mem", "cache-0-original-programs.mem",
             "cache-0-reciprocals.mem", "cache-0-reciprocal-metadata.json"]
    for case in (0, 1):
        prefix = f"case-{case:03d}/"
        names += [prefix + name for name in ("metadata.json", "seed.hex", "final.hex", "stages.mem")]
        for stage in range(8):
            names += [prefix + f"{stem}-{stage}.mem"
                      for stem in ("program", "steps", "rcp-valid", "rcp-index", "reciprocals")]
    return sorted(names)


def fixture_bindings(fixtures, receipt_path):
    """Trust only actual bytes anchored by the independently accepted receipt."""
    fixtures, receipt_path = Path(fixtures).resolve(strict=True), Path(receipt_path).resolve(strict=True)
    _, artifacts = completed_receipt(receipt_path, FIXTURE_RECEIPT_SHA256)
    require(fixtures == receipt_path.parent / "output" / "fixtures", "unexpected fixture producer path")
    result = {name: bound_artifact(fixtures / name, artifacts) for name in selected_fixture_names()}
    require(result["cache-0.bin"]["bytes"] == 268435456, "cache0 is not the retained 256 MiB image")
    cache = load_json(fixtures / "cache-0-metadata.json")
    require(cache.get("cache_id") == 0 and cache.get("cache_bytes") == 268435456 and
            cache.get("prepared_programs") == 8 and cache.get("reciprocal_count") == 239 and
            cache.get("prepared_replay_identity_checked") is True, "wrong retained cache descriptor")
    records = (fixtures / "cases.hex").read_text().splitlines()
    require(len(records) >= 2, "missing retained case descriptors")
    for case, item in ((0, 0), (1, 10000000)):
        meta = load_json(fixtures / f"case-{case:03d}/metadata.json")
        require(meta.get("case_id") == case and meta.get("cache_id") == 0 and
                meta.get("item_hex") == f"{item:016x}" and meta.get("retired") == 3563 and
                meta.get("muls") == 1254 and meta.get("full_native_final_agrees") is True and
                meta.get("singleton_full_stage_agrees") is True, "wrong retained native case identity")
        fields = records[case].split()
        require(len(fields) == 7 and int(fields[0]) == case and int(fields[1]) == 0 and
                int(fields[2], 16) == item and int(fields[3], 16) == 239,
                "retained case descriptor disagrees with metadata")
        require(fields[6].lower() == (fixtures / f"case-{case:03d}/final.hex").read_text().strip().lower(),
                "retained final item differs from descriptor")
        counts = int(fields[4], 16)
        require(sum((counts >> (10 * stage)) & 1023 for stage in range(8)) == 3563,
                "retained program counts are incomplete")
    for stage in range(8):
        for stem in ("program", "rcp-valid", "rcp-index", "reciprocals"):
            require(result[f"case-000/{stem}-{stage}.mem"] == result[f"case-001/{stem}-{stage}.mem"],
                    "native pair does not share one immutable prepared image")
    return result


def channel_counters(data, name, batch_cycles=None):
    require(type(data) is dict, f"{name} counters missing")
    accepted = vector(data["accepted"], 2, name + ".accepted")
    delivered = vector(data["delivered"], 2, name + ".delivered")
    waits = vector(data["arbitration_wait_cycles"], 2, name + ".waits")
    for key in ("backend_requests", "backend_responses", "cancelled_responses",
                "orphan_responses", "occupied_cycles", "high_water"):
        integer(data[key], name + "." + key)
    require(sum(accepted) == data["backend_requests"] == sum(delivered) + data["cancelled_responses"],
            name + " lost, refunded or incomplete request ownership")
    require(data["backend_responses"] == sum(delivered) + data["cancelled_responses"] + data["orphan_responses"],
            name + " response/drop ledger does not close")
    require(all(a >= d for a, d in zip(accepted, delivered)), name + " cross-client response count")
    require(data["high_water"] == (1 if sum(accepted) else 0), name + " queue high-water mismatch")
    require(data["backend_requests"] <= data["occupied_cycles"], name + " requests exceed occupied single-credit clocks")
    if batch_cycles is not None:
        require(data["occupied_cycles"] <= batch_cycles and max(waits) <= batch_cycles,
                name + " nested channel clocks exceed batch elapsed clocks")


def validate_protocol(data):
    require(type(data) is dict and data.get("schema") == PROTOCOL_SCHEMA and data.get("status") == "pass",
            "protocol result is incomplete or unrecognized")
    minimums = {"fairness_pairs": 8, "identical_tag_pairs": 8, "early_reply_hold_cycles": 3,
                "same_edge_request_response_cases": 2, "queued_cancel_cases": 1,
                "issued_cancel_cases": 1, "held_cancel_cases": 1, "foreign_owner_packets": 2,
                "wrong_low_tag_packets": 1, "idle_orphan_packets": 1,
                "malformed_payload_forwarded": 1, "other_client_progress_cases": 1,
                "nonowner_cancel_cases": 1, "quiescent_reset_cases": 1,
                "descriptor_hold_cycles": 3, "response_hold_cycles": 3,
                "checks": 1, "cycles": 1, "counter_closure_checks": 1}
    for name, minimum in minimums.items():
        integer(data[name], name, minimum)
    require(data.get("counter_snapshot_scope") == "before_final_quiescent_reset", "wrong protocol reset/counter domain")
    channel = {"accepted": data["accepted_count"], "delivered": data["delivered_count"],
               "arbitration_wait_cycles": data["arbitration_wait_cycles"],
               "backend_requests": data["backend_request_count"],
               "backend_responses": data["backend_response_count"],
               "cancelled_responses": data["cancelled_response_count"],
               "orphan_responses": data["orphan_response_count"],
               "occupied_cycles": data["occupied_cycles"], "high_water": data["high_water_mark"]}
    channel_counters(channel, "protocol", data["cycles"])
    require(channel["cancelled_responses"] >= 3 and channel["orphan_responses"] >= 4,
            "protocol did not actually exercise cancel/orphan traffic")
    return data


def validate_native(data, profile):
    require(profile in PROFILES and type(data) is dict and data.get("schema") == NATIVE_SCHEMA and
            data.get("status") == "pass" and data.get("profile") == profile, "native profile identity mismatch")
    stalled = profile.endswith("-stalled") or profile in ("cancel0", "cancel1", "malformed-fetch0")
    require(data.get("mode_serial") is profile.startswith("serial-") and
            data.get("mode_stalled") is stalled, "native service scenario mislabeled")
    vector(data["fixture_cases"], 2, "fixture cases")
    vector(data["fixture_item_numbers"], 2, "fixture item numbers")
    require(data.get("fixture_cases") == [0, 1] and data.get("fixture_item_numbers") == [0, 10000000],
            "case IDs were confused with native item numbers")
    require(data.get("quiescent_hard_reset_checked") is True, "genuine quiescent reset was not checked")
    require(data.get("counters_before_final_quiescent_reset") is True,
            "native result mixes post-reset and pre-reset counters")
    for name in ("successful_items", "error_items", "aborted_items", "returned_items", "commits", "multiplies", "stages"):
        integer(data[name], name)
    elapsed = integer(data["batch_elapsed_cycles"], "batch_elapsed_cycles", 1)
    for name in ("sessions_used", "client_availability_cycles", "client_core_cycles",
                 "client_executor_cycles", "client_held_backpressure_cycles"):
        vector(data[name], 2, name)
    require(max(data["client_availability_cycles"]) <= elapsed, "nested client availability was added to batch time")
    require(type(data["identity_collision_checks"]) is dict and
            all(type(value) is bool for value in data["identity_collision_checks"].values()) and
            set(data["identity_collision_checks"]) == {"fetch", "cache"}, "missing measured collision coverage")
    baseline = profile in PROFILES[:4]
    expected = (2, 0, 0, [1, 1]) if baseline else (
        (2, 0, 1, [2, 1] if profile == "cancel0" else [1, 2]) if profile in ("cancel0", "cancel1") else
        ((1, 1, 0, [1, 1]) if profile == "malformed-fetch0" else (6, 0, 0, [3, 3])))
    require((data["successful_items"], data["error_items"], data["aborted_items"], data["sessions_used"]) == expected,
            "native profile is partial or refunded a session namespace")
    require(data["returned_items"] == data["successful_items"] + data["error_items"], "returned-item count mismatch")
    require(data.get("exhaustion_admission_denied") is (profile == "exhaustion"), "exhaustion admission result missing")
    if profile in ("cancel0", "cancel1"):
        require(data.get("cancelled_identity_retained") is True, "cancelled identity was not retained")
    if baseline or profile == "exhaustion":
        require(all(data["identity_collision_checks"].values()), "identical full client tags were not observed")
    rows = data["item_rows"]
    require(type(rows) is list and len(rows) == sum(expected[:3]), "native item rows are incomplete")
    totals = Counter()
    available, core, executor = [0, 0], [0, 0], [0, 0]
    namespaces = [[], []]
    for row in rows:
        require(type(row) is dict and type(row.get("client")) is int and row["client"] in (0, 1), "bad item client")
        client = row["client"]
        namespace = integer(row["namespace"], "item namespace", 1)
        namespaces[client].append(namespace)
        require(row.get("status") in ("success", "error", "cancelled"), "unknown item disposition")
        if profile == "malformed-fetch0":
            require(row["status"] == ("error" if client == 0 else "success"),
                    "malformed reply reached the wrong native client")
        elif profile in ("cancel0", "cancel1"):
            target = int(profile[-1])
            require(row["status"] == ("cancelled" if client == target and namespace == 1 else "success"),
                    "cancelled ownership was attributed to the wrong client or session")
        else:
            require(row["status"] == "success", "baseline/exhaustion contains a non-successful item")
        totals[row["status"]] += 1
        for name in ("commits", "multiplies", "stages"):
            integer(row[name], "item." + name)
            totals[name] += row[name]
        if row["status"] == "success":
            require((row["commits"], row["multiplies"], row["stages"]) == (3563, 1254, 8), "incomplete native success")
        elif row["status"] == "error":
            require((row["commits"], row["multiplies"], row["stages"]) == (0, 0, 0), "owned first-fetch fault did unexpected work")
        else:
            require(0 < row["commits"] < 3563 and row["multiplies"] <= 1254 and row["stages"] < 8,
                    "cancellation was not a partial native prefix")
        if row["status"] != "cancelled":
            latency = integer(row["availability_cycles"], "availability", 1)
            child = integer(row["core_cycles"], "core cycles")
            execute = integer(row["executor_cycles"], "executor cycles")
            require(child + 1 == latency and execute <= child, "native session/core/executor clock domains mixed")
            if row["status"] == "success":
                require(execute >= 3 * 3563 + 34 * 1254, "native superscalar work has impossible modeled latency")
            available[client] += latency
            core[client] += child
            executor[client] += execute
        else:
            require("availability_cycles" not in row, "cancelled prefix was promoted to completed availability")
            latency = integer(row["partial_elapsed_cycles"], "cancelled partial elapsed", 1)
        require(sum(vector(row["session_phase_cycles"], 3, "session phases")) == latency and
                sum(vector(row["item_phase_cycles"], 9, "item phases")) == latency,
                "native per-item phase vectors do not close in their declared domain")
    require([len(x) for x in namespaces] == expected[3] and
            all(sorted(values) == list(range(1, len(values) + 1)) for values in namespaces),
            "session identities were duplicated, skipped or recycled")
    require((totals["success"], totals["error"], totals["cancelled"]) == expected[:3], "item-row dispositions differ")
    require(all(totals[name] == data[name] for name in ("commits", "multiplies", "stages")), "native work ledger mismatch")
    require((available, core, executor) == (data["client_availability_cycles"], data["client_core_cycles"],
                                           data["client_executor_cycles"]), "aggregate nested client clocks do not close")
    returned_by_client = [sum(row["client"] == client and row["status"] != "cancelled" for row in rows)
                          for client in (0, 1)]
    require(all(count <= held <= elapsed for count, held in
                zip(returned_by_client, data["client_held_backpressure_cycles"])),
            "native held-result backpressure was not actually observed")
    for name in ("fetch", "cache"):
        channel_counters(data[name], name, elapsed)
    if baseline:
        require((data["commits"], data["multiplies"], data["stages"]) == (7126, 2508, 16), "native pair is incomplete")
        for name, count in (("fetch", 3563), ("cache", 8)):
            require(data[name]["accepted"] == data[name]["delivered"] == [count, count] and
                    data[name]["cancelled_responses"] == data[name]["orphan_responses"] == 0,
                    "baseline native pair has missing or extraneous service traffic")
    return data


def require_admission(output, source, phase):
    """Refuse direct payload launch outside this exact named runner cgroup."""
    output, source = Path(output).absolute(), Path(source).resolve(strict=True)
    require(source == ROOT, "driver must operate on its own bound source tree")
    require(not output.is_relative_to(source), "output must not modify bound source")
    manifest_path = output.parent / "manifest.json"
    manifest = load_json(manifest_path)
    require(manifest.get("schema") == "openrx.local.execution.v1" and
            manifest.get("migration_state") == "LOCAL_ACTIVE", "active local execution manifest required")
    require(manifest.get("cwd") == str(source), "admitted cwd differs from source")
    argv = manifest.get("argv", [])
    require(str(Path(__file__).resolve()) in argv and str(output) in argv and phase in argv,
            "driver phase/output absent from admitted argv")
    position = argv.index(str(Path(__file__).resolve()))
    require(argv[position + 1:] == sys.argv[1:], "live argv differs from admitted request")
    require(str(Path(argv[0]).resolve()) == str(Path(sys.executable).resolve()), "different admitted Python executable")
    require(sys.dont_write_bytecode, "run admitted driver with Python -B")
    unit = manifest.get("unit")
    memberships = Path("/proc/self/cgroup").read_text().splitlines()
    require(type(unit) is str and any(unit in line.split(":", 2)[-1].split("/") for line in memberships),
            "driver is outside its exact admitted service cgroup")
    return manifest


def cgroup_observation():
    result = {"scope": "cumulative observed admitted cgroup; not per-command RSS or physical performance"}
    try:
        membership = next(line.split(":", 2)[2] for line in Path("/proc/self/cgroup").read_text().splitlines()
                          if line.startswith("0::"))
        directory = Path("/sys/fs/cgroup") / membership.lstrip("/")
        result["membership"] = membership
        result["files"] = {}
        for name in ("memory.peak", "memory.current", "memory.swap.peak", "memory.swap.current", "cpu.stat", "pids.current"):
            try:
                result["files"][name] = (directory / name).read_text().strip()
            except OSError as exc:
                result["files"][name] = {"unavailable": type(exc).__name__}
    except (OSError, StopIteration) as exc:
        result["unavailable"] = type(exc).__name__
    return result


class Commands:
    def __init__(self, output, source, tools):
        self.output, self.source, self.tools = output, source, tools
        self.rows, self.lock = [], threading.Lock()
        (output / "commands").mkdir()

    def run(self, label, argv, allow_nonzero=False):
        require(re.fullmatch(r"[a-z0-9-]+", label) is not None, "unsafe command label")
        directory = self.output / "commands"
        row = {"label": label, "argv": [str(x) for x in argv], "cwd": str(self.source),
               "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
               "cleanup_scope": "GNU timeout owned group; immutable admitted runner cgroup is outer containment"}
        save_new(directory / (label + ".started.json"), row)
        wrapped = [self.tools["time"]["path"], "-v", "-o", str(directory / (label + ".time.txt")),
                   self.tools["timeout"]["path"], "--signal=KILL", str(COMMAND_TIMEOUT_SECONDS) + "s", *row["argv"]]
        began = time.monotonic()
        try:
            with (directory / (label + ".stdout")).open("x") as stdout, (directory / (label + ".stderr")).open("x") as stderr:
                result = subprocess.run(wrapped, cwd=self.source,
                                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                                        stdout=stdout, stderr=stderr,
                                        timeout=COMMAND_TIMEOUT_SECONDS + 5)
            row["returncode"] = result.returncode
            row["timeout_or_signal_exit"] = result.returncode in (124, 137, -9)
        except Exception as exc:
            row["returncode"] = None
            row["error"] = type(exc).__name__ + ": " + str(exc)
            row["supervisor_timeout"] = isinstance(exc, subprocess.TimeoutExpired)
            raise
        finally:
            row["wall_seconds"] = time.monotonic() - began
            row["cgroup_observation"] = cgroup_observation()
            save_new(directory / (label + ".finished.json"), row)
            with self.lock:
                self.rows.append(row)
            print(json.dumps({key: row.get(key) for key in ("label", "returncode", "wall_seconds", "timeout_or_signal_exit")}), flush=True)
        require(allow_nonzero or row["returncode"] == 0, f"{label} failed; original outputs retained")
        return row


def tool_bindings(args):
    values = {name: {"path": str(Path(getattr(args, name)).resolve(strict=True)),
                     **binding(Path(getattr(args, name)).resolve(strict=True))}
              for name in ("iverilog", "vvp", "yosys", "time", "timeout")}
    values["python"] = {"path": str(Path(sys.executable).resolve()), **binding(Path(sys.executable).resolve())}
    values["ivl_runtime"] = {"path": str(args.ivl_runtime.resolve(strict=True)),
                             "files": fingerprint(args.ivl_runtime.resolve(strict=True))}
    require({"ivl", "ivlpp", "vvp.tgt", "vvp.conf", "system.vpi"} <=
            set(values["ivl_runtime"]["files"]), "incomplete selected Icarus helper runtime")
    return values


def validate_reuse(args, sources, fixtures, tools):
    prior = args.reuse_execution.resolve(strict=True)
    receipt_path = prior / "receipt.json"
    receipt, artifacts = completed_receipt(receipt_path, args.reuse_receipt_sha256)
    require(sha(args.reuse_verify) == args.reuse_verify_sha256, "actual root verification proof differs from binding")
    proof = load_json(args.reuse_verify)
    require(proof.get("execution_id") == receipt["execution_id"] and proof.get("integrity_verified") is True and
            proof.get("status") == "PROCESS_EXITED", "root verification proof does not accept this receipt")
    bound_artifact(prior / "manifest.json", artifacts)
    manifest = load_json(prior / "manifest.json")
    require(manifest.get("schema") == "openrx.local.execution.v1" and
            manifest.get("migration_state") == "LOCAL_ACTIVE" and
            manifest.get("execution_id") == receipt["execution_id"] and manifest.get("cwd") == str(ROOT),
            "prior source execution differs")
    argv = manifest.get("argv", [])
    driver = str(ROOT / "scripts/test_dataset_shared.py")
    require(type(argv) is list and driver in argv and argv[:argv.index(driver)] == [tools["python"]["path"], "-B"],
            "prior manifest did not run this exact bound Python driver")
    require(manifest.get("executable") == tools["python"], "prior Python executable binding differs")

    def prior_option(name):
        require(argv.count(name) == 1 and argv.index(name) + 1 < len(argv), "prior argv missing or duplicated " + name)
        return argv[argv.index(name) + 1]

    require(prior_option("--phase") == "prefix" and prior_option("--source") == str(ROOT) and
            prior_option("--output") == str(prior / "output") and
            Path(prior_option("--fixtures")).resolve() == args.fixtures.resolve() and
            Path(prior_option("--fixture-receipt")).resolve() == args.fixture_receipt.resolve(),
            "prior actual runner argv was not the same source/input measured prefix")
    bound_artifact(prior / "output" / "summary.json", artifacts)
    summary = load_json(prior / "output" / "summary.json")
    require(summary.get("schema") == SUMMARY_SCHEMA and summary.get("phase") == "prefix" and
            summary.get("status") == "pass_prefix", "reuse requires a completed measured prefix")
    require(summary.get("source_before") == summary.get("source_after") == sources and
            summary.get("fixture_before") == summary.get("fixture_after") == fixtures and
            summary.get("tools_before") == summary.get("tools_after") == tools,
            "prior source, fixture or tool bytes differ from this request")
    require(summary.get("source_unchanged") is True and summary.get("fixtures_unchanged") is True,
            "prior source/input preservation failed")
    # The receipt binds actual binaries/results; embedded summary claims alone
    # never authorize reuse of edited or substituted objects.
    for relative in ("protocol.vvp", "native.vvp", "protocol.json", "native-concurrent-ideal.json"):
        bound_artifact(prior / "output" / relative, artifacts)
    protocol = validate_protocol(load_json(prior / "output" / "protocol.json"))
    native = validate_native(load_json(prior / "output" / "native-concurrent-ideal.json"), "concurrent-ideal")
    require(summary.get("protocol") == protocol and summary.get("native", {}).get("concurrent-ideal") == native,
            "prior completed prefix result differs from its bound summary")
    source_bindings = manifest.get("sources", [])
    directory_rows = [x for x in source_bindings if x.get("path") == str(ROOT) and x.get("kind") == "directory"]
    require(len(directory_rows) == 1, "prior actual runner source-directory binding missing")
    require({x["relative"]: {"bytes": x["bytes"], "sha256": x["sha256"]}
             for x in directory_rows[0]["files"]} == sources, "actual runner source binding differs")
    return prior, summary


def compile_bench(commands, tools, source, output, label, top, sources, defines=()):
    executable = output / (label + ".vvp")
    argv = [tools["iverilog"]["path"], "-B", tools["ivl_runtime"]["path"],
            "-g2012", "-s", top, "-o", str(executable)]
    argv += ["-D" + name for name in defines]
    argv += [str(path if Path(path).is_absolute() else source / path) for path in sources]
    commands.run("compile-" + label, argv)
    require(executable.is_file(), "compiler did not produce executable")
    return executable


def run_native(commands, tools, executable, fixtures, output, profile, label=None):
    label = label or "native-" + profile
    result = output / (label + ".json")
    commands.run(label, [tools["vvp"]["path"], "-M" + tools["ivl_runtime"]["path"], str(executable), "+fixtures=" + str(fixtures),
                         "+profile=" + profile, "+output=" + str(result)])
    return validate_native(load_json(result), profile)


def synthesize(commands, tools, source, output, top, label, abc):
    netlist, design = output / (label + ".v"), output / (label + ".json")
    # Yosys receives a fixed non-shell script. The driver only admits paths with
    # no whitespace/metacharacters into this tool-specific command language.
    paths = [str(source / name) for name in FABRIC_RTL] + [str(netlist), str(design), str(abc)]
    require(all(re.fullmatch(r"[A-Za-z0-9_./-]+", name) for name in paths), "unsupported Yosys path characters")
    script = "read_verilog " + " ".join(paths[:2]) + "; "
    script += f"synth -top {top} -flatten -noabc; abc -exe {abc} -g simple; clean; check -assert; "
    script += f"write_verilog -noattr {netlist}; write_json {design}"
    commands.run("synth-" + label, [tools["yosys"]["path"], "-p", script])
    module = load_json(design, maximum=16 * 1024 * 1024)["modules"][top]
    kinds = Counter(cell["type"] for cell in module["cells"].values())
    require(not any("LATCH" in kind.upper() for kind in kinds), "mapped fabric inferred a latch")
    require(sum(kinds.values()) > 0, "empty fabric synthesis result")
    return netlist, {"top": top, "generic_cells": sum(kinds.values()),
                     "flop_cells": sum(count for kind, count in kinds.items() if "DFF" in kind.upper()),
                     "latch_cells": 0, "cells_by_type": dict(sorted(kinds.items())),
                     "scope": "new fabric control only; accepted arithmetic was not synthesized",
                     "physical_ppa_or_frequency_accepted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("prefix", "matrix", "synthesis"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--fixture-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--reuse-execution", type=Path)
    parser.add_argument("--reuse-receipt-sha256")
    parser.add_argument("--reuse-verify", type=Path)
    parser.add_argument("--reuse-verify-sha256")
    for name in ("iverilog", "vvp", "yosys", "time", "timeout"):
        parser.add_argument("--" + name, default="/usr/bin/" + name)
    parser.add_argument("--yosys-simcells", type=Path, default=Path("/usr/share/yosys/simcells.v"))
    parser.add_argument("--ivl-runtime", type=Path, default=Path("/usr/lib/x86_64-linux-gnu/ivl"))
    parser.add_argument("--yosys-data", type=Path, default=Path("/usr/share/yosys"))
    parser.add_argument("--abc", type=Path, default=Path("/usr/bin/berkeley-abc"))
    args = parser.parse_args()
    if not 1 <= args.workers <= 6:
        parser.error("workers must be1..6")
    reuse = (args.reuse_execution, args.reuse_receipt_sha256, args.reuse_verify, args.reuse_verify_sha256)
    if (args.phase != "prefix") != all(bool(x) for x in reuse) or (any(reuse) and not all(reuse)):
        parser.error("matrix/synthesis requires all four --reuse-* bindings; prefix forbids them")
    if args.phase == "synthesis" and args.yosys_data.resolve(strict=True) != Path("/usr/share/yosys").resolve(strict=True):
        parser.error("only the known installed /usr/share/yosys data path may be bound for this Yosys packaging")
    source, output, fixtures = args.source.resolve(strict=True), args.output.absolute(), args.fixtures.resolve(strict=True)
    require_admission(output, source, args.phase)
    output.mkdir(exist_ok=False)
    summary = {"schema": SUMMARY_SCHEMA, "phase": args.phase, "status": "running",
               "scientific_acceptance": "unverified_pending_independent_review", "command_timeout_seconds": 120,
               "tool_scope": "bound executables, selected Icarus compiler/VPI helpers and synthesis data; system dynamic libraries are not fully hermetic",
               "workers_requested": args.workers, "native": {}, "mapping": {},
               "new_full_hash_executed": False, "native_reference_or_cache_regenerated": False,
               "physical_frequency_hz": None, "achieved_hashes_per_second": None, "physical_wall_power_w": None,
               "demonstrated_asic_feasibility": False}
    commands = None
    failed = None
    try:
        sources, tools = fingerprint(source), tool_bindings(args)
        fixture = fixture_bindings(fixtures, args.fixture_receipt)
        summary.update(source_before=sources, tools_before=tools, fixture_before=fixture,
                       fixture_receipt_sha256=FIXTURE_RECEIPT_SHA256, cgroup_before=cgroup_observation())
        commands = Commands(output, source, tools)
        for name in ("iverilog", "vvp") + (("yosys",) if args.phase == "synthesis" else ()):
            commands.run("tool-version-" + name, [tools[name]["path"], "-V"], allow_nonzero=True)
        if args.phase == "prefix":
            commands.run("support-units", [tools["python"]["path"], "-B", "-m", "unittest", "discover",
                                           "-s", "tests", "-p", "test_dataset_shared_support.py", "-v"])
            protocol = compile_bench(commands, tools, source, output, "protocol", "tb_dataset_shared_channel",
                                     (*FABRIC_RTL, PROTOCOL_BENCH))
            native = compile_bench(commands, tools, source, output, "native", "tb_dataset_shared_native",
                                   (*ACCEPTED_RTL, *FABRIC_RTL, NATIVE_BENCH))
            protocol_result = output / "protocol.json"
            commands.run("protocol", [tools["vvp"]["path"], "-M" + tools["ivl_runtime"]["path"],
                                      str(protocol), "+output=" + str(protocol_result)])
            summary["protocol"] = validate_protocol(load_json(protocol_result))
            summary["native"]["concurrent-ideal"] = run_native(commands, tools, native, fixtures, output, "concurrent-ideal")
            summary["status"] = "pass_prefix"
            summary["matrix_admission_required"] = True
        else:
            prior, prefix = validate_reuse(args, sources, fixture, tools)
            summary["reuse"] = {"execution": str(prior), "receipt_sha256": args.reuse_receipt_sha256,
                                "root_verify_sha256": args.reuse_verify_sha256,
                                "actual_receipt_source_tool_fixture_and_artifact_bindings_verified": True}
            if args.phase == "matrix":
                summary["native"]["concurrent-ideal"] = prefix["native"]["concurrent-ideal"]
                labels = [profile for profile in PROFILES if profile != "concurrent-ideal"]
                with ThreadPoolExecutor(max_workers=args.workers) as pool:
                    futures = {pool.submit(run_native, commands, tools, prior / "output" / "native.vvp",
                                           fixtures, output, profile): profile for profile in labels}
                    try:
                        for future in as_completed(futures):
                            summary["native"][futures[future]] = future.result()
                    except Exception:
                        for future in futures:
                            future.cancel()
                        raise
                summary["component_pair_comparison"] = {
                    mode: {"serial_batch_cycles": summary["native"]["serial-" + mode]["batch_elapsed_cycles"],
                           "concurrent_batch_cycles": summary["native"]["concurrent-" + mode]["batch_elapsed_cycles"],
                           "scope": "two native component items under identical assumed finite services; not a complete hash"}
                    for mode in ("ideal", "stalled")}
                summary["status"] = "pass_matrix"
            else:
                summary["synthesis_tool_inputs_before"] = {
                    "abc": {"path": str(args.abc.resolve(strict=True)), **binding(args.abc.resolve(strict=True))},
                    "yosys_data": {"path": str(args.yosys_data.resolve(strict=True)),
                                   "files": fingerprint(args.yosys_data.resolve(strict=True))},
                    "simcells": {"path": str(args.yosys_simcells.resolve(strict=True)), **binding(args.yosys_simcells.resolve(strict=True))}}
                channel_netlist, channel_stats = synthesize(commands, tools, source, output,
                    "randomx_dataset_shared_channel", "channel-netlist", args.abc.resolve(strict=True))
                wrapper_netlist, wrapper_stats = synthesize(commands, tools, source, output,
                    "randomx_dataset_shared_fabric", "fabric-netlist", args.abc.resolve(strict=True))
                summary["mapping"] = {"channel": channel_stats, "fabric": wrapper_stats}
                cells = output / "yosys-simcells.v"
                shutil.copyfile(args.yosys_simcells, cells)
                summary["yosys_simcells"] = {"installed": str(args.yosys_simcells.resolve()), **binding(cells)}
                mapped_protocol = compile_bench(commands, tools, source, output, "mapped-protocol", "tb_dataset_shared_channel",
                                                (channel_netlist, cells, PROTOCOL_BENCH), ("SHARED_CHANNEL_NETLIST",))
                result = output / "mapped-protocol.json"
                commands.run("mapped-protocol", [tools["vvp"]["path"], "-M" + tools["ivl_runtime"]["path"],
                                                 str(mapped_protocol), "+output=" + str(result)])
                summary["mapped_protocol"] = validate_protocol(load_json(result))
                require(result.read_bytes() == (prior / "output" / "protocol.json").read_bytes(),
                        "mapped protocol measurements differ from the exact bound RTL prefix")
                mapped_native = compile_bench(commands, tools, source, output, "mapped-native", "tb_dataset_shared_native",
                                              (*ACCEPTED_RTL, wrapper_netlist, cells, NATIVE_BENCH))
                summary["mapped_native"] = run_native(commands, tools, mapped_native, fixtures, output,
                                                      "concurrent-ideal", "mapped-native-concurrent-ideal")
                require((output / "mapped-native-concurrent-ideal.json").read_bytes() ==
                        (prior / "output" / "native-concurrent-ideal.json").read_bytes(),
                        "mapped fabric native-pair measurements differ from bound RTL prefix")
                summary["mapped_parity_byte_exact"] = {"protocol": True, "native_concurrent_ideal": True}
                summary["mapping_scope"] = "fabric/control only; unchanged accepted arithmetic remains RTL"
                summary["status"] = "pass_synthesis"
    except Exception as exc:
        failed = exc
        summary["status"] = "failed"
        summary["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        summary["commands"] = sorted(commands.rows, key=lambda row: row["label"]) if commands else []
        summary["cgroup_after"] = cgroup_observation()
        try:
            summary["source_after"] = fingerprint(source)
            summary["tools_after"] = tool_bindings(args)
            summary["fixture_after"] = fixture_bindings(fixtures, args.fixture_receipt)
            summary["source_unchanged"] = summary.get("source_before") == summary["source_after"]
            summary["fixtures_unchanged"] = summary.get("fixture_before") == summary["fixture_after"]
            require(summary["source_unchanged"] and summary["fixtures_unchanged"] and
                    summary.get("tools_before") == summary["tools_after"], "source/input/tool changed during validation")
            if "synthesis_tool_inputs_before" in summary:
                summary["synthesis_tool_inputs_after"] = {
                    "abc": {"path": str(args.abc.resolve(strict=True)), **binding(args.abc.resolve(strict=True))},
                    "yosys_data": {"path": str(args.yosys_data.resolve(strict=True)),
                                   "files": fingerprint(args.yosys_data.resolve(strict=True))},
                    "simcells": {"path": str(args.yosys_simcells.resolve(strict=True)), **binding(args.yosys_simcells.resolve(strict=True))}}
                require(summary["synthesis_tool_inputs_before"] == summary["synthesis_tool_inputs_after"],
                        "synthesis helper inputs changed during validation")
        except Exception as exc:
            summary["preservation_error"] = type(exc).__name__ + ": " + str(exc)
            summary["status"] = "failed"
            failed = failed or exc
        save_new(output / "summary.json", summary)
        public = {key: summary.get(key) for key in (
            "schema", "phase", "status", "scientific_acceptance", "command_timeout_seconds", "workers_requested", "tool_scope",
            "new_full_hash_executed", "native_reference_or_cache_regenerated", "physical_frequency_hz",
            "achieved_hashes_per_second", "physical_wall_power_w", "demonstrated_asic_feasibility",
            "source_unchanged", "fixtures_unchanged", "fixture_receipt_sha256", "protocol", "native",
            "component_pair_comparison", "mapping", "mapped_protocol", "mapped_native", "mapped_parity_byte_exact", "mapping_scope")
                  if key in summary}
        public["classification"] = "bounded modeled component experiment; independent acceptance remains separate"
        public["commands"] = [{key: row.get(key) for key in ("label", "returncode", "wall_seconds", "timeout_or_signal_exit")}
                              for row in summary["commands"]]
        save_new(output / "public-summary.json", public)
        save_new(output / "artifacts.sha256.json", {str(path.relative_to(output)): binding(path)
                 for path in sorted(output.rglob("*")) if path.is_file()})
    if failed:
        raise failed
    print(json.dumps({"status": summary["status"], "phase": args.phase,
                      "scientific_acceptance": "unverified_pending_independent_review"}), flush=True)


if __name__ == "__main__":
    main()
