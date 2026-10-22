# Verified project status — 2026-10-20

## Finite-fabric analytical component report accepted — 2026-10-22

The [approved issue #72 plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6331310442)
completed as `20261022T023803Z-dd124df0248e`: all three commands returned zero,
98 actual architecture tests passed (86 retained plus 12 new), and both unchanged
[PR87](https://github.com/jliu67/OpenRX/pull/87) JSON gold files match byte-for-byte.
[EXP-026](../experiments/EXP-026-finite-fabric-service-profile.md) profiles 22 bound
accepted [PR89](https://github.com/jliu67/OpenRX/pull/89) recovery records without
rerunning native/RTL/synthesis/full-hash work. Separate independent result review
accepts `PASS_ANALYTICAL_COMPONENT_REPORT_ONLY`, with no findings.

[Evidence](validation/finite-fabric-service-profile-20261022/README.md) retains
receipt/source/tool bindings and preserves original raw `unverified`/driver pending
flags. Logical fetch descriptors are 93/255 request/response bits and cache
106/619 bits. Ideal two-item serial/concurrent batches take 113,953/61,595 modeled
clocks; stalled batches take 149,685/83,537. These bounded observations are not
full-hash projections or physical performance. Two dataset clients do not establish
two VM contexts or independent scratchpads. Physical service, PPA/frequency/power,
complete-hash alternatives and whole-machine feasibility remain unresolved.
All failed/accepted historical records remain unchanged. Scoped draft publication,
independent final-head review and applicable exact-head checks remain separate;
no new-head CI or merge is claimed, and broader issue #72 remains open.


## Shared-fabric delivery verified — 2026-10-21 23:10 UTC

[PR89](https://github.com/jliu67/OpenRX/pull/89) merged normally at
`b6e71b467bc3c51e1c6734853a08b11412c8653a` on 2026-10-21 at 23:06:29 UTC.
Its tree `d4455f073c858c7df5bd4d2ea7373fa52650df56` equals the reviewed head
`f495a34fc8a67f69b7f3e407cc4b509b96b84d64` tree.
[Independent final-head review](https://github.com/jliu67/OpenRX/pull/89#pullrequestreview-5607170870)
passed. All five exact-head jobs passed:
[correctness](https://github.com/jliu67/OpenRX/actions/runs/39688917220/job/119529913097),
[scalar](https://github.com/jliu67/OpenRX/actions/runs/39688917177/job/119529912958),
[native finalization](https://github.com/jliu67/OpenRX/actions/runs/39688917129/job/119529912861),
[correctness](https://github.com/jliu67/OpenRX/actions/runs/39688910672/job/119529890788), and
[scalar](https://github.com/jliu67/OpenRX/actions/runs/39688910729/job/119529891342).
Both exact-merge [correctness](https://github.com/jliu67/OpenRX/actions/runs/39691207864/job/119537554342)
and [scalar](https://github.com/jliu67/OpenRX/actions/runs/39691207800/job/119537553894)
post-merge checks passed, observed at 23:10 UTC.

[Accepted component evidence](validation/shared-dataset-fabric-20261021/README.md)
keeps the failed mapping and successful recovery distinct. This delivery closeout
changes no source, evidence, scientific result or acceptance criterion. Earlier
draft/partial status remains dated history. Physical services, calibrated
PPA/frequency/power, architecture selection, complete-hash alternatives and the
whole-machine target remain open; issue #72 stays open.


## Shared-fabric recovery component validation accepted — 2026-10-21 22:37 UTC

The [approved recovery plan](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6327859314)
completed all 25 commands across fresh prefix, seven-profile matrix and generic
mapping/parity stages. Each stage passed separate independent result review.
The sole source change replaces variable-indexed response writes with guarded
owner branches and fixed slices; accepted arithmetic remains unchanged RTL.
Fresh prefix/matrix JSONs equal their historical accepted records byte-for-byte;
both mapped JSONs equal the new same-source prefix.

[Recovery evidence](validation/shared-dataset-fabric-20261021/README.md) binds the
source and all three stages. Channel mapping completed in 8.961900 seconds with
6,581 generic cells (801 DFF, no latches); flattened fabric mapping completed in
22.189259 seconds with 14,498 cells (1,615 DFF, no latches). These diagnostics/payload
counts are not physical area, and the channel is contained in the fabric count.
The prior timeout and all original evidence/flags remain intact below. This
completes the bounded component-validation stages; PR89 remains draft for final
publication-head review/checks, tracked on [PR89](https://github.com/jliu67/OpenRX/pull/89).
No new-head CI success or merge is claimed here. Physical services, calibrated
PPA/frequency/power, architecture selection, complete-hash alternatives and the
whole-machine target remain open; issue #72 stays open.


## Generic fabric mapping stopped at its bound — 2026-10-21 21:51 UTC

The separately approved [issue #88 plan](https://github.com/jliu67/OpenRX/issues/88#issuecomment-6327206298)
ran as `20261021T214326Z-597d5d52ca81` on unchanged PR89 source `d3f11cc`.
Independent result review classifies this stage **FAIL/incomplete**. The standalone
channel mapped through explicit ABC in 59.309969 seconds: 6,887 generic cells,
including 801 DFF cells and zero latch cells. Flattened fabric mapping returned
137 after 120.506375 seconds without a fabric netlist. This is consistent with
the enforced 120-second timeout; an OOM kill is not established. Both mapped
compiles and both parity runs remain **unrun**.

[Evidence and review](validation/shared-dataset-fabric-20261021/README.md) preserve
the failure separately from accepted prefix/matrix results and raw scientific
flags. Generic counts include diagnostic counters/payload logic, are not physical
area, and must not be added to a containing fabric count. PR89 remains draft;
issue #88 is incomplete. Final publication-head review/checks are tracked on
[PR89](https://github.com/jliu67/OpenRX/pull/89). No physical services,
PPA/frequency/power, complete-hash alternative performance or target feasibility
is established. Earlier partial/unrun statements below remain dated history;
this update changes only the interpretation of that later stage status.


## Shared dataset-fabric RTL/native matrix — 2026-10-21

[Task #88](https://github.com/jliu67/OpenRX/issues/88) and
[EXP-025](../experiments/EXP-025-shared-dataset-fabric.md) add a bounded two-client
finite shared fetch/cache fabric above unchanged accepted item-session cores.
The prefix passed 14 support tests, 2,045 protocol checks and a reference-correct
native pair. The separately admitted seven-profile matrix completed with exact
compiled-prefix binary reuse and no compilation, unit, native/cache-generation,
synthesis or full-hash rerun. Separate independent bounded matrix-result review passes with no blockers.
[Evidence](validation/shared-dataset-fabric-20261021/README.md) retains the distinct
prefix/matrix receipts, source bindings and complete overlapping clock ledgers.

Controlled ideal serial/concurrent batches measure 113,953 / 61,595 modeled clocks;
stalled batches measure 149,685 / 83,537. Cancellation drains, malformed metadata
and reduced namespace exhaustion have the recorded expected component outcomes.
These measurements do not predict complete-hash throughput. Generic synthesis
and mapped parity remain **unrun**; issue #88 and its feature remain incomplete.
Publication-head review and applicable hosted checks are separate draft-PR gates.

The prerequisite [PR87](https://github.com/jliu67/OpenRX/pull/87) merged at
`c5d53686444d11b10edff200e63d7b725ae782b4` after independent exact-head review,
four head checks and two post-merge checks. Earlier dated pending statements
retain their original publication stage. Completed migration and accepted default
functional full-hash evidence are unchanged. Retained preparation/modeled host
services, physical timing/PPA/power, architecture selection and whole-machine
performance gates remain open; broader task #72 stays open.


## Accepted default hardware-dataset result

One default 8×2,048 RandomX v2 functional hardware-dataset hash is
[independently accepted](https://github.com/jliu67/OpenRX/pull/86#pullrequestreview-5588318967)
at public [source `e8277c63504ef035bb82791263b6842c0cc51f51`](https://github.com/jliu67/OpenRX/commit/e8277c63504ef035bb82791263b6842c0cc51f51),
tree `cb3e0615f9df861a081ba2cbb1d47c65603b84cd`. The separate reviewer's
shared-account technical COMMENT accepts this functional result; it is not formal
GitHub approval. See the [full-result summary](validation/dataset-fullhash-20261020/README.md)
and [sanitized current evidence](status-evidence-20261020.json).

| Evidence | Accepted bounded result |
| --- | --- |
| Native assertions | 16,384 iteration states and 16,384 dataset results; 1,346,699 bytecode accesses; eight complete 2 MiB scratchpad boundaries; seven hardware seed transitions; canonical final-digest equality |
| Independent trace review | All 28,026,133 retained records streamed; exported addresses, counts, order, port-byte totals and phase closure verified |
| Clock ledger | 918,672,902 modeled outer clocks, including 874,905,600 nested dataset-availability clocks; actual 3/3/9 dataset phase vectors emitted and checked |
| Providers | Zero live software input/fill/program/dataset calls, including assertion-only dataset callbacks; allowed input/program assertion counts one/eight |
| Preserved history | Earlier failed full attempt remains failed/scientific-unverified; its missing original dataset ledger/vectors remain absent; raw scientific flags unchanged |

Full data/register equality where exports omit values remains exact bound-testbench
assertion evidence. The corrected accepted result is separate from the earlier
software-assisted c96 full hash, component/capacity results and failed attempts.

## Source publication and dependency merges

[PR86](https://github.com/jliu67/OpenRX/pull/86) merged normally into PR83's feature
branch as [`af1e23d384c4d23d007da816bd8b97ff12712a34`](https://github.com/jliu67/OpenRX/commit/af1e23d384c4d23d007da816bd8b97ff12712a34);
that dependency merge retains the accepted tree `cb3e0615f9df861a081ba2cbb1d47c65603b84cd`.
[PR85](https://github.com/jliu67/OpenRX/pull/85)'s earlier documentation reconciliation
merged on main as [`eee6af85b22ab01c362f7ae37676df5247df29b2`](https://github.com/jliu67/OpenRX/commit/eee6af85b22ab01c362f7ae37676df5247df29b2).
Its complete historical sections and provenance remain preserved.
[PR83](https://github.com/jliu67/OpenRX/pull/83) records final source publication,
independent exact-head review, applicable hosted checks and normal merge outcome.
The accepted execution source and later documentation/integration commits have
distinct identities; the acceptance is not rebound to a later whole tree.

## Remaining gates and handoff

Retained cache/superscalar/reciprocal preparation and modeled host
cache/program/table/scratchpad memory services remain explicit. Autonomous setup,
physical memory/controller services, calibrated frequency, physical PPA,
architecture selection and the whole-machine **1 MH/s below 2,500 W** objective
remain unvalidated. Generic mapping and modeled clocks do not establish them.

Task71 remains closed for its original accepted lifecycle scope and retains later
execution records. Broader formal baseline, selected-core/gem5/full-dataset/SMP,
physical power, profiling and M1–M5 gates remain unchanged. Existing ownership,
source-retention and one-slot admission policies remain. This accepted hash needs
no additional scientific run.

---

## Retained reconciliation — 2026-10-19

The complete record below retains its original source and publication stage.
Its pending-review, draft and next-execution statements describe that dated
snapshot; the accepted corrected result above supersedes their current-status
interpretation only. Its original provenance JSON is unchanged.

# Verified project status — 2026-10-19

This is a dated reconciliation of GitHub main
`fa0bc79bdcd89c91aab11596b6f7f5e104aa6884` and retained execution records.
Earlier dated status entries remain historical evidence. Their original sources,
failures, scientific flags and acceptance criteria are unchanged.

## Delivery and acceptance

| Surface | Verified state | Boundary still open |
| --- | --- | --- |
| Migration/publication | [#27 complete](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454), explicit LOCAL_ACTIVE release; [#31 cleanup complete](https://github.com/jliu67/OpenRX/issues/31#issuecomment-6099136057) | Every new workload still requires its own source/request/resource admission. No standing editable mirror or Git sync. |
| Execution components | PR49/51/53/55/57/59/61/63/65/68/70 merged into main; integer/FP/iteration/seed/finalization/prepared-reciprocal work is retained | Component correctness and generic mapping do not establish physical timing, power or area. |
| Connected software-assisted hash | [PR73 merged](https://github.com/jliu67/OpenRX/pull/73); [qualified independent review](https://github.com/jliu67/OpenRX/pull/73#pullrequestreview-5542293357) accepts the original full-run evidence transfer | The full 8×2,048 result remains attributed to exact `c96e96ab1eb46cb727b21befffa526e637ebed4a`, with software providers and separately validated successor edits. |
| Later hardware components | PR76/77/78/79/80/81/82 merged; main ends at [PR82](https://github.com/jliu67/OpenRX/pull/82) | Initial fill/program/input hashing, superscalar execution, item/lifecycle/capacity evidence has bounded scopes; default hardware-dataset full-hash acceptance is separate. |
| Architecture tool | [PR74 merged](https://github.com/jliu67/OpenRX/pull/74); [#72 closeout](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6211077285) accepts the scoped analytical tool | #72 remains open/review. Alternative full-hash timing, physical feasibility and final architecture selection are unresolved. |
| Full hardware-dataset candidate | [PR83](https://github.com/jliu67/OpenRX/pull/83) remains draft at `8e4164230ce633bbe43a385003659680cfec2925` | Six hosted checks passed at that publication head; the retained full attempt failed and has no scientific acceptance. |

PR84 repaired test discovery and [merged only into PR83's feature branch](https://github.com/jliu67/OpenRX/pull/84),
producing `8e416423`. It is not a main merge. Its [independent review](https://github.com/jliu67/OpenRX/pull/84#pullrequestreview-5567152029)
does not rebind execution to the newer publication tree. The six publication-head checks
include [Foundation](https://github.com/jliu67/OpenRX/actions/runs/39202984697/job/117899719289),
[RISC-V](https://github.com/jliu67/OpenRX/actions/runs/39202984676/job/117899719410),
[capacity](https://github.com/jliu67/OpenRX/actions/runs/39202984660/job/117899719220) and
[finalization](https://github.com/jliu67/OpenRX/actions/runs/39202984654/job/117899719064),
plus the push Foundation/RISC-V checks. Hosted correctness is not full-hash acceptance.

## Retained full-attempt status

Execution `20261019T032907Z-e8ffa2ec5555` remains bound to source
`b5f459982e95ad447ba181d957be825e2a0d34d7`, tree
`cc1fea901c89bd2b4f8b58a0ab0d9b982abf455a`.
The independently reviewed corrected preparation passed 30 units, canonical full
native-reference comparison and model compilation; it did not execute the RTL hash.

The retained supervisor checkpoint recorded six of eight program boundaries,
12,288 iteration states/dataset responses, six complete 2 MiB scratchpad comparisons
and six seed comparisons. These were earlier partial observations, not final attained coverage or completed acceptance.
A later terminal receipt, dated 21:33:03 UTC, records `PROCESS_FAILED`, return code 1,
and scientific acceptance `unverified`; the driver summary says `failed` and
`full_hash_execution: false`. The retained integrity-verification record reports
integrity verified. Terminal cause and source/artifact review belong to the existing
supervisor; this reconciliation makes no failure diagnosis or full-hash pass claim.
[Compact status provenance](status-evidence-20261019.json) binds the small retained
records without republishing private host/process/resource details.

Do not restart, duplicate, take over or compete with this execution/supervisor.
Preserve its frozen inputs, builds, outputs and failures. Any successor requires
separate authorization/review/admission; this status correction launches no work.
Complete native comparisons, final digest, nested clock-ledger closure and
independent scientific/source review remain required for acceptance. The retained
terminal integrity-verification status is reported above.

## Meaning of the results

[EXP-022](../experiments/EXP-022-dataset-session-capacity.md) proves finite session
capacity with 16,384 protocol-derived items, plus native item and 2×1 connected
checks. It does not prove a default hardware-dataset hash. Its ideal/stalled totals
641,182 / 1,754,985 are modeled clocks. The 874,905,600 full-workload dataset-clock
sum is an input-derived expectation; neither that sum nor a simulator wall time is
physical ASIC throughput. Dataset availability stays nested in the outer total.

Autonomous cache/program/table preparation, physical bank/controller/memory services,
calibrated frequency, physical PPA and architecture selection remain unresolved.
The whole-machine objective of **1 MH/s below 2,500 W**, including memory,
PHY/controllers, fans and PSU losses, remains unproven. BOOMV3 is a provisional
reuse baseline, not identified X9 silicon or an accepted final architecture.

## Shared pool and next handoff

GitHub issue comments/receipts remain the live ownership authority; the Markdown
board is a summary. The observed open pool is #1/#2/#3/#5/#8/#10/#11/#12/#14/#16/#66/#72.
#2/#10/#11/#12/#14 are blocked; #3/#8/#66/#72 are in review; #16 is ready.
Labels do not override manager scope, external prerequisites or scientific gates.
#71 remains closed for its original accepted lifecycle delivery and is reused as
an execution record; do not reopen it merely to report later evidence.

Formal #8/M1, physical power #10, profiling #11, selected-core/full-dataset/SMP #3/#16,
calibrated M4 #14 and architectural M5 #12 remain open. The accepted native pilot
is distinct from the [later incomplete formal candidate](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6132381807).
The [bounded gem5 light matrix](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891)
passes 39 required plus nine runtime controls with optional AES skipped; it does
not complete those broader gates. #41 is completed planning to reuse, not a new task.

Next status evidence comes from the existing supervisor's terminal review and
the documentation PR's independent exact-head review/checks. Historical audit #66
and external-link findings remain scoped to their recorded trees. No milestone,
claim, dependency, acceptance criterion, setting or access is changed here.
