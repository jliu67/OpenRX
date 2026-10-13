# EXP-010: Native program initialization and sequencing

[Task #62](https://github.com/jliu67/OpenRX/issues/62) extends exact independently
accepted, unmerged PR61 `7f299c74f81332257eefd775086b355969ad85f3` with two
small control/wrapper modules. The [design](../rtl/execute/PROGRAM_SEQUENCE.md)
defines native initialization, eight-program/2,048-iteration sequencing,
DUT-derived external program generation and tagged held/reset/error semantics.

Initial evidence: four native-generated eight-program × four-iteration v1/v2
ideal/stalled RTL pilots pass; v2 clocks 110934/185396 and v1 70110/120864.
All registers/round/control, bytecode accesses, dataset/prefetch addresses, tail
stores and all 2 MiB per program agree with the pinned native reference.
[Evidence](../docs/validation/program-sequence-20261013/README.md) retains exact
inputs, commands, logs, resources and both fixture failures.

The single admitted full native-v2 8×2048 run is active, not passed. The new
reproducible driver, default full-count control contract, connected cancellation,
actual synthesis and mapped tests are pending. Independent review remains
required. Full actual dataset/hardware hash, full v1 8×2048 and calibrated physical
PPA remain open; software initialization/generation/BLAKE2b/finalization and
fixture dataset are explicit boundaries. No merge is authorized.
