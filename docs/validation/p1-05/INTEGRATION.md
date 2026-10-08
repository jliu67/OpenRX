# P1-05 / communication integration

Integration joins current main `9d1a8e3920d74a4dee75e66fe4df048876d11953` and P1-05 evidence commit `fee2a3bd74a8d4f3a5e7fdc592c33edc760cc89e` (implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`). Both parent histories must be retained. No force-push is permitted.

All P1-05 source/build/test/workflow blobs are reused unchanged from the passed branch run. All communication code, tests, router workflow, templates, protocol, AGENTS and validation are retained from main. Shared README/board/state/handoff documents were reconciled rather than selecting one side wholesale. Existing SESSION_LOG content is preserved as a prefix. Communication decisions D012-D014 keep their identifiers; new P1-05 decisions use D015-D017. Previous complete handoffs are archived byte-for-byte under memory/handoffs/; relocated historical relative links are not the current navigation entrypoint.

## Validation at integration publication

P1-05 component run 37722277487 passed 64 tooling tests, 107 upstream tests and six native tests; its downloaded raw artifact was validated as described in [README.md](README.md). Communication component validation is preserved in [../communication/README.md](../communication/README.md).

The integration will run the existing combined CI. Its outcome must be read from the actual integration commit/run; it is **not yet claimed as passed in this publication record**. Later results belong in an append-only update here and the issue handoff. Combining test counts is not a substitute for execution.

Neither component nor integration CI completes the controlled hardware/power experiment. M1 remains open. P1-06S importer software is ready but not implemented; physical host, meter and counter access remain unresolved.

## Final observed outcome — 2026-10-08 UTC

The preceding publication-time pending status is now superseded by this observed result. **Integration commit `960b8b52b40b994fe65704d84c5a0922e676e821` is on main**, advanced through a non-force expected-head update from `9d1a8e3`. Comparison against each parent confirmed the tested adapter and existing communication implementations were preserved; SESSION_LOG changed only by appending to the prior mainline contents.

[Combined CI run 37724306425](https://github.com/jliu67/OpenRandomX/actions/runs/37724306425), job **113138855011**, completed successfully. Every reported step passed. The actual uploaded logs were downloaded and inspected.

| Executed check | Result |
|---|---|
| Combined Python tooling/communication suite | **109 passed**, no skips; log reports 2.642 seconds |
| Upstream RandomX suite | **107 passed**, no skipped cases |
| Native same-process test suite | **6 passed**, no skips; log reports 155.035 seconds |
| Source/profile/build/previous smoke/full-dataset controls | All CI steps passed |
| Adapter native streams | Four runs / **36 intervals** revalidated locally |
| Known-reference controls | All **8** matched |
| Independent upstream comparisons | Both **17-nonce / 3-worker / software-AES** digests matched |
| Failure-path coverage | All **4** deliberately short measurement intervals rejected as expected |

The 109 count is from the actual combined log, not simply inferred by adding 64 and 45. Native controls remain correctness-only. The 36 interval records comprise eight controls, twelve warmups and sixteen measurement-phase records; phase names are not evidence of a controlled performance experiment.

[Artifact 11526993237](https://github.com/jliu67/OpenRandomX/actions/runs/37724306425/artifacts/11526993237) was downloaded as a **66,490-byte ZIP**. Its independently calculated SHA-256 matched GitHub's digest:

`2f6a7d63e8988b8c4405dbb1341dbc9ffe4cbb97a50d76908d00795dea5e0ad1`

All four adapter run reports identified integration commit `960b8b5`. Their raw stream/stderr checksums were recomputed; streams were revalidated with the unchanged wrapper and matched archived summaries. The two differential matches and all three test-suite summaries were read from the actual artifact. [integration-artifact-checks.json](integration-artifact-checks.json) records the ledger. GitHub reports expiration **2027-01-06T03:46:24Z**; retain additional raw files in reviewed Git history before relying on them beyond that date.

The local synthetic harness suite was also rerun: 22 tests passed in 3.762 seconds. This did not constitute a local native RandomX run. Native execution was in GitHub Actions. No throughput or power figure is promoted from these short controls.

Final handoff and release of the P1-05 editing claim are posted on issue #1 and hub #5. Current board/state/handoff files preserve the communication package and point to P1-06S as the next unblocked software task. **P1-05 is done; Phase 1/M1 remains open.**
