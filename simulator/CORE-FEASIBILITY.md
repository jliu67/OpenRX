# Open-core feasibility for the pinned RandomX workload

Research date: 2026-10-08 UTC. Task: [#3](https://github.com/jliu67/OpenRandomX/issues/3). Workload: unchanged RandomX v2.0.1, commit `aaafe71322df6602c21a5c72937ac284724ae561`; v2 primary, v1 regression. This is source-based feasibility research, not an executed core simulation or a performance result.

## Provisional recommendation

Use **Chipyard 1.14.0 / BOOM V3 `MediumBoomV3Config` as the first RTL investigation target**, with scalar RV64GC and software AES. Start functional software checks in the separately documented emulator path before undertaking a Linux-capable RTL environment. Keep Rocket as a simpler integration/control target and CVA6 as an alternative requiring additional FP and memory-map work.

The reason for preferring BOOM is its configurable out-of-order machinery, enabled binary64 divide/square-root path, and existing Chipyard SoC/cosimulation flows. These offer a concrete way to investigate latency overlap later. **They do not establish that BOOM is faster or more efficient for RandomX.** Its chosen configuration has no RVV; it cannot use the pinned vector-crypto AES path. Software AES is a correctness starting point, not a claim about a competitive miner.

The upstream pinned [BoomConfigs.scala](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/generators/chipyard/src/main/scala/config/BoomConfigs.scala) identifies V3 as the stable baseline and describes V4 as less stable with more advanced microarchitecture. Prefer V3 for first integration, rather than selecting V4 merely because it is newer. No RTL modifications or architecture optimizations are authorized by this recommendation. M3 remains open until its exact build, boot and hash-correctness path is demonstrated.

## Immutable research pins

| Component | Revision inspected | Scope |
|---|---|---|
| Chipyard release 1.14.0 | `0acc1e1de2d3284bcd4d876956932a013ffe1949` | Parent configuration and build/docs |
| BOOM, from that parent's gitlink | `5223e44cfeb26f41380057a2eb4d651197475f69` | V3 configuration, FP integration and parameters |
| Rocket Chip, from that parent's gitlink | `55bcad0f59436de98ea510334121de8546b9e9d7` | Shared FPU/multiply support, control core and memory defaults |
| Berkeley HardFloat, from that parent's gitlink | `0ecaef097ce2accbd16a61613699450ed5533f29` | FP dependency and license |
| Standalone CVA6 general release v5.3.0 | `2ef1c1b1fca419354920c5487293bc605294904e` | `cv64a6_imafdc_sv39` candidate, not the Chipyard wrapper |
| CVFPU, from standalone CVA6's gitlink | `3116391bf66660f806b45e212b9949c528b4e270` | CVA6 FP dependency and explicit compliance caveat |

The parent [Git tree](https://api.github.com/repos/ucb-bar/chipyard/git/trees/0acc1e1de2d3284bcd4d876956932a013ffe1949?recursive=1) binds the first four revisions. Chipyard's CVA6 gitlink is `187ed3cd126c68659f446c963599525c2bf58420`; it is a different integration revision and must not inherit compatibility claims from standalone v5.3.0. The newer `cv32a60x-v6.0.0` release concerns a particular RV32 configuration and is not a replacement for this RV64 Linux/FP candidate. Record recursive gitlinks, tool versions and generated configuration before any build; a parent tag alone is insufficient.

## What the workload actually requires

| Requirement | Evidence in unchanged `vendor/randomx/` | Consequence for selection |
|---|---|---|
| Scalar RV64GC execution | `CMakeLists.txt` defaults `RVARCH` to `rv64gc`; `jit_compiler_rv64.cpp` emits integer, compressed and FP instructions | RV64 with M, A, F, D, C and working CSR/instruction-cache interfaces is the starting contract; use the corresponding Linux ABI |
| Exact high-half multiplication | Scalar JIT handlers emit `mulhu` and `mulh`, including superscalar dataset work | A low-half multiplier alone is insufficient; verify signed and unsigned boundary cases |
| Binary64 arithmetic and square root | Scalar JIT emits `fadd.d`, `fsub.d`, `fmul.d`, `fdiv.d`, `fsqrt.d`, moves and conversions | FP presence is not enough; precise results and ordering must be tested |
| Changing FP rounding | FP opcode templates have dynamic `rm=7`; `h_CFROUND` emits `fsrm`; static literal table maps RandomX modes to RISC-V `0,2,3,1` | Exercise RNE, RDN, RUP, RTZ plus immediate post-CSR FP execution and v2's conditional update path |
| Optional vector execution | `JitCompilerRV64` chooses vector code after runtime RVV detection with VLEN at least 128 bits | A scalar-only core is feasible by source design. Claiming RVV changes the actual generated path and requires separate exact controls |
| AES implementation | Scalar static JIT calls `softaes_enc`/`softaes_dec`; `aes_hash.cpp` hardware path calls `*_zvkned`; RVV software-AES helpers have a separate VLEN threshold | Scalar crypto extensions or an MMIO AES accelerator do not automatically accelerate the pinned backend. Preserve software AES initially |
| Runtime support | `cpu.cpp` probes unsupported instructions through SIGILL handling; `virtual_memory.c` uses memory mappings/protection; JIT code uses instruction-cache flushing | A bare-metal hello world is not proof that the unchanged Linux library/JIT runs |

Source interpretation, not execution: the scalar backend supplies an intentional path without RVV. The unchanged build nevertheless compiles vector and `Zvkned` objects with per-file ISA flags even in its default RV64GC build. Thus **the compiler/assembler must understand those extensions although the selected scalar core need not execute those objects**. Preserve the full ELF attributes and disassembly; document that dormant extended-ISA code is present. Validate runtime dispatch rather than calling the entire ELF scalar-only from its global `-march` flag. Avoid `ARCH=native` for the first cross build: its `try_run` probes cannot establish target support merely from cross-compilation.

Use [the source workload report](../docs/PHASE1.md) for memory quantities: the full dataset is 2,181,038,016 bytes, the light/init cache is 256 MiB, and each VM's scratchpad is 2 MiB. These are algorithm allocations, not instructions to make physical L1/L2/L3 match the three scratchpad regions. Light mode can validate hashes but has a different dataset-access cost; it cannot supply mining throughput for the full-memory workload.

## Core comparison at the inspected configurations

| Dimension | BOOM V3 Medium in Chipyard | Rocket control in Chipyard | Standalone CVA6 `cv64a6_imafdc_sv39` |
|---|---|---|---|
| Execution | 2-wide decode, 64-entry ROB; separate integer, memory and FP issue queues | In-order core; current `RocketConfig` uses `WithNHugeCores(1)` | Selected config disables superscalar issue; 8 scoreboard entries |
| FP | `FPUParams` has FLEN 64; selected configuration enables divide/sqrt; Rocket/HardFloat integration | FLEN 64 and divide/sqrt via shared Rocket FPU parameters | F and D enabled; CVFPU dependency has an explicit divide/sqrt caveat |
| Rounding evidence | `fpu.scala` selects `fcsr_rm` for dynamic rounding; `fdiv.scala` buffers rounding and forwards it to `DivSqrtRecF64` | Shared FPU supports rounding-mode inputs; verify the selected core CSR execution sequence | FPU wrapper resolves dynamic rounding from the CSR input; results remain unvalidated |
| Integer multiply | M support, shared multiply/divide machinery; high-half tests still required | `Multiplier.scala` decodes `FN_MULH`, `FN_MULHU`, `FN_MULHSU` | Multiply source implements signed/unsigned high-half paths; tests still required |
| Vector/AES | V3 parameters explicitly set `useVector=false`; software AES baseline | No vector unit selected by `RocketConfig`; a vector configuration is separate work | `RVV=0`. `ZKN=1` is a configuration field, not evidence that AES opcodes are implemented; no matching pinned RandomX scalar AES backend |
| L1/memory | Selected L1D: 64 sets, 4 ways, 64-byte default blocks, 2 MSHRs; inclusive shared cache via parent | Huge-core L1D uses 64 sets, 8 ways and `nMSHRs=0`; shared parent memory framework | 16 KiB instruction cache and 32 KiB write-through data cache; external AXI SoC integration needed |
| Initial burden | Chisel/Scala/CIRCT elaboration, submodules, RTL simulator, guest toolchain and Linux image | Same framework, smaller functional-control target; no assumed runtime ratio | SystemVerilog/Verilator path and SDK exist, but guest image and backing/decode/PMA settings must agree |

The BOOM/Rocket configuration values come from pinned source, not older published block diagrams. BOOM is not a gem5 generic O3 core; configuring similar widths does not create an equivalent model. Scalar AES software execution also prevents an inference about a future hardware-AES architecture's area or energy.

### Concrete blockers rather than assumed compatibility

**Memory capacity:** Chipyard `AbstractConfig` inherits `BaseConfig`/`WithDefaultMemPort`, whose external memory size is `0x10000000` (256 MiB). This is insufficient even for the 256 MiB light cache plus process/VM/guest overhead, and far below the unchanged full dataset. Propose a documented external-memory overlay and matching emitted device tree: initially 1 GiB for bounded Linux light controls and at least 4 GiB for full-memory controls. These are integration starting capacities, not measured optimum hardware sizes. Confirm loader, guest mappings and backing allocation actually cover them.

CVA6's selected config declares only a 1 GiB cached/executable DDR region at `0x80000000`; the stock SoC decoder also maps 1 GiB, while its supplied test-harness SRAM and DTS describe 256 MiB. Full-memory work requires coordinated backing, decode and device-tree changes, plus cacheability across the intended DRAM range. Executable permissions must cover the placement of generated JIT pages. These defaults are SoC integration limitations, not an intrinsic Sv39/RV64 address-capacity limit. Simply increasing a Linux memory argument cannot prove that addresses do not alias or fall outside the RTL decode.

**FP fidelity:** CVFPU's pinned [operations documentation](https://github.com/openhwfoundation/cvfpu/blob/3116391bf66660f806b45e212b9949c528b4e270/README.md#operations) reports known IEEE-754 compliance issues for division and square root. This does not prove that a RandomX hash fails; it makes exact differential tests a prerequisite. The chosen BOOM dependency also describes its FP units as work in progress. Source wiring of rounding is evidence of an intended implementation, not a proof of correct results or CSR ordering. CVA6's `fpu_wrap.sv` connects dynamic rounding, and `csr_regfile.sv` flushes on FRM/FCSR writes; this intended ordering also needs execution controls.

**Crypto configuration:** At standalone CVA6 v5.3.0, the `ZKN=1` field is not sufficient evidence of scalar AES capability. Inspection of `decoder.sv` and `alu.sv` found bit-manipulation handling under ZKN but no AES32/AES64 instruction implementation, and the exact tree has no `core/aes.sv`. Current-master files must not be used to describe this pin. Even a subsequently verified scalar AES core would need a separate reviewed RandomX backend to use those instructions; the pinned hardware path is vector `Zvkned`.

**Memory timing:** Chipyard's old `Memory-Hierarchy.rst` says software RTL simulation uses a single-cycle `SimAXIMem`. At the inspected parent, `AbstractConfig.scala` actually selects `WithBlackBoxSimMem`, whose binder instantiates `SimDRAM`. Record the compiled backing implementation, options, timing configuration and transactions from the generated environment. Neither that name nor simulated core cycle counts alone establishes realistic DRAM latency, power or an SG2042 model.

**Linux and runtime:** Chipyard provides FireMarshal images and FPGA-accelerated Linux boot tests for Rocket/BOOM. That is an upstream-supported path, not our exact `MediumBoomV3Config` Linux boot result. FireMarshal's pinned overview explicitly says automated real-RTL launching currently targets FireSim. Native Verilator Linux loading requires its own tested boot/loader/device path. CVA6 likewise documents a Linux SDK/FPGA boot and an APU Verilator flow; these are distinct documentation paths, not proof of Linux simulation on our exact RV64 FP configuration. Do not silently replace Linux signals and mapping semantics with a libgloss/HTIF bare-metal environment.

**Runtime budget:** Chipyard's pinned RTL simulation guide documents about 6.5 GB host memory for its Rocket elaboration example and warns other configurations may require more. No BOOM build memory, Linux boot time, simulated cycles/second or full RandomX runtime was measured here. Run a bounded pilot, retain timeout/failure logs, and project any expanded run from that observed pilot; do not prescribe full-dataset RTL hashing as a quick smoke test.

## License feasibility

No candidate has been vendored by this research. Preserve component/file notices if doing so later.

| Scope | Inspected terms | Caveat |
|---|---|---|
| Chipyard and BOOM | BSD-3-Clause root licenses; `LICENSE.SiFive` supplies Apache-2.0 terms for applicable files | Top-level BSD does not relicense submodules or every source file |
| Rocket Chip / HardFloat | Berkeley three-clause terms; Rocket also has Apache-2.0 SiFive and separate JTAG notices | Audit the emitted/redistributed dependency set |
| CVA6 | Root `LICENSE` is Solderpad 0.51; selected config header uses `Apache-2.0 WITH SHL-2.0`; other components carry their own notices | A single repository-wide “Solderpad 2.1” label would be inaccurate at this pin |

These are source-license observations, not an opinion on a future product's patent position. The feasibility task needs a dependency notice inventory before redistribution, not a claim that an open ISA makes a vendor chip or implementation open.

## Acceptance sequence

1. Revalidate the RandomX vendor manifest and cross-build the unchanged workload; record toolchain revisions, all compile flags, ELF hashes and per-object ISA metadata.
2. Run bounded Linux scalar controls in the functional emulator path. Preserve exact reference outputs, v1/v2 interpreter/JIT comparisons, unsupported-instruction behavior and failures. This checks software feasibility, not a BOOM core.
3. Pin and elaborate the chosen unmodified BOOM V3 SoC. Save generated configuration, memory size/map, guest image, simulator and dependency versions. Demonstrate boot and required runtime services before workload execution.
4. Exercise high-half multiply, four rounding modes, FP divide/sqrt edge cases, rounding CSR ordering, instruction-cache invalidation and software AES; compare exact results against independent known references. Then compare unchanged v1/v2 hashes across interpreter/JIT.
5. Establish full-memory correctness with the full dataset and compatible guest/backing capacities. Keep any reduced microtests labeled as such and retain upstream test skips explicitly.
6. Only after correctness and calibrated memory/CPU timing assumptions satisfy M4 may architectural sweeps support design conclusions. No FPGA/cloud provisioning, modeled wall power or RTL optimization follows from this source report.

## Primary-source ledger

All links below name inspected immutable revisions, except release discovery pages. The current canonical CVA6 organization is `openhwfoundation`; old `openhwgroup` links redirect but some connector reads do not.

- Release discovery: [Chipyard releases](https://github.com/ucb-bar/chipyard/releases), [CVA6 releases](https://github.com/openhwfoundation/cva6/releases).
- Chipyard: [abstract SoC](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/generators/chipyard/src/main/scala/config/AbstractConfig.scala), [memory binders](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/generators/chipyard/src/main/scala/harness/HarnessBinders.scala), [RTL guide](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/docs/Simulation/Software-RTL-Simulation.rst), [FireMarshal overview](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/docs/Software/FireMarshal.rst), [Linux boot test script](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/.github/scripts/run-linux-poweroff.py).
- BOOM: [V3 configuration fragments](https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/common/config-mixins.scala), [parameters](https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/common/parameters.scala), [FP unit](https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/exu/execution-units/fpu.scala), [divide/sqrt](https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/exu/execution-units/fdiv.scala), [BSD license](https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/LICENSE), [Apache terms](https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/LICENSE.SiFive).
- Rocket: [current Chipyard control configuration](https://github.com/ucb-bar/chipyard/blob/0acc1e1de2d3284bcd4d876956932a013ffe1949/generators/chipyard/src/main/scala/config/RocketConfigs.scala), [core fragments](https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/src/main/scala/rocket/Configs.scala), [external memory defaults/size overlay](https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/src/main/scala/subsystem/Configs.scala), [multiply](https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/src/main/scala/rocket/Multiplier.scala), [FPU](https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/src/main/scala/tile/FPU.scala), [Berkeley license](https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/LICENSE.Berkeley), [Apache terms](https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/LICENSE.SiFive).
- HardFloat: [README / testing caveat](https://github.com/ucb-bar/berkeley-hardfloat/blob/0ecaef097ce2accbd16a61613699450ed5533f29/README.md), [license](https://github.com/ucb-bar/berkeley-hardfloat/blob/0ecaef097ce2accbd16a61613699450ed5533f29/LICENSE).
- CVA6: [selected config](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/core/include/cv64a6_imafdc_sv39_config_pkg.sv), [root license](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/LICENSE), [decoder](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/core/decoder.sv), [ALU](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/core/alu.sv), [multiply](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/core/multiplier.sv), [FPU wrapper](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/core/fpu_wrap.sv), [CSR ordering](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/core/csr_regfile.sv), [test harness backing](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/corev_apu/tb/ariane_testharness.sv), [DDR decoder](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/corev_apu/tb/ariane_soc_pkg.sv), [DTS](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/corev_apu/bootrom/ariane.dts), [build/boot documentation](https://github.com/openhwfoundation/cva6/blob/2ef1c1b1fca419354920c5487293bc605294904e/README.md), [CVFPU gitlink](https://api.github.com/repos/openhwfoundation/cva6/contents/core/cvfpu?ref=2ef1c1b1fca419354920c5487293bc605294904e), [CVFPU caveat](https://github.com/openhwfoundation/cvfpu/blob/3116391bf66660f806b45e212b9949c528b4e270/README.md).

Validation in this report is source inspection and immutable-revision reconciliation only. Core builds, RTL boot, FP conformance tests and RandomX execution on these RTL configurations were not run.
