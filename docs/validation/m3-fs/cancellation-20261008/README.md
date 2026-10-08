# Simulator cancellation controls — 2026-10-08

Task [#16](https://github.com/jliu67/OpenRX/issues/16), session
`codex/20261008-light-resume`, base
`50ba83166a9df0fca243af57a7c889ec752a59fc`.

Removing the default wall cutoff makes explicit cancellation important. The
previous runner could leave the simulator running after SIGINT/SIGTERM and
could skip extraction of already completed runtime controls. The revised
runner starts its child in a separate session, records cancellation, kills its
process group, waits for its direct child, and restores the caller's handlers.
It then rechecks input identities and extracts completed controls. Cancellation
or timeout always fails the overall attempt.

Independent review caught two races in the first exception-raising patch:
a signal inside the timeout handler escaped its sibling catch clause, and a
signal at entry to `finally` could skip cleanup. That version was never
published or used for a real gem5 attempt. The final handler records and stops
the child without raising into arbitrary Python bytecode. Two deterministic
real-process signal injections cover those transition points.

Seven new Linux subprocess controls exercise SIGINT, SIGTERM, an explicit
timeout, the launch window, both transition races, and successful execution.
They use synthetic simulator/resources/payloads and the independent runtime
oracle. They establish host lifecycle/evidence behavior; they do not execute
gem5 Linux. Same-group descendants are terminated; the runner reaps its direct
child. An orphaned descendant zombie may await the host init's reaping.
The test process temporarily adopts orphaned descendants with Linux subreaper
support and verifies actual SIGKILL termination with `waitpid`, then reaps them.
It restores its previous setting. These checks use `kill(pid, 0)` and `waitpid`
rather than assuming `/proc` belongs to the same PID namespace.

The default remains no wall cutoff (`--timeout 0`); positive limits remain
opt-in. The separate simulated tick guard, guest programs, strict validators,
resource pins and model configuration are unchanged.

Root validation:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify_vendor.py
```

All **253 Python tests passed** in 8.366 seconds; all **171 vendor files passed**.
[Full final test log](final-tests.log). Author's targeted gem5 suite passed
34 controls; independent acceptance and source bindings are recorded in
[REVIEW.md](REVIEW.md).

Earlier staging failures are retained: [baseline snapshot log](baseline-snapshot-tests.log)
has two missing fixture errors because the initial local text snapshot omitted
two committed JSONL fixtures. Restoring those exact files resolved the errors.
[Intermediate log](intermediate-tests.log) captured an obsolete source-text
assertion while the helper refactor was in progress; it was updated for the
helper's unchanged no-cutoff behavior. These logs are not final acceptance.

This repair and its tests are separate from the actual guest evidence. No hash,
full-dataset, calibrated timing, measured power or RTL result follows from them.
