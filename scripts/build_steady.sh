#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if (( $# )); then
  # Explicit local staging uses a fresh external build root, never old caches.
  exec python3 scripts/stage_native.py "$@"
fi
# Rebuild rather than silently linking a stale native library.
bash scripts/build.sh
cmake -S benchmarks/steady -B build/steady -DCMAKE_BUILD_TYPE=Release
cmake --build build/steady --parallel "${BUILD_JOBS:-2}"
