# Iteration engine differential and synthesis evidence

[Task #52](https://github.com/jliu67/OpenRX/issues/52) adds the next architectural
boundary from merged main 5a688512. [EXP-005](../../../experiments/EXP-005-iteration-engine.md)
and [interface](../../../rtl/engine/README.md) define the implementation, contract
and measured control/resource comparison. Independent new-work review is pending.

[index.json](index.json) binds original and public digests. Gzip exports are
lossless; decompress and verify their raw SHA-256 before use. The complete raw
attempt, oracle binary and compiled simulation binaries remain preserved locally,
including development failures; no existing result was replaced.

[summary.json](summary.json) records eight RTL and four actual mapped modes,
the 32-iteration native memory differential and A/B/C comparison. [inputs.json](inputs.json),
[preserved-inputs.json](preserved-inputs.json), [extraction.json](extraction.json),
[commands.json](commands.json), [tools.json](tools.json), [resources.json](resources.json)
and [failures.json](failures.json) carry exact provenance, licenses, resource scope
and failed-attempt context. Compressed netlist A/C Verilog and JSON are the actual
local synthesis outputs, rather than regenerated examples.

Tests use the unchanged pinned native instruction implementations with controlled
full-size programs and a deterministic dataset-line provider. The hardware and
generic resource counts exclude the external arithmetic kernel, instruction fetch
and physical SRAM/dataset/cache. Controller/replay clocks are not full-hash
performance or physical timing/power. Broader scientific acceptance remains open.
