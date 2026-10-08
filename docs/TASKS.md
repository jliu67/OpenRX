# OpenRX project board

Updated 2026-10-08 UTC after P1-05 validation. This file is the durable overview; GitHub issues hold discussion and session claims. Status reflects evidence, not intention. No other agents have been launched or assigned by this session.

## Phase 1 / M1

| ID | Work item | Status | Owner / handoff | Acceptance / evidence |
|---|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | Prior ChatGPT session | [Report](PHASE1.md), reproducible [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Harden upstream runner and regression coverage | DONE | Prior ChatGPT session | Commit `360a925`; original 42 tooling tests retained |
| P1-03 | Integrated native correctness controls | DONE for CI host; target-host repeat READY | Next hardware agent unclaimed | 171 vendor files verified; 107 upstream tests; both upstream full-dataset controls; new CI also passes |
| P1-04 | Known-host v1/v2 thread and AES matrix | BLOCKED: controlled benchmark host access | Unclaimed; claim on [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Fixed settings, correct controls, balanced order, sufficient durations, all repeats/raw logs |
| P1-05 | Same-process warmup and hashing interval markers | DONE | ChatGPT; session claim released at handoff | Commit `59b469c`; [adapter protocol](../benchmarks/steady/README.md); [validation](validation/p1-05/README.md); 64 tooling + 107 upstream + 6 native tests passed |
| P1-06S | Power-sample import and validation software | READY for implementation; NOT done | Unclaimed; next unblocked software task | Declared CSV/schema and clock mapping; reject missing coverage/gaps/clock jumps; tested integration/units/boundary; synthetic tests clearly labeled |
| P1-06 | Time-aligned wall-power measurement | BLOCKED: meter/host plus P1-06S | Unclaimed; coordinate on #1 | Declared whole-system boundary, synchronized real samples, uncertainty and hashes/J from measured energy |
| P1-07 | Dynamic bottleneck attribution | BLOCKED: controlled host/counters | Unclaimed; coordinate on #1 | Dynamic instruction/cache/stall evidence with event limitations; no proxy from opcode probabilities |

**M1 remains OPEN.** P1-05 closes the instrumentation task, not the measured hardware/efficiency experiment. Its four hosted correctness configurations are not P1-04. The three-worker case ran on a runner exposing two logical CPUs, so it must not be used as scaling evidence.

The original `scripts/benchmark.py` keeps schema 2 and separate-process warmups. New `scripts/steady_benchmark.py` / `build/steady/openrx-steady` is a separate, opt-in path with persistent dataset/VMs/workers and explicit timestamps. Its scheduling and batch tail differ from the upstream harness; compare configurations within one harness, not mixed throughput figures. Clock brackets do not establish meter synchronization. Power fields remain null.

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
