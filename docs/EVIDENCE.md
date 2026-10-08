# Evidence register

| ID | Claim | Source / revision | Status | Limitation |
|---|---|---|---|---|
| E001 | Official RandomX v2.0.1 released | upstream release API, published 2026-05-10; release URL in RANDOMX.md | Verified metadata | Not Monero activation |
| E002 | Same benchmark supports v1/v2 | pinned src/tests/benchmark.cpp, --v2 option and flag | Verified source | Hardware performance unmeasured |
| E003 | Upstream tests include both algorithms | pinned src/tests/tests.cpp | Verified source | Execution outcome separate |
| E004 | v2 algorithm rationale | pinned doc/design_v2.md | Upstream design account | Developer benchmarks are not our measurements |
| E005 | X5 processor identity | teardown link in HARDWARE.md | Unverified lead | Needs images and chip evidence |
| E006 | X9 efficiency and shipment status | prior conversation | Unverified lead | Needs authoritative source |
| E007 | Exact static v1/v2 workload profile | pinned configuration.h; Git blob aac8914e0e8a52319600169bcc64b6cd9c967565; reviewed 2026-10-08 UTC; [source map](PHASE1.md) and [profile](../benchmarks/profiles/pinned-v2.0.1.json) | Source-derived and reproduced in CI | Not dynamic execution, DRAM traffic or performance |
| E008 | Upstream single-thread affinity ignored; thread-affinity errors may leave process successful | pinned src/tests/benchmark.cpp, mine() and one-thread dispatch with cpuid=-1; reviewed 2026-10-08 UTC | Verified source; wrapper safeguards tested | External CPU placement still needs host validation |
| E009 | Phase 1 tooling and native integration pass | implementation 360a925; [run 37719337133](https://github.com/jliu67/OpenRandomX/actions/runs/37719337133), job 113123130624; observed 2026-10-08 UTC | Executed: 42 tooling tests, 107 upstream tests, smoke/full-dataset controls | Hosted correctness evidence, not M1 efficiency; [details](validation/phase1/README.md) |

Add source URL, revision, retrieval date and exact location when resolving a lead. Do not upgrade confidence merely because several sites repeat the same claim. E001-E006 retain their prior recorded status; this Phase 1 session did not independently reverify current network activation or hardware-market claims.
