# Current state — actual local execution activation

## Native integer execution handoff — 2026-10-13

[Task54](https://github.com/jliu67/OpenRX/issues/54) / [EXP-006](../experiments/EXP-006-native-integer-execute.md)
delivers actual hardware execution of eleven integer families, not software-result
replay. Eight RTL and eleven mapped modes pass against unchanged native execution,
including all98 supported/all158 unsupported raw values, per-instruction and full2MiB
checks, stalls/stale traffic/error/reset, all rounding-mode transport and held returns.
Fast/shared clocks are9,524/9,760 ideal and26,712/26,948 stalled, saving236 clocks
(one per IADD_RS). Actual generic kernel cells/flops are25,885/1,727 versus
25,925/1,792; complete default top154,145/7,921. These are fixture/port cycles and
generic cells, not full hashes or calibrated PPA. [Complete evidence](../docs/validation/integer-execute-20261013/README.md)
retains source/tool/input/command/log/netlist/license/failure/resource bindings.

Sources/attempts are archived and temporary authoring retired read-only at handoff;
all previous assets and bound inputs remain unchanged. Full validation used checked
six-CPU/5GiB/512MiB-swap/128-task limits, one worker; peak cgroup5,080,702,976 bytes,
no OOM/swap/quota throttle. Focused checks used measured1GiB. Next: all final-head
hosted checks and one independent new-work review of this draft. No next merge is
authorized. Multiply/high-multiply/reciprocal, branch, FP/CFROUND, physical memories,
selected-core/calibrated-PPA and complete RandomX hash gates remain open.

## Current component sequence — 2026-10-13

[PR49](https://github.com/jliu67/OpenRX/pull/49), [PR51](https://github.com/jliu67/OpenRX/pull/51)
and [PR53](https://github.com/jliu67/OpenRX/pull/53) are independently accepted and
merged; current parent main is `a6450ceccd32848c438c7dcae6acb98695d2a0e8`.
[Task54](https://github.com/jliu67/OpenRX/issues/54) adds actual native integer
execution under the owner-authorized manager-led continuation; its new-work review
remains pending and no further merge is authorized. Earlier component pointers,
review-pending summaries and governance statements below retain their dated
publication context. Issue claims remain the ownership record, the manager assigns
bounded current scopes, and compute is serialized. Full-core/hash, selected-core,
calibrated timing and physical-power gates remain open.

## Read-grant correction after independent review — 2026-10-13

[PR53 review](https://github.com/jliu67/OpenRX/pull/53#pullrequestreview-5497704738)
blocked original bd193092: an arriving write could retract a scratchpad read
already held under backpressure. The same author reproduced the exact failure
on unchanged original RTL, preserved its source/test/input hashes/fatal log,
and added one retained read-grant bit. Fresh competing requests still give
writes priority; an already presented read retains valid/address/tag until
acceptance and blocks writes until the response is consumed. Reset/new descriptor
clears the grant; architectural return cannot bypass a pending grant.

The new directed regression runs v1/v2, overlapping requests in both orders,
12 read-stall clocks, eight write-stall clocks, six response-stall clocks,
six stale-generation drops and reset of a held grant. It verifies five reads,
three ordered byte-strobe writes and committed-byte persistence. It fails the
rejected RTL and passes all four RTL configurations plus both actual A/C netlists.
The eight native RTL and four native mapped modes remain byte-identical to the
original serialized replay; every native/vendor/AES/store-tail input is unchanged.
Entry totals A/B/C=1056/544/480 and native replay cycles are unchanged.

Corrected generic A/C counts are 126,820/130,599 cells and
7,734/6,705 flops. Compared with the rejected source,
deltas are +10/+10
cells and +1/+1 flops.
The original failing overlap sequence has no valid cycle result to compare.
[Focused evidence](../docs/validation/iteration-engine-read-grant-20261013/README.md)
binds raw failures, corrected source, commands/versions, actual netlists and
resource receipts, retaining every earlier source/result/archive/review.

The initial 4 GiB candidate did not fit fresh headroom. Standalone A synthesis
used kernel-verified CPU600%, RAM3 GiB, swap512 MiB and Tasks128, after a fresh
1 GiB host reserve check; measured memory pressure/swap increased wall time
without an OOM or CPU-quota throttle. Freshly regained headroom admitted C at
4 GiB. Mapped-only checks used 1 GiB based on measured compile/simulation RSS.
All six CPUs remained available, one worker, global slot serialized. Detailed
resource witnesses stay private; sanitized measured limits/peaks/elapsed/swap
are public. Source and attempts are verified/archived and retired read-only at
publication. Prior sources/receipts are preserved; no extra tasks/agents,
install/access/settings change, repeated baseline, force push or merge.

Next: all final-head hosted checks, then the same reviewer's focused delta review.
This author handoff does not establish acceptance or authorize merge. Arithmetic
kernel, physical memories, calibrated PPA and full-hash requirements remain
external. Earlier evidence below records its original source and is retained.

## Hosted log compatibility follow-up — 2026-10-13

Initial draft head a04b9163 has the complete passing local RTL/mapped result
below. Its hosted converter test also passed, but Icarus12 appended a successful
finish diagnostic that the harness's exact-whole-log check rejected. The focused
[compatibility correction](../docs/validation/iteration-engine-ci-compat-20261013/README.md)
requires the same exact PASS record plus successful exit. All eight corrected-driver
RTL modes pass with identical logs; all six hosted native fixture files match.
Every RTL/C++/vendor input and original mapped result remains unchanged. The full
hosted flow must pass on the final draft tip before one independent new-work
review accepts it; no merge is authorized. Earlier original evidence is preserved.

## Iteration memory engine — 2026-10-13

[Task #52](https://github.com/jliu67/OpenRX/issues/52) implements entry loads,
exact signed conversion, tagged execution/memory traffic and dataset feedback,
reusing the independently accepted PR49/51 code now merged at main 5a688512.
[EXP-005](../experiments/EXP-005-iteration-engine.md) and [interface](../rtl/engine/README.md)
record eight passing RTL modes and four passing actual mapped modes. Each mode
checks 32 native differential iterations (16 v2/16 v1), 2,880 bytecode reads,
720 bytecode stores, 256 tail writes, eight aliases, 16 chained contexts, all
2 MiB memory, stale/stalled traffic and three reset aborts. The separate signed
conversion differential passes 4,096 vectors across four rounding modes.

LANES=4 entry clocks are A/B/C=1,056/544/480 across 32 fixtures: parallel conversion
saves 16 per iteration; equal-line coalescing saves four reads/eight clocks per
alias under the stated minimum-latency private-memory contract. Generic A/C
counts are 126,810/130,589 cells and
7,733/6,704 flops. Arithmetic kernel, instruction fetch,
physical SRAM/cache and dataset remain external; these are controller/replay
cycles, not calibrated PPA or hash throughput.

One kernel-verified six-CPU/4 GiB/512 MiB-swap/128-task payload used one worker,
peak RSS 2,630,284 KiB; source/vendor/core/tail inputs and all
original assets remain retained. New source/attempts are archived and temporary
authoring retired read-only at handoff. The first reset testbench sampling failure
is retained with its correction. Next: one independent review of this new draft
feature. Reproduce with `python3 scripts/test_iteration_engine.py --output
/tmp/openrx-engine-fresh --synthesize`, using the global slot and fresh admission.
No code merge is authorized. Earlier dated component/status entries below retain
their original bytes; live task/PR records supply subsequent review and CI status.

## Iteration-tail SRAM integration — 2026-10-12

[Task #50](https://github.com/jliu67/OpenRX/issues/50) extends immutable reviewed
PR49 head 9a3271d5 with ordered R/F scratchpad stores and final-F/cursor retirement.
The pinned interpreter iteration and BytecodeMachine provide a controlled
software differential, using a deterministic dataset-line fixture. Four RTL
configurations and both actual overlap netlists pass 128 iterations, 1,024 stores,
32 aliases, partial-reset/backpressure checks and all 2 MiB final memory bytes.
[EXP-004](../experiments/EXP-004-iteration-tail.md) records shared 25→21 and four-lane
13→9 cycle intervals by overlapping R stores with AES, and delivered generic
counts 46,510/90,661 with 2,605/2,603 flops. Physical SRAM/core/fabric/timing are not
accepted interfaces; this is tail integration, not full-core/hash proof.

New-work independent review remains required. PR49's code, branch and all 19
reviewed-core input bindings are unchanged; no main merge is performed. One
worker ran under checked six-CPU/4 GiB/512 MiB-swap/128-task limits, peak RSS 2,252,132KiB,
with slot/cgroup released. Original sources/data and full new outputs are retained;
temporary authoring is retired at handoff. Next: review this new boundary, then
connect a concrete selected-core/register-file and ordered-memory interface.

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

## First v2 execution component — 2026-10-12

Owner-directed [#48](https://github.com/jliu67/OpenRX/issues/48) implements the
required F/E AES mixer with pinned secworks S-box IP and a VM-completion/F-writeback
interface, including v1 XOR path. Round, both mixer/integration and mapped-netlist
checks pass. [EXP-003](../experiments/EXP-003-v2-aes-rtl.md) records 17 versus 5
no-stall request cycles and 40,848 versus 84,999 generic cells. Physical timing,
area, power and whole-hash improvement remain unmeasured. New implementation
review is pending; this is a bounded owner-authorized phase exception, with all
broader baseline/core/model gates preserved. [Evidence](../docs/validation/aes-rtl-corrected-20261012/README.md)
retains the initial coefficient/tool failures and the failed 2-GiB synthesis;
the full corrected attempt10 passed under checked 4-GiB/600%-CPU limits. No further
native baseline batch was run. Existing scientific assets remain unchanged.

## Accepted scoped native pilot — 2026-10-12

[Owner-published independent terminal acceptance](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969) records execution
`20261012T185152Z-97e747b1f6c4`, exited zero at 18:55:54Z after one admitted
exploratory workload. Source `4a4e30bbbda47cce7713c280d87f1506f7c6f954` and reused native binary/input identities
remain unchanged. All 12 records, known controls/warmups, order/counts/duration,
repeat determinism, original-input/receipt/journal integrity and actual drain/
slot release passed scoped review. The immutable receipt remains scientifically
unverified; the separate independent review grants exploratory acceptance only.
[Selected evidence](../docs/validation/native-pilot-20261012/README.md) records that boundary.

At the terminal handoff, #8 is open/review with its scoped claim released; the
formal balanced thread/AES baseline and M1 are incomplete. The earlier fixture-
only/no-pilot stage below is historical. No new job or fresh host-idle state is
asserted here. #16's accepted 39+9 light gate at scientific source
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726` remains separate, optional AES skipped;
its broader full-dataset/intended-core/SMP and selected-core/timing/power/RTL/
M1–M5 gates remain open. No thermal-equilibrium, isolation, constant-frequency,
external clock/power alignment, PMU, energy/efficiency or competitive PPA claim.

## Accepted bounded light-matrix state — 2026-10-12

[Independent terminal acceptance](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891) records execution
`20261012T032030Z-65cbb4c0cf9e`, scientific source
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`: all 39 required controls
(31 arithmetic + eight software hashes) and nine Linux runtime controls pass.
The optional hardware-AES case is skipped. Both guest statuses and wrapper/gem5
return are zero; complete frames, empty guest stderr, completion and ordered
hypercalls 1/2/3 were verified. Independent review checked 23 input/source
bindings and 26 receipt artifacts; the actual execution/cgroup drained and
heavy slot was released. [Selected evidence](../docs/validation/m3-fs/accepted-light-matrix-20261012.md)
links immutable private-report/receipt identities without publishing host detail.

At the terminal release readback, #16 remains open/router-ready with no claim;
full-dataset/intended-core/SMP, BOOM, timing, measured power, RTL and M1–M5 remain
open. No successor was launched by that closeout. Native work is only separate
tiny-supervisor-fixture preparation/validation; no native benchmark pilot is
reported or authorized here. Completed #41 supplies source-only planning.
Earlier partial/light/migration states below remain dated history; retain every
original source/build/input/receipt identity and use fresh reviewed admission
for any future execution. This is a dated accepted record, not fresh host health.

## Current project direction — X9-class RandomX v2 ASIC, 2026-10-12

The owner narrowed the goal to an X9-class ASIC adapted to exact RandomX v2,
with reuse-first engineering and bounded reverse-engineering evidence. [Mission](PROJECT.md#user-intent),
[priority path](../docs/ROADMAP.md#current-priority-path--2026-10-12) and [alignment #39](https://github.com/jliu67/OpenRX/issues/39)
record the direction and separately reviewed document proposal. Broad surveys and
X5/SG2042 reconstruction are deferred, not completed. BOOMV3 is provisional open
IP, not verified X9 silicon; X9 topology/v2 results and competitive PPA remain unknown.

Shared-pool correction: #2 remains open but owner-priority-blocked through the existing router; [#41](https://github.com/jliu67/OpenRX/issues/41) supplies bounded source-only X9/v2 target/reuse/AES work. Apply the current overlay before historical numeric milestones or ready labels. No router code or scientific status is changed by this priority correction.

The scope change preserves #16's unchanged correctness work, #8/#10/#11 baseline,
power/profiling prerequisites, #3 selected-core acceptance and #14/M4 before #12/M5.
Pinned execution source `4a4e30bb`, accepted receipts and all historical entries
below retain their identities. No new workload, code or scientific result is
created by this documentation/coordination update.

## Accepted native staging and supported correctness — 2026-10-12

[Completed task #35 / merged PR #36](https://github.com/jliu67/OpenRX/pull/36) has
independent source, actual isolated-build and supported-native-correctness
acceptance for execution source `4a4e30bb`. [Current evidence](../docs/validation/native-staging-20261012/README.md)
records the finalized build/correctness receipts, unchanged source/binary
bindings, six native tests, eight reference controls, two differential matches,
16 invalid-CLI checks and retained duration rejections. Upstream supported
coverage is 106 passes plus one conditional skip; unexecuted configuration
coverage is open. Detailed host witnesses remain private.

Earlier failed telemetry and denied headroom attempts are preserved. Successful
executions verified finalization and descendant drain; no native payload remains.
[PR #36 merged at 77cc171a](https://github.com/jliu67/OpenRX/commit/77cc171a935780788ceceb15f75d5c0e3a556650)
after [final review and postmerge CI closeout](https://github.com/jliu67/OpenRX/issues/35#issuecomment-6117228235);
[task #35 is completed](https://github.com/jliu67/OpenRX/issues/35).
#8/EXP-001/M1
still require controlled throughput/power work; no diagnostic rate is a baseline.
Scientific criteria, vendor bytes and disabled synchronization are unchanged.
The dated preparation/state sections below remain historical and do not override
this verified implementation closeout.

## Native staging preparation — 2026-10-12

[Task #35](https://github.com/jliu67/OpenRX/issues/35) prepares external fresh
native builds and explicit steady/control input/output paths on base `3ee72cc`.
Implementation and [lightweight evidence](../docs/validation/native-staging-20261012/README.md)
await independent review in a draft feature PR. 313 tests were exercised: 312
passed in the sandbox; its one denied Unix-socket fixture passed a permitted
targeted rerun. Final 16 staging tests and all 171 vendor files pass.
No native compilation/full-dataset controls or measured baseline were executed;
shared compute-slot approval and reviewed local requests remain required.
Retained sources/assets, immutable runner, sync and #16 scientific scope are
unchanged. #8/EXP-001 and M1 remain open; exact next commands are in the adapter
README and task handoff. Prior dated state text below is retained verbatim.

## Current status — 2026-10-10

[Migration #27 is complete](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454): independently accepted `LOCAL_ACTIVE` and [explicit designated-host release](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817), after merged PRs #28 and #30. [Cleanup #31 / merged PR #32](https://github.com/jliu67/OpenRX/issues/31#issuecomment-6099136057) establishes GitHub-only progress publication: the editable migration checkout and disposable sync mirror were recoverably retired; sync stays disabled. Evidence-bound originals, pinned execution sources and computational assets remain retained.

These are verified GitHub closeout records, not a fresh host-health check. Every new execution still needs its reviewed request, current host/resource checks and existing admission gates. #16's complete unchanged RandomX matrix, full dataset and intended-core/SMP/BOOM gates remain open, as do M1–M5. Controlled measurement configuration/authorization, meter and PMU access are separate prerequisites. Dated CUTOVER_PENDING and pre-final records below are preserved history, not current migration blockers.

**Actual execution state: LOCAL_ACTIVE since 2026-10-10T08:51:50.953900+00:00.**
Dated update: 2026-10-10T08:56:25.052452+00:00.
This dated header records independently accepted activation, explicit release and verified hub delivery.
Eligibility acceptance C: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`; actual transition E:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817`; actual reviewed migration merge M: `f90ac65964bc0138711e4b6d45bcb7e26dff3cc9` /
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`; merged-document audit: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`.
The designated local execution policy is effective under the independently verified explicit #27 release
L: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817`. Its effective-policy hub announcement/bot receipt H:
`https://github.com/jliu67/OpenRX/issues/5#issuecomment-6095882106` / `https://github.com/jliu67/OpenRX/issues/5#issuecomment-6095883184` are verified.
Check [#27](https://github.com/jliu67/OpenRX/issues/27) and local status before each new request; later
BLOCKED/ROLLBACK_REQUIRED evidence or an offline host holds new admission.

This dated update records actual activation/release. Its own separately reviewed documentation PR merge
and readback will be published externally on #27 after actual reviewed integration; they are never self-referential hashes embedded here.
At this dated update, final synchronized migration acceptance W/Z has not yet been published. The live
#27 record supplies the later final receipt once this actual documentation integration and all required
readbacks are independently accepted. This dated pre-Z status remains historical after final publication;
LOCAL_ACTIVE, a released policy, a router label and this header alone do not prove migration completion.

The [owner resource policy](../docs/LOCAL_RESOURCE_POLICY.md) remains unchanged. The immutable
operational runner release is `runner-v1-657b23f1`, SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`; exact resource/profile/kernel proof:
`https://github.com/jliu67/OpenRX/blob/20c2e7b873d291689b86a9e28cdb06a527467032/docs/validation/local-migration-20261009/resource-kernel-20261010/index.json`. The owner-local-max-v1 profile permits six CPU cores
(CPU600%) and uses at most min(14 GiB, fresh MemAvailable minus 1 GiB), with approved lower explicit memory
when justified, swap2GiB/Tasks256 and one payload slot. Admission records current host metrics and rechecks
headroom before launch. It must check the actual payload kernel CPU/memory/swap/task limits and effective
ancestor ceilings, failing closed on missing controllers, mismatched constraints, tighter inherited limits
or lost fresh headroom. The profile publication must independently prove those admission semantics;
manager properties alone are insufficient. Raising CPU quota does not parallelize single-threaded gem5. Historical988 CPU200
was a manager property and was not kernel-enforced; its dated receipts remain unchanged.

Remote execution/direct retrieval remains unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub request, submits locally and publishes hash-indexed sanitized evidence.
No new SSH/listener/poller/self-hosted Actions channel is provided. Hold requests if offline; use temporary
sandboxes for cheap independent work. Permanent request-key bindings and the global payload/descendant
lock prevent duplicate or conflicting expensive execution. Preserve original data and all prior attempts.

The accepted expected Ubuntu24.04/Linux6.8.12 guest and nine unchanged runtime controls remain bound to
execution `20261009T193937Z-576aa858c033` and raw/public indexed review identities. Operational stop proof:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`, execution `20261009T202537Z-a1ca7df2cf1c`,
scope `independently accepted firmware-seen gem5 lifecycle stop; child-9/wrapper1, preserved partial outputs; no scientific pass or graceful checkpoint/statistics flush`. Intentional interruption proves lifecycle/retention, without
a scientific pass, completed matrix or checkpoint/statistics-flush guarantee. Original Library binary
remains unavailable; the verified c822 pinned rebuild is a distinct artifact with its own provenance.
M0 history is preserved; #16 and M1–M5 remain open. No complete gem5 RandomX matrix/full dataset,
intended timing-core/SMP/BOOM, calibrated timing, physical power/efficiency or RTL acceptance is implied.
Whole Codex daemon termination/host reboot/power-loss tests and full hermetic dependency closure remain
unperformed. No scientific checkpoint resume exists; failed/torn records are preserved for additive
manual independent reconciliation, and recover never reruns scientific work.

The previous dated pre-cutover STATE is retained below as historical context. Preserve its byte-exact
original in a new exclusive public archive before this update; its historical pending statements describe
that earlier snapshot and do not override the actual proof above.

# Current state — dated pre-cutover technical snapshot

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

**M0 complete; M1-M5 remain open.** Expected local guest/runtime9 are independently accepted; no
complete gem5 RandomX matrix, timing calibration, measured power/efficiency or RTL exists.

## Persistent execution infrastructure — task#27

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

[Technical receipt](../docs/validation/local-migration-20261009/ACCEPTANCE.md),
[actual runtime](../docs/validation/local-migration-20261009/actual-runtime-v1/index.json) and
[independent review](../docs/validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json)
record original sources/inputs/model/output acceptance.
Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.


[Actual firmware-seen stop index](../docs/validation/local-migration-20261009/actual-gem5-running-stop-v3/index.json) binds44 selected public exports and both independent reviews.
The initial empty-serial stop remains initialization-only. The later intentional stop is accepted for
owned-process termination, inspectable failure/status, retained outputs and integrity, without a
scientific pass or Linux boot for that stop attempt.

The [owner resource directive](../docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
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

Immediately preceding d40f912 STATE/HANDOFF/SESSION_LOG are preserved byte-exact in their immutable commit and local
exclusive archive; public archive reference: `memory/handoffs/pre-cutover-20261010-d40f912-manifest.json and immutable d40f912 history`. Original
pre-migration and pre-LOCAL_VALIDATING snapshots remain retained.

Next at this snapshot: finish independent D_head review/actual merge M/D_merged and preactivation
eligibility acceptance, verify actual E/LOCAL_ACTIVE, then explicit #27 release L. Publish effective hub
notice only after L/readback; final synchronized acceptance/independent review/readback/protocol done
follows. All postmerge proof references are actual reachable publications, never future-file assumptions.

## Actual gem5 Linux runtime — PR #18 / task #16

[PR #18](https://github.com/jliu67/OpenRandomX/pull/18) contains the independently accepted configuration, runner, simulator acquisition workflow and actual runtime evidence. The declared model is one AtomicSimpleCPU, RVV disabled, 16-KiB L1I/L1D, 256-KiB L2, walker caches and 4 GiB RAM. It is functional exploration, not a BOOM/C920/SG2042 or calibrated timing model.

The original local and hosted builds timed out. One incremental resume completed the remaining large compilation units but hit an 8-GiB host linker OOM. A bounded recovery using upstream `--limit-ld-memory-usage` then linked successfully in 248.76 seconds, without recompiling target C++ or changing source/configuration. All 10,933 archived source files match. [Build and recovery evidence](../docs/validation/m3-fs/link-recovery-20261008/README.md) preserves both failure and success.

The original executable is 957,300,488 bytes, SHA-256 `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`. Real build-info identifies gem5 25.1.0.1. A verified package containing the original binary, immutable source/notices, build evidence and minimal Python runtime is saved in two parts. [Prior reuse provenance](../docs/validation/m3-fs/REUSE.md) remains preserved. That binary is currently
unavailable to the migration; the separately recorded pinned local rebuild is a new artifact.

**Actual Linux 6.8.12 boot and all nine RV64 runtime controls passed.** SIGILL recovery, RW/RX page permissions, explicit Linux flush-icache returns and generated-code execution 7 → 19 → 7 matched their exact oracles. The child exited zero with empty framed stderr, a completion marker and ordered hypercalls 1/2/3. A different agent independently replayed the raw serial/report and rehashed the simulator, firmware, kernel, disk and payload bindings. [Executed evidence](../docs/validation/m3-fs/actual-runtime-20261008/README.md) and [acceptance](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md).

The separate unchanged light-mode attempt reached its 1,200-second child limit. It repeated all nine runtime controls and verified/launched the hash ELF, but supplied no complete hash stream or hypercall 3. Independent replay confirms timeout and exact input bindings; it does not establish a hash mismatch. [Light outcome](../docs/validation/m3-fs/ACTUAL-LIGHT-REVIEW-20261008.md). **No complete gem5 RandomX matrix or full dataset is accepted yet.** Task #16 stays open. The nine runtime controls establish combined behavior in this single-core configuration; they do not isolate cache-flush causality or establish SMP/migration or intended timing-core coherence.

Final PR CI at `4f4cf17880ccfa2e904eb9d2dc23892b828bce12` passed 245 Python tests, 107 upstream tests, six native steady controls, 39 exact RandomX checks plus nine runtime checks per native/QEMU environment, and 26 gem5 offline controls. Optional hardware AES has one explicit skip per RandomX probe. [CI ledger](../docs/validation/m3-fs/streaming-ci-20261008/ci-review.json) distinguishes that CI from the actual local gem5 guest. Hosted manual builder/cache/artifact reuse remains unexecuted; its reviewed workflow no longer recompiles gem5 on ordinary PRs. A later separately reviewed runner fix streams flushed records before probe exit and preserves exact child/capture failure behavior; 245 total / 26 gem5 host tests pass. The actual guest evidence remains bound to the original runner snapshot.

## Reliable cancellation and extended light attempt — PR #25

[PR #25](https://github.com/jliu67/OpenRX/pull/25) merged at `abe066f7c1b17cb3225b55cc45848a153a20ea7a`. Its tree is identical to the independently tested source head `9d108c4041e0fa440a676f8a3ee1a2db1d736192`. The runner records SIGINT/SIGTERM, stops the child process group, reaps its direct child, restores handlers and validates completed runtime controls even if hash output is incomplete. Separate review repaired two interruption transition races before publication. Default wall timeout remains disabled; explicit positive wall limits and the simulated tick guard remain available. [Source/lifecycle acceptance](../docs/validation/m3-fs/cancellation-20261008/REVIEW.md).

All 253 Python tests (34 gem5 host/synthetic controls) and all 171 vendor files passed locally. Five source-head hosted checks passed; the two foundation jobs also passed 107 upstream tests and six native steady controls, and the two RISC-V jobs passed 39 required semantic/hash and nine runtime controls per native/QEMU environment. Optional hardware AES has one skip per hash probe. Independent artifact replay is in [the CI review](../docs/validation/m3-fs/cancellation-20261008/ci-review.md). Hosted guest execution was skipped by its manual guard; it is not actual gem5 evidence.

The new actual guest attempt reused those exact inputs with no wall cutoff. Independent replay accepts all nine runtime controls and 31 exact integer/FP checks, with zero hash values. Interpreter cache initialization began; its completion was not observed. Exact-ELF/Atomic review proves both mandatory cache round loops alone require at least `10,519,287,679,000` ticks, exceeding the configured `10^13` allowance. Root manually requested a tool-session stop at 23:54Z after that proof. The tool returned exit 1 and no final runner report; handler receipt, child return code and runner-performed reaping remain unknown. No matching wrapper or simulator process remains. No wall/tick timeout or hash mismatch was observed. [Actual partial acceptance](../docs/validation/m3-fs/light-resume-20261008/REVIEW.md), [raw/input evidence](../docs/validation/m3-fs/light-resume-20261008/README.md), [independently accepted budget proof](../docs/validation/m3-fs/light-resume-20261008/BUDGET-REVIEW.md).

The next unchanged matrix recipe declares `--max-ticks 100000000000000` explicitly; the larger finite guard is not guaranteed sufficient. The manual workflow selects it for light controls and retains `10^13` for runtime-only execution. A separately reviewed optional `--stop-file PATH` lets a different tool/PID namespace request the runner's own SIGINT/cleanup/report path without terminating its tool session. Final root validation passed 257 Python tests (38 gem5 host controls) and all 171 vendor files; [stop-file review](../docs/validation/m3-fs/stop-file-20261008/README.md). This new source was not executed by the saved real guest.

## Integrated software and dated research

[PR #17](https://github.com/jliu67/OpenRandomX/pull/17) merged at `973cd0d94f987ad4a46b85f7b6d66170104c64a1`; #13 is completed. Separate review repaired three malformed-input failure-report crashes without changing energy formulas. The importer passed 64 tests, valid-report preservation and 9,024 numerical checks. [Software acceptance](../docs/validation/p1-06s/PATCH-REVIEW-20261008.md) does not certify physical power collection. Earlier native/QEMU artifacts and independent replay remain in [RUNTIME-CI.md](../docs/validation/m3-fs/RUNTIME-CI.md).

[PR #19](https://github.com/jliu67/OpenRandomX/pull/19) merged at `0592c630fb9b2d05d00550e0a387a3a89c0819f5`; #4 is completed for dated source research. Released Monero consensus uses RandomX v1 by source-backed inference, not an independently observed tip. No actual mainnet v2 date appears in the audited schedule; the October 5 beta schedule is a separate stressnet with mock mainnet values. Keep v2-first research and exact v1 controls. [Audit](../docs/validation/monero-activation/REVIEW-20261008.md) retains 30 capture identities and 18 refetchable immutable files; time-varying raw responses remain temporary.

## Coordination review

Hub #5 and dependency summaries were corrected: #13 and #4 are completed; #10 now waits on #8 plus real host/meter access. Incident #20 was separately reviewed and closed as completed.

[PR #23](https://github.com/jliu67/OpenRandomX/pull/23), merged at `b562a941bec39c3a0747a2129903dd33bb471f62`, queues eligible announcements rather than allowing a single pending request to be replaced. Eight announcement tests and actual bot publication passed; #22 is completed. This was a source-identified loss risk, not proof an observed message had been lost. [Deployment evidence](../docs/validation/coordination/DEPLOYMENT-20261008.json).

The concurrent #24 policy and its session history are preserved. A separate agent accepted its compact major-handoff announcements; the original author corrected the duplicate decision ID at `a2128b9ee9dd93acdfc392bc4752e412f5e5a3d2`. #24 is completed. [Policy review](../docs/validation/coordination/POLICY-REVIEW-20261008.md). Announcements remain procedural; the router neither verifies engineering results nor launches AI workers.

## Remaining gates and next work

- #27: finish and independently verify migration acceptance; expensive research remains held. Inspect the linked acceptance receipt for exact pending gates and resume records.
- #16: after verified cutover, complete unchanged light v2/v1 interpreter/JIT controls on the designated local host, with a verified retained/rebuilt binary, explicit larger tick guard and reliable stop control; preserve partial results. Then address full dataset and every intended core/runtime separately.
- #8/#10/#11: controlled host matrix, synchronized wall power and dynamic profiling require actual host/counter/meter access. #13's software dependency is satisfied; parent M1 #1 stays open.
- #2: hardware identity/evidence remains open. Future Monero mainnet v2 activation and direct live-tip corroboration remain questions.
- #14 M4 requires completed #1/#3; #12 M5 requires #1/#3/#14. No RTL optimization before measured baseline and calibrated model acceptance.

Read live task comments and bot receipts for claims. Exact prior STATE/HANDOFF snapshots are archived under `memory/handoffs/pre-fs-reuse-*-20261008.md`; earlier snapshots and the full session-log prefix, including the concurrent inspector/policy entries, remain preserved.

## Final package integration and handoff

[PR #26](https://github.com/jliu67/OpenRX/pull/26) merged at `77a1641fb85f386bce4a5b51e00dedbe257376f6`, with the exact tested `78599e2812053c85037401e3f2e4d00191428427` tree. All five hosted source-head jobs passed; the independent reviewer checked 257 Python / 107 upstream / six native controls, 38 gem5 host controls, and native/QEMU 39 required plus nine runtime outcomes. Actual hosted guest execution was skipped. [Integration ledger](../docs/validation/m3-fs/stop-file-20261008/integration.json).

The session's [release](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6071620898) is accepted (ready, claim null, no warnings); the required [hub bot copy](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6071623180) is verified. No project simulator or wrapper remains running. Task #16 stays open for the complete unchanged light matrix.
