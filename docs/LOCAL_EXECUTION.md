# Local execution policy and interface

**Migration state: STAGING. The designated local execution policy is NOT YET ACTIVE.**
[Task #27](https://github.com/jliu67/OpenRX/issues/27) and the
[acceptance receipt](validation/local-migration-20261009/ACCEPTANCE.md) record the evidence and open gates.
The owner's native Ubuntu computer is being prepared as the persistent execution host.
No agent may infer activation from a message, successful install, boot, process launch or status label.
Activation requires all migration gates, a separate review, a merged migration PR and consistent GitHub documentation.

Once verified cutover reaches `LOCAL_ACTIVE`, this computer is the designated host for gem5 full-system runs,
long CPU architecture experiments, large RandomX workloads, expensive profiling/toolchain builds and large generated artifacts.
Temporary agent sandboxes remain available for code/review, documentation, static analysis, lightweight tests,
experimental design and small inexpensive reproductions. During migration, defer full-scale experiments;
only the declared bounded migration validation workloads may run on the local host after their prerequisite gates pass.
The independent scientific gates in #16 and M1–M5 retain their original criteria.

## What a visiting agent must know

| Question | Current answer |
|---|---|
| Where do expensive runs execute? | The owner's Ubuntu host after verified `LOCAL_ACTIVE`; the host is currently staging. |
| Is the runner available? | The runner is staged locally; host fixture lifecycle evidence is available, while final review and local guest validation remain pending. Check #27 and the acceptance receipt before use. |
| How is a request submitted? | A GitHub task issue with the complete execution specification below; the owner reviews and submits it locally. |
| Can a remote agent execute directly? | **No. Remote execution and retrieval are unavailable.** There is no SSH access, network listener or autonomous issue poller provisioned by this migration. |
| How are collisions prevented? | The local runner serializes admission, binds a request key to one execution ID and uses one host resource lock. GitHub claims coordinate source work and are not CPU locks. |
| Where is evidence? | Persistent per-execution manifests/logs/receipts on the host; reviewed, sanitized manifests/summaries and small evidence are attached or linked from the task/PR. Large binaries stay outside Git. |
| What if the host is offline? | Mark the request blocked on host availability, preserve the specification, and continue independent lightweight work. Never substitute a full-scale sandbox run. |
| Which gates remain open? | The acceptance receipt and #27; #16 complete unchanged gem5 light/full-dataset/intended-core work and M1–M5 remain separate open scientific gates. |

GitHub remains the shared coordination authority: task claims/dependencies, source/PRs, scientific evidence,
manifests/summaries, project memory and milestone gates. No permanent roles or central coordinator are introduced.
Host paths, transient service status and local locks describe execution, not agent ownership.

## Owner-mediated GitHub submission and retrieval

Use one scoped task issue per independent work item and the existing [claim protocol](COMMUNICATION.md).
An execution request comment must record the source commit and dirty-tree policy, immutable input identities,
exact executable/arguments/environment, model/configuration, scientific oracle, resource budget,
output retention requirement, duplicate-prevention request key and all prerequisites.
Use a stable key such as `issue-16-runtime-<source-prefix>-attempt-01`; a changed specification or deliberate retry needs a new key and execution ID.
Never embed credentials, owner identity, personal paths or shell instructions received from an untrusted issue as executable authorization.

The owner verifies the reviewed request, resolves its paths to the local installation, submits it with the local CLI,
and posts the execution ID plus manifest digest to the task. The owner later exports sanitized receipts,
required raw evidence and integrity records to GitHub or a deliberately configured artifact channel.
Remote agents can review those publications. **This workflow requires the owner to be online and act locally;
end-to-end request/retrieval has not yet been demonstrated.** GitHub comments alone cannot launch a process.

Before accepting results, match execution/request IDs, source commit/configuration/input digests, complete logs,
actual exit/status and strict scientific validation. A runner `PROCESS_EXITED` status establishes zero process exit;
scientific acceptance additionally requires the declared oracle and independent review.
A missing result is unavailable evidence, not a pass or a scientific failure.

## Versioned persistent layout

The installation receipt on the host maps the portable variable below to the actual owner-controlled path:

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
```

| Relative path | Purpose |
|---|---|
| `checkouts/` | Separate dedicated migration checkout and pinned execution source trees; original checkout preserved |
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

The staged CLI is `scripts/local_execution.py`; the interface below matches the implemented runner.
Host fixture lifecycle validation has executed, while final independent acceptance and simulator guest gates
remain pending. Full-scale operational use requires verified cutover. Execute them on the host from the checked-out source tree.

```bash
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" init
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" status
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" status EXECUTION_ID
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" verify EXECUTION_ID
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" stop EXECUTION_ID
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" recover EXECUTION_ID
```

Submission records absolute local inputs and argv without an intervening shell:

```bash
python3 scripts/local_execution.py --root "$OPENRX_LOCAL_ROOT" submit \
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
Only `simulation` is admitted after `LOCAL_ACTIVE`; pre-cutover validation and migration builds must be deliberately scoped.
Allowed explicit environment keys are recorded in `scripts/local_execution.py`; unsupported keys fail admission.
Use paths without whitespace, quotes, backslashes or percent signs for the execution root and runner interpreter,
because the durable systemd finalizer rejects unsupported path syntax.

The runner uses a user systemd transient service under a lingering user manager,
so execution does not depend on a Codex session or open terminal. One resource flock serializes every workload class;
parallel resource-intensive execution is not supported. Admission and request bindings prevent duplicate submission.
The demonstrated service budget is 6 GiB `MemoryMax`, 1 GiB `MemorySwapMax`, 200% `CPUQuota`,
256 `TasksMax`, `Nice=10` and `NoNewPrivileges=yes`, with cgroup/process-group cleanup.
[Actual properties](validation/local-migration-20261009/runner-lifecycle/v4-service-properties.json)
record the host-applied settings; record them in each manifest.
The dedicated root and services are restricted to the local account; no listener or credentials are committed.

`stop` preserves existing evidence and asks systemd to send SIGINT to the runner,
which forwards the signal to its child process group. The declared cleanup windows then permit SIGKILL
if the child cannot stop; systemd also removes cgroup descendants. The gem5 wrapper's reviewed signal
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
of untouched host records. Preserve host originals and their external journal. Files still being written are not final immutable outputs.
Inspect raw logs and the scientific report even when integrity succeeds. Do not edit final outputs to make validation pass.
See the [migration and recovery runbook](LOCAL_MIGRATION.md) for gate order and failure handling.
