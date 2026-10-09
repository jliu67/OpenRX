# gem5 full-system Linux functional gate — task #16

**Current execution gate — migration #27 is STAGING; NOT YET ACTIVE.**
Read [local policy](../../docs/LOCAL_EXECUTION.md), [runbook](../../docs/LOCAL_MIGRATION.md) and
[acceptance receipt](../../docs/validation/local-migration-20261009/ACCEPTANCE.md).
Only declared migration smoke tests may execute on the staging host after prerequisite gates.
Full-scale research is held until cutover; thereafter expensive gem5 runs/builds use the designated Ubuntu host.
Remote agents have no access; owner-mediated GitHub submission/results is the current interface.
The direct/hosted command recipes below are retained technical references and do not authorize independent expensive sandbox execution.
Original binary saving/boot evidence is historical; that Library binary is currently inaccessible and a separately verified pinned local rebuild is in progress.

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
reuse path has not run end to end. The ongoing light-mode attempt must complete
its unchanged 39-control matrix before that stage can pass; task #16 remains open.

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
