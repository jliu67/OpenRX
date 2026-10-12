# EXP-001: controlled v1/v2 native baseline

Status: source characterization, tooling/native correctness preflight and P1-05 same-process instrumentation complete; P1-06S power importer independently accepted as software, merged in PR #17 and #13 closed; controlled target-host experiment and power measurements pending. **Not a completed M1 experiment.**

Hypothesis: the v2/v1 throughput ratio depends on available execution and memory resources; measure instead of assuming SG2042 behavior.

Run upstream tests, then mine-mode v1/v2 with equal seeds/nonces at 1, 2, 4 and suitable higher thread counts. Alternate order and warm up. Use even repeats (at least four) of sufficient duration for balanced v1/v2 starting order. Record CPU/cache/RAM/OS/toolchain details and thermal/power settings. Repeat hardware versus software AES only on an ISA that supports hardware AES.

Acceptance: every known reference matches; full logs and JSON stored; no skipped/failing correctness hidden. Report median and range for throughput, and hashes/J only with time-aligned power samples. Native measurements cannot establish SG2042 bottlenecks.

## Initial preflight outcome — 2026-10-08 UTC

Source-derived analysis and original commands: [docs/PHASE1.md](../docs/PHASE1.md). Initial implementation: `360a9255703a28845a799cfcc1086d1fb84a2c48`. Validation: [docs/validation/phase1/README.md](../docs/validation/phase1/README.md).

42 new tooling tests and all 107 upstream tests passed in the initial CI; both full-dataset reference-control runs passed. These were functional controls on a hosted runner, not the repeated known-host experiment. Static instruction slots, opcode weights and AES round-function counts are not dynamic profiles or hardware measurements.

That original runner's schema 2 separates warmup/measurement records and preserves failed/too-short runs. Its warmups still use separate processes and its single-thread upstream affinity option is ignored/rejected. Use validated external process affinity.

## P1-05 instrumentation outcome — 2026-10-08 UTC

Implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676` adds the opt-in [steady adapter](../benchmarks/steady/README.md) without altering vendor code or the older runner. It retains initialized dataset/VMs/workers through automatic known-hash controls, immediate warmups and balanced measured trials. It records exact monotonic/realtime clock brackets and completed counts. The timing envelope and harness scheduling differences are declared; markers alone do not establish meter synchronization.

[CI run 37722277487](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487) passed 64 tooling, 107 upstream and six native tests. All eight new known controls and both 17-nonce differential comparisons matched; expected duration failures were retained. Downloaded artifact records were revalidated locally. See [P1-05 evidence](../docs/validation/p1-05/README.md). The four CI configurations, including three workers on two exposed CPUs, are not this experiment's controlled performance matrix.

```bash
bash scripts/build_steady.sh
python3 tests/native_steady.py
# Pilot example only; choose a controlled host/CPU set and enough nonces for all
# compared configurations to clear the duration gate. Preserve rejected pilots.
python3 scripts/steady_benchmark.py --versions v1,v2 --threads 1 --aes hardware \
  --nonces 30000 --warmup-nonces 1000 --repeats 4 --min-seconds 30 --timeout 1800
```

Do not mix throughput from the new static-stride first/next/last harness with the upstream dynamic-scheduling harness. Compare configurations inside one declared harness. Clock mapping, meter latency and energy boundaries still require physical validation.

## P1-06S offline analysis outcome — 2026-10-08 UTC

Implementation `2b28d6fb4604a2b861241d38678e24c8541aed02` adds the [power importer](../benchmarks/power/README.md) and 61 deterministic synthetic tests. Subsequent independent software acceptance and repairs are recorded below; [#13](https://github.com/jliu67/OpenRandomX/issues/13) is closed as completed after PR #17 merged. Initial CI passed 182 Python, 107 upstream and six native tests. Its downloaded artifact and saved-data joins were checked; [validation and reproduction](../docs/validation/p1-06s/README.md) preserve the evidence.

The importer revalidates the benchmark and exact input binding, then applies explicit clock mapping, missing/gap/coverage rejection and conditional uncertainty-aware integration. Only measurement intervals count. All power traces exercised this session were synthetic; none establishes measured hashes/J or completes the controlled experiment. The point-power schema deliberately rejects interval-averaged/cumulative exports without a separately reviewed model or extension.

Remaining blockers: controlled benchmark host (#8), dynamic profiler/counter access (#11), and real synchronized power-meter samples/physical validation (#10). Importer software acceptance (#13) is complete. Use the specific open child issue for scoped claims; [#1](https://github.com/jliu67/OpenRandomX/issues/1) remains the parent milestone and discussion gate. Read [docs/TASKS.md](../docs/TASKS.md) and the current issue comments.

Follow-up: select a simulator that can reproduce exact workload behavior, then vary memory latency/cache/AES capacity independently in a calibrated model. Do not bypass the roadmap's baseline/model gates.

## Native staging preparation — 2026-10-12

[Task #35](https://github.com/jliu67/OpenRX/issues/35) adds fresh external native
builds, explicit executable/build/output locations and focused source/artifact
binding tests. [Software validation](../docs/validation/native-staging-20261012/README.md)
records 16 passing staging fixtures and 313 exercised lightweight tests with one
sandbox socket denial followed by a passing targeted rerun. Implementation awaits
independent review. No native compilation, full-dataset controls, pilot, measured
matrix, synchronized power or profiling was performed. This preparation preserves
the exact workload, even balanced repeats (at least four formally), known-hash
controls and all experiment acceptance. The [local-runner commands](../benchmarks/steady/README.md#isolated-local-staging-and-controls)
require separate reviewed requests and the shared compute slot; #8/M1 stay open.


## Independent importer acceptance — 2026-10-08

PR #17 repairs three malformed-input failure-report defects found in independent P1-06S review. A separate patch reviewer accepts the software after 64 importer tests, 327 wrong-type/13 Decimal cases, 10 unchanged valid-report comparisons and 9,024 numerical checks. See docs/validation/p1-06s/PATCH-REVIEW-20261008.md. PR #17 is merged at `973cd0d94f987ad4a46b85f7b6d66170104c64a1` and #13 is closed as completed. No physical power samples were added; M1 remains open.

## Network target context — 2026-10-08

The independently reviewed [Monero source audit](../docs/validation/monero-activation/REVIEW-20261008.md), merged in PR #19, identifies RandomX v1 in the current released mainnet consensus. This is source-backed inference, not an observed chain tip. No v2 mainnet activation date appears in the audited schedule; the October 5 FCMP++ beta schedule is a separate stressnet/testnet. Keep v2-first research and exact v1 controls in this baseline. Raw RandomX hashes do not validate the beta's additional PoW commitment or complete block-validation pipeline.
