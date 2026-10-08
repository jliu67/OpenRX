# Current handoff — Phase 1 timing and communication integrated

Session: `chatgpt/20261008-p105`, 2026-10-08 UTC / 2026-10-07 Edmonton. User requested continued Phase 1 work. **P1-05 is complete; M1/Phase 1 remains open.**

## Start here

Read AGENTS.md, PROJECT.md, STATE.md, DECISIONS.md, OPEN_QUESTIONS.md, [the task board](../docs/TASKS.md), [communication protocol](../docs/COMMUNICATION.md), [hub #5](https://github.com/jliu67/OpenRandomX/issues/5), and the selected issue's latest comments/claim expiry. Use an Agent task/message and a unique session for scoped work. A receipt confirms routing, not that another model is running.

P1-05 implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676` and its evidence/handoff commit `fee2a3bd74a8d4f3a5e7fdc592c33edc760cc89e` were prepared on a separate lineage from base `ea90554`. Before main integration, the expected-head check found communication commits through `9d1a8e3920d74a4dee75e66fe4df048876d11953`. They were preserved, not overwritten. Both lineages are parents of the integration commit. D012-D014 retain communication meanings; P1-05 decisions use D015-D017.

## Verified P1-05 result

The [opt-in steady adapter](../benchmarks/steady/README.md) reuses the dataset, VMs and workers across known controls, same-process warmups and alternating v1/v2 trials. It records explicit clock brackets, completed hashes, raw evidence and failure status without modifying vendor code or the old runner. Its timing envelope includes worker scheduling/bookkeeping but excludes dataset initialization and logging. Do not mix its rates with the upstream harness's different scheduling/batch overhead.

[CI run 37722277487](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487) on `59b469c` passed 64 tooling tests, 107 upstream tests, six native tests and all prior controls. No skips. The downloaded artifact's SHA-256 matched; all four raw streams/36 intervals were revalidated locally. Eight known controls and both differential comparisons matched; four duration rejections were intentional tests. These are correctness results, not controlled performance/power measurements. See [full evidence](../docs/validation/p1-05/README.md).

The concurrent [communication implementation and validation](../docs/validation/communication/README.md), router, templates, AGENTS instructions and issue histories are preserved unchanged. Its 45 tests were independently validated in that session. Combined integration CI must be checked at the actual merge SHA; do not infer a combined test run merely by adding suite counts.

## Next unblocked work

**P1-06S: power-sample importer and validator.** Define timestamp/unit/device/boundary metadata, clock mapping, complete interval coverage, gap/clock-step rejection, numerical integration and uncertainty handling. Clearly label synthetic fixtures and do not populate real power or hashes/J from them. Real meter/host access is still required for P1-06 physical validation.

P1-04 needs a controlled host for the actual repeated thread/AES experiment. P1-07 needs dynamic profiler/counter access. Keep uninstrumented throughput separate from profiling. Do not buy hardware, rent compute, provision model workers or change permissions automatically.

```bash
python3 -m unittest discover -s tests -v
bash scripts/build_steady.sh
bash scripts/test.sh
python3 tests/native_steady.py
```

Choose the target host and pilot counts from the [adapter protocol](../benchmarks/steady/README.md). Clock brackets alone do not certify meter synchronization. The CI three-worker case oversubscribed two exposed CPUs and is not scaling evidence.

## Preserved prior handoffs

The complete [communication handoff snapshot](handoffs/communication-20261008.md), [P1-05 detailed handoff snapshot](handoffs/p1-05-20261008.md), and [P1-05 branch session log](handoffs/p1-05-session-log-20261008.md) are retained byte-for-byte. Relative links inside these relocated historical snapshots may resolve differently; use current links above or their original commits. Historical references to P1-05 as pending are superseded by this current handoff. The current SESSION_LOG preserves the mainline communication entry and appends P1-05 integration.

This session did not launch another agent. Final status and advisory claim release are posted on issue #1 and acknowledged on hub #5. No local native RandomX build, real wall-power sample, PMU profile, RISC-V simulation or RTL result was obtained. Native validation ran in GitHub CI; local work was synthetic tooling, syntax checking and downloaded-evidence validation.
