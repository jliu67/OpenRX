# Conditional protocol floor — 2026-10-22

The [approved issue #72 plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6347919145)
ran once as `20261022T181455Z-4424e8848ccf`. Both commands returned zero:
**12 focused unit tests and one analytical report**, without skips, timeout,
repair or retry. [Separate AI result review](independent-result-review.json)
accepts **CONDITIONAL NECESSARY CEILINGS ONLY**, with no blocking findings.
Publication-head review and applicable hosted checks are separate delivery gates.

## Useful result

The accepted single-credit channel permits a matching backend request and reply
on the same edge, but needs at least **two clock periods between captures**.
Intersect that necessary cadence bound with the retained PR92 array intervals:

`C_i(P) = min(1e9 / T_i, 1e9 / (2P))` requests/s, with `P > 0` in ns.

PR92 supplies `T1 = 2.74122 ns` and `T4 = 0.714793 ns`, each the maximum of
modeled access and cycle time. These retain the hypothetical CACTI6.5 ITRS
45 nm HP / 1 V / 360 K assumptions. Clock period remains symbolic; this work
does not select or establish a physical operating frequency.

| Period domain | Ratio of four-bank/one-bank necessary ceilings |
| --- | --- |
| `0 < P <= 0.3573965 ns` | `28260/7369`, approximately 3.834984 |
| `0.3573965 < P < 1.37061 ns` | `T1/(2P)` |
| `P >= 1.37061 ns` | 1 |

Thus the clock-cadence bound can erase the difference between these two
optimistic ceilings. This does **not** prove actual speedup, equal implementation
performance or simultaneous attainability. A ratio of separate necessary ceilings
does not bound the actual performance ratio. There is no bank-count multiplier,
universal extra reply clock, additive array/protocol latency or `ceil(T/P)+2`
assumption. The five report witnesses are algebraically derived around the exact
breakpoints, not a selected grid of physical clocks.

The proposed fixed 128 KiB / 4,096 logical 32-byte-row SRAM mapping remains
unimplemented; the one global credit is explicit. PR91's 14,252 owned clocks /
7,126 requests is a nested batch attribution, not a provider-latency contract or
sustainable-throughput measurement. Its scripted 91-clock protocol result and
same-edge cases are retained source evidence, not new simulation results.

## Evidence and source identity

- [Generated report](protocol-bound.json), SHA256
  `456f23c1aa1f7ba921a8f68b1afdd3ae552e609b1600cbcc2ad8d37d8eb7fefd`;
  [provenance](provenance.json) and unchanged [generated index](artifacts.sha256.json).
- [Public execution summary](public-summary.json),
  [normalized validation summary](validation-summary-public.json), and complete
  [unit](logs/protocol-bound-units/) / [report](logs/protocol-bound-report/) logs.
  `{SOURCE}` and `{EXECUTION}` replace local prefixes in public status/time
  records; wrappers retain raw status hashes. Complete originals stay local.
- [Exact executed source](source/) contains the adapter, 12 test methods, driver,
  tool bindings, registry and eleven retained input files. The separately pinned
  [manifest](source/SOURCE-MANIFEST01.json), SHA256
  `ea52fe4107df66182ba7e828093a1c4207fbe4dad30c32774e0cb8a982028493`,
  binds 16 files / 213,587 B, plus itself for 17 physical files.
- [Approved plan snapshot](approved-plan-snapshot.md), SHA256
  `08c03e1337bf0877f92472b79e2fab93e38233614431ec3a5cfa79cff74ed93b`.
  Its preparation/UNRUN wording and the source manifest's pre-execution fields
  are preserved historical snapshots; current actual outcomes are recorded above.

The eleven inputs are byte-exact retained PR89 channel/fabric/bench/protocol
records, PR91 accounting and PR92 contract/report/provenance. Original source
notices remain intact. No original accepted code, input, report or scientific
flag was edited. The twelve unit tests exercise parser, substitution, exact
rational arithmetic, boundary and scope rejection; synthetic fixtures are not
physical measurements. The separate report command used the actual retained inputs.

## Actual execution and limits

| Command | Return code | Wall seconds | Maximum command RSS, KiB |
| --- | ---: | ---: | ---: |
| 12 focused unit tests | 0 | 0.265524 | 18,944 |
| Analytical report | 0 | 0.064212 | See preserved GNU time record |

Summed timed commands took 0.329736 seconds, excluding admission/finalization.
One worker/global slot used CPU600%, RAM1 GiB, swap2 GiB and Tasks256; each
command retained its approved 120-second timeout plus five-second shutdown grace.
Actual kernel limits, six-CPU affinity, visible ancestor ceilings and locked
headroom were verified safe and are summarized in the public execution record.
The runner's `kind=simulation` is its admission category for this analytical
bundle; no new CACTI, RTL, gem5, synthesis, build, native/cache or full-hash
workload ran.

The immutable runner verifies terminal integrity over all 22 receipt artifacts.
Receipt SHA256 is
`45dfccc7b214655ec3734af62870f148ffc55d9891a09cf33778fdeeec5154e4`.
Root separately posthashed all 16 frozen files, the manifest, eleven original
inputs, two tools and runner. The reviewer independently checked artifacts,
limits and rational results without rerunning a workload. Raw runner
`scientific_acceptance=unverified` and generated pending-review fields stay
unchanged beside separate narrow acceptance. Tool pinning does not claim a
complete hermetic shared-library/runtime closure.

## Open gates and delivery dependency

Characterized process/PVT/SRAM timing, clock/interface compatibility, sustainable
memory/controller/PHY service and tails, cache/scratchpad organization, complete
power, physical area/frequency, achieved hashes/s and architecture/target
acceptance remain unresolved. Physical unknowns are null. Issue #72 remains open;
this result authorizes no follow-up run or hardware purchase.

The draft publication stacks on documentation PR93's unchanged reviewed head
`3169b2d11efddab88f35935711adb4563b5ea560` to preserve document history and avoid
conflicting current-status edits. PR93 remains unmerged because its applicable
push RISC-V check was cancelled during installation; that check was not rerun or
waived here. The source-bound inputs themselves are accepted PR89/91/92 evidence
and do not depend on that documentation merge. Later retargeting or merge must
preserve independent review and applicable exact-head check gates.
