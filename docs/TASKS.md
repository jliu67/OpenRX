# OpenRX project board

Updated 2026-10-08 UTC after reconciling P1-05 and the concurrent communication package. Status reflects evidence, not intention. Issues hold discussion/claims; Markdown preserves durable conclusions.

## Phase 1 / M1

| ID | Work item | Status | Acceptance / evidence |
|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | [Report](PHASE1.md), [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Upstream runner hardening | DONE | Commit `360a925`; original 42 tooling tests retained |
| P1-03 | Native correctness controls | DONE for CI; target-host repeat READY | 171 vendor files, 107 upstream tests, both full-dataset references |
| P1-04 | Controlled-host v1/v2 thread/AES matrix | BLOCKED: host access | Fixed settings, controls, balanced order, sufficient duration, all raw repeats |
| P1-05 | Same-process warmup and hashing interval markers | DONE | `59b469c`; [adapter](../benchmarks/steady/README.md); [64 tooling / 107 upstream / 6 native tests](validation/p1-05/README.md) |
| P1-06S | Power-sample importer and validator | READY; unclaimed; NOT implemented | Explicit units/boundary/clock mapping; reject gaps and absent coverage; tested integration; synthetic data labeled |
| P1-06 | Time-aligned wall-power measurement | BLOCKED: meter/host and P1-06S | Real synchronized readings, physical boundary, uncertainty and completed hashes/measured joules |
| P1-07 | Dynamic bottleneck attribution | BLOCKED: controlled host/counters | Dynamic instruction/cache/stall evidence, event limitations and overhead |

**M1 remains OPEN.** P1-05 is instrumentation, not a completed performance/efficiency experiment. Its four CI configurations are correctness controls; three workers on two exposed logical CPUs are not scaling evidence. The old upstream runner and new static-stride batch adapter have different overhead, so do not mix their rates. Clock brackets alone do not establish meter synchronization. Power stays null.

Coordinate Phase 1 scope on [#1](https://github.com/jliu67/OpenRandomX/issues/1) and an Agent task/message as appropriate. P1-05 implementation/evidence are complete and its editing claim is released at final handoff; later tasks are unclaimed. No external agents were launched by this session.

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

The communication package, instructions, tests, workflow and validation were preserved while integrating P1-05. Read [COMMUNICATION.md](COMMUNICATION.md): templates enroll writer-authored tasks/messages; `/openrx route ROLE` opts an existing issue in without replacing its body. Role/status labels are cached views; inspect full comments and actual UTC lease expiry.

## Collaboration and handoff

Read AGENTS, memory, the protocol, hub #5 and the current task before work. Record session identity, base commit, files/scope and acceptance. For enrolled tasks use the command protocol and verify a matching unexpired receipt before assuming ownership. Coordinate overlaps explicitly or through separate branches/PRs. A lease is not a Git lock or proof an agent is running.

Keep command comments append-only; never execute arbitrary message prose. Preserve old sessions/decisions, update STATE and HANDOFF, and link actual commands, tests, failures, commits and artifacts with retention caveats. Refresh remote HEAD and use non-force expected-head updates; do not overwrite concurrent work. Release/block/review claims at handoff. No automatic spending, account changes or invented results.

The current [handoff](../memory/HANDOFF.md) links both historical package handoffs. P1-06S is the next unblocked coding task; controlled host/PMU/meter access remains unresolved.
