# EXP-012: native scratchpad finalization

[Task67](https://github.com/jliu67/OpenRX/issues/67) / [design](../rtl/hash/FINALIZATION.md).
Base is validated/frozen draft PR65 at `4f095fc147b5bc78de79746a0a172f38e34d6450`; independent acceptance is not established.

Hypothesis: one reused AES round unit can reproduce native scratchpad reduction
with a bounded held read/result contract; replacing A and applying independent
BLAKE2b-256 should agree exactly with pinned native finalization.

Acceptance: actual memory/raw R/F/E/A matching, all rounding transport, exact
ascending reads/last beat/tags, invalid-size/read errors, stale traffic, held
requests/results and reset/fresh-tag cancellation. Preserve unchanged accepted
execution/IP/native sources. Retain four balanced full2MiB RTL trials and separate
bounded mapped/partial default controls, actual default stage synthesis/cells,
commands/tools/licenses/resources and every failure. New independent exact-head
review remains required before any merge.

Result: 41 RTL / 19 mapped modes pass, with 14 native/Python cases,
four balanced full 2 MiB trials, six malformed-native guards and four invalid
parameter elaborations. Eleven staging/metadata successor checks pass.
Full ideal/stalled primary latency is 393,284 / 1,048,649 modeled clocks.
Actual default scanner/finalizer and bounded 256-byte generic mapping:

| Component | Scratchpad bytes | Generic cells | Flop cells | Latch cells |
| --- | ---: | ---: | ---: | ---: |
| scanner-default | 2,097,152 | 41,321 | 1,195 | 0 |
| finalizer-default | 2,097,152 | 100,485 | 8,958 | 1,024 |
| finalizer-bounded256 | 256 | 100,497 | 8,958 | 1,024 |

[Evidence](../docs/validation/scratchpad-finalization-20261013/README.md) preserves exact source/output/tool/resource
bindings and preparation failures. Hosted final-head validation and new
independent review remain required. These Yosys 0.9 cells are not calibrated PPA.

No selected core/full actual dataset/initial fill/program AES/full hardware hash
or physical PPA is accepted by this component. No full program-chain rerun.
