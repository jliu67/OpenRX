# Native program initialization and sequencing

[Task #62](https://github.com/jliu67/OpenRX/issues/62) builds on independently
accepted, unmerged [PR #61](https://github.com/jliu67/OpenRX/pull/61#pullrequestreview-5503154172)
at `7f299c74f81332257eefd775086b355969ad85f3`. Its arithmetic, bytecode
executor and iteration controller remain byte-identical. New work requires
independent review. No merge is authorized.

`randomx_program_control` initializes native program configuration from the
128-byte entropy header and drives the tagged iteration backend.
`randomx_program_sequence` connects it to the accepted
[`randomx_integer_iteration`](DIVSQRT.md) implementation. Defaults are the pinned
native eight programs and 2,048 iterations per program. Reduced iteration counts
are explicit validation profiles, with no full-count performance inference.

## Boundary and data flow

The hardware computes A, MX/MA, read-register selectors, dataset offset and both
E masks using the unchanged native initialization rules. R is cleared at each
program boundary. The first iteration receives the program's MX/MA scratchpad
cursors. Subsequent iterations receive the prior iteration's full integer,
rounding and memory/control state; the accepted iteration controller resets the
cursors to zero at its tail. Round mode starts at nearest for a new batch and
carries across iterations and programs. F/E are loaded by the existing native
iteration body before instruction execution.

The external source provides raw program instructions and metadata, initialized
scratchpad storage and dataset replies. It receives a held R/F/E/A register file
at every program boundary. In the test provider, pinned BLAKE2b hashes those
**actual DUT registers** into the next seed, and pinned AES generates the next
complete native program. The native oracle generates its own reference sequence.
Oracle values only enter assertions; they never drive DUT metadata, instructions,
scratchpad reads or dataset data.

Initial input BLAKE2b, scratchpad AES fill, program AES generation, interprogram
BLAKE2b and final scratchpad/hash finalization remain software operations outside
this hardware component. Dataset replies use a deterministic function of the
actual requested address. This is connected VM program-loop evidence; it does
not establish a complete hardware hash implementation or full actual RandomX
dataset correctness/throughput. Full v1 8×2048 execution, physical SRAM/dataset
implementation and physical timing/power remain separate work.

## Interface and transaction rules

All descriptors and held responses use ready/valid handshakes. Start captures
`start_tag` and `start_v2`. Metadata request/response carries the batch tag and a
three-bit program index. Its 1,024-bit entropy is in native little-endian 64-bit
word order; the program instruction base must be eight-byte aligned. Instruction,
scratchpad and dataset ports retain their existing accepted interfaces.

The backend generation tag starts at `start_tag` and increments once per
completed iteration. **The caller must reserve a non-overlapping tag span of
PROGRAMS×ITERATIONS values for each live batch**, including cancelled or failed
batches whose external responses have not drained. A span must not be reused
until its transport is quiescent. The maximum span is 16,384, within the 16-bit
tag namespace. Metadata additionally checks its program index; stale responses
are drained without state changes. Stale backend errors can delay a matching
done response for one handshake while the stale error drains.

`program_done_valid` holds all R/F/E/A state, round mode, program index and
iteration count. The external source can compute the next seed while that result
is held. Acknowledgment permits the next metadata request; acknowledgment of the
eighth result instead produces held final `done_valid`. A new batch is accepted
after final done or error acknowledgment. `iteration_commit_*` is an unbuffered
diagnostic pulse with full state and both batch/backend tags; consumers must
observe every pulse if using it as a trace.

Error code 1 is malformed program alignment; code 2 propagates a matching backend
error and its PC/opcode; code 3 handles an impossible control state. Error records
are held until acknowledgment. Backend error takes priority over a simultaneous
matching done. The impossible-state branch is not a physical fault-detection
claim. Reset cancels metadata, backend work and held responses, and suppresses
request/retirement outputs. Previously accepted scratchpad stores stay committed;
there is no memory rollback.

## Reproduction and validation profiles

Use a fresh external output directory and an isolated source snapshot on the
designated, admitted server. The runner rejects output inside its source and
retains commands, tools, licenses, generated native bodies, inputs, failures and
complete output digests. It verifies all 53 accepted PR61 input bindings and the
pinned vendor manifest. Original HardFloat files remain unchanged; the accepted
Icarus-only generated compile view is reused, while Yosys reads original IP.

```sh
python3 scripts/test_program_sequence.py --output /tmp/openrx-sequence-new
python3 scripts/test_program_sequence.py --output /tmp/openrx-sequence-mapped-new --synthesize
python3 scripts/test_program_sequence.py --output /tmp/openrx-sequence-full-new --full-v2
```

Run these separately under the single admitted resource slot. The default profile
executes eight native-generated programs × four iterations, in v1 and v2, with
ideal and stalled/stale transports. It compares full R/F/E/A and round/control
state after every iteration, executed-PC/next-PC route signatures and instruction
counts, each bytecode memory event, dataset/prefetch addresses, tail stores and
all 2 MiB of scratchpad at every program boundary. It exercises native held
program cancellation, version restart, late metadata/ROM/SRAM/dataset replies,
pending loads/held stores/fetches and running divide/sqrt cancellation, including
a committed store prefix.

The standalone control bench uses an explicitly identified arithmetic backend
stub to test the actual default 8×2048 loop counts, feedback, entropy initialization,
held requests/results, nonzero round-mode carry, stale replies and error priority.
It supplies no arithmetic correctness claim. The full v2 profile executes all
16,384 native iterations against the independent oracle, with a three-hour RTL
cap. The earlier short pilot is not a substitute for that profile.

Synthesis maps default control, a distinct short 8×4 control configuration, and the
actual default 8×2048 complete top. Default mapped control runs the full contract
bench. The short mapped control drives complete v1/v2 native program transitions
and held-program resets. Whole-top mapped gates run a bounded first native v2
iteration with full state/memory assertions and connected cancellation tests.
They do not run the full 16,384-iteration workload. Generic cells/flops exclude external memories/provider logic. Modeled
execution clocks use the stated ready/valid responder delays and omit software
preparation/finalization time; they establish no calibrated physical area,
clock frequency, power or full-hash throughput.

## Results at initial draft publication

All four native-generated eight-program × four-iteration RTL pilots pass. V2
ideal/stalled clocks are 110,934/185,396 with 12,331 instruction retirements;
v1 clocks are 70,110/120,864 with 8,207 retirements. Every program boundary checks
all 2 MiB; both profiles produce 256 iteration-tail stores. These are fixed
correctness fixtures, with no full-count throughput inference.

The full v2 job is running, with native reference preparation of 16,384
iterations, 6,305,764 instructions and 1,282,660 bytecode memory events.
Its RTL completion and the new control/reset/mapped checks are pending. Tests
still running or not yet executed are not passes. [Evidence](../../docs/validation/program-sequence-20261013/README.md)
retains the original pilot failures, source bindings and resources. Exact full-run
inputs will distinguish its original harness from later cancellation extensions;
RTL/native workload bytes remain identical.
