# Roadmap and acceptance gates

## Current priority path — 2026-10-12

The objective is an X9-class ASIC adapted to exact RandomX v2, with v1 regression
coverage and reuse-first engineering. The sequence below narrows work; it does
not change any acceptance criterion in the retained milestone table.

1. Bound the X9 comparison envelope to traceable primary claims and explicit
   unknowns. Separate whole-machine advertised targets from measured v2 and
   chip-level results. X9 silicon, core topology and v2 measurements are not
   established; do not wait for unavailable proprietary RTL or infer it from an ISA.
2. Reuse pinned RandomX, accepted tools and preserved builds. Keep #16's existing
   unchanged correctness request/oracle intact; complete light/full-dataset and
   intended-core/SMP gates before claiming that model executes the workload.
3. Complete the controlled #8 baseline, #10 physical power and #11 profiling under
   their existing access, configuration and scientific gates. Measure v2 main-loop
   AES demand versus scalar software AES alongside cache/memory/FP costs; do not
   prescribe a bottleneck from static weights or short functional rates.
4. Under #3, assess one provisional open-IP baseline (BOOMV3) and suitable reusable
   components against exact ISA/JIT, FP/rounding, AES, memory and licensing needs.
   Document the concrete gap and reuse decision; broaden a survey only if evidence
   disqualifies the candidate. BOOMV3 is not verified X9 silicon or a final ASIC choice.
5. Complete #14/M4 correctness and timing calibration with declared uncertainty.
   Only after the existing #1/#3/#14 gates are verified may #12/M5 propose one
   constrained v2 architectural change and evaluate correctness and PPA tradeoffs.
6. Advance the resulting ASIC design/verification and later prototype through the
   retained gates. Declare measurement/model boundaries; functional or FPGA results
   cannot prove X9-class ASIC efficiency or competitive PPA.

**Deferred, still unresolved:** broad processor surveys and #2's X5/SG2042
reconstruction, unless a bounded question directly changes the X9-class v2 design.
Preserve their records and unknowns. Deferral neither completes M2 nor waives
baseline, selected-core, calibrated-model or RTL/prototype acceptance.
[Source-only #41](https://github.com/jliu67/OpenRX/issues/41) bounds the target-envelope and reusable-IP/AES decision in steps 1 and 4; it does not authorize or duplicate #16/#8 execution. Select eligible tasks using this overlay before numeric milestone order or the shared ready query. #2 is held via the supported owner-priority block, without scientific completion. [Scope alignment #39](https://github.com/jliu67/OpenRX/issues/39) records review/publication state.

## Current status — 2026-10-10

[Migration #27 is complete](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454): independently accepted `LOCAL_ACTIVE` and [explicit designated-host release](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817), after merged PRs #28 and #30. [Cleanup #31 / merged PR #32](https://github.com/jliu67/OpenRX/issues/31#issuecomment-6099136057) establishes GitHub-only progress publication: the editable migration checkout and disposable sync mirror were recoverably retired; sync stays disabled. Evidence-bound originals, pinned execution sources and computational assets remain retained.

These are verified GitHub closeout records, not a fresh host-health check. Every new execution still needs its reviewed request, current host/resource checks and existing admission gates. #16's complete unchanged RandomX matrix, full dataset and intended-core/SMP/BOOM gates remain open, as do M1–M5. Controlled measurement configuration/authorization, meter and PMU access are separate prerequisites. Dated CUTOVER_PENDING and pre-final records below are preserved history, not current migration blockers.

| Milestone | Deliverable | Acceptance |
|---|---|---|
| M0 Foundation | Memory, source pin, scripts, CI, templates | Integrity passes, build/tests/smoke recorded, repository accessible |
| M1 Native baseline | Known CPU v1/v2 mine-mode runs | Correct hashes, metadata, repeated runs, measured power for efficiency |
| M2 Hardware evidence | X5/SG2042 architecture report | Traceable sources; unknowns explicit; no guessed internals |
| M3 Simulation feasibility | Select core and simulator | Exact ISA/JIT/FP support, reproducible boot and correctness path |
| M4 Calibrated model | Baseline workload in model | Correct hashes and validated timing assumptions; uncertainty reported |
| M5 First optimization | One architectural change | Correctness unchanged, controlled baseline, area/timing/power tradeoff |
| M6 Prototype | FPGA functional subset | Timing closure and reproducible behavior; FPGA power not ASIC forecast |

First investigation: characterize v1/v2 thread scaling and AES effects on measured hardware, then study cache/memory pressure. Do not prescribe a bottleneck before measurement.

## Execution infrastructure prerequisite — 2026-10-09

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

The distinct pinned build 03 completed at 19:37:51Z with unchanged source/configuration and verified loader.
Runtime-only execution `20261009T193937Z-576aa858c033` completed; independent review accepted the expected
Ubuntu 24.04 / Linux 6.8.12 boot and all nine unchanged runtime controls at 20:04:52Z. The guest status was
zero, framed probe stderr was empty, and the completion marker and ordered hypercalls 1/2/3 were present.
Source, inputs, model and output integrity were independently verified. The model uses one 1-GHz
AtomicSimpleCPU, RVV disabled, 4 GiB RAM, 16-KiB L1I/L1D and 256-KiB L2, with a read-only base disk and
copy-on-write wrapper. This establishes functional controls, without a timing or performance inference.
Initial stop execution `20261009T200904Z-854b672fc611` proved initialization termination only, with empty
serial/no generated config. It is preserved and does not satisfy the broader operational stop gate.
Broader stop outcome at this snapshot: INDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim).
Reviewed broader stop execution: 20261009T202537Z-a1ca7df2cf1c; evidence: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`.
Runtime task publication: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6088623385`; technical transition publication:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095767946`. These publications were verified by exact GitHub readback.

[Policy](LOCAL_EXECUTION.md), [runbook](LOCAL_MIGRATION.md) and
[dated technical receipt](validation/local-migration-20261009/ACCEPTANCE.md) provide gate evidence.
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

This infrastructure prerequisite does not complete a scientific milestone.
