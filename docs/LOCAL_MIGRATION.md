# Loss-intolerant local infrastructure migration

Migration task: [#27](https://github.com/jliu67/OpenRX/issues/27).
Current state: **STAGING — NOT YET ACTIVE**; [published staging evidence](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6084197043).
The [initial hub announcement](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6084177837)
records the critical migration and inactive policy. The [acceptance receipt](validation/local-migration-20261009/ACCEPTANCE.md)
contains actual gate outcomes and blockers; the [execution policy](LOCAL_EXECUTION.md) defines agents' interface.

## State transitions and evidence

| State | Required evidence / permitted next action |
|---|---|
| `INVENTORY` | Record original repository/source/history, scientific artifacts/builds/results/checkpoints/configuration/log identities and host capability without changing the originals. |
| `STAGING` | Preserve original assets; populate fresh persistent paths; verify each transfer digest or explicitly record unavailable artifact and pinned rebuild recipe. Prepare runner/dependencies. |
| `LOCAL_VALIDATING` | Required inputs/dependencies are bound and checked; execute bounded guest/regression/lifecycle tests in new output directories. Full-scale research remains gated. |
| `CUTOVER_PENDING` | All technical acceptance gates have recorded passes; independent review, documentation consistency, merge and cutover announcement remain. |
| `LOCAL_ACTIVE` | All acceptance gates, reviewed merged PR, consistent authoritative documents and final receipt are verified; publish prominent effective-policy announcement. |
| `BLOCKED` | An exact missing external dependency/safety gate prevents advancement. Preserve previous working state and complete independent work. Return to the appropriate earlier state with evidence when resolved. |
| `ROLLBACK_REQUIRED` | A preservation/integrity/regression failure threatens correctness or loss. Stop new admission, preserve failed assets/logs and repair using verified previous inputs. |

Record each transition in the host's append-only migration journal
`$OPENRX_LOCAL_ROOT/migrations/20261009/state-events.jsonl`, the runner state ledger where applicable,
and #27 with evidence digests/locations. Keep the two ledgers and published receipt consistent;
the CLI records runner transitions with `state --state STATE --evidence FILE --reason REASON`.
A comment alone is not a state transition proof.
Never skip gates because a process booted, an agent reported success or a router label changed.
Do not alter scientific acceptance criteria or rewrite Git history.

## Artifact recovery and provenance

The original 2026-10-08 gem5 package was saved in two Library parts; its exact part/archive/binary digests and
save IDs remain in [REUSE.md](validation/m3-fs/REUSE.md) and
[the original package manifest](validation/m3-fs/reusable-package-20261008.json).
The currently callable tools have not exposed a download path for those saved binary parts.
**The original simulator binary is unavailable in this migration so far; its earlier successful save is not a verified local transfer.**
Keep its identity and investigate retrieval; do not mark it restored or silently replace it.

A separate persistent rebuild is being attempted from pinned gem5 v25.1.0.1,
commit `c8222cc67a399bfc01e8658dd14b30d5bfd634f9`, using recorded Ubuntu 22.04 dependencies.
Capture source archive/tree, configuration, compiler/linker/Python/SCons versions, package versions,
complete build logs, executable digest/size and loader/build-info checks. A changed binary digest is expected
for a new toolchain; demonstrate required behavior on this host before accepting that rebuilt artifact.
The new generated config is separately reviewed: SHA-256
`f839a59b33a593a63c3f5bef53bfac468df0619fcc46c3583c76b08b2d08564c`;
the only additions to the unchanged original config are detected optional PNG/HDF5/protobuf capabilities,
with no configured workload/model usage. [Configuration review](validation/local-migration-20261009/rebuild-config-review.json)
accepts this as a distinct rebuild config; it does not establish a simulator or scientific pass.
Preserve the old timeout/OOM/recovery history and original binary digest.
The local attempt 02 also failed with an actual 6-GiB cgroup OOM; its SCons partial build/source/logs
are retained. The waiting pipeline then failed because no final build-result file existed and started no guest.
[Failure evidence](validation/local-migration-20261009/build-failure-02/README.md) binds original and sanitized logs.
The [major failure hub bot copy](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6085149398)
is verified; full technical failure evidence remains on task #27/PR #28.
A separate copied partial-build attempt 03 started with one worker and a separately recorded
8-GiB RAM/2-GiB swap/100% CPU budget. This is a scoped migration-build override; normal runner service
limits remain 6-GiB RAM/1-GiB swap/200% CPU, with the same single-resource discipline. Do not infer incremental-copy effectiveness, build completion or scientific acceptance.

The exact already-audited runtime/hash ELFs were recovered from tracked base64 payloads and their
lengths/ELF metadata/SHA-256 independently reverified. Runtime SHA-256 is
`8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`;
hash ELF is `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`.
This is artifact recovery, not a new runtime/hash pass. See [scientific inventory](validation/local-migration-20261009/scientific-audit.json).
If either original payload later becomes unavailable, perform a documented pinned rebuild as a separate input.
Verify firmware/kernel/disk against
`simulator/gem5/resources.json` and retain preparation/download manifests. No transfer passes without integrity verification.
Keep large binaries, datasets and generated archives outside Git. Public evidence contains portable paths and sanitized metadata.
A redacted export is a reviewed derivative with its own digest; embedded original receipt/event hashes
continue to identify host originals and must not be claimed as hashes of the sanitized bytes.
Verify untouched host records against the host journal and separately bind each public derivative to the
exact redaction method/export digest. Do not feed redacted records to the host integrity checker as originals.

## Ordered migration gates

1. Inventory and hash original scientific state, including the original checkout and tracked prior evidence.
   Preserve exact previous current-state/handoff documents in `memory/handoffs/pre-local-migration-*`.
2. Confirm the designated native Ubuntu host, disk/RAM/CPU capabilities, persistent path ownership,
   user systemd manager/lingering, toolchain pinning and resource budget. Record actual package versions.
3. Verify transferred/recovered inputs or completed pinned rebuilds. Confirm source/configuration bindings
   and simulator loader/build-info before guest execution.
4. Verify the host runner using inexpensive fixtures: duplicate-key rejection, resource serialization,
   status/log retention, integrity checks, safe stop, failure/recovery and process survival after the launching session ends.
   Test the relevant user-manager failure/reboot behavior without deleting existing assets.
5. Run expected pinned guest boot and nine exact Linux runtime controls with a fresh execution ID/output directory.
   Run relevant native/QEMU correctness and repository regressions against unchanged vendored workload.
   Retain exact commands, tool versions, logs, inputs and skipped controls. A boot is not a correctness pass.
6. Independently review preservation, runner lifecycle and scientific smoke evidence. Reconcile AGENTS,
   README, board, memory/handoff, roadmap and this runbook to actual architecture/state.
7. Merge the separately reviewed migration PR, complete the final acceptance receipt and verified state transition,
   then publish the prominent effective-policy announcement on hub #5 and task #27.

The complete gem5 unchanged light matrix, full dataset, intended-core/SMP and selected BOOM Linux gates remain
in #16/M3. Migration runtime smoke acceptance does not close those scientific gates or M1/M4/M5.
The independently reviewed local driver `validate_when_ready_v2.py` is running as the host-managed
`openrx-migration-validation-pipeline-v2-20261009.service`, waiting for attempt03. Its fixed request is
`issue-27-local-runtime-6f54052-attempt-02`; [pipeline review](validation/local-migration-20261009/pipeline-independent-review-v2.json)
binds driver `dab2f21e…`, runner `916b6b0d…` and specification `b0117492…`.
It must verify build/loader/toolchain/inputs and publish evidence-backed `LOCAL_VALIDATING` before
submitting runtime-only smoke. It is a finite owner-authorized local driver, not a remote listener or issue poller.
No simulator has run at this staging snapshot. No expensive research run is authorized before technical gates and cutover.

## Stop, failure and recovery procedures

Use `status EXECUTION_ID` and retained logs to establish what is actually running.
Use `stop EXECUTION_ID`; then confirm service/child termination and retained status/receipt.
For gem5, require its own stop handling/report where available and record missing child/report evidence explicitly.
Do not infer graceful termination from a vanished PID, shell control-C or Codex disconnection.
A stop does not establish a scientific failure, completed matrix or resumable checkpoint.

After service failure, host reboot or power loss, inspect the execution manifest, service status, event stream,
stdout/stderr and process result. Run `recover EXECUTION_ID` to reconcile the recorded state;
run `verify EXECUTION_ID` on finalized evidence. Preserve incomplete outputs and label them partial.
Never clear request mappings or lock files to force a retry. OS-released flock locks can be reused only after
status proves the old service and children are absent. Begin a fresh attempt with a new ID/key after inspection.

If integrity fails, stop new admission and record `ROLLBACK_REQUIRED` with exact failing digests/files.
Keep both originals and staged/rebuilt assets. Restore operation only from verified existing copies
or a separately reproducible rebuild; unavailable originals remain recorded as unavailable.
Rollback means hold/revert the execution-policy cutover and preserve data, not resume expensive sandbox execution.
### Torn-file and journal recovery limit

Power loss can leave an exclusively created manifest/result/receipt incomplete, or an event line torn.
Such malformed records, a broken digest/event chain, output symlinks or nonregular artifacts fail closed:
submission/verification/finalization must not invent a valid receipt or rerun the scientific command.
The runner fsyncs finalized records/directories, but storage/power-loss durability is not a complete
transactional journal guarantee. A host reboot or physical power-loss test has not been performed.

Preserve every affected file byte-for-byte. Make a new forensic copy and record its digest, observed service/
cgroup state, parsing/integrity error and last intact event in a separate incident record.
Hold new admission and record `BLOCKED` with evidence using an intact state ledger; if that ledger is broken,
its own CLI must refuse mutation, and the GitHub task/incident explicitly records the blocked condition.
Do not truncate a torn tail, overwrite a malformed file, erase request mappings or construct a success receipt.
Manual, independently reviewed reconciliation is required before execution can resume, with an additive
recovery record preserving prior ledger bytes and duplicate-prevention bindings. No automatic replay or
scientific checkpoint recovery is implemented.

Before activation, external blockers leave state non-complete; after activation, an offline host leaves
execution requests queued/blocked and agents continue lightweight work.
