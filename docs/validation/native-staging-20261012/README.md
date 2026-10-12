# Native staging software validation — 2026-10-12

## Current accepted outcome — 2026-10-12

The isolated build and **supported native correctness** are independently
accepted for the exact executed source `4a4e30bbbda47cce7713c280d87f1506f7c6f954`.
The documentation reconciliation does not relabel that execution source as a
later documentation commit. [Task #35](https://github.com/jliu67/OpenRX/issues/35)
is the live publication/review authority; selected non-identifying results and
original receipt identities are in [accepted-results.json](accepted-results.json).
Raw host records and detailed capability witnesses remain privately retained.

Build `20261012T013303Z-848c58102f71` completed with exit zero in 9.96 seconds.
Source and artifact bindings, seven logs, all 169 receipt artifacts and actual
compile/link provenance were independently checked. The new steady executable
is 255,608 bytes, SHA-256
`a1ebd867a845640e5d080be77806942dde0f6f51e45db7a9a93c5e6e047817cf`.
It is a new reproducible artifact; the no-argument developer build remains distinct.

Correctness `20261012T024840Z-8c34147db074` completed with exit zero. Independent
review checked all 44 receipt artifacts, staged/source/binary/journal bindings,
106 supported upstream passes plus one exact source-defined conditional skip,
the unchanged six native tests/four configurations, eight known-reference
controls, two 17-nonce differential matches and 16 invalid-CLI rejections.
All four intentional too-short measurement intervals are retained as rejections.
The exact conditional test identity and capability evidence stay private;
unexecuted configuration/all-ISA coverage remains explicitly unresolved.
Do not report 107 upstream passes or complete configuration coverage on this run.

The build used six compile workers; the native suite retained its original
hashing/init worker counts. Actual resource and ancestor admission passed.
Observed aggregate cgroup peaks were 592,883,712 bytes for the build and
2,503,630,848 bytes for correctness, with no OOM or cgroup throttling. These are
execution-resource observations, not performance/efficiency results. Both final
receipts verify against the external journal; descendants drained and the slot
was released. Source/vendor bytes, immutable runner and scientific criteria are
unchanged.

History is preserved: the first build attempt failed before compilation on an
optional telemetry read; the first submitted correctness attempt was denied by
fresh headroom before child launch. A separately reviewed collector correction
and a fresh reviewed-range allocation produced the successful executions.
No failed key/receipt was reused, no reserve or admission gate was weakened,
and no earlier record was overwritten.

**#8/EXP-001/M1 remain open.** This proves supported functional correctness, not
the controlled thread/AES throughput matrix, calibrated timing, synchronized
wall power, profiling or complete all-configuration coverage. Short raw harness
rates are diagnostic; do not mix harnesses or promote them into a baseline.
[PR #36 merged normally at 77cc171a](https://github.com/jliu67/OpenRX/commit/77cc171a935780788ceceb15f75d5c0e3a556650)
after [exact-head review](https://github.com/jliu67/OpenRX/pull/36#pullrequestreview-5486270130)
and successful [postmerge foundation](https://github.com/jliu67/OpenRX/actions/runs/38199767807)
and [scalar checks](https://github.com/jliu67/OpenRX/actions/runs/38199767808).
[Task #35 is completed](https://github.com/jliu67/OpenRX/issues/35#issuecomment-6117228235);
the merged tree matches the reviewed head. This closes implementation only,
without a throughput pilot, simulation or research-milestone completion.

## Historical preparation snapshot — preserved

Task [#35](https://github.com/jliu67/OpenRX/issues/35), base main
`3ee72cc4840b35b7a4e655276f100ab699c8f4cb`. Owner approved adapter/tests and
draft PR publication. **Implementation awaiting independent review; no native
build, full-dataset run, controlled measurement or M1 acceptance is claimed.**

The build helper uses a fresh external destination and explicit pinned library
path. Launch/control adapters accept external input/build/output locations,
verify staged artifact/source digests and preserve the existing strict record
oracle. Retained original/pinned source, builds, data and receipts were untouched.
No simulator, immutable runner, settings, synchronization or vendor changes.
The native wrapper also avoids signaling a numerical process group after its
child was already reaped during interruption; a focused fixture checks this.

Commands:

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p test_local_execution.py \
  -k test_finalizer_timeout_protocol_handles_path_and_abstract_socket_and_joins_thread -v
python3 -m unittest discover -s tests -p test_native_staging.py -v
bash -n scripts/build_steady.sh
python3 scripts/stage_native.py --help
python3 scripts/steady_benchmark.py --help
python3 tests/native_steady.py --help
```

All 171 vendor files verify. The broad lightweight suite exercised 313 tests:
312 passed; one existing finalizer test could not bind a temporary Unix socket
under the sandbox. Its permitted targeted rerun passed. The final 16 staging
fixtures pass after the last code edit; Bash syntax and all three CLI help
checks pass. The original sandbox failure is retained, not relabeled as a clean
single-run suite. [Index](index.json) binds the raw and public log digests.

New fixtures cover source/symlink isolation, preservation of existing builds and
evidence, vendor-failure ordering, missing artifacts/receipts/binaries, malformed
receipts, changed source/artifact rejection before launch, external provenance
copies, location options excluded from native argv, retained duration rejection,
native control path routing and reaped-child signal safety. Tool/build fixtures
are synthetic and do not compile or measure RandomX.

The pinned GitHub archive omitted six manifest entries. Each was copied into
temporary staging from the retained original only after verifying its exact
manifest digest; the index lists all six. No vendor byte was changed and these
materializations are not new PR changes.

Heavy checks are explicitly unexecuted: native compilation, 107 upstream tests,
six full-dataset steady controls and the controlled thread/AES matrix. Parent
thread messaging returned `thread not found`; no compute-slot approval was
received, so no heavy job was submitted. Existing immutable local-runner gates,
one payload slot, measured memory headroom and uncontended native measurement
still apply. Independent source/request review must precede those runs.

At the lightweight host inspection the process saw six CPUs, 16,725,934,080 bytes
RAM, 5,989,568,512 bytes MemAvailable and 8,589,930,496 bytes swap; these are a
dated observation, not admission evidence. The proposed build uses six workers
with unchanged owner-local-max-v1 resource selection. Fresh host/cgroup checks
and measured utilization/peak memory must determine the real budget. The native
controls allocate over 2 GiB and require their own serialized reviewed request.
The [staging specification](../../../benchmarks/steady/README.md#isolated-local-staging-and-controls)
provides exact portable commands; #8/EXP-001 and M1 remain open.
