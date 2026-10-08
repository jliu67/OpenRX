# EXP-001: controlled v1/v2 native baseline

Status: source characterization and tooling/native correctness preflight complete; controlled target-host experiment and power measurements pending. **Not a completed M1 experiment.**

Hypothesis: the v2/v1 throughput ratio depends on available execution and memory resources; measure instead of assuming SG2042 behavior.

Run upstream tests, then mine-mode v1/v2 with equal seeds/nonces at 1, 2, 4 and suitable higher thread counts. Alternate order, warm up, use at least three repeats of sufficient duration. Record CPU/cache/RAM/OS/toolchain details and thermal/power settings. Repeat hardware versus software AES only on an ISA that supports hardware AES.

Acceptance: every known reference matches; full logs and JSON stored; no skipped/failing correctness hidden. Report median and range for throughput, and hashes/J only with time-aligned power samples. Native measurements cannot establish SG2042 bottlenecks.

## Phase 1 preflight outcome — 2026-10-08 UTC

Source-derived analysis and exact next commands: [docs/PHASE1.md](../docs/PHASE1.md). Implementation: `360a9255703a28845a799cfcc1086d1fb84a2c48`. Validation: [docs/validation/phase1/README.md](../docs/validation/phase1/README.md).

42 new tooling tests and all 107 upstream tests passed in CI; both full-dataset reference-control runs passed. These were functional controls on a hosted runner, not the repeated known-host experiment. Static instruction slots, opcode weights and AES round-function counts are not dynamic profiles or hardware measurements.

Runner schema 2 separates warmup/measurement records and records failed/too-short runs. Four measurement repeats are suggested for balanced v1/v2 start order. Current warmups use separate processes; precise same-VM warmup and power-aligned interval markers remain P1-05. The upstream single-thread affinity option is ignored, so the wrapper rejects it; use validated external process affinity instead.

Blockers: target benchmark host, dynamic profiler/counter access, steady-state interval instrumentation and real power-meter samples. Owner for the next measured experiment is unclaimed; coordinate on GitHub issue #1 and [docs/TASKS.md](../docs/TASKS.md).

Follow-up: select a simulator that can reproduce exact workload behavior, then vary memory latency/cache/AES capacity independently in a calibrated model. Do not bypass the roadmap's baseline/model gates.
