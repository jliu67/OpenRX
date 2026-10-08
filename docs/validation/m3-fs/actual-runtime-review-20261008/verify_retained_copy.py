#!/usr/bin/env python3
"""Read-only check of retained actual runtime evidence against its original."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys


def digest(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained", required=True, type=Path)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.retained / "artifact-manifest.json").read_text())
    audit = {"scope": "retained actual runtime evidence byte consistency; no execution",
             "argv": [sys.executable, *sys.argv], "files": [], "encoded_artifacts": []}
    errors = []
    for expected in manifest["files"]:
        rel = Path(expected["path"])
        try:
            assert not rel.is_absolute() and ".." not in rel.parts
            retained_path = args.retained / rel
            assert retained_path.is_file() and not retained_path.is_symlink()
            data = retained_path.read_bytes()
            actual = digest(data)
            assert actual == {key: expected[key] for key in ("bytes", "sha256")}
            original_path = args.original / rel
            original_match = None
            metadata_match = None
            if original_path.exists():
                assert original_path.is_file() and not original_path.is_symlink()
                original_data = original_path.read_bytes()
                original_match = data == original_data
                if str(rel) == "execution-source/manifest.json":
                    retained_metadata, original_metadata = json.loads(data), json.loads(original_data)
                    retained_metadata.pop("snapshot_utc")
                    original_metadata.pop("snapshot_utc")
                    metadata_match = retained_metadata == original_metadata
                    assert metadata_match
                else:
                    assert original_match
            else:
                assert str(rel) in {"README.md", "command.txt", "m5out/device.dtb.base64"}
            audit["files"].append({"path": str(rel), **actual,
                                   "original_byte_match": original_match,
                                   "original_metadata_match_except_snapshot_utc": metadata_match})
        except (AssertionError, OSError) as exc:
            errors.append({"path": str(rel), "error": type(exc).__name__ + ": " + str(exc)})
    for expected in manifest["encoded_artifacts"]:
        try:
            decoded = base64.b64decode(b"".join((args.retained / expected["path"]).read_bytes().split()), validate=True)
            actual = digest(decoded)
            assert actual == {"bytes": expected["decoded_bytes"], "sha256": expected["decoded_sha256"]}
            assert decoded == (args.original / expected["decoded_path"]).read_bytes()
            audit["encoded_artifacts"].append({"path": expected["path"], **actual,
                                                "original_byte_match": True})
        except (AssertionError, OSError, ValueError) as exc:
            errors.append({"path": expected["path"], "error": type(exc).__name__ + ": " + str(exc)})
    audit["errors"] = errors
    audit["status"] = "pass" if not errors else "fail"
    args.output.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
