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
