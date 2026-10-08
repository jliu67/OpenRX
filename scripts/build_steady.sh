#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Rebuild rather than silently linking a stale native library.
bash scripts/build.sh
cmake -S benchmarks/steady -B build/steady -DCMAKE_BUILD_TYPE=Release
cmake --build build/steady --parallel "${BUILD_JOBS:-2}"
