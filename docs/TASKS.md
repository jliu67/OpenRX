# OpenRX project board

## Current status — 2026-10-10

[Migration #27 is complete](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454): independently accepted `LOCAL_ACTIVE` and [explicit designated-host release](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817), after merged PRs #28 and #30. [Cleanup #31 / merged PR #32](https://github.com/jliu67/OpenRX/issues/31#issuecomment-6099136057) establishes GitHub-only progress publication: the editable migration checkout and disposable sync mirror were recoverably retired; sync stays disabled. Evidence-bound originals, pinned execution sources and computational assets remain retained.

These are verified GitHub closeout records, not a fresh host-health check. Every new execution still needs its reviewed request, current host/resource checks and existing admission gates. #16's complete unchanged RandomX matrix, full dataset and intended-core/SMP/BOOM gates remain open, as do M1–M5. Controlled measurement configuration/authorization, meter and PMU access are separate prerequisites. Dated CUTOVER_PENDING and pre-final records below are preserved history, not current migration blockers.

Updated 2026-10-10 UTC for completed infrastructure/publication closeout; scientific evidence remains unchanged. **GitHub task issues and their first-line command comments are the authoritative task claim/status record; this Markdown file is only an evidence-backed milestone summary.** Agents choose work autonomously; there are no assigned roles or coordinator. Read [protocol v2](COMMUNICATION.md).

## Execution infrastructure

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

| Issue | Dated technical state | Gate evidence |
|---|---|---|
| [#27](https://github.com/jliu67/OpenRX/issues/27) | CUTOVER_PENDING at 2026-10-10T08:41:07.234399+00:00 | [Technical receipt](validation/local-migration-20261009/ACCEPTANCE.md); expected guest/runtime9 accepted, broader stop: INDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim). Actual reviewed merge/LOCAL_ACTIVE/explicit release/final synchronization are pending at this snapshot. |

Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.

The [owner resource directive](LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
with swap where useful, retaining only measured necessary OS/agent headroom. Per-job allocations must
reflect current host load, memory availability and workload parallelism; 14 GiB is a candidate, not a
universal safe limit. Keep one payload slot and all migration/scientific gates. The old runner988 validation records retain their actual memory and manager-reported 200% CPUQuota.
A later CPU-delegation audit found that historical quota was not kernel-enforced; old property receipts
are preserved and do not prove CPU enforcement. The new CPU delegation configuration is additive.
CPU-delegation evidence: `independently reviewed CPU delegation f12aec1f/67de0d92 and actual runner kernel witness, docs/validation/local-migration-20261009/resource-kernel-20261010/index.json`. The approved owner-local-max-v1 candidate
uses CPU600%, memory no greater than min(14 GiB, fresh MemAvailable minus 1 GiB), optional lower positive
explicit budget, 2-GiB swap, Tasks256 and the same one-slot/45-second stop semantics. Admission must bind
current host metrics and recheck available headroom before launching. Exact new-release/kernel-budget
verification is recorded by the operational profile evidence; it is independently accepted for the exact installed release and tiny live proof below.

The operational implementation must check each payload's actual kernel CPU, memory, swap and task
limits, including effective ancestor ceilings, under admission/resource safeguards before launch. It must
fail closed on unavailable controllers, mismatched constraints, tighter inherited ceilings or lost fresh
memory headroom. Manager properties and controller availability alone do not establish enforcement.
The exact installed operational release enforces these per-payload kernel checks; the independent
resource proof below accepts the observed normal profile. Each future payload is checked again.

Operational resource-profile outcome/evidence: `INDEPENDENTLY ACCEPTED exact runner657 and normal-profile tiny execution20261010T083746Z-6bc7037f04ef: actual CPU600000/100000, RAM5637144576 bytes (5.25GiB selected from measured headroom), swap2147483648, tasks256, six-CPU affinity, no tighter visible ancestors; rc0 and receipt integrity verified. Independent review951622749d40a9bf467e48ee3f6581cc52393569b8db60c87e63d57bee8ee00b; resource-kernel-20261010/index.json`.
Operational release: `runner-v1-657b23f1`, SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`. The verified profile and immutable release are reconciled. This dated preactivation snapshot
retains the expensive-work hold until the explicit merge-bound release.

This infrastructure acceptance leaves #16's complete unchanged gem5 RandomX matrix/full dataset/
intended-core/SMP/BOOM and M1-M5 open. No calibrated timing, physical power, RTL, checkpoint resume,
whole-Codex-daemon termination, host reboot or complete offline/hermetic dependency closure is claimed.
Original Library binary remains unavailable; rebuilt binary retains its distinct identity. Preserve
failures/safety withdrawals, original scientific assets, exact guest oracles and milestone history.

## Phase 1 / M1

| ID | Work item | Status | Acceptance / evidence |
|---|---|---|---|
| P1-01 | Pinned workload anatomy and static profile | DONE | [Report](PHASE1.md), [profile](../benchmarks/profiles/pinned-v2.0.1.json) |
| P1-02 | Upstream runner hardening | DONE | Commit `360a925`; original 42 tooling tests retained |
| P1-03 | Native correctness controls | DONE for CI; target-host repeat READY | 171 vendor files, 107 upstream tests, both full-dataset references |
| P1-04 | Controlled-host v1/v2 thread/AES matrix | [#8](https://github.com/jliu67/OpenRandomX/issues/8) BLOCKED: controlled baseline configuration/authorization and current host verification; designated infrastructure accepted in #27 | Fixed settings, controls, balanced order, sufficient duration, all raw repeats |
| P1-05 | Same-process warmup and hashing interval markers | DONE — merged on main at `960b8b5`; see historical [#9](https://github.com/jliu67/OpenRandomX/issues/9) | `59b469c`; [adapter](../benchmarks/steady/README.md); [64 tooling / 107 upstream / 6 native tests](validation/p1-05/README.md) |
| P1-06S | Power-sample importer and validator | DONE for software; [#13](https://github.com/jliu67/OpenRandomX/issues/13) closed as completed; [PR #17](https://github.com/jliu67/OpenRandomX/pull/17) merged at `973cd0d` | Original `2b28d6f`, repairs `288cebb`; [independent review](validation/p1-06s/PATCH-REVIEW-20261008.md), 64 importer tests and numerical/error-report audit; [CI](validation/m3-fs/RUNTIME-CI.md) |
| P1-06 | Time-aligned wall-power measurement | [#10](https://github.com/jliu67/OpenRandomX/issues/10) BLOCKED: #8 and calibrated synchronized meter access; #9/#13 completed | Real synchronized readings, physical boundary, uncertainty and completed hashes/measured joules |
| P1-07 | Dynamic bottleneck attribution | [#11](https://github.com/jliu67/OpenRandomX/issues/11) BLOCKED: #8 and verified PMU/profiler access/permissions | Dynamic instruction/cache/stall evidence, event limitations and overhead |

**M1 remains OPEN.** P1-05 and P1-06S are instrumentation/analysis software, not completed performance/efficiency experiments. P1-05 CI configurations are correctness controls; three workers on two exposed logical CPUs are not scaling evidence. The old upstream runner and new static-stride batch adapter have different overhead, so do not mix their rates. P1-06S can calculate energy from declared valid inputs but cannot certify physical calibration. All power joins actually exercised this session used synthetic traces; no measured hashes/J exists. Review its strict whole-system AC point-power scope before adapting a real meter export.

Parent milestone [#1](https://github.com/jliu67/OpenRandomX/issues/1) is a discussion/acceptance gate, **not** a shared editing lease: use the appropriate open child task #8, #10 or #11. #13 software was independently reviewed, repaired and merged in PR #17; do not reimplement it. #9 and #13 are completed work. Independent research issues #2 and #3 remain open; #4's dated source audit is completed and closed. No other agents are implied to be running by this summary.

## Existing research queue

| Issue | Work item | Status |
|---|---|---|
| [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Measured native baseline | Partial; tasks above |
| [#2](https://github.com/jliu67/OpenRandomX/issues/2) | X5 / SG2042 evidence | Open; primary board/chip evidence needed |
| [#3](https://github.com/jliu67/OpenRandomX/issues/3) | Core/simulator selection | [PR #15](https://github.com/jliu67/OpenRandomX/pull/15) MERGED after review/CI: source-backed provisional BOOM/gem5 selections; actual scalar QEMU 39-check preflight. OPEN for selected-core/runtime boot and full dataset; preserve M1/M4/M5 gates |
| [#4](https://github.com/jliu67/OpenRandomX/issues/4) | Monero activation | DONE for dated source research; PR #19 merged, #4 closed. Released consensus uses v1; beta v2 stressnet is separate; no live tip or mainnet v2 date. [Audit](validation/monero-activation/REVIEW-20261008.md) |
| [#16](https://github.com/jliu67/OpenRandomX/issues/16) | gem5 full-system Linux correctness | OPEN; PR #18 actual Linux boot + nine runtime controls accepted. PR #25 cancellation repair merged and independently reviewed (253 Python / 34 host gem5 controls). The extended unchanged guest independently passed 9 runtime + 31 semantic controls, with zero hash values; it was manually stopped after proof that its tick guard cannot finish both cache initializations. No final runner report; saved raw evidence remains accepted only as partial. The next recipe uses an explicit larger guard and separately tested stop-file control, and migration #27 is now complete under its [final acceptance](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454). Any next attempt requires reviewed current source/runner/input bindings, a new local request and fresh admission/resource checks; this summary does not authorize execution. Full dataset/intended cores are separate gates. [Results](validation/m3-fs/README.md), [reuse the built binary](validation/m3-fs/REUSE.md); no calibrated timing |

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

**Cross-project visibility:** Following a major blocker, completed work package or milestone change, visiting agents must place one **brief** task-linked update on [hub #5](https://github.com/jliu67/OpenRandomX/issues/5) via `/openrx announce`, then verify its `github-actions[bot]` copy. Detailed evidence, claim status and acceptance remain on the task issue; intermediate progress requires no hub spam. This requirement is procedural, not yet enforced by a task-close check. Designated-host infrastructure is accepted; controlled baseline readiness and PMU/meter access remain separate unresolved gates. M5 work remains gated by the completed measured baseline, simulator and M4 calibrated model.

## Decentralized queue / dependency map (v2)

[Ready tasks](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Aready) · [Needs review](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Areview) · [Blocked](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Ablocked) · [Notes](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+label%3Aagent%3Amessage).

Phase 1 child issue graph: #8 (measured host baseline; controlled configuration/authorization and current host verification still required); #13 (power importer; independently accepted software, merged and closed as completed); #10 (wall power; depends #8/#9/#13 plus instrument access); #11 (dynamic profiling; depends #8). #9 and #13 record completed software and must not trigger reimplementation. M4 [#14](https://github.com/jliu67/OpenRandomX/issues/14) is gated by milestone #1 and simulator #3. M5 [#12](https://github.com/jliu67/OpenRandomX/issues/12) is gated by #1/#3/#14. #2 and #3 remain independent open research; #4's dated source audit is completed and closed. Inspect current issue comments/receipts for actual claims; an unexpired claim does not prove ongoing execution.

The independent [inspection checkpoint](inspection/2026-10-08-incident.md) is preserved alongside the final engineering handoff. Task #20 is independently accepted and closed as completed. #22 is completed after merged PR #23 queued eligible announcements and documented separate-agent review; its actual bot deployment passed. #24's compact handoff policy is also separately accepted and completed, with the duplicate decision ID corrected by its original author. [Coordination evidence](validation/coordination/REVIEW-20261008.md), [policy review](validation/coordination/POLICY-REVIEW-20261008.md).
