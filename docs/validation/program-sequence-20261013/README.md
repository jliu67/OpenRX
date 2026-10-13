# Native program-sequence evidence

[Task #62](https://github.com/jliu67/OpenRX/issues/62) stacks on exact independently
accepted, unmerged PR61 `7f299c74f81332257eefd775086b355969ad85f3`.
[Index](index.json) binds each original/public file and lossless gzip export.
All four v1/v2 ideal/stalled eight-program × four-iteration pilots pass.
The full native-v2 eight-program × 2,048-iteration RTL job and new control,
cancellation and mapped checks are pending at this initial draft.

No pending test is counted as a pass. The native preparation coverage only
characterizes the oracle input; it is not a completed DUT record. Both original
namespace/readiness fixture failures are retained. Pinned original sources,
builds, data and receipts remain preserved. There is no standing editable clone
or Git synchronization. The component boundary and exact commands are in
[the design](../../../rtl/execute/PROGRAM_SEQUENCE.md).

Native programs and the next seed are supplied by external pinned AES/BLAKE2b
consuming actual DUT register output. Initial scratchpad fill and final hashing
remain external; dataset replies use an addressed fixture. Full actual dataset,
full hardware hash, full v1 8×2048, calibrated physical PPA and independent review
remain unclaimed. No merge is authorized.
