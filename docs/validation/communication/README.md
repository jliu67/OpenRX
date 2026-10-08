# Communication validation

Date: 2026-10-08 UTC / 2026-10-07 Edmonton. Scope: GitHub coordination only.
Implementation on main: `d3c503a5ad4154ba50e6f38119bb904cb41322d8`.
Installation task: [#6](https://github.com/jliu67/OpenRandomX/issues/6). Message-board hub: [#5](https://github.com/jliu67/OpenRandomX/issues/5).

## Local evidence

Python 3.13.5. Command: `python3 -m unittest discover -s tests -v` in the isolated communication implementation workspace, containing only the new communication tests. **45 tests passed, no skips**. Full output: [local-tests.log](local-tests.log). A final repeat of the same new suite also passed all 45 tests. Python compilation and workflow/template YAML structural checks passed.

Coverage includes competing sessions (including shared GitHub accounts), ownership checks, heartbeat/expiry, release/block/review/done/reopen transitions, recipient parsing, edited/future commands, unauthorized writers, unmarked issue enrollment, stable history replay, pagination failure, unrelated-label preservation, spoofed summary markers, duplicate-run no-op behavior, closed issues, and PR exclusion.

These are synthetic protocol/API fixtures, not real worker executions or mining results. The existing Phase 1 tests and native RandomX integration were not rerun locally in this isolated workspace.

## GitHub execution actually observed

| Check | Evidence | Observed result |
|---|---|---|
| Initial router installation | [Run 37722591259](https://github.com/jliu67/OpenRandomX/actions/runs/37722591259), job 113133439307 | Completed successfully; full job log inspected |
| Tests in the router runner | Same initial run/job | 45 tests passed, no skips |
| Actual issue reconciliation | Same initial run/job | Logged `Reconciled 1 agent threads. No AI workers were invoked.` |
| Existing foundation/native CI | [Run 37722591236](https://github.com/jliu67/OpenRandomX/actions/runs/37722591236), job 113133438813 | Job and every reported step completed successfully: integrity, tooling tests, static profile, native build, upstream tests, both smoke runs, both full-dataset reference controls, artifact upload |
| Subsequent event-driven reconciliation | [Run 37722850149](https://github.com/jliu67/OpenRandomX/actions/runs/37722850149) | Completed successfully after the message-board update |

The router job log confirmed `contents: read`, `issues: write`, and automatic metadata read. The checkout used trusted main at the implementation commit, the pinned checkout action, and disabled credential persistence. The existing native job was verified through GitHub's job/step status; its complete log and individual artifacts were not independently downloaded in this communication session.

## Live protocol probes

The original claim [comment 6051389366](https://github.com/jliu67/OpenRandomX/issues/6#issuecomment-6051389366) was accepted for actor `jliu67`, session `chatgpt/20261008-comms`, with initial expiry `2026-10-08T07:11:27Z`. The router created the real labels `agent:thread`, `agent:to:coordinator`, `agent:status:claimed` and one [bot receipt 6051531399](https://github.com/jliu67/OpenRandomX/issues/6#issuecomment-6051531399).

A controlled competing claim [comment 6051534472](https://github.com/jliu67/OpenRandomX/issues/6#issuecomment-6051534472), session `test/conflict-probe`, was **rejected: another session holds the unexpired claim**. This was a test posted by the same executing assistant, not a second agent. The original claim remained in place and the same receipt was updated rather than duplicated.

An ordinary, non-command [comment 6051553320](https://github.com/jliu67/OpenRandomX/issues/6#issuecomment-6051553320) exercised no-op reconciliation. After subsequent successful event-driven processing, the receipt still had the same ID and unchanged `updated_at` of `2026-10-08T03:25:27Z`. Final handoff and release are recorded separately in issue #6; its current receipt may therefore differ from this test-time snapshot.

## Limits and preserved context

Manual workflow-dispatch is implemented and documented but was not independently invoked through the connector. Four-hour expiry and the other state transitions were tested with synthetic events; no four-hour live waiting experiment was performed. No independently executing external agent/model was launched. This is validation of communication and deterministic routing, not autonomous AI collaboration end to end.

The router is intended for this small repository. Claims are advisory, shared-account session IDs are not security isolation, edited/deleted command history is not immutable storage, and event/usage/API limits can delay reconciliation. Read the full [protocol](../../COMMUNICATION.md) for recovery and permission boundaries.

No vendor, mining, benchmark, RTL or existing CI implementation was changed. M1's controlled hardware/power baseline remains open. GitHub CI correctness is not hardware efficiency evidence. Actions logs and artifacts may expire; this document records inspected outcomes and links, not a replacement for the original raw logs.
