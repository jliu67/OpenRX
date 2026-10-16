# Hardware initial scratchpad AES fill evidence

[Design](../../../rtl/hash/INITIAL_FILL.md) and [EXP-016](../../../experiments/EXP-016-initial-scratchpad-fill.md) define the bounded implementation above merged main `b8cd07070f4e38a0e784e0b123225856c7879f6f`. `HARDWARE_FILL=1` replaces live software AES fill with the existing licensed AES round; default `0` preserves the historical path. Input BLAKE2b, program generation and native light dataset callbacks remain untimed host providers.

## Exact executed sources

[Source proof](executed-source.json) separates standalone code `825f25502ad74f1dac40d3b287d173aca84ab5c1` at `/tmp/openrx-initial-fill-source02` from connected code `e22c8e01d04af726fd0faa69ec171c13317ac64c` at `/tmp/openrx-initial-fill-source03`. The four standalone files are unchanged at e22. The successor fixes matching same-cycle seed-response readiness and adds focused recovery selectors; all original recovery defaults remain. Publication adds evidence/memory documentation without changing executed code. Independent complete-tree comparison found all 4,295 tracked source03 blobs equal to e22 Git objects.

## Standalone differential and synthesis

[Summary](standalone/summary.json), [commands/resources](standalone/commands.json), [input hashes](standalone/inputs.json), [fixture hashes](standalone/fixtures.sha256.json) and [full output hash index](standalone/artifacts.sha256.json) bind 12 native cases, five malformed native cases, 30 RTL modes, four invalid hardware capacities and 18 mapped modes. Zero/ones/incrementing/PRNG seeds exercise all four complete 2 MiB images and native final seeds. Split-call continuation is also checked.

| Full image | Profile | Accepted writes | Write stalls | Request-to-response availability |
| --- | --- | ---: | ---: | ---: |
| Zero | Ideal | 131,072 | 0 | 131,072 |
| Ones | Stalled | 131,072 | 87,380 | 218,452 |
| Incrementing | Stalled | 131,072 | 87,380 | 218,452 |
| PRNG | Ideal | 131,072 | 0 | 131,072 |

Five held-response observation clocks per image are separate. Bounded controls cover held requests/responses, cancellation/reset before, during, while stalled and at return, accepted-write persistence and restart. Eighteen 256-byte mapped records exactly equal matching RTL records. These are bounded mapped checks, not a full mapped 2 MiB proof.

Actual default new-component Yosys/ABC mapping is **36,168 generic cells, 547 flop cells, zero latches**. Separate bounded 256-byte mapping is 36,182/547/0. Mapping includes fill controller plus reused AES round, excludes SRAM/executor and establishes no physical timing/area/power. Full Icarus cases each use about 301–304 host seconds and 28,544 KiB peak RSS; default synthesis uses 84.30 seconds and 754,900 KiB. These are tool runtimes, not device rates.

Standalone immutable execution `20261016T082316Z-86c364941cf5` exits 0 and [integrity verifies](standalone/verify.json). Original manifest/complete outputs/receipt remain at its [recorded absolute path](standalone/execution.json). The first [failed snapshot attempt](failed-vendor-snapshot/execution.json) stopped at vendor preflight: git archive omitted six export-ignored originals. A fresh snapshot restored their exact manifest bytes; [derivation](standalone/snapshot-derivation.json) retains that correction. The failure, first snapshot and original assets remain unchanged.

## Connected native-reference correctness

[Combined check](connected/checks.json) passes prepared two-program × one-iteration workloads: Icarus ideal and pinned Verilator ideal/stalled. All initial 2 MiB SRAM words, post-fill program-0 seed, iteration states, hardware interprogram seed, program memories, final reduction and 32-byte digest agree with the unchanged native reference. Live provider counters record one input-hash callback and zero software-fill provider calls per normal hash. Software fill is an assertion oracle only in hardware mode.

| Verilator profile | Hardware/transport total | Initialization hardware fill |
| --- | ---: | ---: |
| prepared-ideal | 532,408 | 131,076 |
| prepared-stalled | 1,586,553 | 393,220 |

Four-state/two-state ideal digest and complete ledgers agree exactly. Focused connected recovery includes changed-input initialization cancellation/restart with fresh generation and seed, seed-provider error and matching unsolicited host-write error. The same-cycle seed offer is held until it can actually be consumed; stale transfers drain. Recovery selectors record this focused subset; default CLI selections retain all six cancellation phases/eight errors. [37 cheap unit checks](unit-tests.log) cover staging and closing/rejecting ledger invariants.

Connected immutable execution `20261016T084736Z-e61113d5b84c` exits 0 and [integrity verifies](connected/verify.json). Its original complete outputs, native/tool reuse receipts, traces, binaries and generated views remain preserved at the [recorded absolute path](connected/execution.json). No default 8×2,048 rerun occurred.

## Independent bounded review

[Independent review](independent-review.json) accepts the declared standalone and bounded connected scope with zero blockers. It verifies all 4,295 frozen source blobs, 936 receipt artifacts and the separate output indices. Original sources, assets, failures and complete outputs remain preserved. [Task #75](https://github.com/jliu67/OpenRX/issues/75) records the scoped implementation claim and final draft publication, exact public head and applicable hosted checks. Those public gates are separate from the retained execution evidence. New connected proof is v2 only; the default full workload, complete recovery matrix and separate v1 connected replay were not rerun.

## Accounting and claim boundary

The historical c96 measurement remains **40,975,538** hardware/transport clocks with 39,946,977 measured executor clocks; its initial transport stage was 131,074. New measured ideal initialization is **131,076** clocks. The explicit stage substitution is `40,975,538 - 131,074 + 131,076 = 40,975,540`. This is a derived accounting substitution, **not a new full-hash measurement or speedup claim**. It replaces the stage and cannot add the 131,072 writes again. Nested provider/fill clocks close to one disjoint outer stage; stall observations are not additive work.

Actual prelaunch kernel checks retain CPU 600% with all six cores, 4 GiB RAM, 2 GiB swap and Tasks256, no tighter visible ancestors and fresh headroom above the 5 GiB admission requirement. Icarus/AES/Yosys commands are serial single-worker tools; Verilator compilation uses `-j6`. Icarus batch peak RSS is 308,260 KiB, CPU 100%, elapsed 14:22.02; compiled batch peak is 379,420 KiB, CPU 195%, elapsed 4:09.46. Recorded command peaks/utilization describe only those processes; no final whole-host/cgroup peak or device throughput is inferred.

Input hash/program-generation/dataset device costs, full hardware-only hash, alternative full-hash performance, physical memory service and physical ASIC/PPA feasibility remain unresolved. No architecture, engine count, frequency, process or memory technology is selected. The next bounded AES implementation is program generation from actual post-fill/interprogram seeds. Independent final-publication-head review and applicable hosted gates remain required before acceptance; no merge is requested here.
