# M3 validation — executable scalar preflight, source-backed selection

Session `codex/20261008-m3`; [PR #15](https://github.com/jliu67/OpenRandomX/pull/15), task [#3](https://github.com/jliu67/OpenRandomX/issues/3). Reproduction and exact inputs are in [EXP-002](../../../experiments/EXP-002-riscv-functional-preflight.md). Vendor RandomX remains unchanged.

## Executed controls

| Environment | Actual result | Scope |
|---|---|---|
| Local x86-64/GCC13 manual build | 39 required pass, eight exact software-AES hashes; one optional skip | Native functional; no RISC-V execution locally |
| Initial CI native CMake/GCC13 | 39 required pass, eight exact software-AES hashes; one optional skip | Same C++ probe, native correctness only |
| Initial CI RISC-V/GCC14 under QEMU8.2.2 | 39 required pass, eight exact software-AES hashes; one optional skip | Scalar emulation/light mode; no cycles/energy/full dataset |
| Local Python suite | 199 tests pass, no unittest skips | Existing 182 + 17 evidence rejection tests |
| Existing initial foundation CI | Source/build/profile/references/upstream/native steps all pass | Existing regression coverage, no measured baseline |

Initial implementation: `e5eafde50d074f19afb37d08ccec4c59dd88a33d`.
Actual [RISC-V run 37790683112](https://github.com/jliu67/OpenRandomX/actions/runs/37790683112), job113356939599; existing [foundation run37790683131](https://github.com/jliu67/OpenRandomX/actions/runs/37790683131), job113356939659. The PR-triggered checkout records merge SHA `107ac39232a6a2cc470415eae90a9d64237779ce`, while workflow head is the implementation SHA. Initial raw stream was locally replayed against the stricter reviewed validator. Final CI outcomes are posted on #3/PR #15.

Required matrix: seven integer wraparound/high-half multiply checks; six scalar FP checks per rounding mode (readback, positive add, negative subtraction, multiply, divide, sqrt); two input hashes per v2/v1 and interpreter/JIT. Counts=39 required plus one optional hardware-AES skip. Hardware AES was not requested, not silently treated as verified. Native and RISC-V log records preserve exact inputs, hashes, flags and FP bits.

## Audited archive and retained evidence

Downloaded artifact11555544301, 452645 bytes; actual SHA-256 matched GitHub:
`5f042957866115a6eeb488953ec8d52c892896fd359353efac9da9d9334fadcb`.
Expires2027-01-06T14:13:21Z. Root independently extracted it and ran current
`validate_output(..., expect_riscv=True)` against the QEMU stream.

The downloaded linked binary was ELF64 little-endian RISC-V, e_machine243.
Its digest matched report:
`61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`.
The exact execution command is in [report](ci-qemu-initial-report.json);
raw [JSONL](ci-qemu-initial.jsonl), [ELF metadata](ci-elf-initial.txt),
[environment](ci-environment-initial.txt), [local probe](local-native.jsonl),
[local report](local-native-report.json) and [Python log](local-tests.log)
are committed. No CI binary is duplicated into vendor/source history.

Observed cross GCC14.2.0, binutils2.42, QEMU8.2.2 package
`1:8.2.2+ds-0ubuntu1.18`, sysroot libc2.39; native GCC13.3.0.
The CMake executable was3.31.6 even though dpkg's installed cmake package
was3.28.3: record both rather than equating package inventory with PATH.
Reviewed upstream QEMU11.1.2 is a source-research pin, not the executed emulator.
Build logs/disassembly/ELF attributes are in the artifact. Scalar runtime CPU
has V disabled although dormant vector/crypto objects are linked.

## Review fixes, local limitations and failures

[Independent review](REVIEW.md) checked exact FP oracles, hash constants,
library/VM flags, cross-build source support, licenses, SIGILL/cache-flush
runtime assumptions, and evidence rejection. Initial review found successful
streams would be rejected because stage records were not yet accepted; this
was fixed before the first native execution and first published implementation.
Subsequent review hardened independent semantic/config/flag binding and
malformed-record handling, and enabled compile_commands export. 17 mutation
regressions exercise these rejection paths; they are not target measurements.

Local CMake, RISC-V compiler and QEMU were unavailable. Native library was
manually compiled with GCC13, C/C++ source list from pinned CMake, x86 JIT
assembly, -O3 -DNDEBUG -fPIC -maes, plus per-file -mssse3/-mavx2; probe
used C++17, -O3 -DNDEBUG -Wall -Wextra -Werror -frounding-math
-fno-fast-math -ffp-contract=off and linked librandomx.a with -pthread.
Its config accurately says build metadata unrecorded; this paragraph records
the actual manual command. The upstream assembly linker reported a GNU-stack
note warning; source was not changed.

All167 vendored UTF-8 source/text files matched their manifest bytes locally.
The connector refused four binary audit PDFs; full local verify_vendor failed
because those files were absent. Real CI checked all171 files successfully.
Initial Git clone failed due unavailable CLI authentication; connector reads
and Git object API writes supplied exact source and expected-head branch updates.

## Acceptance limits

Actual emulated correctness is established for this bounded scalar light path.
Selected BOOM Linux boot, full-dataset RISC-V controls, gem5 functional runs,
vector/hardware AES, calibrated timing, wall power and hashes/J remain unexecuted
here. QEMU's automatic translated-code invalidation is not hardware cache
coherence evidence. gem5 SE startup signal recovery and cache-flush support
are unresolved; [#16](https://github.com/jliu67/OpenRandomX/issues/16) tracks
the full-system Linux investigation. M3/#3 stays open; M1/M4/M5 gates stay intact.
