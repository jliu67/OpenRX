#!/usr/bin/env python3
"""Download exact guest resources; preparation alone is not Linux boot evidence."""
import argparse
import gzip
import hashlib
import json
import os
import shutil
import time
import urllib.request
from pathlib import Path


def hashes(path):
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while data := stream.read(4 * 1024 * 1024):
            md5.update(data)
            sha256.update(data)
            size += len(data)
    return {"bytes": size, "md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def verify(path, resource):
    result = hashes(path)
    if result["md5"] != resource["upstream_md5"]:
        raise ValueError(f"Upstream MD5 mismatch: {resource['id']}")
    if resource.get("sha256") and result["sha256"] != resource["sha256"]:
        raise ValueError(f"Pinned SHA-256 mismatch: {resource['id']}")
    if resource.get("bytes") and result["bytes"] != resource["bytes"]:
        raise ValueError(f"Pinned byte count mismatch: {resource['id']}")
    return result


def download(resource, directory, seconds):
    target = directory / resource["filename"]
    if target.exists():
        return verify(target, resource)
    partial = target.with_suffix(target.suffix + ".download")
    unpacked = target.with_suffix(target.suffix + ".unpack")
    started = time.monotonic()
    request = urllib.request.Request(resource["url"], headers={"User-Agent": "OpenRX-gem5-preparation/1"})
    # Socket and wall limits are both intentional. No unbounded retry loop.
    received = 0
    with urllib.request.urlopen(request, timeout=30) as response, partial.open("wb") as out:
        while data := response.read(1024 * 1024):
            if time.monotonic() - started > seconds:
                raise TimeoutError(f"Download exceeded {seconds}s: {resource['id']}")
            received += len(data)
            if received > 2 * 1024**3:
                raise ValueError("Compressed/raw resource exceeds 2 GiB download bound")
            out.write(data)
    if resource.get("compressed_bytes") and received != resource["compressed_bytes"]:
        raise ValueError("Compressed resource byte count differs from pin")
    if resource.get("compressed_sha256") and hashes(partial)["sha256"] != resource["compressed_sha256"]:
        raise ValueError("Compressed resource SHA-256 differs from pin")
    if resource["gzip"]:
        expanded = 0
        with gzip.open(partial, "rb") as inp, unpacked.open("wb") as out:
            while data := inp.read(4 * 1024 * 1024):
                if time.monotonic() - started > seconds:
                    raise TimeoutError("Resource download/decompression wall bound exceeded")
                expanded += len(data)
                if expanded > 8 * 1024**3:
                    raise ValueError("Expanded resource exceeds 8 GiB bound")
                out.write(data)
        result = verify(unpacked, resource)
        os.replace(unpacked, target)
        partial.unlink()
    else:
        result = verify(partial, resource)
        os.replace(partial, target)
    result["downloaded_bytes"] = received
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resource-timeout", type=int, default=900)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("resources.json"))
    args = parser.parse_args()
    if args.resource_timeout <= 0:
        parser.error("resource-timeout must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "evidence_class": "resource-preparation",
              "boot_executed": False, "status": "fail", "resources": [],
              "resource_timeout_seconds": args.resource_timeout,
              "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest()}
    try:
        manifest = json.loads(args.manifest.read_text())
        # Retain the exact input metadata alongside observed SHA-256 values.
        shutil.copyfile(args.manifest, args.output_dir / "resources-input.json")
        for resource in manifest["resources"]:
            result = download(resource, args.output_dir, args.resource_timeout)
            report["resources"].append({**resource, "observed": result})
        report["status"] = "pass"
    except (OSError, ValueError, TimeoutError) as exc:
        report["error"] = str(exc)
    finally:
        (args.output_dir / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
