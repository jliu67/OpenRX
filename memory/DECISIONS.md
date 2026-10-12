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
