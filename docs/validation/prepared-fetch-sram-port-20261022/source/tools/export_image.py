#!/usr/bin/env python3
"""Offline packing for the single explicitly admitted retained cache0 image."""
import argparse
import hashlib
import json
from pathlib import Path
import re

COUNTS = (447, 438, 449, 447, 444, 449, 452, 437)
KIND = "actual-initCache-generated-programs"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def words(path, digits, count):
    lines = Path(path).read_text(encoding="ascii").splitlines()
    require(len(lines) == count, f"row count: {Path(path).name}")
    require(all(re.fullmatch(r"[0-9a-fA-F]{%d}" % digits, row) for row in lines),
            f"hex width/value: {Path(path).name}")
    return [int(row, 16) for row in lines]


def read_image(source):
    source = Path(source)
    cache = json.loads((source / "cache-0-metadata.json").read_text())
    require(cache.get("cache_id") == 0 and cache.get("prepared_programs") == 8 and
            cache.get("reciprocal_count") == 239 and
            cache.get("prepared_replay_identity_checked") is True, "cache descriptor")
    descriptors = (source / "cases.hex").read_text().splitlines()
    require(len(descriptors) >= 2, "case descriptors missing")
    counts = None
    for case, item in ((0, 0), (1, 10000000)):
        meta = json.loads((source / f"case-{case:03d}" / "metadata.json").read_text())
        require(meta.get("kind") == KIND and meta.get("native_generated_programs") is True,
                "image kind")
        require(meta.get("case_id") == case and meta.get("cache_id") == 0 and
                meta.get("item_hex") == f"{item:016x}" and meta.get("retired") == 3563 and
                meta.get("muls") == 1254 and meta.get("full_native_final_agrees") is True and
                meta.get("singleton_full_stage_agrees") is True, "case identity")
        fields = descriptors[case].split()
        require(len(fields) == 7 and int(fields[0]) == case and int(fields[1]) == 0 and
                int(fields[2], 16) == item and int(fields[3], 16) == 239, "case descriptor")
        require(re.fullmatch(r"[0-9a-fA-F]{20}", fields[4]) is not None, "counts width")
        packed = int(fields[4], 16)
        found = tuple((packed >> (10 * i)) & 1023 for i in range(8))
        require(found == COUNTS, "admitted counts")
        require(counts is None or found == counts, "shared counts")
        counts = found
    metadata = json.loads((source / "cache-0-reciprocal-metadata.json").read_text())
    require(metadata.get("global_indices") is True and metadata.get("deduplicated") is False,
            "reciprocal namespace")
    entries = metadata.get("entries")
    require(type(entries) is list and len(entries) == 239, "reciprocal entry count")
    table = words(source / "cache-0-reciprocals.mem", 16, 239)
    for i, entry in enumerate(entries):
        require(type(entry) is dict and entry.get("index") == i, "reciprocal entry index")
        divisor = entry.get("divisor")
        require(type(divisor) is int and 0 < divisor < (1 << 32) and
                divisor & (divisor - 1) != 0, "reciprocal divisor")
        value = entry.get("value_hex")
        require(type(value) is str and re.fullmatch(r"[0-9a-fA-F]{16}", value) is not None,
                "reciprocal metadata width")
        # Exact integer identity of retained randomx_reciprocal, no floating point.
        expected = ((1 << (63 + divisor.bit_length())) // divisor) & ((1 << 64) - 1)
        require(table[i] == int(value, 16) == expected, "reciprocal table value")
    rows = []
    seen = set()
    for program, count in enumerate(counts):
        arrays = []
        for stem, digits in (("program", 16), ("rcp-valid", 1), ("rcp-index", 8), ("reciprocals", 16)):
            one = source / "case-000" / f"{stem}-{program}.mem"
            two = source / "case-001" / f"{stem}-{program}.mem"
            values = words(one, digits, 512)
            require(one.read_bytes() == two.read_bytes(), "shared image differs")
            arrays.append(values)
        for pc in range(512):
            instruction, valid, index, reciprocal = (a[pc] for a in arrays)
            require(valid in (0, 1), "reciprocal flag")
            if pc >= count:
                require((instruction, valid, index, reciprocal) == (0, 0, 0, 0), "source padding")
                rows.append(0)
                continue
            require((instruction & 255) <= 13, "unsupported opcode")
            require(valid == int((instruction & 255) == 13), "reciprocal opcode flag")
            if valid:
                require(index == instruction >> 32 and index < len(table), "reciprocal index binding")
                require(reciprocal == table[index], "row reciprocal value")
                seen.add(index)
            else:
                require(index == 0 and reciprocal == 0, "nonreciprocal metadata")
            rows.append(instruction | (reciprocal << 64) | (index << 128) | (valid << 160))
    require(seen == set(range(239)), "reciprocal coverage")
    return rows, counts


def export_image(source, output):
    rows, counts = read_image(source)
    output = Path(output)
    require(not output.exists(), "output already exists; no overwrite or live reload")
    output.mkdir(parents=True)
    (output / "rows.mem").write_text("".join(f"{value:064x}\n" for value in rows), encoding="ascii")
    (output / "counts.mem").write_text("".join(f"{value:03x}\n" for value in counts), encoding="ascii")
    report = {"schema": "openrx.prepared-fetch-export.v1", "kind": KIND,
              "scope": "single_retained_cache0_image_only", "rows": 4096, "row_bits": 256,
              "payload_bits": 161, "reserved_zero_bits": 95, "active_rows": sum(counts),
              "padding_rows": 4096 - sum(counts), "reciprocal_entries": 239,
              "counts": list(counts), "physical_acceptance": False,
              "files": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                        for name in ("rows.mem", "counts.mem")}}
    (output / "export.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_image(args.source, args.out), sort_keys=True))


if __name__ == "__main__":
    main()
