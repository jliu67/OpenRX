# OpenRX

Research a programmable RISC-V processor optimized for RandomX v2, with v1 compatibility. The long-term ambition is to exceed the Antminer X5 and investigate the advertised X9 efficiency target. No competitive silicon, hardware power result, or SG2042 simulation exists yet.

## Start here

- [Project board](docs/TASKS.md): task status, claims, blockers and collaboration protocol
- [Latest agent handoff](memory/HANDOFF.md): exact next steps and evidence
- [Phase 1 workload report](docs/PHASE1.md): initial source analysis and measurement protocol
- [Same-process instrumentation update](docs/PHASE1-STEADY.md): P1-05 completion and current limitations
- [Steady adapter protocol](benchmarks/steady/README.md): opt-in runner, timing boundary and commands
- [Project memory](memory/PROJECT.md): goals and constraints
- [Current state](memory/STATE.md): completed work and next actions
- [Agent instructions](AGENTS.md): required startup and handoff procedure
- [Roadmap](docs/ROADMAP.md): milestones and evidence gates
- [RandomX baseline](docs/RANDOMX.md): pinned implementation and v1/v2 selection
- [Hardware evidence](docs/HARDWARE.md): what remains unverified
- [Experiments](experiments/README.md): hypothesis and result format

## Phase 1 progress

Source characterization, reproducible static profiling and upstream-runner hardening are retained. **P1-05 same-process warmup and timing is now implemented and validated**, commit `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`. [CI run 37722277487](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487) passed 64 tooling tests, 107 upstream tests, six new native tests, and the previous smoke/full-dataset controls. The new native controls and both differential checks matched; the artifact was downloaded and its raw records/checksums revalidated. See [P1-05 validation](docs/validation/p1-05/README.md).

**M1/Phase 1 remains open:** controlled target-host throughput, dynamic profiling, power-data import software and real synchronized wall-power observations are still outstanding. A green CI run is not a measured efficiency baseline. The older runner remains available as an independent control; its rates must not be mixed with the new adapter's different scheduling/batch overhead.

## Quick start (Linux)

Install Git, CMake, a C/C++ toolchain, Make, and Python 3.10+. On Ubuntu: `sudo apt install git cmake build-essential python3`.

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -v
python3 scripts/workload_profile.py
bash scripts/build.sh
bash scripts/test.sh
# Fast functional smoke test; NOT mining throughput:
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
# Full-dataset known-reference controls, >2 GiB RAM:
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --nonces 1000 --repeats 1
# Optional same-process adapter and bounded native correctness suite:
bash scripts/build_steady.sh
python3 tests/native_steady.py
```

RandomX v2.0.1 source is included in `vendor/randomx/` at commit `aaafe71322df6602c21a5c72937ac284724ae561`; no submodule download is required. Its original BSD-3-Clause license and notices are retained. See [third-party notices](THIRD_PARTY_NOTICES.md).

Runs create timestamped directories under `benchmarks/results/` with raw logs and JSON metadata. Commit selected, reviewed results alongside analysis. Never treat a cloud-host smoke test as SG2042 performance, or calculate hashes/J without a measured power boundary.

Foundation-session validation and original CI evidence remain in [docs/VALIDATION.md](docs/VALIDATION.md). Initial Phase 1 evidence remains in [docs/validation/phase1/](docs/validation/phase1/README.md); newer P1-05 evidence is linked above.

## Repository map

| Directory | Purpose |
|---|---|
| memory/ | Durable goals, state, decisions, open questions, session log |
| docs/ | Evidence register, methodology, hardware notes, roadmap |
| vendor/randomx/ | Unmodified upstream source snapshot |
| scripts/ | Source integrity, build, tests, reproducible runs and evidence validation |
| tests/ | Tooling regressions and explicit native integration controls |
| benchmarks/ | Results, measurement instructions and opt-in steady adapter |
| experiments/ | Experiment proposals and outcome records |
| simulator/ | Simulator selection and configuration plans |
| rtl/ | Future verified processor work; no RTL implemented yet |
| .github/ | CI, experiment/research issue templates, PR checklist |

A repository note is persistent context, not an autonomous service: agents must read it, update it, and commit their handoffs.
