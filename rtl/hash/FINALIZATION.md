# Native scratchpad finalization

Task [#67](https://github.com/jliu67/OpenRX/issues/67) implements the post-execution
boundary defined by pinned RandomX `VmBase::getFinalResult`: reduce all scratchpad
bytes with `hashAes1Rx4`, replace the complete 64-byte A bank, and compute unkeyed
**BLAKE2b-256** over the actual 256-byte little-endian R/F/E/A register file.
It stacks above PR65 at `4f095fc147b5bc78de79746a0a172f38e34d6450`.
Local component validation passes as recorded below; hosted verification and independent review are required. PR65's public review remains
unpublished; neither component is authorized to merge by this document.

## Components and byte order

`randomx_scratchpad_aes_hash` reuses unchanged `randomx_aes_round` and its pinned
licensed secworks S-boxes. One shared combinational round handles one lane per
clock. The initial S0/S1/S2/S3 constants and two closing keys come directly from
`vendor/randomx/src/aes_hash.cpp`. Byte zero is bits `[7:0]`, and lane zero is bits
`[127:0]`. Each ascending 64-byte group supplies four distinct raw 128-bit keys:
AESENC for lanes 0/2, AESDEC for lanes 1/3. These rounds include column mixing
and raw-key XOR. After the last group, apply XKEY0 to all four lanes, then XKEY1
to all four lanes, retaining the same direction for each lane. There is no AES
key expansion or special final cipher round.

`randomx_scratchpad_finalizer` captures raw R/F/E/A and the rounding mode, waits
for the scanner, and feeds R/F/E plus replacement A to the unchanged
`randomx_regfile_blake2b` with `DIGEST_BYTES=32` and message length 256.
That parameter changes the BLAKE2b initialization; taking 32 bytes from the
64-byte digest is a different computation and is rejected by every fixture.
R/F/E and rounding bits are preserved. A and the digest become successful
returned state together. A read/error result retains original A and a zero digest.

## Memory and ownership contract

The requester owns the complete scratchpad exclusively, with execution writes
quiescent until the finalizer's returned result is consumed or reset cancels it.
This component reads memory and never writes it. Default `SCRATCHPAD_BYTES` is
2,097,152; a smaller elaboration value must be a positive multiple of 64 and
no larger than the native size. Runtime request length must equal that value;
otherwise a held error is returned without a memory read. Smaller configurations
are explicit bounded verification fixtures and do not stand in for the default
native scratchpad.

The port allows one outstanding ordered 128-bit read, with at least one clock
from acceptance to response. Byte address increments by 16 from zero through
`SCRATCHPAD_BYTES-16`; the default has 131,072 reads ending at `0x1ffff0`.
Request address/tag remain stable under backpressure. Response data/error applies
only to the outstanding matching tag; mismatched responses and their errors are
drained. Returned results remain stable while `rsp_valid && !rsp_ready`.

The 33-bit memory tag is `{request_generation[15:0], read_index[16:0]}`. The
17-bit index covers the complete default scan without wrapping or aliasing an
earlier read. This width extends the existing generation-tagged 128-bit contract;
integration with a narrower shared fabric needs an explicit adapter/reservation,
which this standalone boundary does not supply. A requester must not reuse a
generation while any canceled/completed response with that generation can still
arrive. Reset suppresses all valids/readiness, cancels partial work and held
returns, and clears private state. It cannot recall accepted external reads.
A fresh nonreused generation safely rejects late responses; no unbounded tag
uniqueness or memory rollback is claimed.

## Validation and synthesis scopes

`scripts/test_scratchpad_finalization.py` runs only within the caller's admitted,
serialized payload and requires a fresh output directory outside the source.
It verifies 246 validated/frozen draft-parent inputs, all 171 native sources and original licensed IP
before compilation. The new oracle calls unchanged pinned `hashAes1Rx4<true>`
and native BLAKE2b with independent 32/64-byte parameters. Python `hashlib`
independently checks the digests. Expected hashes enter assertions only; the DUT
receives actual scratchpad bytes and the original raw register file.

The bounded corpus has zero, walking-bit and deterministic PRNG cases at
64/128/256/4,096 bytes. The full corpus reuses the accepted final program-7
scratchpad/register artifacts, with exact source/raw/public digests, and a
separate full deterministic PRNG input. Four full RTL trials use ABBA input
order with ideal/stalled memory balanced across the two cases. They do not
regenerate the previous 16,384-iteration program chain.

Directed tests cover captured inputs/all rounding modes, request/response stalls,
wrong-generation/wrong-index errors, first/last matching read errors, invalid
size, held completion, and reset during request/read/AES/BLAKE/held return with
fresh-tag restarts. The complete bounded 256-byte integration is tested with
its actual synthesized netlist. Default 2 MiB mapped controls exercise invalid
requests, first-read errors and canceled reads with partial fresh-tag restart;
they do not complete a full mapped hash. Actual default scanner/finalizer mapping
is measured separately from that bounded netlist. Generic cells, flops and
inherited BLAKE latches are reported separately, with modeled clocks and tool
versions; these are not technology timing, physical area, memory macros or power.

## Observed local result

All 41 RTL / 19 mapped modes pass, including four full 2 MiB trials in balanced
actual/pattern/pattern/actual order with ideal/stalled/ideal/stalled memory.
Each full trial reads 131,072 beats. Ideal and stalled primary response latencies
are 393,284 and 1,048,649 modeled clocks; setup/held/consumption clocks are reported
separately. All 14 native/Python fixtures, six malformed-native guards and four
invalid elaborations pass. Actual default scanner and finalizer synthesis and
complete bounded 256-byte gates are measured separately in [evidence](../../docs/validation/scratchpad-finalization-20261013/README.md).
Default mapped controls exercise cancellation/errors and partial restart, with
`native_success=0`; they are not a full mapped 2 MiB finalization.

The locally executed driver is retained unchanged. Publication corrects output
labels, version capture, a consumed-manifest binding and staging-test CI triggers;
11 focused successor guards pass and all scientific RTL/native/oracle/fixture/bench
bytes and command construction remain exact. Hosted full validation of the
published driver and independent exact-head review remain required.

## Reproduction

After manager slot admission and fresh actual-kernel resource checks, execute
from the frozen feature source with one worker and the global resource lock:

```bash
python3 scripts/test_scratchpad_finalization.py \
  --output /tmp/openrx-scratchpad-finalization-validation-UNIQUE --synthesize
```

Preserve complete outputs, command logs/timings, input hashes, source snapshots,
tool/licensing records, actual resource receipts and every failed attempt.
The independent reviewer must verify the published feature's exact head.

Initial scratchpad fill, AES program generation, full actual dataset, a selected
core, complete hardware hash integration and calibrated/physical PPA remain open.
This feature changes none of the accepted execution's `(v & 60)==0` gate,
scratchpad-address recurrence or rounding propagation across programs.
