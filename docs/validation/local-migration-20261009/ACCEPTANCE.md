# Dated local migration technical acceptance — pre-cutover

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

[Runtime evidence](actual-runtime-v1/index.json), [independent runtime review](actual-runtime-v1/independent-review/independent-runtime-review.json)
and [postreview integrity](actual-runtime-v1/postreview-integrity.json) preserve exact scientific rows/raw
serial and separately bound sanitized host metadata.

| Required gate | Dated technical outcome | Evidence / remaining action |
|---|---|---|
| Original scientific state preserved | VERIFIED AVAILABLE ORIGINAL STATE | [Original preservation](native-independent-review.json), [postbuild audit](local-validating-live-v1/independent-build-preflight-postbuild-review.json) and actual runtime rehash.694 original/10,933 source entries retained; original Library simulator/unneeded cached pyc unavailable explicitly recorded. |
| Required dependencies | VERIFIED PINNED STARTUP CLOSURE |41 package archives/installed versions,43 library bindings and actual pinned loader/build-info checked; no full offline/hermetic closure. |
| Essential artifacts | VERIFIED DISTINCT REBUILD/EXACT GUEST INPUTS | New binarye4129f16…/1,036,720,416bytes with c822 source/config provenance; exact original ELFs/resources. Original saved binary not restored. |
| Expected guest boot | INDEPENDENTLY ACCEPTED | Execution193937, Ubuntu24.04/Linux6.8.12, complete hypercalls1/2/3 and original config/input model. |
| Correctness/regression smoke | INDEPENDENTLY ACCEPTED WITH SKIPS | New strict guest9; native runtime9/hash39, vendor171/upstream106+valid AVX2skip;287 source tests/40 wrapper controls remain snapshot-bound. No full gem5 RandomX matrix. |
| Launch/session independence | ARCHITECTURE ACCEPTED | Exact988 ten real host controls/launcher exit with continuing manager-owned logs. Whole Codex daemon termination/host reboot unperformed. |
| Status/logs inspectable | VERIFIED | Actual runtime manifests/events/raw logs/process/report/final receipt and source/request IDs retained and independently checked. |
| Stop/failure/recovery | INDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim) | Initial200904 initialization-only stop preserved; broader stop execution20261009T202537Z-a1ca7df2cf1c, actual independent evidence `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`. No checkpoint resume. |
| Output integrity | RUNTIME VERIFIED; BROADER STOP INDEPENDENTLY VERIFIED: all21 artifacts,890 source entries and9 pinned inputs; partial interrupted outputs preserved | Actual runtime receipt/external witness/output/model/input rechecks and[postreview integrity](actual-runtime-v1/postreview-integrity.json); actual stop integrity must match its independently reviewed proof. |
| GitHub architecture consistent | CONDITIONAL DOC SNAPSHOT; FINAL MERGED AUDIT PENDING | Local-only GitHub request/results, immutable runner, locks/offline/no direct remote access; actual D_head/M/D_merged/A_pre/C/E/L readbacks remain future steps at this snapshot. |
| Handoffs/instructions consistent | Final-head mechanical and independent semantic audits required before merge; this snapshot records accepted technical gates only | This exact dated snapshot needs independent review/actual merged-document comparison. Preserve prior STATE/HANDOFF/SESSION_LOG/history. |
| Reviewed migration PR merged | PENDING AT SNAPSHOT |[PR28](https://github.com/jliu67/OpenRX/pull/28); only actual reviewed final-head merge/readback M can satisfy the gate. |
| Complete final acceptance | PENDING | Preactivation F/Q/C certificate after real merge, exact-C review R, actual E/V/L/release, hub/bot synchronization and W/Z/R_Z/publication remain future facts. |


[Actual firmware-seen stop index](actual-gem5-running-stop-v3/index.json) binds44 selected public exports and both independent reviews.
The initial empty-serial stop remains initialization-only. The later intentional stop is accepted for
owned-process termination, inspectable failure/status, retained outputs and integrity, without a
scientific pass or Linux boot for that stop attempt.

The [owner resource directive](../../LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
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

New runtime acceptance review raw SHA12db13426bddda29b7857f423e52fca0b87842c3225d81b2ec2cb3f793170bae,
public SHA941753ae00bc1ca14ee325d03364fa8ca1293cbeca37071c0747467dfbc3d226; index157ca184… binds39
small UTF8 exports/744,273 raw bytes. Runtime rows7dd1fdcb… and serial92a28e6b… remain byte-identical.
Only declared prefix substitutions and one exact stdout hostname field redaction occur in host metadata;
all CR/NUL/scientific framing are retained. Public chain hashes identify host originals; sanitized
records cannot replace raw verifier inputs.

Failed build02, stoppedpipelinev2, withdrawn916 overall execution acceptance, original frozenwrapper
race audit, initial-stop scope and false-harness/audit corrections remain retained; skips never pass.
No whole100GB-output throughput, graceful checkpoint/statistics flush, hardware power or physical crash
recovery is inferred. Inspect current executions with installed immutable runner657 status/verify; historical988 executions retain their own immutable snapshots and receipts;
recover only observes failed records and never reruns scientific work. Malformed/torn records failclosed
with preserved additive forensic copies/manual reconciliation. Full-scale work still requires real
explicit release; dated technical acceptance never activates it.
