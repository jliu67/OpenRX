# Bounded native input BLAKE2b-512

`randomx_input_blake2b` reuses the accepted `randomx_blake2b_chain_core`
without changing its compression arithmetic or licensed IP. Its contract is
unkeyed BLAKE2b-512 for **0 through 80 input bytes**, inclusive. It is a bounded
input stage for the existing lifecycle descriptor, not an arbitrary-length
BLAKE2b engine.

The seven-bit length port can represent 0–127. Lengths 81–127 return a held error
with a zero seed and do not start compression. The interface cannot represent
longer messages; callers must reject them before constructing a descriptor.

## Native bytes and final block

Input byte zero is `req_input[7:0]`. The wrapper captures all input bits, the exact
byte count and the caller's 16-bit tag at request acceptance. Bytes below the
captured length are mapped to the compression core in native byte order; every
remaining byte through the end of the 128-byte block is zero. Unused input-bus
bytes are ignored, including poisoned nonzero tails.

All supported lengths use one final block, including an empty message. The
compression parameters are digest length 64, key length zero and twelve rounds.
The exact byte count is the final counter; `init` starts the block and `next` is
never asserted. There is no SHA-style suffix. Returned digest byte zero occupies
`rsp_seed[7:0]`.

## Ownership, backpressure and cancellation

One request is owned at a time. The captured block and length remain stable
through core initialization and computation. A separate start state clears the
core's previous held digest-valid before the wrapper observes a new result.

The response retains its seed, error and tag until accepted. Requests cannot
replace a held response. Synchronous reset or cancellation discards wrapper
ownership and resets the compression core; request/response valids are also
suppressed while either control is asserted. A caller must continue to enforce
its generation/tag reuse rules around external late traffic.

## Lifecycle integration and historical reproduction

`HARDWARE_INPUT_HASH=1` is explicit and requires `HARDWARE_FILL=1`; unsupported
parameter combinations fail elaboration and the reproduction CLI rejects them.
Default `HARDWARE_INPUT_HASH=0` preserves the historical software-assisted path.
`HARDWARE_PROGRAM` is a separate existing option.

The parent captures the descriptor, reserves a fresh generation and starts the
input wrapper. It accepts only a successful seed with the matching generation
before admitting hardware fill. The scratchpad owner is NONE during input
hashing, with no scratchpad request or write. Fill then obtains INIT ownership.
Reset/cancel/error suppresses the input wrapper and invalidates its ownership.

Hardware input mode removes the live external initialization provider: no
initialization request is emitted, and all late initialization writes/responses
are drained, including matching errors. They cannot provide a seed or fault the
current request. Native seed calculations in the bench are assertion-only, with
separate counts/times. Native Light dataset callbacks remain a live provider.

Outer phase 10 is the disjoint `input_hash` stage. Three nested observations
partition it into start/idle, computation and held return. Initial fill has its
own stage; removed host seed wait is not counted again in either stage. Producer
response stalls and native callback seconds are distinct observations.

## Validation boundary

Standalone source `307cc9ceef0328021aa7063b0930120b72884099` passes 614 native
vectors covering every supported length, four patterns per length, 162 poisoned
unused-tail cases and 128 arbitrary cases. Eighteen RTL modes include all 47
unsupported lengths and reset/cancel before start, early/middle/final computation
and held return, plus held request/result and changed-length restart. Sixteen
mapped modes use 26 boundary vectors and the corresponding control checks,
including unsupported lengths 81 and 127; mapped PASS records equal RTL records.

Valid request-to-response availability is 28 testbench clocks. Generic synthesis
of this wrapper and the unchanged compression core reports 38,538 cells, 3,753
flop cells and **1,024 inherited latch cells**. This includes the existing G
operand latches and excludes the connected engine, scratchpad and image buffer.

[Evidence](../../docs/validation/input-blake2b-20261016/README.md) and
[EXP-018](../../experiments/EXP-018-bounded-input-blake2b.md) retain exact sources,
commands, tools, fixtures, outputs and the initial oracle include-order failure.
Runner integrity verification is separate from independent scientific review.
Generic cell counts and simulated clocks do not establish physical area,
frequency, power, ASIC efficiency or a whole-machine target. A bounded connected
run does not replace the historical default 8×2,048 measurement.
