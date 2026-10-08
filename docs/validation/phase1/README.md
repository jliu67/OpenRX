# Phase 1 validation record

Date: 2026-10-08 UTC (2026-10-07 Edmonton). Implementation commit: `360a9255703a28845a799cfcc1086d1fb84a2c48`. Original reviewed base: `2e6f3653883c4a8b344be4c4c7e4b1d8dfec0df4`.

## Local tooling checks

`python3 -m unittest discover -s tests -v` passed **42 tests, zero skips** using Python 3.13.5. Full local output is [tooling-tests.log](tooling-tests.log). The four runner integration tests execute temporary synthetic benchmark fixtures to exercise command orchestration, timeout/nonzero failures, short-run rejection and warmup separation. Their fixture rates/hashes are NOT new RandomX measurements.

`python3 scripts/workload_profile.py --output benchmarks/profiles/pinned-v2.0.1.json` produced the committed deterministic profile. The input configuration's Git blob hash matched connector-read blob `aac8914e0e8a52319600169bcc64b6cd9c967565`. Python compilation checks also passed. No full native source build was performed locally because direct network/DNS access was unavailable.

## Actual native integration in GitHub Actions

[Run 37719337133](https://github.com/jliu67/OpenRandomX/actions/runs/37719337133) completed successfully on the implementation commit. Job: `113123130624`; configured runner: `ubuntu-24.04`; reported image OS: Ubuntu 24.04.5; C/C++ compiler: GNU 13.3.0. The job log was inspected, not merely its green badge.

| Check | Observed outcome |
|---|---|
| Vendor integrity | All 171 files matched |
| Tooling regression suite | 42 passed; no skips |
| Static profile reproduction | Byte-for-byte diff passed |
| Native build | Passed |
| Upstream randomx-tests | 107 passed; no skipped test cases |
| V1/V2 light smoke | Passed; 2 nonces each; not known-reference throughput evidence |
| V1/V2 full-dataset controls | Runner passed; 1,000 nonces, seed 0, one hashing thread, two init threads, one repetition |
| Artifact upload | Passed; 12 files, 18,690 bytes |

The full-dataset runner checks both calculated and printed hashes against constants read from pinned `benchmark.cpp`. Success therefore establishes that its known-reference checks passed. Individual run JSON/logs were not independently downloaded in this session; no numeric throughput is reported here.

Raw build/test/benchmark logs, CMake caches and metadata are in [correctness-logs artifact 11524827413](https://github.com/jliu67/OpenRandomX/actions/runs/37719337133/artifacts/11524827413). Uploaded archive SHA-256 reported by Actions: `9432a68b6e38a25fde57fdddb3557ad8cf2c108df57eafffc638bbc679032d06`. This is an Actions-reported digest, not a separately downloaded-and-rehashed archive. Run metadata is also retained in [ci-status.json](ci-status.json). Artifacts are subject to retention; promote raw files into reviewed repository evidence before using them for durable performance conclusions.

Commands used by the workflow:

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -v
python3 scripts/workload_profile.py --output build/validation/workload-profile.json
diff -u benchmarks/profiles/pinned-v2.0.1.json build/validation/workload-profile.json
bash scripts/build.sh
bash scripts/test.sh
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --init-threads 2 --nonces 1000 --repeats 1 --timeout 300
```

## Warnings, limitations and non-results

Upstream CMake minimum-version deprecation and missing `.note.GNU-stack`/executable-stack linker warnings remained visible. Inherited checkout/upload actions also emitted Node.js runtime deprecation warnings. Nothing was silently patched in vendor code to suppress these.

The local workspace's direct source-download attempt failed with DNS resolution error; authenticated connector reads and CI were used instead. No wall-power access, calibrated power model, controlled bare-metal thread/AES matrix, hardware-counter profile, RISC-V performance run or simulation was obtained. CI step durations include setup and are not mining hashrate. **M1 and issue #1 remain open.**
