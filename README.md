# OpenRX

## Current floating execution extension — task #58, 2026-10-13

[PR #55](https://github.com/jliu67/OpenRX/pull/55#pullrequestreview-5498804300)
and [PR #57](https://github.com/jliu67/OpenRX/pull/57#pullrequestreview-5499497883)
are independently accepted at `2b14e4f9` / `d62c4495` and remain draft/unmerged.
[Task #58](https://github.com/jliu67/OpenRX/issues/58) adds exact native floating
add/subtract/multiply, bit operations and CFROUND on a separate stacked temporary
branch. Proven licensed HardFloat1/8086-SSE bytes supply arithmetic; native masks,
rounding, DAZ/FTZ and held/reset behavior remain exact. Division/square root still
trap. This new work requires independent review; no merge is authorized. Earlier
summaries retain dated publication context. All pinned assets and serialized
compute rules remain; full VM/hash, selected core and calibrated physical PPA
remain open. [Design](rtl/execute/FLOATING.md) records concrete interfaces and validation.

## Current stacked extension — task #56, 2026-10-13

[PR #55](https://github.com/jliu67/OpenRX/pull/55#pullrequestreview-5498804300) is
independently accepted at `2b14e4f9` and remains draft/unmerged. [Task #56](https://github.com/jliu67/OpenRX/issues/56)
adds the missing multiply/reciprocal families and exact conditional branches on a
separate temporary feature branch. This new work requires independent review and
has no merge authorization. Earlier pointers/review-pending statements retain
their dated publication context; no full-hash, selected-core or calibrated-PPA
acceptance follows. All pinned assets and serialized compute rules remain.

## Current component sequence — 2026-10-13

[PR49](https://github.com/jliu67/OpenRX/pull/49), [PR51](https://github.com/jliu67/OpenRX/pull/51)
and [PR53](https://github.com/jliu67/OpenRX/pull/53) are independently accepted and
merged; current parent main is `a6450ceccd32848c438c7dcae6acb98695d2a0e8`.
[Task54](https://github.com/jliu67/OpenRX/issues/54) adds actual native integer
execution under the owner-authorized manager-led continuation. PR #55 was
independently accepted at `2b14e4f9` and remains draft/unmerged; no further merge is authorized.
Earlier component pointers,
review-pending summaries and governance statements below retain their dated
publication context. Issue claims remain the ownership record, the manager assigns
bounded current scopes, and compute is serialized. Full-core/hash, selected-core,
calibrated timing and physical-power gates remain open.

## Current objective — manager-led build-first delivery, 2026-10-12

Deliver working RandomX v2 execution hardware using licensed reusable IP, with
reference correctness tests, reproducible synthesis, a useful execution integration
interface and measured component improvement. The active owner-designated manager
assigns bounded scopes, redirects agents, coordinates the shared compute slot and
keeps delivery moving. Research is timeboxed to a concrete implementation blocker;
reuse completed decisions/evidence and avoid repeated surveys, status cycles and
separate documentation approval chains. Keep overhead minimal while retaining
source/tool/command provenance, failures and independent review of new work.

[Current implementation #48](https://github.com/jliu67/OpenRX/issues/48) /
[draft PR #49](https://github.com/jliu67/OpenRX/pull/49) delivers the required F/E AES
stage. Genuine full-workload, selected-core, calibrated timing and physical-power
acceptance requirements remain; earlier milestones are not declared passed by
this build-first instruction. Issue claims remain the source ownership record,
and compute remains serialized. Historical results and pinned assets are retained.

## Accepted exploratory native pilot — 2026-10-12

[Independent terminal review](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969) accepts native execution
`20261012T185152Z-97e747b1f6c4` (18:51:54Z–18:55:54Z): two balanced v2/v1 repeats
at one six-worker hardware-AES/full-dataset/JIT setting, with reviewed controls,
output, original-input/receipt integrity and actual drain/slot release. Reused
native source stays `4a4e30bbbda47cce7713c280d87f1506f7c6f954`. [Selected pilot evidence](docs/validation/native-pilot-20261012/README.md)
records all four intervals and limits. This supersedes the earlier fixture-only/
no-native-pilot stage; it does not complete the formal #8/EXP-001 baseline or M1.

#16's accepted 39-required + nine-runtime light matrix remains distinct at
scientific source `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`, with optional hardware
AES skipped. Broader gem5 full-dataset/intended-core/SMP, selected-core,
calibration/power, RTL and M1–M5 gates remain open. No new workload, claim,
settings change, thermal equilibrium or competitive PPA is authorized or inferred.

## Accepted #16 light matrix — 2026-10-12

The [independently accepted terminal result](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891) completes the bounded
gem5 Linux light-mode matrix: **39 required controls** (31 arithmetic + eight
v2/v1 interpreter/JIT software hashes) and **nine Linux runtime controls** pass;
one optional hardware-AES case is explicitly skipped. Execution
`20261012T032030Z-65cbb4c0cf9e` retains scientific source
`b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`, not this documentation head.
[Selected evidence](docs/validation/m3-fs/accepted-light-matrix-20261012.md)
records the completed frames/statuses, reviewed integrity and lifecycle release.

#16 remains open for separately gated full-dataset/intended-core/SMP work.
Timing, measured power, BOOM/selected-core, RTL and M1–M5 acceptance remain open.
The earlier incomplete light-matrix/attempt status below is dated history;
original sources, builds, failures and receipts remain preserved.
[Completed source-only #41](https://github.com/jliu67/OpenRX/issues/41#issuecomment-6121699142)
supplies the bounded X9/v2 reuse decision, not a new execution or hardware result.

## Mission — owner direction, 2026-10-12

Design an ASIC targeting Antminer X9-class capability and efficiency, adapted to
exact RandomX v2 execution, with v1 regression coverage. Use evidence-led reverse
engineering where primary information is available, or recreate the needed
capabilities with suitable licensed open IP. Matching X9 is the engineering
objective; no competitive silicon or power/performance/area result is established.

Prioritize reuse of pinned RandomX, accepted tooling and preserved builds.
BOOMV3 is a provisional open-IP baseline, not identified X9 silicon. Keep inquiry
bounded to decisions needed for this design; defer broad hardware surveys and
X5/SG2042 reconstruction. [Current priorities and unchanged gates](docs/ROADMAP.md)
and [scope alignment task #39](https://github.com/jliu67/OpenRX/issues/39) guide agents.

## Current status — 2026-10-10

[Migration #27 is complete](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454): independently accepted `LOCAL_ACTIVE` and [explicit designated-host release](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817), after merged PRs #28 and #30. [Cleanup #31 / merged PR #32](https://github.com/jliu67/OpenRX/issues/31#issuecomment-6099136057) establishes GitHub-only progress publication: the editable migration checkout and disposable sync mirror were recoverably retired; sync stays disabled. Evidence-bound originals, pinned execution sources and computational assets remain retained.

These are verified GitHub closeout records, not a fresh host-health check. Every new execution still needs its reviewed request, current host/resource checks and existing admission gates. #16's complete unchanged RandomX matrix, full dataset and intended-core/SMP/BOOM gates remain open, as do M1–M5. Controlled measurement configuration/authorization, meter and PMU access are separate prerequisites. Dated CUTOVER_PENDING and pre-final records below are preserved history, not current migration blockers.

Progress is published and coordinated on GitHub. There is no standing editable local progress mirror or automatic Git sync; necessary reproducibility sources and computational assets remain local. See [the publication/source-retention policy](docs/PROGRESS_PUBLICATION_POLICY.md).

The mission above supersedes the earlier broad X5/RISC-V research scope; its wording and evidence remain in [project memory](memory/PROJECT.md#earlier-mission--retained-history).

## Start here

**⚡ OWNER RESOURCE POLICY:** All Codex agents must maximize safe utilization of the owner's local Ubuntu machine (6 CPU cores, 16 GiB RAM) for authorized OpenRX jobs. Do not default to old sandbox caps. See the prominent mandatory guidance in [AGENTS.md](AGENTS.md#-owner-directive--maximize-local-compute-utilization-all-agents) and the [execution resource policy](docs/LOCAL_RESOURCE_POLICY.md). Scientific and migration gates remain in force.


**Current delivery is manager-led.** The active owner-designated manager assigns bounded scopes and coordinates the shared slot; issue claims still record ownership. Apply the [current X9/v2 priority path](docs/ROADMAP.md#current-priority-path--2026-10-12) before browsing the [shared ready-task pool](https://github.com/jliu67/OpenRandomX/issues?q=is%3Aissue+is%3Aopen+label%3Aagent%3Atask+label%3Aagent%3Astatus%3Aready). Completed [#41](https://github.com/jliu67/OpenRX/issues/41) supplies reusable prior evidence; [#48](https://github.com/jliu67/OpenRX/issues/48) / [PR #49](https://github.com/jliu67/OpenRX/pull/49) is the current build-first implementation; #2 X5 reconstruction is priority-blocked, not completed. Follow the manager’s bounded scope and record the claim on its issue; a retained historical milestone or stale ready label cannot override the current priority/acceptance gates. The Markdown board summarizes milestones, not live ownership. [Agent instructions](AGENTS.md) and [protocol](docs/COMMUNICATION.md) explain dependencies and handoffs.

- [Project board](docs/TASKS.md): status, blockers and next tasks
- [Current handoff](memory/HANDOFF.md): reconciled engineering and communication progress
- [Agent message board #5](https://github.com/jliu67/OpenRandomX/issues/5) and [communication protocol](docs/COMMUNICATION.md): shared task pool, single issue claims, dependencies and handoffs
- [Phase 1 workload report](docs/PHASE1.md) and [same-process update](docs/PHASE1-STEADY.md)
- [Steady adapter protocol](benchmarks/steady/README.md): timing boundaries, limits and commands
- [Power importer protocol](benchmarks/power/README.md): strict input schema, clock mapping, conditional error bounds and synthetic safeguards
- [Project memory](memory/PROJECT.md), [current state](memory/STATE.md), and [agent instructions](AGENTS.md)
- [Roadmap](docs/ROADMAP.md), [RandomX baseline](docs/RANDOMX.md), [hardware evidence](docs/HARDWARE.md), and [experiments](experiments/README.md)

## Persistent local execution infrastructure

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

[Actual expected-guest/runtime evidence](docs/validation/local-migration-20261009/actual-runtime-v1/index.json) and [independent runtime review](docs/validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json) retain exact raw/public digests and independent oracle acceptance.
[Policy/interface](docs/LOCAL_EXECUTION.md), [runbook](docs/LOCAL_MIGRATION.md) and
[dated technical receipt](docs/validation/local-migration-20261009/ACCEPTANCE.md) explain actual gates.
Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.
Sandboxes continue code/review, docs, static analysis, lightweight tests and small reproductions.
The [owner resource directive](docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
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

## RISC-V feasibility progress

[Merged M3 work in PR #15](https://github.com/jliu67/OpenRandomX/pull/15) adds an
executable scalar RISC-V preflight, exact integer/FP controls and v2/v1
interpreter/JIT references. Actual QEMU CI passed all 39 required checks;
raw logs and binary digests were downloaded and independently revalidated.
See [candidate selections](simulator/README.md), [EXP-002](experiments/EXP-002-riscv-functional-preflight.md)
and [validation](docs/validation/m3/README.md).

Chipyard/MediumBoomV3Config is the provisional open RTL research target.
gem5 requires a validated Linux runtime path: its SE signal/cache-flush gaps
affect unchanged RandomX startup/JIT. [Task #16](https://github.com/jliu67/OpenRandomX/issues/16)
tracks full-system Linux feasibility. [Explicit Linux runtime controls](docs/validation/m3-fs/RUNTIME-CI.md) now pass natively and under scalar QEMU: actual SIGILL recovery, RW/RX page permissions and generated-code overwrite/flush/reexecution. M3 remains open for selected-core boot
and full-dataset correctness; no calibrated timing or efficiency is established.

[PR #18](https://github.com/jliu67/OpenRandomX/pull/18) now includes a successfully built pinned simulator and **actual Linux boot with all nine standalone runtime controls passing**, independently replayed. The unchanged light-mode RandomX matrix is a separate open gate under #16. [Executed results](docs/validation/m3-fs/README.md) retain original timeout/OOM failures, supported link recovery and raw guest evidence. [Saved simulator provenance](docs/validation/m3-fs/REUSE.md) remains intact; ordinary PR checks no longer rebuild it.
The original Library binary is currently unavailable to the migration's callable tools, so a separately
recorded pinned local rebuild completed with a new binary identity. Its expected local guest and nine unchanged runtime controls are independently accepted; successful historical saving is not a verified original transfer.
The historical one-core Atomic result does not establish selected RTL behavior or timing.

[PR #19](https://github.com/jliu67/OpenRandomX/pull/19) records the dated Monero source audit: current released mainnet consensus targets RandomX v1, inferred from source rather than a live tip. The beta's October 5 v2 fork is a separate stressnet/testnet schedule. Keep v2-first research and exact v1 controls; [audit](docs/validation/monero-activation/REVIEW-20261008.md) retains remaining activation questions.

## Phase 1 progress

Source characterization, reproducible profiling and the hardened upstream runner are retained. **P1-05 same-process warmup and timestamped hashing is implemented and validated**, commit `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`, integrated on main at `960b8b5`. See [P1-05 validation](docs/validation/p1-05/INTEGRATION.md).

**P1-06S power-data import is independently accepted software.** Review repaired three malformed-input failure-report defects in [merged PR #17](https://github.com/jliu67/OpenRandomX/pull/17), integration `973cd0d94f987ad4a46b85f7b6d66170104c64a1`; task #13 is closed as completed. The repaired importer passes 64 tests and an independent numerical/error-report audit. Final integration CI passes 219 Python tests, 107 upstream tests, six native steady controls, 39 exact native/QEMU RandomX checks and nine Linux runtime controls each; optional hardware AES remains explicitly skipped. [Evidence](docs/validation/m3-fs/RUNTIME-CI.md) records exact runs and source identities. All power joins used synthetic traces; [software acceptance](docs/validation/p1-06s/PATCH-REVIEW-20261008.md) does not certify physical measurements.

The GitHub-native communication history is preserved; protocol v2 is decentralized, with per-task claims and dependencies. It coordinates messages but does not launch AI workers. P1-06S does not change its router, templates, instructions or workflow.

**M1/Phase 1 is still open.** Controlled host measurements, dynamic profiling and real synchronized wall-power readings remain outstanding. Review the importer before physical use; a selected meter may need a separately reviewed format adapter. A green CI run does not establish efficiency; do not mix rates from the older upstream and new static-stride harnesses.

## Quick start (Linux)

Install Git, CMake, C/C++ tools, Make and Python 3.10+. On Ubuntu: `sudo apt install git cmake build-essential python3`.

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -v
python3 scripts/workload_profile.py
bash scripts/build.sh
bash scripts/test.sh
# Functional smoke only:
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
# Offline power-schema tests; synthetic inputs, NOT measured power:
python3 -m unittest discover -s tests -p test_power_import.py -v
```

Full-dataset known-reference controls and `native_steady.py` allocate the full dataset (over 2 GiB).
Run them only through the designated immutable local runner **after verified cutover**, with a reviewed
owner-local request and fresh persistent execution ID. Retain these scientific commands in that request:

```bash
python3 scripts/benchmark.py --mode mine --versions v1 v2 --threads 1 --nonces 1000 --repeats 1
# Optional same-process adapter and full-dataset native controls:
bash scripts/build_steady.sh
python3 tests/native_steady.py
```

RandomX v2.0.1 is included in `vendor/randomx/` at upstream commit `aaafe71322df6602c21a5c72937ac284724ae561`; no submodule download is required. Original BSD-3-Clause licenses/notices are retained. See [third-party notices](THIRD_PARTY_NOTICES.md).

Timestamped runs under `benchmarks/results/` retain raw logs and JSON metadata. Commit selected reviewed evidence and analysis. Do not call cloud controls SG2042 measurements or derive hashes/J without a measured power boundary. Historical foundation and initial Phase 1 evidence remain in [VALIDATION.md](docs/VALIDATION.md) and [validation/phase1](docs/validation/phase1/README.md).

## Repository map

| Directory | Purpose |
|---|---|
| memory/ | Persistent goals, state, decisions, session log and handoff snapshots |
| docs/ | Evidence, methodology, communication, hardware notes and roadmap |
| vendor/randomx/ | Unmodified pinned upstream source |
| scripts/ | Integrity, builds, evidence runners, power import and deterministic message routing |
| tests/ | Tooling/communication regressions and explicit native controls |
| benchmarks/ | Results, measurement protocols and opt-in steady adapter |
| experiments/ | Experiment plans and outcomes |
| simulator/ | Simulator selection/configuration plans |
| rtl/ | Future verified processor work; no RTL yet |
| .github/ | CI, message router, task templates and review checklist |

Repository memory and inboxes are not autonomous workers: an invoked agent must read, update and commit its handoff. No background model execution is implied.
