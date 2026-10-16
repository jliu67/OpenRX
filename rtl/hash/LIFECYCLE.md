# Connected prepared RandomX v2 lifecycle

[Task #71](https://github.com/jliu67/OpenRX/issues/71) connects the accepted
instruction, iteration, reciprocal preparation, register hashing and scratchpad
finalization blocks. The request carries the actual input bytes and caller tag;
the response carries the 32-byte digest. Defaults are eight native v2 programs,
384 instructions per program, 2,048 iterations per program and a 2 MiB scratchpad.
The reproducible test is `scripts/test_prepared_hash_lifecycle.py`.
The test driver defaults to a bounded eight-program × two-iteration pilot;
`--full-v2` selects the canonical eight-program × 2,048-iteration workload.
`--interfaces-only` reports recovery/capacity checks separately and cannot claim
a completed RTL hash.

The three new modules have separate responsibilities:

| Module | Responsibility |
| --- | --- |
| `randomx_prepared_program_sequence` | Load and prepare one complete immutable image before its first iteration, then reuse it through the program |
| `randomx_prepared_program_hash_sequence` | Connect actual R/F/E/A to hardware BLAKE2b-512 between programs and hold the next program until its seed is accepted |
| `randomx_prepared_hash_lifecycle` | Capture input, initialize exclusive scratchpad ownership, execute the chain, scan final memory, replace A and return BLAKE2b-256 |

`PREPARED_RCP=0` is the paired runtime-reciprocal baseline. Both variants load
exactly the same image and execute the same native workload. `PREPARED_RCP=1`
computes each active reciprocal once during admission. It preserves lexical
zero/power-of-two NOP handling and unsigned 32-bit divisors. Existing execution,
rounding, v2 CFROUND gating, AES mixing and address recurrence are unchanged.

## Provider and hardware boundary

The external initialization callback receives the captured input (up to 80 bytes),
computes the native input BLAKE2b-512 and AES scratchpad fill, and returns the
post-fill seed. It must deliver every 16-byte beat in ascending order, with all
byte strobes set, before returning success. Accepted writes are immediately
visible and persist across cancellation or failure. They are never rolled back.

The program callback receives the actual initial or hardware-derived next seed.
It produces native AES-generated entropy and 384 instruction words. Oracle
registers, program images and seeds are assertion data; they never drive these
providers or the DUT. The seventh interprogram result is hashed; the eighth
program bypasses interprogram hashing and goes directly to finalization.

The dataset provider calls the unchanged pinned native `initDatasetItem` for
each actual aligned address, using a 256 MiB native cache and the documented key
in `lifecycle_native.hpp`. Its item bytes equal the RandomX dataset; it does not
allocate the logical 2,181,038,016-byte dataset. This light-mode implementation
does not model physical DRAM transactions, latency or power. Each returned item
is 64 bytes. Cache initialization, input/fill, program generation, dataset item
generation and assertion-only hashing have separate host-time records; none is
converted to device clocks.

The hardware owns SRAM transport, program load/preparation, all execution,
seven interprogram BLAKE2b hashes for the default chain, the complete final SRAM
scan, native A replacement and final BLAKE2b-256. Initial fill and program AES
generation remain software providers. A reference-correct connected hash does
not establish a complete autonomous ASIC, a selected architecture or calibrated
whole-machine throughput, timing, area or power.

## Ownership and recovery

Only one request is active. Each accepted request allocates a monotonically
increasing 16-bit hash generation; the caller tag is returned separately. SRAM
has exclusive owners INIT=0, EXEC=1 and FINAL=2; NONE=3 emits no transfer.

| Interface tag | Layout, most significant first |
| --- | --- |
| Scratchpad, 51 bits | hash generation 16, owner 2, provider subtag 33 |
| Dataset, 32 bits | hash generation 16, iteration backend tag 16 |
| Program load, 41 bits | hash generation 16, image epoch 16, PC 9 |
| Metadata | hash generation and program index |

The finalizer retains its complete 33-bit subtag. Executor subtags are zero
extended; the current response must match the expected transfer. Wrong
generation, image epoch, program or backend tags are drained, including stale
error replies. A matching provider error aborts the active request and returns a
held error under the original caller tag. Final success and error payloads remain
stable until accepted. A successor always starts with fresh initialization.

Cancellation invalidates active control/image ownership without undoing accepted
stores. Hash generations and admission epochs survive cancellation and errors.
Admission reserves enough remaining unique image epochs for the whole batch.
`generation_exhausted` covers either namespace; `req_ready` refuses a batch that
cannot finish before wrap. A hard reset restarts namespaces only after the
external transports have been drained. Reset cannot distinguish a reply from a
previous use of an identifier if a provider violates this drain contract.

## Validation and accounting

The native assertion fixture extracts the pinned instruction/iteration and
initialization bodies unchanged. For the default 8×2,048 workload its final
digest must also equal unchanged `randomx_calculate_hash`. RTL checks per-iteration
retirement counts/route fingerprints, every bytecode memory event and dataset address, complete iteration
R/F/E/A and rounding/address state, every program's full 2 MiB, each hardware
seed, final A and final digest. Initialization and program generation independently
use actual DUT input/seed values. Held/stalled, stale-error, matching-error,
cancellation and namespace-capacity tests exercise the interface contract.

An outer clock belongs to exactly one stage: initialization transport,
control/metadata, preparation, execution, interprogram seed, finalization or held
return. Iteration, executor and finalizer phases partition their parent stages.
Stalls and reply waits are nested observers, never extra outer clocks. Exported
traffic distinguishes 16-byte bus beats, useful strobed bytes and logical
bytecode/entry/tail/dataset bytes. Paired tests require equal native work, equal
common-stage/phase costs, positive native reciprocal counts and measured
reciprocal cost equations, including every load/preparation.

Icarus provides four-state simulation. The optional pinned Verilator backend
uses the same native callbacks/assertions with two-state simulation; its bounded
result is cross-checked against Icarus before using it for a full run. Sparse
event traces include outer/iteration/executor phase transitions; they are diagnostics, not a calibrated
architectural model. The driver rejects stale output directories and source/output
overlap, hashes consumed source and retained tool/library receipts, and preserves
commands, failures, licensed compile views and complete output inventories.

Run scientific work only through a fresh authorized immutable local-runner
admission. Keep all earlier sources, tool builds, failures and receipts. See the
task's published experiment/evidence for exact executed profiles and limitations;
an available test option is not evidence that it has passed.
