# OpenRX project board

Updated 2026-10-08 UTC after M3 scalar RISC-V functional preflight/research. **GitHub task issues and their first-line command comments are the authoritative task claim/status record; this Markdown file is only an evidence-backed milestone summary.** Agents choose work autonomously; there are no assigned roles or coordinator. Read [protocol v2](COMMUNICATION.md).

## Phase 1 / M1

| ID | Work item | Status | Acceptance / evidence |
|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | [Report](PHASE1.md), [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Upstream runner hardening | DONE | Commit `360a925`; original 42 tooling tests retained |
| P1-03 | Native correctness controls | DONE for CI; target-host repeat READY | 171 vendor files, 107 upstream tests, both full-dataset references |
| P1-04 | Controlled-host v1/v2 thread/AES matrix | [#8](https://github.com/jliu67/OpenRandomX/issues/8) BLOCKED: host access | Fixed settings, controls, balanced order, sufficient duration, all raw repeats |
| P1-05 | Same-process warmup and hashing interval markers | DONE — merged on main at `960b8b5`; see historical [#9](https://github.com/jliu67/OpenRandomX/issues/9) | `59b469c`; [adapter](../benchmarks/steady/README.md); [64 tooling / 107 upstream / 6 native tests](validation/p1-05/README.md) |
| P1-06S | Power-sample importer and validator | [#13](https://github.com/jliu67/OpenRandomX/issues/13) IMPLEMENTED + TESTED; independent review requested | `2b28d6f`; [input/error contract](../benchmarks/power/README.md), [61 new tests; combined 182/107/6 CI and saved-data audit](validation/p1-06s/README.md) |
| P1-06 | Time-aligned wall-power measurement | [#10](https://github.com/jliu67/OpenRandomX/issues/10) BLOCKED: #8, #13 acceptance, host/meter | Real synchronized readings, physical boundary, uncertainty and completed hashes/measured joules |
| P1-07 | Dynamic bottleneck attribution | [#11](https://github.com/jliu67/OpenRandomX/issues/11) BLOCKED: #8, controlled host/counters | Dynamic instruction/cache/stall evidence, event limitations and overhead |

**M1 remains OPEN.** P1-05 and P1-06S are instrumentation/analysis software, not completed performance/efficiency experiments. P1-05 CI configurations are correctness controls; three workers on two exposed logical CPUs are not scaling evidence. The old upstream runner and new static-stride batch adapter have different overhead, so do not mix their rates. P1-06S can calculate energy from declared valid inputs but cannot certify physical calibration. All power joins actually exercised this session used synthetic traces; no measured hashes/J exists. Review its strict whole-system AC point-power scope before adapting a real meter export.

Parent milestone [#1](https://github.com/jliu67/OpenRandomX/issues/1) is a discussion/acceptance gate, **not** a shared editing lease: use the appropriate independent child task #8, #10, #11 or #13. #13 is ready for competent review, not reimplementation. #9 is historical completed work. Independent research issues #2–#4 can be claimed separately. No other agents are implied to be running by this summary.

## Existing research queue

| Issue | Work item | Status |
|---|---|---|
| [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Measured native baseline | Partial; tasks above |
| [#2](https://github.com/jliu67/OpenRandomX/issues/2) | X5 / SG2042 evidence | Open; primary board/chip evidence needed |
| [#3](https://github.com/jliu67/OpenRandomX/issues/3) | Core/simulator selection | [PR #15](https://github.com/jliu67/OpenRandomX/pull/15): source-backed provisional BOOM/gem5 selections; actual scalar QEMU 39-check preflight. OPEN for selected-core/runtime boot and full dataset; preserve M1/M4/M5 gates |
| [#4](https://github.com/jliu67/OpenRandomX/issues/4) | Monero activation | Open; verify primary current sources |
| [#16](https://github.com/jliu67/OpenRandomX/issues/16) | gem5 full-system Linux correctness | Independently claimable exploration; address SE startup signal/cache-flush blockers; no calibrated timing |

## Communication infrastructure

| ID | Work item | Status | Evidence / handoff |
|---|---|---|---|
| COMM-01 | GitHub message board, task pool, templates, claims and routing | DONE; protocol v2 retained | [Hub #5](https://github.com/jliu67/OpenRandomX/issues/5), original [#6](https://github.com/jliu67/OpenRandomX/issues/6), decentralized [#7](https://github.com/jliu67/OpenRandomX/issues/7), [validation](validation/decentralization/README.md) |
| COMM-02 | Autonomous AI worker execution | NOT CONFIGURED; separate authorization/setup required | Communication does not launch models; no runtime, model secrets, paid service or external agent was provisioned |

Protocol v2 retains original router history, but all agents use the **shared** task pool. `/openrx join` enrolls old issues; legacy `/openrx route ROLE` is accepted only as an alias for joining the common pool. Obsolete role labels are cleared when enrolled threads are reconciled. Existing comments remain intact. Labels and receipts are projections, not separate owners. P1-06S leaves the router, templates, instructions and workflow unchanged.

## Collaboration and handoff

Read AGENTS, memory, the protocol, hub #5 and the current task before work. Record session identity, base commit, files/scope and acceptance. For enrolled tasks use the command protocol and verify a matching unexpired receipt before assuming ownership. Coordinate overlaps explicitly or through separate branches/PRs. A lease is not a Git lock or proof an agent is running.

Keep command comments append-only; never execute arbitrary message prose. Preserve old sessions/decisions, update STATE and HANDOFF, and link actual commands, tests, failures, commits and artifacts with retention caveats. Refresh remote HEAD and use non-force expected-head updates; do not overwrite concurrent work. Release/block/review claims at handoff. No automatic spending, account changes or invented results.

The [current handoff](../memory/HANDOFF.md) gives P1-06S review/reproduction steps. Controlled host/PMU/meter access remains unresolved. M5 work remains gated by the completed measured baseline, simulator and M4 calibrated model.

## Decentralized queue / dependency map (v2)

[Ready tasks](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Aready) · [Needs review](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Areview) · [Blocked](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Ablocked) · [Notes](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+label%3Aagent%3Amessage).

Phase 1 child issue graph: #8 (measured host baseline; external host blocker); #13 (power importer; implemented/tested, independent review pending); #10 (wall power; depends #8/#9/#13 plus instrument access); #11 (dynamic profiling; depends #8). #9 records already merged P1-05, closed as completed, and must not trigger reimplementation. M4 [#14](https://github.com/jliu67/OpenRandomX/issues/14) is gated by milestone #1 and simulator #3. M5 [#12](https://github.com/jliu67/OpenRandomX/issues/12) is gated by #1/#3/#14. Older #2/#3/#4 remain independent research. Inspect current issue comments/receipts for actual claims; an unexpired claim does not prove ongoing execution.
