# EXP-005 — iteration scratchpad and execute-memory integration

Current closeout (2026-10-13): [PR53](https://github.com/jliu67/OpenRX/pull/53)
is independently accepted and merged at `a6450ceccd32848c438c7dcae6acb98695d2a0e8`. The review-pending and original
source/count records below are retained historical author stages. Full-core/hash
and physical/calibrated-PPA gates remain open; task54 is separate new work.

## Read-grant correction after independent review — 2026-10-13

[PR53 review](https://github.com/jliu67/OpenRX/pull/53#pullrequestreview-5497704738)
blocked original bd193092: an arriving write could retract a scratchpad read
already held under backpressure. The same author reproduced the exact failure
on unchanged original RTL, preserved its source/test/input hashes/fatal log,
and added one retained read-grant bit. Fresh competing requests still give
writes priority; an already presented read retains valid/address/tag until
acceptance and blocks writes until the response is consumed. Reset/new descriptor
clears the grant; architectural return cannot bypass a pending grant.

The new directed regression runs v1/v2, overlapping requests in both orders,
12 read-stall clocks, eight write-stall clocks, six response-stall clocks,
six stale-generation drops and reset of a held grant. It verifies five reads,
three ordered byte-strobe writes and committed-byte persistence. It fails the
rejected RTL and passes all four RTL configurations plus both actual A/C netlists.
The eight native RTL and four native mapped modes remain byte-identical to the
original serialized replay; every native/vendor/AES/store-tail input is unchanged.
Entry totals A/B/C=1056/544/480 and native replay cycles are unchanged.

Corrected generic A/C counts are 126,820/130,599 cells and
7,734/6,705 flops. Compared with the rejected source,
deltas are +10/+10
cells and +1/+1 flops.
The original failing overlap sequence has no valid cycle result to compare.
[Focused evidence](../docs/validation/iteration-engine-read-grant-20261013/README.md)
binds raw failures, corrected source, commands/versions, actual netlists and
resource receipts, retaining every earlier source/result/archive/review.

The initial 4 GiB candidate did not fit fresh headroom. Standalone A synthesis
used kernel-verified CPU600%, RAM3 GiB, swap512 MiB and Tasks128, after a fresh
1 GiB host reserve check; measured memory pressure/swap increased wall time
without an OOM or CPU-quota throttle. Freshly regained headroom admitted C at
4 GiB. Mapped-only checks used 1 GiB based on measured compile/simulation RSS.
All six CPUs remained available, one worker, global slot serialized. Detailed
resource witnesses stay private; sanitized measured limits/peaks/elapsed/swap
are public. Source and attempts are verified/archived and retired read-only at
publication. Prior sources/receipts are preserved; no extra tasks/agents,
install/access/settings change, repeated baseline, force push or merge.

Next: all final-head hosted checks, then the same reviewer's focused delta review.
This author handoff does not establish acceptance or authorize merge. Arithmetic
kernel, physical memories, calibrated PPA and full-hash requirements remain
external. Earlier evidence below records its original source and is retained.

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
