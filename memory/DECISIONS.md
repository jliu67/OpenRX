# Decision log

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D001 | Target v2 first; compare v1 | Avoid optimizing only an older workload | Upstream algorithm changes |
| D002 | Vendor unmodified v2.0.1 at a commit SHA | Complete code included, reproducible checkout, preserves licensing | Validated upstream update |
| D003 | Same release for v1/v2 comparisons | Controls library/JIT differences; v2 flag selects workload | Historical release comparison needed |
| D004 | Private remote initially | No user visibility preference given | User requests open publication |
| D005 | No RTL in foundation | Need correctness and credible workload model first | Baseline and simulator gates pass |
| D006 | No efficiency number without power measurement | Hashrate does not establish energy efficiency | Power sampling implemented |
| D007 | Separate source-derived slots/opcode weights from dynamic execution and performance | Static counts cannot identify a hardware bottleneck | Dynamic traces and calibrated model exist |
| D008 | Reject ignored single-thread affinity; preserve vendor source | Upstream dispatch passes CPU ID -1 in this path; silent acceptance corrupts comparisons | An explicitly reviewed affinity/backend change exists |
| D009 | Treat CI as correctness evidence; retain M1 as open | Hosted one-repeat controls have no controlled host/power baseline | Known-host matrix and time-aligned power meet acceptance |
| D010 | Use docs/TASKS.md, issue claims and memory/HANDOFF.md for collaboration | User made this repo the persistent project board for agents | User changes project workflow |
| D011 | Label separate-process warmup and inferred intervals explicitly | They are not same-VM cache warmup or synchronized meter timestamps | A tested steady-state measurement adapter is available |
| D012 | Use GitHub issue threads for conversations and Markdown for durable memory | Avoid a single shared mutable chat file; preserve reviewable task-specific communication | Repository scale or user workflow changes |
| D013 | Separate deterministic message routing from AI execution | Installing an inbox must not silently provision paid model workers or imply agents are running | User authorizes a bounded model/runtime configuration |
| D014 | Use advisory four-hour actor/session claims and full-history reconciliation | Reduce accidental overlapping work and recover superseded events without claiming transactional locks | Real usage exposes lease, scale or stronger isolation requirements |
| D015 | Add an opt-in same-process library adapter; retain the old upstream control harness | Obtain persistent dataset/VM/worker trials without modifying pinned algorithm source | Benchmark scope or platform support changes |
| D016 | Compare throughput only within one declared harness | New static-stride first/next/last batching has different overhead from upstream dynamic scheduling/tail; matching hashes do not imply equivalent timing | Controlled harness-overhead study justifies a comparison |
| D017 | Record monotonic/realtime brackets but leave power alignment unverified | Clock units/resolution and bracket widths are not a calibrated meter chain; duration excludes initialization and includes synchronization | A tested importer and real synchronized meter evidence exist |

| D018 | No coordinator, assigned agent roles or centralized work allocation | User clarified independent agents periodically visit and choose tasks; any capable visitor can claim or review | User changes governance model |
| D019 | Treat protocol comments on each specific task issue as the **only live claim authority** | Avoid conflicting ownership between milestone issue #1, role inboxes and Markdown board; one independently claimable subtask per issue | Stronger transactional locking is needed |
| D020 | Block issue-dependent tasks until all prerequisite issues close as completed | Prevent premature M4/M5 work and make dependencies machine-readable; missing/not-planned/malformed prerequisites fail closed | Human review/model evidence requirements change |
| D021 | Preserve v1 commands and issue histories while retiring role inboxes | Non-destructive migration: legacy route ROLE joins shared queue; no false active agents | Legacy clients are retired and compat can be removed |

Integration note: D012-D014 already published by the communication package retain their IDs. The unpublished P1-05 branch's conflicting proposed IDs were assigned D015-D017 during reconciliation; no communication decision was replaced.

## P1-06S — 2026-10-08 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D022 | Start with strict whole-system AC point-power JSON bound to a revalidated steady run and explicit affine clock calibration | Avoid guessed units, wrong runs, CPU-package/wall-power confusion and unsupported averaging/counter semantics | A real meter/export and independently reviewed response/conversion model justify another schema |
| D023 | Use conditional worst-case error bounds and isolated synthetic outputs; never automatically certify physical evidence | Sample gaps and clock labels cannot establish calibration, unsampled waveform error or real power provenance; systematic bias must not vanish with repetition | Independent physical validation and review establish stronger evidence or a better error model |

## M3 feasibility — 2026-10-08 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D024 | Use unchanged scalar RV64GC/lp64d software-AES light controls as the first RISC-V execution gate | Pinned JIT has scalar fallback; actual QEMU exact hashes and all four rounding modes passed; optional vector/crypto objects still need compiler support | Full-dataset, candidate core or optional-vector paths are executed and reviewed |
| D025 | Provisionally select Chipyard 1.14.0 / MediumBoomV3Config for open RTL research | Traceable scalar FP/div-sqrt core and configurable memory path; source choice is not a performance ranking or accepted boot | Exact emitted config/Linux/hash/memory evidence or measurements favors another candidate |
| D026 | Investigate gem5 full-system Linux before accepting unchanged RandomX runtime; do not call generic O3 BOOM/C920 | SE signal handling cannot recover startup ISA probes, cache-flush syscall259 is missing, mprotect ignored; QEMU has different coherence semantics | Independently validated full-system runtime or separately reviewed simulator fixes exist |


## Linux runtime/import review — 2026-10-08 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D027 | Require explicit Linux signal/protection/flush/overwrite controls before runtime hash acceptance | Known QEMU hashes do not independently establish OS/JIT contracts | Selected core/runtime and SMP/migration controls provide stronger evidence |
| D028 | Accept repaired P1-06S software separately from physical measurements | Independent review repaired failure-report bugs; no actual meter/host evidence exists | Real calibrated synchronized power meets M1 |
| D029 | Explore pinned gem5 full-system Linux with AtomicSimpleCPU, supported classic caches, scalar guest controls and 4 GiB backing | Pinned SE ignores required Linux signal/protection operations; the official full-system example supplies the declared cache/boot path | Accept only executed controls; repeat on intended cores before timing or coherence claims, and keep M1/M4/M5 gates |

| D030 | Require a short hub #5 announcement for significant outcomes, blockers and milestone changes | Independent visiting agents need cross-task visibility without lengthy repeated logs or permanent coordination roles; task issues remain the claim/evidence authority | An audited automated gate or a different notification mechanism is justified |

## Simulator reuse and coordination review — 2026-10-08 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D031 | Reuse an exact verified simulator binary for guest runs; keep source builds manual and checkpoint partial work | Repeated cold gem5 compilation exhausted CI before guest execution; the older upstream container lacks this setup's required guest API/fix | A compatible upstream binary is independently verified or the source/configuration changes |
| D032 | Queue eligible hub announcements and require separate-agent acceptance evidence | A single pending workflow slot can replace an unprocessed announcement; router labels cannot certify independent review | GitHub scheduling or project governance changes |

Reconciliation: the concurrent hub-policy entry reused D029, already assigned to atomic gem5. Separate review accepted its unchanged policy and the unique-ID correction to D030. The new simulator/queue decisions start at D031; all earlier decisions and session history remain preserved.

## Long guest execution — 2026-10-08 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D033 | Keep guest wall cutoff opt-in; explicitly stop and reap the simulator on cancellation while retaining completed controls | The prior 1,200-second bound mostly covered boot and exposed no complete hash matrix; unlimited waits require reliable explicit cancellation and truthful partial evidence | Observed workload progress justifies a declared limit or a different execution model is accepted |

## Extended guest budget and stop control — 2026-10-09 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D034 | Declare `10^14` ticks explicitly for the next unchanged light matrix; retain the runtime-only default and all strict completion checks | Exact retained-ELF loops and actual width/clock prove a conservative 10,519,287,679,000-tick minimum for two mandatory cache round loops alone, exceeding `10^13`; the proposed margin is not a sufficient-budget proof | Executed complete matrix or a changed ELF/model provides new evidence |
| D035 | Offer an optional fresh stop marker observed inside the runner's main wait loop | Tool-session control-C ended the actual attempt without a final runner report; a shared-filesystem request can reach the runner's own signal/cleanup/report path across PID namespaces | A verified tool/process interface provides equivalent lifecycle control; source/host review must remain separate from actual gem5 acceptance |

## Critical local infrastructure migration — 2026-10-09 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D036 | Designate the owner's Ubuntu computer for persistent expensive execution only after evidence-backed migration cutover | User requires loss-intolerant preservation, reproducibility, durable operation and verified scientific/lifecycle gates; temporary sandboxes remain for lightweight work | Required gates and reviewed merged PR pass; publish activation from objective evidence |
| D037 | Keep GitHub authoritative and use owner-mediated task submission/result publication; remote execution is unavailable | No secure remote access/listener/poller has been implemented or tested; avoid implying visiting agents can access the host or creating permanent roles | A separately documented secure submission/retrieval mechanism is implemented and demonstrated |
| D038 | Preserve original saved simulator identity and independently verify a separate pinned rebuild when original Library parts are inaccessible | A historic artifact save is not a current transfer; scientific provenance must distinguish an unavailable original from a new toolchain build | Exact original archive is retrieved and fully verified, or the separate rebuild passes local gates |

## Native staging preparation — 2026-10-12

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D039 | Use fresh external native build/output roots and verify successful build artifact/source bindings before staged launches | Retained sources are read-only inputs; retired CMake caches and source-relative results cannot satisfy the local runner output contract | Independent review or actual staged native evidence requires a different interface; scientific criteria remain unchanged |

Execution follow-up for D039 (2026-10-12): different agents accepted the actual
external build and supported native correctness. The fresh reviewed-range
allocation preserved the OS reserve and fail-closed kernel/headroom checks after
an earlier no-child denial. Exact conditional skips stay distinct from passes;
unexecuted configuration coverage and controlled throughput/power remain open.
This records the existing decision's result, not a change to scientific criteria
or resource policy. Detailed host witnesses remain private.

## Owner scope refocus — 2026-10-12

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D040 | Target an X9-class ASIC adapted to exact RandomX v2, with bounded reverse-engineering evidence and reuse-first open-IP engineering; defer unrelated surveys/X5 reconstruction | Owner explicitly narrowed the project to avoid open-ended research and recreating proven components | Traceable evidence changes the target or disqualifies the provisional reuse candidate; scientific gates remain unchanged |

This direction does not establish X9 internals, v2 measurements or competitive PPA,
select a final ASIC implementation, or waive #16/#8/#10/#11/#3/#14/#12 acceptance.
[Task #39](https://github.com/jliu67/OpenRX/issues/39) tracks the separately reviewed
canonical-text and non-destructive coordination proposal. Prior decision bytes are retained.

Routing follow-up for D040 (2026-10-12): apply owner-priority eligibility through
existing task protocol, not prose-only deferral or manual label deletion. #2 stays
open and blocked, while bounded source-only #41 supplies eligible X9/v2 target/reuse/
AES work. Current task selectors use the narrowed overlay before numeric milestones.
No router code, dependencies, acceptance gate or scientific completion changes.

## First-component execution — owner, 2026-10-12 20:49 UTC

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D041 | Implement the required v2 F/E AES mixer now under the direct owner's bounded phase exception; reuse pinned BSD secworks S-box IP and unchanged RandomX software as oracle | Deliver working execution hardware with tests, real synthesis and writeback integration instead of repeating completed source work; arbitrary raw E keys require round glue rather than a full cipher/key schedule | Exact correctness, integration or measured core profiling changes the design; no bottleneck, physical PPA or proprietary X9 claim is inferred |

[#48](https://github.com/jliu67/OpenRX/issues/48) and [EXP-003](../experiments/EXP-003-v2-aes-rtl.md) record implementation and evidence. Generic one-lane/four-lane comparison is 17/5 request cycles and 40,848/84,999 cells. The failed 2-GiB four-lane mapping is retained; a focused 4-GiB retry passed. Independent new-work review remains required, and broader scientific gates remain open.

## D042 — ordered scratchpad integration, 2026-10-12

Reuse PR49 unchanged and implement the actual post-dataset R/F store boundary with an explicit in-order 128-bit SRAM contract. Overlap independent captured R stores with AES compute, retaining R-before-F visibility for aliasing lines. Differential reference uses the verbatim pinned interpreter/bytecode and a declared dataset-line fixture, with full 2 MiB memory comparison. No accepted core/cache/fabric or SRAM macro exists, so do not infer full-core integration, hash speedup or physical PPA. [Task #50](https://github.com/jliu67/OpenRX/issues/50) / [EXP-004](../experiments/EXP-004-iteration-tail.md) carry new-work review and evidence.

## D043 — per-iteration memory and execute boundary, 2026-10-13

Own the actual scratchpad load/operand conversion and dataset/register-feedback
path around a tagged external arithmetic kernel. Reuse the merged AES/store tail
unchanged. Expose program/E-mask/rounding state and one ordered committed-memory
port, with generation-tag cancellation and explicit partial-write persistence.
Provide serial conversion and uncoalesced references to isolate control-cycle
gains; coalesce equal entry lines only under private exclusive-memory ownership.
The native bytecode memory differential and actual mapped netlists verify this
integration without claiming a full core, hash or physical PPA. Revisit on concrete
kernel/memory integration evidence. [Task #52](https://github.com/jliu67/OpenRX/issues/52)
and [EXP-005](../experiments/EXP-005-iteration-engine.md) require independent new-work review.

D043 correction follow-up (2026-10-13): fresh write priority cannot preempt an
already presented read. Retain its grant until acceptance, then block writes
until the response is consumed; reset clears the grant. Independent review
exposed this protocol defect, which the directed original-failure/RTL/mapped
regression now covers. Component clocks remain controller/replay model results;
physical PPA/full hash remain open.

## D044 — bounded native integer execution, 2026-10-13

Execute eleven native integer families directly behind the accepted iteration
interface, reusing its conversion/AES/store components and unchanged licensed
native compile/execute semantics for assertions. There is no accepted compatible
native integer core asset in the current repository; a larger RISC-V/FPU/core
integration is deferred. Unsupported multiply/FP/branch/CFROUND raw values trap
explicitly, including native reciprocal cases that could become NOPs. Compare a
one-clock two-add IADD_RS with a shared two-clock addition schedule, and verify
actual mapped kernels and one fully mapped connected top. Generic cells and
fixture cycles do not establish full hashes or physical PPA. Revisit when extending
the exact opcode set or integrating concrete memory/core/FP IP. [Task54](https://github.com/jliu67/OpenRX/issues/54)
and [EXP-006](../experiments/EXP-006-native-integer-execute.md) bind new-work review.

## D045 — exact multiplication and lexical branch targets, 2026-10-13

Extend the reviewed native executor with all remaining multiply/high-multiply/
reciprocal families and CBRANCH, retaining unsupported FP/CFROUND. Reuse an unsigned
128-bit product for low/unsigned-high/signed-high, with exact signed correction;
compare direct and radix-4 iterative hardware. A 64-step restoring reciprocal computes
the unchanged native integer quantity; zero/power-of-two native NOPs do not mark
register usage. Immutable programs, backward-only targets and each branch marking
all registers used allow a lexical first-visit tracker with one latest target
cache; replayed execution never changes compile-time usage. Native compiled targets
are assertions, not hardware inputs. [Task #56](https://github.com/jliu67/OpenRX/issues/56)
and [EXP-007](../experiments/EXP-007-native-multiply-branch.md) carry separate new-work
review. Revisit on exact opcode/interface evidence or technology timing/area; no
complete VM/hash or physical PPA acceptance is inferred.


## D046 — reused binary64 IP with exact native controls, 2026-10-13

Use unmodified Berkeley HardFloat1/8086-SSE for binary64 add/subtract/multiply,
retaining original license/bytes/archive/manifest. The native RandomX reference
uses DAZ/FTZ; adapt inputs to signed zero and flush on subnormal output or upstream
underflow flag, including rounding to minimum normal. Keep supplied after-rounding
control, first-operand NaN payload and native four-mode mapping. Do not invent or
approximate arithmetic. Preserve signed32 memory conversion, F/E/A selection,
FSCAL mask and v2-guarded/v1-unconditional CFROUND; FP never marks integer usage.
Expose one shared versus two parallel lanes with atomic vector retirement/reset.
Division/square-root trap until implemented. Full RTL primitive coverage and a
separately declared balanced mapped corner corpus retain exact native flags/bits.
[Task #58](https://github.com/jliu67/OpenRX/issues/58) / [EXP-008](../experiments/EXP-008-native-floating-execute.md)
require new independent review; generic cells/clocks do not accept physical PPA or
full hashes. Revisit on specific integration/technology evidence.

## D047 — native configuration and program-loop control, 2026-10-13

Initialize A/MX/MA/read selectors/dataset offset/E masks from native program
entropy, clear R per program and retain native round mode across default 2,048
iterations and eight programs. Reuse the independently accepted iteration and
arithmetic RTL without changes. External pinned AES/BLAKE2b consumes actual DUT
register output to generate each next program; golden data only enters assertions.
Keep scratchpad fill/program generation/interprogram hashing/final hash outside
the hardware boundary and the addressed dataset fixture explicit. Reserve a
non-overlapping PROGRAMS×ITERATIONS generation-tag span until all cancelled or
completed transport is quiescent; reset cancels work without memory rollback.
Validate full native-v2 RTL counts, v1 short transitions, default control counts
and bounded actual mapping. Do not treat the control backend stub as arithmetic
proof or short mapped gates as a full16k-iteration gate run. [Task #62](https://github.com/jliu67/OpenRX/issues/62)
and [EXP-010](../experiments/EXP-010-native-program-sequence.md) retain independent
review. Revisit on concrete hardware initialization/finalization/dataset integration
or technology timing/power evidence; full hash/physical PPA remain unaccepted.

## 2026-10-14 — Charge reciprocal preparation at immutable admission

Use one fully loaded 384/256-word image, epoch/PC tags and private native constants; repeated iterations reuse only the completed owned image. Zero/power-of-two raw unsigned 32-bit immediates remain lexical NOPs; same-address or identical reload is charged again. Reset/whole cancel invalidates arrays logically, execution cancel retains the image without undoing committed stores; generations cannot be reused while late replies can arrive. Keep default runtime execution and reject the legacy prepared-netlist ABI. Compare common native/memory work through disjoint measured clocks and nested observers; full pipeline unknowns remain null. [Task69](https://github.com/jliu67/OpenRX/issues/69)/[EXP-013](../experiments/EXP-013-prepared-program-reciprocals.md) require independent review and complete-pipeline baseline before full-hash claims or widening.


## 2026-10-14 — PR70 explicit parent binding and bounded hosted scope

Keep the original accepted compatibility manifest unchanged. Permit exactly the
two intentional executor successors only when old hashes match that manifest and
new hashes match both live bytes and the unchanged219-input server record; retain
default PREPARED_RCP=0 and reject other changes. Candidate hosted source/evidence
checks remain separate from the deferred complete native program-sequence/synthesis
server replay and independent acceptance. Preserve the initial hosted failure and
all scientific inputs/results. [Evidence](../docs/validation/prepared-reciprocals/README.md#hosted-source-binding-correction).


## 2026-10-14 — Restore PR70 actual program-sequence regression gate

The historical head1345 source-only route skipped native/mapped integration.
The corrected gate unconditionally runs the existing --synthesize regression;
binding/rejection checks remain additional guards. Fresh serial server validation
passes9RTL/9mapped/4invalid/3actualsynthesis, with exact mapped/RTL PASS equality.
All219 original science inputs and accepted manifests/old-new binding digests stay
unchanged. Existing8×4 native v1/v2 tests, default8×2048 control contract and bounded
whole-top native gates are separate scopes; no --full-v2 rerun or full-pipeline
performance acceptance. Sources/complete outputs and superseded binding-only CI
artifacts are preserved. [Evidence](../docs/validation/prepared-reciprocals/README.md#restored-integration-gate--2026-10-14).
Independent exact-head review remains required; no merge. Compute slot released.

## D048 — fixed native register-file BLAKE2b and buffered seeds, 2026-10-13

Reuse the pinned BSD2 four-G/message schedule while declaring a minimal core continuation correction. Preserve all original files and the demonstrated two-block mismatch. Hash exact 256-byte little-endian R/F/E/A with independently parameterized 64/32-byte digests; final scratchpad AES remains external. Buffer state/tag/index/round controls, hash exactly PROGRAMS-1 results and bypass the last. Gate the next descriptor/final result while a seed is held; reset cancels without rolling back accepted stores. Preserve and count the original 1,024 G operand latches, using exact licensed installed cell models for gates. Validate balanced native vectors, actual hardware-derived connected programs, errors/held/reset/cancellation and new-stage mapping without repeating accepted whole-core/full 16K baselines. [Task #64](https://github.com/jliu67/OpenRX/issues/64) / [EXP-011](../experiments/EXP-011-native-regfile-blake2b.md) require new independent review; no physical PPA/full-hash acceptance follows.

## D049 — native scratchpad A reduction and final digest, 2026-10-13

Reuse unchanged licensed AES round/S-box IP with one shared lane to scan actual
private quiescent memory in ascending128-bit beats. Apply distinct per-lane raw
keys, ENC0/2 and DEC1/3, then both pinned closing keys; replace all512 A bits only
with a successful returned finalization result. Feed raw R/F/E plus replacementA
to the validated/frozen draft independently parameterized 32-byte BLAKE2b path. Extend transport
tags to generation16+beat17 so a full2MiB scan never aliases an earlier read; do
not reuse a generation while late traffic is possible. Leave execution and all
initialization/dataset/full-hash/PPA boundaries unchanged. Actual new-stage cells
and fixture clocks, full2MiB RTL and bounded256B mapped tests remain distinct.
[Task67](https://github.com/jliu67/OpenRX/issues/67) /
[design](../rtl/hash/FINALIZATION.md) require new independent review.

## D050 — preserve both accepted parents and declare combined source bindings, 2026-10-14

Merge accepted main5f into reviewed reciprocal candidate35c without rebasing or
rewriting either parent's evidence. Preserve original53/69/219/246/259 manifests
and their exact source identities. Admit only narrowly named, exact digest-bound
successors in an additive combined declaration, retaining default PREPARED_RCP=0,
native mathematical criteria and unconditional actual integration gates. Changed
context is not an all-original-inputs-unchanged claim. Run affected execution,
hardware-seed and scratchpad-finalization regressions from one frozen combined
source under fresh serialized resource admission, then request new independent
exact-head review. Existing complete16K/native-v2 evidence is reused where its
inputs remain unchanged; this bounded combination is not a full-hash/PPA result.


## D051 — Recover verified components without relabeling a failed wrapper

The original combined runner failed only after successful unit/seed commands,
because external orchestration assumed a nonexistent seed-summary status field.
Preserve its failed receipt/traceback and exact complete outputs. Reuse that
bounded component proof only after immutable-runner integrity, complete source,
logged native/mapped results and input bindings verify. Run only missing
finalization under a fresh admitted request from identical frozen source.
Composite closeout binds both runner attempts and retains original failure;
neither source-only checks nor partial/skipped execution can satisfy a gate.
Publication changes only declared metadata/evidence; new exact-head independent
review remains required. No full prepared hash, physical PPA or own merge follows.


## D052 — connect actual native values before architecture feasibility, 2026-10-16

Use captured input and actual hardware-derived seeds for native software fill/
program callbacks; use unchanged pinned initDatasetItem values rather than an
addressed placeholder. Keep callback host seconds and unknown device/physical
cost separate from a closing transport/hardware ledger. Prove one complete default
v2 hash against unchanged randomx_calculate_hash, then validate recovery and
namespace reservation independently. Reserve a whole batch's image epochs before
admission; preserve generations across cancel/error and require drained transports
before hard reset. Retain exact full-source evidence and declared successors.
First correctness proof selects no engine count, issue width, scratchpad arrangement,
process or memory technology; physical efficiency and independent review remain
separate gates. [Task71](https://github.com/jliu67/OpenRX/issues/71) /
[EXP-014](../experiments/EXP-014-connected-v2-lifecycle.md).

## 2026-10-16 — task #72 model evidence boundary

Use the accepted full native-dataset fixture for traffic and lifecycle accounting;
use its direct per-clock bench counters when sparse CSV omits nested transitions.
Use the detailed accepted short successor only for its bounded actual bytecode
windows and explicitly measured FU spans. Keep alternative full-hash timing and
all uncharacterized device/provider/physical costs unknown. Width, context count,
FU II and memory policy are scenario inputs, never a production selection. Gate
further overlap with a parameterized context-tagged blocking hardware experiment,
finite arbitration/readiness instrumentation and native value/lifecycle checks.
