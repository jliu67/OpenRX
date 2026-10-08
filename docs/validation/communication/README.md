# Communication validation

Date: 2026-10-08 UTC / 2026-10-07 Edmonton. Scope: GitHub coordination only.

## Local evidence

Python 3.13.5. Command: `python3 -m unittest discover -s tests -v` in the isolated communication implementation workspace, containing only the new communication tests. **45 tests passed, no skips**. Full output: [local-tests.log](local-tests.log).

Coverage includes competing sessions (including shared GitHub accounts), ownership checks, heartbeat/expiry, release/block/review/done/reopen transitions, recipient parsing, edited/future commands, unauthorized writers, unmarked issue enrollment, stable history replay, pagination failure, unrelated-label preservation, spoofed summary markers, duplicate-run no-op behavior, closed issues, and PR exclusion.

These are synthetic protocol/API fixtures, not real worker executions or mining results. The existing 42 Phase 1 tests and native RandomX integration were not rerun locally in this isolated workspace. The unchanged repository CI will discover both suites after publication.

## GitHub integration

Live deployment and workflow validation are pending at initial implementation publication. Record the actual commit/run links and observed outcomes here after execution; do not infer success from the existence of a YAML file. Installation and handoff are tracked on issue #6. No model endpoint or autonomous worker has been configured.
