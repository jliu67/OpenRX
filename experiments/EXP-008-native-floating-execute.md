# EXP-008 — exact native floating execution and CFROUND

Status: all twelve RTL and eleven applicable mapped modes pass; new independent review pending.
[Task #58](https://github.com/jliu67/OpenRX/issues/58) stacks on independently
accepted, unmerged PR #57 at d62c449. The parent heads remain unchanged and no merge
is authorized. [Design/interface](../rtl/execute/FLOATING.md) and upstream byte
manifest describe the concrete HardFloat1/8086-SSE choice, exact masks, native
DAZ/FTZ/NaN behavior and version-dependent CFROUND. Division/square-root remain errors.

| FP vector | Ideal integrated clocks | Ideal execute interval | Stalled integrated clocks | Stalled execute interval |
| --- | --- | --- | --- | --- |
| Shared one lane | 16604 | 16396 | 33574 | 32918 |
| Parallel two lanes/default | 13116 | 12908 | 30086 | 29430 |

Difference is 3,488 clocks in either model/interval, exactly four per 872 arithmetic
FP instructions. Unit response-handshake latency is five/shared versus one/parallel.
Standalone shared mapping is 26,522 generic cells/571 flops; parallel is 49,363/156.
Shared saves 22,841 generic cells while adding 415 flops and four clocks per vector FP
instruction. These are controlled fixture clocks and generic mappings, not calibrated
clock, physical area/power, natural instruction mix or full-hash throughput.

Unchanged native compiler/execute/reference operations supply assertion-only
2,928 R/F/E/rounding retirements, target/PC/memory traces and all 2 MiB. Twelve RTL
modes cover the complete declared opcode set, primitive full/curated matrices,
errors/reset/stalls/raw-field transport. Actual mapped tests verify both variants'
3,840-vector corner corpus and connected ideal/stalled/error runs, comparing exact
PASS/cycle records. Complete default mapping is 260,110 generic cells/9,826 flops; all three complete mapped native/error records equal RTL.
Shared whole-top
synthesis and expanded old integer sharing variants are absent.

All 171 RandomX sources, eleven unmodified licensed HardFloat sources and accepted
AES/tail/controller/converter bindings 19/17/22 are verified. Two wrapper-boundary
failures and the strict five-raw-variant fixture correction are preserved with exact
source/output/hash/archive provenance. Original/pinned sources, builds, data and
receipts remain retained. Full source/commands/tools/licensed logs/fixtures/netlists/
measured resources accompany the stacked draft and new independent review.


The unit payload used actual checked CPU 600%, 2 GiB RAM, 512 MiB swap, Tasks 128,
six-CPU affinity, one worker and fresh 1 GiB OS reserve. Its measured cgroup peak
was 1,114,402,816 bytes, zero swap/OOM/limit hits/quota throttles.
Default integration rejected the 7.5 GiB candidate on fresh headroom, admitting
6.5 GiB RAM/2 GiB swap under the same CPU/tasks/worker/ancestor checks and 1 GiB reserve.
Measured integration peak 6,979,321,856 bytes, swap peak 1,136,898,048 bytes; memory-limit
events 1202, OOM/kills 0, CPU throttles 0. Complete raw
timing and sanitized counters retain actual pressure/duration (integration 39m32s); both payloads and
descendants drained. One largely serial tool worker dominated CPU use; all six
cores were available. [Licensed evidence](../docs/validation/floating-execute-20261013/README.md)
retains raw/public hashes, complete archives, actual netlists and all earlier attempts.
