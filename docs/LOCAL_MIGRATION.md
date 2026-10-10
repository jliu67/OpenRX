# Loss-intolerant local infrastructure migration

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

The distinct pinned build 03 completed at 19:37:51Z with unchanged source/configuration and verified loader.
Runtime-only execution `20261009T193937Z-576aa858c033` completed; independent review accepted the expected
Ubuntu 24.04 / Linux 6.8.12 boot and all nine unchanged runtime controls at 20:04:52Z. The guest status was
zero, framed probe stderr was empty, and the completion marker and ordered hypercalls 1/2/3 were present.
Source, inputs, model and output integrity were independently verified. The model uses one 1-GHz
AtomicSimpleCPU, RVV disabled, 4 GiB RAM, 16-KiB L1I/L1D and 256-KiB L2, with a read-only base disk and
copy-on-write wrapper. This establishes functional controls, without a timing or performance inference.
Initial stop execution `20261009T200904Z-854b672fc611` proved initialization termination only, with empty
serial/no generated config. It is preserved and does not satisfy the broader operational stop gate.
Broader stop outcome at this snapshot: INDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim).
Reviewed broader stop execution: 20261009T202537Z-a1ca7df2cf1c; evidence: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`.
Runtime task publication: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6088623385`; technical transition publication:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095767946`. These publications were verified by exact GitHub readback.

[Actual runtime evidence](validation/local-migration-20261009/actual-runtime-v1/index.json) and
[independent review](validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json)
record expected guest/runtime9 and source/input/model/output acceptance.

[Actual firmware-seen stop index](validation/local-migration-20261009/actual-gem5-running-stop-v3/index.json) binds44 selected public exports and both independent reviews.
The initial empty-serial stop remains initialization-only. The later intentional stop is accepted for
owned-process termination, inspectable failure/status, retained outputs and integrity, without a
scientific pass or Linux boot for that stop attempt.

The [owner resource directive](LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
with swap where useful, retaining only measured necessary OS/agent headroom. Per-job allocations must
reflect current host load, memory availability and workload parallelism; 14 GiB is a candidate, not a
universal safe limit. Keep one payload slot and all migration/scientific gates. The old runner988 validation records retain their actual memory and manager-reported 200% CPUQuota.
A later CPU-delegation audit found that historical quota was not kernel-enforced; old property receipts
are preserved and do not prove CPU enforcement. The new CPU delegation configuration is additive.
CPU-delegation evidence: `independently reviewed CPU delegation f12aec1f/67de0d92 and actual runner kernel witness, docs/validation/local-migration-20261009/resource-kernel-20261010/index.json`. The approved owner-local-max-v1 candidate
uses CPU600%, memory no greater than min(14 GiB, fresh MemAvailable minus 1 GiB), optional lower positive
explicit budget, 2-GiB swap, Tasks256 and the same one-slot/45-second stop semantics. Admission must bind
current host metrics and recheck available headroom before launching. Exact new-release/kernel-budget
verification is recorded by the operational profile evidence; it is independently accepted for the exact installed release and tiny live proof below.

The operational implementation must check each payload's actual kernel CPU, memory, swap and task
limits, including effective ancestor ceilings, under admission/resource safeguards before launch. It must
fail closed on unavailable controllers, mismatched constraints, tighter inherited ceilings or lost fresh
memory headroom. Manager properties and controller availability alone do not establish enforcement.
The exact installed operational release enforces these per-payload kernel checks; the independent
resource proof below accepts the observed normal profile. Each future payload is checked again.

Operational resource-profile outcome/evidence: `INDEPENDENTLY ACCEPTED exact runner657 and normal-profile tiny execution20261010T083746Z-6bc7037f04ef: actual CPU600000/100000, RAM5637144576 bytes (5.25GiB selected from measured headroom), swap2147483648, tasks256, six-CPU affinity, no tighter visible ancestors; rc0 and receipt integrity verified. Independent review951622749d40a9bf467e48ee3f6581cc52393569b8db60c87e63d57bee8ee00b; resource-kernel-20261010/index.json`.
Operational release: `runner-v1-657b23f1`, SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`. The verified profile and immutable release are reconciled. This dated preactivation snapshot
retains the expensive-work hold until the explicit merge-bound release.

This infrastructure acceptance leaves #16's complete unchanged gem5 RandomX matrix/full dataset/
intended-core/SMP/BOOM and M1-M5 open. No calibrated timing, physical power, RTL, checkpoint resume,
whole-Codex-daemon termination, host reboot or complete offline/hermetic dependency closure is claimed.
Original Library binary remains unavailable; rebuilt binary retains its distinct identity. Preserve
failures/safety withdrawals, original scientific assets, exact guest oracles and milestone history.

## State transitions and evidence

| State | Required evidence / permitted next action |
|---|---|
| `INVENTORY` | Record original repository/source/history, scientific artifacts/builds/results/checkpoints/configuration/log identities and host capability without changing the originals. |
| `STAGING` | Preserve original assets; populate fresh persistent paths; verify each transfer digest or explicitly record unavailable artifact and pinned rebuild recipe. Prepare runner/dependencies. |
| `LOCAL_VALIDATING` | Required inputs/dependencies are bound and checked; execute bounded guest/regression/lifecycle tests in new output directories. Full-scale research remains gated. |
| `CUTOVER_PENDING` | All technical acceptance gates have recorded passes; independent review, documentation consistency, merge and cutover announcement remain. |
| `LOCAL_ACTIVE` | All eligibility gates, reviewed merged PR and consistent authoritative documents are verified. Hold expensive submissions until #27 verifies explicit release bound to acceptance/event/merge/document audit; then publish effective-policy hub notice, verify bot and complete final synchronized acceptance. |
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

A distinct persistent rebuild completed from pinned gem5 v25.1.0.1,
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
validation limits were 6-GiB RAM/1-GiB swap/200% CPU. The new owner directive requires measured operational allocation rather than automatic reuse of those limits, while retaining the same single-resource discipline.
Attempt03 completed at 2026-10-09T19:37:51.079045Z with returncode0, `source_changed:[]`, unchanged
configf839a59b…, build-info exit0 and loader exit0. Build-result raw SHA-256 is
`8eef5987f056d1090d85ece94ee120da5ac35c8828a92b406d119c98730a9c3f`.
The new binary is 1,036,720,416 bytes, SHA-256
`e4129f16377346f02b7d68cd508644e5a77cc2daec84a303cc788cb301c05902`.
This is a verified new build record, not restored original bytes or a scientific pass.
Actual preflight at 19:38:51.228039Z bound sourceb4b5ffc, runner988, request03, 41 package pins,
exact guest resources/runtime and runtime-library profilefda84e15…; preflight raw SHA-256 is
`d2043b278dbb1fabf69b220989414cb8c850ea8a5e56dcfa675dbab44ca31626`.
At that preflight snapshot, guest correctness and operational stop were still pending. Subsequent
strict guest acceptance is linked above; the broader stop outcome must match its separate reviewed evidence.
The [completed build/preflight export index](validation/local-migration-20261009/local-validating-live-v1/index.json)
binds15 actual metadata/source files using exactly two ordered prefix substitutions.
[Independent postbuild integrity review](validation/local-migration-20261009/local-validating-live-v1/independent-build-preflight-postbuild-review.json)
freshly rehashed the new binary, original694 scientific files/10,933 simulator source entries,41 packages,
43 runtime-library bindings and exact guest assets. It revalidates actual source/state/request integrity,
not guest correctness, safe stop or cutover. Bounded manager/socket observations retain their stated limits.

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
7. Merge the separately reviewed migration PR and independently audit the actual merged documents/source.
   Complete immutable eligibility evidence/certificate, review it separately, and verify the actual LOCAL_ACTIVE
   transition. Hold expensive submissions until #27 publishes a verified explicit release binding certificate,
   event, actual merge and merged-document audit. Publish the effective-policy hub notice after release, verify
   its bot copy, then complete the final synchronized acceptance/report. No future/self-referential proof is inferred.

The complete gem5 unchanged light matrix, full dataset, intended-core/SMP and selected BOOM Linux gates remain
in #16/M3. Migration runtime smoke acceptance does not close those scientific gates or M1/M4/M5.
The previously reviewed fixed pipeline v2 is **stopped before preflight or guest execution**.
[Safety hold](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085377771) and
[review correction](https://github.com/jliu67/OpenRX/pull/28#pullrequestreview-5473038322) withdraw runner 916
overall future execution acceptance after a post-reap numerical PID/process-group signal risk; its narrow
fsync evidence remains retained. A [controlled wrapper audit](validation/local-migration-20261009/wrapper-reap-safety-audit.json)
also confirms the race in the untouched frozen execution wrapper, with all signals intercepted.

Corrected runner `988cf13f…` and wrapper `5c275bf3…` are now independently accepted for a new immutable
local validation release; [final review](validation/local-migration-20261009/final-runner-wrapper-independent-review.json)
records exact source bindings. The generic runner's reviewed
f6ea signal fix (25 focused controls) and tiny [systemd-notify component fixtures](validation/local-migration-20261009/systemd-notify-component/)
are separate earlier evidence. Final accepted source passes 287 complete repository tests, including 28 runner
controls, plus 40 targeted wrapper controls. A 55.1219-second controlled finalizer delay with six actual
notifications and receipt integrity proves extension beyond 45 seconds. The original false test harness
result and [audit addendum](validation/local-migration-20261009/finalizer-extension-integration/audit-addendum.json)
are preserved with [the export index](validation/local-migration-20261009/finalizer-extension-integration/export-index.json); terminal manager properties were not captured, and no actual
large-artifact throughput or guest correctness is inferred.
The worker stop budget remains 45 seconds; only its private `Type=simple` / `NotifyAccess=exec` finalizer
may extend its deadline while flushing/checksumming large outputs.

Preserve original/frozen source and old request keys 01/02 (never submitted). The replacement readonly
execution checkout is now pinned to `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`; runner 988/wrapper 5c,
request revision 03 and pipeline v3 have [independently verified exact bindings](validation/local-migration-20261009/pipeline-independent-review-v3.json).
[Runtime request](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085838632) key
`issue-27-local-runtime-b4b5ffc-attempt-01` has SHA-256
`d11d6f4e5043e3d51a73a0ecf52fc8aa95eb459c6546e46d4136f78013da7972`.
Driver `ace55beda…` was launched as `openrx-migration-validation-pipeline-v3-20261009.service` and submitted
runtime-only execution `20261009T193937Z-576aa858c033` after completed build/loader/toolchain/input
preflight and actual LOCAL_VALIDATING. The completed expected guest/runtime9 and final output integrity are independently accepted.
Broader stop outcome: INDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim); actual evidence:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`. Initial200904 initialization-only stop stays preserved.
No expensive research is authorized before the independently verified explicit release.
The branch also guards hosted full gem5 build/full-system and full-dataset/native steady steps with literal
skips while retaining commands/criteria. They are deferred to reviewed local requests, not counted as passes.
The guards are not effective on main until reviewed merge; no self-hosted Actions execution channel exists.

A separate [fixed stop-proof controller](validation/local-migration-20261009/stop-controller-independent-review.json)
was reviewed before execution. Its first actual attempt proved initialization-only termination.
Broader post-OpenSBI stop evidence: INDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim); do not broaden the initial scope.
Controller SHA-256 is `1d65cc6e275f09ee4da3049f6a5a4ec62a364945314121216c269a22a003c817`;
[Published request](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085930183)
key is `issue-27-gem5-stop-migration-attempt-01`, specification SHA-256
`76218e477bd84c36cb5991c06685af16718a589ab8a0c45eaaec25b643607f14`.
It observes the exact gem5 executable in its owned cgroup through a live pidfd, creates a fresh fsynced
stop marker, and requires report/receipt/empty-cgroup evidence. That initial attempt is accepted only
for initialization termination; the broader stop gate requires its separate reviewed evidence above.
If the controller is interrupted, reentry may observe its existing same-key execution but cannot duplicate
or restart it; missing original stop-marker timing cannot be accepted as a new proof. Scientific checkpoint
resume and graceful gem5 statistics/checkpoint finalization remain unavailable.

## Stop, failure and recovery procedures

Select the immutable release from the host installation receipt:

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
export OPENRX_RUNNER="$OPENRX_LOCAL_ROOT/releases/runner-v1-657b23f1/local_execution.py"
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status EXECUTION_ID
```

Use that installed runner's `status EXECUTION_ID` and retained logs to establish what is actually running.
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

## Final acyclic cutover evidence order

Freeze D_head (premerge reviewed head); actual merge/readback M may cite it. Write distinct D_merged
after M, binding M+D_head and accepted functional source. Capture preactivation authority audit A_pre,
complete narrative F with migration_complete:false, and independent completeness audit Q before
certificate C. C's13 true gates certify actual eligibility, not future publication; C remains
migration_complete:false. Independent exact-C review R stays outside C. Use independently preflighted
regular/no-symlink/immutable/fsynced evidence and complete stable journal-prefix snapshots; never hash
live changing ledgers or make a receipt hash its own reviewer/publication. Installed validator checks
Booleans/local hashes/merge syntax only; actual semantic/GitHub review remains mandatory.

After real CUTOVER_PENDING, verify E/LOCAL_ACTIVE exact approved-C binding/from_state/predecessor and
unchanged source/evidence, then independent V. Hold expensive work until actual #27 release L binds
E+C+actual M+D_merged+reviews and is read back. Publish the effective-policy hub notice afterward,
verify its bot copy, then pre-Z completeness/synchronization audit W. Write final report Z only after
those facts exist; exact-Z reviewer R_Z binds Z externally in publication/readback sidecars P_Z, never
back inside Z. Protocol review/bot precedes done; `/openrx done` has no session argument and follows
actual final independent acceptance/readback. No platform approval is fabricated or protection bypassed.
Raw host paths/bytes remain private; safe original/public digests are published in reviewed indices.
Final proof lives at real reachable #27 comments/authorized artifacts or a separately reviewed evidence
PR, never dangling future-file links. Later offline/BLOCKED/ROLLBACK evidence holds new admission.
