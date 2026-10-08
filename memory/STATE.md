# Current state

Updated 2026-10-08 UTC / Edmonton. **M0 complete; M1 measured hardware baseline remains open. M3 has source-backed provisional selections and an actual scalar RISC-V functional preflight. M3/M4/M5 acceptance remains open.**

## Latest result — M3 feasibility, PR #15

**Merged on main at `83cbb3ec279a9fab9c5bb18b567fbbd7591f1aed`.** Reviewed final implementation `f9c3ee7debc94807a4a82b537079bdf455aea551` passed [RISC-V CI 37791921197](https://github.com/jliu67/OpenRandomX/actions/runs/37791921197) and [foundation CI 37791921307](https://github.com/jliu67/OpenRandomX/actions/runs/37791921307): **199 Python, 107 upstream, six native steady tests**, plus **39 native / 39 emulated RISC-V required probe checks**. One optional hardware-AES skip per probe was explicit. Final artifact/digest/compile-command audit is retained in [final-ci-audit.json](../docs/validation/m3/final-ci-audit.json).

[PR #15](https://github.com/jliu67/OpenRandomX/pull/15), branch `openrx/m3-riscv-preflight`, advances [task #3](https://github.com/jliu67/OpenRandomX/issues/3). Initial implementation `e5eafde50d074f19afb37d08ccec4c59dd88a33d` passed [RISC-V CI 37790683112](https://github.com/jliu67/OpenRandomX/actions/runs/37790683112) and existing [native CI 37790683131](https://github.com/jliu67/OpenRandomX/actions/runs/37790683131).

Actual native and QEMU RV64GC controls passed **39 required checks each**: seven integer checks, 24 FP checks across four rounding modes, eight exact v2/v1 interpreter/JIT software-AES hashes. Hardware AES was explicitly not requested (one optional skip each). Light mode uses 256 MiB cache, no full dataset. QEMU 8.2.2 and cross GCC 14.2.0 were observed in the actual job, distinct from upstream source-review pins.

Downloaded artifact 11555544301 matched SHA-256 `5f042957866115a6eeb488953ec8d52c892896fd359353efac9da9d9334fadcb`; raw streams were replayed through the stricter current validator. The linked binary is ELF64 little-endian RISC-V (machine 243), with digest `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657` matching the report. [Validation](../docs/validation/m3/README.md) retains logs, exact commands, inputs, versions and limits. Local Python suite passed **199 tests**, including 17 evidence-validator regressions. Final CI/review receipts are linked on #3/PR #15.

[Source research](../simulator/README.md) provisionally selects Chipyard 1.14.0 / MediumBoomV3Config for open RTL research and gem5 v25.1.0.1 for architectural exploration. BOOM boot/hashes are unexecuted. gem5 SE has unsupported signal recovery for RandomX startup ISA probes, lacks Linux cache-flush syscall 259 and ignores mprotect; investigate full-system Linux in new independently claimable [#16](https://github.com/jliu67/OpenRandomX/issues/16). Generic O3 is not BOOM or C920. CVA6 is deferred with FP div/sqrt and memory-map concerns.

## Earlier work preserved

- Pinned unchanged RandomX v2.0.1 `aaafe71322df6602c21a5c72937ac284724ae561`; v2 primary, v1 comparisons.
- P1-05 persistent timing adapter remains implemented/validated.
- P1-06S power importer remains implemented/tested with independent acceptance pending on #13. No physical power result was added.
- Protocol v2, 57 router tests and per-task issue claims remain unchanged. No permanent roles, coordinator or always-running model workers.
- Previous [state](handoffs/pre-m3-state-20261008.md) and [handoff](handoffs/pre-m3-20261008.md) retain full P1-06S history byte-for-byte; SESSION_LOG prefix is preserved.

## Next gates

1. PR #15 is merged as a reviewed M3 research/functional work package. Keep #3 open pending selected-runtime/core boot and full-dataset correctness.
2. Claim #16 separately for gem5 full-system Linux correctness. Prepare sufficient consistent guest RAM and exact image/toolchain provenance.
3. Demonstrate selected BOOM/Chipyard Linux configuration and full-dataset v1/v2 correctness before accepting core feasibility.
4. #8 controlled hardware host, #10 real synchronized meter and #11 counters remain externally blocked; #13 still needs independent importer acceptance. M1 is open.
5. #14 M4 calibration still depends on #1/#3; #12 M5 remains gated by #1/#3/#14.

No core RTL simulation, calibrated timing, dynamic hardware bottleneck, wall-power samples or hashes/J advantage has been established. QEMU functional results are real execution under emulation, not hardware performance. Read current #3/#16 receipts and branch/PR state before further edits.
