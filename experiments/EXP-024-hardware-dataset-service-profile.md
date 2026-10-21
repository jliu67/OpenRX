# EXP-024: hardware-dataset service-demand profile

[Task #72](https://github.com/jliu67/OpenRX/issues/72) extends the existing
[architecture tools](../tools/architecture/README.md) with a separately bound
compact profile of the [accepted default hardware-dataset result](../docs/validation/dataset-fullhash-20261020/README.md).
It reuses PR74's necessary-bound helpers without changing its original evidence,
portable bytecode windows, scheduling results or reproduction command.

The new fixture projects the accepted PR86 source `e8277c63504ef035bb82791263b6842c0cc51f51`,
tree `cb3e0615f9df861a081ba2cbb1d47c65603b84cd`, into reviewed aggregate
counts and complete clock vectors. Actual fixture bytes must match trusted
SHA256 `fb6a6302dd6c57e835515c9e23ad39e2462e41885dc92bc49b48b056e0e96130`
before accepted attribution. Strict schema, workload, native-comparison,
zero-live-provider, count and vector-closure checks remain additional gates.
Changed or malformed inputs retain untrusted provenance and no accepted report.

The observed per-hash links are distinct:

| Interface | Responses/hash | Minimum data B/response | Minimum data B/hash |
| --- | ---: | ---: | ---: |
| Logical VM dataset output | 16,384 | 64 | 1,048,576 |
| Prepared-cache response | 131,072 | 64 | 8,388,608 |
| Prepared instruction response | 58,376,192 | 8 | 467,009,536 |

These nested link payloads must not be summed as off-chip traffic. Instruction
replies also bundle reciprocal validity/index/value and transport fields; eight
bytes is only the raw instruction minimum. The 239-entry reciprocal table is
retained storage, not an independent transaction count. Cache/program placement,
local reuse, complete wire width, bank mapping, physical controllers and energy
remain unknown. Retained data capacities are 256 MiB cache, 32 KiB instruction
capacity, 1,912 B reciprocal values and 2 MiB mutable scratchpad per context, before
metadata/ECC/queue/macro overhead.

The 918,672,902 modeled outer clocks contain 874,905,600 dataset-availability
clocks, including 874,889,216 core clocks and 16,384 session-launch clocks.
The 873,676,800 superscalar-executor clocks are nested again inside that core
work. No nested quantity is added to the outer total. These modeled clocks do
not establish a physical frequency or alternative architecture's full-hash cost.

Existing envelope helpers supply 36 conditional Little's-law rows: three
interfaces, assumed 1/10/100/300 ns response latency and assumed 1/2/4 independently
ready requests per context. Readiness is not established by issue width.
Requested 1 MH/s is a target, not an achieved rate; the strict complete-machine
energy ceiling remains 2.5 mJ/hash. Physical service, complete wall power and
architecture gates remain unresolved when their required inputs are absent.

The explicitly approved [execution request](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6306625245)
ran only bounded analytical validation. All 86 architecture tests, including 19
new methods, pass; the historical comparison and sensitivity JSONs reproduce
byte-for-byte; the new CLI succeeds and all bound source bytes remain unchanged.
Separate independent result review accepts this bounded analytical result.
See [evidence and reproduction](../docs/validation/hardware-dataset-service-profile-20261021/README.md).
Publication-head review and applicable hosted checks remain separate gates.

No native/RTL workload or full hash was repeated. Original failed and accepted
results, raw scientific flags, sources and scientific criteria remain unchanged.
Task #72 remains open. A finite shared dataset-service experiment with explicit
client identity and native value checks is a next bounded candidate, subject to
current task scope and admission; no production engine count, memory technology,
physical PPA, frequency or whole-machine performance is selected or accepted.
