# Current state

Stage: M0 complete; Phase 1 source/tooling work and **P1-05 same-process instrumentation complete**; **M1 measured hardware baseline still open**.

Project name: OpenRX. GitHub remote remains private `jliu67/OpenRandomX`; repository administrative name was not changed.

## Completed

- Official RandomX v2.0.1 source pinned at `aaafe71322df6602c21a5c72937ac284724ae561`, unmodified; same release supports v1/v2.
- Foundation source manifest, scripts, CI, memory, evidence rules and experiments retained.
- [Phase 1 workload report](../docs/PHASE1.md), reproducible static profile, and upstream runner schema 2 from implementation `360a925` retained.
- New opt-in [same-process adapter](../benchmarks/steady/README.md), implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`: persistent dataset/VMs/workers, independent v1/v2 controls, balanced trial order, immediate warmups, explicit monotonic/realtime clock brackets, range checks, FP-state restoration and exact completed counts.
- New evidence wrapper preserves raw intervals/stderr/metadata, rejects incomplete or inconsistent records and short trials, kills/reaps timed-out process groups, and summarizes only accepted measured-phase records. It does not measure power.
- [Project board](../docs/TASKS.md), issue #1 communications and [agent handoff](HANDOFF.md) track completion, ownership, blockers and next commands.

## Validation and remote status

Historical foundation and initial Phase 1 evidence remain in docs/VALIDATION.md and docs/validation/phase1/. P1-05 was developed on `openrx/p1-05-steady-timing` before integration.

[CI run 37722277487](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487), job `113132440545`, passed on implementation `59b469c`: 171-file integrity, 64 tooling tests (42 previous plus 22 new), deterministic profile, native library/adapter build, all 107 upstream tests, previous smoke/full-dataset controls, and all 6 new native tests. No test skips. New native checks include 8 known-reference controls, repeated known hashes, 1/2/3-worker and AES cases, both 17-nonce differential comparisons, and expected duration rejection.

The actual 66,083-byte CI artifact was downloaded; its SHA-256 matched GitHub metadata. All four raw adapter streams (36 intervals) were revalidated locally, archived summaries matched, and raw/source checksums were checked. See [P1-05 validation](../docs/validation/p1-05/README.md). Local new synthetic tooling tests passed (22); no local RandomX build was possible because direct source download failed. Actual native execution was in CI.

No vendored source or older runner changed. No controlled hardware throughput/AES/thread experiment, wall-power samples, dynamic bottleneck attribution, RISC-V simulation or RTL result exists. The CI runner exposed two logical CPUs; its three-worker case is correctness-only oversubscription, not scaling data. Short native trials do not establish thermal equilibrium or efficiency.

## Next actions and blockers

1. Tooling agent: claim **P1-06S**, the next unblocked software task. Implement a strict power-sample import/validation path against the new clock brackets. Declare CSV units, clock synchronization and power boundary; fail on missing coverage, gaps, invalid timestamps or unsupported alignment; distinguish synthetic tests from real readings. No energy result exists yet.
2. Hardware-capable agent: claim P1-04; identify an actually controlled host, repeat reference controls there, then collect the balanced thread/AES matrix with sufficiently long trials and complete settings.
3. Complete P1-06 only with real synchronized whole-system power measurements and a validated importer. Meter/host access remains unresolved.
4. Complete P1-07 profiling on a controlled host; record counter support, permissions and instrumentation overhead.
5. Continue issues #2/#4 primary-source verification and #3 simulator feasibility without bypassing roadmap gates.

Routine scoped code/research commits are authorized. Do not spend money, alter account/visibility settings, fabricate results or claim agents are running between sessions. P1-05's session editing claim is released at handoff; future agents must read current issue comments and remote HEAD before editing.
