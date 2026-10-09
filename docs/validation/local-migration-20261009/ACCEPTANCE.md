# Local migration acceptance receipt — incomplete

Task: [#27](https://github.com/jliu67/OpenRX/issues/27). Date: 2026-10-09 UTC.
**Actual state: STAGING. Local execution policy NOT YET ACTIVE.**
This receipt is a live, non-complete migration record. No unverified gate is accepted.

| Required acceptance gate | Current outcome | Evidence / required next evidence |
|---|---|---|
| Original scientific state preserved | PASS FOR AVAILABLE ORIGINAL STATE | [Independent preservation review](native-independent-review.json) rehashes all 694 original tracked files unchanged and all 10,933 pinned simulator source entries. Twelve exact pre-migration documentation snapshots and digest manifest are retained under `memory/handoffs/`. [Scientific inventory](scientific-audit.json) verifies 24/26/11 available historical evidence entries without mismatches; one historical cached `.pyc` is unavailable and explicitly recorded. |
| Required simulator dependencies verified | IN PROGRESS | Native Ubuntu 22.04 identified; pinned dependency/build and loader records pending. |
| Essential artifacts checksummed or reproducibly rebuilt | IN PROGRESS | Original saved gem5 package is unavailable through callable tools; pinned rebuild in progress. Exact original runtime/hash guest ELFs recovered from tracked payloads and digest-reverified; firmware, kernel, compressed/expanded disk are now verified against exact pins in [resource integrity](guest-resources-integrity.json). [Inventory](scientific-audit.json) and [distinct build config review](rebuild-config-review.json). Original identities remain in prior evidence. |
| Local simulator boots expected guest | NOT RUN | Requires completed verified local simulator/artifacts and durable runner. Earlier sandbox boot is historical evidence only. |
| Relevant correctness/regression smoke tests pass | PARTIAL — NATIVE PASS; GEM5 PENDING | Host native controls: original 257 Python tests, vendor 171 files, 106 upstream passes plus one explicit unsupported-AVX2 skip, 39 exact semantic/hash controls (one optional AES skip) and nine runtime controls pass; [Independent native review](native-independent-review.json) accepts the host controls; a full 277-test suite including the initial 20 runner tests also passed in [the retained log](all-tests-runner-final.log). New gem5 guest and final runner-source reconciliation remain pending. [Native evidence](native-smoke/). Scientific criteria unchanged. |
| Long process survives Codex/launch-session termination | LAUNCH-SESSION INDEPENDENCE DEMONSTRATED | [Observed launcher absence/log progress/host-manager ancestry](runner-lifecycle/v4-session-independence-observation.json) and [concurrency/independence result](runner-lifecycle/v4-independence-concurrency-results.json) show host-managed operation after the submitting process ended. The complete ChatGPT session and host were not terminated/rebooted; this limit is explicit. Final independent gate acceptance pending. |
| Status and logs remain inspectable | HOST FIXTURES DEMONSTRATED | Ten retained per-execution manifests/logs/receipts and [the lifecycle evidence index](runner-lifecycle/evidence-index.json); local simulator inspection remains pending. |
| Safe stop, failure and recovery demonstrated | HOST FIXTURES DEMONSTRATED | [Lifecycle cases](runner-lifecycle/integration-results-v4.json) exercise process failure, safe stop with detached descendant, hard-killed worker and deliberate small-budget OOM; interruption and status evidence are preserved. Actual host reboot and gem5 child stop/report have not been exercised on this host. Scientific checkpoint resume is unavailable. |
| Output integrity checks pass | HOST FIXTURES VERIFIED; FINAL REVIEW PENDING | [All finalized fixture receipts verified](runner-lifecycle/v4-final-all-receipts-verified.json), with external append-only receipt bindings; input/output mutation controls and final source review pending reconciliation. Actual guest final outputs remain pending. |
| GitHub documents actual architecture | DRAFTED FOR REVIEW | LOCAL_EXECUTION/LOCAL_MIGRATION, board/instructions/memory drafted; initial inactive announcement published. |
| Agent handoffs/instructions internally consistent | DRAFTED FOR REVIEW | History snapshots retained; final gate/state/command reconciliation pending. |
| Reviewed migration PR merged | NOT YET | Dedicated migration branch; separate review and merge pending. |
| Final acceptance receipt completed | INCOMPLETE | This receipt must be finalized from objective linked evidence, limits and blockers. |

The original 936,569,944-byte archive and 957,300,488-byte simulator were saved/verified historically;
their availability on this host has not been demonstrated. A newly rebuilt simulator must retain separate
provenance and demonstrate required behavior. Source pin is gem5
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9` / v25.1.0.1.
The original light evidence manifest lists one unavailable cached Python bytecode file
`execution-source/tests/__pycache__/native_riscv_probe.cpython-312.pyc`; this is disclosed,
with its source and scientific raw evidence preserved. No scientific original has been fabricated or silently substituted.

Remote access is unavailable: requests and results require an owner-mediated GitHub/local workflow.
No listener, SSH access or autonomous job poller has been configured. End-to-end owner request/retrieval remains untested.

#16 remains open for the complete unchanged gem5 light matrix and later full-dataset/intended-core gates.
M0 is complete; M1–M5 remain open. No new hardware timing, physical energy or RTL acceptance is implied.

Public lifecycle manifests/events/receipts are path-sanitized, independently reviewed derivatives.
Their embedded artifact and event-chain hashes identify the untouched host bytes; they do not assert that
redacted public files have the same digests or remain replayable by `local_execution.py verify`.
Integrity acceptance uses retained host originals and the append-only external receipt journal.
The export index/review records each public-file digest and exact redaction; native result oracles are unchanged.

Host-only command/asset records reside under `$OPENRX_LOCAL_ROOT/migrations/20261009/` and
`$OPENRX_LOCAL_ROOT/executions/ID/`; public evidence will link sanitized manifests and test reports here.
Inspect/resume commands are in [the execution policy](../../LOCAL_EXECUTION.md) and
[the runbook](../../LOCAL_MIGRATION.md). No scientific checkpoint resume is certified.
