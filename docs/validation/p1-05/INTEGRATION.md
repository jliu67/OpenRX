# P1-05 / communication integration

Integration joins current main `9d1a8e3920d74a4dee75e66fe4df048876d11953` and P1-05 evidence commit `fee2a3bd74a8d4f3a5e7fdc592c33edc760cc89e` (implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`). Both parent histories must be retained. No force-push is permitted.

All P1-05 source/build/test/workflow blobs are reused unchanged from the passed branch run. All communication code, tests, router workflow, templates, protocol, AGENTS and validation are retained from main. Shared README/board/state/handoff documents were reconciled rather than selecting one side wholesale. Existing SESSION_LOG content is preserved as a prefix. Communication decisions D012-D014 keep their identifiers; new P1-05 decisions use D015-D017. Previous complete handoffs are archived byte-for-byte under memory/handoffs/; relocated historical relative links are not the current navigation entrypoint.

## Validation at integration publication

P1-05 component run 37722277487 passed 64 tooling tests, 107 upstream tests and six native tests; its downloaded raw artifact was validated as described in [README.md](README.md). Communication component validation is preserved in [../communication/README.md](../communication/README.md).

The integration will run the existing combined CI. Its outcome must be read from the actual integration commit/run; it is **not yet claimed as passed in this publication record**. Later results belong in an append-only update here and the issue handoff. Combining test counts is not a substitute for execution.

Neither component nor integration CI completes the controlled hardware/power experiment. M1 remains open. P1-06S importer software is ready but not implemented; physical host, meter and counter access remain unresolved.
