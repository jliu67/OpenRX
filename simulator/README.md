# M3 — RISC-V core and simulator feasibility

Updated 2026-10-08. OpenRX now has an executable scalar RISC-V correctness
preflight and source-backed candidate selections. **M3 remains open** for
selected-core/simulator boot, full-dataset controls and independent acceptance.
QEMU functional success does not satisfy M4 timing calibration.

| Purpose | Provisional selection | Current evidence / limitation |
|---|---|---|
| First unchanged scalar Linux interpreter/JIT control | QEMU user mode, `rv64,v=false`, RV64GC/lp64d compilation, software AES | Actual CI light-mode v2/v1 controls pass; no cycle or power model |
| Architectural exploration | gem5 v25.1.0.1; full-system Linux path to investigate | Generic O3 is not BOOM/C920. SE lacks guest SIGILL recovery and syscall 259 cache flushing; unchanged RandomX probes may fail before main |
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

## Remaining engineering gates

1. Demonstrate full-system gem5 Linux startup with an exact guest/toolchain,
   SIGILL recovery and JIT synchronization; run the same light controls.
2. Demonstrate selected BOOM/Chipyard Linux configuration with adequate
   backing, decode, PMA and device-tree memory. Default 256-MiB RAM cannot
   establish RandomX memory feasibility; plan at least 4 GiB for full mode.
3. Repeat upstream and unchanged full-dataset v1/v2 controls on the accepted
   runtime/core; light hashes do not exercise allocated-dataset timing.
4. Complete measured M1 baseline and M4 timing calibration before M5 RTL
   optimization. Functional runs establish no wall-power or hashes/J result.
