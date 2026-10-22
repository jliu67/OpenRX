#!/usr/bin/env python3
"""Independent, offline oracle for the single retained cache0 SRAM image.

PREPARED / UNRUN. This file is a future validation command, not its evidence.
It deliberately does not import the exporter or derive gold from exported rows.
Only logical image packing is checked; no physical SRAM/timing claim follows.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


COUNTS = (447, 438, 449, 447, 444, 449, 452, 437)
IMAGE_KIND = "actual-initCache-generated-programs"
CASE_KIND = "prepared-fetch-cache0-one-bank-v1"
HEX = re.compile(r"^[0-9a-fA-F]+$")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def regular(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"not a regular bound file: {path}")
    return path


def binding(path):
    data = regular(path).read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def load_json(path):
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(regular(path).read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def hex_words(path, width, count):
    lines = regular(path).read_text(encoding="ascii").splitlines()
    require(len(lines) == count, f"wrong row count: {path}")
    digits = (width + 3) // 4
    values = []
    for number, line in enumerate(lines):
        require(len(line) == digits and HEX.fullmatch(line) is not None,
                f"malformed fixed-width hex: {path}:{number + 1}")
        value = int(line, 16)
        require(value < 1 << width, f"out-of-width value: {path}:{number + 1}")
        values.append(value)
    return values


def inspect_source(source):
    """Use native descriptors and original fields, independently of exporter."""
    source = Path(source)
    case = source / "case-000"
    meta = load_json(case / "metadata.json")
    expected = {"case_id": 0, "cache_id": 0, "item_hex": "0000000000000000",
                "kind": IMAGE_KIND, "native_generated_programs": True,
                "retired": 3563, "muls": 1254, "full_native_final_agrees": True,
                "singleton_full_stage_agrees": True}
    require(meta == expected and all(type(meta[key]) is type(value) for key, value in expected.items()),
            "case metadata differs from the admitted native case")
    cache = load_json(source / "cache-0-metadata.json")
    expected_cache = {"cache_id": 0, "key_hex": "74657374206b657920303030", "key_bytes": 12,
                      "cache_bytes": 268435456, "cache_lines": 4194304, "native_flags": 0,
                      "argon_initializations": 1, "reciprocal_count": 239,
                      "prepared_programs": 8, "prepared_replay_identity_checked": True}
    require(cache == expected_cache
            and all(type(cache[key]) is type(value) for key, value in expected_cache.items()),
            "cache0 metadata differs from the admitted retained image")
    descriptor_lines = regular(source / "cases.hex").read_text(encoding="ascii").splitlines()
    require(len(descriptor_lines) >= 2, "missing native pair descriptors")
    descriptor = descriptor_lines[0].split()
    require(len(descriptor) == 7 and descriptor[:4] == ["0", "0", "0000000000000000", "000000ef"],
            "wrong cache0/case0 descriptor identity")
    require(len(descriptor[4]) == 20 and HEX.fullmatch(descriptor[4]) is not None,
            "malformed native packed program counts")
    packed_counts = int(descriptor[4], 16)
    require(tuple((packed_counts >> (10 * stage)) & 1023 for stage in range(8)) == COUNTS,
            "native counts differ from admitted immutable metadata")
    require(descriptor[5] == "0005000403040504" and len(descriptor[6]) == 128
            and HEX.fullmatch(descriptor[6]) is not None, "malformed retained descriptor tail")
    other = descriptor_lines[1].split()
    require(len(other) == 7 and other[:6] == ["1", "0", "0000000000989680", "000000ef",
                                            descriptor[4], descriptor[5]],
            "case1 descriptor does not share cache0 program metadata")
    table = hex_words(source / "cache-0-reciprocals.mem", 64, 239)
    reciprocal_meta = load_json(source / "cache-0-reciprocal-metadata.json")
    require(set(reciprocal_meta) == {"global_indices", "deduplicated", "entries"}
            and reciprocal_meta["global_indices"] is True
            and reciprocal_meta["deduplicated"] is False, "wrong global reciprocal metadata")
    entries = reciprocal_meta["entries"]
    require(type(entries) is list and len(entries) == 239, "wrong reciprocal metadata count")
    for index, entry in enumerate(entries):
        require(set(entry) == {"index", "divisor", "value_hex"}
                and type(entry["index"]) is int and entry["index"] == index,
                "global reciprocal index is not sequential")
        divisor = entry["divisor"]
        require(type(divisor) is int and 0 < divisor < 1 << 32 and divisor & (divisor - 1) != 0,
                "invalid original reciprocal divisor")
        value_hex = entry["value_hex"]
        require(type(value_hex) is str and len(value_hex) == 16 and HEX.fullmatch(value_hex),
                "invalid reciprocal metadata value")
        # Independent integer quotient form of retained RandomX reciprocal.c:
        # floor(2**(63 + bit_length(divisor)) / divisor). No model/native call.
        reciprocal = (1 << (63 + divisor.bit_length())) // divisor
        require(reciprocal == int(value_hex, 16) == table[index],
                f"reciprocal mathematical/metadata/table disagreement at {index}")

    gold = []
    seen_indices = []
    sources = ["cases.hex", "cache-0-metadata.json", "cache-0-reciprocals.mem",
               "cache-0-reciprocal-metadata.json", "case-000/metadata.json"]
    for stage, count in enumerate(COUNTS):
        names = {stem: case / f"{stem}-{stage}.mem"
                 for stem in ("program", "rcp-valid", "rcp-index", "reciprocals")}
        instruction = hex_words(names["program"], 64, 512)
        valid = hex_words(names["rcp-valid"], 1, 512)
        indices = hex_words(names["rcp-index"], 32, 512)
        reciprocals = hex_words(names["reciprocals"], 64, 512)
        sources.extend(str(path.relative_to(source)) for path in names.values())
        for pc in range(512):
            instr, is_rcp, index, reciprocal = (instruction[pc], valid[pc], indices[pc], reciprocals[pc])
            if pc >= count:
                require((instr, is_rcp, index, reciprocal) == (0, 0, 0, 0),
                        f"nonzero retained padding stage{stage}/pc{pc}")
                gold.append(0)
                continue
            opcode = instr & 255
            require(opcode <= 13 and is_rcp == int(opcode == 13),
                    f"instruction/reciprocal-valid semantics disagree stage{stage}/pc{pc}")
            if is_rcp:
                require(index < len(table) and index == instr >> 32 and reciprocal == table[index],
                        f"prepared instruction/global reciprocal binding differs stage{stage}/pc{pc}")
                seen_indices.append(index)
            else:
                require(index == 0 and reciprocal == 0,
                        f"nonreciprocal row carries reciprocal metadata stage{stage}/pc{pc}")
            # Independent byte-oriented assembly; no exporter helper/layout import.
            payload = instr.to_bytes(8, "little") + reciprocal.to_bytes(8, "little")
            payload += index.to_bytes(4, "little") + bytes([is_rcp])
            gold.append(int.from_bytes(payload, "little"))
    require(seen_indices == list(range(239)), "admitted reciprocal namespace is incomplete/reordered")
    return gold, {name: binding(source / name) for name in sorted(sources)}


def verify(source, image, report):
    source, image, report = Path(source), Path(image), Path(report)
    gold_path = image / "gold-payload.mem"
    require(not report.exists() and not gold_path.exists(), "refusing to overwrite prior oracle output")
    require(report.parent.is_dir(), "report directory must already exist")
    gold, source_bindings = inspect_source(source)
    observed_rows = hex_words(image / "rows.mem", 256, 4096)
    observed_counts = hex_words(image / "counts.mem", 10, 8)
    require(tuple(observed_counts) == COUNTS, "exported count metadata differs from native descriptor")
    for slot, expected in enumerate(gold):
        require(observed_rows[slot] == expected, f"SRAM row differs from original native fields: {slot}")
    # Gold is emitted only from independent source reconstruction, never rows.mem.
    with gold_path.open("x", encoding="ascii", newline="\n") as output:
        for expected in gold:
            output.write(f"{expected:041x}\n")
    result = {"schema": 1, "image_kind": CASE_KIND,
              "outcome": "PASS_CONDITIONAL_IMAGE_PACKING_ONLY",
              "original_source_kind": IMAGE_KIND, "cache_id": 0,
              "counts": list(COUNTS), "active_rows": sum(COUNTS),
              "padding_rows": 4096 - sum(COUNTS), "logical_rows": 4096,
              "logical_row_bits": 256, "payload_bits": 161, "reserved_zero_bits": 95,
              "reciprocal_rows": 239, "global_reciprocal_indices": [0, 238],
              "independent_gold_from_original_fields": True,
              "oracle_imports_exporter": False, "source_bindings": source_bindings,
              "output_bindings": {name: binding(image / name)
                                  for name in ("rows.mem", "counts.mem", "gold-payload.mem")},
              "oracle_binding": binding(Path(__file__)),
              "physical_sram_characterized": False, "achievable_frequency_hz": None,
              "physical_area_mm2": None, "physical_energy_j": None,
              "controller_phy_characterized": False, "full_hash_revalidated": False,
              "achieved_hashes_per_second": None, "wall_power_w": None,
              "acceptance_scope": "Offline immutable image packing and source binding only; RTL/controller cadence remains separate and unrun until its admitted command."}
    with report.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.source, args.image, args.report)
    print(json.dumps({"outcome": result["outcome"], "active_rows": result["active_rows"],
                      "padding_rows": result["padding_rows"], "report": str(args.report)}, sort_keys=True))


if __name__ == "__main__":
    main()
