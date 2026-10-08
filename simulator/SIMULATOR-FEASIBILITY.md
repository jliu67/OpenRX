# M3 simulator feasibility: a functional path before timing

Reviewed 2026-10-08 UTC, session `codex/20261008-m3`, task [#3](https://github.com/jliu67/OpenRandomX/issues/3). This is source-supported selection research for pinned RandomX `aaafe71322df6602c21a5c72937ac284724ae561`, not a completed RandomX simulator validation or an accepted M4 model. See [core feasibility](CORE-FEASIBILITY.md) for RTL choices and their exact configuration limits.

## Recommendation and evidence boundary

Use **scalar RV64GC Linux binaries under QEMU user-mode for the first bounded correctness preflight**. Use **gem5 RISC-V as the provisional architectural-exploration candidate**, initially atomic functional execution in a validated full-system Linux environment, then a separately verified timing CPU configuration. The unmodified workload has signal-handling and JIT cache-flush blockers in the reviewed syscall-emulation path; reduced SE arithmetic probes remain useful separately. Keep **Chipyard/BOOM with Verilator as the RTL simulation alternative**. Spike is a useful independent ISA oracle for reduced tests, with a separate proxy-kernel or Linux integration requirement.

These tools serve different purposes. QEMU and Spike establish functional behavior; they do not simulate a BOOM pipeline or establish hashes/J. gem5 O3 is a configurable software CPU model, not BOOM RTL, SG2042/C920 or an X5 implementation. Verilator executes the RTL actually generated; its testbench memory system still needs a declared model and calibration.

| Evidence layer | Status in this report | What would establish it |
|---|---|---|
| Upstream source and API feasibility | Reviewed at exact revisions below | Source links, license inventory, identified compatibility gaps |
| Project functional smoke under a RISC-V emulator | Not executed by this report's author | Retained preflight logs, versions, ELF/disassembly, exact expected output and exit status; use the session validation record for actual execution results |
| Pinned gem5 full-system Linux standalone runtime | **Executed and independently accepted**, 2026-10-08 update | Actual Linux boot and nine signal/protection/overwrite/flush controls; complete report, serial and source/configuration/payload bindings linked below |
| Pinned gem5/Spike/RTL RandomX correctness | **Pending for gem5; unexecuted for Spike/RTL** | FP and JIT probes plus matching full-algorithm v2 hashes and v1 regressions on each selected CPU/runtime |
| Native versus simulated timing calibration | **Unexecuted** | Controlled native M1 measurements, declared comparable machine/configuration, ROI, model checks and uncertainty |
| Energy/area/silicon performance | **Unknown** | Separately validated power/physical-design evidence; no conversion from emulator wall time |

M3 remains open until the selected core/runtime has an executed reproducible correctness path. A green QEMU probe alone does not accept gem5, BOOM, CVA6 or M4.

## Executed Linux runtime update — 2026-10-08

After the dated source review, the pinned gem5 full-system configuration
booted Linux 6.8.12 and passed all **nine standalone runtime controls** on
one Atomic RISC-V core with RVV disabled, 4 GiB mapped RAM, 16 KiB L1I/L1D,
256 KiB L2 and 8 KiB walker caches. Exact SIGILL, memory-permission,
generated-code overwrite/reexecution and explicit Linux flush-icache oracles
passed; child exit was zero with complete framed output, empty probe stderr
and hypercalls 1/2/3. [Actual execution](../docs/validation/m3-fs/actual-runtime-20261008/README.md),
[report](../docs/validation/m3-fs/actual-runtime-20261008/report.json) and
[independent acceptance](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md)
bind the source, executable, resources, emitted configuration and guest payload.

This runtime-only attempt requested no RandomX hashes. The separate complete
unchanged light-mode v2/v1 interpreter/JIT attempt timed out without a complete result. The result
does not establish FP/RandomX correctness, full-dataset operation, intended
timing-core/RTL behavior or SMP/migration coherence. Permission transitions
can also synchronize instructions; these combined controls do not isolate
the flush mechanism. The earlier SE source analysis remains valid and was
not converted into an executed SE failure claim. Follow the verified
[reuse recipe](../docs/validation/m3-fs/REUSE.md) and current execution record
instead of repeating a source build.

## Exact review revisions and licenses

These are research pins, not a claim that they have been installed or that this combination has built successfully. A CI distribution package is a different revision and must retain its package version and binary digest; recording an upstream release here does not pin an `apt` dependency.

| Component | Reviewed revision | License evidence | Intended role |
|---|---|---|---|
| gem5 | `v25.1.0.1`, `c8222cc67a399bfc01e8658dd14b30d5bfd634f9` | [LICENSE](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/LICENSE), BSD 3-clause; retain per-file/dependency notices and [COPYING](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/COPYING) | Architectural models and memory hierarchy |
| QEMU | `v11.1.2`, release commit `4fc49f46dc95d4a27de2509e7fceb2931e91faeb` | [LICENSE](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/LICENSE), emulator as a whole GPLv2, file-specific compatible licenses; firmware separate | Linux ELF functional execution |
| Spike | `fdc1ffa05152707a00ca22a9cf50c59a1b487875` | [LICENSE](https://github.com/riscv-software-src/riscv-isa-sim/blob/fdc1ffa05152707a00ca22a9cf50c59a1b487875/LICENSE), BSD 3-clause | Reduced ISA differential oracle |
| Chipyard | `1.14.0`, `0acc1e1de2d3284bcd4d876956932a013ffe1949` | [LICENSE](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/LICENSE), BSD 3-clause parent; submodules have their own notices | SoC integration and RTL elaboration |
| Verilator | `v5.052`, `ea338be98e1e838d3518809ce8899f85a009963c` | [README](https://github.com/verilator/verilator/blob/ea338be98e1e838d3518809ce8899f85a009963c/README.rst) and [copyright](https://github.com/verilator/verilator/blob/ea338be98e1e838d3518809ce8899f85a009963c/docs/guide/copyright.rst), LGPL-3.0-only OR Artistic-2.0 | Compile generated RTL to a simulation executable |

Release/ref verification: [gem5 release](https://github.com/gem5/gem5/releases/tag/v25.1.0.1), [QEMU official download](https://www.qemu.org/download/), [QEMU annotated tag object](https://api.github.com/repos/qemu/qemu/git/tags/ceaea6cb3e2a7d966f9ca97c7ebb5b88cd764dd0), [Spike resolved ref](https://api.github.com/repos/riscv-software-src/riscv-isa-sim/git/ref/heads/master), [Chipyard release](https://github.com/ucb-bar/chipyard/releases/tag/1.14.0), [Verilator tag object](https://api.github.com/repos/verilator/verilator/git/tags/efa4927be48e75c3cd08fc848b198d1d9d237f00). Spike's old `v1.1.0` release must not be cited as supporting the current source's vector-crypto list.

Chipyard's parent gitlinks pin BOOM `5223e44cfeb26f41380057a2eb4d651197475f69`, Rocket Chip `55bcad0f59436de98ea510334121de8546b9e9d7`, HardFloat `0ecaef097ce2accbd16a61613699450ed5533f29`, and its CVA6 **wrapper** `187ed3cd126c68659f446c963599525c2bf58420`. The wrapper is not the standalone CVA6 core revision. Preserve `git submodule status --recursive`, build environment and generated RTL digests in an actual experiment. Verilator `v5.052` is an independent candidate pin; compatibility with Chipyard 1.14.0 is not established here.

## ISA, JIT, floating point and AES checks

The pinned [RandomX CMake](../vendor/randomx/CMakeLists.txt) begins RISC-V builds with `rv64gc`. `ARCH=native` runs extension probes and can add V, Zba, Zbb, Zicbop, Zvkb and Zvkned. Therefore, an ELF built on the host with native detection is not a portable RV64GC control. Record compiler, target triple, `-march`, `-mabi`, CMake cache, ELF attributes and disassembly. Avoid fast-math and preserve dynamic rounding. CPU extension flags and actual selected RandomX backend must be retained separately.

The [RISC-V JIT](../vendor/randomx/src/jit_compiler_rv64.cpp) rewrites executable code and calls `__builtin___clear_cache`. The linked compiler runtime may invoke the Linux RISC-V flush-icache ABI. A direct `fence.i` test and a Linux builtin/syscall test answer different questions: the [Linux CMODX documentation](https://docs.kernel.org/arch/riscv/cmodx.html) explains that a local fence alone does not handle migration to another hart under the default Linux ABI. Do not bypass this with an unreviewed vendor patch or silently ignore a syscall failure.

| Requirement | gem5 at review pin | QEMU at review pin | Spike at review pin | Chipyard / Verilator |
|---|---|---|---|---|
| RV64 integer/M/A/C and FP F/D | Decoder/source-supported candidate; exact selected ELF still needs execution | Linux-user RV64 candidate; exact CPU feature configuration needs execution | [README](https://github.com/riscv-software-src/riscv-isa-sim/blob/fdc1ffa05152707a00ca22a9cf50c59a1b487875/README.md) lists these extensions | Determined by generated core configuration; a framework-wide feature list is insufficient |
| Dynamic FP rounding | [`RM_REQUIRED`](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/arch/riscv/fp_inst.hh) selects `frm` for instruction `rm=7`, rejects reserved modes, then configures SoftFloat; [`fadd_d`, `fdiv_d`, `fsqrt_d`](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/arch/riscv/isa/decoder.isa) use FP semantics | [`fpu_helper.c`](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/target/riscv/tcg/fpu_helper.c) selects `env->frm` for dynamic rounding and maps it to software FP rounding | Source-supported F/D candidate; independent operation/rounding tests still required | Test the selected FPU including divide/sqrt; see core report's CVFPU known compliance caveat |
| Self-modifying code | `fence_i` decoded with non-speculative/serialize/squash flags, empty semantic body; this is not proof of instruction/decode-cache invalidation for every CPU model | [Linux-user RISC-V loop](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/linux-user/riscv/cpu_loop.c) returns success for flush-icache syscall because QEMU automatically detects self-modification; test actual repeated overwrite/re-execution | Zifencei is listed; execute overwrite tests, not just an empty fence | Core I-cache/flush protocol, Linux runtime and testbench all matter |
| Scalar AES | [`decoder.isa`](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/arch/riscv/isa/decoder.isa) includes AES32/AES64 scalar operations; this does not imply RandomX uses them | [Scalar helper](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/target/riscv/tcg/crypto_helper.c) includes AES64 semantics | README lists Zkne/Zknd | Exact core config and decoder evidence needed |
| Vector AES (Zvkned) | Reviewed decoder has no `vaes*` instruction entries; do not select the pinned RandomX vector-AES backend on this pin | [Vector-crypto helper](https://github.com/qemu/qemu/blob/4fc49f46dc95d4a27de2509e7fceb2931e91faeb/target/riscv/tcg/vcrypto_helper.c) contains Zvkned AES round semantics; enabling V alone is insufficient | Pinned README lists V and Zvkned | Not implied by V/RVV support, an AES accelerator, or the Chipyard parent |

The minimal scalar control should disable V explicitly in the emulator, use RV64GC/LP64D and force software AES. This establishes a conservative correctness route, not an evaluation of the workload's fastest available backend. Do not infer hardware-AES availability from scalar Zkne/Zknd: pinned RandomX includes a dedicated **vector** Zvkned implementation, and each compiler/runtime/backend combination must be checked.

Required probes are exact-output integer wraparound/multiply-high, FP add/multiply/divide/sqrt in all four RandomX rounding modes, `frm` changes followed by dependent operations, and code generation followed by clear-cache, execution, overwrite, clear-cache and re-execution. Include writable-to-executable transitions and actual return-code checks. Finally run unmodified algorithm v2 and v1 controls; a small arithmetic probe does not prove a complete hash.

## Linux and runtime paths

**QEMU Linux-user is the first path:** cross-compile an RV64GC ELF, select a scalar CPU and execute it under `qemu-riscv64`. The EXP-002 command uses dynamic linkage and an explicit guest sysroot. Record and supply the matching guest loader/libraries; do not mix a host libc with the guest ABI. A static ELF is a separate viable control when built and tested explicitly. Its [official user-mode documentation](https://www.qemu.org/docs/master/user/main.html) describes syscall translation and host-backed threads, so host timings and memory scheduling are not simulated processor measurements. Start single-threaded; concurrency and memory-order correctness are a separate extension.

**gem5 SE has two independent workload blockers:** the pinned [RISC-V SE workload](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/arch/riscv/linux/se_workload.cc) provides `mmap`, `munmap`, `futex`, `clone`, `clone3` and `riscv_hwprobe`, but guest `rt_sigaction`, `rt_sigprocmask` and `rt_sigreturn` use `ignoreWarnOnceFunc`. The pinned [RISC-V faults implementation](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/arch/riscv/faults.cc), in `UnknownInstFault::invokeSE` and `IllegalInstFault::invokeSE`, panics for unsupported instruction execution instead of delivering a recoverable guest SIGILL.

This matters before any hash or JIT call. Unchanged RandomX [cpu.cpp](../vendor/randomx/src/cpu.cpp) constructs its global `Cpu` before `main`, installing a SIGILL handler and using `sigsetjmp` around V and vector-AES probes. [cpu_rv64.S](../vendor/randomx/src/cpu_rv64.S) unconditionally includes `vsetvli`, `vaesem.vv` and `vaesdm.vv` in those probes. On a scalar configuration, SE can therefore panic during startup; enabling V alone still does not supply the absent vector-AES instruction semantics. This is a source-supported failure path, not a locally executed gem5 failure. An interpreter-only library path does not avoid the global constructor.

Separately, SE's RV64 syscall table jumps from 258 to 260 with **no syscall 259 (`riscv_flush_icache`) entry**. Inspect the linked ELF's builtin implementation before attempting JIT: a path that invokes 259 also requires a separately reviewed simulator implementation and coherence tests. `mprotect` is handled by `ignoreFunc`, so SE does not validate real permission enforcement either. Use full-system Linux for the unchanged workload, or resolve both signal delivery and cache flushing with separately reviewed simulator changes. Do not bypass either blocker by silently modifying vendor dispatch or pretending an ignored syscall established its contract.

The reviewed standard-library API supports [`BinaryResource(local_path=...)`](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/gem5/resources/resource.py), [`SimpleProcessor(cpu_type=CPUTypes.ATOMIC, num_cores=1, isa=ISA.RISCV)`](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/gem5/components/processors/simple_processor.py), `SimpleBoard`, and [`set_se_binary_workload(binary, arguments=[...])`](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/gem5/components/boards/se_binary_workload.py). That workload API documents only partial dynamic-ELF support when host and guest ISAs match; use a **static guest ELF** for the x86-host/RISC-V SE control. These are source-checked APIs, not an executed configuration. Start with a local ELF and explicit guest memory to avoid an implicit download or changing resource revision. Repeat every correctness gate with the intended timing CPU, including O3 if selected; atomic success is not timing-model correctness.

**gem5 full-system is the exercised functional path:** the pinned [RISC-V Ubuntu example](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/configs/example/gem5_library/riscv-ubuntu-run.py) uses `RiscvBoard`, classic caches, DDR4 memory and `riscv-ubuntu-24.04-boot` resource version `2.0.0`. OpenRX's separately pinned configuration and resources now have an actual Linux boot and nine accepted standalone runtime controls, linked above. Preserve kernel, firmware, disk and guest toolchain digests, actual flush-icache results and boot logs before accepting unchanged hashes. The current 4 GiB mapped guest RAM has not yet established full-dataset allocation headroom; record actual workload allocation needs.

**Spike is not a drop-in Linux-user substitute:** its README's simple path is `spike pk hello`, built for the proxy kernel. RandomX's Linux executable allocation, threads and runtime dependencies must be supported by the separately pinned proxy-kernel build or by a full Linux boot integration. Use a minimal static oracle for ISA probes first. Spike's sequentially consistent functional model is not an RVWMO timing calibration.

**Chipyard requires a named RTL configuration and workload environment:** [software RTL simulation documentation](https://chipyard.readthedocs.io/en/latest/simulation/software-rtl-simulation/) provides `sims/verilator`, `CONFIG`, `run-binary` and fast ELF memory loading. Bare-metal libgloss supplies a minimal syscall environment, not automatically Linux's mmap/JIT ABI. A full RandomX path therefore needs a separately validated Linux/FireMarshal boot image or a reviewed reduced harness. Preserve the generated memory map, actual SimDRAM implementation and ELF loader behavior; see the core report for pinned-source corrections to older memory documentation.

## Resource cost and the timing gate

Pinned RandomX has a 256 MiB Argon/cache allocation, a `2,181,038,016`-byte dataset (2 GiB plus 33,554,368 bytes), and a 2 MiB scratchpad per VM. V2 generates 384 instructions per program, with 2,048 iterations and eight programs per hash. These are [source constants](../vendor/randomx/src/configuration.h), not retired-instruction counts or measured bottlenecks. Light mode avoids the full dataset allocation but computes dataset items on demand; it is a correctness control with different execution/memory behavior, not a mining-throughput surrogate.

Propose **4 GiB guest RAM for a single-worker full-dataset trial**, then record actual peak RSS/guest allocation and adjust explicitly. Dataset, cache, runtime/kernel, JIT and simulator structures need headroom. The core report identifies Chipyard/CVA6 sample memory regions below this requirement; a larger RAM command-line setting alone does not fix a core's cacheable/executable range or device-tree map. Host memory must also cover simulator overhead, build/elaboration and disk/image storage. Chipyard documentation reports approximately 6.5 GB just to elaborate its default Rocket example; treat this as an upstream report, not a local measurement or a guarantee for BOOM.

The accepted runtime-only gem5 attempt recorded 958.249 host seconds including wrapper input checks, 917.34 host seconds in gem5's final stats and reported peak child RSS of 357,088 KiB. These are observed host costs for this one boot/runtime attempt, not RandomX throughput, calibrated processor timing or physical efficiency. The original attempt had a 1,200-second wall bound; retain limits and timeout/nonzero-exit evidence for each further attempt. Complete the unchanged light hash matrix before progressing to full-dataset hashes and repeated JIT regeneration; scale only after observing actual workload runtime and memory. Do not shrink algorithm constants and call the resulting hashes RandomX.

For M4, record CPU width/queues/functional-unit latencies, branch prediction, I/D-cache geometry and policy, TLBs, dataset/scratchpad mapping, coherence, prefetch and DRAM model. A gem5 default configuration does not identify a real core. The [official O3 description](https://www.gem5.org/documentation/general_docs/cpu_models/O3CPU) identifies a model loosely based on Alpha 21264; parameter similarity does not turn it into BOOM or C920. Similarly, [Verilator's overview](https://verilator.org/guide/latest/overview.html) describes compiled RTL execution, not a physical-power engine.

Use controlled native measurements and separate microbenchmarks for calibration, report residual error and uncertainty, and validate on workload cases withheld from tuning. Preserve initialization versus hashing ROIs and the distinction between light/full-dataset mode. Calibration requires more than fitting a final hashrate. Synthesis/activity-based energy is a future separate result; it cannot be relabeled as whole-system wall power. M1 remains open, and this research does not unlock processor optimization under M5.

## Next acceptance work

1. Use the [retained executed scalar Linux preflight](../docs/validation/m3/README.md), including exact compiler/package versions, ELF digest/disassembly and failures; repeat controls when the configuration changes and distinguish the CI's actual QEMU package from the upstream research pin.
2. Reuse the completed pinned gem5 build and accepted Linux runtime stage; execute the complete unchanged light-mode scalar integer/FP and v2/v1 interpreter/JIT matrix. The SE signal/cache-flush gaps remain separately source-audited; no simulator or vendor workaround was added by the full-system runtime result.
3. Match known complete v2 hashes plus v1 regressions in interpreter and JIT modes; record both software-AES controls and any separately enabled vector/crypto backend. Repeat correctness under each intended CPU model.
4. Elaborate the chosen RTL candidate with compatible pinned dependencies, verify RAM/cacheable/executable mappings and run the same semantic probes and workload controls. Do not substitute generic gem5 O3 results for this RTL gate.
5. Only after workload correctness and M1 evidence, propose an M4 calibration experiment with declared assumptions and uncertainty. Keep task #3 open until the complete selected core/simulator workload path is independently accepted; the standalone gem5 runtime stage does not complete it.
