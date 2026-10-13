# EXP-007 — native multiply, reciprocal and conditional branch hardware

Status: all nine RTL and eleven applicable mapped modes pass; independent new-work review pending.
[Task #56](https://github.com/jliu67/OpenRX/issues/56) stacks on independently accepted,
unmerged PR #55 exact `2b14e4f9a726c1f7e066576bbe8fc351c87d158c`. That head is preserved;
this new work needs its own independent review and no merge is authorized.

[Design/interface](../rtl/execute/MULTIPLY-BRANCH.md) adds seven multiply/reciprocal
families and CBRANCH to the existing native executor. All 161 integer/branch raw values
are now supported. The remaining 95 FP/CFROUND values still trap. Complete VM/hash,
selected-core, physical-memory and calibrated-PPA gates remain open.

The unsigned product supplies low and unsigned high, with exact signed-high
correction; direct and radix-4 iteration are selectable. The 64-step reciprocal
uses native floor semantics; zero/power-of-two divisors are actual NOPs. Lexical
first-visit usage tracks native branch compilation independently of replayed
instructions; each branch marks all registers used, so one latest target cache
suffices. No predecoded/golden targets or arithmetic results enter hardware.

Eight controlled full-size programs execute 2,736 native/hardware instruction steps,
580 multiplications, 218 branches/90 taken jumps, 562 loads, 272 stores and 64 tail writes.
Four chains/four aliases, every retirement, native target, nextPC, memory event,
architectural result and all 2 MiB match. All 161 raw values, all 64 rotations/four shifts,
three memory masks and sixteen branch condition shifts are covered. Branch cases
include target−1/jump-to-zero, self-loops, consecutive barriers, fallthroughs,
one/two-taken loops and repeated actual stores. Both stalled modes inject 2,736 old
ROM, 610 old SRAM and eight old dataset replies while checking held payloads.

Native primitive vectors separately compare 2,304 low/unsigned-high/signed-high
products and 609 divisors/all 33 NOP classes, held replies/inactive inputs and reset.
Error modes retain all 95 unsupported raw values and 97 held errors, abort/restart,
reset held fetch/pending load/store and now multiply/reciprocal cancellation,
late packets and committed-prefix persistence. The reviewed four-rounding-mode/
raw-FE/held-return transport test still passes; no FP execution is claimed.

| Multiplier | Ideal integrated clocks | Ideal execute interval | Stalled integrated clocks | Stalled execute interval |
| --- | --- | --- | --- | --- |
| Direct/default | 12036 | 11828 | 29502 | 28846 |
| Radix-4 iterative | 30596 | 30388 | 48062 | 47406 |

The actual difference is 18,560 clocks in either port model and interval, exactly
32 per multiplication. Unit request-to-response-handshake latency is 1/33 clocks;
non-NOP reciprocal is 65. These controlled fixture/port clocks do not infer a
natural instruction mix, production frequency or full-hash throughput.

Actual local Yosys 0.9 standalone direct multiplier is 25,723 cells/81 flops; iterative
is 5,528/537. Iteration saves 20,195 generic cells while adding 456 flops and 32 clocks
per product. Reciprocal is 1,374/153. Direct is the latency-oriented default; the
iterative option exposes the area/latency tradeoff. Critical-path, physical area,
clock/power and full-system efficiency remain unmeasured. The complete default top
is 189,296 generic cells/8,396 flops. All three complete
mapped connected/error tests match RTL results and clocks. Iterative whole-top
synthesis is not delivered; both actual mapped arithmetic variants separately
run native primitive and connected/error tests with the RTL controller/executor.

```sh
python3 scripts/test_integer_multiply.py --output /tmp/openrx-multiply-fresh --synthesize
```

The first expanded fixture lost inherited rotate coverage because multiply/branch
changed register distribution. Strict coverage rejected it before RTL execution.
Its complete source/output remains preserved and source archived/read-only. Adding
64 explicit native rotate instructions retains the strict check, changing no RTL.
All earlier PR #55 and controller/converter/AES/tail/vendor sources/inputs/results/
receipts/builds remain retained. New source and all failures/outputs/tool versions/
commands/licenses/netlists/resource witnesses are retained and archived at handoff.

Completed full single-worker payload used kernel-verified CPU 600%, RAM 6 GiB, swap 512 MiB,
Tasks 128, six-CPU affinity, no tighter visible ancestors and fresh 1 GiB OS reserve
from 7,883,431,936 bytes MemAvailable. Measured peak cgroup memory is
5,853,196,288 bytes; peak swap 0 bytes.
Kernel events show no OOM/memory-limit hits or CPU quota throttling. Both payloads
and descendants drained, and the shared slot is released. Complete raw timing
and sanitized resource counters accompany [the evidence](../docs/validation/multiply-branch-20261013/README.md).
No settings/access/install/security/spending, baseline/audit, force push or merge.

The initial serialized driver completed all RTL, mapped-unit/connected modes and
whole-top synthesis, then terminal disconnection raised BrokenPipe at its progress
print (rc120). This transport failure is preserved. A fresh checked 1 GiB mapped-only
completion reused the exact netlist and frozen inputs for the remaining three tests
(rc0), with durable console logging and no repeated synthesis. It peaked at
1,013,276,672 cgroup bytes, with zero swap/limit hits/OOM/quota throttles. Full
run/completion elapsed times are 19m05s/9m29s. One compiler/simulator worker
dominated CPU usage; all six CPUs were available without quota throttling.
