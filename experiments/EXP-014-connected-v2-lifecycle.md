# EXP-014: connected prepared v2 hash lifecycle

[Task #71](https://github.com/jliu67/OpenRX/issues/71) / [draft PR #73](https://github.com/jliu67/OpenRX/pull/73)
build on merged main `aebe30a0c2d1547fed6b66976ba0757b4b66389a`.
The immediate gate is one reference-correct default v2 hash using actual native
dataset values. Architecture feasibility remains secondary; this experiment
selects no engine count, issue width, scratchpad arrangement, process or memory
technology. The whole-machine target remains 1 MH/s below 2,500 W, including
memories, PHY/controllers, fans and PSU losses.

[Design](../rtl/hash/LIFECYCLE.md) describes the explicit software/hardware
boundary. [Evidence](../docs/validation/connected-v2-lifecycle-20261016/README.md)
binds exact frozen sources, tools, commands, outputs, failures and receipts.
All original/pinned native and RTL inputs, previous experiments, builds and
receipts remain retained. No workload or acceptance criterion is weakened.

The hash request supplies `OpenRX connected prepared RandomX v2 lifecycle 20261016`
(55 bytes); the native cache key is
`OpenRX connected lifecycle dataset key 20261016`.
Native `initDatasetItem` supplies actual values on demand from a 256 MiB cache.
The logical dataset is 2,181,038,016 bytes; materialized dataset allocation is zero.
Initialization/fill and program generation remain software callbacks receiving
actual DUT input/seeds. Host seconds, unmodeled provider device cost and internal
physical memory traffic remain separate from hardware/transport clocks.

## Bounded simulator cross-check

Frozen execution `20261016T003513Z-18a0cadf8aeb` passes both Icarus variants for
one program × one iteration, ideal memory. Pinned Verilator execution
`20261016T010110Z-84a498089b69` reproduces both PASS records, complete cycle
ledgers and traffic exactly. Both receipts pass integrity verification.

| Mode | Preparation clocks | Execution clocks | Total hardware/transport clocks |
| --- | ---: | ---: | ---: |
| Runtime reciprocal baseline | 770 | 3,269 | 528,407 |
| Prepared reciprocal | 1,496 | 2,543 | 528,407 |

Both initialize all 2 MiB, load all 384 words, execute 384 retirements and 88
bytecode memory events, scan all 2 MiB, replace native A and return the native
32-byte digest. Eleven active reciprocals move 726 clocks from execution into
preparation. One iteration gives no net saving; it does not amortize preparation.
This is a deterministic correctness/cycle-accounting cross-check, not a controlled
throughput or energy baseline. EXP-001 controls and balanced repetitions remain
required for that separate acceptance.

## Default reference gate

The source of immutable full run `20261016T010320Z-b2c8ed47ab4c` is published at
`c96e96ab1eb46cb727b21befffa526e637ebed4a`. All 4,106 frozen source paths match
that public tree. Its native 8×2,048 fixture has passed unchanged
`randomx_calculate_hash`: 16,384 iterations, 6,306,885 instruction steps and
1,434,807 bytecode memory events. This native result alone is not an RTL pass.
The prepared/ideal RTL run passes all 16,384 iterations, 6,306,885 retirements,
1,434,807 bytecode memory events, eight admissions/3,072 loaded words, seven
hardware seeds and complete 2 MiB initialization/final scan. Its 40,975,538
hardware/transport clocks close exactly; the completed receipt verifies. The
returned digest in API byte order is
`ac16f4ddc7068d476a5e6e5c510c9d27a186e6468e5407225b71e3b51945c7c5`.
[Exact first-full result](../docs/validation/connected-v2-lifecycle-20261016/full-v2-first/summary.json)
is from public c96. The separately validated successor and consumed-source deltas are recorded below.

The driver checks actual input-derived initialization, actual hardware-seed-driven
program images, every native iteration state/route/memory event, dataset address,
all scratchpad bytes at each program boundary, final A and digest. No oracle
register, seed or memory image supplies DUT inputs. Cancellation/held/error and
namespace-capacity checks are separate profiles; available options do not imply
those profiles have passed. Exact completed successor records follow.

Whole-hash baseline/stalled comparison, autonomous hardware initialization/AES
program generation, physical dataset service, complete new-top mapping and
calibrated timing/power remain unaccepted. Model feasibility cannot replace
correctness evidence. Independent review of the final exact PR head is required;
no own merge is authorized.

## Recovery and paired accounting successor

[Serial successor](../docs/validation/connected-v2-lifecycle-20261016/recovery-paired/summary.json)
passes four baseline/prepared × ideal/stalled modes at 8×2, six cancellations,
eight selected matching faults and exact/insufficient batch capacity, hash-tag
wrap refusal and drained hard-reset recovery. The 31 unit checks cover ledger
closure, native-count/traffic equations and staging/CLI guards. The run's receipt
integrity verifies; all 171 pinned native files remain unchanged. Held successful
and error returns retain their fields, accepted writes persist, stale replies
drain, and recovery starts with a fresh generation/initialization request.

Both timing profiles measure 190 runtime reciprocal operations versus 95 prepared
constants. Each costs 66 measured model clocks; execution saves 12,540 while
preparation adds 6,270, leaving 6,270 fewer total clocks in each profile. All
common stages and native work match. These deterministic paired checks establish
ledger arithmetic, not statistical full-hash speedup or physical performance.
Nested executor/reply-wait/stale-drop counters and state-transition traces are
observations, not calibrated functional-unit service models.

[Four-state capacity](../docs/validation/connected-v2-lifecycle-20261016/icarus-capacity/summary.json)
separately checks the same source under Icarus. Its explicit interface-only status
claims no completed hash. [Consumed-source deltas](../docs/validation/connected-v2-lifecycle-20261016/source-deltas.json)
separate these runs from c96: batch admission, diagnostic clearing, stronger
assertions/accounting and host compiler flags changed; accepted math and native
dataset implementations did not. Full 8×2,048 was not rerun on this successor.
No source/output/receipt or failed attempt was replaced.
