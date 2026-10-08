# EXP-001: controlled v1/v2 native baseline

Status: source characterization, tooling/native correctness preflight and P1-05 same-process instrumentation complete; controlled target-host experiment and power measurements pending. **Not a completed M1 experiment.**

Hypothesis: the v2/v1 throughput ratio depends on available execution and memory resources; measure instead of assuming SG2042 behavior.

Run upstream tests, then mine-mode v1/v2 with equal seeds/nonces at 1, 2, 4 and suitable higher thread counts. Alternate order and warm up. Use even repeats (at least four) of sufficient duration for balanced v1/v2 starting order. Record CPU/cache/RAM/OS/toolchain details and thermal/power settings. Repeat hardware versus software AES only on an ISA that supports hardware AES.

Acceptance: every known reference matches; full logs and JSON stored; no skipped/failing correctness hidden. Report median and range for throughput, and hashes/J only with time-aligned power samples. Native measurements cannot establish SG2042 bottlenecks.

## Initial preflight outcome — 2026-10-08 UTC

Source-derived analysis and original commands: [docs/PHASE1.md](../docs/PHASE1.md). Initial implementation: `360a9255703a28845a799cfcc1086d1fb84a2c48`. Validation: [docs/validation/phase1/README.md](../docs/validation/phase1/README.md).

42 new tooling tests and all 107 upstream tests passed in the initial CI; both full-dataset reference controls passed. These were functional controls on a hosted runner, not the repeated known-host experiment. Static instruction slots, opcode weights and AES round-function counts are not dynamic profiles or hardware measurements.

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

Remaining blockers: controlled benchmark host, dynamic profiler/counter access, a tested power-data import/validation path (P1-06S, ready for software work), and real synchronized power-meter samples. Owner for the next measured experiment is unclaimed; coordinate on issue #1 and [docs/TASKS.md](../docs/TASKS.md).

Follow-up: select a simulator that can reproduce exact workload behavior, then vary memory latency/cache/AES capacity independently in a calibrated model. Do not bypass the roadmap's baseline/model gates.
