# File-requested simulator stop and light guard — 2026-10-09

Task [#16](https://github.com/jliu67/OpenRX/issues/16), session
`codex/20261008-light-resume`, based on PR #25's merged
`abe066f7c1b17cb3225b55cc45848a153a20ea7a`.

A tool-session control-C ended the actual long guest attempt without producing
a final runner report. Exact tool termination beyond that request is unknown;
[the actual record](../light-resume-20261008/REVIEW.md) retains this limitation.
The new optional `--stop-file PATH` lets an operator in another tool/PID
namespace create a marker that the runner observes itself. It raises SIGINT
while its handlers are installed, stops the simulator process group, waits
for its direct child and validates completed controls into a failed report.
No separate controller thread is introduced.

Choose a nonexistent path at launch. Existing entries, including dangling
symlinks, are rejected before launch. The runner never reads marker contents
or creates/removes the marker. Main-thread polling keeps one original positive
timeout deadline; the default remains no wall cutoff. Completed children are
observed before late markers so a normal success is not relabeled.
`interruption_source=stop-file` records observed stop intent; a coincident
external SIGINT cannot be uniquely distinguished from the self-signal.

Four new real-process controls cover file-requested cancellation with complete
runtime/incomplete hash frames, stale/dangling markers without launch, watched
normal success and a deterministic late-marker race. The existing explicit
timeout test now uses the polling path and verifies that its deadline is not
renewed. Group termination/direct-child reaping is checked using the existing
Linux subreaper fixture. These are real **host** processes with synthetic
simulator/resources/payloads; they do not execute gem5 Linux.

Independent review found that the initial polling patch checked a marker
before observing an already-exited child. It was corrected and both success
controls added before publication. Source and evidence acceptance are in
[REVIEW.md](REVIEW.md).

Root validation:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_vendor.py
```

All **257 Python tests passed** in 9.628 seconds, including **38 gem5 controls**.
All **171 vendor files passed**. [Final full log](final-tests.log),
[vendor check](vendor-integrity.log). Runner SHA256 is
`90edcae3facc3e6348dd5902ed85627919afb0616c9187b75f995695466caaf5`;
tests SHA256 is
`99f3471f2405e16208f730ef778a7e4d9581685d257bb656c4c403e879bad2da`.

The manual workflow now uses an explicit `10^14` guard for light controls and
retains `10^13` for runtime-only work. [Host shell checks](workflow-guard-check.json)
validate Bash syntax and both conditional argument paths. The exact retained
ELF [budget proof](../light-resume-20261008/BUDGET-REVIEW.md) motivates this
proposed finite margin; it does not guarantee completion for a future ELF.

The actual saved guest executed the **earlier PR #25 runner**, not this
stop-file revision. Actual partial runtime/arithmetic evidence, hosted
native/QEMU replay and these host lifecycle tests remain separate. No full
hash, full dataset, timing, power or RTL result follows from this change.
