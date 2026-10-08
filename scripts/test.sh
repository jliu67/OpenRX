#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/verify_vendor.py
mkdir -p build/validation
build/randomx/randomx-tests 2>&1 | tee build/validation/randomx-tests.log
