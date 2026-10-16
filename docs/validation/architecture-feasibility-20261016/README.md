# Task #72: reproducible architectural model evidence

The [implementation and full contract](../../../tools/architecture/README.md)
and [EXP-015](../../../experiments/EXP-015-architecture-feasibility.md) explain
reproduction, source equations and validation boundaries. These are analytical
scenarios and necessary bounds. Full-hash timing of alternatives and physical
ASIC feasibility remain unresolved. No production engine count, clock, process
or memory technology is selected.

## Retained measurements and validation

- Full accepted native-v2 workload: 8 programs × 2,048 iterations, 6,306,885
  instructions and 1,434,807 bytecode memory events. Actual native light dataset
  values, every iteration/program boundary and the final digest passed the
  existing accepted connected RTL/native checks at source `c96e96ab`.
- Outer event-CSV timing matches 40,975,538 hardware/transport clocks and every
  accepted traffic ledger field. Fixed-state equations have zero stage/iteration/
  total residuals while explicitly retaining the **39,946,977-clock measured
  executor aggregate**. Nested iteration measurements are accepted per-clock
  bench counters, not inferred sparse-CSV durations.
- Bounded detailed successor: eight independently replayed first-iteration
  windows, 3,081 instructions and 668 bytecode memory events. Exact native route,
  memory address/order and store-lane checks pass. This 8×2 workload differs from
  the default hash's seed lineage after program zero.
- All eight scalar timing equations close with zero residual using explicit
  fetch/request/reply/store/return states and measured FU service inputs.
  This does not independently predict operand-dependent FU latency.
- 58 focused tests pass. They include malformed/omitted trace states, native
  route/address tampering, preservation guards, dependencies, barriers, memory
  ordering/bandwidth/banks/queues, FU occupancy/II, context isolation, power
  unknowns and strict rejection thresholds.

The first parser attempt failed because it assumed nested transitions were
recorded by the older sparse observer. That failed source/run remains preserved.
The corrected parser exposes nested CSV durations as null and binds direct bench
counters separately. The admitted corrected extraction passes; a separate admitted
portable reproduction checks the numerical comparison/sensitivity artifacts
byte-for-byte. No RTL, native hash or dataset-generation simulation was rerun.

## Bounded comparison example

Mean abstract cycles per bytecode-window job, over eight disjoint windows:

| Configuration | Contexts | Response 0 cycles | Response 10 cycles | Response 50 cycles |
|---|---:|---:|---:|---:|
| Single-issue blocking | 1 | 1,663.000 | 2,498.000 | 5,838.000 |
| Multicontext blocking | 4 | 961.125 | 1,276.625 | 3,376.594 |
| Limited nonblocking | 4 | 920.250 | 1,136.531 | 3,077.313 |
| Dual issue | 4 | 903.406 | 1,104.469 | 3,028.188 |

All 488 rows retain exact configuration inputs, including 1/2/4/8/16 contexts
and isolated bank/port/bandwidth/queue/II sweeps. The same nonpipelined FU pool,
conservative register/memory/control ordering and identical correlated trace
contexts apply. Memory queue slots and FU slots remain occupied through full
macro completion, including dependent post-response compute. Latencies 0/10/50
are arbitrary scenario inputs; none is fitted to the RTL aggregate. The changed
interface omits RTL fetch/protocol costs; scalar RTL calibration is separate.

These numbers describe finite batches of isolated bytecode windows. They
exclude outer entry/AES/tail, dataset service and the lifecycle, so neither their
means nor their speed ratios establish full-hash throughput. New hardware still
requires value/hash equivalence and issue/completion/readiness validation.

## Full-workload placement and target bounds

The real-dataset full trace contains 1,036,508 bytecode reads and 398,299 writes
of 8 bytes, plus 32,768 outer reads and 32,768 outer writes of 64 bytes. It writes
31,073 of 32,768 lines during execution. These counts replace the preliminary
synthetic-dataset scratchpad fixture. They describe one workload, not production
cache behavior.

Static-prefix backing scenarios below use independent 64-byte transfers with
masked stores, no reuse/combining/cache, and include cold fill/final scan:

| Local hot prefix per context | Scratch transfer bytes/hash | Dataset payload bytes/hash |
|---|---:|---:|
| 16 KiB | 38,422,336 | 1,048,576 |
| 64 KiB | 33,740,032 | 1,048,576 |
| 256 KiB | 15,536,192 | 1,048,576 |
| 512 KiB | 13,615,488 | 1,048,576 |
| 2 MiB | 0 | 1,048,576 |

At 1 MH/s, bytes/hash numerically become required bytes/µs: the 256 KiB scenario
requires 15.536192 TB/s scratch transfer plus 1.048576 TB/s logical dataset
payload before extra physical traffic. Its optimistic all-wall transfer ceiling
is **18.8425909847 pJ/bit**, assigning the entire 2,500 W budget to those transfers.
It is a rejection ceiling, not a memory energy estimate. At assumed 100 ns mean
service latency and one ready cold read/context, the same prefix's 104,607 cold
execution reads/hash require at least 10,461 independent outstanding requests/
contexts by Little's law; readiness and physical service remain unvalidated.

Every conventional live context retains 2 MiB of mutable state, wherever placed.
Nested hot ranges alias the same image. Dynamic cache hits, dirty evictions,
reconstruction/compression savings, macro area/leakage, physical random service,
frequency/process and controller command timing are unknown. Dataset values
were generated in light mode from a 256 MiB cache, not materialized full-dataset
storage or physical DRAM. Input hashing, fill/program generation and internal
dataset-provider device costs remain untimed and unknown.

The gate rejects correctness/order loss, insufficient capacity/outstanding
independence/sustainable service, <1 MH/s, or wall power >=2,500 W. Complete wall
energy must be <2.5 mJ/hash at 1 MH/s. Power requires compute/memory/provider,
controller/PHY/fabric, logic/SRAM leakage, refresh, VRM, fans/auxiliaries and PSU
losses; unknown terms remain null. Passing hypothetical necessary conditions
never demonstrates ASIC feasibility.

## Files

- `full-evidence.json`, `short-evidence.json`: bindings, locality, counters,
  explicit partial source-state calibration and provider boundaries.
- `baseline-calibration.json`: bounded scalar protocol equations/residuals.
- `comparisons.json`: 488 constrained window scenarios; full-hash rate/power null.
- `sensitivity.json`: placement/capacity, request latency, dataset, port,
  random/peak-efficiency and complete energy bounds with rejection gates.
- `provenance.json`, `artifacts.sha256.json`: actual compact input and public
  artifact hashes; measured/source-derived/assumed/unknown classifications.
- `validation.json`, `unit-tests.log`: reproduction checks and test evidence.
- The portable fixture is in `tools/architecture/fixtures/successor-first-iterations`.

Public evidence changes only three generic coverage-label strings from the
admitted derived measurements. Fixture source-map paths use public retained-input
labels. Provenance and the public artifact index are regenerated against these
exact published bytes. Original raw traces, input/source snapshots, failures,
commands, resource checks and receipts remain preserved on the authorized server.

Next hardware: a configurable context-tagged blocking dispatcher with independent
scratchpad namespaces, finite arbitration and explicit issue/completion/readiness
instrumentation, validated against native values and the existing full lifecycle.
Its evidence should gate wider issue and more aggressive nonblocking service.
Independent review precedes merge; this task performs no merge.
