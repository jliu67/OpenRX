# Current state

Stage: M0 complete; Phase 1 source/tooling work package complete; **M1 measured hardware baseline still open**.

Project name: OpenRX. GitHub remote remains private `jliu67/OpenRandomX`; repository administrative name was not changed.

## Completed

- Official RandomX v2.0.1 source pinned at `aaafe71322df6602c21a5c72937ac284724ae561`, unmodified; same release supports v1/v2.
- Foundation source manifest, scripts, CI, memory, evidence rules and experiments retained.
- [Phase 1 workload report](../docs/PHASE1.md) and reproducible [static profile](../benchmarks/profiles/pinned-v2.0.1.json).
- Benchmark runner schema 2: separated warmup records, balanced v1/v2 order, median/min/max and failure counts, minimum-duration checks, pinned-reference validation, integer/affinity safeguards, CPU/cgroup context.
- [Project board](../docs/TASKS.md), issue #1 communication and [agent handoff](HANDOFF.md) now track completed work, ownership, blockers and next commands.

## Validation and remote status

Original foundation validation remains in docs/VALIDATION.md and docs/validation/foundation/. The private remote was created and its original 213-file tree verified in the foundation session.

Implementation commit `360a9255703a28845a799cfcc1086d1fb84a2c48` is on main. Local tooling: 42 tests passed, no skips. Native integration: [GitHub Actions run 37719337133](https://github.com/jliu67/OpenRandomX/actions/runs/37719337133) passed source integrity (171 files), the same 42 tooling tests, deterministic profile reproduction, native build, all 107 upstream tests (no skips), both light smoke runs, both full-dataset reference controls, and artifact upload. See [Phase 1 validation](../docs/validation/phase1/README.md).

No vendored source changed. No controlled hardware throughput/AES/thread matrix, wall-power samples, dynamic bottleneck attribution, RISC-V simulation or RTL result has been obtained. CI controls were one repetition per algorithm and are not a performance/efficiency baseline.

## Next actions and blockers

1. Hardware-capable agent: claim P1-04 on issue #1; identify the actual host, repeat known references, then run the balanced controlled matrix in docs/PHASE1.md. Host access is currently unresolved.
2. Tooling agent: P1-05 is ready for a separate adapter or reviewed patch providing same-process warmup and exact steady-state interval markers. Current warmups are separate-process preconditioning only.
3. Complete P1-06 with real synchronized wall-power readings; no meter access or energy claims exist yet.
4. Complete P1-07 dynamic profiling on a controlled host; record counter support and collection overhead.
5. Continue issues #2/#4 primary-source hardware/network verification and #3 simulator feasibility without bypassing the roadmap gates.

Routine scoped code/research commits are authorized. Do not spend money, alter account/visibility settings, fabricate results or claim agents are running between sessions. The completed session claim is released; future agents must inspect current issue comments and remote HEAD before editing.

## GitHub communication package — 2026-10-08 UTC

Implemented on main at `d3c503a5ad4154ba50e6f38119bb904cb41322d8`: [message board #5](https://github.com/jliu67/OpenRandomX/issues/5), task/message templates, role/status inbox labels, four-hour session claims and a deterministic Actions router. Read [docs/COMMUNICATION.md](../docs/COMMUNICATION.md) before using commands. Existing research issues and all Phase 1 evidence/gates are preserved.

Validation: 45 new communication tests passed locally and in [router run 37722591259](https://github.com/jliu67/OpenRandomX/actions/runs/37722591259). Live routing accepted the installation claim and rejected a conflicting test session; repeated reconciliation did not duplicate the state receipt. [Foundation/native CI run 37722591236](https://github.com/jliu67/OpenRandomX/actions/runs/37722591236) also completed successfully. Details and limits: [communication validation](../docs/validation/communication/README.md).

No autonomous model worker, external queue, scheduled polling, model credential or paid service was provisioned. Inbox roles do not imply active agents. The current installation/handoff claim lifecycle is recorded on [#6](https://github.com/jliu67/OpenRandomX/issues/6); no continuing worker is claimed by this package. Invoke an authorized agent to read an inbox and act. M1 remains open.
