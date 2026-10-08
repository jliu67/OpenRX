# OpenRX project board

Updated 2026-10-08 UTC after decentralizing communications. **GitHub task issues and their first-line command comments are the authoritative task claim/status record; this Markdown file is only an evidence-backed milestone summary.** Agents choose work autonomously; there are no assigned roles or coordinator. Read [protocol v2](COMMUNICATION.md).

## Phase 1 / M1

| ID | Work item | Status | Acceptance / evidence |
|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | [Report](PHASE1.md), [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Upstream runner hardening | DONE | Commit `360a925`; original 42 tooling tests retained |
| P1-03 | Native correctness controls | DONE for CI; target-host repeat READY | 171 vendor files, 107 upstream tests, both full-dataset references |
| P1-04 | Controlled-host v1/v2 thread/AES matrix | [#8](https://github.com/jliu67/OpenRandomX/issues/8) BLOCKED: host access | Fixed settings, controls, balanced order, sufficient duration, all raw repeats |
| P1-05 | Same-process warmup and hashing interval markers | DONE — merged on main at `960b8b5`; see historical [#9](https://github.com/jliu67/OpenRandomX/issues/9) | `59b469c`; [adapter](../benchmarks/steady/README.md); [64 tooling / 107 upstream / 6 native tests](validation/p1-05/README.md) |
| P1-06S | Power-sample importer and validator | [#13](https://github.com/jliu67/OpenRandomX/issues/13) READY; not implemented | Explicit units/boundary/clock mapping; reject gaps and absent coverage; tested integration; synthetic data labeled |
| P1-06 | Time-aligned wall-power measurement | [#10](https://github.com/jliu67/OpenRandomX/issues/10) BLOCKED: #8, #13, host/meter | Real synchronized readings, physical boundary, uncertainty and completed hashes/measured joules |
| P1-07 | Dynamic bottleneck attribution | [#11](https://github.com/jliu67/OpenRandomX/issues/11) BLOCKED: #8, controlled host/counters | Dynamic instruction/cache/stall evidence, event limitations and overhead |

**M1 remains OPEN.** P1-05 is instrumentation, not a completed performance/efficiency experiment. Its four CI configurations are correctness controls; three workers on two exposed logical CPUs are not scaling evidence. The old upstream runner and new static-stride batch adapter have different overhead, so do not mix their rates. Clock brackets alone do not establish meter synchronization. Power stays null.

Parent milestone [#1](https://github.com/jliu67/OpenRandomX/issues/1) is a discussion/acceptance gate, **not** a shared editing lease: claim the appropriate independent child task #8, #10, #11 or #13. P1-05 was merged after our #9 review issue was opened; #9 is historical, not new work. Independent research issues #2–#4 can be claimed separately. No other agents are implied to be running by this summary.

## Existing research queue

| Issue | Work item | Status |
|---|---|---|
| [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Measured native baseline | Partial; tasks above |
| [#2](https://github.com/jliu67/OpenRandomX/issues/2) | X5 / SG2042 evidence | Open; primary board/chip evidence needed |
| [#3](https://github.com/jliu67/OpenRandomX/issues/3) | Core/simulator selection | Open; preserve baseline/model gates |
| [#4](https://github.com/jliu67/OpenRandomX/issues/4) | Monero activation | Open; verify primary current sources |

## Communication infrastructure

| ID | Work item | Status | Evidence / handoff |
|---|---|---|---|
| COMM-01 | GitHub message board, inboxes, templates, claims and routing | DONE | [Hub #5](https://github.com/jliu67/OpenRandomX/issues/5), [implementation task #6](https://github.com/jliu67/OpenRandomX/issues/6), commit `d3c503a`, [45 tests and live validation](validation/communication/README.md) |
| COMM-02 | Autonomous AI worker execution | NOT CONFIGURED; separate authorization/setup required | Communication does not launch models; no runtime, model secrets, paid service or external agent was provisioned |

The protocol v2 retains the original router history, but all agents now use the **shared** task pool. `/openrx join` enrolls old issues; legacy `/openrx route ROLE` is accepted only as an alias for joining the common pool. Obsolete role labels are cleared when enrolled threads are reconciled. Existing comments remain intact. Labels and receipts are projections, not separate owners.

## Collaboration and handoff

Read AGENTS, memory, the protocol, hub #5 and the current task before work. Record session identity, base commit, files/scope and acceptance. For enrolled tasks use the command protocol and verify a matching unexpired receipt before assuming ownership. Coordinate overlaps explicitly or through separate branches/PRs. A lease is not a Git lock or proof an agent is running.

Keep command comments append-only; never execute arbitrary message prose. Preserve old sessions/decisions, update STATE and HANDOFF, and link actual commands, tests, failures, commits and artifacts with retention caveats. Refresh remote HEAD and use non-force expected-head updates; do not overwrite concurrent work. Release/block/review claims at handoff. No automatic spending, account changes or invented results.

The [current handoff](../memory/HANDOFF.md) links both historical packages. The next unblocked tooling task is [P1-06S #13](https://github.com/jliu67/OpenRandomX/issues/13). [M5 #12](https://github.com/jliu67/OpenRandomX/issues/12) is deliberately blocked by #1/#3 **and** the separately required M4 calibrated-model gate; no premature RTL optimization. Controlled host/PMU/meter access remains unresolved.

## Decentralized queue / dependency map (v2)

[Ready tasks](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Aready) · [Needs review](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Areview) · [Blocked](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Ablocked) · [Notes](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+label%3Aagent%3Amessage).

Phase 1 child issue graph: #8 (measured host baseline; external host blocker); #13 (power importer; ready); #10 (wall power; depends #8 and #13 plus instrument access); #11 (dynamic profiling; depends #8). #9 records already merged P1-05 work, now closed as completed, and must not trigger reimplementation. M4 calibration [#14](https://github.com/jliu67/OpenRandomX/issues/14) is gated by milestone #1 and simulator #3. M5 planning [#12](https://github.com/jliu67/OpenRandomX/issues/12) is gated by #1, #3 and the completed evidence-backed M4 issue #14. Older issues #2, #3 and #4 remain independent research tasks. The current issue receipt is the place to inspect active sessions; an unexpired claim does not prove ongoing execution.
