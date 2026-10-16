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

The connected mode is explicit; historical software-assisted reproduction stays
the default. Hardware input hashing feeds the existing hardware initial-fill
boundary before any scratchpad write. Reference assertions and native Light
dataset callbacks remain distinct from live input-hash providers.

## Validation boundary

Focused native, RTL, mapped, recovery and connected evidence will identify its
exact executed source, commands, tool identities and retained outputs. Generic
cell counts and simulated clocks do not establish physical area, frequency,
power, ASIC efficiency or a whole-machine target. The inherited compression
core's latch count must be reported separately from flip-flops. A bounded
connected run does not replace the historical default 8×2,048 measurement.
