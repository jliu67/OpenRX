# gem5 full-system Linux functional gate — task #16

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

[Actual expected-guest/runtime evidence](../../docs/validation/local-migration-20261009/actual-runtime-v1/index.json) and [independent runtime review](../../docs/validation/local-migration-20261009/actual-runtime-v1/independent-review/independent-runtime-review.json) retain exact raw/public digests and independent oracle acceptance.
Remote execution/direct retrieval remain unavailable. The owner or an explicitly authorized local
session reviews a pinned GitHub task request, submits locally with the immutable runner and publishes
sanitized manifests/results. The owner need not be physically present. No remote execution service,
autonomous issue poller or self-hosted Actions runner is supplied. Issue prose alone grants no execution
authority. Permanent
request-key binding/global payload-and-descendant resource locking prevent duplicates/conflicts; GitHub
claims allocate source work, not CPU. If host offline, hold expensive requests and continue cheap work.
Hosted full gem5/full-dataset/native steady controls stay DEFERRED to reviewed local requests; skips are
unexecuted, never passed. Mainline guard effectiveness is conditional on the actual reviewed merge.

The [owner resource directive](../../docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
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

This path targets **unchanged scalar RandomX under actual guest Linux**, avoiding
the pinned simulator's syscall-emulation signal/cache-flush gaps. It first boots
the guest and runs the standalone Linux runtime controls. A separate opt-in step
attempts the complete light-mode v2/v1 interpreter/JIT matrix. Neither step
establishes full-dataset correctness, selected RTL behavior, calibrated timing,
hardware power or competitive efficiency.

The [2026-10-08 executed outcome](../../docs/validation/m3-fs/README.md) records
successful resource/ELF preparation, a completed pinned simulator build and
actual Linux 6.8.12 boot. All nine standalone guest runtime controls, the
complete 1/2/3 hypercall sequence and input bindings passed
[independent review](../../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md).
Task #16 remains open for the complete unchanged light-mode v2/v1 hash matrix;
its separate 1,200-second attempt timed out after repeating the nine runtime controls and launching the hash probe. No hash mismatch or complete hash result was observed. The
[saved executable package](../../docs/validation/m3-fs/REUSE.md) supports reuse
without another source build. Earlier timeout/OOM records remain intact.

This status update was made after PR #18's successful CI head
`53933bac18e1c1ef0128ee8bd4f40c356dcf1165`; the retained CI documentation digest
is historical. No functional implementation changed in this documentation update.

## Exact inputs

Simulator source: gem5 v25.1.0.1,
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9`.
The source build and compile environment must accompany execution evidence;
`run.py` records the observed simulator executable digest but cannot infer its
source revision from the executable alone.

The [`resources.json`](resources.json) manifest locks the actual dependencies
of gem5's `riscv-ubuntu-24.04-boot@2.0.0` resource, without querying a mutable
catalog at execution time. All three resources were downloaded on 2026-10-08,
their upstream MD5 values verified, and SHA-256/byte-count pins retained. Both
compressed and expanded disk identities are recorded. SHA-256 pins identify
the observed downloaded bytes; they are not a reproducible source-build proof.

| Input | Exact resource | Actual bytes | License boundary |
|---|---|---:|---|
| Firmware | `riscv-bootloader-opensbi-1.3.1@1.0.0` | 1,292,496 | OpenSBI is BSD-2-Clause; inspect binary component/source notices |
| Kernel | `riscv-linux-6.8.12-kernel@1.0.0` | 19,749,472 | Linux GPL-2.0-only; guest bridge/build components have separate notices |
| Compressed disk | `riscv-ubuntu-24.04-img@2.0.0` gzip | 1,517,651,202 | Ubuntu aggregates separately licensed packages |
| Expanded disk | Same resource, partition 1 | 5,242,880,000 | Package copyright files remain in the guest |

The gem5 resource catalog supplies **empty license strings for every binary**;
do not assign one blanket license to the Ubuntu image or claim a complete binary
license audit. This project references/downloads the resources without committing
or redistributing them. Source component notices are linked below. The catalog
boot workload's prose says Linux 6.6.33 although its exact dependency is the
6.8.12 resource; the executed guest's `uname` is the acceptance evidence for
the kernel actually running. Catalog size fields for the firmware/kernel are
also approximate; the manifest contains measured bytes.

## Configuration and guest transfer

`fs.py` is checked against the pinned gem5 APIs: one RISC-V AtomicSimpleCPU,
RVV explicitly disabled, the example's classic private L1/L2/walk-cache
hierarchy (16 KiB instruction/data L1 and 256 KiB L2), dual-channel DDR4
backing and **4 GiB of guest RAM**. Atomic execution is a functional starting
point, not the eventual architectural timing configuration. Other implemented
scalar ISA extensions remain visible in `config.ini` and the generated DTB;
RV64GC compilation does not mean the simulator implements exactly that ISA.
Passing overwrite/re-execution controls establishes guest runtime semantics in
this declared cache hierarchy; coherence and permission behavior must be
repeated on each intended timing core. The pinned `NoCache` implementation
documents a full-system warning, so this recipe follows the official RISC-V
example's supported cache-hierarchy class rather than assuming cacheless boot.

Kernel arguments explicitly select `/sbin/gem5_init.sh` and `no_systemd`.
The upstream image boots the kernel, emits hypercall 1, enters the gem5 user's
shell, emits hypercall 2, and obtains the host script through `gem5-bridge
readfile`. The pinned image recipe installs that init path. The script decodes
base64 guest ELF payloads into `/tmp/openrx`, verifies each SHA-256 inside the
guest, runs the runtime probe before any workload, and retains framed stdout,
stderr and exit status. No in-guest package install, network download or disk
image mutation is needed; gem5 supplies its normal copy-on-write disk wrapper.

The image emits hypercall 3 after the script, even when the script fails.
Therefore, **hypercall 3 or simulator exit 0 alone cannot pass this gate**.
`run.py` requires the full event sequence, complete independent probe oracles,
zero guest statuses, empty probe stderr, a completion marker and unchanged
configuration/payload/resource digests. It preserves a failed report on timeout
or a partial hash matrix, including any independently validated runtime stage.
Original serial logs remain intact; extracted JSONL only removes UART CR bytes
and framing text.

## Acquire and reuse the simulator

**Historical hosted recipes — DEFERRED.** The migration branch guards the expensive manual
`gem5-build.yml` / `gem5-fs.yml` jobs with literal skips, preserving their commands and criteria.
The workflow description below records the previous hosted path; it does not authorize dispatch.
Mainline guards require reviewed merge, skipped jobs are never passes and no self-hosted Actions runner
is configured. New expensive requests use the designated local runner only after verified cutover;
scoped migration validation still requires its own prerequisite evidence.

Pull requests now run fast offline controls only. The actual Linux guest job in
[`gem5-fs.yml`](../../.github/workflows/gem5-fs.yml) is manually invoked with a
successful **same-repository** simulator-build run ID and a separately reviewed
expected `gem5.opt` SHA-256. It downloads the fixed-name
`gem5-simulator-riscv-opt` artifact, validates it before executing anything, then
cross-builds guest controls and attempts boot. Guest tests never invoke a
simulator source build.

Review the producer run and its exact project commit before approving a binary
digest. The [bundle validator](bundle.py) binds the expected binary bytes to
the successful manual build's repository, run/attempt, project commit, pinned
gem5 revision, canonical `build_opts/RISCV`, full generated Kconfig and recorded
toolchain. It rejects changed bytes, missing provenance, alternate ISA/config
records, extra members and symlinks. Only after this gate does the workflow make
the binary executable, check its host dependencies and compare actual
`--build-info` output with the producer record. An artifact's own digest alone
is not an independent trust anchor. Producer records are source/build assertions
checked for consistency; the validator cannot derive a source revision from an
executable or establish source reproducibility.

If a usable reviewed bundle is unavailable, run the separate **manual-only**
[`gem5-build.yml`](../../.github/workflows/gem5-build.yml). It acquires unchanged
source at the pin above, generates the canonical RISCV configuration and makes
one bounded source-build attempt with two workers. The default bound is 60
minutes, selectable from 10 to 90; the job cap is 120 minutes. The upstream
`--limit-ld-memory-usage` option enables GNU ld's `--no-keep-memory` to reduce
host link memory. The exact build command and linker setting are recorded in
the bundle and the v2 cache recipe; simulator features are unchanged. Partial SCons
work is checkpointed even after a build timeout. A later manual attempt restores
only a matching source/target/recipe/full-installed-package/generated-config
cache namespace. Cache keys include run/attempt so an interrupted attempt can
save new progress. Lookup/checkpoint identities, full build logs, actual config
and source status survive failure. Cache eviction, branch scope or changed
packages/configuration can still cause a cold build. Cache reuse is an
acceleration aid, not correctness or provenance proof.

SCons reuse also requires the same absolute source/build paths. These workflows
keep `GITHUB_WORKSPACE/build/gem5-source` stable for the same repository and
hosted runner layout, and record the actual absolute paths. Moving or renaming
that workspace can require a fresh manual build. Configuration/toolchain drift
after restoration suppresses the checkpoint instead of saving it under an old
namespace.

The builder publishes a usable bundle only after a successful clean-source
build, configuration validation and executable build-info check. It does not
boot Linux. Once a reviewer approves that run/commit and binary digest, invoke
the manual guest workflow with `simulator_run_id`, `simulator_sha256` and the
optional `light_hashes` flag. Reuse the same bundle for later guest experiments;
only a deliberate manual build attempt recompiles the simulator. Both workflows
retain logs and failures with read-only repository permissions; only the guest
consumer needs Actions read access to retrieve the selected artifact.

## Reproduce with an already reviewed executable

After installing the scalar GCC 14 guest compiler and the simulator's recorded
shared-library dependencies, use the existing executable. Replace the binary
path and approved digest below before running:

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -p 'test_gem5*.py' -v
mkdir -p build
REVIEWED_GEM5_BINARY=/path/to/reviewed/gem5.opt
APPROVED_GEM5_SHA256=replace_with_the_reviewed_64_character_digest
printf '%s  %s\n' "$APPROVED_GEM5_SHA256" "$REVIEWED_GEM5_BINARY" | sha256sum -c -
riscv64-linux-gnu-gcc-14 -O2 -std=c11 -Wall -Wextra -Werror -march=rv64gc -mabi=lp64d simulator/runtime-probe/main.c -o build/openrx-runtime-probe
python3 simulator/gem5/prepare.py --output-dir build/gem5-resources
python3 simulator/gem5/run.py --gem5 "$REVIEWED_GEM5_BINARY" --resources build/gem5-resources --runtime-binary build/openrx-runtime-probe --output-dir build/gem5-runtime
```

Add `--hash-binary build/probe-riscv/openrx-riscv-probe` and an explicit
`--max-ticks 100000000000000` after separately building
the unchanged scalar workload with the existing pinned toolchain. That is a
**light-mode** control. Full-dataset memory, multithreading and every intended
timing CPU remain separate acceptance gates. Do not shrink RandomX constants
to make a simulation finish.


### Execution timeouts

The simulator runner **does not impose a wall-clock timeout by default**. Previous
1,200-second attempts are retained as historical evidence, not a default limit.
Use `--timeout SECONDS` explicitly only when a bounded experiment is desired;
`--timeout 0` also disables the wall-clock limit. `--max-ticks` remains a
separate simulator event/tick guard and is **not** a wall-clock timeout.

The manually triggered GitHub Actions Linux execution job has no project-specific
`timeout-minutes` override, but GitHub-hosted runners still impose their own
platform limits and can terminate long jobs. Neither disabling the project's
wall limit nor increasing a workflow budget guarantees completion. Keep logs,
intermediate output and exact failure evidence; cancel stalled runs explicitly.

## Resource cost and evidence

The compressed download plus expanded image need approximately 6.3 GiB of
temporary disk space. Allow additional space for gem5 source/build products,
compiler packages and raw logs. Guest memory is 4 GiB; host memory also must
cover simulator/kernel/device overhead and two compiler processes if build and
simulation overlap. The runner records actual host elapsed time and child peak
RSS on Linux, with no conversion to simulated throughput or hashes per joule.
Atomic RAM allocation is not a promise that an arbitrary 7 GiB host can finish
full-dataset simulation. Build and simulation should run sequentially.

Offline controls exercise altered resources, wrong ELF, failed script status,
stderr, truncated/duplicated streams, exact pins and rejected/tampered simulator
bundles. The retained real prefixless Kconfig fixture checks parser compatibility;
the header-only ELF bundle fixture is synthetic and is never executed.
These tests verify the runner, **not a mocked Linux boot**. Actual local build,
boot and nine runtime controls are separately retained in the
[execution record](../../docs/validation/m3-fs/actual-runtime-20261008/README.md)
and independent review above. The new hosted manual builder/cache/artifact
reuse path has not run end to end. The light-mode attempt described in these historical records did not
complete its unchanged 39-control matrix; task #16 remains open. The cited 2026-10-08 build/boot/runtime
records are historical evidence, not a new migration-host pass or an active simulation.

## Primary sources

- [Pinned RISC-V Ubuntu example](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/configs/example/gem5_library/riscv-ubuntu-run.py)
- [Pinned RiscvBoard and disk/DTB configuration](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/gem5/components/boards/riscv_board.py)
- [Pinned kernel/disk/readfile API](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/gem5/components/boards/kernel_disk_workload.py)
- [Pinned ISA parameters](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/arch/riscv/RiscvISA.py)
- [Pinned hypercall exit handlers](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/gem5/simulate/exit_handler.py)
- [Image init source](https://github.com/gem5/gem5-resources/blob/672d04917020934d452b2e767e97875c34693dee/src/riscv-fs/riscv-ubuntu-22.04-24.04/files/gem5_init.sh)
- [Image after-boot source](https://github.com/gem5/gem5-resources/blob/672d04917020934d452b2e767e97875c34693dee/src/riscv-fs/riscv-ubuntu-22.04-24.04/files/after_boot.sh)
- [Image installation/init paths](https://github.com/gem5/gem5-resources/blob/672d04917020934d452b2e767e97875c34693dee/src/riscv-fs/riscv-ubuntu-22.04-24.04/scripts/post-installation.sh)
- [OpenSBI v1.3.1 notices](https://github.com/riscv-software-src/opensbi/blob/v1.3.1/COPYING.BSD)
- [Linux v6.8 license rules](https://github.com/torvalds/linux/blob/v6.8/COPYING)
- [Ubuntu licensing](https://ubuntu.com/legal/intellectual-property-policy)
- [Cross-run same-repository artifact download](https://github.com/actions/download-artifact)
- [Cache matching and eviction behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)
- [Pinned low-memory linker option](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/SConstruct)

## Extended light attempt and external stop requests

[The extended actual attempt](../../docs/validation/m3-fs/light-resume-20261008/README.md)
passed all nine runtime and 31 arithmetic controls, with zero completed hash
values. It was manually stopped after independent exact-ELF/configuration
review proved the default `10^13` per-call tick guard insufficient for both
mandatory cache initializations. The next recipe declares `10^14` explicitly;
that larger finite guard still requires executed completion and strict review.
Default values and historical attempt records remain unchanged.

For a monitored long run, pass `--stop-file /tmp/openrx-stop-next-attempt`
with a path that does not exist. From another tool session, create that file
to request the runner's own SIGINT cleanup and failed final report, including
completed runtime controls. The runner never creates or removes the file;
choose a fresh path for each attempt. Polling this optional control introduces
no wall-clock cutoff. An existing stop path is rejected before launch.

The actual tool-level control-C stop above yielded no final runner report.
[Saved serial/input review](../../docs/validation/m3-fs/light-resume-20261008/REVIEW.md)
distinguishes this limitation from passing host lifecycle tests and from any
future use of the new control. No simulator remains running at that handoff.
