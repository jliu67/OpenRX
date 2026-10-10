#!/usr/bin/env python3
"""Owner-operated, append-only local execution. No network execution listener.

All jobs use one host lock and user systemd cgroups. Process completion never
certifies scientific correctness. Interrupted experiments are never auto-resumed.
"""
import argparse
from contextlib import contextmanager
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import uuid

STATES = {
    "INVENTORY": {"STAGING", "BLOCKED", "ROLLBACK_REQUIRED"},
    "STAGING": {"LOCAL_VALIDATING", "BLOCKED", "ROLLBACK_REQUIRED"},
    "LOCAL_VALIDATING": {"CUTOVER_PENDING", "BLOCKED", "ROLLBACK_REQUIRED"},
    "CUTOVER_PENDING": {"LOCAL_ACTIVE", "BLOCKED", "ROLLBACK_REQUIRED"},
    "LOCAL_ACTIVE": {"BLOCKED", "ROLLBACK_REQUIRED"},
    "BLOCKED": {"INVENTORY", "STAGING", "LOCAL_VALIDATING", "CUTOVER_PENDING", "ROLLBACK_REQUIRED"},
    "ROLLBACK_REQUIRED": {"INVENTORY", "STAGING", "BLOCKED"},
}
GATES = (
    "original_state_preserved", "dependencies_verified", "essential_artifacts_verified",
    "expected_guest_booted", "correctness_smoke_passed", "session_independence_verified",
    "status_logs_inspectable", "stop_failure_recovery_demonstrated",
    "github_architecture_consistent", "handoffs_consistent", "reviewed_pr_merged",
    "output_integrity_verified", "final_receipt_complete",
)
ENV_ALLOW = {"PATH", "LANG", "LC_ALL", "LD_LIBRARY_PATH", "PYTHONPATH", "CC", "CXX",
             "CFLAGS", "CXXFLAGS", "LDFLAGS", "OMP_NUM_THREADS", "MAKEFLAGS"}
DEFAULT_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
VALIDATION_SCOPES = ("lifecycle", "unit", "vendor-integrity", "guest-runtime-smoke", "regression-smoke")
ID_RE = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{12}$")
RESOURCE_PROFILE = "owner-local-max-v1"
GIB = 1024 ** 3
MEMORY_MARGIN_BYTES = GIB
MEMORY_CAP_BYTES = 14 * GIB
MEMORY_GRANULARITY_BYTES = 256 * 1024 ** 2


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def host_resources(meminfo_path=Path("/proc/meminfo")):
    """Record available RAM; swap is a maximum allowance, never a reservation."""
    values = {}
    required = {"MemTotal", "MemAvailable", "SwapTotal", "SwapFree"}
    for line in Path(meminfo_path).read_text().splitlines():
        match = re.fullmatch(r"(\w+):\s+(\d+) kB", line)
        if match and match[1] in required:
            values[match[1]] = int(match[2]) * 1024
    if set(values) != required or not 0 <= values["MemAvailable"] <= values["MemTotal"] or not 0 <= values["SwapFree"] <= values["SwapTotal"]:
        raise ValueError("Cannot establish actual available host RAM/swap")
    return {"at": now(), "memory_bytes": values, "logical_cpus": os.cpu_count(),
            "allowed_cpus": sorted(os.sched_getaffinity(0))}


def select_resources(profile, memory_bytes=None):
    if profile != RESOURCE_PROFILE:
        raise ValueError("Unsupported local resource profile")
    observed = host_resources()
    ceiling = min(MEMORY_CAP_BYTES, observed["memory_bytes"]["MemAvailable"] - MEMORY_MARGIN_BYTES)
    if memory_bytes is not None:
        if type(memory_bytes) is not int or memory_bytes <= 0 or memory_bytes > ceiling:
            raise ValueError("Requested memory must be positive and fit available RAM plus OS headroom")
        selected = memory_bytes
    else:
        selected = ceiling // MEMORY_GRANULARITY_BYTES * MEMORY_GRANULARITY_BYTES
    if selected <= 0:
        raise ValueError("Insufficient available RAM after necessary OS headroom")
    resources = {"MemoryMax": str(selected), "MemorySwapMax": "2G", "CPUQuota": "600%",
                 "TasksMax": 256, "Nice": 10, "NoNewPrivileges": True, "global_slots": 1}
    metadata = {"name": profile, "admission": observed, "memory_margin_bytes": MEMORY_MARGIN_BYTES,
                "memory_cap_bytes": MEMORY_CAP_BYTES, "default_rounding_bytes": MEMORY_GRANULARITY_BYTES,
                "safe_ceiling_bytes": ceiling, "requested_memory_bytes": memory_bytes,
                "selected_memory_bytes": selected, "allocation_slack_bytes": ceiling - selected,
                "kernel_page_bytes": os.sysconf("SC_PAGE_SIZE"),
                "kernel_memory_max_bytes": selected // os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PAGE_SIZE"),
                "kernel_rounding": "Linux page_counter limits truncate byte requests to whole pages; default 256MiB blocks are page aligned",
                "swap_is_reservation": False,
                "rationale": "All six CPUs available; RAM uses measured safe headroom, rounded down in 256MiB blocks for executor fluctuations. Exact known-workload requests must fit the same ceiling. One resource slot remains."}
    return resources, metadata


def check_resource_headroom(directory, manifest):
    profile = manifest["resource_profile"]
    resources = manifest["resources"]
    if profile["name"] != RESOURCE_PROFILE or resources["MemoryMax"] != str(profile["selected_memory_bytes"]):
        raise ValueError("Bound resource profile is inconsistent")
    observed = host_resources()
    required = profile["selected_memory_bytes"] + profile["memory_margin_bytes"]
    available = observed["memory_bytes"]["MemAvailable"]
    safe = available >= required
    json_new(directory / "prelaunch-resource-check.json", {
        "profile": profile["name"], "observed": observed, "required_available_bytes": required,
        "available_bytes": available, "safe": safe,
        "scope": "Fresh headroom check under the global execution lock; bound limits are not changed"})
    if not safe:
        raise ValueError(f"Available RAM fell below bound budget plus OS headroom: {available} < {required}; no child launched")


def kernel_resources(unit, cgroup_root=Path("/sys/fs/cgroup")):
    """Read this service and every visible ancestor; never use manager properties."""
    group = own_cgroup(unit)
    if group is None:
        # Direct nonproduction worker tests have no named unit. The production
        # private CLI rejects that condition before entering worker().
        return None
    relative = group[0]
    if not relative.startswith("/") or ".." in Path(relative).parts:
        raise ValueError("Unsafe named service cgroup path")
    base = Path(cgroup_root).resolve()
    directory = base / relative.lstrip("/")
    records = []
    names = ("cpu.max", "memory.max", "memory.high", "memory.swap.max", "pids.max",
             "cgroup.controllers", "cgroup.subtree_control", "cpuset.cpus.effective")
    while True:
        files = {}
        for name in names:
            try:
                files[name] = (directory / name).read_text().strip()
            except FileNotFoundError:
                files[name] = None
        records.append({"path": str(directory), "is_root": directory == base, "files": files})
        if directory == base:
            break
        directory = directory.parent
    return {"at": now(), "service_cgroup": relative, "groups": records,
            "worker_allowed_cpus": sorted(os.sched_getaffinity(0))}


def kernel_resource_errors(observed, profile):
    errors = []
    if not observed["groups"]:
        return ["No named service kernel cgroup was observed"]
    memory = profile["kernel_memory_max_bytes"]
    if memory <= 0:
        errors.append("Requested memory is smaller than one kernel page")
    if len(observed["worker_allowed_cpus"]) < 6:
        errors.append("Worker affinity exposes fewer than six CPUs")
    for index, group in enumerate(observed["groups"]):
        values = group["files"]
        path = group["path"]
        cpu = values["cpu.max"]
        if cpu is not None:
            match = re.fullmatch(r"(max|[1-9]\d*) ([1-9]\d*)", cpu)
            if match is None or (index == 0 and (match[1] == "max" or int(match[1]) != 6 * int(match[2]))) or (match[1] != "max" and int(match[1]) < 6 * int(match[2])):
                errors.append(f"Missing, invalid or tighter CPU quota: {path}")
        elif not group["is_root"]:
            errors.append(f"Missing CPU controller limit: {path}")
        for name, expected in (("memory.max", memory), ("memory.high", memory),
                               ("memory.swap.max", 2 * GIB), ("pids.max", 256)):
            value = values[name]
            if value is None:
                if not group["is_root"]:
                    errors.append(f"Missing {name} controller limit: {path}")
                continue
            if not re.fullmatch(r"max|\d+", value):
                errors.append(f"Invalid {name}: {path}")
                continue
            exact = index == 0 and name != "memory.high"
            if (exact and value != str(expected)) or (value != "max" and int(value) < expected):
                errors.append(f"Missing, invalid or tighter {name}: {path}")
        cpus = values["cpuset.cpus.effective"]
        if cpus is not None:
            allowed = set()
            for item in cpus.split(","):
                match = re.fullmatch(r"(\d+)(?:-(\d+))?", item)
                if match is None or int(match[1]) > int(match[2] or match[1]) or int(match[2] or match[1]) > 65535:
                    errors.append(f"Invalid effective CPU set: {path}")
                    break
                allowed.update(range(int(match[1]), int(match[2] or match[1]) + 1))
            if len(allowed & set(observed["worker_allowed_cpus"])) < 6:
                errors.append(f"Effective CPU availability is below six: {path}")
    return errors


def check_kernel_resource_limits(directory, manifest, require_service=False):
    try:
        observed = kernel_resources(manifest["unit"])
        errors = (["Current named production service cgroup is missing"] if require_service else []) if observed is None else kernel_resource_errors(observed, manifest["resource_profile"])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        observed, errors = None, [str(exc)]
    json_new(directory / "prelaunch-kernel-check.json", {
        "observed": observed, "errors": errors, "safe": not errors,
        "production_enforced": observed is not None and not errors,
        "production_required": require_service,
        "scope": "Exact named service limits and visible ancestor constraints before payload; direct nonproduction worker tests have no service cgroup"})
    if errors:
        raise ValueError("Kernel resource admission denied; no child launched: " + "; ".join(errors))


def digest(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError(f"Artifact must be a regular file, not a symlink: {path}")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def identity(path):
    path = Path(path).absolute()
    if path.is_file():
        return digest(path)
    if not path.is_dir() or path.is_symlink():
        raise ValueError(f"Missing regular source/input: {path}")
    items = []
    for candidate in sorted(path.rglob("*")):
        relative = candidate.relative_to(path)
        if ".git" in relative.parts:
            continue
        if candidate.is_symlink():
            raise ValueError(f"Source/input directory contains an unbound symlink: {candidate}")
        if candidate.is_file():
            item = digest(candidate)
            item.pop("path")
            items.append({"relative": str(relative), **item})
    return {"path": str(path), "kind": "directory", "files": items,
            "sha256": hashlib.sha256(encode(items)).hexdigest()}


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def sync_regular_file(path):
    """Flush retained bytes without following links or blocking on special files."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError(f"Cannot durably flush a nonregular artifact: {path}")
        os.fsync(fd)
    finally:
        os.close(fd)


def flush_retained(directory, retained):
    """Persist scientific files and nested directory entries before a receipt."""
    for path in retained:
        sync_regular_file(path)
    directories = {directory, *(path for path in directory.rglob("*") if path.is_dir())}
    for path in sorted(directories, key=lambda path: len(path.parts), reverse=True):
        sync_directory(path)
    # The ID namespace itself must survive after the nested contents are flushed.
    sync_directory(directory.parent)


def notify_finalizer_timeout():
    """Extend only the manager's finalization timeout; never signal readiness."""
    address = os.environ.get("NOTIFY_SOCKET")
    if not address:
        return False
    if address.startswith("@"):
        address = "\0" + address[1:]
    elif not address.startswith("/"):
        raise ValueError("Invalid systemd notification socket address")
    message = b"EXTEND_TIMEOUT_USEC=45000000"
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
        client.settimeout(2)
        client.connect(address)
        if client.send(message) != len(message):
            raise OSError("Incomplete systemd finalizer timeout notification")
    return True


@contextmanager
def finalizer_timeout_extension():
    """Keep receipt hashing/flushing alive without extending the worker stop grace."""
    if not notify_finalizer_timeout():
        yield lambda: None
        return
    stopped = threading.Event()
    errors = []

    def health_check():
        if errors:
            raise OSError("Systemd finalizer timeout extension failed: " + str(errors[0]))

    def heartbeat():
        while not stopped.wait(10):
            try:
                notify_finalizer_timeout()
            except (OSError, ValueError) as exc:
                errors.append(exc)
                stopped.set()

    thread = threading.Thread(target=heartbeat, name="openrx-finalizer-heartbeat", daemon=True)
    thread.start()
    try:
        yield health_check
    finally:
        stopped.set()
        thread.join()
        health_check()


def write_new(path, data):
    """Never replace an existing file, even on an interrupted/retried operation."""
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(path.parent)


def json_new(path, value):
    write_new(path, encode(value))


def read_json(path):
    return json.loads(Path(path).read_text())


@contextmanager
def locked(path, blocking=True):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield fd
    finally:
        os.close(fd)


def events(path):
    path = Path(path)
    if not path.exists():
        return []
    records = [json.loads(line) for line in path.read_text().splitlines()]
    previous = None
    for record in records:
        unsigned = {k: v for k, v in record.items() if k != "sha256"}
        if (record.get("previous_sha256") != previous or
                record.get("sha256") != hashlib.sha256(encode(unsigned)).hexdigest()):
            raise ValueError(f"Broken append-only event chain: {path}")
        previous = record["sha256"]
    return records


def append_event(path, event):
    path = Path(path)
    with locked(path.with_suffix(".lock")):
        previous = events(path)
        record = {"at": now(), **event, "previous_sha256": previous[-1]["sha256"] if previous else None}
        record["sha256"] = hashlib.sha256(encode(record)).hexdigest()
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encode(record))
            stream.flush()
            os.fsync(stream.fileno())
        sync_directory(path.parent)
        return record


def init(root):
    root = Path(root).absolute()
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("Execution root and its parent directories must not be symlinks")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    for name in ("executions", "requests", "locks", "state"):
        child = root / name
        if child.is_symlink():
            raise ValueError(f"Execution directory is a symlink: {child}")
        child.mkdir(mode=0o700, exist_ok=True)
        sync_directory(child)
    # mkdir(parents=True) may have introduced more than one namespace level.
    # Flush existing parents as well; their contents and permissions are untouched.
    for directory in (root, *root.parents):
        sync_directory(directory)
    with locked(root / "locks" / "state.lock"):
        if not events(root / "state" / "events.jsonl"):
            append_event(root / "state" / "events.jsonl", {
                "state": "INVENTORY", "reason": "Owner initialized execution storage; no acceptance inferred",
                "runner": digest(Path(__file__).resolve()), "remote_execution": "unavailable"})
    return root


def current_state(root):
    history = events(Path(root) / "state" / "events.jsonl")
    if not history:
        raise ValueError("Run init first")
    return history[-1]["state"]


def validate_acceptance(path):
    receipt = read_json(path)
    if receipt.get("schema") != "openrx.local.acceptance.v1":
        raise ValueError("LOCAL_ACTIVE requires openrx.local.acceptance.v1 receipt")
    for name in GATES:
        gate = receipt.get("gates", {}).get(name, {})
        if gate.get("passed") is not True or not gate.get("evidence"):
            raise ValueError(f"Acceptance gate incomplete: {name}")
        for item in gate["evidence"]:
            actual = digest(item["path"])
            if actual["sha256"] != item["sha256"]:
                raise ValueError(f"Acceptance evidence digest mismatch: {name}")
    merge = receipt.get("reviewed_merge", {})
    if not re.fullmatch(r"[0-9a-f]{40}", merge.get("commit", "")) or not merge.get("review_url") or not merge.get("pr_url"):
        raise ValueError("Acceptance requires actual reviewed merge commit and review/PR URLs")
    return digest(path)


def transition(root, state, evidence, reason):
    root = Path(root)
    binding = digest(evidence)
    with locked(root / "locks" / "admission.lock"):
        with locked(root / "locks" / "state.lock"):
            previous = current_state(root)
            if state not in STATES.get(previous, set()):
                raise ValueError(f"Invalid transition {previous} -> {state}")
            if state == "LOCAL_ACTIVE":
                validate_acceptance(evidence)
            return append_event(root / "state" / "events.jsonl", {
                "state": state, "from_state": previous, "evidence": binding, "reason": reason,
                "remote_execution": "unavailable"})


def manager_ready():
    status = subprocess.run(["systemctl", "--user", "show-environment"], stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, text=True)
    if status.returncode:
        raise ValueError("User systemd manager unavailable; no execution submitted")
    linger = subprocess.run(["loginctl", "show-user", str(os.getuid()), "-p", "Linger", "--value"],
                            capture_output=True, text=True)
    if linger.returncode or linger.stdout.strip() != "yes":
        raise ValueError("User lingering must be enabled and verified before durable execution")


def execution_dir(root, execution_id):
    if not ID_RE.fullmatch(execution_id):
        raise ValueError("Invalid execution ID")
    path = Path(root) / "executions" / execution_id
    if not path.is_dir() or path.is_symlink():
        raise ValueError("Unknown execution ID")
    return path


def systemd_command(root, directory, manifest):
    python = str(Path(sys.executable).resolve())
    runner = str(directory / "runner.py")
    finalizer = " ".join([python, runner, "--root", str(root), "_finalize", manifest["execution_id"]])
    # systemd property strings use their own escaping, not shell syntax.
    if any(char in finalizer for char in ('"', "'", "\\", "%", "\n")) or any(" " in str(p) for p in (root, directory, python)):
        raise ValueError("systemd runner paths require no whitespace, quotes, percent or backslash")
    resources = manifest["resources"]
    if not re.fullmatch(r"[1-9]\d*", resources["MemoryMax"]) or resources["CPUQuota"] != "600%" or resources["MemorySwapMax"] != "2G":
        raise ValueError("Unsupported or invalid bound resource limits")
    return ["systemd-run", "--user", "--quiet", "--no-block", "--unit", manifest["unit"],
            "--property=MemoryMax=" + resources["MemoryMax"], "--property=CPUQuota=" + resources["CPUQuota"], "--property=TasksMax=256",
            "--property=MemorySwapMax=" + resources["MemorySwapMax"], "--property=Nice=10", "--property=NoNewPrivileges=yes",
            "--property=KillMode=mixed", "--property=KillSignal=SIGINT",
            "--property=TimeoutStopSec=45s", "--property=SendSIGKILL=yes",
            "--property=UMask=0077", "--property=Restart=no",
            "--property=NotifyAccess=exec",
            f"--property=ExecStopPost={finalizer}",
            python, runner, "--root", str(root), "_worker", manifest["execution_id"]]


def submit(root, request_key, kind, cwd, argv, inputs, sources=(), env_items=(), validation_scope=None,
           resource_profile=RESOURCE_PROFILE, memory_bytes=None):
    root = Path(root).absolute()
    if not request_key or len(request_key) > 256 or "\n" in request_key:
        raise ValueError("Request key must be a nonempty single line of at most 256 characters")
    if not argv or not inputs:
        raise ValueError("An argv and at least one bound input are required")
    if kind not in {"validation", "build", "simulation"}:
        raise ValueError("Unknown execution kind")
    if kind == "validation" and validation_scope not in VALIDATION_SCOPES:
        raise ValueError("Pre-cutover validation requires an explicit supported validation scope")
    if kind != "validation" and validation_scope is not None:
        raise ValueError("Validation scope is only applicable to validation requests")
    cwd = Path(cwd).resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError("cwd must be a directory")
    env = dict(DEFAULT_ENV)
    for item in env_items:
        key, sep, value = item.partition("=")
        if not sep or key not in ENV_ALLOW or "\x00" in value:
            raise ValueError(f"Environment key is not explicitly allowed: {key}")
        env[key] = value
    executable = shutil.which(argv[0], path=env["PATH"]) if "/" not in argv[0] else str(cwd / argv[0])
    if not executable:
        raise ValueError("Executable unavailable in declared PATH")
    executable = str(Path(executable).resolve(strict=True))
    argv = [executable, *argv[1:]]
    manager_ready()
    # Hash before admission, then recheck in worker under the resource lock.
    bindings = [identity(path) for path in inputs]
    source_bindings = [identity(path) for path in sources]
    with locked(root / "locks" / "admission.lock"):
        state = current_state(root)
        if state in {"BLOCKED", "ROLLBACK_REQUIRED"} or (kind == "simulation" and state != "LOCAL_ACTIVE"):
            raise ValueError(f"{kind} admission denied in {state}")
        request_path = root / "requests" / (hashlib.sha256(request_key.encode()).hexdigest() + ".json")
        if request_path.exists():
            old = read_json(request_path)
            raise ValueError(f"Request key already claimed by {old['execution_id']}; inspect/recover it, never duplicate")
        resources, profile = select_resources(resource_profile, memory_bytes)
        execution_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12]
        directory = root / "executions" / execution_id
        directory.mkdir(mode=0o700)
        sync_directory(directory.parent)
        argv_template = argv
        argv = [item.replace("{execution_dir}", str(directory)) for item in argv]
        manifest = {
            "schema": "openrx.local.execution.v1", "execution_id": execution_id, "created_at": now(),
            "request_key": request_key, "kind": kind, "migration_state": state,
            "validation_scope": validation_scope,
            "unit": f"openrx-{execution_id}.service", "argv": argv, "cwd": str(cwd), "env": env,
            "argv_template": argv_template,
            "inputs": bindings, "sources": source_bindings, "executable": digest(executable),
            "runner": digest(Path(__file__).resolve()), "scientific_acceptance": "unverified",
            "resources": resources, "resource_profile": profile,
            "resource_lock": str(root / "locks" / "execution.lock"),
            "finalizer_timeout": "Private ExecStopPost extends its own timeout while durable flush/hash work continues; worker stop grace remains 45s",
            "output_rule": "All scientific output must be under {execution_dir}; use this literal argv placeholder",
            "resume": "forbidden; separately reviewed incremental build uses a new ID and request key",
            "remote_execution": "unavailable; owner-mediated local submission only",
        }
        write_new(directory / "runner.py", Path(__file__).resolve().read_bytes())
        json_new(directory / "manifest.json", manifest)
        command = systemd_command(root, directory, manifest)
        json_new(directory / "submission-command.json", {"argv": command})
        json_new(request_path, {"request_key": request_key, "execution_id": execution_id,
                                "manifest": digest(directory / "manifest.json")})
        append_event(directory / "events.jsonl", {"status": "QUEUED", "manifest": digest(directory / "manifest.json")})
        result = subprocess.run(command, capture_output=True, text=True)
        json_new(directory / "submission-result.json", {"returncode": result.returncode,
                 "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            append_event(directory / "events.jsonl", {"status": "SUBMISSION_FAILED", "returncode": result.returncode})
    if result.returncode:
        finalize(root, execution_id, {"SERVICE_RESULT": "submission-failed", "EXIT_STATUS": str(result.returncode)})
        raise ValueError(f"systemd submission failed; preserved execution {execution_id}")
    return execution_id


def check_bindings(root, directory, manifest):
    request_path = Path(root) / "requests" / (hashlib.sha256(manifest["request_key"].encode()).hexdigest() + ".json")
    request = read_json(request_path)
    if request.get("execution_id") != directory.name or request.get("manifest") != digest(directory / "manifest.json"):
        raise ValueError("Execution manifest no longer matches exclusive request binding")
    snapshot = digest(directory / "runner.py")
    if any(snapshot[key] != manifest["runner"][key] for key in ("bytes", "sha256")):
        raise ValueError("Execution runner snapshot identity changed since submission")
    for item in [manifest["executable"], *manifest["inputs"], *manifest["sources"]]:
        actual = identity(item["path"])
        if actual != item:
            raise ValueError(f"Input/source identity changed since submission: {item['path']}")


def own_cgroup(unit):
    """Resolve only this named systemd service, never a shared caller cgroup."""
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            relative = line[3:]
            if relative.endswith("/" + unit):
                return relative, Path("/sys/fs/cgroup") / relative.lstrip("/")
    return None


def drain_cgroup(unit):
    """Keep the resource lock until detached descendants leave the service."""
    group = own_cgroup(unit)
    if group is None:
        # Unit tests call worker directly; production CLI requires its own unit.
        return
    relative, directory = group
    while True:
        others = set()
        for procs in directory.rglob("cgroup.procs"):
            others.update(int(pid) for pid in procs.read_text().split() if int(pid) != os.getpid())
        if not others:
            return
        for pid in others:
            try:
                # pidfd binds the process identity even if the numerical PID is reused.
                fd = os.pidfd_open(pid)
                try:
                    membership = Path(f"/proc/{pid}/cgroup").read_text()
                    if any(line == "0::" + relative or line.startswith("0::" + relative + "/")
                           for line in membership.splitlines()):
                        signal.pidfd_send_signal(fd, signal.SIGKILL)
                finally:
                    os.close(fd)
            except ProcessLookupError:
                pass
            except FileNotFoundError:
                pass
        time.sleep(0.05)


def wait_previous_cgroups(root, manifest, interrupted):
    """Cover a killed worker's lock-release/manager-cleanup gap before launch."""
    group = own_cgroup(manifest["unit"])
    if group is None:
        return
    parent = group[1].parent
    while True:
        occupied = False
        for directory in (Path(root) / "executions").iterdir():
            if not directory.is_dir() or directory.name == manifest["execution_id"]:
                continue
            history = events(directory / "events.jsonl")
            if not any(item.get("status") == "RUNNING" for item in history):
                continue  # queued workers have never launched an expensive child
            other = read_json(directory / "manifest.json")
            candidate = parent / other["unit"]
            if candidate.is_dir() and any(path.read_text().strip() for path in candidate.rglob("cgroup.procs")):
                occupied = True
                break
        if not occupied:
            return
        if interrupted:
            raise InterruptedError("Stopped while prior service cgroup was draining")
        time.sleep(0.1)


def worker(root, execution_id, require_service=False):
    directory = execution_dir(root, execution_id)
    manifest = read_json(directory / "manifest.json")
    process = None
    interrupted = []
    old_handlers = {}

    def handle(signum, _frame):
        # Never reenter Popen's poll/wait while it is updating reaping state.
        # The main loop alone owns child signaling and reaping.
        interrupted.append(signum)

    for sig in (signal.SIGINT, signal.SIGTERM):
        old_handlers[sig] = signal.signal(sig, handle)
    try:
        # Nonblocking poll allows stop of a queued worker without taking its slot.
        lockfd = os.open(Path(root) / "locks" / "execution.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            while True:
                if interrupted:
                    raise InterruptedError("Stopped before resource admission")
                try:
                    fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    time.sleep(0.1)
            wait_previous_cgroups(root, manifest, interrupted)
            check_bindings(root, directory, manifest)
            state = current_state(root)
            if state in {"BLOCKED", "ROLLBACK_REQUIRED"} or (manifest["kind"] == "simulation" and state != "LOCAL_ACTIVE"):
                raise ValueError(f"Execution admission revoked: {state}")
            if interrupted:
                raise InterruptedError("Stopped before launch")
            check_resource_headroom(directory, manifest)
            check_kernel_resource_limits(directory, manifest, require_service)
            append_event(directory / "events.jsonl", {"status": "RUNNING", "pid": os.getpid(), "migration_state": state})
            stdout = os.open(directory / "stdout.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            stderr = os.open(directory / "stderr.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(stdout, "wb") as out, os.fdopen(stderr, "wb") as err:
                process = subprocess.Popen(manifest["argv"], cwd=manifest["cwd"], env=manifest["env"],
                                           stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True)
                append_event(directory / "events.jsonl", {"status": "CHILD_STARTED", "pid": process.pid})
                stop_started = None
                while process.poll() is None:
                    if interrupted:
                        if stop_started is None:
                            stop_started = time.monotonic()
                            try:
                                os.killpg(process.pid, interrupted[0])
                            except ProcessLookupError:
                                pass
                        elif time.monotonic() - stop_started > 25:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                    time.sleep(0.1)
                returncode = process.wait()
                out.flush()
                err.flush()
                os.fsync(out.fileno())
                os.fsync(err.fileno())
            status = "INTERRUPTED" if interrupted else ("PROCESS_EXITED" if returncode == 0 else "PROCESS_FAILED")
            json_new(directory / "process-result.json", {"status": status, "returncode": returncode,
                     "signals": interrupted, "finished_at": now(), "scientific_acceptance": "unverified"})
            append_event(directory / "events.jsonl", {"status": status, "returncode": returncode, "signals": interrupted})
            return 130 if interrupted else (0 if returncode == 0 else 1)
        finally:
            if process is not None:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                drain_cgroup(manifest["unit"])
            os.close(lockfd)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        status = "INTERRUPTED" if interrupted else "ADMISSION_FAILED"
        json_new(directory / "process-result.json", {"status": status, "error": str(exc),
                 "signals": interrupted, "finished_at": now(), "scientific_acceptance": "unverified"})
        append_event(directory / "events.jsonl", {"status": status, "error": str(exc), "signals": interrupted})
        return 130 if interrupted else 1
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)


def unit_status(unit):
    result = subprocess.run(["systemctl", "--user", "show", unit,
                             "--property=LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,ControlGroup,MemoryPeak"],
                            capture_output=True, text=True)
    return {"query_returncode": result.returncode,
            **dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)}


def finalized_files(directory):
    ignored = {directory / name for name in ("receipt.json", "events.lock", "finalize.lock")}
    retained = []
    for path in sorted(directory.rglob("*")):
        # rglob does not descend through directory links; accepting them would
        # silently omit external scientific outputs from the receipt.
        if path.is_symlink():
            raise ValueError(f"Output integrity unsupported: symlink must be preserved and investigated: {path}")
        if path.is_file() and path not in ignored:
            retained.append(path)
        elif not path.is_file() and not path.is_dir():
            raise ValueError(f"Output integrity unsupported: nonregular artifact must be preserved and investigated: {path}")
    return retained


def finalize(root, execution_id, service_env=None, health_check=None):
    directory = execution_dir(root, execution_id)
    # submit holds admission until its durable submission receipt is written.
    # --no-block prevents systemd-run from waiting for this finalizer.
    with locked(Path(root) / "locks" / "admission.lock"), locked(directory / "finalize.lock"):
        if (directory / "receipt.json").exists():
            bindings = [item for item in events(Path(root) / "state" / "execution-receipts.jsonl")
                        if item.get("execution_id") == execution_id]
            actual = digest(directory / "receipt.json")
            if not bindings:
                # Recover a crash between exclusive receipt creation and its journal append.
                verify_artifacts(directory, read_json(directory / "receipt.json"))
                flush_retained(directory, [*finalized_files(directory), directory / "receipt.json"])
                if health_check:
                    health_check()
                append_event(Path(root) / "state" / "execution-receipts.jsonl", {
                    "execution_id": execution_id, "receipt": actual, "recovered_binding": True,
                    "limitation": "Receipt origin was not journal-bound before interruption; retained artifact digests rechecked"})
            elif len(bindings) != 1 or bindings[0]["receipt"] != actual:
                raise ValueError("Existing receipt does not match durable receipt binding")
            return read_json(directory / "receipt.json")
        service_env = service_env if service_env is not None else os.environ
        manager = {key: service_env.get(key) for key in ("SERVICE_RESULT", "EXIT_CODE", "EXIT_STATUS")}
        process_path = directory / "process-result.json"
        process_result = read_json(process_path) if process_path.exists() else None
        status = process_result["status"] if process_result else "INTERRUPTED_UNREAPED"
        if manager["SERVICE_RESULT"] not in {None, "success"} and status == "PROCESS_EXITED":
            status = "SERVICE_FAILED"
        retained = finalized_files(directory)
        flush_retained(directory, retained)
        append_event(directory / "events.jsonl", {"status": "FINALIZED", "process_status": status, "systemd": manager})
        artifacts = [digest(path) for path in retained]
        receipt = {"schema": "openrx.local.receipt.v1", "execution_id": execution_id, "at": now(),
                   "status": status, "systemd": manager, "process": process_result,
                   "artifacts": artifacts, "scientific_acceptance": "unverified",
                   "resume_allowed": False}
        if health_check:
            health_check()
        json_new(directory / "receipt.json", receipt)
        append_event(Path(root) / "state" / "execution-receipts.jsonl", {
            "execution_id": execution_id, "receipt": digest(directory / "receipt.json")})
        return receipt


def verify_artifacts(directory, receipt):
    if (receipt.get("schema") != "openrx.local.receipt.v1" or
            receipt.get("execution_id") != directory.name or
            receipt.get("scientific_acceptance") != "unverified"):
        raise ValueError("Receipt schema/identity/scientific status invalid")
    actual_paths = {str(path.resolve()) for path in finalized_files(directory)}
    if actual_paths != {item["path"] for item in receipt["artifacts"]}:
        raise ValueError("Output integrity mismatch: finalized artifact set changed")
    for artifact in receipt["artifacts"]:
        path = Path(artifact["path"])
        if directory not in path.parents or digest(path) != artifact:
            raise ValueError(f"Output integrity mismatch: {path}")
    events(directory / "events.jsonl")


def verify(root, execution_id):
    directory = execution_dir(root, execution_id)
    receipt = read_json(directory / "receipt.json")
    bindings = [item for item in events(Path(root) / "state" / "execution-receipts.jsonl")
                if item.get("execution_id") == execution_id]
    if len(bindings) != 1 or bindings[0]["receipt"] != digest(directory / "receipt.json"):
        raise ValueError("Receipt integrity mismatch or missing durable receipt binding")
    verify_artifacts(directory, receipt)
    return {"execution_id": execution_id, "integrity_verified": True,
            "scientific_acceptance": receipt["scientific_acceptance"], "status": receipt["status"]}


def status(root, execution_id=None):
    root = Path(root)
    if execution_id is None:
        return {"migration_state": current_state(root), "remote_execution": "unavailable",
                "executions": [p.name for p in sorted((root / "executions").iterdir()) if p.is_dir()]}
    directory = execution_dir(root, execution_id)
    manifest = read_json(directory / "manifest.json")
    history = events(directory / "events.jsonl")
    receipt = read_json(directory / "receipt.json") if (directory / "receipt.json").exists() else None
    return {"execution_id": execution_id, "latest_event": history[-1] if history else None,
            "unit": unit_status(manifest["unit"]), "receipt": receipt,
            "logs": [str(directory / name) for name in ("stdout.log", "stderr.log")]}


def stop(root, execution_id):
    directory = execution_dir(root, execution_id)
    manifest = read_json(directory / "manifest.json")
    if (directory / "receipt.json").exists():
        return {"execution_id": execution_id, "already_finalized": True}
    append_event(directory / "events.jsonl", {"status": "STOP_REQUESTED"})
    result = subprocess.run(["systemctl", "--user", "stop", manifest["unit"]], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"systemd stop failed: {result.stderr.strip()}; preserve and inspect unit")
    return {"execution_id": execution_id, "stop_requested": True, "unit": unit_status(manifest["unit"])}


def recover(root, execution_id):
    directory = execution_dir(root, execution_id)
    manifest = read_json(directory / "manifest.json")
    if (directory / "receipt.json").exists():
        bindings = [item for item in events(Path(root) / "state" / "execution-receipts.jsonl")
                    if item.get("execution_id") == execution_id]
        if not bindings:
            finalize(root, execution_id)
        return verify(root, execution_id)
    state = unit_status(manifest["unit"])
    if state.get("query_returncode") != 0:
        raise ValueError("systemd manager unavailable; cannot establish safe recovery")
    if state.get("ActiveState") not in {"inactive", "failed"}:
        raise ValueError("Unit still active or transitioning; inspect/stop before recovery")
    # systemd owns cgroup termination; never kill a saved PID that may be reused.
    group = state.get("ControlGroup")
    if group:
        cgroup = Path("/sys/fs/cgroup") / group.lstrip("/") / "cgroup.events"
        if cgroup.exists() and "populated 1" in cgroup.read_text():
            raise ValueError("Unit cgroup still populated; stop through systemd before recovery")
    return finalize(root, execution_id, {"SERVICE_RESULT": "recovered-after-interruption",
                                       "EXIT_CODE": state.get("ExecMainCode"), "EXIT_STATUS": state.get("ExecMainStatus")})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    item = commands.add_parser("state")
    item.add_argument("--state", choices=STATES, required=True)
    item.add_argument("--evidence", type=Path, required=True)
    item.add_argument("--reason", required=True)
    item = commands.add_parser("submit")
    item.add_argument("--request-key", required=True)
    item.add_argument("--kind", choices=("validation", "build", "simulation"), required=True)
    item.add_argument("--validation-scope", choices=VALIDATION_SCOPES)
    item.add_argument("--cwd", type=Path, required=True)
    item.add_argument("--input", type=Path, action="append", required=True)
    item.add_argument("--source", type=Path, action="append", default=[])
    item.add_argument("--env", action="append", default=[])
    item.add_argument("--resource-profile", choices=(RESOURCE_PROFILE,), default=RESOURCE_PROFILE)
    item.add_argument("--memory-bytes", type=int, help="Exact known-workload RAM budget; must fit measured available RAM and OS headroom")
    item.add_argument("argv", nargs=argparse.REMAINDER)
    item = commands.add_parser("status")
    item.add_argument("execution_id", nargs="?")
    for name in ("stop", "recover", "verify", "_worker", "_finalize"):
        commands.add_parser(name).add_argument("execution_id")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = {"root": str(init(args.root)), "state": current_state(args.root)}
        elif args.command == "state":
            result = transition(args.root, args.state, args.evidence, args.reason)
        elif args.command == "submit":
            argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            result = {"execution_id": submit(args.root, args.request_key, args.kind, args.cwd,
                      argv, args.input, args.source, args.env, args.validation_scope,
                      args.resource_profile, args.memory_bytes)}
        elif args.command == "_worker":
            manifest = read_json(execution_dir(args.root, args.execution_id) / "manifest.json")
            if own_cgroup(manifest["unit"]) is None:
                raise ValueError("Private worker entrypoint requires its own named systemd cgroup")
            return worker(args.root, args.execution_id, require_service=True)
        elif args.command == "_finalize":
            try:
                with finalizer_timeout_extension() as health_check:
                    result = finalize(args.root, args.execution_id, health_check=health_check)
            except (OSError, ValueError) as exc:
                # An immutable late failure record prevents verify from accepting
                # a receipt if notification failed after that receipt was written.
                directory = execution_dir(args.root, args.execution_id)
                json_new(directory / ("finalizer-timeout-error-" + uuid.uuid4().hex + ".json"), {
                    "at": now(), "error": str(exc), "scientific_acceptance": "unverified",
                    "reason": "Private finalizer failed; preserve all outputs and inspect/recover"})
                raise
        else:
            functions = {"status": status, "stop": stop, "recover": recover, "verify": verify, "_finalize": finalize}
            result = functions[args.command](args.root, args.execution_id)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"local execution: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
