# EXP-025: finite shared dataset-service transport

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

