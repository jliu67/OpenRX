# Connected prepared v2 lifecycle evidence

[Task #71](https://github.com/jliu67/OpenRX/issues/71), [draft PR #73](https://github.com/jliu67/OpenRX/pull/73),
[EXP-014](../../../experiments/EXP-014-connected-v2-lifecycle.md) and
[interface design](../../../rtl/hash/LIFECYCLE.md) define the scope.

## Exact completed checkpoints

[Icarus bounded](icarus-bounded/summary.json) and
[Verilator bounded](verilator-bounded/summary.json) pass identical one-program ×
one-iteration ideal native workloads in both baseline/prepared modes.
[Cross-backend comparison](verilator-bounded/cross-backend.json) requires exact
PASS records and complete ledger/traffic equality. Each variant takes 528,407
hardware/transport clocks. It initializes/scans every one of 131,072 16-byte
scratchpad beats and returns native final A/digest. These are bounded results.

[Public source checkpoint](validated-source-commit.json) binds all eleven new
source files at `c96e96ab1eb46cb727b21befffa526e637ebed4a`; those bytes are identical
to bounded attempt04 and full attempt05. Its `full_attempt05_pending` field records
publication-time status. Later results must be recorded separately. Ten original
ledger rejection tests pass inside the completed compiled checkpoint. Recovery
and stronger observer successor edits have their separate completed records below.
[Complete blob proof](public-source-proof.json) independently verifies SHA256,
size and execute bits against the frozen manifest for all 4,106 public-tree files.
[Proof notes](full-v2-first/source-proof-notes.json) retain an earlier rejected
archive-stream comparison; only the successful direct blob proof is relied on.

Each bounded directory retains exact consumed-source hashes, commands/tool
versions, native summary/digest, all output hashes, request, source path/inventory
identity, fresh headroom and integrity verification. Complete original sources,
executables, generated C++/VPI/HDL, licensed compile views, traces, stdout/stderr
and receipts remain at the absolute execution paths in those records. The runner's
`scientific_acceptance: unverified` is unchanged; integrity verification and
native assertions do not replace independent review.

## Full default run

Immutable execution `20261016T010320Z-b2c8ed47ab4c` uses the exact public c96
source, prepared/ideal only, 8×2,048. Its native fixture agrees with unchanged
`randomx_calculate_hash`; the [complete RTL result](full-v2-first/summary.json)
passes all 16,384 iterations/6,306,885 retirements/1,434,807 bytecode events,
eight admissions/3,072 loaded words, seven hardware seeds, full 2 MiB and final
32-byte digest. The closing total is 40,975,538 hardware/transport clocks;
[receipt integrity verifies](full-v2-first/verify.json). API-order digest is
`ac16f4ddc7068d476a5e6e5c510c9d27a186e6468e5407225b71e3b51945c7c5`.
This first full result belongs to exact c96. Successor recovery/observer edits
are validated separately; full 8×2,048 was not rerun on that successor. One prepared/ideal hash establishes no paired
full-hash throughput or physical PPA. Native provider host seconds remain separate.
The simulator took 2,451.264 seconds; this host runtime is not a device rate.

## Recovery and accounting successor

[Verilator successor execution](recovery-paired/summary.json)
`20261016T014629Z-8c43e1ea115d` passes four baseline/prepared × ideal/stalled
8×2 native hash modes, six cancellations, eight selected matching errors and one
capacity/reset case. All 31 unit tests and 171 native source checks pass inside
the admitted payload; [receipt integrity verifies](recovery-paired/verify.json).
Each normal mode covers 16 iteration states, 6,167 retirements, 1,334 bytecode
events, eight complete program images, seven hardware seeds, every 2 MiB
program boundary, final A and native digest.

| Profile | Baseline clocks | Prepared clocks | Net clocks saved |
| --- | ---: | ---: | ---: |
| Ideal | 583,950 | 577,680 | 6,270 |
| Stalled | 1,658,825 | 1,652,555 | 6,270 |

The checked equation charges 95 prepared reciprocals ×66 clocks and removes
190 runtime reciprocals ×66 clocks; common native work/stages match. These
deterministic short comparisons establish accounting, not a full-hash throughput
or energy baseline. Stalled profiles discard exactly two stale replies per
scratchpad/dataset/program/metadata request and report actual wait occupancy.
Cancellation and matching errors preserve accepted writes, hold errors/diagnostics,
drain late replies and require a fresh generation/initialization. Error profiles
assert the selected fault reached its target and returned its expected code.

[Icarus capacity-only execution](icarus-capacity/summary.json)
`20261016T020318Z-caa9e8d3a25c` passes the exact same 267 consumed inputs in
four-state simulation; [receipt integrity verifies](icarus-capacity/verify.json).
Its `pass_lifecycle_interfaces` status claims no completed hash. Both simulators
allow exact remaining batch capacity, refuse insufficient image epochs and hash
tag wrap, then recover after a hard reset with drained transports.

[Consumed-source deltas](source-deltas.json) explicitly identify eight changed/new
source files relative to full c96: batch admission, error diagnostics, reference
reciprocal counts, assertions/accounting/tests and child compiler optimization.
Accepted math/iteration/native dataset bytes remain unchanged. All consumed
inputs equal the publication source; later additions are documentation/evidence.
The full default hash remains source-specific c96 evidence.

## Tool and native library provenance

The native library is retained at
`/home/server/openrx-local/v1/executions/20261012T013303Z-848c58102f71/build-only/native-build/randomx/librandomx.a`,
SHA256 `bddb3f9a206b1ec34ca78d3a9b13a9388d7312d6660b7d148d4ed514958fb8d6`.
The driver verifies its successful original receipt/build manifest, PIC flags
and all 171 pinned native source files. It never reconfigures a retired CMake
cache or changes that library.

Verilator 5.020 source commit `5c5314b39cd888f427807d626e1502cbf222c292` and
official Ubuntu prerequisites have [exact archive pins](tool-inputs.json).
The successful fresh tool build is `20261016T005835Z-851d576006d4`:
[commands](tool-build02-commands.json), [result](tool-build02-tool-root.json),
[declared package aliases](tool-build02-package-aliases.json) and
[integrity verification](tool-build02-verify.json).
Binary SHA256 is `d7f6b1ccd5b83ae7cfb1a7ea1778504cf86a29245b4249e1820df9b8978d1ab1`.
Packages are unpacked into fresh execution output; no maintainer scripts, package
installation, `make install`, host PATH/settings or security changes occur.
The build script stages package aliases as regular byte-identical files because
the immutable runner rejects output symlinks. Original archives are retained.

Icarus is four-state; Verilator is two-state. Both use the same native provider
and assertion harness. The old bounded/full c96 traces omit idle rows and do not
capture every inner FSM transition; they cannot calibrate FU occupancy. The
validated successor harness explicitly records iteration/executor transitions and
exports nested executor/reply-wait/stale-drop counters. These observations do not
calibrate functional-unit service or physical timing.

## Failures and resource boundary

[Retained execution index](retained-executions.json) preserves the first failed
RTL compile (duplicate vendor modules), the first tool build's failed symlink
finalization, and successful fresh successors without relabeling failures.
Attempt03 was not admitted because that failed tool build had no accepted
receipt; it is not a simulation result. All raw errors and source snapshots
remain retained under the task's local evidence directory and execution paths.

All heavy work uses installed runner657/global lock with fresh admission and
actual kernel checks: CPU600%, RAM6GiB selected from current safe headroom,
swap2GiB and Tasks256. Compilation uses six workers; simulation is single-threaded.
Tool-build02's recorded live peak was 2,380,460,032 bytes with no swap/limit/OOM
events at that sample; CPU throttling was nonzero (28 periods/7,218 microseconds).
These are sampled resource facts, not complete-run peak or throughput claims.
The successor live sample observed 3,858,407,424 bytes peak so far, zero swap/limit/
OOM events, and nonzero throttling (42 periods/5,684 microseconds). Exact final
process outcomes, manifest/receipt/log hashes and retained source paths are in
the execution index; samples remain explicitly incomplete.

## Reproduction

Use a new authorized immutable-runner request, a fresh output path, exact source
and separately bound retained library/tool receipts. A payload selects bounded
normal/recovery checks with `--programs 8 --iterations 2 --profiles ideal stalled
--variants baseline prepared --cancellation --matching-errors --capacity-checks`.
Use `--full-v2 --profiles ideal --variants prepared` for the full correctness gate.
`--backend verilator` additionally requires `--verilator-root` and
`--verilator-build-execution`; otherwise the driver uses Icarus. Never reuse an
old output directory or write generated output into source.

`scripts/build_lifecycle_verilator.py --pins <bound-pins.json> --output <fresh-output>`
is an admitted run-in-place build, not an installer. On the designated host the
retained absolute archive paths in `tool-inputs.json` are authoritative. On another
compatible x86-64 Ubuntu host, stage those exact URLs/bytes and write a new bound
pins file with the staged absolute `file` paths; never rewrite the original pins
or receipts. Reuse accepted tools instead of rebuilding without a reason.

Unknown provider device cycles, DRAM internal traffic, frequency, watts and area
remain null. Whole-machine efficiency and selected architecture remain open.
Final exact-head CI and a new independent implementation/evidence review are
required before acceptance or merge.
