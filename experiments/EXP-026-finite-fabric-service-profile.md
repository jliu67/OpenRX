# EXP-026: finite dataset-fabric analytical service profile

Status: independently accepted **analytical component report only**, 2026-10-22.
Scoped draft publication, independent final-head review and applicable exact-head
checks remain separate gates. Broader [issue #72](https://github.com/jliu67/OpenRX/issues/72)
is open.

## Question and evidence boundary

Can a byte/source-bound analytical adapter summarize the accepted finite shared
fabric's per-link descriptor demand, finite ownership and source-specific work
and clock ledgers without changing the accepted scheduler or full-hash domains?
This is a reporting experiment over retained component evidence. It introduces
no new native/cache generation, RTL simulation, synthesis, full hash or physical
measurement.

The accepted component is [PR89](https://github.com/jliu67/OpenRX/pull/89), public head
`f495a34fc8a67f69b7f3e407cc4b509b96b84d64`, tree
`d4455f073c858c7df5bd4d2ea7373fa52650df56`, normal merge
`b6e71b467bc3c51e1c6734853a08b11412c8653a`, with
[independent final-head acceptance](https://github.com/jliu67/OpenRX/pull/89#pullrequestreview-5607170870).
[EXP-025](EXP-025-shared-dataset-fabric.md) retains prefix, matrix, failed mapping
and accepted recovery separately. The registry binds 22 existing public JSONs,
145,352 actual bytes, recovery source/tool identities and explicit logical port
widths. It preserves the recovery source-bindings parent rather than rewriting
that historical record to a later accepted head.

The new repository additions are `tools/architecture/finite_fabric.py`, its
`fixtures/accepted_finite_fabric_v1.json` registry and 12 test methods in
`tests/test_architecture_finite_fabric.py`. All retained analytical/support/gold
and accepted input bytes remain unchanged. The [PR87](https://github.com/jliu67/OpenRX/pull/87)
[hardware-dataset service profile](EXP-024-hardware-dataset-service-profile.md)
and PR74 scheduling/full-hash evidence keep their original domains and numbers.

## Logical transport and clocks

Descriptors include each source payload, its 64-bit client tag and one backend
owner bit. Ready/valid/cancel/diagnostic wires, byte rounding and physical encoding
are excluded.

| Interface | Request payload bits | Response payload bits | Request descriptor bits | Response descriptor bits |
| --- | ---: | ---: | ---: | ---: |
| Prepared instruction fetch | 28 | 190 | 93 | 255 |
| Prepared cache line | 41 | 554 | 106 | 619 |

| Retained profile | Batch modeled clocks | Success / error / cancelled | Namespaces used by client |
| --- | ---: | --- | --- |
| concurrent-ideal | 61,595 | 2 / 0 / 0 | [1, 1] |
| serial-ideal | 113,953 | 2 / 0 / 0 | [1, 1] |
| serial-stalled | 149,685 | 2 / 0 / 0 | [1, 1] |
| concurrent-stalled | 83,537 | 2 / 0 / 0 | [1, 1] |
| cancel0 | 149,693 | 2 / 0 / 1 | [2, 1] |
| cancel1 | 149,685 | 2 / 0 / 1 | [1, 2] |
| malformed-fetch0 | 74,849 | 1 / 1 / 0 | [1, 1] |
| exhaustion | 184,787 | 6 / 0 / 0 | [3, 3] |

The exact controlled two-item serial/concurrent fractions are 113953/61595 ideal
and 149685/83537 stalled. The eight-profile report includes the prefix's
concurrent-ideal pair plus the seven-profile matrix; its 22 rows repeat native
items 0 and 10,000,000. They do not represent 22 distinct native items or a
representative full-hash workload. The matrix's historical 20-row total is unchanged.
Batch elapsed excludes the first acceptance edge. Client availability, held clocks,
child phases, executor clocks and channel occupancy are nested observations,
not disjoint time to add to the batch.

Each interface has one finite owner credit. For concurrent-ideal, 7,126 fetch
requests/replies carry 662,718 request and 1,817,130 response descriptor bits;
16 cache requests/replies carry 1,696 and 9,904 bits on that separate link.
Fetch owner-credit occupancy is 14,252/61,595 batch clocks. These are logical
per-link fractions; occupancy includes protocol/held time and does not measure
provider-only latency or sustainable physical supply.

Checks preserve successful and returned-error availability closure, source-specific
phase vectors, partial cancelled work and observed-order namespace consumption.
Cancellation does not refund a namespace. Exhaustion denies a fourth admission
without wrapping. Directed protocol coverage retains 2,045 checks and 91 ledger
observations. Packet-routing attribution comes from pinned RTL/testbench assertions
and accepted reviews; aggregate counters alone do not prove it.

Standalone channel mapping reports 6,581 generic cells/801 DFF/zero latches;
the containing fabric reports 14,498/1,615/zero. The scopes are not added, and
these diagnostics/payload counts do not establish physical area.

## Actual authorized validation

The [claim](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6331297362)
and separately approved [three-command plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6331310442)
bind execution `20261022T023803Z-dd124df0248e`. All three commands returned zero
without timeout. Actual architecture discovery passed 98 methods: 86 retained
plus 12 new, with no failures, errors or skips. The finite-profile CLI produced
the bound report; the unchanged PR87 CLI reproduced both accepted JSON gold
files byte-for-byte. The old 58-second scheduler reproduction was not repeated.

Combined driver-measured command wall time was 2.253554025 seconds. GNU time
maximum RSS was 32,168 / 16,888 / 16,172 KiB respectively for units, finite-profile
CLI and PR87 parity CLI. These are per-command process observations, not cgroup
memory peaks, physical service latency or RandomX throughput. Actual one-worker,
one-slot bounds were six CPUs (CPU600%), RAM 1 GiB, swap 2 GiB, Tasks256 and
120 seconds plus five seconds supervisory grace per command.

[Evidence](../docs/validation/finite-fabric-service-profile-20261022/README.md)
binds unchanged sources/tools, all 26 receipt artifacts, report arithmetic and
separate independent review `PASS_ANALYTICAL_COMPONENT_REPORT_ONLY`, with no
findings. The report's accepted component classification concerns accepted PR89
inputs; current-run review is a separate decision. Raw runner `unverified` and
driver `unverified_pending_independent_review` fields remain unchanged, as do
original failed mapping/full-hash records and all earlier accepted evidence.

## Limits and next gate

No two-VM or independent 2 MiB scratchpad validation follows from two dataset
clients. Logical descriptor bits are not aggregate off-chip traffic. Physical
service supply/latency, frequency, area, whole-machine wall power, achieved hashes/s,
alternative full-hash cycles, selected engine count and ASIC feasibility remain
unknown or unresolved. Do not extrapolate either bounded batch ratio to a full
hash. The 1 MH/s below 2,500 W objective and broader issue #72 gates remain open.
A scoped draft PR still needs independent final-head review and applicable
exact-head checks before normal merge; this record makes no new-head check or
merge claim.
