# Initial scratchpad AES fill

`randomx_initial_scratchpad_fill` replaces the initial host AES fill when the
connected lifecycle sets `HARDWARE_FILL=1`. The default `0` retains the legacy
provider interface for exact historical reproduction and paired comparisons.
This stage reuses the proven `randomx_aes_round` and unchanged licensed secworks
S-boxes. It supplies no new input hash, program generator or dataset provider.

## Pinned semantics

The input is the raw 64-byte BLAKE2b-512 result for the captured hash input.
The unchanged pinned RandomX `fillAes1Rx4` updates four independent 128-bit lanes
once per 64-byte group and writes their updated bytes directly to memory.
Lane 0 occupies bits `[127:0]`; byte 0 occupies bits `[7:0]`.

| Lane | Operation | Raw 128-bit key, most-significant hex digit first |
| --- | --- | --- |
| 0 | AESDEC | `b4f44917dbb5552b627166096daca553` |
| 1 | AESENC | `0da1dc4e1725d378846a710d6d7caf07` |
| 2 | AESDEC | `3e20e345f4c0794f9f947ec63f1262f1` |
| 3 | AESENC | `4916915416314c88b1ba317c6aef8135` |

There is no key expansion, pre-XOR, extra diffusion or last-round exception.
Directions are the opposite of the final scratchpad reduction. One shared
combinational AES round offers each 16-byte beat; the corresponding lane advances
only when that write is accepted. Backpressure holds address, data and tag.
The full 2 MiB image has 131,072 writes and 32,768 updates per lane. The returned
512-bit state equals the last 64 image bytes and drives actual program-0
generation. No assertion/oracle state drives that provider.

## Ownership and recovery

The core captures one seed/tag request, streams full-strobe ascending writes,
then holds its seed/tag response until accepted. No next request is admitted
while streaming or returning. Reset and cancellation suppress transfers and
abandon control; already accepted external SRAM writes persist. The caller owns
tag uniqueness and cancellation/reinitialization of the image.

The lifecycle retains its monotonically allocated hash generation and INIT
scratchpad owner through input hashing, fill admission, all writes and returned
seed validation. Program preparation/execution cannot start before those writes
complete. In hardware mode the host returns only the input-hash seed; matching
seed responses offered alongside request acceptance are held until the following
response-consumption state. Ready stays low for that matching response during
the request state, so no acknowledged seed is lost. Matching unsolicited host
writes after initialization request acceptance are errors and emit no SRAM write;
writes offered before acceptance are drained. Stale tags are drained.
Cancellation requires a fresh generation and fresh seed;
it does not roll back memory. Hard reset retains the existing drained-transport
requirement. The fill capacity is a 64-byte multiple from 64 bytes through 2 MiB;
the connected normal workload uses the full 2 MiB.

## Accounting and remaining boundaries

Hardware mode records one outer `initialization_hardware_fill` stage, with a
closing partition of provider wait and fill phases. It replaces the legacy
`initialization_transport` stage. It never adds another outer copy of the same
memory-write clocks. Stalls remain nested observations.

The retained default full run at `c96e96ab` measured 40,975,538 hardware/transport
clocks including 131,074 initial-transport clocks. A stage substitution must
subtract that old cost before inserting measured new fill-stage clocks. Such a
substitution is an accounting equation, not a new full-hash measurement at the
changed source. No default 8×2,048 rerun is implied.

Input BLAKE2b, AES program generation and native light dataset item generation
remain untimed host providers. Software fill is retained as a differential
assertion oracle and in explicit legacy mode. Generic synthesis cell counts and
modeled cycles establish no physical frequency, process, area, power or selected
architecture. The next missing AES boundary is native program generation from
the actual post-fill/interprogram seeds; input hashing and dataset generation
also remain hardware gaps.
