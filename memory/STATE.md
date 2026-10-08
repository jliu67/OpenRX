# Current state

Updated 2026-10-08 UTC / 2026-10-07 Edmonton. **M0 complete; Phase 1 source/tooling, P1-05 timing and P1-06S importer implementation/testing complete. M1 measured hardware baseline remains OPEN.** P1-06S task [#13](https://github.com/jliu67/OpenRandomX/issues/13) remains open for independent review; implementation is not peer acceptance or a physical measurement. Project name: OpenRX; private remote: `jliu67/OpenRandomX`.

## Latest engineering result

Implementation `2b28d6fb4604a2b861241d38678e24c8541aed02` adds [power_import.py](../scripts/power_import.py) and 61 synthetic regression tests. The [power protocol](../benchmarks/power/README.md) defines whole-system AC point-power readings, run/digest binding, calibrated affine clock mapping, coverage/gap/error checks, rational timestamp-weighted integration and conditional uncertainty. Synthetic traces require explicit opt-in and never fill measured interval efficiency fields. Original inputs and failures are preserved; the importer cannot acquire or certify meter readings.

[CI run 37726645625](https://github.com/jliu67/OpenRandomX/actions/runs/37726645625), job 113146214930, passed on that implementation: **182 Python tests, 107 upstream RandomX tests, six native steady tests**, with no skips; source/profile/build and existing references also passed. The 61 new tests passed locally on Python 3.13.5, including a final repeat. Native execution occurred in CI, not locally.

Artifact 11528236706 was downloaded; the 68,046-byte ZIP SHA-256 matched `1eacda6564e038bc5933b04bc5030b20b5373b629551e801a64e6bed946a6358`. Actual suite logs were inspected. Three successful native streams joined to explicitly synthetic constant-power traces (12 measurement intervals); the duration-rejected run was refused. The [validation record](../docs/validation/p1-06s/README.md), digest ledger and locally executed reproduction helper retain these checks and the 2027-01-06 artifact retention deadline. No real energy or performance result is inferred from them.

## Prior implementation preserved

- Unmodified RandomX v2.0.1 pinned at `aaafe71322df6602c21a5c72937ac284724ae561`; v2 primary, v1 comparisons, source integrity and all earlier evidence retained.
- Initial Phase 1 `360a925`: source analysis, static profile and hardened upstream runner. That runner still uses separate-process warmup.
- P1-05 `59b469c`, main integration `960b8b5`: separate persistent dataset/VM/worker adapter, known controls, same-process warmup, exact interval boundaries. Do not mix rates with the older harness. See [P1-05 evidence](../docs/validation/p1-05/INTEGRATION.md).
- Protocol v2 `c387b824`: no coordinator, permanent roles or assumed running agents. Per-task issue comments are the sole live claim authority; Markdown summarizes evidence. The router, 57 communication tests, workflow, templates, AGENTS and issue histories are unchanged by P1-06S.
- The entire previous [state](handoffs/pre-p106s-state-20261008.md) and [handoff](handoffs/pre-p106s-20261008.md) are retained byte-for-byte. Their relative links and earlier pending wording are historical; current entrypoints are here and HANDOFF.md. SESSION_LOG remains append-only.

## Next actions and external blockers

1. Any capable visiting agent: review [#13](https://github.com/jliu67/OpenRandomX/issues/13), especially the schema, conditional error model, synthetic isolation and retained failures. Reproduce the 61 tests and artifact join. Request fixes or record evidence-backed acceptance; do not reimplement completed code.
2. [#8](https://github.com/jliu67/OpenRandomX/issues/8): obtain authorized controlled-host access, repeat correctness and collect the fixed-setting v1/v2/thread/AES experiment.
3. [#10](https://github.com/jliu67/OpenRandomX/issues/10): after prerequisites are accepted, validate against real synchronized meter readings, declared physical boundary, response/calibration records and uncertainty. The importer deliberately does not support generic CSV, interval-averaged exports or cumulative energy counters; a real device may need a separately reviewed adapter.
4. [#11](https://github.com/jliu67/OpenRandomX/issues/11): dynamic profiling on the controlled host with supported counters and measured overhead. No bottleneck has yet been established by this work.
5. Independent research #2/#3/#4 may proceed without bypassing the M1/M4/M5 gates.

**No controlled hardware matrix, wall-power samples, dynamic bottleneck profile, RISC-V simulation or RTL result was obtained.** Calibration/synchronization declarations are not independent verification. No hardware purchase, paid compute, account change, model worker or autonomous agent was provisioned.

Read AGENTS, [protocol](../docs/COMMUNICATION.md), [task board](../docs/TASKS.md), hub #5 and the specific task's current comments/receipt before working. Use session-scoped claims, independent branches for overlaps and non-force expected-head updates. Final P1-06S editing-claim release/review request belongs on #13, not the parent milestone #1.
