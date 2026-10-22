# PR94 protocol-floor delivery closeout — 2026-10-22 19:00 UTC

This delivery addendum preserves the [original EXP-028 validation bundle](../conditional-protocol-floor-20261022/README.md)
byte-exact. It changes no scientific evidence, raw flags, acceptance criteria or historical record.

## Reviewed publication and actual merge

[PR94](https://github.com/jliu67/OpenRX/pull/94) merged normally at 18:58:26 UTC as
[`273cc464836c68fda8c1dd2352fe4029a4255d7f`](https://github.com/jliu67/OpenRX/commit/273cc464836c68fda8c1dd2352fe4029a4255d7f).
Its actual tree `2cad6a45f3a67233c36c56e8d95a241faf4d2a4e` equals the
reviewed original head `e8f8ffb3c03ed6c2638b10e624c8beea47683b20` tree.
Separate AI independent review and all four applicable exact-head checks passed
before merge. Review was performed by a separate AI agent; source and safeguards were preserved.
Exact-merge attempt1 checks passed, verified at 19:00:32 UTC:
[Foundation](https://github.com/jliu67/OpenRX/actions/runs/39836025905/job/120024473305)
(11 successful steps; full-dataset reference and same-process steady controls
intentionally skipped/deferred) and
[RISC-V](https://github.com/jliu67/OpenRX/actions/runs/39836025949/job/120024473503)
(13 successful steps). Skipped controls never count as passes.

The actual merge parents are main `11e8855ec55dd69546f2c8e0321b2bc4d46d0bd3`
and original head `e8f8ffb3c03ed6c2638b10e624c8beea47683b20`.
The publication's original parent was PR93 head
`3169b2d11efddab88f35935711adb4563b5ea560`, tree
`0b446f08e73cb2dac65c859d2440857c916bc11d`. Separate AI review checked the
unchanged 41-file publication: 35 additions, six additive modifications and zero
deleted lines. Review is neither human approval nor physical acceptance.

Four applicable publication-head jobs passed before merge:

- [Push foundation](https://github.com/jliu67/OpenRX/actions/runs/39831800792/job/120009572264).
- [Push scalar](https://github.com/jliu67/OpenRX/actions/runs/39831800661/job/120009571324).
- [PR foundation](https://github.com/jliu67/OpenRX/actions/runs/39832819853/job/120013165117).
- [PR scalar](https://github.com/jliu67/OpenRX/actions/runs/39832819991/job/120013165428).

Both postmerge jobs ran on attempt1 at the actual merge
`273cc464836c68fda8c1dd2352fe4029a4255d7f`; the successful outcomes above
were verified at 19:00:32 UTC. Foundation's intentionally deferred full-dataset
reference and same-process steady controls remain skipped, never passed.
The actual merge tree was checked directly; no stale synthetic ref is represented
as a new merge.

## Historical fields and current interpretation

The original plan's preparation/UNRUN wording, source-manifest fields, raw
`unverified`/pending-review flags and validation README's original draft/dependency
paragraph remain snapshots. Actual execution and separate narrow result review
are recorded alongside them. Earlier draft status does not mean the run remained unrun.

PR93's [original cancelled attempt](https://github.com/jliu67/OpenRX/actions/runs/39799339116/job/119895244138)
was explicitly annotated as exceeding the unchanged 25-minute CI limit during
compiler/emulator installation. That failure remains preserved and never counts
as passed. Its single [ordinary retry](https://github.com/jliu67/OpenRX/actions/runs/39799339116/job/120013439526)
passed before reviewed merge `11e8855ec55dd69546f2c8e0321b2bc4d46d0bd3`
at 18:48:11 UTC. Its tree `0b446f08e73cb2dac65c859d2440857c916bc11d`
equaled the reviewed head tree; exact-merge
[foundation](https://github.com/jliu67/OpenRX/actions/runs/39834563003/job/120019335975)
and [scalar](https://github.com/jliu67/OpenRX/actions/runs/39834563356/job/120019337281)
jobs passed. Deferred full-dataset and same-process controls were skipped, not passed.
No workflow, timeout, settings or safeguard was changed.

PR94 retargeted to that main merge without changing its accepted head/tree.
Separate review confirmed identical base-tree contents and unchanged effective diff.
The [approved issue72 handoff](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6348394688)
was accepted with claim null and no warnings; broader issue #72 stays open.
This note supersedes delivery interpretation only and preserves dated history.

## Accepted execution identity and scientific scope

The one approved execution `20261022T181455Z-4424e8848ccf` remains complete:
12 actual tests and one report/two rc0 commands, without skips, timeouts or retry;
wall times were 0.265524 and 0.064212 s. No scientific workload was rerun for delivery.

The [approved plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6347919145)
retained one worker/global slot, CPU600%, RAM1 GiB, swap2 GiB, Tasks256 and
120 seconds plus five seconds supervisory grace per command.

The source-manifest SHA256 remains
`ea52fe4107df66182ba7e828093a1c4207fbe4dad30c32774e0cb8a982028493`;
report SHA256 `456f23c1aa1f7ba921a8f68b1afdd3ae552e609b1600cbcc2ad8d37d8eb7fefd`;
receipt SHA256 `45dfccc7b214655ec3734af62870f148ffc55d9891a09cf33778fdeeec5154e4`.

The source manifest binds 16 files plus itself; the eleven retained inputs and two
pinned tools remained unchanged. All 22 receipt artifacts remain retained with
the immutable runner. The [separate AI result review](../conditional-protocol-floor-20261022/independent-result-review.json)
passed at 18:17 UTC for conditional necessary ceilings only, without blocking findings.
The [report](../conditional-protocol-floor-20261022/protocol-bound.json) retains exact rational output.

Acceptance remains conditional necessary ceilings only: with symbolic `P>0` ns,
`C_i(P)=min(1e9/T_i,1e9/(2P))`, using hypothetical 45 nm HP / 1 V / 360 K
`T1=2.74122 ns` and `T4=0.714793 ns`. This establishes neither actual speedup,
joint attainability, a physical clock nor bank/architecture selection.
Characterized process/PVT/SRAM, clock/interface compatibility, sustainable memory
service and tails, controller/PHY and cache/scratchpad organization, physical
area/frequency, whole-machine power and achieved hashes/s remain open.

The necessary-ceiling ratio is `28260/7369` (about 3.834984) through
`P=0.3573965 ns`, then `T1/(2P)`, and one from `P=1.37061 ns`.
Accepted single-credit source allows same-edge matching backend request/reply
while requiring at least two periods between captures. No additive `ceil(T/P)+2`,
universal extra response clock or bank-count multiplier is introduced.
PR91 occupancy and scripted protocol clocks remain source-specific attributions,
not provider latency or sustainable-throughput measurements.

Migration and full-hash functional acceptance retain their completed scopes.
Hosted checks, generic synthesis and conditional analytical acceptance do not
complete physical or whole-machine performance gates. No further public execution
request, validation run, physical experiment or purchase is authorized here.

## Preservation and verification limits

Only additive delivery documentation was prepared. All seven original publication
documents remain in full, and every accepted original validation file remains
byte-exact. This addendum adds no source/test/model change, scientific workload,
private journal, credential, clone or synchronization action. Delivery conclusions
are bound to verified actual-merge receipts; a head check, readiness transition
or synthetic ref alone does not prove postmerge success.
