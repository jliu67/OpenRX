# Roadmap and acceptance gates

| Milestone | Deliverable | Acceptance |
|---|---|---|
| M0 Foundation | Memory, source pin, scripts, CI, templates | Integrity passes, build/tests/smoke recorded, repository accessible |
| M1 Native baseline | Known CPU v1/v2 mine-mode runs | Correct hashes, metadata, repeated runs, measured power for efficiency |
| M2 Hardware evidence | X5/SG2042 architecture report | Traceable sources; unknowns explicit; no guessed internals |
| M3 Simulation feasibility | Select core and simulator | Exact ISA/JIT/FP support, reproducible boot and correctness path |
| M4 Calibrated model | Baseline workload in model | Correct hashes and validated timing assumptions; uncertainty reported |
| M5 First optimization | One architectural change | Correctness unchanged, controlled baseline, area/timing/power tradeoff |
| M6 Prototype | FPGA functional subset | Timing closure and reproducible behavior; FPGA power not ASIC forecast |

First investigation: characterize v1/v2 thread scaling and AES effects on measured hardware, then study cache/memory pressure. Do not prescribe a bottleneck before measurement.

## Execution infrastructure prerequisite — 2026-10-09

[Migration #27](https://github.com/jliu67/OpenRX/issues/27) is **LOCAL_VALIDATING; the designated local policy is NOT YET ACTIVE**.
The owner's Ubuntu computer will execute full-system simulations, long CPU experiments, large RandomX workloads,
expensive profiling/toolchain builds and large generated artifacts after verified acceptance.
[Policy/interface](LOCAL_EXECUTION.md), [runbook](LOCAL_MIGRATION.md) and
[gate receipt](validation/local-migration-20261009/ACCEPTANCE.md) specify availability, owner-mediated GitHub
submission/retrieval, single-resource locking, offline behavior and incomplete migration gates.
Pinned build 03/loader/input preflight completed; execution `20261009T193937Z-576aa858c033` has started
runtime-only smoke, with guest/actual-stop acceptance pending. Remote execution is unavailable; no direct
host access is implied. Expensive research remains held until #27 has independently verified acceptance,
matching `LOCAL_ACTIVE` and explicit release bound to the actual reviewed merge/merged-document audit.
Branch workflow guards defer hosted full gem5/full-dataset/native steady steps to reviewed local requests,
without deleting commands or changing criteria. Skipped controls remain unexecuted; mainline enforcement
awaits reviewed merge and no self-hosted Actions runner has been provisioned.

This is an infrastructure prerequisite, not a new scientific milestone or completion of M1–M5.
M0's historical completion and all existing milestone acceptance criteria are preserved.
Local boot/runtime smoke and runner durability do not establish complete RandomX, selected-core timing,
calibration, hardware power, area or RTL behavior. Keep #16 light/full-dataset/intended-core acceptance separate.
