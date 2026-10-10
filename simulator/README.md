# M3 — RISC-V core and simulator feasibility

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

[Actual expected-guest/runtime evidence](../docs/validation/local-migration-20261009/actual-runtime-v1/index.json) and [independent runtime review](../docs/validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json) retain exact raw/public digests and independent oracle acceptance.
Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.

The [owner resource directive](../docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
with swap where useful, retaining only measured necessary OS/agent headroom. Per-job allocations must
reflect current host load, memory availability and workload parallelism; 14 GiB is a candidate, not a
universal safe limit. Keep one payload slot and all migration/scientific gates.
The old runner988 validation records retain their actual memory and manager-reported 200% CPUQuota.
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
Scientific records/commands below preserve their dated original criteria and evidence. Retained
expensive direct/hosted recipes are technical references, subject to the verified explicit local release.

Updated 2026-10-08. OpenRX has scalar RISC-V RandomX controls under QEMU and
an independently accepted gem5 full-system Linux boot with nine standalone
runtime controls. **M3 remains open** for complete gem5 RandomX controls,
selected-core boot, full-dataset correctness and independent acceptance.
Functional success does not satisfy M4 timing calibration.

| Purpose | Provisional selection | Current evidence / limitation |
|---|---|---|
| First unchanged scalar Linux interpreter/JIT control | QEMU user mode, `rv64,v=false`, RV64GC/lp64d compilation, software AES | Actual CI light-mode v2/v1 controls pass; no cycle or power model |
| Architectural exploration | gem5 v25.1.0.1; one-core Atomic full-system Linux runtime accepted | Nine standalone runtime controls pass; complete light matrix remains open after a bounded timeout. SE source blockers remain; generic Atomic/O3 is not BOOM/C920 or calibrated timing |
| Open RTL research target | Chipyard 1.14.0 / `MediumBoomV3Config` (BOOM V3) | Source-supported scalar/FP candidate; Linux boot, sufficient guest memory, exact hashes and configuration unexecuted |
| Alternative scalar RTL baseline | Rocket in the same Chipyard pin | Useful in-order comparison; no performance/efficiency selection evidence |
| Deferred alternative | CVA6 v5.3.0 scalar FP configuration | Memory-map/harness capacity and pinned CVFPU div/sqrt compliance concerns; `ZKN` is not proof of AES implementation |

Exact releases, commits, per-component licenses and source locations are in
[CORE-FEASIBILITY.md](CORE-FEASIBILITY.md) and
[SIMULATOR-FEASIBILITY.md](SIMULATOR-FEASIBILITY.md). These are selections for
research, not a measured ranking. Do not describe gem5 generic CPU parameters
as the RTL of a particular processor.

## Runnable functional path

The [probe](probe/main.cpp) links the unchanged pinned RandomX release. It
checks integer wraparound/high-half multiplication, all four rounding modes,
and both upstream inputs through v2/v1 interpreter and JIT paths. Light mode
uses one 256-MiB cache at a time. The separate
[runner](../tests/native_riscv_probe.py) checks complete JSONL and independent
oracles, rejects failures and keeps raw output, commands and binary digest.

Use [EXP-002](../experiments/EXP-002-riscv-functional-preflight.md) for exact
build/run commands, inputs and acceptance. The
[workflow](../.github/workflows/riscv-preflight.yml) cross-builds with GCC 14
and preserves ELF identity, disassembly, compile commands and actual package
versions. Even a scalar run must compile upstream's dormant vector/crypto
objects; ELF attributes can therefore include extensions disabled in the
execution CPU. Never substitute `ARCH=native` in a cross build.

The [validation record](../docs/validation/m3/README.md) distinguishes local
native controls, actual emulated RISC-V results and source-only candidate
research. Reviewed upstream QEMU revisions and the distro version used by CI
are different records.

## Executed gem5 Linux runtime

The pinned gem5 build booted Linux 6.8.12 with one Atomic RISC-V core, RVV
disabled, 4 GiB mapped RAM and the declared classic L1/L2/walk caches. All
**nine standalone runtime controls** passed: SIGILL recovery, denied RW
execution/RX writes, generated returns 7 → 19 → 7 and successful explicit
Linux RISC-V instruction-cache flush calls. Child exit, complete frames,
empty probe stderr and hypercalls 1/2/3 were independently replayed.
See [actual execution](../docs/validation/m3-fs/actual-runtime-20261008/README.md)
and [independent acceptance](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md).

This runtime-only attempt requested no RandomX hashes. The separate complete
light-mode v2/v1 interpreter/JIT attempt timed out without a complete result; the nine runtime
checks do not establish its 39 semantic/hash controls. Permission transitions
may also synchronize instructions, so the result does not isolate flushing
or prove SMP, migration or intended timing-core coherence. Reuse the verified
executable via [REUSE.md](../docs/validation/m3-fs/REUSE.md); check the
[latest execution record](../docs/validation/m3-fs/README.md) before launching
another bounded attempt.

## Remaining engineering gates

1. Complete and independently accept unchanged light-mode v2/v1 interpreter/JIT
   controls on the booted gem5 Linux configuration. The nine standalone runtime
   controls passed; complete RandomX correctness remains a separate gate.
2. Demonstrate selected BOOM/Chipyard Linux configuration with adequate
   backing, decode, PMA and device-tree memory. Default 256-MiB RAM cannot
   establish RandomX memory feasibility; plan at least 4 GiB for full mode.
3. Repeat upstream and unchanged full-dataset v1/v2 controls on the accepted
   runtime/core; light hashes do not exercise allocated-dataset timing.
4. Complete measured M1 baseline and M4 timing calibration before M5 RTL
   optimization. Functional runs establish no wall-power or hashes/J result.
