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

PR #17 adds standalone SIGILL recovery, RW/RX page-permission and generated-code overwrite/cache-flush controls. Actual native and QEMU RV64GC execution passes nine controls each; existing 39 exact RandomX controls remain passing. Separate review and digest-checked CI streams are in docs/validation/m3-fs/RUNTIME-CI.md. Permission transitions may synchronize instructions, and QEMU self-modification handling is distinct from hardware. These results prepare #16; they do not complete gem5 boot, selected-core feasibility, full dataset or M4 timing calibration.

## Pinned full-system preparation and build outcome — 2026-10-08

Draft PR #18 adds a separately reviewed one-core AtomicSimpleCPU/classic-cache
Linux recipe with RVV off and 4 GiB backing, exact guest resource preparation,
digest-checked payload transfer, strict independent oracles and bounded CI.
Firmware/kernel/disk preparation and static ELF/guest-library checks actually
ran. Seven wrapper tests and ten explicitly synthetic independent failure
controls pass; they do not execute Linux.

The local canonical source build reached three six-worker 20-minute limits
without observed compiler source errors or OOM, but did not link a simulator binary.
Both hosted cold builds reached their 45-minute limits; all guest stages were
skipped. No gem5 Linux boot, runtime control or RandomX hash was executed.
[Results and complete build evidence](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/README.md)
retain exact inputs, commands, versions, source consistency and failures.
Task #16 remains open for incremental/larger-budget build and actual runtime,
then complete unchanged light controls before full-dataset/intended-core work.

## Successful simulator reuse and actual Linux runtime — 2026-10-08

The earlier build-only failure record above is historical. One canonical incremental resume finished compilation, then hit the 8-GiB host linker limit. Upstream low-memory linking recovered in 248.76 seconds without source/configuration changes; all 10,933 archived source files match. The exact original simulator and its source/runtime/provenance are saved for reuse; no further cold build is needed. [Recovery](../docs/validation/m3-fs/link-recovery-20261008/README.md), [reuse recipe](../docs/validation/m3-fs/REUSE.md).

Real Linux 6.8.12 boot and all nine standalone RV64 runtime oracles pass on one Atomic core, RVV off, classic caches and 4 GiB mapped RAM. Independent review replayed exact serial frames, zero status/empty stderr/completion, hypercalls1/2/3 and source/executable/resource/payload bindings. [Actual run](../docs/validation/m3-fs/actual-runtime-20261008/README.md), [separate acceptance](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md). Host elapsed time and memory are resource observations only.

The separate unchanged light attempt timed out at its 1,200-second child bound after repeating all nine runtime controls and verifying/launching the hash ELF. It exposed no complete hash result; independent replay verifies inputs and the timeout, not a hash mismatch. [Light outcome](../docs/validation/m3-fs/ACTUAL-LIGHT-REVIEW-20261008.md). Task #16 stays open. A separately reviewed stdout-streaming repair now preserves flushed progress on future timeouts; its host tests and actual old-runner evidence are explicitly distinct. Runtime controls do not isolate cache-flush causality or prove SMP/migration, full-dataset, intended timing-core or RTL compatibility. The new manual hosted builder/cache/reuse workflow is reviewed and offline-tested but has not run end to end. Preserve M1/M3/M4/M5 gates and every earlier failure record.

## Extended partial guest and execution-budget proof — 2026-10-09

PR #25's independently reviewed lifecycle repair merged at `abe066f7c1b17cb3225b55cc45848a153a20ea7a`, with the tested `9d108c4` tree unchanged. Local 253 Python / 34 gem5 controls and five hosted source-head checks passed; independent native/QEMU artifact replay remains separate from actual gem5 execution. [Lifecycle/CI records](../docs/validation/m3-fs/cancellation-20261008/README.md).

The exact retained simulator, resources and runtime/hash ELFs were reused for one extended unchanged guest with no wall timeout. It independently passed nine runtime controls and 31 integer/FP controls, but emitted zero hash values and only interpreter cache-init begin. A static exact-ELF/Atomic audit establishes that both mandatory cache round loops alone require at least 10,519,287,679,000 ticks, exceeding the `10^13` per-call allowance. This is an execution-budget proof, not an observed timeout or performance result.

Root requested manual tool-session cancellation after that proof. No final runner report was produced; handler receipt, simulator child code and runner reaping are unknown. No matching processes remain. No actual wall/tick exit or hash mismatch was observed. [Saved raw/post-input evidence and separate partial acceptance](../docs/validation/m3-fs/light-resume-20261008/README.md), [accepted budget proof](../docs/validation/m3-fs/light-resume-20261008/BUDGET-REVIEW.md). Historical failures and their source bindings remain unchanged.

The next unchanged matrix declares an explicit larger finite `10^14` guard; manual CI uses it for light controls and retains `10^13` for runtime-only work. New optional stop-file controls are separately reviewed host behavior and were not exercised by this actual attempt. Complete 39-control light hashing, full dataset, intended-core/SMP coherence and BOOM boot remain open, alongside M1 measurements and M4/M5 calibration/RTL gates.
