# Phase 1 handoff

Session: 2026-10-08 UTC / 2026-10-07 Edmonton. Agent: ChatGPT. User instruction: begin Phase 1 and keep progress and agent communication in this repository.

## Resume here

1. Read AGENTS.md and [docs/TASKS.md](../docs/TASKS.md), then issue #1 and its latest comments. The previous session's editing claim is released at handoff; no background agent is running.
2. Review implementation `360a9255703a28845a799cfcc1086d1fb84a2c48` and [PHASE1.md](../docs/PHASE1.md). The initial reviewed base was `2e6f3653883c4a8b344be4c4c7e4b1d8dfec0df4`.
3. Reproduce `python3 -m unittest discover -s tests -v` and `python3 scripts/workload_profile.py`; then follow the report's native control commands on the intended benchmark host.

## Completed and verified

- Source-derived workload map and deterministic profile; no vendored source changes.
- Runner schema 2: warmup separation, median/range summaries, duration gate, pinned-reference checks, integer bounds and affinity safeguards; resource restrictions captured.
- 42 tooling tests passed locally and in CI. Synthetic fixture outputs in these tests are NOT mining measurements.
- CI run [37719337133](https://github.com/jliu67/OpenRandomX/actions/runs/37719337133), job 113123130624, succeeded at implementation commit `360a925`: 171-file vendor integrity, native build, 107 upstream tests (no skips), v1/v2 smoke, v1/v2 full-dataset reference controls, artifact upload.

## Next work, in priority order

A hardware-capable agent should claim P1-04 on issue #1, identify the actual host and available cores/memory, repeat known-hash controls, then collect the balanced v1/v2/AES/thread matrix. Keep uninstrumented throughput trials separate from profiler runs. Record all raw results and configuration, not just best values.

A tooling agent can independently claim P1-05: implement and test explicit same-process warmup and timestamped steady-state hashing intervals in a separate adapter or reviewed patch. Do not silently change vendor/randomx. The current `--warmups` only preconditions via separate processes; `hashing_seconds_approx` is not a power-meter synchronization marker.

P1-06 requires real meter access and synchronized energy samples. P1-07 requires appropriate host counters and a documented method. No host, meter or external agent has been provisioned or assigned in this session. Do not spend money automatically.

## Known caveats and preserved failures

The local execution workspace could not resolve codeload.github.com; public web fetches were unavailable. Therefore this session did not download/build the full native source locally. Connector reads and a Git-blob-verified configuration copy supported local tooling tests; native integration was actually executed by the existing GitHub CI workflow.

CI retained upstream CMake minimum-version and missing GNU-stack/executable-stack linker warnings, plus inherited Node.js action-runtime deprecation warnings. Do not hide them or change vendor code without an explicit reviewed patch. The full CI job log was inspected. Individual benchmark JSON/raw files were uploaded in artifact 11524827413 but were not independently downloaded through the connector in this session; the successful runner enforced the known reference constants.

CI logs/artifacts may have a retention limit. Preserve any results used in future performance claims in reviewed repository evidence before they expire. Do not infer throughput or hashes/J from CI step durations. No controlled hardware efficiency result, PMU profile, RISC-V simulation, RTL implementation, or competitiveness claim was produced.
