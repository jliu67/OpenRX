# Native register-file BLAKE2b

[Task #64](https://github.com/jliu67/OpenRX/issues/64) extends independently
accepted [PR #63](https://github.com/jliu67/OpenRX/pull/63#pullrequestreview-5505712453)
at `990f36830c5a9854bf8e2cf1fe7fd7d4ccf7f192`. All 69 accepted execution
inputs, original arithmetic IP and pinned RandomX source remain unchanged.
This new stage requires its own independent review; no merge is authorized.

## Native message and digest contract

The pinned RandomX `RegisterFile` is exactly 256 bytes, in R/F/E/A order at
offsets 0/64/128/192. Each bank is 512 bits. Byte zero is the low byte of R;
floating registers retain their raw native binary64 bits. Two 128-byte BLAKE2b
blocks use cumulative byte counters 128 and 256. Only the second is final.
Unkeyed fanout/depth are both one and there are twelve compression rounds.

`randomx_regfile_blake2b` accepts this fixed message through a tagged, buffered
ready/valid request. `DIGEST_BYTES=64` implements the native interprogram digest;
`DIGEST_BYTES=32` independently initializes the native final-digest parameter.
The 32-byte result is not a truncated 64-byte digest. Digest byte zero occupies
bits 7:0; the upper 256 bits are zero in 32-byte mode. Lengths other than 256
produce a held error and zero digest. Reset cancels a partial or held result.

## Reused IP and declared correction

The BSD-2-Clause [cyrozap/blake2](https://github.com/cyrozap/blake2) source is
pinned to `36f00fd6351f82cb476fd82af8d615f28aaf677d`. The original core, four-G
compression design, message schedule, license and README are preserved byte for
byte under [vendor/blake2](vendor/blake2/manifest.json); the complete original
13-file snapshot is separately archived. [RFC 7693](https://www.rfc-editor.org/rfc/rfc7693.html)
defines the compression and digest parameterization.

The original core's `next` path reinitializes its chaining value from the IV.
An executed native two-block negative test demonstrates the resulting mismatch.
`randomx_blake2b_chain_core` is a separately declared derivative: it captures
continuation, retains the preceding chaining value and initializes v0–v7 from
that value for the next block. G arithmetic, rotations, message schedule and
round count remain original. The scope is unkeyed 256-byte register files and
32/64-byte digests. General keyed, salted, tree, arbitrary-length and high-counter
operation is not validated by this component.

The original combinational G operand holds infer 1,024 level-sensitive latches
in generic synthesis. They remain preserved and are reported separately from
flip-flops. Mapped simulation uses the installed Yosys generic-cell models with
their original license and exact digest. No latch timing or technology closure
is inferred from a generic simulation result.

## Connected program boundary

`randomx_program_seed` captures the completed register file, batch tag, program
index, iteration count and round mode. It hashes programs zero through six,
holds the native 64-byte seed with their state, and bypasses hashing after
program seven. A parameterized one-to-eight-program profile uses exactly
`PROGRAMS-1` hashes. Invalid indices or iteration counts outside 1–2048 produce
held errors. Requests and results are inactive during reset.

`randomx_program_hash_sequence` connects that bridge to the unchanged accepted
program sequencer. It blocks the next metadata request and final batch response
until the buffered program result is acknowledged. The caller supplies native
program metadata and instructions generated from the **hardware-produced seed**.
The independent native oracle computes its own sequence; its outputs enter only
assertions. All original transport/tag reservation, stale-response and committed
memory rules in [PROGRAM_SEQUENCE.md](../execute/PROGRAM_SEQUENCE.md) still apply.

A seed-stage error is held as code 3 with the captured tag/program and zero
PC/opcode; its acknowledgment resets the connected transaction. Existing backend
errors retain their original codes and fields. Reset never rolls back stores
already accepted by external scratchpad storage. Impossible-state handling is
not a physical fault-detection claim.

Initial input hashing, scratchpad AES fill, native program AES generation, final
scratchpad AES reduction into A and the real RandomX dataset remain external.
The 32-byte primitive accepts the caller's post-reduction register file; this
stage does not deliver complete hardware finalization or full-hash throughput.

## Reproduction

Use a frozen source snapshot, a fresh external output directory and the admitted
single server resource slot. The driver preserves commands, tools, source and
artifact digests, native fixtures, original-IP negative proof and failures.
Original HardFloat bytes remain unchanged; Icarus uses the accepted generated
compatibility view while Yosys reads the original IP.

```sh
python3 scripts/test_regfile_blake2b.py --output /tmp/openrx-hash-new
python3 scripts/test_regfile_blake2b.py --output /tmp/openrx-hash-mapped-new --synthesize
```

Each digest receives the same 524 native register-file messages: four byte
patterns, 256 single-byte high-bit positions, 256 fixed-seed arbitrary messages
and eight independently accepted full-run register files. Native C computes all
expected digests. Connected v1/v2 ideal/stalled eight-program × four-iteration
tests use actual hardware seeds and compare every native state, memory event and
all 2 MiB per program. Separate held/error/reset and cancellation tests cover
both compression blocks, held seeds, final bypass and late transport responses.

Synthesis and mapped checks cover the new 32/64-byte digest units and program
seed bridge. Mapped new-stage gates connect to the preserved execution RTL;
whole-backend mapping and full 16,384-iteration baselines are reused from PR63.
Generic cell/flop counts and modeled fixture clocks establish no technology
area, calibrated frequency, physical power or full-hash performance.

[EXP-011](../../experiments/EXP-011-native-regfile-blake2b.md) and
[evidence](../../docs/validation/regfile-blake2b-20261013/README.md) record the
completed validation, exact publication and remaining boundaries.

## Completed server validation

All 18 RTL modes and 17 mapped modes pass. Both digest sizes use the same 524 native messages. Digest latency is 56 modeled clocks; the held seed bridge adds its capture/return stages and has 58-clock hash latency, zero-clock final bypass, 459 hashes/65 bypasses in its corpus, four resets and three invalid iteration counts. Eight native cancellation modes cover both compression blocks and held seed/final/batch responses, retaining all 2 MiB of committed memory and restarting the opposite version. Existing backend reset/error scenarios also pass.

Four native v1/v2 ideal/stalled eight-program × four-iteration chains use exactly seven actual hardware seeds, with full state/events and all 2 MiB checked at each program boundary. V2 clocks are 111348/185810; v1 clocks are 70524/121278. Each is 414 clocks above the accepted software-seed fixture. These fixture model clocks omit software initialization, program generation and finalization and establish no full-count or physical throughput.

Actual server mapping uses Yosys 0.9 (git sha1 1979e0b). Counts include inherited G operand latches and exclude the accepted execution backend, external memories and software providers.

| New stage | Generic cells | Flip-flops | Latches |
| --- | ---: | ---: | ---: |
| hash-64 | 45,891 | 5,156 | 1,024 |
| hash-32 | 45,635 | 5,156 | 1,024 |
| seed | 57,378 | 7,755 | 1,024 |

Mapped digest and seed gates reproduce their RTL records exactly, including connected transitions, held/error/reset behavior and cancellation. The connected backend remains accepted RTL; there is no regenerated whole-core or full 16K gate run. The corpus reuses eight assertion-only register-file frames from the accepted full native-v2 PR63 run; the new connected tests use eight programs × four iterations.
