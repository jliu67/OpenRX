# EXP-025: finite shared dataset-service transport

## Fixed-slice recovery accepted for bounded components — 2026-10-21 22:37 UTC

The [separately authorized recovery](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6327859314)
completed 25 commands across three admitted stages, each independently accepted.
Only `randomx_dataset_shared_channel.v` changed: guarded owner branches/fixed
response slices replace variable-indexed valid/tag/payload writes. Channel SHA256
is `0d02318cad0991321fed4a365664d231f90f1968ef2e1fdc733c3b5291d06493`;
the complete 15-file source manifest is
`1176a4a2112e364fb6aec674146273d27729388ef7854a8de56388f03524e5ea`.
Accepted arithmetic and acceptance criteria are unchanged.

The fresh seven-command prefix passed 14 support tests, 2,045 protocol checks and
a two-item native pair. Its two JSONs match historical accepted results exactly.
The nine-command matrix reused the fresh same-source binaries; all seven profile
JSONs match their historical records. Its 20 rows repeat the two retained items:
17 successes, one expected error and two cancellations, not 17 distinct items.

The final nine commands completed explicit ABC mapping and byte-exact mapped
protocol/native parity with the fresh prefix. Standalone channel mapping took
8.961900 seconds, yielding 6,581 generic cells/801 DFF/zero latches. Flattened fabric
mapping took 22.189259 seconds, yielding 14,498 cells/1,615 DFF/zero latches. Counts
include diagnostics/payload logic, are not physical area and must not be added
across these nested scopes. Mapped native host runtime was 51.139495 seconds;
this is not a chip frequency or complete-hash performance measurement.

[Source, receipts and reviews](../docs/validation/shared-dataset-fabric-20261021/README.md)
preserve the prior failed mapping and all original raw flags. No full hash or
native/cache generation was repeated. The bounded component stages are accepted;
PR89 stays draft for final publication-head review/checks. Physical services,
PPA/frequency/power, architecture selection and complete-hash alternatives remain
open. Earlier failed/partial entries below are preserved as dated history.


## Later generic mapping attempt — 2026-10-21 21:51 UTC

Current stage: **FAIL/incomplete** after the separately approved
[bounded plan](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6327206298).
Execution `20261021T214326Z-597d5d52ca81` used unchanged PR89 head
`d3f11cc39a55154ed04ed1aa2a57768531c76ce0`; accepted arithmetic stayed RTL.
Three tool probes and standalone channel mapping completed. Flattened fabric
mapping returned 137 at 120.506375 seconds, consistent with its enforced
120-second timeout; no fabric netlist exists and OOM causation is not established.
Both mapped compiles and both parity runs did not run.

The default TAG64/REQ28/RSP190 channel completed explicit ABC mapping in
59.309969 seconds with 6,887 generic cells, including 801 DFF cells and no latches.
These diagnostic/payload-inclusive counts are not physical area and must not be
added to a containing whole-fabric count. Cumulative admitted-cgroup peaks were
1,073,741,824 bytes RAM and 916,295,680 bytes swap; they are not per-command RSS
or chip measurements.

[Public evidence](../docs/validation/shared-dataset-fabric-20261021/README.md)
and separate independent review preserve this failure, channel assets and all
earlier accepted prefix/matrix results. No full hash, units/matrix or native/cache
generation was rerun. Fabric mapping and byte-exact mapped protocol/native parity
remain required; PR89 stays draft. Final publication-head review/checks and
physical/service/performance gates remain separate. The earlier partial snapshot
below is preserved as dated history without changing its original bytes.


Status: partial — prefix and seven-profile RTL/native matrix independently accepted;
generic synthesis and mapped parity unrun.

## Hypothesis

Two accepted item-session clients can overlap their arithmetic while sharing
separate finite instruction/cache channels, without misrouting identical client
tags, losing cancelled ownership or recycling exhausted identities. Compare
controlled serial/concurrent batches under the same finite service parameters.
This experiment does not select a production engine count or predict complete-hash
throughput or physical service capacity.

## Controls and configuration

- Task [#88](https://github.com/jliu67/OpenRX/issues/88); base main
  `c5d53686444d11b10edff200e63d7b725ae782b4`, tree
  `cec1e8646f483e73fc6719fbd4c21118480eb3cd`.
- Frozen 15-file source manifest SHA256
  `40ac32a3a0e949305c10432f4d265903d011105b1d104ad9ac2445bcd6dbd3fe`.
  Seven accepted RTL/license files stay unchanged; two independent item-session
  clients share one credit per fetch/cache channel.
- Native fixture cases000/001 mean itemnumbers0 and10,000,000 on retained cache0,
  not two newly generated caches or literal itemnumbers0/1. Cache/program/reciprocal
  preparation is retained. Providers return actual DUT-indexed cache bytes and
  immutable prepared instruction/reciprocal associations; expected states are
  assertion-only oracles.
- Full65-bit backend identity is `{client_id, full64-bit accepted client tag}`.
  Session namespace bits are reduced to2 to reach three-session exhaustion.
  Accepted arithmetic and quiescent-reset/no-refund contracts remain unchanged.
- [Prefix request](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6307296763)
  and [matrix request](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6318167243)
  were separately admitted on the existing authorized server/immutable runner657.
  CPU600%, RAM1GiB, swap2GiB, Tasks256 and one slot; matrix uses at most six jobs.
  Every payload command has a120-second GNU timeout and5-second supervisory grace.

## Acceptance and correctness

The prefix checks support accounting/provenance, protocol ownership/fairness,
same-tag cross-client identity, immutable descriptors, early/held/orphan replies,
cancellation and genuine-quiescent reset. Native comparisons check every observed
instruction state, cache-XOR stage, final item and actual cache index.
The matrix adds serial/concurrent finite-service comparisons, both cancellation
owners, transparent malformed-fetch error and namespace exhaustion.
Record batch elapsed, per-client availability/held phases, channel occupancy,
request/response/cancel/orphan counts and arbitration waits separately.

Process exit/receipt integrity do not replace separate independent result review.
Generic new-fabric synthesis, mapped protocol/native parity, final publication-head
review and applicable hosted checks remain separate task-completion gates.
No physical/PPA/frequency/power or complete-hash alternative acceptance criterion
is weakened.

## Results

[Compact evidence](../docs/validation/shared-dataset-fabric-20261021/README.md)
binds exact artifacts, resources and complete ledgers.

The accepted prefix passes14 support units,2,045 protocol checks/91 ledger
observations and two native items with7,126 commits,2,508 multiplies and16 stages.
The native pair used5.896576 seconds and61,595 modeled batch clocks.

The separately completed matrix ran seven profiles through exact prefix binary
reuse, with no unit/compilation/native/cache-generation rerun. All seven commands
exited zero without timeout. Separate independent bounded matrix-result review passes with no blockers.
Ideal serial/concurrent batches use113,953/61,595 modeled clocks; stalled batches
use149,685/83,537. Cancel0/1 each retain cancelled identity with two successes and
one abort, burning[2,1]/[1,2] namespaces. Malformed-fetch0 produces one success and
one owning-core error. Exhaustion completes six successful items at[3,3] and denies
the fourth admission.

Matrix worker-command wall time is26.444271 seconds; actual cumulative cgroup peak is
71,790,592 bytes, zero swap and78.970740 CPU seconds without throttling.
Generic synthesis/mapped parity are **unrun**, with no cell-count result claimed.
Original failed full-hash/preparation records remain preserved separately from
the prior accepted full functional hash; no full hash was repeated here.

## Interpretation and next action

Controlled concurrent batches overlap accepted item arithmetic while finite
channels preserve the recorded identity/error/cancellation behavior. Their modeled
batch reduction is source/profile-specific and cannot be extrapolated to full-hash
throughput, selected production architecture or a physical memory controller.
Nested client/channel clocks must not be added to elapsed batch time.
Follow separate admission for generic new-fabric mapping/parity, then independent
result/head review and applicable checks; keep the draft/task partial until those
gates pass. Physical service characterization, calibrated timing/power, autonomous
setup, architecture selection and the whole-machine target remain open.

