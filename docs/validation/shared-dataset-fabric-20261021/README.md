# Finite shared dataset-fabric RTL/native evidence — 2026-10-21

This is a partial [task #88](https://github.com/jliu67/OpenRX/issues/88) result:
a two-client finite shared instruction/cache fabric around unchanged accepted
item-session cores. Prefix protocol/native correctness is independently accepted.
Seven further native profiles completed and pass separate independent bounded review.
Generic synthesis and mapped protocol/native parity are **unrun**. Final
publication-head review and applicable hosted checks remain separate gates;
this evidence does not complete issue #88.

Read [EXP-025](../../../experiments/EXP-025-shared-dataset-fabric.md) and the
[transport contract](../../../rtl/dataset_shared/DATASET_SHARED.md). Completed
migration and prior accepted default functional full-hash evidence remain intact.
No full hash was repeated for this experiment.

## Bindings and retained inputs

Base main is `c5d53686444d11b10edff200e63d7b725ae782b4`, tree
`cec1e8646f483e73fc6719fbd4c21118480eb3cd`, through normally merged
[PR87](https://github.com/jliu67/OpenRX/pull/87). Its independent exact-head review,
four head checks and two post-merge checks are complete. The frozen executed
source manifest SHA256 is
`40ac32a3a0e949305c10432f4d265903d011105b1d104ad9ac2445bcd6dbd3fe`.
Seven accepted RTL/license files remain unchanged; eight new files implement
transport, benches, driver and focused support tests.

[Source bindings](source-bindings.json) and
[verification summary](verification-summary.json) retain source, tool, selected
fixture, receipt and reuse identities. The selected95 fixture files derive from
accepted producer receipt SHA256
`f3ced2d4f48eaa7c49359cea893c65666377c7f0a84386c035736357bfb59ad8`.
Cases000/001 are actual itemnumbers0 and10,000,000, sharing retained cache0 and
prepared programs. The cache data file SHA256 is
`c52c404a5bee51f732d0d697af753fa206b407d5e8d7e77cd7d9a866f11d3691`.

Providers return immutable prepared instruction/reciprocal associations and actual
DUT-indexed64-byte cache data. Native instruction states, eight-stage states and
final items are assertion-only oracles. Retained preparation and modeled host
memory services remain explicit; this does not establish autonomous initialization
or a physical memory controller.

| Admitted phase | Execution / receipt SHA256 | Actual scope |
| --- | --- | --- |
| Prefix | `20261021T032914Z-a5cc7c4a15d0` / `3325f8490adb1d5fb7361a640983ff2b9006822943d757b29d2f1b1489816007` | 14 support units, two Icarus compiles, directed protocol and one concurrent-ideal native pair |
| Matrix | `20261021T141051Z-7fb322066922` / `728ea10ff95770ebe5fc04df7f64c1458fdb9aaca8f19d2fd2ffe2f60021e8af` | Seven remaining profiles using exact compiled prefix VVP binaries; no compilation/unit/native/cache-generation rerun |

The [prefix request](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6307296763)
and [matrix request](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6318167243)
were separately admitted. Original rejection/unrun handoffs and subsequent
approved execution records remain retained. All52 prefix and65 matrix receipt
artifacts pass integrity verification. Raw process receipts retain
scientific acceptance `unverified`; the public summaries retain their original
pending-review fields. Process completion and integrity do not establish acceptance.
Separate independent prefix review passes. The
[independent bounded matrix review](independent-result-review.json) passes with no
blockers; its source/input/native/ledger acceptance does not accept mapping or
physical performance.

## Protocol and native outcomes

The prefix passes14 support units and [2,045 protocol checks](prefix01/protocol.json)
across91 ledger observations. There are23 accepted/backend requests,20 client
deliveries,3 cancelled drains and4 orphan replies across27 backend responses.
Eight round-robin/identical-tag pairs, early/held replies, cancellation ownership,
matching malformed payload forwarding, genuine-quiescent reset and counter closure
are checked. High-water is one owned credit.

The [prefix summary](prefix01/public-summary.json) and
[matrix summary](matrix01/public-summary.json) include complete native/clock/channel
records. The matrix summary carries the exact bound concurrent-ideal prefix
result; it was **reused**, not rerun. The matrix executes exactly seven new
profile commands and only Icarus/VVP version probes alongside them. Its20 native
item rows contain17 successes,1 expected error and2 cancelled items, totaling
60,573 commits,21,320 multiplies and136 stages. These repeat the two retained
native fixture items; they are not17 distinct native cases.

| Profile / source | Success / error / abort | Native commits / multiplies / stages | Batch modeled clocks |
| --- | --- | --- | ---: |
| [concurrent-ideal / prefix](prefix01/native-concurrent-ideal.json) | 2 / 0 / 0 | 7,126 / 2,508 / 16 | 61,595 |
| [serial-ideal / matrix](matrix01/native-serial-ideal.json) | 2 / 0 / 0 | 7,126 / 2,508 / 16 | 113,953 |
| [serial-stalled / matrix](matrix01/native-serial-stalled.json) | 2 / 0 / 0 | 7,126 / 2,508 / 16 | 149,685 |
| [concurrent-stalled / matrix](matrix01/native-concurrent-stalled.json) | 2 / 0 / 0 | 7,126 / 2,508 / 16 | 83,537 |
| [cancel0 / matrix](matrix01/native-cancel0.json) | 2 / 0 / 1 | 7,127 / 2,509 / 16 | 149,693 |
| [cancel1 / matrix](matrix01/native-cancel1.json) | 2 / 0 / 1 | 7,127 / 2,509 / 16 | 149,685 |
| [malformed-fetch0 / matrix](matrix01/native-malformed-fetch0.json) | 1 / 1 / 0 | 3,563 / 1,254 / 8 | 74,849 |
| [exhaustion / matrix](matrix01/native-exhaustion.json) | 6 / 0 / 0 | 21,378 / 7,524 / 48 | 184,787 |

Cancellation retains the cancelled backend identity, drains ownership and burns
[2,1]/[1,2] client namespaces, with one partial aborted instruction followed by
the recorded successful native items. Malformed matching fetch metadata reaches
the owning unchanged core and produces its error while the other client succeeds.
Reduced2-bit namespace exhaustion completes three sessions per client and denies
a fourth admission without identity recycling. Cross-client identical lower64-bit
tags are qualified by the explicit client bit; arbitrary same-client identity
reuse and arbitrary old hard-reset packets are outside the contract.

## Clock and resource boundaries

Batch elapsed clocks enclose overlapping client work. Availability, executor/core,
held-result, channel occupancy and arbitration waits are distinct nested ledgers;
do not add them to batch elapsed time. The prefix batch61,595 includes client
availability61,587/61,590, separate core61,586/61,589 and held4each.
Phase vectors sample pre-edge owned phases until post-edge result availability.
Their sums close to each client availability, including the adapter's launch;
these source-specific bins are not the old full-hash observer vector.
The complete per-item and channel records remain in the linked JSONs.

Both phases used existing immutable runner657, actual kernel CPU600%, RAM1GiB,
swap2GiB, Tasks256 and one slot. Prefix worker count is1; matrix maximum is6.
Each payload command has GNU timeout120s plus5s supervisory wait grace.
No command timed out.

| Actual observation | Prefix | Matrix |
| --- | ---: | ---: |
| Cumulative cgroup memory peak, bytes | 53,821,440 | 71,790,592 |
| Cumulative cgroup CPU seconds | 8.609579 | 78.970740 |
| Swap peak / CPU throttling | 0 / none | 0 / none |
| Native-pair command wall seconds | 5.896576 | Seven profile commands: 6.455875–17.672226 |
| Worker-command wall seconds | 8.553239 | 26.444271 |

Matrix worker-command time is measured from CHILD_STARTED to process-result finish.
The26.486097-second CHILD_STARTED→PROCESS_EXITED event interval additionally
contains0.041826 seconds of runner observation overhead. Neither interval is
RandomX throughput or physical device latency. The earlier six-times-prefix memory
planning estimate was not a measured matrix peak; the actual matrix peak above
supersedes that estimate for this bounded run. System dynamic libraries are not
claimed fully hermetic.

## Remaining acceptance

No synthesis, mapped parity, full-hash rerun, native/cache generation, architecture
selection or physical acceptance occurred in the matrix. A separately scoped
admission must validate generic new-fabric mapping and mapped protocol/native
parity before the task can complete. Final publication-head review and applicable
hosted checks remain separate.

Two clients and one credit are experimental controls. Controlled modeled batch
overlap does not establish physical services, frequency, PPA, power, production
engine count, complete-hash alternative performance, achieved hashes/s or the
whole-machine1MH/s below2,500W target. Broader task #72, autonomous setup and
scientific/physical gates remain open. Preserve all historical failed and accepted
full-hash/preparation records, original sources, checkpoints and raw scientific
flags unchanged.
