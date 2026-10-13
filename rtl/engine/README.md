# Iteration memory and execution interface

`randomx_iteration_engine` implements one RandomX program iteration around an
external bytecode arithmetic kernel. It computes the entry scratchpad addresses,
loads and forms R/F/E, routes the kernel's scratchpad operations, reads and XORs
the dataset line, updates the memory registers, and invokes the unchanged
[AES/store tail](../iteration/README.md). It returns the architectural state only
after all eight tail writes commit. RandomX v2 is primary; v1 uses the same
interface and its original F XOR E tail.

The arithmetic kernel, instruction fetch, physical 2 MiB SRAM, and dataset cache
are external. The tests replay memory traffic and final registers from actual
pinned software bytecode execution. They verify this controller's integration;
they do not implement or measure an arithmetic core or a full RandomX hash.

## Descriptor and data layout

All channels use synchronous ready/valid handshakes at the rising clock edge.
The sender holds valid and every payload field stable until accepted. The engine
holds one iteration at a time and can accept the next descriptor on the same
edge that the previous retirement is accepted. R, F, E, and A are 512-bit vectors
with element 0 in bits 63:0; each 128-bit beat has its lowest addressed byte in
bits 7:0. Each floating vector contains eight binary64 values. The descriptor
supplies R and A, the two scratchpad cursors, mx/ma, the four program read-register
selectors, both E masks, the dataset offset, program address, version, current
two-bit rounding mode, and a 16-bit generation tag.

Entry addresses are exactly `(spAddr0 XOR low32(R[read0] XOR R[read1])) &
0x001fffc0` and `(spAddr1 XOR high32(...)) & 0x001fffc0`. The first line is XORed
into R. Sixteen signed 32-bit integers from the second line become eight F and
eight E binary64 values; E uses the pinned `0x00ffffffffffffff` dynamic mask and
the alternating program E masks. Every signed32 integer fits binary64 exactly,
including INT32_MIN, so the converter needs no rounding operation or general
floating-point IP. The execute packet also carries A, E masks, program address,
version, and the rounding mode. The external kernel supplies its final R/F/E
and rounding mode, including any CFROUND updates. The kernel must retain the
pinned floating-point environment and exact instruction semantics.

After execution, the dataset read uses the old ma masked by `0x7fffffc0`, plus
the dataset offset. The prefetch hint uses the changed mp register: v2 changes
ma, while v1 changes mx, by XORing low32 of R[read2] XOR R[read3]. Both versions
then swap mx/ma. The returned 64-byte dataset line is XORed into R before the
existing tail. Retirement returns R/F/E, mx/ma, rounding mode and the tag, with
both scratchpad cursors zero. E remains available for the architectural result
even though only R and F are stored.

## Memory and cancellation contract

The scratchpad channel uses 21-bit byte addresses relative to private 2 MiB
memory. Commands are 16-byte aligned and data is 128 bits. There is one ordered
outstanding read for the active generation. The adapter must also account for
any cancelled read still draining after reset. There is at least one clock
between command acceptance and the response; zero-cycle responses are unsupported. During execution, the kernel
uses this same port. If both requests are fresh, a write wins arbitration. A read already presented
under backpressure retains its grant until acceptance, even if a write arrives
later; the kernel must keep that read valid/address/tag stable. The pending write
waits until the accepted read response is consumed. Reset clears the retained
grant and outstanding-read state. The kernel must keep its memory requests stable
under backpressure and wait for read responses. A 16-bit write strobe selects
individual bytes. `sp_wr_ready` means the bytes have committed in order, rather
than admission into a reorderable queue. Execution return is blocked until all
memory traffic drains, including a presented final request.

Dataset addresses are 64-bit byte addresses relative to the supplied dataset
base/offset. Its response is one 512-bit line with at least one-cycle latency.
`ds_prefetch_valid` is an advisory pulse when the dataset read is accepted; the
consumer can ignore it. The SRAM and dataset adapters must echo the generation
tag. All execute requests, returns and memory traffic also carry that tag.
Responses and execution commands with a different tag are consumed and dropped.
Tags identify cancelled generations as well as completed iterations. Reserve
tag zero for reset and do not reuse a tag until every old response and command
with that tag has drained; wraparound is the caller's responsibility.

Reset suppresses handshakes, cancels the active controller/tail state and clears
registers. It does not roll back bytes whose write handshake already committed.
The caller must abandon the cancelled iteration's architectural state and
arrange safe restart of the scratchpad context. This interface does not provide
transactional rollback or protection against another master modifying the
private scratchpad. Equal-line coalescing is valid only with exclusive ownership
and no external writes between the two entry reads.

## Configurations and reproducible checks

`LANES` is 1 or 4, inherited from the existing AES/store tail. `SERIAL_CONVERT`
and `COALESCE_LINES` are boolean synthesis parameters:

| Configuration | Conversion | Equal-line entry reads | Purpose |
| --- | --- | --- | --- |
| A | One shared converter, 16 clocks | Eight beats | Reference resource/control schedule |
| B | Sixteen parallel converters | Eight beats | Isolate conversion-cycle gain |
| C (default) | Sixteen parallel converters | Four beats | Also remove redundant private-line reads |

The driver compares A/B/C at LANES=4 and C at LANES=1 in both minimum-latency
and stalled channel models. A and C at LANES=4 are synthesized and their actual
mapped netlists run the same differential. B and LANES=1 are RTL-only coverage.
The minimum-latency entry interval, from descriptor acceptance to execution
packet acceptance, is `2 * entry_read_beats + 1 + 16 * SERIAL_CONVERT` clocks.
This excludes the external arithmetic kernel's execution time. Aliased entry
lines save four read commands and eight clocks under that port model; the
fixture's alias frequency is deliberate coverage, not a workload estimate.

From a temporary source snapshot, using an output directory that does not exist
and is outside that source:

```sh
python3 scripts/test_iteration_engine.py --output /tmp/openrx-engine-fresh --synthesize
```

Local substantial runs require the existing global compute slot and fresh
resource admission. The driver verifies the unchanged RandomX manifest and the
merged AES/tail input bindings, creates six include files with verbatim native functions/bodies
and upstream notices, records commands/tool versions/inputs/failures, and
retains every licensed generated output. The controlled programs have the real
v2 size of 384 instructions and v1 size of 256, using fourteen integer, floating,
memory and CFROUND instruction families. Thirty-two iterations include sixteen
v2, sixteen v1, sixteen chained contexts, eight aliases, first/last scratchpad
lines and all four initial rounding modes. Real native memory reads and stores
are replayed against the same full 2 MiB image. Checks cover operand formation,
addresses, byte strobes, memory ordering, architectural retirement, complete
memory, stalls, stale traffic and three reset-abort positions, including one
already committed partial store. A separate 4,096-vector signed conversion test
uses pinned native SIMD conversion across all four rounding modes.

Generic cell counts describe the flattened controller, conversion datapath and
existing tail. They exclude physical memories, the arithmetic kernel, clock
tree and technology mapping. Controller/replay cycles and generic cells do not
establish chip frequency, power, calibrated PPA, dataset-cache performance or
full-hash throughput. Independent review of this new integration remains required.

The directed arbitration regression separately overlaps independent read/write
requests. It checks a stalled read followed by a write, a stalled write followed
by a fresh read, stalled read responses, stale-generation traffic, reset of an
unaccepted grant, and byte-strobe persistence. It fails on the original bd193092
controller, which could retract a presented read. The corrected four RTL
configurations and delivered A/C netlists run this same regression in the driver.
Original source, rejected review and prior serialized-replay results stay retained;
the correction evidence records regenerated cells and unchanged replay cycles.
