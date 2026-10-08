"""Reject substituted artifacts before executing a downloaded simulator.

The ELF fixture is header-only synthetic data and is never executed. Kconfig
comes from the retained real c8222cc RISCV build; these are offline controls.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from simulator.gem5 import bundle

ROOT = Path(__file__).resolve().parents[1]
REVISION = "c8222cc67a399bfc01e8658dd14b30d5bfd634f9"
PROJECT = "a" * 40
REPOSITORY = "jliu67/OpenRandomX"
CONFIG = (ROOT / "tests/fixtures/gem5-riscv-config.txt").read_text()
BUILD_INFO = """Build information:
gem5 version 25.1.0.1
compiled test-fixture
build options:
    BUILD_ISA = True
    USE_RISCV_ISA = True
    USE_ARM_ISA = False
    USE_MIPS_ISA = False
    USE_POWER_ISA = False
    USE_SPARC_ISA = False
    USE_X86_ISA = False
    BUILD_GPU = False
    USE_KVM = True
    USE_SYSTEMC = True
    USE_MULTIPLE_PROTOCOLS = True
    USE_TEST_OBJECTS = False
    PROTOCOL = MI_example
"""


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "bundle"
        self.directory.mkdir()
        header = bytearray(64)
        header[:6] = b"\x7fELF\x02\x01"
        header[16:18] = (3).to_bytes(2, "little")
        header[18:20] = (62).to_bytes(2, "little")
        (self.directory / "gem5.opt").write_bytes(header)
        data = {"config.txt": CONFIG, "build-info.txt": BUILD_INFO,
                "build-options.txt": 'RUBY=y\nPROTOCOL="MI_example"\nRUBY_PROTOCOL_MI_example=y\nBUILD_ISA=y\nUSE_RISCV_ISA=y\n',
                "source-commit.txt": "commit " + REVISION + "\nAuthor: fixture\n",
                "environment.txt": "offline synthetic provenance fixture\n",
                "toolchain-packages.txt": "gcc-13\t13.3.0\npython3.12\t3.12.3\n",
                "ldd.txt": "libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6\n"}
        for name, contents in data.items():
            (self.directory / name).write_text(contents)
        hashes = {p.name: self.digest(p) for p in self.directory.iterdir()}
        self.expected_binary = hashes["gem5.opt"]
        self.manifest = {"schema_version": 1, "gem5_commit": REVISION,
            "build_target": "build/RISCV/gem5.opt", "source_clean": True,
            "build_command": ["scons", "build/RISCV/gem5.opt", "-j2", "--limit-ld-memory-usage"],
            "link_memory_setting": "-Wl,--no-keep-memory",
            "repository": REPOSITORY, "workflow": ".github/workflows/gem5-build.yml",
            "run_id": 123, "run_attempt": 2, "project_commit": PROJECT,
            "host": "ubuntu-24.04-x86_64", "toolchain_sha256": hashes["toolchain-packages.txt"],
            "cache_namespace": "gem5-ubuntu24-x86_64-" + REVISION + "-RISCV-opt-v2-limit-ld-memory-" + hashes["toolchain-packages.txt"] + "-" + hashes["config.txt"] + "-",
            "files": hashes}
        self.metadata = {"id": 123, "run_attempt": 2, "head_sha": PROJECT,
            "repository": {"full_name": REPOSITORY}, "event": "workflow_dispatch",
            "path": ".github/workflows/gem5-build.yml", "status": "completed", "conclusion": "success"}
        self.write_manifest()

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_manifest(self):
        (self.directory / "manifest.json").write_text(json.dumps(self.manifest))

    def validate(self, metadata=None, expected=None):
        return bundle.validate(self.directory, self.metadata if metadata is None else metadata,
                               REPOSITORY, "123", self.expected_binary if expected is None else expected)

    def change_file(self, name, contents):
        (self.directory / name).write_text(contents)
        self.manifest["files"][name] = self.digest(self.directory / name)
        if name == "config.txt":
            self.manifest["cache_namespace"] = "gem5-ubuntu24-x86_64-" + REVISION + "-RISCV-opt-v2-limit-ld-memory-" + self.manifest["files"]["toolchain-packages.txt"] + "-" + self.manifest["files"]["config.txt"] + "-"
        self.write_manifest()

    def test_valid_offline_fixture_is_consistent(self):
        self.assertEqual(self.validate()["binary_sha256"], self.expected_binary)

    def test_real_prefixless_kconfig_is_supported(self):
        bundle.check_config(CONFIG)
        with self.assertRaises(ValueError):
            bundle.check_config(CONFIG.replace("USE_RISCV_ISA=y", "CONFIG_USE_RISCV_ISA=y"))

    def test_rehashed_substituted_binary_rejected_by_external_anchor(self):
        (self.directory / "gem5.opt").write_bytes((self.directory / "gem5.opt").read_bytes() + b"substitution")
        self.manifest["files"]["gem5.opt"] = self.digest(self.directory / "gem5.opt")
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "externally supplied"):
            self.validate()

    def test_missing_provenance_and_self_consistent_wrong_source(self):
        original = copy.deepcopy(self.manifest)
        for update in [lambda m: m.pop("source_clean"), lambda m: m.update(gem5_commit="b" * 40),
                       lambda m: m.update(build_target="build/ALL/gem5.opt"),
                       lambda m: m.update(build_command=["scons", "build/RISCV/gem5.opt", "-j2"]),
                       lambda m: m.update(link_memory_setting="untracked linker flags"),
                       lambda m: m.update(project_commit="b" * 40), lambda m: m.update(run_attempt=1)]:
            self.manifest = copy.deepcopy(original)
            update(self.manifest)
            self.write_manifest()
            with self.assertRaises(ValueError):
                self.validate()

    def test_other_repo_wrong_workflow_pr_run_and_failed_build_are_rejected(self):
        changes = [{"repository": {"full_name": "other/repo"}}, {"event": "pull_request"},
                   {"path": ".github/workflows/unreviewed.yml"}, {"id": 999},
                   {"conclusion": "failure"}, {"status": "in_progress"}, {"head_sha": None},
                   {"run_attempt": True}, {"repository": []},
                   {"path": ".github/workflows/gem5-build.yml@"},
                   {"path": ".github/workflows/gem5-build.yml-other@main"}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(self.metadata | change)

    def test_github_workflow_path_accepts_documented_ref_suffix(self):
        for path in [".github/workflows/gem5-build.yml", ".github/workflows/gem5-build.yml@main"]:
            self.assertEqual(self.validate(self.metadata | {"path": path})["status"], "pass")

    def test_unauthenticated_metadata_shape_rejected(self):
        for metadata in [[], "metadata", {}, {"id": 123, "repository": None}]:
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                self.validate(metadata)

    def test_duplicate_manifest_json_field_rejected(self):
        path = self.directory / "manifest.json"
        path.write_text(path.read_text().replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'))
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            self.validate()

    def test_binary_missing_provenance_missing_and_extra_members_rejected(self):
        for name in ["gem5.opt", "source-commit.txt"]:
            path = self.directory / name
            contents = path.read_bytes()
            path.unlink()
            with self.assertRaises(ValueError):
                self.validate()
            path.write_bytes(contents)
        (self.directory / "unexpected-script").write_text("exit 0")
        with self.assertRaises(ValueError):
            self.validate()

    def test_symlink_member_rejected(self):
        path = self.directory / "gem5.opt"
        target = Path(self.temporary.name) / "outside"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "regular files"):
            self.validate()

    def test_rehashed_wrong_isa_systemc_or_kvm_config_rejected(self):
        for old, new in [("USE_RISCV_ISA=y", "# USE_RISCV_ISA is not set"),
                         ("# USE_X86_ISA is not set", "USE_X86_ISA=y"),
                         ("USE_SYSTEMC=y", "# USE_SYSTEMC is not set"),
                         ("USE_KVM=y", "# USE_KVM is not set")]:
            self.change_file("config.txt", CONFIG.replace(old, new))
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.validate()

    def test_rehashed_build_options_version_and_runtime_feature_lies_rejected(self):
        self.change_file("build-options.txt", 'BUILD_ISA=y\nUSE_RISCV_ISA=y\n')
        with self.assertRaises(ValueError):
            self.validate()
        self.change_file("build-options.txt", 'RUBY=y\nPROTOCOL="MI_example"\nRUBY_PROTOCOL_MI_example=y\nBUILD_ISA=y\nUSE_RISCV_ISA=y\n')
        for changed in [BUILD_INFO.replace("25.1.0.1", "24.1.0.1"),
                        BUILD_INFO.replace("USE_RISCV_ISA = True", "USE_RISCV_ISA = False")]:
            self.change_file("build-info.txt", changed)
            with self.assertRaises(ValueError):
                self.validate()

    def test_unbound_toolchain_cache_namespace_rejected(self):
        self.manifest["cache_namespace"] = "other-build-namespace"
        self.write_manifest()
        with self.assertRaises(ValueError):
            self.validate()

    def test_checkpoint_namespace_changes_after_config_or_toolchain_drift(self):
        toolchain = self.directory / "toolchain-packages.txt"
        config = self.directory / "config.txt"
        original = bundle.cache_namespace(toolchain, config)
        self.assertEqual(original, self.manifest["cache_namespace"])
        config.write_text(CONFIG + "# drifted configuration\n")
        self.assertNotEqual(bundle.cache_namespace(toolchain, config), original)
        config.write_text(CONFIG)
        toolchain.write_text(toolchain.read_text() + "libc6\tchanged\n")
        self.assertNotEqual(bundle.cache_namespace(toolchain, config), original)

    def test_bad_requests_rejected_before_api_path_or_shell_use(self):
        for run_id in ["0", "../runs/123", "123; echo bad", "$(id)", "01", "1\n"]:
            with self.subTest(run_id=run_id), self.assertRaises(ValueError):
                bundle.request(run_id, self.expected_binary)
        for digest in ["", "a" * 63, "A" * 64, "$(id)"]:
            with self.assertRaises(ValueError):
                bundle.request("123", digest)

    def test_cli_preserves_failed_validation_report(self):
        self.manifest.pop("source_clean")
        self.write_manifest()
        metadata = Path(self.temporary.name) / "run.json"
        metadata.write_text(json.dumps(self.metadata))
        report = Path(self.temporary.name) / "failure.json"
        result = subprocess.run([sys.executable, str(ROOT / "simulator/gem5/bundle.py"), "validate",
            "--bundle", str(self.directory), "--run-metadata", str(metadata), "--repository", REPOSITORY,
            "--run-id", "123", "--expected-sha256", self.expected_binary, "--report", str(report)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(report.read_text())["status"], "fail")


if __name__ == "__main__":
    unittest.main()
