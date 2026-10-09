# Local source build attempt 02 — preserved failure

**STAGING; local execution policy remains inactive.**
The host-managed pinned gem5 rebuild failed with the unit's actual `Result=oom-kill`
at `MemoryMax=6442450944` (6 GiB). SCons retained partial build state and its complete failure log.
No complete `build-result.json` was produced, so the waiting validation pipeline failed with
`FileNotFoundError` before simulator/guest validation. No boot or scientific pass follows.

[Failure receipt](failure-receipt.json), [build unit status](build-unit-status.txt),
[build command](build-command.json), [complete build log](build.log),
[pipeline status](pipeline-unit-status.txt) and [pipeline log](pipeline.log) retain the exact observations.
Source pin/configuration and failed tree are preserved. A separate copied partial-build attempt 03
uses one worker and a separately recorded memory budget; its outcome is not claimed here.
A build failure is an actionable staging failure, not migration completion or a fabricated recovered artifact.

Public paths are sanitized; the receipt binds both original-host and exported bytes.
Original logs and partial files remain on the host under the recorded portable installation root.
