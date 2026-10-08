#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/verify_vendor.py
cmake -S vendor/randomx -B build/randomx -DCMAKE_BUILD_TYPE=Release -DARCH="${ARCH:-native}"
cmake --build build/randomx --parallel "${BUILD_JOBS:-2}"
