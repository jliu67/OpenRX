# M3 — RISC-V core and simulator feasibility

**Current execution gate — migration #27 is LOCAL_VALIDATING; NOT YET ACTIVE.**
Read [local execution policy](../docs/LOCAL_EXECUTION.md) and
[acceptance receipt](../docs/validation/local-migration-20261009/ACCEPTANCE.md).
Full-scale simulation is held until independently verified acceptance/matching LOCAL_ACTIVE and explicit
#27 release bound to actual reviewed merge/merged-document audit; later expensive runs use the owner's Ubuntu host through
owner-mediated GitHub requests/results. Remote agents have no direct host access.
Historical simulator/guest acceptance below remains intact; it does not validate the new host.
The saved original Library binary is currently inaccessible to migration tools. A distinct pinned build03
and loader/input preflight completed; runtime-only execution `20261009T193937Z-576aa858c033` has started,
with guest correctness and actual stop still pending. Local active state alone does not release expensive work.

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
