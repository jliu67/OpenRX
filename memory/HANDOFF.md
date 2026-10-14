# Handoff — actual designated local execution

## Reciprocal preparation candidate — task #69, 2026-10-14

[Task #69](https://github.com/jliu67/OpenRX/issues/69) adds once-per-immutable-program reciprocal preparation above accepted main `8f3b9bc3d7f0182d66185abe95310f0bab00274b`. Final server validation passes eight accounting tests, 48 native iterations/12 admissions, 11 RTL/four mapped checks and three intentional invalid elaborations, with zero final unexpected failures; four failed attempts are preserved. Preparation+execution clocks on the directed corpus are ideal 370444→159376 and stalled 398580→187512, including every reload; no full-hash performance is accepted. Actual default generic cache mappings are 75979/24877 baseline cells/flops and 152277/49640 prepared, guard 390/0; no full prepared-backend/physical PPA claim. [EXP-013](../experiments/EXP-013-prepared-program-reciprocals.md) and [evidence](../docs/validation/prepared-reciprocals/README.md) bind exact source, native/clock/synthesis results and fresh kernel receipts. Main 8f, PR65 exact4f and PR68 exacta4 plus all originals remain preserved.

Next action: independent exact-head feature review, then a complete comparable pipeline baseline with initial fill/generation, actual dataset/calibrated memory, 8×2048 execution and interprogram/final hash before performance acceptance. No own merge or architectural widening. Compute slot released; current claim and independent-review handoff receipts are indexed on task #69. Reproduce with `python3 scripts/test_prepared_reciprocals.py --output /tmp/openrx-prepared-reciprocal-validation-UNIQUE --synthesize` only inside a fresh authorized server admission. Draft [PR #70](https://github.com/jliu67/OpenRX/pull/70) preserves the original server result; its CI successor adds only explicit two-path binding guards and bounded hosted checks. All 219 executed inputs and accepted manifests are unchanged. Inherited complete native program-sequence/synthesis replay remains deferred and unexecuted pending fresh authorized serial admission; a hosted guard pass is not that replay. Independent review applies to the final exact head. Bounded successor validation passes 12 parent rejection tests, eight accounting tests and retained-evidence guards; fresh metadata payload peak 21762048 bytes, no swap/limit/OOM/throttle events. The following dated sections are retained historical snapshots.


## Native program sequencing — task #62, completed validation 2026-10-13

[Draft PR #63](https://github.com/jliu67/OpenRX/pull/63) adds native entropy/config
initialization and default eight-program ×2,048-iteration sequencing above original
accepted PR61 `7f299c74f81332257eefd775086b355969ad85f3`. Full native-v2 RTL
passes all 16,384 iterations/6,305,764 retirements/1,282,660 bytecode events/131,072
tail stores; full state and all 2 MiB per program agree. Nine current RTL and nine
mapped modes pass. Actual Yosys0.33 default whole mapping 249196 cells/12526 flops;
control 4500/2383. Short v2 clocks 110934/185396, v1 70110/120864. [Evidence](../docs/validation/program-sequence-20261013/README.md)
binds exact inputs/archives/resources and explicitly separates full native RTL,
short mapped control, default contract stub and bounded whole-top gates.
External initialization/generation/interprogram BLAKE2b/finalization and addressed
fixture dataset remain boundaries; full actual dataset/hardware hash/full v1
8×2048/physical PPA remain open. The owner-approved parent PR55/57/59/61 merges are complete on main
`9bbda64098bc6dfc999a67e1fdf9333abe0959d3`, whose tree equals the original
accepted base. PR63 now targets main without rebasing or regenerating the workload.
Original accepted sources and evidence remain preserved. New independent review is required; PR63 has no merge authorization.
[Design](../rtl/execute/PROGRAM_SEQUENCE.md) / [EXP-010](../experiments/EXP-010-native-program-sequence.md). Earlier initial/draft snapshots retain
their dated context.

## Native program sequencing — task #62, 2026-10-13

[Task #62](https://github.com/jliu67/OpenRX/issues/62) stacks on independently
accepted, unmerged [PR #61](https://github.com/jliu67/OpenRX/pull/61#pullrequestreview-5503154172)
at `7f299c74f81332257eefd775086b355969ad85f3`.
Two new modules initialize native program configuration and sequence the accepted
iteration executor through default eight programs × 2,048 iterations. Four short
v1/v2 ideal/stalled native-generated pilots pass. The full native-v2 job and new
control/reset/synthesis/mapped checks are pending; no pending test is a pass.
External initialization/program generation/interprogram BLAKE2b/final hash and
addressed fixture dataset are explicit boundaries. Full hardware hash/actual
dataset/physical PPA remain open. All accepted parent/main heads and original
sources/evidence remain preserved. New independent review is required; no merge
is authorized. [Design](../rtl/execute/PROGRAM_SEQUENCE.md) / [EXP-010](../experiments/EXP-010-native-program-sequence.md).

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

## Exact native floating execution handoff — task #58, 2026-10-13

[Task #58](https://github.com/jliu67/OpenRX/issues/58) /
[EXP-008](../experiments/EXP-008-native-floating-execute.md) extends independently
accepted, unmerged PR #57 at `d62c4495`, preserving both reviewed PR #55/#57 heads.
Unmodified licensed HardFloat1/8086-SSE supplies exact binary64 add/subtract/multiply;
FSWAP/FSCAL and native v1/v2 CFROUND/masks/DAZ+FTZ retain their exact semantics.
All 246 supported raw values execute; ten division/sqrt values still return held
errors. Complete VM/hash, selected core, physical memories and calibrated PPA remain open.

Twelve RTL and eleven applicable mapped modes pass: 19,968 full native primitive
vectors per variant, explicit balanced 3,840 mapped corner vectors, 2,928 actual
R/F/E/mode retirements, targets/dynamic PC, 872 arithmetic FP/584 CFROUND operations,
338 loads/104 stores/64 tail writes, four chains/aliases and all 2 MiB. All arithmetic
modes/64 CFROUND rotations/v2 apply+skip, unsupported/errors/reset/stale traffic,
atomic FP cancellation and unchanged raw-field/held-return transport are covered.

Shared/parallel units are 26,522/49,363 generic cells and 571/156 flops, with five/one
clock response latency. Integrated clocks 16,604/13,116 ideal, 33,574/30,086 stalled
differ by 3,488, exactly four per arithmetic FP operation. Complete default mapping
is 260,110/9,826. Shared whole-top and expanded old integer-sharing
matrices are absent; these controlled clocks/generic mappings are not physical PPA.
[Complete licensed evidence](../docs/validation/floating-execute-20261013/README.md)
binds inputs/commands/tools/fixtures/netlists/failures/resources/verified archives.

Original/pinned source/build/data/receipt assets remain retained. All 171 RandomX,
eleven HardFloat and 19/17/22 accepted component bindings are unchanged. Two own
wrapper-boundary failures and strict five-raw-value fixture correction are retained;
no criterion was relaxed. Twelve RTL modes and both actual mapped units passed
before complete top mapping reused their frozen code/fixtures. Source and complete
attempts are archived/verified, retired read-only preserving execute bits at handoff.
Unit/integration budgets were checked 2 GiB/6.5 GiB, CPU 600%, swap 512 MiB/2 GiB, Tasks 128,
six CPUs/one worker/fresh 1 GiB reserve; peaks 1,114,402,816/6,979,321,856,
integration swap 1,136,898,048, limit events 1202, no OOM/kills, CPU throttles 0.
Both payloads/descendants drained. Next: exact-head hosted checks then one independent
review of this new stacked draft. Neither reviewed parent nor new code is authorized
to merge. Earlier summaries retain dated publication context.

## Native multiply and branch handoff — task #56, 2026-10-13

[Task #56](https://github.com/jliu67/OpenRX/issues/56) /
[EXP-007](../experiments/EXP-007-native-multiply-branch.md) extends independently
accepted, unmerged PR #55 at `2b14e4f9` on a separate stacked draft. All 19 integer/branch
families (161 raw values) now execute actual native semantics; all 95 FP/CFROUND
values still return explicit held errors. Nine RTL and eleven applicable mapped
modes pass against unchanged native arithmetic/compilation/execution, including
2,736 retirements, native targets/dynamic PC, complete 2 MiB, stores/chains, held
traffic/stale tags/error/reset and unchanged raw-FE/all-rounding-mode transport.

Direct/iterative clocks are 12,036/30,596 ideal and 29,502/48,062 stalled, exactly
32 extra per each of 580 products. Actual unit cells/flops are 25,723/81 versus
5,528/537; reciprocal 1,374/153. Complete default mapping is 189,296/8,396.
Iterative full-top synthesis is absent; its mapped arithmetic units run with RTL
controller/executor. Fixture clocks/generic cells do not establish physical PPA
or full-hash performance. [Licensed evidence](../docs/validation/multiply-branch-20261013/README.md)
binds exact source/commands/tools/fixtures/logs/netlists/failures/resources.

One serialized worker used actual CPU 600%, RAM 6 GiB, swap 512 MiB, Tasks 128,
six-CPU affinity and fresh 1 GiB OS reserve; measured full-run peak cgroup 5,853,196,288 bytes,
peak swap 0 bytes, no OOM/limit hits/quota throttle. Payload/descendants
drained; source and complete attempts are archived/verified and retired read-only
at handoff, preserving execute bits. All prior pinned/bound assets remain. Strict
coverage rejected the first fixture before DUT tests; explicit rotations repaired
coverage without changing production RTL. A terminal disconnect stopped the first
driver at a progress print after successful synthesis (rc120/BrokenPipe). The
three remaining mapped tests reused the exact netlist in a fresh checked 1 GiB
payload (rc0), peak 1,013,276,672 cgroup bytes and zero swap/OOM/limit hits/CPU
throttles, with durable console output and no synthesis rerun. Both original
failure and completion evidence are retained. Next: exact-head hosted checks and one
independent review of this new extension. No merge is authorized; PR #55 remains
draft/unmerged. FP, complete VM/hash, physical memories, selected core and calibrated
timing/power gates remain open. Earlier summaries retain dated publication context.

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

## Working v2 AES-stage handoff — 2026-10-12

[#48](https://github.com/jliu67/OpenRX/issues/48) supplies tested synthesizable
`rtl/aes` code, licensed pinned IP, a VM-completion/writeback interface, v1 XOR path,
standalone software oracle and `scripts/test_aes_rtl.py`. All declared round,
mixer, integration, mapped-netlist and output/parameter guard checks passed.
[EXP-003](../experiments/EXP-003-v2-aes-rtl.md) and [raw exports](../docs/validation/aes-rtl-corrected-20261012/README.md)
show a 17→5 cycle request interval and 40,848→84,999 generic cells. Clock timing,
physical area/power and full-hash benefit are unavailable. Initial source/results remain retained; review identified and corrected the
v1 F XOR E boundary. Complete attempt10 passed both corrected configurations
and mapped netlists under a checked 4-GiB budget. Both job cgroups are absent and the global slot is free.

Next action: independent review of this new exact feature head. Reproduce with
`python3 scripts/test_aes_rtl.py --output /tmp/openrx-aes-fresh-attempt --synthesize`
using adequate RAM and the existing shared-host slot/admission policy. The draft
PR is not merged; #8/#16 and selected-core/calibrated-PPA gates remain open. Do not
restart the rejected native batch or another source survey for this handoff.
Temporary authoring is archived and retired into a read-only execution snapshot
at handoff; originals, builds, data, receipts and cancelled sync remain retained.

## Current accepted pilot handoff — 2026-10-12

Read [the independent exploratory acceptance](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969) and
[pilot evidence](../docs/validation/native-pilot-20261012/README.md). Execution
`20261012T185152Z-97e747b1f6c4` finished/drained with scoped input/output/receipt/
review integrity verified; native source stays `4a4e30bbbda47cce7713c280d87f1506f7c6f954`. The pilot completed
two balanced v2/v1 repeats at one six-worker hardware-AES/full-dataset/JIT setting.
#8 remains open/review after the owner released its scoped claim; formal #8/M1
acceptance is incomplete. Prior fixture-only and running/pending handoffs are history.

Next preparation is one separately reviewed formal balanced thread/AES baseline
request, using existing accepted tools/builds, complete coverage and at least
four balanced formal repeats under declared controlled settings. Carry forward
the pilot's v2 repeat spread and calibration/thermal limits; no next payload or
settings change is authorized by this document. Every subsequent execution still
needs its own request/source/runner/input binding, fresh host/kernel admission
and a serialized slot. The terminal slot release is not a current health check.

Keep #16's accepted 39-required + nine-runtime light matrix at scientific source
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726` distinct: optional hardware AES skipped,
broader gem5 full-dataset/intended-core/SMP still open. Native full-dataset pilot
results do not satisfy the gem5/intended-core gate, and leave M1–M5,
physical power/PMU, selected-core/calibration or RTL/ASIC requirements.

## Current accepted light-matrix handoff — 2026-10-12

Read [#16's independent terminal result](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891) and
[selected evidence](../docs/validation/m3-fs/accepted-light-matrix-20261012.md)
before continuing. Execution `20261012T032030Z-65cbb4c0cf9e` completed all
39 required light controls (31 arithmetic + eight software hashes) and nine
runtime controls; optional hardware AES was skipped. Scientific source stays
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`; do not relabel the accepted build,
request, raw serial or receipts with a newer documentation head. Input/receipt
integrity, final statuses, descendant/cgroup drain and slot release are verified.

The monitoring claim was released; #16 is open/router-ready at that readback,
with no successor launched by its closeout. Full dataset, intended-core/SMP,
BOOM/selected-core, timing, measured power, RTL and M1–M5 remain separate gates.
Next native work is limited to tiny-supervisor-fixture preparation/validation
on the diagnostic thread; a native benchmark pilot has not been launched or
accepted here. Every later payload still needs its own reviewed source/runner/
input/request identity, fresh host/kernel checks and serialized slot admission.

Reuse the [completed #41 planning decision](../docs/research/X9-V2-REUSE-DECISION.md)
and preserved builds; no core/AES hardware selection or v2/PPA result follows.
The preceding mission/attempt statements below are retained dated snapshots;
this current light-gate handoff supersedes their incomplete-matrix wording only.

## Current mission handoff — X9-class v2 ASIC, 2026-10-12

Follow the owner's narrowed [mission](PROJECT.md#user-intent) and [bounded path](../docs/ROADMAP.md#current-priority-path--2026-10-12):
reuse pinned RandomX, accepted tools and preserved builds; assess the provisional
BOOMV3/open-IP fit and v2 main-loop AES versus scalar software AES using evidence.
Reverse engineering supplies only traceable facts; X9 internals/topology, measured
v2 efficiency and competitive PPA are unestablished. Defer unrelated broad surveys
and X5 reconstruction while retaining open questions and historical evidence.

Earlier source-only eligibility pointed to [#41](https://github.com/jliu67/OpenRX/issues/41); that work is completed and the current build-first manager assignment above supersedes this prior routing instruction. #2 is owner-priority-blocked via the existing router and stays unresolved. The ready pool is Issues plus router labels/bot JSON, not a separate local task file. Use the narrowed overlay before numeric milestone order; reuse completed #13 importer software.

Keep #16's existing correctness request and oracle unchanged. Controlled #8,
physical #10, profiling #11, selected-core #3 and calibrated #14 gates still precede
#12 RTL optimization; this mission does not authorize new execution or hardware.
[Alignment #39](https://github.com/jliu67/OpenRX/issues/39) contains the draft head,
review/CI and issue/hub pointers; read actual PR state before treating its canonical
text as merged. A distinct GitHub Projects board could not be verified with the
available read access; repository board/issue alignment is reported separately.

## Current native handoff — accepted supported correctness, 2026-10-12

Execution source `4a4e30bbbda47cce7713c280d87f1506f7c6f954` remains pinned.
[Merged PR #36](https://github.com/jliu67/OpenRX/pull/36) implements the unchanged
scientific harness's external staging/input/output flow. Different agents
accepted its source, build `20261012T013303Z-848c58102f71` and supported correctness
`20261012T024840Z-8c34147db074`. [Selected public evidence](../docs/validation/native-staging-20261012/accepted-results.json)
keeps raw receipt identities separate from a non-identifying summary; complete
private records, exact conditional witness and external journals remain retained.

Supported result: 106 upstream passes and one source-defined conditional skip;
six unchanged native tests/four configurations, eight exact controls, two
17-nonce differential matches, 16 invalid-CLI rejections and four deliberate
duration rejections. Unexecuted configuration/all-ISA coverage remains open.
Both successful receipts verify, original inputs are unchanged, descendants
drained and native slots released. Preserve the earlier pre-compile failure and
no-child admission denial, their permanent keys and all prior evidence.

[PR #36 merged at 77cc171a](https://github.com/jliu67/OpenRX/commit/77cc171a935780788ceceb15f75d5c0e3a556650);
[task #35 completed after final review and postmerge CI](https://github.com/jliu67/OpenRX/issues/35#issuecomment-6117228235).
Keep code/vendor/test hashes identical to executed source, and never relabel
old execution artifacts with the merged documentation head.
Any future controlled pilot needs its own pinned request, declared host/settings,
duration/affinity/oracle, fresh admission and uncontended root-granted slot.
#8/EXP-001/M1 throughput/power remain open; short functional rates are diagnostic.
No new workload or identifying host inventory is published here. Read live task
coordination for other payloads; the historical handoffs below are preserved.

## Native staging software handoff — 2026-10-12

Session `codex/native-staging-20261012`, [#35](https://github.com/jliu67/OpenRX/issues/35),
base `3ee72cc4840b35b7a4e655276f100ab699c8f4cb`. Owner explicitly approved
adapter/tests and a draft PR. No new agent task was launched. Temporary /tmp
authoring only; all original/pinned scientific sources/builds/data/receipts remain
preserved and Git synchronization stays disabled. This package changes native
location/staging infrastructure and leaves workload/options/acceptance intact.

[Validation](../docs/validation/native-staging-20261012/README.md) records 16 new
passing fixtures, 313 exercised lightweight tests (one sandbox socket denial with
passing targeted rerun), 171 vendor checks, commands, distinct raw/public digests
and all unexecuted heavy checks. Parent-thread message delivery was unavailable,
so no compute slot was received and no native build/control request was submitted.
Different-agent source/evidence review remains pending; no merge or acceptance.

Next: review the exact feature head, then coordinate the shared slot and submit
the [unchanged-runner build and native-control specifications](../benchmarks/steady/README.md#isolated-local-staging-and-controls)
with fresh keys/IDs, exact source/toolchain/input identities and fresh host/kernel
resource checks. Initial build candidate: six workers, existing owner-local-max-v1
budget selected from measured headroom; retain utilization and peak memory.
Wait for final build receipt plus runner verify before consuming artifacts.
Full-dataset controls require their own serialized request, then controlled #8
pilots/formal matrix require separate experiment authorization/settings/duration.
No performance/power/PMU or M1 conclusion follows from software fixtures.
PR/claim-review/hub publication URLs and retirement archive are on #35; read the
actual readbacks rather than assuming this draft has been independently accepted.
All earlier handoff text remains below.

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

Read current task claims and leases before work; no permanent role or central coordinator is established.
For local inspection, select the installed immutable release bound above:

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
export OPENRX_RUNNER="$OPENRX_LOCAL_ROOT/releases/runner-v1-657b23f1/local_execution.py"
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify 20261009T193937Z-576aa858c033
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify 20261009T202537Z-a1ca7df2cf1c
```

Inspect manifests, retained raw logs, source/input hashes and strict independent review before consuming
results. stop preserves evidence; scientific retries use a new reviewed request key/execution ID. Do not
clear request mappings, truncate journals or treat sanitized public chains as host original bytes.

The previous dated pre-cutover HANDOFF follows as historical context. Preserve its byte-exact original
in a new exclusive public archive first. Its retained recipe is inactive unless the current reviewed
request, resource profile and explicit release authorize it.

# Handoff — dated pre-cutover technical snapshot

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

This handoff assigns no permanent role or coordinator. Read live claims and latest #27 task proof,
[policy](../docs/LOCAL_EXECUTION.md), [runbook](../docs/LOCAL_MIGRATION.md),
[technical receipt](../docs/validation/local-migration-20261009/ACCEPTANCE.md), hub#5 and actual remoteHEAD.

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

[Actual runtime index](../docs/validation/local-migration-20261009/actual-runtime-v1/index.json) and
[independent review](../docs/validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json)
accept expected guest/strict9/original source/input/model/output identity. Native controls/vendor/upstream
and final287/40 source evidence remain exactly snapshot-bound; optional capability skips explicit.
Corrected988/5c immutable runtime source b4b5ffc remains distinct from later docs/evidence commits.
Build02 OOM/stoppedv2/withdrawn916/frozenwrapper race and initial200904 stop scope stay retained.

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

Next: independent final-head/document review and actual merge/merged-tree consistency audit, then
acyclic F/Q/C/R readiness and actual E/V. Hold expensive work until explicit L/release is real/readback.
Publish hub effective policy afterward and verify bot; W/Z/external exact-Z review and final publication/
protocol completion follow. Do not relabel scientific execution source as the final docs/merge commit.

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
export OPENRX_RUNNER="$OPENRX_LOCAL_ROOT/releases/runner-v1-657b23f1/local_execution.py"
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify 20261009T193937Z-576aa858c033
```

No checkpoint resume. Corrupt/torn manifests/receipts/ledgers remain preserved and held for additive
manual independent forensic reconciliation; never clear mappings or automatically rerun. Public/raw
digests stay separately indexed and no private paths/credentials/binaries enter Git.
Immediately preceding d40f912 handoff/state/log are byte-exact in their immutable commit and local archive; actual public
archive reference: `memory/handoffs/pre-cutover-20261010-d40f912-manifest.json and immutable d40f912 history`. All earlier archived handoffs stay intact.
The historical recipe below remains inactive and never overrides live explicit-release authority.

## Previous handoff — reviewed cancellation; partial guest and tick-budget proof

2026-10-09 UTC; session `codex/20261008-light-resume`. User authorized continued engineering after extensive repository, agent-message, board and handoff ingestion. Read live [#16](https://github.com/jliu67/OpenRX/issues/16) comments/receipts and current main before claiming work. The repository is now **jliu67/OpenRX**, same repository ID 1409576804. Historical OpenRandomX URLs redirect; use OpenRX for API calls. This document is not a live ownership registry.

## Accepted implementation and actual outcome

[PR #25](https://github.com/jliu67/OpenRX/pull/25) merged at `abe066f7c1b17cb3225b55cc45848a153a20ea7a`. Its tree equals tested source head `9d108c4041e0fa440a676f8a3ee1a2db1d736192`. Independent review repaired two cancellation races before publication; 253 Python tests, including 34 gem5 host controls, and 171 vendor files passed. Five source-head hosted checks passed; separate artifact replay retained 107 upstream / six native steady checks and exact 39 semantic/hash plus nine runtime controls per native/QEMU environment. The hosted gem5 guest job was skipped. [Lifecycle acceptance](../docs/validation/m3-fs/cancellation-20261008/REVIEW.md), [CI replay](../docs/validation/m3-fs/cancellation-20261008/ci-review.md).

The fresh real guest independently passed all nine runtime controls and all 31 integer/FP controls, with **zero completed hash values**. Interpreter cache initialization began; no cache pass, complete hash stream or final hypercall was observed. Exact ELF/configuration review proves both mandatory cache round loops alone require at least **10,519,287,679,000 ticks**, exceeding the current `10^13` per-call allowance. A manual tool-session stop followed that proof at 2026-10-08T23:54Z. It returned exit 1 with no final runner report; actual handler receipt/child return code/reaping are unavailable. No matching wrapper or simulator remains. No observed wall/tick timeout or hash mismatch occurred. [Actual partial acceptance and raw/input bindings](../docs/validation/m3-fs/light-resume-20261008/README.md), [budget proof](../docs/validation/m3-fs/light-resume-20261008/BUDGET-REVIEW.md).

The new optional stop-file control and manual workflow light guard have separate host/source acceptance. Final root validation passes 257 Python tests (38 gem5 controls) and all 171 vendor files; [review and logs](../docs/validation/m3-fs/stop-file-20261008/README.md). They were not executed by that saved real guest. Default no-wall policy, strict validators, workload, resources and model remain unchanged.

## Historical pre-migration execution recipe — inactive

Reuse the original simulator; do not repeat a source build. [REUSE.md](../docs/validation/m3-fs/REUSE.md) gives the two saved parts, exact digests, reconstruction and runtime environment. The original simulator SHA256 is `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`; runtime ELF is `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`; retained hash ELF is `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`. Newly built hosted hash ELF `0e310b9c...` is separate evidence, not this payload.

This pre-migration recipe records the formerly intended sandbox execution inputs. Do not execute it during
migration or use it to bypass the designated host. After cutover, request a fresh durable local attempt with
verified input identities through the local execution interface. Historical command:

```bash
LD_LIBRARY_PATH=/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu \
python3 simulator/gem5/run.py \
  --gem5 /tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt \
  --resources /tmp/openrx-fs-resource-audit \
  --runtime-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe \
  --hash-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe \
  --output-dir /tmp/openrx-gem5-light-next-attempt3 \
  --max-ticks 100000000000000 \
  --stop-file /tmp/openrx-stop-next-light-attempt3
```

Monitor continuously and preserve raw output. The larger finite guard is proposed, not guaranteed sufficient. From another tool session, create the stop file to request the runner's own SIGINT cleanup/report path; never reuse an existing stop marker. Tool/session control-C did not yield a final report in the recorded attempt, so do not infer that outcome. Positive `--timeout SECONDS` remains opt-in. If inputs disappear, restore the saved package and prepare pinned resources before launching; missing inputs are not guest failures.

Acceptance requires exit zero, complete runtime/hash frames with zero statuses and empty stderr, all nine runtime and 39 required semantic/hash controls (eight v2/v1 interpreter/JIT hashes), consistent summary/optional AES skip, guest completion, ordered hypercalls 1/2/3 and unchanged input identities. Do not shrink RandomX constants or infer hashes from partial arithmetic controls.

## Remaining project gates

M0 is complete; M1–M5 remain open. #13 importer software and #4 dated source audit are completed; #20 inspection, #22 queued announcements and #24 compact-handoff policy are completed. #8/#10/#11 require controlled host/counter/meter access. #2 lacks primary X5 board/chip/firmware binding; documented stock SG2042 properties do not identify an X5 derivative. Future Monero activation/live-tip corroboration remains open. Full dataset, intended cores/SMP and selected BOOM Linux boot are separate from Atomic functional controls. M4/M5 still require measured baseline and calibrated model; no RTL, timing or physical efficiency result is established.

All 171 vendor files are now materialized and verified locally; the former four-PDF snapshot omission is resolved. Prior STATE/HANDOFF snapshots are archived under `memory/handoffs/pre-light-resume-*-20261008.md`; original timeout/build/OOM records and SESSION_LOG history remain unchanged. PR #26 integrated at `77a1641fb85f386bce4a5b51e00dedbe257376f6`, with the tested head/tree unchanged. [Final release](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6071620898) is accepted: ready, claim null, no warnings. The required [hub bot copy](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6071623180) was verified. [Integration/CI receipts](../docs/validation/m3-fs/stop-file-20261008/integration.json) preserve exact source/run/job identities.
