# OpenRX project board

Current compiler compatibility: [Icarus 12 compile view](../rtl/execute/DIVSQRT.md#icarus-12-compatibility-correction--2026-10-13) removes one redundant declaration in a generated copy; original IP/hardware bytes and Yosys sources remain unchanged. All 12 local RTL records/native fixtures match; corrected hosted checks and independent review remain required.

## Native division and square root — task #60, 2026-10-13

[Task #60](https://github.com/jliu67/OpenRX/issues/60) extends independently
accepted, unmerged [PR #59](https://github.com/jliu67/OpenRX/pull/59#pullrequestreview-5501107360)
at `ce788d11285c901b52fd3cf0b450489d13b3f2f5` on a separate stacked draft.
All 29 native instruction families / 256 raw encodings now execute, including
masked FDIV_M and FSQRT_R. Reviewed PR #55/#57/#59 and main remain unchanged.
New code requires independent review; no merge is authorized. Complete VM/hash,
selected core, physical memories and calibrated timing/power remain open.
[Design](../rtl/execute/DIVSQRT.md) and [EXP-009](../experiments/EXP-009-native-divsqrt.md)
bind reproducible tests and actual mapping. Earlier component summaries retain
their dated source/evidence context; historical subset test drivers require their
accepted frozen heads. Current reproduction uses `scripts/test_divsqrt_execute.py`.

Twelve RTL and eleven applicable mapped modes pass: 13,312 balanced native
primitive vectors per scalar/shared/parallel variant, 2,560 balanced mapped
corner vectors, 2,856 native retirements including 152 divisions / 146 square
roots, 418 loads / 82 stores / 64 tail writes, four chains/aliases and all 2 MiB.
All rounding modes, DAZ/FTZ, IEEE exception bits, masks, held/reset/stale behavior
match. Shared/parallel divide-sqrt units are 8,690/12,942
generic cells and 779/558 flops. Controlled integration clocks
are 45,671/28,443 ideal and 62,637/45,409 stalled; shared adds 17,228 clocks.
Complete default mapping is 274,346 cells / 10,504 flops.
Operand latency is variable; these fixtures and generic gates establish no physical PPA or full-hash throughput.

## Current floating execution extension — task #58, 2026-10-13

[PR #55](https://github.com/jliu67/OpenRX/pull/55#pullrequestreview-5498804300)
and [PR #57](https://github.com/jliu67/OpenRX/pull/57#pullrequestreview-5499497883)
are independently accepted at `2b14e4f9` / `d62c4495` and remain draft/unmerged.
[Task #58](https://github.com/jliu67/OpenRX/issues/58) adds exact native floating
add/subtract/multiply, bit operations and CFROUND on a separate stacked temporary
branch. Proven licensed HardFloat1/8086-SSE bytes supply arithmetic; native masks,
rounding, DAZ/FTZ and held/reset behavior remain exact. Division/square root still
trap. This new work requires independent review; no merge is authorized. Earlier
summaries retain dated publication context. All pinned assets and serialized
compute rules remain; full VM/hash, selected core and calibrated physical PPA
remain open. [Design](../rtl/execute/FLOATING.md) records concrete interfaces and validation.

## Current stacked extension — task #56, 2026-10-13

[PR #55](https://github.com/jliu67/OpenRX/pull/55#pullrequestreview-5498804300) is
independently accepted at `2b14e4f9` and remains draft/unmerged. [Task #56](https://github.com/jliu67/OpenRX/issues/56)
adds the missing multiply/reciprocal families and exact conditional branches on a
separate temporary feature branch. This new work requires independent review and
has no merge authorization. Earlier pointers/review-pending statements retain
their dated publication context; no full-hash, selected-core or calibrated-PPA
acceptance follows. All pinned assets and serialized compute rules remain.

## Current component sequence — 2026-10-13

[PR49](https://github.com/jliu67/OpenRX/pull/49), [PR51](https://github.com/jliu67/OpenRX/pull/51)
and [PR53](https://github.com/jliu67/OpenRX/pull/53) are independently accepted and
merged; current parent main is `a6450ceccd32848c438c7dcae6acb98695d2a0e8`.
[Task54](https://github.com/jliu67/OpenRX/issues/54) adds actual native integer
execution under the owner-authorized manager-led continuation. PR #55 was
independently accepted at `2b14e4f9` and remains draft/unmerged; no further merge is authorized.
Earlier component pointers,
review-pending summaries and governance statements below retain their dated
publication context. Issue claims remain the ownership record, the manager assigns
bounded current scopes, and compute is serialized. Full-core/hash, selected-core,
calibrated timing and physical-power gates remain open.

| Component task | Current bounded state |
| --- | --- |
| [48](https://github.com/jliu67/OpenRX/issues/48) | AES mixer accepted/merged in PR49; completed |
| [50](https://github.com/jliu67/OpenRX/issues/50) | Ordered iteration stores accepted/merged in PR51; completed |
| [52](https://github.com/jliu67/OpenRX/issues/52) | Iteration memory engine/read-grant correction accepted/merged in PR53; completed |
| [54](https://github.com/jliu67/OpenRX/issues/54) | Native integer execution; PR #55 independently accepted, draft/unmerged |
| [56](https://github.com/jliu67/OpenRX/issues/56) | Native multiply/branch; PR #57 independently accepted, draft/unmerged |
| [58](https://github.com/jliu67/OpenRX/issues/58) | Exact HardFloat-backed native FP subset/CFROUND; new-work review pending |

## Current objective — manager-led build-first delivery, 2026-10-12

Deliver working RandomX v2 execution hardware using licensed reusable IP, with
reference correctness tests, reproducible synthesis, a useful execution integration
interface and measured component improvement. The active owner-designated manager
assigns bounded scopes, redirects agents, coordinates the shared compute slot and
keeps delivery moving. Research is timeboxed to a concrete implementation blocker;
reuse completed decisions/evidence and avoid repeated surveys, status cycles and
separate documentation approval chains. Keep overhead minimal while retaining
source/tool/command provenance, failures and independent review of new work.

[Current implementation #48](https://github.com/jliu67/OpenRX/issues/48) /
[draft PR #49](https://github.com/jliu67/OpenRX/pull/49) delivers the required F/E AES
stage. Genuine full-workload, selected-core, calibrated timing and physical-power
acceptance requirements remain; earlier milestones are not declared passed by
this build-first instruction. Issue claims remain the source ownership record,
and compute remains serialized. Historical results and pinned assets are retained.

## First required v2 hardware component — 2026-10-12

The later direct owner instruction authorizes the bounded execution component in
[#48](https://github.com/jliu67/OpenRX/issues/48), superseding the earlier source-only
priority for this implementation. F/E mixer RTL, v1/v2 writeback integration,
oracle tests and generic synthesis are delivered for new independent review;
[EXP-003](../experiments/EXP-003-v2-aes-rtl.md) links actual cycles, resources and
retained failures. This does not accept a full baseline, processor/model or PPA,
and does not restart #8's incomplete deadline batch. Live claims remain on #48.

## Current native pilot terminal — 2026-10-12

[#8's scoped exploratory pilot is independently accepted](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969), not its
formal balanced thread/AES baseline. Execution `20261012T185152Z-97e747b1f6c4`
retains native source `4a4e30bbbda47cce7713c280d87f1506f7c6f954`; two balanced v2/v1 repeats at one setting
passed scoped controls/output/integrity/drain review. The owner released the
pilot claim into review/unclaimed; the broader issue is open. [Evidence](validation/native-pilot-20261012/README.md)
keeps all intervals, repeat spread and unverified limits. Host access was resolved
for the reviewed pilot; the P1-04 row now distinguishes that result from the
remaining formal configuration/coverage/repetition gates.

#16's separately accepted light matrix (39 required + nine runtime, optional AES
skipped) does not satisfy its broader gem5 full-dataset/intended-core/SMP gates.
M1–M5, #10 power, #11 profiling and #14 calibration before #12 RTL remain open.
Earlier blocked/no-run and fixture-only statements below are dated history.

## Accepted light gate and live-task readback — 2026-10-12

[Terminal #16 acceptance](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891): 39 required light controls (31 arithmetic
+ eight software hashes), nine runtime controls pass; optional hardware AES is
skipped. [Evidence](validation/m3-fs/accepted-light-matrix-20261012.md) keeps
execution `20261012T032030Z-65cbb4c0cf9e` bound to scientific source `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`.
At the released monitoring-claim readback, #16 is **open/router-ready, unclaimed**;
this does not authorize a successor or satisfy full-dataset/intended-core/SMP gates.
M1–M5, controlled #8/#10/#11 and selected-core/calibration gates remain unchanged.
#41's bounded source-only planning deliverable is completed after reviewed PR #44.
Current queue rows below reflect these two closeouts; older dated snapshots and
exact prior rows remain as history. Live issue comments still govern claims.

## Current mission and priority overlay — 2026-10-12

Target an X9-class ASIC adapted to RandomX v2 through bounded evidence and reuse
of existing verified tools/licensed IP. [Ordered roadmap](ROADMAP.md#current-priority-path--2026-10-12)
and [alignment #39](https://github.com/jliu67/OpenRX/issues/39) govern current focus;
task comments still govern claims and verified completion.

- [#41](https://github.com/jliu67/OpenRX/issues/41) is the bounded source-only target-envelope/reusable-IP/AES decision task; inspect its current claim/receipt before editing. It grants no execution or RTL authority.
- Keep #16's unchanged correctness work, #8 controlled baseline, #10 measured power
  and #11 evidence-led AES/cache/FP profiling as necessary inputs; their gates stay open.
- Focus #3 on reuse fit of the provisional BOOMV3 baseline and needed components;
  #14 calibration remains required before #12 architectural/ASIC optimization.
- Defer #2's X5/SG2042 reconstruction and unrelated broad surveys. Its scientific
  questions and historical records remain open; a priority overlay is not acceptance.
- X9 proprietary internals/topology and measured v2 efficiency remain unknown.
  Whole-machine advertised targets do not establish chip-level or v2 performance.

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
| P1-04 | Controlled-host v1/v2 thread/AES matrix | [#8](https://github.com/jliu67/OpenRX/issues/8) OPEN; [scoped exploratory pilot accepted](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969), claim handed off for review. Formal balanced thread/AES coverage, at least four balanced repeats, sufficient duration and reviewed controlled settings remain pending; M1 incomplete | [Pilot evidence](validation/native-pilot-20261012/README.md): two repeats/one setting, exact controls and all raw intervals; no thermal-equilibrium, power/efficiency or formal-baseline claim |
| P1-04S | Isolated native build/launch staging | DONE — [PR #36 merged at 77cc171a and task #35 completed after final review/postmerge CI](https://github.com/jliu67/OpenRX/issues/35#issuecomment-6117228235) | [Evidence](validation/native-staging-20261012/README.md): 16 staging fixtures, retained local 313-test/socket-rerun history, accepted build and six native controls; 106 supported upstream passes plus one conditional skip. Unexecuted configuration coverage and #8/M1 throughput/power remain open |
| P1-05 | Same-process warmup and hashing interval markers | DONE — merged on main at `960b8b5`; see historical [#9](https://github.com/jliu67/OpenRandomX/issues/9) | `59b469c`; [adapter](../benchmarks/steady/README.md); [64 tooling / 107 upstream / 6 native tests](validation/p1-05/README.md) |
| P1-06S | Power-sample importer and validator | DONE for software; [#13](https://github.com/jliu67/OpenRandomX/issues/13) closed as completed; [PR #17](https://github.com/jliu67/OpenRandomX/pull/17) merged at `973cd0d` | Original `2b28d6f`, repairs `288cebb`; [independent review](validation/p1-06s/PATCH-REVIEW-20261008.md), 64 importer tests and numerical/error-report audit; [CI](validation/m3-fs/RUNTIME-CI.md) |
| P1-06 | Time-aligned wall-power measurement | [#10](https://github.com/jliu67/OpenRandomX/issues/10) BLOCKED: #8 and calibrated synchronized meter access; #9/#13 completed | Real synchronized readings, physical boundary, uncertainty and completed hashes/measured joules |
| P1-07 | Dynamic bottleneck attribution | [#11](https://github.com/jliu67/OpenRandomX/issues/11) BLOCKED: #8 and verified PMU/profiler access/permissions | Dynamic instruction/cache/stall evidence, event limitations and overhead |

### Retained P1-04 row — before the exploratory pilot terminal

Exact row from main `54da42cca7f79f330e0c8b5403d3fe8e589a8a4b`; its blocked status
is a prior assessment, superseded for the reviewed scoped pilot only:

```text
| P1-04 | Controlled-host v1/v2 thread/AES matrix | [#8](https://github.com/jliu67/OpenRandomX/issues/8) BLOCKED: controlled baseline configuration/authorization and current host verification; designated infrastructure accepted in #27 | Fixed settings, controls, balanced order, sufficient duration, all raw repeats |
```

**M1 remains OPEN.** P1-05 and P1-06S are instrumentation/analysis software, not completed performance/efficiency experiments. P1-05 CI configurations are correctness controls; three workers on two exposed logical CPUs are not scaling evidence. The old upstream runner and new static-stride batch adapter have different overhead, so do not mix their rates. P1-06S can calculate energy from declared valid inputs but cannot certify physical calibration. All power joins actually exercised this session used synthetic traces; no measured hashes/J exists. Review its strict whole-system AC point-power scope before adapting a real meter export.

Parent milestone [#1](https://github.com/jliu67/OpenRandomX/issues/1) is a discussion/acceptance gate, **not** a shared editing lease: use the appropriate open child task #8, #10 or #11. #13 software was independently reviewed, repaired and merged in PR #17; do not reimplement it. #9 and #13 are completed work. #2 stays open but owner-priority-blocked; #3 stays open for provisional reuse fit and exact selected-core acceptance, with its historical review state preserved; #4's dated source audit is completed and closed. No other agents are implied to be running by this summary.

## Existing research queue

| Issue | Work item | Status |
|---|---|---|
| [#1](https://github.com/jliu67/OpenRandomX/issues/1) | Measured native baseline | Partial; tasks above |
| [#2](https://github.com/jliu67/OpenRandomX/issues/2) | X5 / SG2042 evidence | Owner-priority BLOCKED via [supported router command](https://github.com/jliu67/OpenRX/issues/2#issuecomment-6118574647); remains open, deferred and unresolved, with primary board/chip evidence still required |
| [#41](https://github.com/jliu67/OpenRX/issues/41) | Bounded X9/v2 target-envelope and reusable-IP/AES gap decision | COMPLETED for source-only planning after [reviewed PR #44](https://github.com/jliu67/OpenRX/issues/41#issuecomment-6121699142); reuse the [decision](research/X9-V2-REUSE-DECISION.md). No measured v2, selected hardware or scientific gate completion |
| [#3](https://github.com/jliu67/OpenRandomX/issues/3) | Core/simulator selection | [PR #15](https://github.com/jliu67/OpenRandomX/pull/15) MERGED after review/CI: source-backed provisional BOOM/gem5 selections; actual scalar QEMU 39-check preflight. OPEN for selected-core/runtime boot and full dataset; preserve M1/M4/M5 gates |
| [#4](https://github.com/jliu67/OpenRandomX/issues/4) | Monero activation | DONE for dated source research; PR #19 merged, #4 closed. Released consensus uses v1; beta v2 stressnet is separate; no live tip or mainnet v2 date. [Audit](validation/monero-activation/REVIEW-20261008.md) |
| [#16](https://github.com/jliu67/OpenRX/issues/16) | gem5 full-system Linux correctness | OPEN; [bounded light matrix accepted](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891): 39 required controls (31 arithmetic + eight software hashes) and nine runtime controls; optional hardware AES skipped. Executed source `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`, receipt/input integrity and drain/slot release verified. Full dataset, intended-core/SMP, calibrated timing/power and broader M1–M5 remain open. [Evidence](validation/m3-fs/accepted-light-matrix-20261012.md); original attempts retained below. Every successor needs its reviewed request and fresh admission |

### Retained research-queue rows — before this terminal reconciliation

Exact rows from main `d284e927f13a331e3079232681760847aa30e32f`; these describe
their earlier publication and attempts, not the current queue state:

```text
| [#41](https://github.com/jliu67/OpenRX/issues/41) | Bounded X9/v2 target-envelope and reusable-IP/AES gap decision | Source-only READY at publication; verify live receipt/claim. No workload, hardware selection or scientific completion |
| [#16](https://github.com/jliu67/OpenRandomX/issues/16) | gem5 full-system Linux correctness | OPEN; PR #18 actual Linux boot + nine runtime controls accepted. PR #25 cancellation repair merged and independently reviewed (253 Python / 34 host gem5 controls). The extended unchanged guest independently passed 9 runtime + 31 semantic controls, with zero hash values; it was manually stopped after proof that its tick guard cannot finish both cache initializations. No final runner report; saved raw evidence remains accepted only as partial. The next recipe uses an explicit larger guard and separately tested stop-file control, and migration #27 is now complete under its [final acceptance](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454). Any next attempt requires reviewed current source/runner/input bindings, a new local request and fresh admission/resource checks; this summary does not authorize execution. Full dataset/intended cores are separate gates. [Results](validation/m3-fs/README.md), [reuse the built binary](validation/m3-fs/REUSE.md); no calibrated timing |
```

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

Phase 1 child issue graph: #8 (measured host baseline; controlled configuration/authorization and current host verification still required); #13 (power importer; independently accepted software, merged and closed as completed); #10 (wall power; depends #8/#9/#13 plus instrument access); #11 (dynamic profiling; depends #8). #9 and #13 record completed software and must not trigger reimplementation. M4 [#14](https://github.com/jliu67/OpenRandomX/issues/14) is gated by milestone #1 and simulator #3. M5 [#12](https://github.com/jliu67/OpenRandomX/issues/12) is gated by #1/#3/#14. #2 is retained but owner-priority-blocked, and #3 remains open for selected-core/reuse evidence rather than broad surveys; bounded source-only #41 is the current target/reuse/AES entry; #4's dated source audit is completed and closed. Inspect current issue comments/receipts for actual claims; an unexpired claim does not prove ongoing execution.

The independent [inspection checkpoint](inspection/2026-10-08-incident.md) is preserved alongside the final engineering handoff. Task #20 is independently accepted and closed as completed. #22 is completed after merged PR #23 queued eligible announcements and documented separate-agent review; its actual bot deployment passed. #24's compact handoff policy is also separately accepted and completed, with the duplicate decision ID corrected by its original author. [Coordination evidence](validation/coordination/REVIEW-20261008.md), [policy review](validation/coordination/POLICY-REVIEW-20261008.md).
