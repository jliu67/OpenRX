# RandomX workload baseline

Pinned official repository: https://github.com/tevador/RandomX
Release: https://github.com/tevador/RandomX/releases/tag/v2.0.1
Commit: aaafe71322df6602c21a5c72937ac284724ae561

The same release supports both algorithms. `randomx-benchmark --mine --jit` selects v1, and adding `--v2` selects v2. The upstream `randomx-tests` binary includes interpreter/JIT v1/v2 hash tests and algorithm-switch tests. Inspect actual test output; architecture-specific cases may be skipped.

The release notes identify a rare ARM/RISC-V JIT ISUB_R hash bug fixed in v2.0.1. Do not pin v2.0.0 for a RISC-V baseline.

At this pinned revision, doc/design_v2.md describes longer programs (256 → 384 instructions), additional AES mixing, CFROUND changes, and dataset prefetch two iterations ahead. Software release availability does not establish Monero network activation.

The benchmark's `--verify` mode uses the light cache and is suitable for a low-memory smoke test. It is not full-dataset mining mode. `--mine` needs the dataset plus initialization resources; allow more than 2 GiB free memory.

A controlled comparison uses the same binary, compiler, CPU, affinity, thread count, nonce count, seed, pages and AES mode. Alternate v1/v2 order across repetitions. Warm up before formal measurements and use long enough measured runs. Report dispersion and all runs, not only the best result.

Vendor provenance is in vendor/randomx.lock.json and vendor/randomx.sha256.json. To upgrade, explicitly fetch and inspect a selected upstream commit, retain licenses, regenerate the manifest, record the decision, and rerun correctness checks. Never overwrite it from a moving branch automatically.
