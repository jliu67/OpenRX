# EXP-029 — Immutable prepared-fetch SRAM-port interface

Date: 2026-10-22. Task: [issue #72](https://github.com/jliu67/OpenRX/issues/72).
Base: `90b87f55220151a2bb43ed097c8d55e62a534e0b`.
Scope: one standalone logical prepared-fetch service and its explicit controller
cadence. Separate AI [actual-result review](../docs/validation/prepared-fetch-sram-port-20261022/independent-result-review.json)
passed for the functional behavioral port only at 21:37:39 UTC; draft publication,
exact public-head review and applicable checks remain pending. This is not human
or account-holder approval.

## Falsifiable question and admitted image

Can an explicitly synchronous immutable row port deliver the one admitted cache0
program image through the unchanged two-client shared channel with exact row
data, owner/full tag/address echo, held replies and cancellation drain? Does this
specific controller achieve its proposed three-clock continuous capture spacing,
with the cumulative and post-reset transport/occupied-clock ledgers closing?

The image comes from retained execution `20261018T175827Z-447be94ead08`.
Cases000/001 share the same 32 arrays. Counts are
`[447,438,449,447,444,449,452,437]`: 3,563 active rows, 533 zero padding slots
and 239 prepared reciprocal rows/global indices0–238. This establishes no general
capacity for all accepted program images or larger global reciprocal namespaces.

Logical storage is 4,096 ×256-bit rows/128KiB: instruction64, reciprocal64,
global-index32, reciprocal-valid1 and 95 zero reserved bits. Counts, response
echo/error, full owner/tag and control lie outside the payload capacity.
Reciprocal values are denormalized offline; there is no separate live reciprocal
lookup or runtime row-write/reload interface. Requests past a program's admitted
count return held tagged errors without reading padding as executable content.

The [component](../rtl/prepared_fetch_sram/README.md) reuses the accepted shared
channel unchanged. Cancellation keeps the captured identity and drains one
response; nonowner cancellation must not affect it. Quiescent reset clears
transport diagnostics while retaining the image and external tag history.
Finite test tags do not wrap or reuse live identities.

## Approved method and source binding

[Public execution plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6351774332)
and source manifest SHA256
`6a4f3bd1f58fd96573519e931e472abacdef9fcbec6e85bf82058c5c50eb694f`
bind 84 listed source files plus the manifest. The 71 copied inputs retain their
original bytes; the oracle reconstructs gold independently from original fields,
without importing exporter code. The command wrapper imports both independent
modules in one process; process isolation is not claimed.

Execution `20261022T213322Z-acbfc58fe1e4` ran exactly four sequential commands:

1. 36 Python tests: 24 exporter and 12 independent-oracle mutation methods.
2. Offline image export and independent comparison of all 4,096 rows/counts.
3. One Icarus compile of the standalone adapter/model/bench.
4. One VVP run with 12 named scenarios and a 100,000-modeled-clock watchdog.

One worker/global slot used CPU600%, RAM1GiB, swap2GiB and Tasks256. Each command
had 120 seconds plus five seconds supervisory grace; stop-first-failure was
mandatory. No fallback, payload retry, cap enlargement or search expansion was
used. Command walls were 1.672562, 0.164733, 0.032045 and 2.427293 seconds.
These are validation costs, not workload throughput.

## Actual bounded result

All four commands returned zero; the 36 tests had no skips, and there were no
timeouts or payload retries. The simulation completed 170,056 checks in 21,648
modeled clocks:

| Observation | Count |
| --- | ---: |
| Scenarios | 12 |
| Accepted/backend requests and backend responses | 7,199 each |
| Active row reads | 7,167 |
| Both-owner exhaustive active-row queries | 7,126 |
| Address errors without row reads | 32 |
| Cancellation drains | 3 |
| Client accepted counts | 3,599 /3,600 |
| Client delivered counts | 3,598 /3,598 |
| Total channel occupied clocks | 14,445 |
| Occupied clocks before last reset | 14,443 |
| Occupied clocks after last reset | 2 |

The 32-capture continuous case measured 31 intervals/93 modeled clocks, exactly
three-clock spacing: capture E0, synchronous row read E1, consume E2 and next
capture E3. These are nested controller observations, not disjoint values to add
to total elapsed clocks. The bench also checks sealed-image issue blocking,
held replies and captured-descriptor replacement, queued/issued/held cancellation,
nonowner cancellation, opaque epoch echo, bounds errors, quiescent reset and
terminal client/channel/provider drain.

See the [bound evidence](../docs/validation/prepared-fetch-sram-port-20261022/README.md)
for original/sanitized output identities, commands, resource observations and
source mapping. Raw scientific flags remain unchanged. Separate AI actual-result
review accepts only the bounded functional behavioral port result; it does not
rewrite those historical flags. Publication-head review and CI remain separate.

## Scientific limits and preservation

Offline `$readmemh` preload plus the declared behavioral synchronous memory port
remain explicit modeled host services. They are not autonomous hardware setup
or a characterized physical SRAM macro. No live software input/fill/program/
dataset-generation callback, cache.bin load, native/cache generation, whole-core
build, CACTI/gem5, synthesis/mapped campaign or full-hash rerun occurred.

This controller's three-clock spacing does not change EXP-028's necessary
two-clock floor, characterize physical latency/ports, establish an achievable
frequency, prove bank speedup or validate physical area/energy, controller/PHY
service/tails, wall power, achieved hashes/s, architecture selection or the
whole-machine target. Broader issue #72 remains open. Accepted channel/arithmetic,
original sources/results/checkpoints, earlier failures and every raw scientific
flag are preserved. Preparation/UNRUN statements inside the exact source
snapshot describe their dated pre-execution state and are not rewritten.


