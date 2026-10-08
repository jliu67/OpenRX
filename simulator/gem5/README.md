# gem5 full-system Linux functional gate — task #16

This path targets **unchanged scalar RandomX under actual guest Linux**, avoiding
the pinned simulator's syscall-emulation signal/cache-flush gaps. It first boots
the guest and runs the standalone Linux runtime controls. A separate opt-in step
attempts the complete light-mode v2/v1 interpreter/JIT matrix. Neither step
establishes full-dataset correctness, selected RTL behavior, calibrated timing,
hardware power or competitive efficiency.

The [2026-10-08 executed outcome](../../docs/validation/m3-fs/README.md) records
successful resource/ELF preparation and native/QEMU runtime controls, followed
by hosted/local source-build timeouts before a simulator executable linked.
Linux boot and guest controls were not run. The reviewed recipe remains
unaccepted for task #16 until its actual execution criteria pass.

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

## Reproduce

The ordinary Ubuntu 24.04 GitHub Actions workflow
[`gem5-fs.yml`](../../.github/workflows/gem5-fs.yml) builds exact gem5 source with
two workers, cross-builds the runtime probe, prepares the pinned images and
**attempts a real Linux boot**. Build, preparation and simulator wall limits are
45 minutes, 15 minutes per resource, and 20 minutes per execution respectively;
the complete job is capped at 90 minutes. Logs/configuration/guest binaries and
reports upload even on failure. Large source builds can exceed these limits;
failure is retained and never relabeled as executed success. There is no paid
runner/cloud provisioning in this workflow.

The local equivalent, after installing the documented native build dependencies
and the scalar GCC 14 guest compiler:

```bash
python3 scripts/verify_vendor.py
python3 -m unittest discover -s tests -p test_gem5_fs.py -v
git clone --depth 1 --branch v25.1.0.1 https://github.com/gem5/gem5.git build/gem5-source
test "$(git -C build/gem5-source rev-parse HEAD)" = c8222cc67a399bfc01e8658dd14b30d5bfd634f9
cd build/gem5-source
timeout --kill-after=30s 45m scons build/RISCV/gem5.opt -j2
cd ../..
riscv64-linux-gnu-gcc-14 -O2 -std=c11 -Wall -Wextra -Werror -march=rv64gc -mabi=lp64d simulator/runtime-probe/main.c -o build/openrx-runtime-probe
python3 simulator/gem5/prepare.py --output-dir build/gem5-resources
python3 simulator/gem5/run.py --gem5 build/gem5-source/build/RISCV/gem5.opt --resources build/gem5-resources --runtime-binary build/openrx-runtime-probe --output-dir build/gem5-runtime --timeout 1200
```

Add `--hash-binary build/probe-riscv/openrx-riscv-probe` after separately building
the unchanged scalar workload with the existing pinned toolchain. That is a
**light-mode** control. Full-dataset memory, multithreading and every intended
timing CPU remain separate acceptance gates. Do not shrink RandomX constants
to make a simulation finish.

## Resource cost and evidence

The compressed download plus expanded image need approximately 6.3 GiB of
temporary disk space. Allow additional space for gem5 source/build products,
compiler packages and raw logs. Guest memory is 4 GiB; host memory also must
cover simulator/kernel/device overhead and two compiler processes if build and
simulation overlap. The runner records actual host elapsed time and child peak
RSS on Linux, with no conversion to simulated throughput or hashes per joule.
Atomic RAM allocation is not a promise that an arbitrary 7 GiB host can finish
full-dataset simulation. Build and simulation should run sequentially.

Offline evidence controls pass seven tests for altered resources, wrong ELF,
failed script status, stderr, truncated/duplicated streams and exact pins.
These tests verify the runner, **not a mocked Linux boot**. The local resource
preparation was executed and verified; actual build/boot/workload status must
be reported from the retained session/CI artifacts, not inferred from this
recipe. Task #16 remains open until its executed acceptance criteria pass.

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
