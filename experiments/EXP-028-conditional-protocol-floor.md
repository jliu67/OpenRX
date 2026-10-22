# EXP-028 — Conditional protocol-floor necessary ceilings

Date: 2026-10-22. Task: [issue #72](https://github.com/jliu67/OpenRX/issues/72).
Status: two-command run completed; separate AI result review passed at 18:17 UTC
within conditional necessary-ceiling scope. Exact publication-head review and
applicable checks remain separate gates.

## Question and retained assumptions

How does the accepted single-credit channel's minimum two-clock capture cadence
constrain PR92's conditional array-service ceilings without choosing a physical
clock or inventing a memory response contract? Retain hypothetical CACTI6.5
45 nm ITRS HP / 1 V / 360 K assumptions, fixed 128 KiB, 32-byte logical rows
and one global credit. Row mapping is not implemented hardware. Cache,
scratchpads and controller/PHY service remain outside this calculation.

Accepted source-bound RTL requires at least two clock periods between captures
and permits matching backend request/reply on the same edge. No universal extra
reply clock or additive `ceil(T/P)+2` assumption is justified. With symbolic
period `P>0` and retained intervals `T1=2.74122 ns`, `T4=0.714793 ns`, calculate

    C_i(P)=min(1e9/T_i,1e9/(2P)) requests/s.

This intersects necessary conditional ceilings; it neither establishes joint
attainability nor bounds actual implementation speedup.

## Actual bounded execution

The [approved plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6347919145) ran once as
`20261022T181455Z-4424e8848ccf`: 12 actual focused tests passed, followed by the
rational report command. Both commands returned zero with no timeout, skip or
retry. Timed wall durations were 0.265524 and 0.064212 seconds. One worker/global
slot used CPU600%, RAM1 GiB, swap2 GiB and Tasks256, with 120 seconds plus five
seconds grace per command. No CACTI build/model, RTL/mapped/gem5 simulation,
native/cache generation or full-hash campaign was rerun.

The 16 bound source files plus manifest, 11 original retained inputs, two tools
and immutable runner remain unchanged. Report SHA256 is
`456f23c1aa1f7ba921a8f68b1afdd3ae552e609b1600cbcc2ad8d37d8eb7fefd`;
receipt SHA256 is `45dfccc7b214655ec3734af62870f148ffc55d9891a09cf33778fdeeec5154e4`.
[Evidence](../docs/validation/conditional-protocol-floor-20261022/README.md)
retains source/input/tool identities, exact rational output, logs and raw flags.

## Useful conditional result

| Symbolic period domain | Ratio of four-bank/one-bank necessary ceilings |
| --- | --- |
| `0<P<=0.3573965 ns` | `28260/7369`, approximately 3.835 |
| `0.3573965<P<1.37061 ns` | `T1/(2P)` |
| `P>=1.37061 ns` | 1 |

The exact breakpoints are `P=T4/2` and `P=T1/2`. The report emits five witnesses
derived algebraically around those boundaries; they are not selected physical
frequencies. The result shows when the protocol floor makes the two optimistic
ceilings equal, without claiming equal actual performance or selecting banks.
PR91's nested owner occupancy and 91 scripted protocol clocks remain
source-specific attributions, not independent memory latency or sustained rate.

## Publication and remaining gates

The intended draft base is PR93 head `3169b2d1` on
`codex/conditional-sram-closeout-20261022`. Its
[AI-review COMMENT](https://github.com/jliu67/OpenRX/pull/93#pullrequestreview-5618779156) is posted, but cancelled
push scalar check `119895244138` still holds merge. This experiment does not
waive that gate or claim either draft is merged.

Raw runner `unverified` and report/driver pending-review fields are preserved.
Separate AI result review accepts only the conditional necessary-ceiling calculation;
[review record](../docs/validation/conditional-protocol-floor-20261022/independent-result-review.json).
Characterized SRAM/PVT, actual clock/interface compatibility, sustainable memory
service/tails, controller/PHY energy, cache/scratchpad organization, physical
frequency/area, whole-machine power, achieved hashes/s and architecture selection
remain unresolved. Broader issue #72 stays open; no further validation or public
execution request follows automatically.
