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

## Critical local infrastructure migration

**STAGING — the new infrastructure is NOT YET ACTIVE.**
[Task #27](https://github.com/jliu67/OpenRX/issues/27) is migrating persistent, expensive execution to the
owner's Ubuntu computer. [Local execution policy](docs/LOCAL_EXECUTION.md),
[migration/recovery runbook](docs/LOCAL_MIGRATION.md) and
[acceptance receipt](docs/validation/local-migration-20261009/ACCEPTANCE.md) explain actual availability,
submission, locks, evidence and remaining gates. Remote execution/retrieval is unavailable;
GitHub requests require owner-mediated local submission and result publication.

Defer full-scale simulations until verified cutover. After `LOCAL_ACTIVE`, gem5 full-system work,
long architecture/RandomX workloads, expensive profiling/builds and large artifacts use that host.
Sandboxes continue supporting code/review, lightweight tests, static analysis and small reproductions.
Scientific #16 and M1–M5 remain open independently of infrastructure acceptance.
Migration-branch guards defer hosted expensive gem5/full-dataset/native steady steps to reviewed local
requests; skipped controls are unexecuted, never passed. Those guards require reviewed merge before
main is updated, and no self-hosted Actions runner is configured.

## RISC-V feasibility progress

[Merged M3 work in PR #15](https://github.com/jliu67/OpenRandomX/pull/15) adds an
executable scalar RISC-V preflight, exact integer/FP controls and v2/v1
interpreter/JIT references. Actual QEMU CI passed all 39 required checks;
raw logs and binary digests were downloaded and independently revalidated.
See [candidate selections](simulator/README.md), [EXP-002](experiments/EXP-002-riscv-functional-preflight.md)
and [validation](docs/validation/m3/README.md).

Chipyard/MediumBoomV3Config is the provisional open RTL research target.
gem5 requires a validated Linux runtime path: its SE signal/cache-flush gaps
affect unchanged RandomX startup/JIT. [Task #16](https://github.com/jliu67/OpenRandomX/issues/16)
tracks full-system Linux feasibility. [Explicit Linux runtime controls](docs/validation/m3-fs/RUNTIME-CI.md) now pass natively and under scalar QEMU: actual SIGILL recovery, RW/RX page permissions and generated-code overwrite/flush/reexecution. M3 remains open for selected-core boot
and full-dataset correctness; no calibrated timing or efficiency is established.

[PR #18](https://github.com/jliu67/OpenRandomX/pull/18) now includes a successfully built pinned simulator and **actual Linux boot with all nine standalone runtime controls passing**, independently replayed. The unchanged light-mode RandomX matrix is a separate open gate under #16. [Executed results](docs/validation/m3-fs/README.md) retain original timeout/OOM failures, supported link recovery and raw guest evidence. [Saved simulator provenance](docs/validation/m3-fs/REUSE.md) remains intact; ordinary PR checks no longer rebuild it.
The original Library binary is currently unavailable to the migration's callable tools, so a separately
recorded pinned local rebuild is in progress; successful historical saving is not a verified local transfer. This one-core Atomic result does not establish selected RTL behavior or timing.

[PR #19](https://github.com/jliu67/OpenRandomX/pull/19) records the dated Monero source audit: current released mainnet consensus targets RandomX v1, inferred from source rather than a live tip. The beta's October 5 v2 fork is a separate stressnet/testnet schedule. Keep v2-first research and exact v1 controls; [audit](docs/validation/monero-activation/REVIEW-20261008.md) retains remaining activation questions.

## Phase 1 progress

Source characterization, reproducible profiling and the hardened upstream runner are retained. **P1-05 same-process warmup and timestamped hashing is implemented and validated**, commit `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`, integrated on main at `960b8b5`. See [P1-05 validation](docs/validation/p1-05/INTEGRATION.md).

**P1-06S power-data import is independently accepted software.** Review repaired three malformed-input failure-report defects in [merged PR #17](https://github.com/jliu67/OpenRandomX/pull/17), integration `973cd0d94f987ad4a46b85f7b6d66170104c64a1`; task #13 is closed as completed. The repaired importer passes 64 tests and an independent numerical/error-report audit. Final integration CI passes 219 Python tests, 107 upstream tests, six native steady controls, 39 exact native/QEMU RandomX checks and nine Linux runtime controls each; optional hardware AES remains explicitly skipped. [Evidence](docs/validation/m3-fs/RUNTIME-CI.md) records exact runs and source identities. All power joins used synthetic traces; [software acceptance](docs/validation/p1-06s/PATCH-REVIEW-20261008.md) does not certify physical measurements.

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
# Offline power-schema tests; synthetic inputs, NOT measured power:
python3 -m unittest discover -s tests -p test_power_import.py -v
```

Full-dataset known-reference controls and `native_steady.py` allocate the full dataset (over 2 GiB).
Run them only through the designated immutable local runner **after verified cutover**, with a reviewed
owner-local request and fresh persistent execution ID. Retain these scientific commands in that request:

```bash
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --nonces 1000 --repeats 1
# Optional same-process adapter and full-dataset native controls:
bash scripts/build_steady.sh
python3 tests/native_steady.py
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
