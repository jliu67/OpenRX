# Independent stop-file and workflow review — 2026-10-09

Reviewer: `state_review`, separate from implementation author `runner_review`.
The exact source below is accepted for optional file-requested cancellation and
the manual workflow's explicit light tick allowance. No blocking issue remains.
This is host/source acceptance; no gem5 guest was launched for this review.

## Exact accepted source

The integration baseline is PR #25's actual merge
`abe066f7c1b17cb3225b55cc45848a153a20ea7a` (ABE). Acceptance is bound to these
file bytes, rather than an unpublished final commit identity:

| File | SHA256 |
| --- | --- |
| `simulator/gem5/run.py` | `90edcae3facc3e6348dd5902ed85627919afb0616c9187b75f995695466caaf5` |
| `tests/test_gem5_fs.py` | `99f3471f2405e16208f730ef778a7e4d9581685d257bb656c4c403e879bad2da` |
| `.github/workflows/gem5-fs.yml` | `df121f7abe162994ec0093e34d6da20f422c98fb188bdf104e69a850bd02cac7` |

The source digests were checked again after independent tests and the final
documentation review. Publication, final commit and claim-release receipts
must be recorded separately after they exist.

## Independent validation

Executed from the repository root against the exact accepted runner/test bytes:

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p 'test_gem5*.py' -v
```

The independent full suite passed **257 tests in 9.538 seconds**. The separate
gem5 host-control suite passed **38 tests in 5.476 seconds**. Root's retained
[full log](final-tests.log) separately records 257 passing tests in 9.628
seconds; its [vendor check](vendor-integrity.log) records all 171 files passing.
No new simulator build, native/QEMU artifact replay or actual guest execution
was required for this change.

The lifecycle controls use real host wrapper/simulator processes with synthetic
resources and payloads. They cover externally created stop markers, complete
runtime with incomplete hash frames, stale regular and dangling-symlink markers,
watched normal success, the late-marker completion race, the original positive
timeout deadline and existing launch/timeout/finally signal transitions.

Namespace-correct `kill(pid, 0)` and `waitpid` assertions prove the direct child
is reaped and absent. A test-only Linux subreaper, with its prior setting
restored, adopts the SIGTERM-ignoring descendant, proves its SIGKILL termination
and then reaps it. These assertions do not infer absence from a mismatched
`/proc` namespace. Production reaps its direct child; it terminates the process
group but does not claim to reap arbitrary descendants itself.

Two additional independent real-process checks passed: a FIFO marker created
during `Popen` is observed without opening or blocking on it, and a real host
SIGTERM in that launch window retains the first host-signal provenance even
when a marker is also created. Both checks verified group termination,
direct-child reaping, adopted-descendant termination/reaping and caller-handler
restoration.

## Reviewed behavior and correction

`--stop-file` is optional. Its absolute path preserves the unresolved final
component. `lexists` rejects an existing entry before expensive preparation and
again immediately before launch, including a dangling symlink. The runner does
not create, read, follow or remove the marker. Creating a new entry while the
child is active requests interruption; the entry remains available as evidence.

Only the configured watch enables bounded main-thread polling. A positive
timeout keeps one monotonic deadline after child creation; polling intervals
neither renew it nor count as a timeout themselves. The default retains no wall
cutoff. The no-marker wait path, strict validators, workloads, resources,
simulated model and runtime-only tick default remain unchanged.

Independent review reproduced an initial defect: a marker created after an
already successful child had been reaped could relabel that completion as an
interruption. The final implementation observes `process.poll()` before testing
the marker. It adds both watched-success and deterministic marker-after-reap
regressions. A completed child now retains its normal return code and validation
outcome without sending a signal to a potentially reused PID.

When a live-child marker is observed, the main thread records that observation
and raises SIGINT on itself while the existing non-raising handler is installed.
The same interruption, group cleanup, direct-child wait, handler restoration and
partial-output validation path is used. A complete nine-control runtime stream
survives; an incomplete hash stream still fails. The first signal's identity and
source context remain stable across repeated signals and cleanup transitions.

`interruption_source=stop-file` identifies the observed request context. It does
not uniquely identify an operating-system signal sender: a coincident external
SIGINT between observing the marker and raising SIGINT cannot be distinguished
from the self-signal. The source comment and user-facing evidence retain that
limit. An earlier host SIGTERM retains `host-signal` rather than being relabeled.

## Manual workflow review

Compared with the exact ABE workflow, the offline job, manual guest-job
condition, other guest steps, job properties and timeout policy are unchanged.
The only workflow change is the guest-run shell's conditional tick argument.
Independent YAML/source comparison, `bash -n`, and execution with a shell
`python3` stub reproduced the actual arguments recorded in
[workflow-guard-check.json](workflow-guard-check.json):

| `LIGHT_HASHES` | `--max-ticks` | Hash argument |
| --- | --- | --- |
| `false` | `10000000000000` | absent |
| `true` | `100000000000000` | `--hash-binary build/probe-gem5/openrx-riscv-probe` |

Neither path adds a wall-time or stop-file override. These are shell controls,
not a hosted guest run. The exact retained-ELF
[budget proof](../light-resume-20261008/BUDGET-REVIEW.md) establishes that its two
mandatory cache round loops alone need at least **10,519,287,679,000 ticks** in
the actual width-one, 1000-tick Atomic configuration, exceeding `10^13`.
`10^14` is an explicit proposed finite margin, not a completion guarantee or a
performance prediction. A future workflow build can produce a different ELF;
the exact retained-ELF proof is not silently transferred to that new payload.

## Documentation and actual-evidence review

Reviewed pending `memory/STATE.md`, `memory/HANDOFF.md`, `docs/TASKS.md`,
`memory/DECISIONS.md`, `memory/SESSION_LOG.md`,
`experiments/EXP-002-riscv-functional-preflight.md`, the m3-fs README/reuse
guidance and the actual/stop-file evidence READMEs against ABE and retained
evidence. A separate read-only peer also reviewed that documentation. No
remaining blocking inconsistency or source-binding mistake was found. The
archived pre-resume STATE/HANDOFF match ABE byte-for-byte, and SESSION_LOG
preserves its exact prior prefix.

The records correctly retain the actual earlier-runner result: nine runtime and
31 integer/FP controls pass, **zero hashes** complete, and interpreter cache
initialization begins without an observed cache pass. Tool-session control-C
returned exit 1 without a final runner report. Exact termination mechanism,
handler receipt, simulator return code and runner-performed reaping remain
unknown; observed absence of matching processes does not replace those missing
receipts. No observed wall/tick timeout or hash mismatch is invented.

That actual run executed PR #25 source head
`9d108c4041e0fa440a676f8a3ee1a2db1d736192`, whose tree equals ABE; it did not
execute this stop-file revision. The historical [hosted CI review](../cancellation-20261008/ci-review.md)
continues to identify source head, synthetic PR checkout and actual merge
separately, with 253 Python / 34 host controls and a skipped guest job. Its
native/QEMU replay is separate from the actual partial guest and these new
257/38 host controls. Full hashes, full dataset, intended cores, calibrated
timing, physical efficiency and RTL acceptance remain open.
