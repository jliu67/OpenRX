# Project status

Updated 2026-11-28 against main `fee4e697741ce520fa917405a58ec9914f071498`
(after [PR #98](https://github.com/jliu67/OpenRX/pull/98) merged).
[Issue #72](https://github.com/jliu67/OpenRX/issues/72) is the current architecture
research and review thread. The whole-machine **1 MH/s below 2,500 W** target,
final architecture and physical PPA remain unvalidated.

## Accepted and reusable work

| Work | Evidence and exact scope |
| --- | --- |
| Default functional hardware-dataset hash | [Accepted result](validation/dataset-fullhash-20261020/README.md), [source-bound summary](status-evidence-20261020.json): one 8×2,048 v2 hash at source `e8277c6`/tree `cb3e0615`; native states, dataset results, eight complete scratchpad boundaries, seven seeds and final digest agree. The 918,672,902 modeled clocks include nested dataset availability. Retained preparation and modeled host memory services remain explicit. |
| Earlier software-assisted connected hash | [EXP-014](../experiments/EXP-014-connected-v2-lifecycle.md) and [evidence](validation/connected-v2-lifecycle-20261016/README.md). This is a distinct source/provider scope, not a replacement for the later hardware-dataset result. |
| Components and conditional service models | [Experiment index](../experiments/README.md) and [validation records](validation/) retain exact arithmetic, lifecycle, fabric and conditional SRAM outcomes. Generic mapping, behavioral-port results and analytical ceilings are not characterized physical service. |
| Reproducible shared-context VM source | Merged [PR #98](https://github.com/jliu67/OpenRX/pull/98), [source and reproduction](../experiments/shared_context_vm/). Accepted benches cover shared execution/fetch and four independently initialized iteration checkpoints from one input. Preparation/loading are untimed; this delivery does not implement consecutive-iteration carry or certify cancellation through the iteration shell. Exact external native assets and pinned tools remain required. |

<a id="pr96-delivery-closeout-recorded-2026-11-04"></a>

PR96 delivery is complete: the [verified closeout](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6353946679)
records its reviewed merge and applicable checks. [EXP-029](../experiments/EXP-029-prepared-fetch-sram-port.md)
and [evidence](validation/prepared-fetch-sram-port-20261022/README.md) retain the
bounded behavioral SRAM-port result. Deferred controls were skipped, not passed.

## Current architecture research

Engineering is paused for external audit. The [audit snapshot](../experiments/audit_20261128/)
provides source, ordinary reproduction and selected retained results, including the
failed FP activity collector and administrative recovery. It adds no physical acceptance.

The [November 27 milestone](https://github.com/jliu67/OpenRX/issues/72#issuecomment-7212687875)
separates four-input canonical native counts, bounded mapped-scalar validation
and source-order locality from physical claims. The
[dependency/resource frontier](https://github.com/jliu67/OpenRX/issues/72#issuecomment-7221225073)
records conditional recurrence, issue and private-capacity bounds; lower bounds
are not achievable schedules or a selected architecture.

The [November 28 update](https://github.com/jliu67/OpenRX/issues/72#issuecomment-7232430380)
records the latest public scoped outcomes:

- SRAM64/P3 native checks pass, but one input exceeds the declared timing budget;
  the equal-weight two-input average leaves only 0.67% before omitted costs.
  Bank/controller timing and whole-machine energy are physically unqualified.
- valuegraph65 passed its build, 21 directed groups and six DATA/validator tests;
  the first in-place run hit the modeled progress guard with zero comparison rows.
  Cursor starvation is plausible, not proven. There is no improvement result or
  architecture rejection; the corrected comparison is blocked by the retained
  evidence/build envelope.

The next research priority is the whole-machine cost of execution resources,
private-state residence, operand/metadata ports and memory service before another
implementation campaign. Detailed new experimental evidence stays local, with
reviewed milestones on issue #72; this page does not duplicate execution diaries.

## Remaining acceptance gates

- Retained cache/superscalar/reciprocal preparation and modeled services remain
  explicit. Autonomous setup and complete physical memory/controller/PHY supply,
  including latency tails, still need evidence.
- Exact source-bound native behavior, rounding, ordered memory, ownership,
  cancellation and declared v1/four-state coverage remain required within each
  experiment's scope. A bounded component pass does not accept a full design.
- Characterized technology/PVT, loaded timing, area, switching/leakage and
  whole-machine power (including links/controllers, cooling and conversion)
  are unresolved. Modeled clocks, generic cells and assumed frequency do not
  establish hashes/s or hashes/J.
- Formal baseline, selected-core/gem5/full-dataset/SMP and M1–M5 criteria remain
  as recorded in the [roadmap](ROADMAP.md) and [task board](TASKS.md). Existing
  source retention, independent review, applicable checks, exclusive execution
  and fresh admission/resource safeguards are unchanged.

Original failures, scientific-unverified flags, skipped controls and accepted
source identities retain their meaning. Separate AI technical review is not
formal human/account-holder approval. Status text authorizes no new workload.

## Historical records

Use the [experiment index](../experiments/README.md), [validation records](validation/)
and linked issues/PRs for individual results and delivery checks. The complete
[previous status timeline](https://github.com/jliu67/OpenRX/blob/fee4e697741ce520fa917405a58ec9914f071498/docs/STATUS.md)
and [previous README](https://github.com/jliu67/OpenRX/blob/fee4e697741ce520fa917405a58ec9914f071498/README.md)
are pinned to the pre-cleanup main commit. Historical memory/handoff entries are
dated snapshots; use this page and issue #72 for current navigation. No evidence
files or scientific acceptance criteria were removed by this condensation.
