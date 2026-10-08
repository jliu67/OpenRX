# OpenRandomX

Research a programmable RISC-V processor optimized for RandomX v2, with v1 compatibility. The long-term ambition is to exceed the Antminer X5 and investigate the advertised X9 efficiency target. No competitive silicon, hardware power result, or SG2042 simulation exists yet.

## Start here

- [Project memory](memory/PROJECT.md): goals and constraints
- [Current state](memory/STATE.md): completed work and next actions
- [Agent instructions](AGENTS.md): required startup and handoff procedure
- [Roadmap](docs/ROADMAP.md): milestones and evidence gates
- [RandomX baseline](docs/RANDOMX.md): pinned implementation and v1/v2 selection
- [Hardware evidence](docs/HARDWARE.md): what remains unverified
- [Experiments](experiments/README.md): hypothesis and result format

## Quick start (Linux)

Install Git, CMake, a C/C++ toolchain, Make, and Python 3.10+. On Ubuntu: `sudo apt install git cmake build-essential python3`.

```bash
python3 scripts/verify_vendor.py
bash scripts/build.sh
bash scripts/test.sh
# Fast functional smoke test in verification mode; NOT mining throughput:
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
# Full-dataset mining baseline, >2 GiB RAM; tune threads to your machine:
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --nonces 1000 --repeats 3
```

RandomX v2.0.1 source is included in `vendor/randomx/` at commit `aaafe71322df6602c21a5c72937ac284724ae561`; no submodule download is required. Its original BSD-3-Clause license and notices are retained. See [third-party notices](THIRD_PARTY_NOTICES.md).

Runs create timestamped directories under `benchmarks/results/` with raw logs and JSON metadata. Commit selected, reviewed results alongside analysis. Never treat a cloud-host smoke test as SG2042 performance, or calculate hashes/J without a measured power boundary.

Local validation: 107 upstream tests passed with no skips, and both full-dataset algorithm reference checks matched. See [validation evidence](docs/VALIDATION.md). GitHub CI has not run yet.

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
