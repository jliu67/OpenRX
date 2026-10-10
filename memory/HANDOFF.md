# Handoff — actual designated local execution

**Actual execution state: LOCAL_ACTIVE since 2026-10-10T08:51:50.953900+00:00.**
Dated update: 2026-10-10T08:56:25.052452+00:00.
This dated header records independently accepted activation, explicit release and verified hub delivery.
Eligibility acceptance C: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`; actual transition E:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817`; actual reviewed migration merge M: `f90ac65964bc0138711e4b6d45bcb7e26dff3cc9` /
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`; merged-document audit: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`.
The designated local execution policy is effective under the independently verified explicit #27 release
L: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817`. Its effective-policy hub announcement/bot receipt H:
`https://github.com/jliu67/OpenRX/issues/5#issuecomment-6095882106` / `https://github.com/jliu67/OpenRX/issues/5#issuecomment-6095883184` are verified.
Check [#27](https://github.com/jliu67/OpenRX/issues/27) and local status before each new request; later
BLOCKED/ROLLBACK_REQUIRED evidence or an offline host holds new admission.

This dated update records actual activation/release. Its own separately reviewed documentation PR merge
and readback are published externally on #27; they are never self-referential hashes embedded here.
At this dated update, final synchronized migration acceptance W/Z has not yet been published. The live
#27 record supplies the later final receipt once this actual documentation integration and all required
readbacks are independently accepted. This dated pre-Z status remains historical after final publication;
LOCAL_ACTIVE, a released policy, a router label and this header alone do not prove migration completion.

The [owner resource policy](../docs/LOCAL_RESOURCE_POLICY.md) remains unchanged. The immutable
operational runner release is `runner-v1-657b23f1`, SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`; exact resource/profile/kernel proof:
`https://github.com/jliu67/OpenRX/blob/20c2e7b873d291689b86a9e28cdb06a527467032/docs/validation/local-migration-20261009/resource-kernel-20261010/index.json`. The owner-local-max-v1 profile permits six CPU cores
(CPU600%) and uses at most min(14 GiB, fresh MemAvailable minus 1 GiB), with approved lower explicit memory
when justified, swap2GiB/Tasks256 and one payload slot. Admission records current host metrics and rechecks
headroom before launch. It must check the actual payload kernel CPU/memory/swap/task limits and effective
ancestor ceilings, failing closed on missing controllers, mismatched constraints, tighter inherited limits
or lost fresh headroom. The profile publication must independently prove those admission semantics;
manager properties alone are insufficient. Raising CPU quota does not parallelize single-threaded gem5. Historical988 CPU200
was a manager property and was not kernel-enforced; its dated receipts remain unchanged.

Remote execution/direct retrieval remains unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub request, submits locally and publishes hash-indexed sanitized evidence.
No new SSH/listener/poller/self-hosted Actions channel is provided. Hold requests if offline; use temporary
sandboxes for cheap independent work. Permanent request-key bindings and the global payload/descendant
lock prevent duplicate or conflicting expensive execution. Preserve original data and all prior attempts.

The accepted expected Ubuntu24.04/Linux6.8.12 guest and nine unchanged runtime controls remain bound to
execution `20261009T193937Z-576aa858c033` and raw/public indexed review identities. Operational stop proof:
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`, execution `20261009T202537Z-a1ca7df2cf1c`,
scope `independently accepted firmware-seen gem5 lifecycle stop; child-9/wrapper1, preserved partial outputs; no scientific pass or graceful checkpoint/statistics flush`. Intentional interruption proves lifecycle/retention, without
a scientific pass, completed matrix or checkpoint/statistics-flush guarantee. Original Library binary
remains unavailable; the verified c822 pinned rebuild is a distinct artifact with its own provenance.
M0 history is preserved; #16 and M1–M5 remain open. No complete gem5 RandomX matrix/full dataset,
intended timing-core/SMP/BOOM, calibrated timing, physical power/efficiency or RTL acceptance is implied.
Whole Codex daemon termination/host reboot/power-loss tests and full hermetic dependency closure remain
unperformed. No scientific checkpoint resume exists; failed/torn records are preserved for additive
manual independent reconciliation, and recover never reruns scientific work.

Read current task claims and leases before work; no permanent role or central coordinator is established.
For local inspection, select the installed immutable release bound above:

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
export OPENRX_RUNNER="$OPENRX_LOCAL_ROOT/releases/runner-v1-657b23f1/local_execution.py"
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify 20261009T193937Z-576aa858c033
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify 20261009T202537Z-a1ca7df2cf1c
```

Inspect manifests, retained raw logs, source/input hashes and strict independent review before consuming
results. stop preserves evidence; scientific retries use a new reviewed request key/execution ID. Do not
clear request mappings, truncate journals or treat sanitized public chains as host original bytes.

The previous dated pre-cutover HANDOFF follows as historical context. Preserve its byte-exact original
in a new exclusive public archive first. Its retained recipe is inactive unless the current reviewed
request, resource profile and explicit release authorize it.

# Handoff — dated pre-cutover technical snapshot

**Dated technical snapshot: CUTOVER_PENDING, updated 2026-10-10T08:41:07.234399+00:00; actual technical transition 2026-10-10T08:40:10.191934+00:00.**
At this snapshot the migration policy is not released. This dated record does not activate execution.
Expensive OpenRX work uses the designated Ubuntu host only after [#27](https://github.com/jliu67/OpenRX/issues/27)
publishes independently verified eligibility acceptance, matching `LOCAL_ACTIVE` and an **explicit release**
bound to the actual reviewed merge and merged-document audit. Local active state alone is insufficient.
Until that release is verified, defer full-scale work. Check the latest hash-linked state/release proof and
local runner status; a later BLOCKED/ROLLBACK_REQUIRED record or offline host holds new requests.
The effective-policy hub notice follows release; overall completion follows verified hub delivery and
final synchronized acceptance. No merge, release or completion is claimed by this pre-cutover snapshot.

This handoff assigns no permanent role or coordinator. Read live claims and latest #27 task proof,
[policy](../docs/LOCAL_EXECUTION.md), [runbook](../docs/LOCAL_MIGRATION.md),
[technical receipt](../docs/validation/local-migration-20261009/ACCEPTANCE.md), hub#5 and actual remoteHEAD.

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

[Actual runtime index](../docs/validation/local-migration-20261009/actual-runtime-v1/index.json) and
[independent review](../docs/validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json)
accept expected guest/strict9/original source/input/model/output identity. Native controls/vendor/upstream
and final287/40 source evidence remain exactly snapshot-bound; optional capability skips explicit.
Corrected988/5c immutable runtime source b4b5ffc remains distinct from later docs/evidence commits.
Build02 OOM/stoppedv2/withdrawn916/frozenwrapper race and initial200904 stop scope stay retained.

Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.


[Actual firmware-seen stop index](../docs/validation/local-migration-20261009/actual-gem5-running-stop-v3/index.json) binds44 selected public exports and both independent reviews.
The initial empty-serial stop remains initialization-only. The later intentional stop is accepted for
owned-process termination, inspectable failure/status, retained outputs and integrity, without a
scientific pass or Linux boot for that stop attempt.

The [owner resource directive](../docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
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

Next: independent final-head/document review and actual merge/merged-tree consistency audit, then
acyclic F/Q/C/R readiness and actual E/V. Hold expensive work until explicit L/release is real/readback.
Publish hub effective policy afterward and verify bot; W/Z/external exact-Z review and final publication/
protocol completion follow. Do not relabel scientific execution source as the final docs/merge commit.

```bash
export OPENRX_LOCAL_ROOT=/path/to/openrx-local/v1
export OPENRX_RUNNER="$OPENRX_LOCAL_ROOT/releases/runner-v1-657b23f1/local_execution.py"
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" status
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" verify 20261009T193937Z-576aa858c033
```

No checkpoint resume. Corrupt/torn manifests/receipts/ledgers remain preserved and held for additive
manual independent forensic reconciliation; never clear mappings or automatically rerun. Public/raw
digests stay separately indexed and no private paths/credentials/binaries enter Git.
Immediately preceding d40f912 handoff/state/log are byte-exact in their immutable commit and local archive; actual public
archive reference: `memory/handoffs/pre-cutover-20261010-d40f912-manifest.json and immutable d40f912 history`. All earlier archived handoffs stay intact.
The historical recipe below remains inactive and never overrides live explicit-release authority.

## Previous handoff — reviewed cancellation; partial guest and tick-budget proof

2026-10-09 UTC; session `codex/20261008-light-resume`. User authorized continued engineering after extensive repository, agent-message, board and handoff ingestion. Read live [#16](https://github.com/jliu67/OpenRX/issues/16) comments/receipts and current main before claiming work. The repository is now **jliu67/OpenRX**, same repository ID 1409576804. Historical OpenRandomX URLs redirect; use OpenRX for API calls. This document is not a live ownership registry.

## Accepted implementation and actual outcome

[PR #25](https://github.com/jliu67/OpenRX/pull/25) merged at `abe066f7c1b17cb3225b55cc45848a153a20ea7a`. Its tree equals tested source head `9d108c4041e0fa440a676f8a3ee1a2db1d736192`. Independent review repaired two cancellation races before publication; 253 Python tests, including 34 gem5 host controls, and 171 vendor files passed. Five source-head hosted checks passed; separate artifact replay retained 107 upstream / six native steady checks and exact 39 semantic/hash plus nine runtime controls per native/QEMU environment. The hosted gem5 guest job was skipped. [Lifecycle acceptance](../docs/validation/m3-fs/cancellation-20261008/REVIEW.md), [CI replay](../docs/validation/m3-fs/cancellation-20261008/ci-review.md).

The fresh real guest independently passed all nine runtime controls and all 31 integer/FP controls, with **zero completed hash values**. Interpreter cache initialization began; no cache pass, complete hash stream or final hypercall was observed. Exact ELF/configuration review proves both mandatory cache round loops alone require at least **10,519,287,679,000 ticks**, exceeding the current `10^13` per-call allowance. A manual tool-session stop followed that proof at 2026-10-08T23:54Z. It returned exit 1 with no final runner report; actual handler receipt/child return code/reaping are unavailable. No matching wrapper or simulator remains. No observed wall/tick timeout or hash mismatch occurred. [Actual partial acceptance and raw/input bindings](../docs/validation/m3-fs/light-resume-20261008/README.md), [budget proof](../docs/validation/m3-fs/light-resume-20261008/BUDGET-REVIEW.md).

The new optional stop-file control and manual workflow light guard have separate host/source acceptance. Final root validation passes 257 Python tests (38 gem5 controls) and all 171 vendor files; [review and logs](../docs/validation/m3-fs/stop-file-20261008/README.md). They were not executed by that saved real guest. Default no-wall policy, strict validators, workload, resources and model remain unchanged.

## Historical pre-migration execution recipe — inactive

Reuse the original simulator; do not repeat a source build. [REUSE.md](../docs/validation/m3-fs/REUSE.md) gives the two saved parts, exact digests, reconstruction and runtime environment. The original simulator SHA256 is `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`; runtime ELF is `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`; retained hash ELF is `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`. Newly built hosted hash ELF `0e310b9c...` is separate evidence, not this payload.

This pre-migration recipe records the formerly intended sandbox execution inputs. Do not execute it during
migration or use it to bypass the designated host. After cutover, request a fresh durable local attempt with
verified input identities through the local execution interface. Historical command:

```bash
LD_LIBRARY_PATH=/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu \
python3 simulator/gem5/run.py \
  --gem5 /tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt \
  --resources /tmp/openrx-fs-resource-audit \
  --runtime-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe \
  --hash-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe \
  --output-dir /tmp/openrx-gem5-light-next-attempt3 \
  --max-ticks 100000000000000 \
  --stop-file /tmp/openrx-stop-next-light-attempt3
```

Monitor continuously and preserve raw output. The larger finite guard is proposed, not guaranteed sufficient. From another tool session, create the stop file to request the runner's own SIGINT cleanup/report path; never reuse an existing stop marker. Tool/session control-C did not yield a final report in the recorded attempt, so do not infer that outcome. Positive `--timeout SECONDS` remains opt-in. If inputs disappear, restore the saved package and prepare pinned resources before launching; missing inputs are not guest failures.

Acceptance requires exit zero, complete runtime/hash frames with zero statuses and empty stderr, all nine runtime and 39 required semantic/hash controls (eight v2/v1 interpreter/JIT hashes), consistent summary/optional AES skip, guest completion, ordered hypercalls 1/2/3 and unchanged input identities. Do not shrink RandomX constants or infer hashes from partial arithmetic controls.

## Remaining project gates

M0 is complete; M1–M5 remain open. #13 importer software and #4 dated source audit are completed; #20 inspection, #22 queued announcements and #24 compact-handoff policy are completed. #8/#10/#11 require controlled host/counter/meter access. #2 lacks primary X5 board/chip/firmware binding; documented stock SG2042 properties do not identify an X5 derivative. Future Monero activation/live-tip corroboration remains open. Full dataset, intended cores/SMP and selected BOOM Linux boot are separate from Atomic functional controls. M4/M5 still require measured baseline and calibrated model; no RTL, timing or physical efficiency result is established.

All 171 vendor files are now materialized and verified locally; the former four-PDF snapshot omission is resolved. Prior STATE/HANDOFF snapshots are archived under `memory/handoffs/pre-light-resume-*-20261008.md`; original timeout/build/OOM records and SESSION_LOG history remain unchanged. PR #26 integrated at `77a1641fb85f386bce4a5b51e00dedbe257376f6`, with the tested head/tree unchanged. [Final release](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6071620898) is accepted: ready, claim null, no warnings. The required [hub bot copy](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6071623180) was verified. [Integration/CI receipts](../docs/validation/m3-fs/stop-file-20261008/integration.json) preserve exact source/run/job identities.
