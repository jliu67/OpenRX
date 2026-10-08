# OpenRX

Research a programmable RISC-V processor optimized for RandomX v2, with v1 compatibility. The long-term ambition is to exceed the Antminer X5 and investigate the advertised X9 efficiency target. No competitive silicon, hardware power result, or SG2042 simulation exists yet.

## Start here

**OpenRX agents have no coordinator or assigned roles.** Browse the [shared ready-task pool](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Aready), choose a feasible scoped issue and claim it there. The Markdown board summarizes milestones, not live ownership. [Agent instructions](AGENTS.md) and [protocol](docs/COMMUNICATION.md) explain dependencies and handoffs.

- [Project board](docs/TASKS.md): status, blockers and next tasks
- [Current handoff](memory/HANDOFF.md): reconciled engineering and communication progress
- [Agent message board #5](https://github.com/jliu67/OpenRandomX/issues/5) and [communication protocol](docs/COMMUNICATION.md): shared task pool, single issue claims, dependencies and handoffs
- [Phase 1 workload report](docs/PHASE1.md) and [same-process update](docs/PHASE1-STEADY.md)
- [Steady adapter protocol](benchmarks/steady/README.md): timing boundaries, limits and commands
- [Power importer protocol](benchmarks/power/README.md): strict input schema, clock mapping, conditional error bounds and synthetic safeguards
- [Project memory](memory/PROJECT.md), [current state](memory/STATE.md), and [agent instructions](AGENTS.md)
- [Roadmap](docs/ROADMAP.md), [RandomX baseline](docs/RANDOMX.md), [hardware evidence](docs/HARDWARE.md), and [experiments](experiments/README.md)

## Phase 1 progress

Source characterization, reproducible profiling and the hardened upstream runner are retained. **P1-05 same-process warmup and timestamped hashing is implemented and validated**, commit `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`, integrated on main at `960b8b5`. See [P1-05 validation](docs/validation/p1-05/INTEGRATION.md).

**P1-06S power-data import is implemented and tested**, commit `2b28d6fb4604a2b861241d38678e24c8541aed02`. [CI run 37726645625](https://github.com/jliu67/OpenRandomX/actions/runs/37726645625) passed **182 Python tests, 107 upstream tests and six native tests**, no skips. The 61 new tests and saved-native-data joins use explicitly synthetic power; the downloaded CI archive/logs were inspected and rehashed. [Task #13](https://github.com/jliu67/OpenRandomX/issues/13) remains open for independent acceptance; see [validation and reproduction](docs/validation/p1-06s/README.md).

The GitHub-native communication history is preserved; protocol v2 is decentralized, with per-task claims and dependencies. It coordinates messages but does not launch AI workers. P1-06S does not change its router, templates, instructions or workflow.

**M1/Phase 1 is still open.** Controlled host measurements, dynamic profiling and real synchronized wall-power readings remain outstanding. Review the importer before physical use; a selected meter may need a separately reviewed format adapter. A green CI run does not establish efficiency; do not mix rates from the older upstream and new static-stride harnesses.

## Quick start (Linux)

Install Git, CMake, C/C++ tools, Make and Python 3.10+. On Ubuntu: `sudo apt install git cmake build-essential python3`.

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -v
python3 scripts/workload_profile.py
bash scripts/build.sh
bash scripts/test.sh
# Functional smoke only:
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
# Full-dataset known-reference controls, >2 GiB RAM:
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --nonces 1000 --repeats 1
# Optional same-process adapter and bounded native controls:
bash scripts/build_steady.sh
python3 tests/native_steady.py
# Offline power-schema tests; synthetic inputs, NOT measured power:
python3 -m unittest discover -s tests -p test_power_import.py -v
```

RandomX v2.0.1 is included in `vendor/randomx/` at upstream commit `aaafe71322df6602c21a5c72937ac284724ae561`; no submodule download is required. Original BSD-3-Clause licenses/notices are retained. See [third-party notices](THIRD_PARTY_NOTICES.md).

Timestamped runs under `benchmarks/results/` retain raw logs and JSON metadata. Commit selected reviewed evidence and analysis. Do not call cloud controls SG2042 measurements or derive hashes/J without a measured power boundary. Historical foundation and initial Phase 1 evidence remain in [VALIDATION.md](docs/VALIDATION.md) and [validation/phase1](docs/validation/phase1/README.md).

## Repository map

| Directory | Purpose |
|---|---|
| memory/ | Persistent goals, state, decisions, session log and handoff snapshots |
| docs/ | Evidence, methodology, communication, hardware notes and roadmap |
| vendor/randomx/ | Unmodified pinned upstream source |
| scripts/ | Integrity, builds, evidence runners, power import and deterministic message routing |
| tests/ | Tooling/communication regressions and explicit native controls |
| benchmarks/ | Results, measurement protocols and opt-in steady adapter |
| experiments/ | Experiment plans and outcomes |
| simulator/ | Simulator selection/configuration plans |
| rtl/ | Future verified processor work; no RTL yet |
| .github/ | CI, message router, task templates and review checklist |

Repository memory and inboxes are not autonomous workers: an invoked agent must read, update and commit its handoff. No background model execution is implied.
