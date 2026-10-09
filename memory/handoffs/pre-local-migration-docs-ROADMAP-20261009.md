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
