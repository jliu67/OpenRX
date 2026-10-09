# Local migration acceptance receipt — incomplete

Task: [#27](https://github.com/jliu67/OpenRX/issues/27). Date: 2026-10-09 UTC.
**Actual state: STAGING. Local execution policy NOT YET ACTIVE.**
This receipt is a live, non-complete migration record. No unverified gate is accepted.
The corrected immutable runner 988/wrapper 5c and readonly source
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726` now have reviewed request/pipeline v3 bindings.
The pipeline is waiting for build 03; actual build/loader/guest/stop/cutover gates remain pending.
Prior pipeline v2 is stopped and runner 916 overall acceptance remains withdrawn.

**Activation authority:** this dated receipt cannot activate execution. Only a verified `LOCAL_ACTIVE`
transition on [#27](https://github.com/jliu67/OpenRX/issues/27), bound to the actual reviewed merge commit
and final acceptance receipt, makes the designated policy effective. Otherwise defer full-scale work.
A final checked-in pre-cutover snapshot may remain `CUTOVER_PENDING`; the append-only merge-bound
acceptance and transition on #27 determine live availability.

| Required acceptance gate | Outcome at this snapshot | Evidence / remaining requirement |
|---|---|---|
| Original scientific state preserved | PASS FOR AVAILABLE ORIGINAL STATE | [Independent preservation review](native-independent-review.json): 694 original tracked files unchanged and 10,933 pinned simulator source entries verified; 12 exact documentation snapshots. Historical missing cached `.pyc` and original simulator unavailability are disclosed. |
| Required simulator dependencies verified | PARTIAL; BUILD/LOADER PENDING | [Toolchain review](toolchain-independent-review.json): 41 selected archive hashes/metadata and installed versions match. Full offline/hermetic closure is not claimed; completed build/loader records pending. |
| Essential artifacts checksummed or reproducibly rebuilt | PARTIAL; SIMULATOR PENDING | [Resource/ELF review](resources-independent-review.json) accepts exact original payloads and firmware/kernel/compressed/expanded disk. Original simulator inaccessible; [build02 OOM preserved](build-failure-02/README.md), separate build 03 running at 8-GiB RAM/2-GiB swap/100% CPU, one worker. [Config review](rebuild-config-review.json) retains separate rebuild provenance. |
| Local simulator boots expected guest | NOT RUN | Verified rebuilt simulator/loader and actual expected guest evidence still required. Historical sandbox boot is not local acceptance. |
| Relevant correctness/regression smoke pass | PARTIAL; GEM5 PENDING | [Native review](native-independent-review.json): vendor 171, upstream 106 plus valid AVX2 skip, strict 39 semantic/hash with optional AES skip, runtime 9 pass. [Final exact-source review](final-runner-wrapper-independent-review.json):287 full tests (28 runner) and 40 targeted wrapper controls pass; actual guest runtime 9 remains pending. |
| Long process survives Codex/launch-session termination | ARCHITECTURAL INDEPENDENCE ACCEPTED | Launcher absence, continued service logs and lingering host-manager ownership independently reviewed. Entire ChatGPT daemon termination and host reboot were not performed; [exact limits](final-runner-wrapper-independent-review.json). |
| Status and logs inspectable | HOST FIXTURES DEMONSTRATED | Retained manifests/events/logs/receipts and [lifecycle index](runner-lifecycle/evidence-index.json); actual simulator status/logs pending. |
| Safe stop, failure and recovery demonstrated | HOST FIXTURES ACCEPTED; ACTUAL GEM5 STOP PENDING | [Final control-flow review](final-runner-wrapper-independent-review.json), earlier snapshot-bound lifecycle fixtures and private finalizer extension accepted. [Stop controller](stop-controller-independent-review.json) is statically reviewed but unlaunched pending first verified capture; actual gem5 stop/report/empty-cgroup evidence required. No scientific checkpoint resume. |
| Output integrity checks pass | HOST FIXTURES VERIFIED; ACTUAL GUEST PENDING | Receipt/journal mutation and symlink/FIFO/flush-failure safeguards accepted. [55.1219-second finalizer proof](finalizer-extension-integration/audit-addendum.json) retains false harness/audit correction and verified receipt, with terminal manager status/large-output throughput unclaimed. Guest final-output verification pending. |
| GitHub documents actual architecture | STAGED / REVIEWED IN PART | Policy/runbook/board/memory and [exact-head review](https://github.com/jliu67/OpenRX/pull/28#pullrequestreview-5473259439) describe actual local-only architecture. Final gate/availability reconciliation pending. |
| Handoffs/instructions internally consistent | STAGED; FINAL RECONCILIATION PENDING | History and unavailable/withdrawn artifacts preserved; current b4b5ffc/runner 988/request 03/pipeline v3 bindings recorded. |
| Reviewed migration PR merged | NOT YET | [PR #28](https://github.com/jliu67/OpenRX/pull/28) reviewed at b4b5ffc for staging; actual guest/final evidence acceptance and merge pending. |
| Final acceptance receipt completed | INCOMPLETE | Final objective evidence/limitations plus actual reviewed merge and activation binding remain required. |

The current [owner runtime request](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085838632)
uses key `issue-27-local-runtime-b4b5ffc-attempt-01` and specification SHA-256
`d11d6f4e5043e3d51a73a0ecf52fc8aa95eb459c6546e46d4136f78013da7972`.
[Pipeline v3 review](pipeline-independent-review-v3.json) binds readonly b4b5ffc, immutable runner 988,
selected toolchain/input pins and driver `ace55beda…`. Its host service is waiting for build 03/preflight;
a request comment or active waiting service establishes no simulator/scientific pass.

Prior v4/full 277=24717, cd90/full 279/22-focused/v6,916/23-focused and f6ea/25-focused snapshots remain
separate provenance. Runner916 overall future execution acceptance was withdrawn after the signal hazard;
its narrow fsync evidence remains. [Original wrapper audit](wrapper-reap-safety-audit.json) intercepted the
unsafe group signal without signaling a real host group. Corrected988/5c final 287/28/40 evidence is distinct.
Old request keys 01/02 were never submitted and pipeline v2 stopped before preflight/guest execution.


The original 936,569,944-byte archive and 957,300,488-byte simulator were saved/verified historically;
their availability on this host has not been demonstrated. A newly rebuilt simulator must retain separate
provenance and demonstrate required behavior. Source pin is gem5
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9` / v25.1.0.1.
The original light evidence manifest lists one unavailable cached Python bytecode file
`execution-source/tests/__pycache__/native_riscv_probe.cpython-312.pyc`; this is disclosed,
with its source and scientific raw evidence preserved. No scientific original has been fabricated or silently substituted.

The separate [published stop request](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085930183)
remains unlaunched until its first-capture and source/input/cgroup prerequisites. Public controller/driver
source exports are path-sanitized reviewed derivatives; execution binds the retained host bytes.

Remote access is unavailable: requests/results require the owner-mediated GitHub/local workflow,
operated by the owner or an explicitly authorized local session with unchanged reviewed-request/gate criteria.
This authorized migration session does not require owner presence or create a remote access mechanism.
No listener, SSH access or autonomous job poller has been configured. The old owner-mediated runtime request/pipeline source review is retained, but pipeline v2 is stopped on the
published [safety hold](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085377771).
Both old request keys were never submitted. New immutable source/request/pipeline revision 03 bindings are
[independently reviewed](pipeline-independent-review-v3.json); actual request execution/result retrieval remains
pending build/loader/guest gates. [Final code review](final-runner-wrapper-independent-review.json) accepts 988/5c for local validation only.

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
