# EXP-006 — actual native integer bytecode execution

Status: implemented; native/RTL, actual kernel mappings and complete default-top
mapped validation passed locally
for [task54](https://github.com/jliu67/OpenRX/issues/54). New-work independent review
remains required; no next merge is authorized. Parent main is
`a6450ceccd32848c438c7dcae6acb98695d2a0e8`.

The [integer executor](../rtl/execute/README.md) implements actual instruction
fetch, weighted decoding, eleven integer families and ordered memory access behind
the unchanged accepted iteration controller. This replaces software register
result replay for the declared subset. All 158 other raw opcodes trap explicitly;
FP/CFROUND, multiply/reciprocal/high multiply and branches remain unsupported.
ROM, private SRAM and a declared dataset-line model are external. This is not a
complete RandomX VM, selected RISC-V core, full-hash or calibrated-PPA result.

The unchanged pinned native compiler/interpreter supplies assertions for eight
controlled full-size programs: four v2/384 and four v1/256, four chained contexts,
four line aliases, 2,560 actual instruction retirements, 700 loads, 228 stores and
64 tail writes. Hardware fetches actual ROM words, reads actual addressed SRAM,
computes integer results, commits its own writes, performs dataset feedback and
runs the existing AES/tail. Golden states are not executor inputs. Every instruction,
memory event, architectural result and all 2 MiB final bytes are compared.

Coverage includes all98 supported raw values, rotate0–63, shifts0–3, L1/L2/L3 masks,
127 addition wraps, 126 subtraction wraps, 28 R5 displacements, 160 equal-register
immediate forms, 80 equal-register swap NOPs, 240 zero-base L3 loads, 116 lower-half
and 112 upper-half stores. Imm32 includes0/1, negative values, INT32_MIN/MAX,
rotation edges and address/overflow patterns. Both schedules reject all158 other
values, hold160 error records, restart on error acknowledgement, reset held fetch,
pending load and held uncommitted store, discard late replies and retain committed
prefix writes. Stalled modes inject2,560 old ROM,748 old SRAM and eight old dataset
responses while checking stable command/retirement payloads.

| Schedule | Ideal integrated cycles | Ideal fetch-to-last-commit cycles | Stalled integrated cycles | Stalled execute interval |
| --- | --- | --- | --- | --- |
| Two-add fast/default | 9524 | 9316 | 26712 | 26056 |
| Shared addition | 9760 | 9552 | 26948 | 26292 |

Fast IADD_RS saves one actual execution clock per instruction:236 across these
programs, with the same236-cycle difference in both execute and whole-iteration
intervals under both port models. Only IADD_RS sharing is claimed, not a shared
whole ALU. Fetch/memory model latency is included, and no natural workload mix,
clock-frequency, hash-rate or physical-power conclusion follows.

Generic standalone synthesis has completed: fast25,885 cells/1,727 flops; shared
25,925/1,792. Sharing uses40 more generic cells and65 more flops in these actual
mappings, so sharing is not an area improvement. The fast schedule is236 clocks
shorter and has40 fewer generic cells; physical critical paths remain unmeasured.
The complete default top has154,145 cells/7,921 flops. Both actual kernel mappings
and the fully mapped top pass their supported/error/reset tests with the same
responses and cycle records as RTL. Kernel-only and integrated counts must not be
conflated; physical memories remain external.

Reproduce from a temporary source with fresh output and required compute admission:

```sh
python3 scripts/test_integer_execute.py --output /tmp/openrx-integer-fresh --synthesize
```

Both actual kernel mappings are validated through the unchanged RTL controller;
the complete default connected top also has its own actual mapped validation.
Shared whole-top synthesis is not delivered. The complete command/tool/input/log,
license, fixture, failure and netlist retention index is supplied with the draft.
The current one-worker payload is kernel-verified CPU600%, RAM5GiB, swap512MiB,
Tasks128 with six-CPU affinity and no tighter visible ancestors; fresh observed
MemAvailable was7,528,636,416 bytes and required1GiB headroom was retained. The completed29m20s payload had peak RSS3,821,160KiB and cgroup peak5,080,702,976
bytes, zero swap, no OOM/max events and no CPU-quota throttle; the main exited0
and cgroup had only the guard before release. Final no-descendant/slot checks
follow. One worker reflects single-threaded Yosys/Icarus and bounded worst-case
integrated memory; all six CPUs remained available. Every old
component/vendor/source/result/receipt is preserved; no install/access/settings
change, baseline rerun, force push or code merge.
