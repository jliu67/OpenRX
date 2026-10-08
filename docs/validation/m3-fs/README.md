# Linux runtime controls and gem5 feasibility — 2026-10-08

**The standalone Linux runtime controls passed native and scalar QEMU execution.
The pinned gem5 source builds timed out before linking; gem5 Linux boot and
guest runtime/hash controls remain unexecuted. Task #16 remains open.**

| Evidence stage | Actual outcome | Durable record |
|---|---|---|
| Native Linux runtime | Nine required controls passed | [Runtime review](RUNTIME-REVIEW.md), raw/report files in this directory |
| Cross-built scalar QEMU runtime | Nine required controls passed; known workload matrix still passes 39 controls | [Executed runtime CI](RUNTIME-CI.md) and [CI audit](runtime-ci-audit.json) |
| Guest input preparation | Exact firmware/kernel/disk bytes downloaded and pinned; all SHA-256/upstream MD5 checks passed | [Preparation](PREPARATION.md), [observed resource report](resource-preparation-20261008.json) |
| Guest ELF/library prerequisites | All 15 provider checks and 345 versioned symbols present in the inspected guest image | [ELF review](CROSS-ELF-REVIEW.md), [audit](guest-elf-audit-20261008.json) |
| Pinned source/API/configuration review | Classic L1/L2/walk-cache configuration and guest transfer path approved; seven offline tests and ten explicitly synthetic fault cases passed | [Independent scaffold review](GEM5-REVIEW.md), [retained control inputs/logs](review-controls-20261008/README.md) |
| Hosted gem5 source build | Both original PR/push attempts hit their 45-minute build bound, exit 124 | [CI failure review](CI-BUILD.md), [exact ledger](CI-BUILD.json), full downloaded logs |
| Local gem5 source build | Three 20-minute six-worker windows timed out, final exit 124 at 16:50:20 UTC; 2,266 generated/object outputs retained; simulator not linked | [Local build evidence](build-20261008/README.md) |
| gem5 Linux boot | **Not run:** no usable simulator executable | [Execution status](execution-status-20261008.json) |
| gem5 runtime, light hashes, full dataset | **Not run:** Linux boot has not occurred | [Execution status](execution-status-20261008.json) |

The local source integrity comparison covered all 10,933 regular archive files
with zero differences. No compiler error or OOM was reported in the completed
compilation windows; the terminal result was the declared host build timeout.
Early dependency-discovery failures and the interrupted two-worker attempt are
also retained in the local build record. There is no gem5 binary digest, guest
serial log, generated device tree or real guest execution report from this
session. Synthetic wrapper fixtures are labeled and cannot substitute for them.

The first workflow revision triggered duplicate PR/push builds. The reviewed
final workflow removes the heavy push trigger, retaining scoped PR execution
and manual dispatch. It still uses the declared canonical source build with a
45-minute bound; the evidence does not establish that a cold build fits that
budget. Its downstream boot step is real code, not a mocked success. Failures
remain visible and artifacts preserve the source/build environment and logs.

The retained guest transfer decodes and verifies payloads inside Linux, runs
runtime controls before the unchanged workload, and validates raw output
independently. Hypercall 3 alone never accepts execution because the image emits
it even after a child script fails. The declared simulator configuration is one
Atomic RISC-V core, RVV disabled, 4 GiB RAM and classic private L1/L2/walk caches.
This is a functional candidate, not a BOOM/C920 model or calibrated timing CPU.

## Next commands

Resume the **unchanged canonical** build from the retained local source/build
directory, with the exact environment in [the local build handoff](build-20261008/README.md).
Preserve a new bounded log and source/configuration comparison:

```bash
cd /tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9
PATH=/tmp/openrx-gem5-source/apt-root/usr/bin:$PATH \
PYTHONPATH=/tmp/openrx-gem5-source/python-build-deps \
PYTHON_CONFIG=/tmp/openrx-gem5-source/bin/python3-config \
LD_LIBRARY_PATH=/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu \
timeout 1200 python3 -m SCons build/RISCV/gem5.opt -j6 --without-tcmalloc
```

For a fresh build, a source-reviewed alternative omits unused Ruby/SystemC/KVM.
It does not omit O3/Minor or the full RISC-V decoder, and it has **not built or
booted in this session**. Keep it separate from the current incremental build:

```bash
scons defconfig build/RISCV_CLASSIC build_opts/RISCV
scons setconfig build/RISCV_CLASSIC RUBY=n USE_SYSTEMC=n USE_KVM=n
timeout --signal=TERM --kill-after=30s 45m scons build/RISCV_CLASSIC/gem5.opt -j2
```

See the [exact source audit and reuse caveats](GEM5-REVIEW.md#future-supported-classic-only-build-alternative).
Changing those options can invalidate existing compilation signatures; no
build-time improvement is measured. Record the resulting configuration and
binary identity rather than attributing an old canonical build to this recipe.

After an actual successful source build, from the OpenRX repository root:

```bash
LD_LIBRARY_PATH=/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu \
python3 simulator/gem5/run.py --gem5 /tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt --resources /tmp/openrx-fs-resource-audit --runtime-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe --output-dir /tmp/openrx-gem5-runtime-attempt --timeout 1200
```

Use the actual reduced-build executable path if choosing that separate recipe.
The local environment needs its recorded native-library path; do not treat an
absent binary or host loader error as a guest result. Re-download pinned inputs
through `simulator/gem5/prepare.py` if temporary inputs are unavailable.

Only after nine genuine gem5 guest runtime controls pass, repeat in a new output
directory with `--hash-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe`.
That attempts the unchanged **light-mode** v2/v1 interpreter/JIT matrix. Preserve
timeout/partial output honestly. Full-dataset controls, intended timing-core
correctness, RTL boot and M1/M4 calibration remain independent required gates.
No physical throughput, power, hashes per joule or silicon advantage was added.
