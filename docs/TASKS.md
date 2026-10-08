# OpenRX project board

Updated 2026-10-08 UTC. This file is the durable overview; GitHub issues hold discussion and session claims. Status reflects evidence, not intention. No other agents have been launched or assigned by this session.

## Phase 1 / M1

| ID | Work item | Status | Owner / handoff | Acceptance / evidence |
|---|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | ChatGPT, completed this session | [Report](PHASE1.md), reproducible [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Harden runner and add regression coverage | DONE | ChatGPT, completed this session | Commit `360a925`; 42 tooling tests pass locally and in CI |
| P1-03 | Integrated native correctness controls | DONE for CI host; target-host repeat READY | Next hardware agent unclaimed | 171 vendor files verified; 107 upstream tests; both full-dataset controls; [CI evidence](validation/phase1/README.md) |
| P1-04 | Known-host v1/v2 thread and AES matrix | BLOCKED: benchmark host access | Unclaimed; claim on [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Fixed settings, correct controls, balanced order, sufficient durations, all repeats/raw logs |
| P1-05 | Same-process warmup and exact hashing interval markers | READY for scoped implementation/review | Unclaimed; coordinate on #1 | Separate adapter or explicit reviewed patch; preserve hashes; timestamped interval excludes initialization |
| P1-06 | Time-aligned wall-power measurement | BLOCKED: meter/host/instrumentation | Unclaimed; coordinate on #1 | Declared whole-system boundary, synchronized samples, uncertainty and hashes/J from measured energy |
| P1-07 | Dynamic bottleneck attribution | BLOCKED: controlled host/counters | Unclaimed; coordinate on #1 | Dynamic instruction/cache/stall evidence with event limitations; no proxy from opcode probabilities |

**M1 remains OPEN.** A passing CI run is correctness evidence, not a completed measured efficiency baseline. Code for P1-02 uses schema version 2; warmup records are excluded from measurement summaries.

## Existing research queue (preserved)

| Issue | Work item | Status / dependency |
|---|---|---|
| [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Measured native baseline | Partial; Phase 1 subtasks above |
| [#2](https://github.com/jliu67/OpenRandomX/issues/2) | X5 / SG2042 evidence | Open, unclaimed; requires primary board/chip evidence |
| [#3](https://github.com/jliu67/OpenRandomX/issues/3) | Core and simulator selection | Open, unclaimed; no architecture optimization before baseline/model gates |
| [#4](https://github.com/jliu67/OpenRandomX/issues/4) | Monero network activation | Open, unclaimed; recheck current primary sources |

## Collaboration protocol

Before work, read AGENTS.md, the memory files, this board, the relevant experiment and current issue comments. Post a session-scoped claim with agent identity, base commit, exact files/scope, and acceptance criteria. Do not assume an old claim means an agent is still running. For overlapping changes use separate branches/PRs and agree file ownership; do not rewrite another agent's changes.

At handoff, record tested commands, failures, evidence class, commit/run links, blockers and the next executable step. Update STATE.md and append SESSION_LOG.md; keep consequential decisions in DECISIONS.md. Mark the claim completed, released or blocked. Refresh the remote head before publishing; use expected-head checks and never force-push over concurrent work.

The most recent handoff is [memory/HANDOFF.md](../memory/HANDOFF.md). Routine scoped research/code is authorized; purchases, paid compute, account/visibility changes and fabricated results are not.

## Communication infrastructure

| ID | Work item | Status | Evidence / handoff |
|---|---|---|---|
| COMM-01 | GitHub message board, inboxes, templates, claims and routing | DONE | [Hub #5](https://github.com/jliu67/OpenRandomX/issues/5), [implementation task #6](https://github.com/jliu67/OpenRandomX/issues/6), commit `d3c503a`, [45 tests and live validation](validation/communication/README.md) |
| COMM-02 | Autonomous AI worker execution | NOT CONFIGURED; separate authorization/setup required | Communication does not launch models; no runtime, model secrets, paid service or external agent was provisioned |

Read [COMMUNICATION.md](COMMUNICATION.md). New task/message templates enroll writer-authored issues; `/openrx route ROLE` opts an existing issue in without replacing its content. Inbox labels are cached routing views; consult the full thread and actual claim expiry before work. Existing issues #1–#4 retain their prior state and discussion. Infrastructure completion does not complete M1 or bypass scientific evidence gates.
