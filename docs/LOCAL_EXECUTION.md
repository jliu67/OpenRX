# Local execution policy and interface

**Snapshot updated 2026-10-09T19:57:09.253251Z; state LOCAL_VALIDATING since 2026-10-09T19:38:51Z. The policy is NOT YET ACTIVE.**
[Task #27](https://github.com/jliu67/OpenRX/issues/27) and the
[acceptance receipt](validation/local-migration-20261009/ACCEPTANCE.md) record the evidence and open gates.
The owner's native Ubuntu computer is being prepared as the persistent execution host.
No agent may infer activation from a message, successful install, boot, process launch or status label.
Activation requires all migration gates, a separate review, a merged migration PR and consistent GitHub documentation.

**Execution authorization:** expensive execution becomes effective only when [task #27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified acceptance, its matching `LOCAL_ACTIVE` transition and an explicit release
bound to the actual reviewed merge and merged-document audit. Local active state alone does not release work.
Until that release is verified, defer full-scale work. Dated repository snapshots preserve history;
they never activate execution. Consult the live proof and local status for current availability.

Once the verified #27 release exists, this computer is the designated host for gem5 full-system runs,
long CPU architecture experiments, large RandomX workloads, expensive profiling/toolchain builds and large generated artifacts.
Temporary agent sandboxes remain available for code/review, documentation, static analysis, lightweight tests,
experimental design and small inexpensive reproductions. During migration, defer full-scale experiments;
only the declared bounded migration validation workloads may run on the local host after their prerequisite gates pass.
The independent scientific gates in #16 and M1–M5 retain their original criteria.

## What a visiting agent must know

| Question | Current answer |
|---|---|
| Where do expensive runs execute? | The owner's Ubuntu host after matching acceptance/LOCAL_ACTIVE and verified explicit #27 release; the host is currently LOCAL_VALIDATING and full-scale work is held. |
| Is the runner available? | Immutable runner `988cf13f…`, readonly `b4b5ffc…` source and fixed runtime request/pipeline v3 have reviewed bindings. Build03/loader/input preflight completed; runtime-only execution `20261009T193937Z-576aa858c033` has started. Guest correctness, actual stop/final outputs and cutover are unverified. Prior runner916 acceptance stays withdrawn and pipelinev2 stopped. Check #27/latest local status before use. |
| How is a request submitted? | A GitHub task issue with the complete execution specification below; the owner or an explicitly authorized local session reviews and submits it locally. |
| Can a remote agent execute directly? | **No. Remote execution and retrieval are unavailable.** There is no SSH access, network listener or autonomous issue poller provisioned by this migration. |
| How are collisions prevented? | The local runner serializes admission, binds a request key to one execution ID and uses one host resource lock. GitHub claims coordinate source work and are not CPU locks. |
| Where is evidence? | Persistent per-execution manifests/logs/receipts on the host; reviewed, sanitized manifests/summaries and small evidence are attached or linked from the task/PR. Large binaries stay outside Git. |
| What if the host is offline? | Mark the request blocked on host availability, preserve the specification, and continue independent lightweight work. Never substitute a full-scale sandbox run. |
| Which gates remain open? | The acceptance receipt and #27; #16 complete unchanged gem5 light/full-dataset/intended-core work and M1–M5 remain separate open scientific gates. |

GitHub remains the shared coordination authority: task claims/dependencies, source/PRs, scientific evidence,
manifests/summaries, project memory and milestone gates. No permanent roles or central coordinator are introduced.
Host paths, transient service status and local locks describe execution, not agent ownership.

The migration branch is adding literal skip guards for hosted full-system gem5 execution/source builds and
foundation full-dataset/native steady workload steps. Their original commands and scientific criteria remain
retained; skipped expensive controls are **DEFERRED to reviewed local requests, never passed**.
Lightweight Python/vendor/upstream controls, two-nonce verify and one-cache native/QEMU correctness remain.
These branch guards become mainline policy only after the reviewed PR merges; main is not yet updated
at this LOCAL_VALIDATING snapshot. No self-hosted GitHub Actions runner has been provisioned. Do not dispatch the
retained expensive hosted jobs to bypass migration or an offline local host.

## Owner-mediated GitHub submission and retrieval

Here, the local operator means **the owner or an explicitly authorized local session**, including the
current migration session. The host must be online; the owner need not be physically present.
This definition grants no remote access, and a GitHub issue/comment alone grants no execution authority.
The same reviewed request, pinned inputs, resource locks and gate requirements apply to either operator.

Use one scoped task issue per independent work item and the existing [claim protocol](COMMUNICATION.md).
An execution request comment must record the source commit and dirty-tree policy, immutable input identities,
exact executable/arguments/environment, model/configuration, scientific oracle, resource budget,
output retention requirement, duplicate-prevention request key and all prerequisites.
Use a stable key such as `issue-16-runtime-<source-prefix>-attempt-01`; a changed specification or deliberate retry needs a new key and execution ID.
Never embed credentials, owner identity, personal paths or shell instructions received from an untrusted issue as executable authorization.

The retained staging [runtime request revision 02](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085115884)
binds key `issue-27-local-runtime-6f54052-attempt-02`, specification SHA-256
`b0117492ebcf3681fcd28d5b0ae04c7ede200a1deb341566890647d09fdf8ecd` and runner
`916b6b0d33956c847350dc54124132020968aa5a6ff11576911141fa27460977`.
The earlier [pipeline source review](validation/local-migration-20261009/pipeline-independent-review-v2.json)
accepted fixed guards at that snapshot, but **pipeline v2 is now stopped and runner 916 overall future execution
acceptance is withdrawn** after a post-reap PID/process-group signal risk was found.
[Safety hold](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085377771) and
[withdrawal review](https://github.com/jliu67/OpenRX/pull/28#pullrequestreview-5473038322) preserve this correction.
Old request keys 01/02 were never submitted. The replacement [runtime request revision 03](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085838632)
now binds key `issue-27-local-runtime-b4b5ffc-attempt-01`, specification SHA-256
`d11d6f4e5043e3d51a73a0ecf52fc8aa95eb459c6546e46d4136f78013da7972`, runner 988 and readonly source
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`.
[Exact-head review](https://github.com/jliu67/OpenRX/pull/28#pullrequestreview-5473259439) and
[pipeline binding review](validation/local-migration-20261009/pipeline-independent-review-v3.json)
verify those actual source/request/toolchain bindings. Fixed driver
`ace55beda986a44a931b27cc05bcf16590d63ae0cfce1504ec72059cd1c01910` is running as
`openrx-migration-validation-pipeline-v3-20261009.service`. It verified completed build03/loader/input
preflight and submitted runtime-only execution `20261009T193937Z-576aa858c033` at 19:39:37Z.
The new simulator is a distinct 1,036,720,416-byte binary, SHA-256
`e4129f16377346f02b7d68cd508644e5a77cc2daec84a303cc788cb301c05902`.
Preflight SHA-256 `d2043b278dbb1fabf69b220989414cb8c850ea8a5e56dcfa675dbab44ca31626`
supports LOCAL_VALIDATING at 19:38:51Z, not scientific acceptance. Last bounded observations find the
smoke running; complete expected-guest/runtime results, actual gem5 stop and final output verification
remain pending. No full-scale workload or active policy is claimed. The fixed driver is not a remote issue poller.

[Completed build/preflight exports](validation/local-migration-20261009/local-validating-live-v1/index.json)
bind the actual [preflight](validation/local-migration-20261009/local-validating-live-v1/preflight.json),
new binary/config/build-info/loader, source/input/request and bounded live observations.
[Independent postbuild review](validation/local-migration-20261009/local-validating-live-v1/independent-build-preflight-postbuild-review.json)
rehashed the binary,694 original files,10,933 simulator source entries,41 package pins and43 runtime-library
bindings. It accepts build/preflight integrity only. Live manager success while active is not terminal success;
instantaneous socket observations and listener-disable notice do not prove perpetual listener absence,
whole Codex shutdown/host reboot survival or guest correctness. Raw/public evidence identities remain distinct.

The local operator verifies the reviewed request, resolves its paths to the local installation, submits it with the local CLI,
and posts the execution ID plus manifest digest to the task. The local operator later exports sanitized receipts,
required raw evidence and integrity records to GitHub or a deliberately configured artifact channel.
Remote agents can review those publications. **This workflow requires the host online and an owner or explicitly authorized local session to act locally;
the reviewed runtime request has been submitted, but final scientific-result retrieval remains pending.**
GitHub comments alone cannot launch a process.

Before accepting results, match execution/request IDs, source commit/configuration/input digests, complete logs,
actual exit/status and strict scientific validation. A runner `PROCESS_EXITED` status establishes zero process exit;
scientific acceptance additionally requires the declared oracle and independent review.
A missing result is unavailable evidence, not a pass or a scientific failure.

The [separate stop request](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6085930183) is published
and statically reviewed; its controller is still unlaunched until the first verified capture and exact
source/input/owned-cgroup prerequisites. It supplies no actual stop, guest or activation claim.

## Versioned persistent layout

The installation receipt on the host maps the portable variable below to the actual owner-controlled path:

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
export OPENRX_RUNNER="$OPENRX_LOCAL_ROOT/releases/runner-v1-988cf13f/local_execution.py"
```

| Relative path | Purpose |
|---|---|
| `checkouts/` | Separate dedicated migration checkout and pinned execution source trees; original checkout preserved |
| `releases/runner-v1-DIGEST/` | Immutable runner releases; every execution also captures its own runner bytes |
| `sources/`, `builds/`, `toolchains/` | Immutable source captures, persistent incremental simulator builds and pinned dependency records |
| `artifacts/` | Checksummed firmware, kernel, disk, runtime/hash ELFs and restored/rebuilt artifacts |
| `executions/ID/` | Per-attempt manifest, runner snapshot, events, stdout/stderr, process result and receipt |
| `requests/` | Request-key binding to an execution ID; do not erase to force a duplicate |
| `locks/` | Admission, global `execution.lock` resource lock and migration-state locks |
| `state/events.jsonl` | Append-only execution-infrastructure transition ledger |
| `state/execution-receipts.jsonl` | Append-only external receipt-digest bindings used by integrity verification |
| `migrations/20261009/` | Host inventory, original-state capture, package/build logs and migration progress |

Do not move, truncate, overwrite or remove prior scientific data, source builds, results, checkpoints, logs or configurations.
Create a fresh directory/ID for every attempt. Preserve a failed build and investigate a supported incremental rebuild
in that exact tree only when its immutable source/configuration/toolchain binding remains valid; keep the prior failure log.
A rebuild from pinned source is a new artifact with a new digest, never recovery of an unavailable original binary.

## Local runner contract

The source implementation is `scripts/local_execution.py`. Owner operations use the immutable installed
release in `$OPENRX_RUNNER`, selected from the installation receipt, rather than a mutable checkout.
The interface below matches the reviewed runner988 release.
Host fixture records and narrow source reviews are preserved. The corrected source/request/pipeline
bindings are now reviewed; actual build/loader/input preflight passed and the runtime-only request has
been submitted. Further submissions still require their own verified prerequisites and reviewed scope.
Prior runner 916 overall future execution acceptance was withdrawn; its fsync review remains scoped durability evidence.
[Signal-safety review](validation/local-migration-20261009/runner-signal-safety-independent-review.json)
accepts only the narrow f6ea revision with 25 focused tests. Corrected runner `988cf13f…` removes post-reap group
signaling and makes the main loop the sole child reaper. It adds a private finalizer deadline extension using
`Type=simple` / `NotifyAccess=exec`; the worker's 45-second stop budget remains unchanged.
[Final runner/wrapper review](validation/local-migration-20261009/final-runner-wrapper-independent-review.json)
accepts 287 complete repository tests (including 28 runner controls), 40 targeted gem5 wrapper controls,
and a 55.1219-second controlled finalizer delay with six real notifications and verified receipt integrity.
The original false harness result is preserved with [its audit addendum](validation/local-migration-20261009/finalizer-extension-integration/audit-addendum.json). Terminal manager properties
were not captured; this proves timeout extension, not actual large-output throughput or a guest pass.

The nested scientific wrapper had the same confirmed race in a controlled tiny-child fixture:
[wrapper safety audit](validation/local-migration-20261009/wrapper-reap-safety-audit.json) intercepted the
signal without signaling any host group. Its accepted `run_process` source `5c275bf3…` records signals and
polls only in the owning main loop; exact scientific oracles, model and guest/resource acceptance are unchanged.
The original checkout and frozen6f54052 snapshot remain untouched. The reviewed readonly `checkouts/execution-b4b5ffc` now supplies the corrected wrapper and clean,
byte-verified source for local validation. The old frozen executable wrapper remains retained.
The earlier v4/full 277, cd90/full 279/22-focused/v6, and916/23-focused evidence retain their exact snapshots;
they remain separate historical snapshots. The now accepted final combination is exactly runner
`988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882` and wrapper
`5c275bf3da88417970b2219614a39d136fc046d7c6c692fcf4025debb867060e`.
No guest or migration acceptance is inferred from those host tests.

```bash
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" init
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status EXECUTION_ID
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify EXECUTION_ID
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" stop EXECUTION_ID
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" recover EXECUTION_ID
```

Submission records absolute local inputs and argv without an intervening shell:

```bash
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" submit \
  --request-key UNIQUE_REQUEST_KEY --kind validation --validation-scope lifecycle \
  --cwd "$OPENRX_LOCAL_ROOT/checkouts/EXECUTION_CHECKOUT" \
  --input "$OPENRX_LOCAL_ROOT/artifacts/VERIFIED_INPUT" \
  --source "$OPENRX_LOCAL_ROOT/checkouts/EXECUTION_CHECKOUT" \
  -- python3 SCRIPT_WITH_DECLARED_ORACLE.py --output-dir '{execution_dir}/output' ARGUMENTS
```

Every scientific output path must be inside the execution directory: include the literal
`{execution_dir}` argv placeholder, expanded by the runner after reserving a fresh ID.
Bind every executable, script/configuration and guest/resource input using repeated `--input`/`--source` flags.
The runner records digests at submission and rechecks them under the resource lock before launch.
`--kind validation` requires an explicit scope: `lifecycle`, `unit`, `vendor-integrity`,
`guest-runtime-smoke` or `regression-smoke`. The template above uses a lifecycle fixture;
a guest smoke request uses `--validation-scope guest-runtime-smoke` and the unchanged gem5 runtime oracle.
`--kind simulation` is admitted only after `LOCAL_ACTIVE`; validation and build requests remain allowed
in active state. This mechanical admission does not verify GitHub release: the operator must hold expensive
submission until the matching explicit #27 release is independently verified. Pre-cutover validation and
migration builds must be deliberately scoped.
Allowed explicit environment keys are recorded in `scripts/local_execution.py`; unsupported keys fail admission.
Use paths without whitespace, quotes, backslashes or percent signs for the execution root and runner interpreter,
because the durable systemd finalizer rejects unsupported path syntax.

The runner uses a user systemd transient service under a lingering user manager,
so execution does not depend on a Codex session or open terminal. The global resource flock covers
payload execution and descendant drain for every workload class; parallel resource-intensive payload
execution is not supported. Admission and request bindings prevent duplicate submission.
Finalization is recorded separately and may overlap the next payload's admission. Dependent result
consumers must wait for the prior execution's receipt and successfully run `verify EXECUTION_ID`
before using its outputs.
The demonstrated service budget is 6 GiB `MemoryMax`, 1 GiB `MemorySwapMax`, 200% `CPUQuota`,
256 `TasksMax`, `Nice=10` and `NoNewPrivileges=yes`, with cgroup/process-group cleanup.
[Actual properties](validation/local-migration-20261009/runner-lifecycle/v4-service-properties.json)
record the host-applied settings; record them in each manifest.
The dedicated root and services are restricted to the local account; no listener or credentials are committed.

`stop` preserves existing evidence and asks systemd to send SIGINT to the runner,
whose main loop forwards it only while its sole ownership check establishes the child remains unreaped. The declared cleanup windows then permit SIGKILL
if the child cannot stop; systemd also removes cgroup descendants. After natural child reaping, the standalone gem5 wrapper
relies on this outer host cgroup cleanup for detached descendants and never signals a stale numerical group.
Run scientific guest attempts through the accepted local runner; standalone direct invocation does not
supply that durable outer-manager cleanup contract. The gem5 wrapper's reviewed signal
and optional stop-file path remains responsible for its scientific report; missing graceful reports must be recorded. `recover` reconciles manager failure
or host reboot and records interrupted state; it does not rerun the command.
A terminal failure/interruption needs a fresh reviewed attempt and request key.
**Scientific checkpoint/resume is unavailable until separately demonstrated for the exact model/input/version.**
Incremental compilation is separate from simulator checkpoint resume.

`verify` checks retained receipt/output digests against the append-only external receipt binding.
For a lossless private archive, retain both the original execution directory and
`state/execution-receipts.jsonl`; a self-edited receipt cannot establish integrity without its separate binding.
Public exports replace personal paths and are reviewed derivatives. Original artifact/event-chain hashes
in those records identify the retained host bytes, not the sanitized files. Public derivatives cannot be
passed through the host runner's digest/event-chain verifier as if byte-identical originals.
Review the published export index/digests and exact redaction method, then the separate acceptance review
of untouched host records. Preserve host originals and their external journal.
Malformed or torn manifests/receipts or a broken ledger fail closed; preserve them and record `BLOCKED`
for manual, additive forensic reconciliation. Neither cleanup nor `recover` overwrites broken records
or automatically reruns scientific work. See the runbook's power-loss limitation. Files still being written are not final immutable outputs.
Inspect raw logs and the scientific report even when integrity succeeds. Do not edit final outputs to make validation pass.
See the [migration and recovery runbook](LOCAL_MIGRATION.md) for gate order and failure handling.
