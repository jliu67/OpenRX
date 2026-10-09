# Local migration acceptance receipt — incomplete

Task: [#27](https://github.com/jliu67/OpenRX/issues/27). Date: 2026-10-09 UTC.
**Actual state: STAGING. Local execution policy NOT YET ACTIVE.**
This receipt is a live, non-complete migration record. No unverified gate is accepted.
**Current safety hold:** pipeline v2 stopped before preflight/guest execution; runner 916 overall future
execution acceptance withdrawn. Corrected runner `988cf13f…` + wrapper `5c275bf3…` are now independently accepted for local validation,
but require a fresh immutable reviewed-code checkout/request/pipeline binding before guest submission. Earlier evidence remains scoped history.

| Required acceptance gate | Current outcome | Evidence / required next evidence |
|---|---|---|
| Original scientific state preserved | PASS FOR AVAILABLE ORIGINAL STATE | [Independent preservation review](native-independent-review.json) rehashes all 694 original tracked files unchanged and all 10,933 pinned simulator source entries. Twelve exact pre-migration documentation snapshots and digest manifest are retained under `memory/handoffs/`. [Scientific inventory](scientific-audit.json) verifies 24/26/11 available historical evidence entries without mismatches; one historical cached `.pyc` is unavailable and explicitly recorded. |
| Required simulator dependencies verified | IN PROGRESS | Native Ubuntu 22.04 identified; [independent toolchain review](toolchain-independent-review.json) verifies 41 selected package archive SHA/metadata and installed versions. This is not a complete offline dependency closure; completed build/loader records pending. |
| Essential artifacts checksummed or reproducibly rebuilt | IN PROGRESS | Original saved gem5 package is unavailable through callable tools; new pinned build attempt 02 failed with actual 6-GiB cgroup OOM, preserved in [failure evidence](build-failure-02/README.md). Separate copied partial-build attempt 03 is running with one worker and a recorded 8-GiB RAM/2-GiB swap/100% CPU budget; no simulator transfer/build pass is claimed. Exact original runtime/hash guest ELFs recovered from tracked payloads and digest-reverified; firmware, kernel, compressed/expanded disk are now verified against exact pins in [resource integrity](guest-resources-integrity.json). [Independent resource/ELF review](resources-independent-review.json), [inventory](scientific-audit.json) and [distinct build config review](rebuild-config-review.json). Original identities remain in prior evidence. |
| Local simulator boots expected guest | NOT RUN | Requires completed verified local simulator/artifacts and durable runner. Earlier sandbox boot is historical evidence only. |
| Relevant correctness/regression smoke tests pass | PARTIAL — NATIVE PASS; GEM5 PENDING | Host native controls: original 257 Python tests, vendor 171 files, 106 upstream passes plus one explicit unsupported-AVX2 skip, 39 exact semantic/hash controls (one optional AES skip) and nine runtime controls pass; [Independent native review](native-independent-review.json) accepts the host controls; a full 277-test suite including the initial 20 runner tests also passed in [the retained log](all-tests-runner-final.log). [Independent final runner review](runner-independent-review.json) accepts `cd90f1d0…` with 22 focused tests and targeted v6 output tests; v4/full 277 tests are bound to prior `24717a7f…`, not the final source. Runner916 storage-flush review/23 tests remain narrow evidence; its overall future execution acceptance is withdrawn. [Signal-only f6ea review](runner-signal-safety-independent-review.json) passes25 focused tests. [Final combination review](final-runner-wrapper-independent-review.json) independently passes 287 complete tests (including 28 runner controls) and 40 targeted wrapper controls bound to988/5c; new immutable execution bindings and actual gem5 guest remain pending. [Native evidence](native-smoke/). Scientific criteria unchanged. |
| Long process survives Codex/launch-session termination | LAUNCH-SESSION INDEPENDENCE DEMONSTRATED | [Observed launcher absence/log progress/host-manager ancestry](runner-lifecycle/v4-session-independence-observation.json) and [concurrency/independence result](runner-lifecycle/v4-independence-concurrency-results.json) show host-managed operation after the submitting process ended. The complete ChatGPT session and host were not terminated/rebooted; this limit is explicit. [Independent durability review](runner-durability-independent-review.json) accepts the demonstrated architectural session-independence property and explicitly retains those limits. |
| Status and logs remain inspectable | HOST FIXTURES DEMONSTRATED | Ten retained per-execution manifests/logs/receipts and [the lifecycle evidence index](runner-lifecycle/evidence-index.json); local simulator inspection remains pending. |
| Safe stop, failure and recovery demonstrated | SAFETY HOLD — FINAL COMBINATION PENDING | [Lifecycle cases](runner-lifecycle/integration-results-v4.json) exercise process failure, safe stop with detached descendant, hard-killed worker and deliberate small-budget OOM; interruption and status evidence are preserved. [Independent review](runner-independent-review.json) accepts the preserved process-failure/recovery fixtures. A controlled [wrapper timing audit](wrapper-reap-safety-audit.json) confirms stale post-reap signaling in the old frozen source without signaling a host group; [Final corrected combination review](final-runner-wrapper-independent-review.json) accepts signal/reap ownership and actual finalizer extension evidence; fresh request/pipeline binding and actual guest remain pending. Actual host reboot and gem5 child stop/report have not been exercised on this host; malformed/torn durable records require manual additive reconciliation, never overwrite/replay. Scientific checkpoint resume is unavailable. |
| Output integrity checks pass | HOST FIXTURES INDEPENDENTLY VERIFIED | [All finalized fixture receipts verified](runner-lifecycle/v4-final-all-receipts-verified.json), with external append-only receipt bindings; [final independent source/output review](runner-independent-review.json) also verifies symlink/FIFO rejection without false acceptance. Reviewed `cd90f1d0…` output fixtures are separate from v4 lifecycle source. Runner916 explicitly fails receipt publication on storage-flush errors and that [narrow review](runner-durability-independent-review.json) is retained; its overall future execution acceptance is withdrawn. [Final review](final-runner-wrapper-independent-review.json) accepts 55.1219-second controlled delay, six real notifications and receipt integrity. [Original false harness and corrected audit](finalizer-extension-integration/audit-addendum.json) preserved; terminal manager status and actual large-output throughput are not claimed. Actual guest final outputs remain pending. |
| GitHub documents actual architecture | DRAFTED FOR REVIEW | LOCAL_EXECUTION/LOCAL_MIGRATION, board/instructions/memory drafted; initial inactive announcement published. |
| Agent handoffs/instructions internally consistent | DRAFTED FOR REVIEW | History snapshots retained; final gate/state/command reconciliation pending. |
| Reviewed migration PR merged | NOT YET | Dedicated migration branch and [PR #28](https://github.com/jliu67/OpenRX/pull/28); initial independent review is a partial review of staging work, with actual guest/final source acceptance and merge pending. |
| Final acceptance receipt completed | INCOMPLETE | This receipt must be finalized from objective linked evidence, limits and blockers. |

The original 936,569,944-byte archive and 957,300,488-byte simulator were saved/verified historically;
their availability on this host has not been demonstrated. A newly rebuilt simulator must retain separate
provenance and demonstrate required behavior. Source pin is gem5
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9` / v25.1.0.1.
The original light evidence manifest lists one unavailable cached Python bytecode file
`execution-source/tests/__pycache__/native_riscv_probe.cpython-312.pyc`; this is disclosed,
with its source and scientific raw evidence preserved. No scientific original has been fabricated or silently substituted.

Remote access is unavailable: requests and results require an owner-mediated GitHub/local workflow.
No listener, SSH access or autonomous job poller has been configured. The old owner-mediated runtime request/pipeline source review is retained, but pipeline v2 is stopped on the
published [safety hold](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085377771).
Both old request keys were never submitted. New corrected immutable source/request/pipeline revision03
and actual request execution/result retrieval remain pending binding review/build/loader/guest gates.
[Final code review](final-runner-wrapper-independent-review.json) accepts988/5c for local validation only.

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
