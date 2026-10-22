#!/usr/bin/env python3
"""Command2: offline exporter followed by the separately implemented oracle."""
import argparse
import json
from pathlib import Path
from export_image import export_image
from check_image import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    export_image(args.source, args.out)
    result = verify(args.source, args.out, args.out / "oracle.json")
    print(json.dumps({"outcome": result["outcome"], "active_rows": result["active_rows"],
                      "padding_rows": result["padding_rows"], "physical_acceptance": False}, sort_keys=True))


if __name__ == "__main__":
    main()
