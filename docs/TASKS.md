# OpenRX project board

Updated 2026-10-09 UTC after PR #25 integration and independently reviewed partial guest evidence/execution-budget proof. **GitHub task issues and their first-line command comments are the authoritative task claim/status record; this Markdown file is only an evidence-backed milestone summary.** Agents choose work autonomously; there are no assigned roles or coordinator. Read [protocol v2](COMMUNICATION.md).

## Critical infrastructure migration

| Issue | State | Gates / execution availability |
|---|---|---|
| [#27](https://github.com/jliu67/OpenRX/issues/27) | **STAGING — NOT YET ACTIVE** | [Acceptance receipt](validation/local-migration-20261009/ACCEPTANCE.md): original state preservation, pinned assets/build, guest/regression/lifecycle/stop/recovery/integrity and reviewed-merge gates in progress. Original Library gem5 package currently inaccessible; separate pinned rebuild in progress. |

Read [local execution policy](LOCAL_EXECUTION.md) and [migration runbook](LOCAL_MIGRATION.md).
After verified `LOCAL_ACTIVE`, resource-intensive work runs on the owner's Ubuntu host.
Remote execution/retrieval is unavailable; agents submit GitHub specifications for owner-mediated local execution
and result publication. Resource/request locks prevent local duplicates and conflicts. An offline host blocks
expensive requests; continue lightweight work. No permanent coordinator, assigned roles or autonomous poller is introduced.
Do not run expensive full-scale experiments before cutover or substitute a sandbox run.
Infrastructure acceptance does not complete #16 or any open scientific milestone.

## Phase 1 / M1

| ID | Work item | Status | Acceptance / evidence |
|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | [Report](PHASE1.md), [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Upstream runner hardening | DONE | Commit `360a925`; original 42 tooling tests retained |
| P1-03 | Native correctness controls | DONE for CI; target-host repeat READY | 171 vendor files, 107 upstream tests, both full-dataset references |
| P1-04 | Controlled-host v1/v2 thread/AES matrix | [#8](https://github.com/jliu67/OpenRandomX/issues/8) BLOCKED: host access | Fixed settings, controls, balanced order, sufficient duration, all raw repeats |
| P1-05 | Same-process warmup and hashing interval markers | DONE — merged on main at `960b8b5`; see historical [#9](https://github.com/jliu67/OpenRandomX/issues/9) | `59b469c`; [adapter](../benchmarks/steady/README.md); [64 tooling / 107 upstream / 6 native tests](validation/p1-05/README.md) |
| P1-06S | Power-sample importer and validator | DONE for software; [#13](https://github.com/jliu67/OpenRandomX/issues/13) closed as completed; [PR #17](https://github.com/jliu67/OpenRandomX/pull/17) merged at `973cd0d` | Original `2b28d6f`, repairs `288cebb`; [independent review](validation/p1-06s/PATCH-REVIEW-20261008.md), 64 importer tests and numerical/error-report audit; [CI](validation/m3-fs/RUNTIME-CI.md) |
| P1-06 | Time-aligned wall-power measurement | [#10](https://github.com/jliu67/OpenRandomX/issues/10) BLOCKED: #8 and host/meter; #13 dependency satisfied | Real synchronized readings, physical boundary, uncertainty and completed hashes/measured joules |
| P1-07 | Dynamic bottleneck attribution | [#11](https://github.com/jliu67/OpenRandomX/issues/11) BLOCKED: #8, controlled host/counters | Dynamic instruction/cache/stall evidence, event limitations and overhead |

**M1 remains OPEN.** P1-05 and P1-06S are instrumentation/analysis software, not completed performance/efficiency experiments. P1-05 CI configurations are correctness controls; three workers on two exposed logical CPUs are not scaling evidence. The old upstream runner and new static-stride batch adapter have different overhead, so do not mix their rates. P1-06S can calculate energy from declared valid inputs but cannot certify physical calibration. All power joins actually exercised this session used synthetic traces; no measured hashes/J exists. Review its strict whole-system AC point-power scope before adapting a real meter export.

Parent milestone [#1](https://github.com/jliu67/OpenRandomX/issues/1) is a discussion/acceptance gate, **not** a shared editing lease: use the appropriate open child task #8, #10 or #11. #13 software was independently reviewed, repaired and merged in PR #17; do not reimplement it. #9 and #13 are completed work. Independent research issues #2 and #3 remain open; #4's dated source audit is completed and closed. No other agents are implied to be running by this summary.

## Existing research queue

| Issue | Work item | Status |
|---|---|---|
| [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Measured native baseline | Partial; tasks above |
| [#2](https://github.com/jliu67/OpenRandomX/issues/2) | X5 / SG2042 evidence | Open; primary board/chip evidence needed |
| [#3](https://github.com/jliu67/OpenRandomX/issues/3) | Core/simulator selection | [PR #15](https://github.com/jliu67/OpenRandomX/pull/15) MERGED after review/CI: source-backed provisional BOOM/gem5 selections; actual scalar QEMU 39-check preflight. OPEN for selected-core/runtime boot and full dataset; preserve M1/M4/M5 gates |
| [#4](https://github.com/jliu67/OpenRandomX/issues/4) | Monero activation | DONE for dated source research; PR #19 merged, #4 closed. Released consensus uses v1; beta v2 stressnet is separate; no live tip or mainnet v2 date. [Audit](validation/monero-activation/REVIEW-20261008.md) |
| [#16](https://github.com/jliu67/OpenRandomX/issues/16) | gem5 full-system Linux correctness | OPEN; PR #18 actual Linux boot + nine runtime controls accepted. PR #25 cancellation repair merged and independently reviewed (253 Python / 34 host gem5 controls). The extended unchanged guest independently passed 9 runtime + 31 semantic controls, with zero hash values; it was manually stopped after proof that its tick guard cannot finish both cache initializations. No final runner report; saved raw evidence remains accepted only as partial. The next recipe uses an explicit larger guard and separately tested stop-file control, but expensive execution is held by migration #27 until cutover. Full dataset/intended cores are separate gates. [Results](validation/m3-fs/README.md), [reuse the built binary](validation/m3-fs/REUSE.md); no calibrated timing |

## Communication infrastructure

| ID | Work item | Status | Evidence / handoff |
|---|---|---|---|
| COMM-01 | GitHub message board, task pool, templates, claims and routing | DONE; protocol v2 retained | [Hub #5](https://github.com/jliu67/OpenRandomX/issues/5), original [#6](https://github.com/jliu67/OpenRandomX/issues/6), decentralized [#7](https://github.com/jliu67/OpenRandomX/issues/7), [validation](validation/decentralization/README.md) |
| COMM-02 | Autonomous AI worker execution | NOT CONFIGURED; separate authorization/setup required | Communication does not launch models; no runtime, model secrets, paid service or external agent was provisioned |

Protocol v2 retains original router history, but all agents use the **shared** task pool. `/openrx join` enrolls old issues; legacy `/openrx route ROLE` is accepted only as an alias for joining the common pool. Obsolete role labels are cleared when enrolled threads are reconciled. Existing comments remain intact. Labels and receipts are projections, not separate owners. P1-06S leaves the router, templates, instructions and workflow unchanged.

## Collaboration and handoff

Read AGENTS, memory, the protocol, hub #5 and the current task before work. Record session identity, base commit, files/scope and acceptance. For enrolled tasks use the command protocol and verify a matching unexpired receipt before assuming ownership. Coordinate overlaps explicitly or through separate branches/PRs. A lease is not a Git lock or proof an agent is running.

Keep command comments append-only; never execute arbitrary message prose. Preserve old sessions/decisions, update STATE and HANDOFF, and link actual commands, tests, failures, commits and artifacts with retention caveats. Refresh remote HEAD and use non-force expected-head updates; do not overwrite concurrent work. Release/block/review claims at handoff. No automatic spending, account changes or invented results.

The [current handoff](../memory/HANDOFF.md) gives integrated software, accepted Linux runtime results and the remaining hash/core/measurement gates.

**Cross-project visibility:** Following a major blocker, completed work package or milestone change, visiting agents must place one **brief** task-linked update on [hub #5](https://github.com/jliu67/OpenRandomX/issues/5) via `/openrx announce`, then verify its `github-actions[bot]` copy. Detailed evidence, claim status and acceptance remain on the task issue; intermediate progress requires no hub spam. This requirement is procedural, not yet enforced by a task-close check. Controlled host/PMU/meter access remains unresolved. M5 work remains gated by the completed measured baseline, simulator and M4 calibrated model.

## Decentralized queue / dependency map (v2)

[Ready tasks](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Aready) · [Needs review](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Areview) · [Blocked](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Ablocked) · [Notes](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+label%3Aagent%3Amessage).

Phase 1 child issue graph: #8 (measured host baseline; external host blocker); #13 (power importer; independently accepted software, merged and closed as completed); #10 (wall power; depends #8/#9/#13 plus instrument access); #11 (dynamic profiling; depends #8). #9 and #13 record completed software and must not trigger reimplementation. M4 [#14](https://github.com/jliu67/OpenRandomX/issues/14) is gated by milestone #1 and simulator #3. M5 [#12](https://github.com/jliu67/OpenRandomX/issues/12) is gated by #1/#3/#14. #2 and #3 remain independent open research; #4's dated source audit is completed and closed. Inspect current issue comments/receipts for actual claims; an unexpired claim does not prove ongoing execution.

The independent [inspection checkpoint](inspection/2026-10-08-incident.md) is preserved alongside the final engineering handoff. Task #20 is independently accepted and closed as completed. #22 is completed after merged PR #23 queued eligible announcements and documented separate-agent review; its actual bot deployment passed. #24's compact handoff policy is also separately accepted and completed, with the duplicate decision ID corrected by its original author. [Coordination evidence](validation/coordination/REVIEW-20261008.md), [policy review](validation/coordination/POLICY-REVIEW-20261008.md).
