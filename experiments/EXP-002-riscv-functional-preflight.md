# EXP-002 — scalar RISC-V functional preflight and M3 selection

Session: `codex/20261008-m3`; base `d9e41cd07766e9c990641605dff1145d2f035d7d`.
Task: [#3](https://github.com/jliu67/OpenRandomX/issues/3). RandomX revision:
`aaafe71322df6602c21a5c72937ac284724ae561` (unmodified v2.0.1).

## Question and scope

Can the unchanged scalar RISC-V interpreter and JIT produce the pinned v2 and
v1 hashes in an executable Linux environment, with required integer and FP
semantics intact? Which open core/model is a justified next research target?
This is independent M3 feasibility work. It neither satisfies M1 measured
hardware acceptance nor M4 calibrated timing, and does not authorize M5 RTL
optimization.

## Fixed configuration

- Cross compiler: GCC 14 `riscv64-linux-gnu`, baseline `rv64gc`, ABI `lp64d`.
- Upstream `ARCH=default`; no configure-time native ISA discovery.
- QEMU Linux user mode: `-cpu rv64,v=false -L /usr/riscv64-linux-gnu`.
  RVV is disabled at execution, including automatic vector-JIT selection.
  Upstream nevertheless builds its optional vector/AES objects; GCC 14 and a
  compatible assembler must support those intrinsics/instructions.
- Light mode: 256 MiB cache, no full dataset, ordinary pages, software AES.
- Cache key `test key 000` (12 bytes); inputs `This is a test` (14 bytes) and
  `Lorem ipsum dolor sit amet` (26 bytes), lengths exclude null terminators.
  References: pinned `src/tests/tests.cpp`, `test_a` and `test_b`.
- Required: integer wraparound and high-half multiplication; rounding-sensitive
  scalar operations in all four RandomX modes; v2 then v1 interpreter/JIT,
  each with both inputs. A second input regenerates JIT code in the same VM.
- Native controls exercise the same probe. They do not prove RISC-V execution.
  Optional hardware AES is outside the scalar QEMU acceptance matrix.

## Commands

On Ubuntu 24.04 with authorized ordinary development packages:

```bash
sudo apt-get update
sudo apt-get install -y cmake gcc-14-riscv64-linux-gnu g++-14-riscv64-linux-gnu qemu-user
python3 scripts/verify_vendor.py
cmake -S simulator/probe -B build/probe-native -DCMAKE_BUILD_TYPE=Release -DARCH=default
cmake --build build/probe-native --target openrx-riscv-probe --parallel 2
python3 tests/native_riscv_probe.py --binary build/probe-native/openrx-riscv-probe \
  --output-dir build/riscv-validation/native
cmake -S simulator/probe -B build/probe-riscv -DCMAKE_BUILD_TYPE=Release \
  -DARCH=default -DCMAKE_TOOLCHAIN_FILE="$PWD/simulator/toolchains/riscv64-linux-gnu.cmake"
cmake --build build/probe-riscv --target openrx-riscv-probe --parallel 2
python3 tests/native_riscv_probe.py --binary build/probe-riscv/openrx-riscv-probe \
  --qemu qemu-riscv64 --sysroot /usr/riscv64-linux-gnu \
  --output-dir build/riscv-validation/qemu
```

Every invocation needs a new output directory. The wrapper rejects overwriting
evidence, non-RISC-V ELF input to QEMU, incomplete/mismatched hash matrices,
failed required checks, inconsistent summaries, subprocess errors and timeout.
Raw JSONL, stderr, binary SHA-256, exact command and outcome survive failure.
The [CI workflow](../.github/workflows/riscv-preflight.yml) retains compiler/
emulator/package versions, ELF attributes, linked disassembly, configuration,
binary and logs for 90 days. Record observed versions rather than claiming the
distro emulator equals the reviewed upstream release. Package repositories and
hosted runner images can change; this is a recorded environment, not a frozen
container/toolchain.

## Acceptance and follow-on gates

1. Full vendor integrity check passes in the real checkout.
2. Required native controls and scalar RISC-V controls pass; inspect actual
   logs, ELF identity, versions and independent reference comparisons.
3. Before declaring exact candidate compatibility, repeat upstream suite and
   full-dataset controls on that candidate configuration. Light mode has
   different dataset behavior and cannot establish memory-system feasibility.
4. Before accepting M3, demonstrate an exact selected core/simulator runtime
   or boot path, JIT cache coherence, FP correctness and supported ISA. Address
   the gem5 SE cache-flush syscall gap or use a validated full-system path.
5. M4 still requires a controlled native baseline and model calibration with
   uncertainty. QEMU has no calibrated cycle/power model; gem5 generic O3 is
   not BOOM, C920 or SG2042. Keep #3/#14/#12 acceptance separate.

## Result record

See [M3 validation](../docs/validation/m3/README.md) for executed outcomes,
failures, skipped paths and review. Candidate source analyses are
[core feasibility](../simulator/CORE-FEASIBILITY.md) and
[simulator feasibility](../simulator/SIMULATOR-FEASIBILITY.md).


## Explicit Linux runtime controls — 2026-10-08

PR #17 adds standalone SIGILL recovery, W^X and generated-code overwrite/cache-flush controls. Actual native and QEMU RV64GC execution passes nine controls each; existing39 exact RandomX controls remain passing. Separate review and digest-checked CI streams are in docs/validation/m3-fs/RUNTIME-CI.md. Permission transitions may synchronize instructions, and QEMU self-modification handling is distinct from hardware. These results prepare #16; they do not complete gem5 boot, selected-core feasibility, full dataset or M4 timing calibration.
