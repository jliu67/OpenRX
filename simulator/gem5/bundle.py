#!/usr/bin/env python3
"""Package/validate one pinned simulator; never download or build implicitly."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

GEM5_COMMIT = "c8222cc67a399bfc01e8658dd14b30d5bfd634f9"
BUILD_WORKFLOW = ".github/workflows/gem5-build.yml"
BUILD_TARGET = "build/RISCV/gem5.opt"
BUILD_COMMAND = ["scons", BUILD_TARGET, "-j2", "--limit-ld-memory-usage"]
LINK_MEMORY_SETTING = "-Wl,--no-keep-memory"
BUILD_OPTIONS = b'RUBY=y\nPROTOCOL="MI_example"\nRUBY_PROTOCOL_MI_example=y\nBUILD_ISA=y\nUSE_RISCV_ISA=y\n'
FILES = {"gem5.opt", "build-options.txt", "config.txt", "build-info.txt",
         "source-commit.txt", "environment.txt", "ldd.txt", "toolchain-packages.txt"}
ISA_FLAGS = {"BUILD_ISA": True, "USE_RISCV_ISA": True, "USE_ARM_ISA": False,
             "USE_MIPS_ISA": False, "USE_POWER_ISA": False,
             "USE_SPARC_ISA": False, "USE_X86_ISA": False, "BUILD_GPU": False,
             "USE_KVM": True, "USE_SYSTEMC": True, "USE_MULTIPLE_PROTOCOLS": True,
             "USE_TEST_OBJECTS": False}
CACHE_PREFIX = "gem5-ubuntu24-x86_64-" + GEM5_COMMIT + "-RISCV-opt-v2-limit-ld-memory-"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cache_namespace(toolchain, config):
    return CACHE_PREFIX + sha256(toolchain) + "-" + sha256(config) + "-"


def json_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON field: " + key)
        obj[key] = value
    return obj


def load_json(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=json_object)


def request(run_id, expected_sha256):
    if not re.fullmatch(r"[1-9][0-9]{0,19}", str(run_id)):
        raise ValueError("build run ID must be a positive decimal integer")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("an externally supplied lowercase binary SHA-256 is required")


def workflow_path(path):
    if type(path) is not str:
        return False
    base, separator, ref = path.partition("@")
    return base == BUILD_WORKFLOW and (not separator or bool(ref.strip()))


def check_config(raw):
    values = {}
    for line in raw.splitlines():
        match = re.fullmatch(r"([A-Za-z0-9_]+)=(.*)", line)
        disabled = re.fullmatch(r"# ([A-Za-z0-9_]+) is not set", line)
        if match or disabled:
            name = (match or disabled)[1]
            if name in values:
                raise ValueError("duplicate generated config symbol: " + name)
            values[name] = match[2] if match else "n"
    required = {name: "y" if enabled else "n" for name, enabled in ISA_FLAGS.items()}
    required.update(RUBY="y", RUBY_PROTOCOL_MI_example="y", PROTOCOL='"MI_example"')
    for name, value in required.items():
        if values.get(name) != value:
            raise ValueError("unexpected generated RISCV configuration: " + name)


def check_build_info(raw):
    if "gem5 version 25.1.0.1" not in raw.splitlines():
        raise ValueError("wrong observed simulator version")
    values = {}
    for line in raw.splitlines():
        match = re.fullmatch(r"\s+([A-Za-z0-9_]+) = (.*)", line)
        if match:
            if match[1] in values:
                raise ValueError("duplicate build-info option")
            values[match[1]] = match[2]
    for name, enabled in ISA_FLAGS.items():
        if values.get(name) != str(enabled):
            raise ValueError("wrong observed simulator feature: " + name)
    if values.get("PROTOCOL") != "MI_example":
        raise ValueError("wrong observed Ruby protocol")


def elf_host(path):
    with Path(path).open("rb") as stream:
        header = stream.read(20)
    if (len(header) != 20 or header[:6] != b"\x7fELF\x02\x01"
            or int.from_bytes(header[16:18], "little") not in (2, 3)
            or int.from_bytes(header[18:20], "little") != 62):
        raise ValueError("expected Linux x86-64 executable ELF")


def validate(directory, metadata, repository, run_id, expected_sha256):
    request(run_id, expected_sha256)
    run_id = int(run_id)
    if (not isinstance(metadata, dict) or not isinstance(metadata.get("repository"), dict)
            or metadata.get("id") != run_id
            or type(metadata.get("id")) is not int
            or metadata.get("repository", {}).get("full_name") != repository
            or metadata.get("event") != "workflow_dispatch"
            or not workflow_path(metadata.get("path"))
            or metadata.get("status") != "completed" or metadata.get("conclusion") != "success"
            or type(metadata.get("run_attempt")) is not int or metadata["run_attempt"] <= 0
            or type(metadata.get("head_sha")) is not str
            or not re.fullmatch(r"[0-9a-f]{40}", metadata["head_sha"])):
        raise ValueError("artifact must come from a successful same-repository manual simulator build")
    directory = Path(directory)
    if directory.is_symlink() or {p.name for p in directory.iterdir()} != FILES | {"manifest.json"}:
        raise ValueError("unexpected simulator bundle members")
    for name in FILES | {"manifest.json"}:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("bundle members must be regular files: " + name)
    manifest = load_json(directory / "manifest.json")
    toolchain_sha256 = sha256(directory / "toolchain-packages.txt")
    expected = {"schema_version": 1, "gem5_commit": GEM5_COMMIT, "build_target": BUILD_TARGET,
                "build_command": BUILD_COMMAND, "link_memory_setting": LINK_MEMORY_SETTING,
                "source_clean": True, "repository": repository, "workflow": BUILD_WORKFLOW,
                "run_id": run_id, "run_attempt": metadata.get("run_attempt"),
                "project_commit": metadata.get("head_sha"), "host": "ubuntu-24.04-x86_64",
                "toolchain_sha256": toolchain_sha256,
                "cache_namespace": cache_namespace(directory / "toolchain-packages.txt", directory / "config.txt")}
    if (not isinstance(manifest, dict) or set(manifest) != set(expected) | {"files"}
            or any(manifest.get(key) != value for key, value in expected.items())
            or type(manifest.get("schema_version")) is not int
            or type(manifest.get("run_id")) is not int
            or type(manifest.get("run_attempt")) is not int
            or manifest.get("source_clean") is not True
            or not isinstance(manifest.get("files"), dict) or set(manifest["files"]) != FILES):
        raise ValueError("missing or mismatched pinned simulator provenance")
    for name in FILES:
        if manifest["files"][name] != sha256(directory / name):
            raise ValueError("bundle digest mismatch: " + name)
    if sha256(directory / "gem5.opt") != expected_sha256:
        raise ValueError("simulator binary differs from externally supplied SHA-256")
    if (directory / "build-options.txt").read_bytes() != BUILD_OPTIONS:
        raise ValueError("not the pinned canonical build_opts/RISCV")
    if not (directory / "source-commit.txt").read_text().startswith("commit " + GEM5_COMMIT + "\n"):
        raise ValueError("source commit record mismatch")
    if (not (directory / "environment.txt").read_text().strip()
            or not (directory / "toolchain-packages.txt").read_text().strip()):
        raise ValueError("missing build environment")
    if "not found" in (directory / "ldd.txt").read_text():
        raise ValueError("producer recorded missing shared libraries")
    elf_host(directory / "gem5.opt")
    check_config((directory / "config.txt").read_text())
    check_build_info((directory / "build-info.txt").read_text())
    return {"status": "pass", "binary_sha256": expected_sha256, "gem5_commit": GEM5_COMMIT,
            "build_run_id": run_id, "build_run_attempt": manifest["run_attempt"],
            "project_commit": manifest["project_commit"], "timing_calibrated": False}


def command(args, *, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError("command failed: " + " ".join(args) + "\n" + result.stdout + result.stderr)
    return result.stdout


def pack(source, output, environment, toolchain, selected_namespace):
    source, output = Path(source).resolve(strict=True), Path(output)
    if command(["git", "rev-parse", "HEAD"], cwd=source).strip() != GEM5_COMMIT:
        raise ValueError("wrong source revision")
    if command(["git", "status", "--porcelain"], cwd=source).strip():
        raise ValueError("simulator source must be clean after build")
    if (source / "build_opts/RISCV").read_bytes() != BUILD_OPTIONS:
        raise ValueError("canonical build options changed")
    binary = source / BUILD_TARGET
    elf_host(binary)
    info = command([str(binary), "--build-info"])
    check_build_info(info)
    config = (source / "build/RISCV/gem5.build/config").read_text()
    check_config(config)
    expected_namespace = cache_namespace(toolchain, source / "build/RISCV/gem5.build/config")
    if selected_namespace != expected_namespace:
        raise ValueError("generated configuration/toolchain changed after cache selection")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(binary, output / "gem5.opt")
    shutil.copyfile(environment, output / "environment.txt")
    shutil.copyfile(toolchain, output / "toolchain-packages.txt")
    (output / "build-options.txt").write_bytes(BUILD_OPTIONS)
    (output / "build-info.txt").write_text(info)
    (output / "config.txt").write_text(config)
    (output / "source-commit.txt").write_text(command(["git", "show", "--no-patch", "--format=fuller", "HEAD"], cwd=source))
    (output / "ldd.txt").write_text(command(["ldd", str(binary)]))
    toolchain_sha256 = sha256(output / "toolchain-packages.txt")
    manifest = {"schema_version": 1, "gem5_commit": GEM5_COMMIT, "build_target": BUILD_TARGET,
                "build_command": BUILD_COMMAND, "link_memory_setting": LINK_MEMORY_SETTING,
                "source_clean": True, "repository": os.environ["GITHUB_REPOSITORY"],
                "workflow": BUILD_WORKFLOW, "run_id": int(os.environ["GITHUB_RUN_ID"]),
                "run_attempt": int(os.environ["GITHUB_RUN_ATTEMPT"]),
                "project_commit": os.environ["GITHUB_SHA"], "host": "ubuntu-24.04-x86_64",
                "toolchain_sha256": toolchain_sha256,
                "cache_namespace": expected_namespace,
                "files": {name: sha256(output / name) for name in sorted(FILES)}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"binary_sha256": manifest["files"]["gem5.opt"], "manifest": str(output / "manifest.json")}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    check = commands.add_parser("request")
    for group in [check, commands.add_parser("validate")]:
        group.add_argument("--run-id", required=True)
        group.add_argument("--expected-sha256", required=True)
    verify = commands.choices["validate"]
    verify.add_argument("--bundle", type=Path, required=True)
    verify.add_argument("--run-metadata", type=Path, required=True)
    verify.add_argument("--repository", required=True)
    verify.add_argument("--report", type=Path, required=True)
    create = commands.add_parser("pack")
    create.add_argument("--source", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--environment", type=Path, required=True)
    create.add_argument("--toolchain", type=Path, required=True)
    create.add_argument("--cache-namespace", required=True)
    args = parser.parse_args()
    try:
        if args.operation == "request":
            request(args.run_id, args.expected_sha256)
        elif args.operation == "pack":
            pack(args.source, args.output, args.environment, args.toolchain, args.cache_namespace)
        else:
            verdict = validate(args.bundle, load_json(args.run_metadata), args.repository,
                               args.run_id, args.expected_sha256)
            args.report.write_text(json.dumps(verdict, indent=2) + "\n")
            print(json.dumps(verdict))
        return 0
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        error = {"status": "fail", "error": str(exc), "timing_calibrated": False}
        if args.operation == "validate":
            args.report.write_text(json.dumps(error, indent=2) + "\n")
        print(json.dumps(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
