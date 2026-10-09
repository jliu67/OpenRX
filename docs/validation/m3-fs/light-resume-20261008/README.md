# Extended unchanged light attempt — 2026-10-08

Task [#16](https://github.com/jliu67/OpenRX/issues/16), session
`codex/20261008-light-resume`. Source head
`9d108c4041e0fa440a676f8a3ee1a2db1d736192` was integrated by
[PR #25](https://github.com/jliu67/OpenRX/pull/25) at
`abe066f7c1b17cb3225b55cc45848a153a20ea7a`, with the identical whole tree.

The unchanged real gem5 guest passed all **nine runtime controls** and emitted
**31 exact integer/FP control passes**. It emitted **zero completed hash
values**. Interpreter cache initialization began; no cache pass, hash summary,
hash END/stderr frames, guest-completion marker or hypercall 3 was observed.
[Independent actual review](REVIEW.md) accepts these subsections only; it
rejects complete matrix acceptance.

## Execution and disposition

The launch was requested at 2026-10-08T23:09:15Z with no wall timeout and a
`10^13` per-call simulated tick guard. Exact invocation is in [command.txt](command.txt);
[preflight.json](preflight.json) and [executing-source/](executing-source/)
retain the eight source/configuration/validator snapshots. The original
simulator, Linux resources and retained runtime/hash ELFs were reused, with
no compilation or workload/model change. [integration.json](integration.json)
binds tested source, merge and tree separately.

Independent review of the **exact retained ELF** and actual Atomic width/clock
proved that both mandatory cache initializations alone require at least
10,519,287,679,000 ticks, exceeding the configured 10,000,000,000,000 allowance.
[Budget proof](BUDGET-REVIEW.md), [machine ledger](budget-review.json), and
[root count replay](root-budget-replay.log) preserve the derivation. This
excludes every hash and all other work; it is an execution-budget bound,
not a timing prediction or a hash result.

At 23:54:06Z the session requested one control-C stop because this allowance
could not complete the matrix. The execution tool returned exit 1 with `^C`.
**No final runner report was generated.** Exact termination beyond the
requested tool control is unknown; no handler receipt, child return code or
direct-child reaping result can be inferred. [cancellation.json](cancellation.json)
and [host-disposition.json](host-disposition.json) retain that limitation.
No matching gem5 or wrapper process was observed after the stop. No wall
timeout or tick-guard exit event was observed, and no hash mismatch was emitted.

The retained simulation.json says `running` and records hypercalls 1/2 only;
its last_tick is the **last event checkpoint**, not the live tick at stop.
It cannot supply a final simulator status or elapsed tick count.
[monitor.jsonl](monitor.jsonl) records external phase/file/process observations;
RSS and wall observations are resource evidence, not workload progress
percentages or hardware throughput. [monitor.py](monitor.py) collected them.

## Preserved evidence

[raw-manifest.json](raw-manifest.json) binds all 11 original output files,
including serial, configuration, generated guest script, DTB, citations and
stdout/stderr. Empty stats.txt is retained. Text files preserve original
bytes; device.dtb is stored as base64 with its original decoded size/hash.
No synthetic final report was substituted for the missing one.

[runtime.jsonl](runtime.jsonl) and [runtime-stderr.log](runtime-stderr.log)
are extracted complete frames; [RUNTIME-REVIEW.md](RUNTIME-REVIEW.md) binds
the strict nine-control result. [hash.partial.jsonl](hash.partial.jsonl)
contains 33 records: one configuration, 31 arithmetic checks and one cache
begin. It is explicitly incomplete and fails the full hash validator.
[post-inputs.json](post-inputs.json) is a separate post-session audit,
not a runner report: it verifies all launch-source snapshots, the simulator
and three pinned resources, and equality of both retained ELFs to the exact
base64 payloads embedded in the saved guest script.

## Next execution and acceptance

Use the retained verified simulator and unchanged payloads in a new output
directory, declaring `--max-ticks 100000000000000` explicitly. The proposed
tenfold finite guard is not proven sufficient. The new optional stop-file
control enables the runner's own stop/report path from a separate tool/PID
namespace; its host tests are separate from this old-source actual attempt.
Keep continuous monitoring and preserve failure/partial output.

Acceptance still requires simulator exit zero, complete probe frames with
empty stderr and zero statuses, exact nine runtime plus 39 required
semantic/hash controls (including all eight v2/v1 interpreter/JIT hashes),
matching summary/optional AES skip, guest completion, ordered hypercalls
1/2/3 and unchanged input identities. Full dataset, intended cores/SMP,
BOOM boot, M1 measurements and M4/M5 remain separate gates. No RTL, calibrated
timing, physical power or efficiency result is established here.
