#!/usr/bin/env python3
"""Read-only independent binding audit; never launch the simulator or guest."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile

ROOT = Path("/tmp/openrx-gem5-source")
REVISION = "c8222cc67a399bfc01e8658dd14b30d5bfd634f9"
ARCHIVE = ROOT / "gem5-c8222cc.tar.gz"
ARCHIVE_EXPECTED_SHA256 = "0f4102a3ece810342b0a0124d44f9cb6a5b0aba08b436998b5e5069ab35bdba3"
SOURCE = ROOT / ("gem5-" + REVISION)
BINARY = SOURCE / "build/RISCV/gem5.opt"
IDENTITY = ROOT / "link-recovery-20261008/binary-identity.json"
REPORT = Path(__file__).with_suffix(".json")


def digest(stream):
    result = hashlib.sha256()
    count = 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
        count += len(block)
    return result.hexdigest(), count


def file_digest(path):
    with path.open("rb") as stream:
        return digest(stream)


def signature(path):
    value = path.stat()
    return {"device": value.st_dev, "inode": value.st_ino,
            "size_bytes": value.st_size, "mtime_ns": value.st_mtime_ns,
            "mode": oct(stat.S_IMODE(value.st_mode))}


def main():
    began = datetime.now(timezone.utc).isoformat()
    identity_raw = IDENTITY.read_bytes()
    recorded = json.loads(identity_raw)
    binary_before = signature(BINARY)
    binary_sha256, binary_bytes = file_digest(BINARY)
    binary_after = signature(BINARY)
    archive_before = signature(ARCHIVE)
    archive_sha256, archive_bytes = file_digest(ARCHIVE)
    counts = {"regular_files": 0, "directories": 0, "symbolic_links": 0,
              "hard_links": 0, "other_nondirectories": 0}
    differences = []
    inventory = hashlib.sha256()
    source_bytes = 0
    extraction_root = ROOT.resolve(strict=True)
    with tarfile.open(ARCHIVE, "r:gz") as archive:
        for member in archive:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe archive member: " + member.name)
            if member.isdir():
                counts["directories"] += 1
                continue
            if not member.isfile():
                key = "symbolic_links" if member.issym() else "hard_links" if member.islnk() else "other_nondirectories"
                counts[key] += 1
                differences.append({"path": member.name, "reason": "unexpected nonregular archive entry"})
                continue
            counts["regular_files"] += 1
            source_bytes += member.size
            with archive.extractfile(member) as archived_stream:
                archived_sha256, archived_bytes = digest(archived_stream)
            inventory.update((member.name + "\0" + str(member.size) + "\0" + archived_sha256 + "\n").encode())
            current = ROOT.joinpath(*relative.parts)
            if current.is_symlink() or not current.is_file():
                differences.append({"path": member.name, "reason": "missing or nonregular extracted file"})
                continue
            if not current.resolve(strict=True).is_relative_to(extraction_root):
                differences.append({"path": member.name, "reason": "extracted path leaves extraction root"})
                continue
            before = signature(current)
            current_sha256, current_bytes = file_digest(current)
            after = signature(current)
            if archived_bytes != member.size or current_bytes != member.size or current_sha256 != archived_sha256 or before != after:
                differences.append({"path": member.name, "reason": "content, size or stable-read mismatch",
                                    "archive_sha256": archived_sha256, "extracted_sha256": current_sha256,
                                    "archive_bytes": member.size, "extracted_bytes": current_bytes,
                                    "stable_read": before == after})
    archive_after = signature(ARCHIVE)
    checks = {
        "binary_path_matches_identity": recorded.get("path") == str(BINARY),
        "identity_source_revision_matches_pin": recorded.get("source_revision") == REVISION,
        "binary_sha256_matches_identity": recorded.get("sha256") == binary_sha256,
        "binary_size_matches_identity": recorded.get("size_bytes") == binary_bytes,
        "binary_regular_and_not_symlink": BINARY.is_file() and not BINARY.is_symlink(),
        "binary_stable_read": binary_before == binary_after,
        "archive_sha256_matches_supplied_pin": archive_sha256 == ARCHIVE_EXPECTED_SHA256,
        "archive_stable_read": archive_before == archive_after,
        "all_regular_source_members_match": not differences,
        "all_expected_regular_members_checked": counts["regular_files"] == 10933,
        "identity_record_unchanged": identity_raw == IDENTITY.read_bytes(),
    }
    report = {
        "schema": "openrx-independent-source-binary-binding-v1",
        "status": "pass" if all(checks.values()) else "fail",
        "started_utc": began, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "checks": checks,
        "linked_identity_record": {"path": str(IDENTITY), "sha256": hashlib.sha256(identity_raw).hexdigest()},
        "binary": {"path": str(BINARY), "sha256": binary_sha256, "size_bytes": binary_bytes,
                   "stat_before": binary_before, "stat_after": binary_after},
        "source": {"archive": str(ARCHIVE), "archive_sha256": archive_sha256,
                   "expected_archive_sha256": ARCHIVE_EXPECTED_SHA256,
                   "archive_size_bytes": archive_bytes, "extraction_root": str(ROOT),
                   "expected_revision": REVISION, "entry_counts": counts,
                   "regular_member_bytes": source_bytes,
                   "regular_member_inventory_sha256": inventory.hexdigest(),
                   "modified_or_missing_archive_members": differences},
        "scope": "Independent byte comparison of every regular source archive member and the linked binary identity. Generated build outputs and bytecode are outside the source archive.",
        "limits": "No executable launched or guest inputs modified. This binds observed source and binary identities; it is not source reproducibility, proof of compiler provenance, Linux boot, guest runtime correctness, timing calibration or power evidence.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
