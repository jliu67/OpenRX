# Native staging software validation — 2026-10-12

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
