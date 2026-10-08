# OpenRX

Research a programmable RISC-V processor optimized for RandomX v2, with v1 compatibility. The long-term ambition is to exceed the Antminer X5 and investigate the advertised X9 efficiency target. No competitive silicon, hardware power result, or SG2042 simulation exists yet.

## Start here

- [Project board](docs/TASKS.md): task status, claims, blockers and collaboration protocol
- [Latest agent handoff](memory/HANDOFF.md): exact next steps and evidence
- [Phase 1 workload report](docs/PHASE1.md): source analysis and measurement protocol
- [Project memory](memory/PROJECT.md): goals and constraints
- [Current state](memory/STATE.md): completed work and next actions
- [Agent instructions](AGENTS.md): required startup and handoff procedure
- [Roadmap](docs/ROADMAP.md): milestones and evidence gates
- [RandomX baseline](docs/RANDOMX.md): pinned implementation and v1/v2 selection
- [Hardware evidence](docs/HARDWARE.md): what remains unverified
- [Experiments](experiments/README.md): hypothesis and result format

## Phase 1 progress

Source characterization, reproducible static profiling and benchmark-runner hardening are committed. The 42 new tooling tests and all 107 upstream tests passed in [CI run 37719337133](https://github.com/jliu67/OpenRandomX/actions/runs/37719337133), including both full-dataset reference controls. See [Phase 1 validation](docs/validation/phase1/README.md). The controlled target-host throughput matrix, dynamic bottleneck profiling and wall-power measurements remain open; CI success does not complete M1.

## Quick start (Linux)

Install Git, CMake, a C/C++ toolchain, Make, and Python 3.10+. On Ubuntu: `sudo apt install git cmake build-essential python3`.

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -v
python3 scripts/workload_profile.py
bash scripts/build.sh
bash scripts/test.sh
# Fast functional smoke test in verification mode; NOT mining throughput:
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
# Full-dataset mining baseline, >2 GiB RAM; tune threads to your machine:
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --nonces 1000 --repeats 3
```

RandomX v2.0.1 source is included in `vendor/randomx/` at commit `aaafe71322df6602c21a5c72937ac284724ae561`; no submodule download is required. Its original BSD-3-Clause license and notices are retained. See [third-party notices](THIRD_PARTY_NOTICES.md).

Runs create timestamped directories under `benchmarks/results/` with raw logs and JSON metadata. Commit selected, reviewed results alongside analysis. Never treat a cloud-host smoke test as SG2042 performance, or calculate hashes/J without a measured power boundary.

Local validation: 107 upstream tests passed with no skips, and both full-dataset algorithm reference checks matched. See [validation evidence](docs/VALIDATION.md). [GitHub CI passed](https://github.com/jliu67/OpenRandomX/actions/runs/37716942121).

## Repository map

| Directory | Purpose |
|---|---|
| memory/ | Durable goals, state, decisions, open questions, session log |
| docs/ | Evidence register, methodology, hardware notes, roadmap |
| vendor/randomx/ | Unmodified upstream source snapshot |
| scripts/ | Source integrity check, build, tests, reproducible runs |
| benchmarks/ | Results and measurement instructions |
| experiments/ | Experiment proposals and outcome records |
| simulator/ | Simulator selection and configuration plans |
| rtl/ | Future verified processor work; no RTL implemented yet |
| .github/ | CI, experiment/research issue templates, PR checklist |

A repository note is persistent context, not an autonomous service: agents must read it, update it, and commit their handoffs.
