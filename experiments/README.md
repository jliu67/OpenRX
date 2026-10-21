# Experiments

## Shared dataset-fabric experiment — 2026-10-21

[EXP-025](EXP-025-shared-dataset-fabric.md) records a partial two-client finite
shared instruction/cache service experiment above merged PR87/main `c5d5368`.
Its prefix passed 14 units, directed protocol and native correctness; seven
additional native profiles completed through exact prefix binary reuse.
Separate independent bounded matrix-result review passes with no blockers.
[Evidence](../docs/validation/shared-dataset-fabric-20261021/README.md) separates
these component results from unrun generic synthesis/mapped parity, publication
gates and unresolved physical/full-hash performance. Historical experiments,
failed runs and scientific criteria remain unchanged.


## Accepted EXP-023 result — 2026-10-20

[EXP-023](EXP-023-full-hardware-dataset-hash.md) now has one independently accepted
default 8×2,048 functional hardware-dataset result at public `e8277c6`/tree
`cb3e0615`. The [validation summary](../docs/validation/dataset-fullhash-20261020/README.md)
separates full native assertions and modeled clocks from retained prepared host
services and unknown physical PPA/frequency/architecture. The prior preparation
and full-attempt failures remain unchanged; earlier candidate entries are history.

## Current experiment index — 2026-10-19

[Verified project status](../docs/STATUS.md) distinguishes merged component
experiments through [EXP-022](EXP-022-dataset-session-capacity.md) from the draft
[EXP-023 candidate](https://github.com/jliu67/OpenRX/blob/8e4164230ce633bbe43a385003659680cfec2925/experiments/EXP-023-full-hardware-dataset-hash.md).
PR82 is merged on main; PR83 remains draft. Retained preparation passed, but the
subsequent frozen b5f45998 full attempt ended PROCESS_FAILED/scientific-unverified.
The existing supervisor owns terminal review. Earlier six-program observations
remain partial history; no full hardware-dataset acceptance or physical PPA follows.
Older entries below retain source-specific publication-stage statements.

## Executable architecture feasibility — task #72, 2026-10-16

[EXP-015](EXP-015-architecture-feasibility.md) binds the executable trace scheduler,
partial source-state calibration, 58 focused tests, portable native windows,
488 bounded comparison rows and reproducible scratchpad/dataset/complete-energy
necessary bounds. Full-hash alternative timing and physical feasibility remain
unresolved; source/provider boundaries and the preserved parser failure are explicit.

## Native register-file hashing — task #64, 2026-10-13

[Task #64](https://github.com/jliu67/OpenRX/issues/64) connects native hardware BLAKE2b seeds above independently accepted PR63 `990f36830c5a9854bf8e2cf1fe7fd7d4ccf7f192` ([review](https://github.com/jliu67/OpenRX/pull/63#pullrequestreview-5505712453)). All 18 RTL/17 mapped modes pass: balanced 524 native messages per 32/64-byte digest, held/reset/errors, four actual hardware-seed chains and eight native cancellation modes. Hash/bridge latency is 56/58 modeled clocks, last-program bypass zero; exactly seven seeds per eight programs adds 414 fixture clocks in each profile. Actual new-stage mapping includes 1,024 inherited latches, reported separately from flops; it excludes the preserved backend. [Design](../rtl/hash/README.md), [EXP-011](../experiments/EXP-011-native-regfile-blake2b.md) and [evidence](../docs/validation/regfile-blake2b-20261013/README.md) retain exact sources/outputs/resources/failures. At initial publication, new independent review and hosted verification are pending; subsequent results are recorded on task #64 and the draft PR. No merge is authorized. Full dataset, external AES stages, complete hardware finalization and physical PPA remain open. Earlier component sections retain their dated boundaries; 69 accepted inputs, 171 native files and five IP originals and all original assets remain unchanged.

Current compiler compatibility: [Icarus 12 compile view](../rtl/execute/DIVSQRT.md#icarus-12-compatibility-correction--2026-10-13) removes one redundant declaration in a generated copy; original IP/hardware bytes and Yosys sources remain unchanged. All 12 local RTL records/native fixtures match; corrected hosted checks and independent review remain required.

## Native division and square root — task #60, 2026-10-13

[Task #60](https://github.com/jliu67/OpenRX/issues/60) extends independently
accepted, unmerged [PR #59](https://github.com/jliu67/OpenRX/pull/59#pullrequestreview-5501107360)
at `ce788d11285c901b52fd3cf0b450489d13b3f2f5` on a separate stacked draft.
All 29 native instruction families / 256 raw encodings now execute, including
masked FDIV_M and FSQRT_R. Reviewed PR #55/#57/#59 and main remain unchanged.
New code requires independent review; no merge is authorized. Complete VM/hash,
selected core, physical memories and calibrated timing/power remain open.
[Design](../rtl/execute/DIVSQRT.md) and [EXP-009](EXP-009-native-divsqrt.md)
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

Copy TEMPLATE.md to a numbered experiment. Track hypothesis → configuration → correctness → measurements → interpretation → next action. Negative and failed results belong in the record. Use GitHub research/experiment issue templates for ownership and discussion; durable conclusions go into memory and docs.

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

[Local execution interface](../docs/LOCAL_EXECUTION.md) describes GitHub requests, immutable local
submission, locks, manifests/logs/results and offline behavior.
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

Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.
Every attempt retains a new execution ID/request key, exact source/input/config identities, logs and
scientific oracle. No checkpoint resume or scientific pass is inferred from boot/process exit.
The [owner resource directive](../docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
with swap where useful, retaining only measured necessary OS/agent headroom. Per-job allocations must
reflect current host load, memory availability and workload parallelism; 14 GiB is a candidate, not a
universal safe limit. Keep one payload slot and all migration/scientific gates.
The old runner988 validation records retain their actual memory and manager-reported 200% CPUQuota.
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

