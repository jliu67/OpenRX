# EXP-005 — iteration scratchpad and execute-memory integration

Status: implemented and locally differential/mapped validated; independent review
of new work pending. [Task #52](https://github.com/jliu67/OpenRX/issues/52).
Parent source is merged main `5a688512041eb3c156ead207eb57ed83e375a5d2`.

## Implemented boundary

The [iteration engine](../rtl/engine/README.md) implements entry R/F/E loads and
exact signed32-to-binary64 conversion, a tagged execution request/return with
ordered scratchpad memory access, dataset read/prefetch and mx/ma feedback,
dataset-line XOR and the unchanged AES/store tail. The external arithmetic
kernel must execute exact pinned bytecode; the external adapters must provide
private committed SRAM and tagged dataset lines. Instruction fetch, arithmetic
execution and physical memories are not part of this RTL. E masks, program
address and the current/final rounding mode cross the execution boundary.

This is owner-directed next-component implementation, following independently
accepted and merged PR49/51. All previous core/tail/vendor source and evidence
remain unchanged. It does not accept a full selected core, calibrated model,
physical PPA or full RandomX hash.

## Differential and resource results

The native reference executes six licensed include files containing verbatim functions/bodies and the
unchanged pinned BytecodeMachine with fourteen controlled instruction families,
including real memory instructions and CFROUND. It runs 16 v2 and 16 v1 full-size
program iterations (384/256 instructions), including 16 chained contexts and
eight entry-line aliases. It records 2,880 actual 64-bit bytecode reads and 720
stores. Each hardware run replays that traffic, commits 256 tail writes and
compares all 2 MiB of final scratchpad plus per-iteration architectural state,
dataset addresses and rounding feedback. This is a declared deterministic
dataset-line fixture, not full-dataset execution or a trusted full-hash oracle.

All eight RTL modes pass: A/B/C at LANES=4 and C at LANES=1, with minimum-latency
or stalled ports. Both actual LANES=4 A/C mapped netlists pass both port modes
with byte-identical result/cycle logs to RTL. Every mode checks three reset aborts,
including one already committed partial bytecode store. Stalled modes also
inject stale SRAM/dataset/execution traffic and block premature kernel return
until the final memory operation drains. A separate 4,096-vector native SIMD
differential verifies the signed conversion at edges, powers, random bit patterns
and all four rounding modes. Invalid conversion/coalescing parameters are rejected.

| LANES=4 configuration | Entry reads across 32 iterations | Entry clocks | Whole controller/replay clocks | Generic cells | Flop cells |
| --- | --- | --- | --- | --- | --- |
| A | 256 | 1056 | 7953 | 126810 | 7733 |
| B | 256 | 544 | 7441 | RTL only | RTL only |
| C | 224 | 480 | 7377 | 130589 | 6704 |

A shares one converter; B uses sixteen converters; C also coalesces equal private
entry lines. Under the specified one-clock response port, conversion saves 16
entry clocks per iteration (33→17 with different lines). Each alias saves four
128-bit commands and eight additional clocks (17→9); the deliberate eight-alias
fixture reduces 256 entry reads to 224. These are control/port-model results.
Whole replay clocks include replayed memory traffic but exclude actual arithmetic
kernel execution latency. No natural alias-frequency, clock-frequency, hash-rate,
physical-area or power conclusion follows. Generic cells include the old tail
but exclude arithmetic execution, SRAM/dataset/cache macros and technology PPA.

## Reproduction and retained evidence

```sh
python3 scripts/test_iteration_engine.py --output /tmp/openrx-engine-fresh --synthesize
```

Use a fresh output outside the temporary source and the designated host's shared
slot with fresh admission. [Evidence](../docs/validation/iteration-engine-20261013/README.md)
binds every input, verbatim extraction, native trace, image, tool version, command,
complete log, actual mapped netlist and raw/public export. Compiler is g++11.4,
Icarus11.0 and Yosys0.9. No local dependency install or settings change was needed.

One sequential payload used kernel-verified CPU600%, RAM4 GiB, swap512 MiB and
Tasks128, six-CPU affinity and no tighter visible ancestors. Fresh available
memory exceeded the allocation plus a 1 GiB reserve. Single-threaded tools used
one worker: peak RSS 2,630,284 KiB, observed CPU
100%, elapsed 21:26.88. The allocation
was justified by the previous measured synthesis peak and this added controller;
all six cores remained available. Detailed host witnesses stay private. The
payload/descendants drain and the global lock is released before handoff.

The first reset helper missed an accepted read and failed its prefix timeout.
The preserved failure was a testbench sampling error; corrected development and
the complete final RTL/mapped matrix pass. A one-off Python generator typo before
artifact creation was corrected. All earlier source, binaries, attempts and
receipts remain retained. New source and raw outputs are archived and verified;
temporary authoring is retired read-only at publication. No standing clone or
Git synchronization is created. Independent review of this new work is the next
gate; a code merge is not authorized.
