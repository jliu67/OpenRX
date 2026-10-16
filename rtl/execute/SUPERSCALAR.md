# Prepared native superscalar program execution

This component executes one already prepared RandomX superscalar program on eight
64-bit integer registers. It follows the pinned native `executeSuperscalar`
semantics in `vendor/randomx/src/superscalar.cpp`; it does not use the VM's
frequency-coded instruction decoder. The accepted `randomx_mul64` supplies low,
unsigned-high and signed-high products without modifying that IP.

Program generation, reciprocal preparation, the immutable instruction image and
its response service are external. Argon2/cache initialization, cache-line reads,
the eight-program dataset-item controller and the final dataset response are
also external. This executor is not a complete dataset generator.

## Admission and prepared image

One request captures the eight input registers, caller tag, prepared-image epoch,
instruction count, selected address-register index and reciprocal-table count.
Counts from zero through 512 and address registers zero through seven are valid.
Zero instructions return the captured state without an instruction request.
The selected value is a raw register result; the later dataset controller must
perform the matching cache-line XOR before selecting the next cache address.

The instruction service receives a transaction tag, image epoch and instruction
index. It returns the native eight-byte instruction and, for `IMUL_RCP`, a valid
prepared reciprocal packet containing its full 32-bit table index and 64-bit
value. The table index must match the instruction's immediate and be below the
captured table count. The native cache initializer uses one reciprocal table
across all eight programs; indices are not limited to the current program length
or nine-bit instruction index. Prepared indices such as 0, 1, 2 and 4 are valid
indices, and are never interpreted as divisors or power-of-two no-ops.

Matching epoch/index/reciprocal metadata establishes association with the request.
The external preparer remains responsible for supplying the correct immutable
image, table and value for that context. The oracle export binds those actual
inputs and records their identities; the RTL does not prove an arbitrary host
reciprocal value correct. The image and table must remain immutable until return
or until all abandoned service traffic is drained.

## Native arithmetic

All 14 native encodings are implemented: `ISUB_R`, `IXOR_R`, `IADD_RS`, `IMUL_R`,
`IROR_C`, the three add-immediate forms, the three XOR-immediate forms,
`IMULH_R`, `ISMULH_R` and `IMUL_RCP`. Arithmetic wraps modulo 2^64. The three
immediate-size variants have identical execution semantics. Immediates for add
and XOR are sign-extended from 32 bits. Shifted add uses modifier bits 3:2 with
no VM r5 displacement. Register aliases retain native register semantics.

The full opcode and destination bytes are checked. Source bytes are checked only
for instructions that read a source register; unused fields remain ignored.
Rotate immediates 0 through 63 are supported, including an explicit zero rotate.
Larger raw rotate immediates return an error; the portable pinned reference has
undefined shifts outside that range, and generated native programs use 1–63.
Malformed instructions or matching service errors return a held error before
the affected instruction retires.

## Lifecycle and observation

Only one instruction request is outstanding. Its payload remains held until
accepted. A matching early response is held until the request has been accepted;
stale transaction tags are drained. A matching response must have the captured
image epoch and expected instruction index. The current instruction, operand
registers and prepared reciprocal are captured before execution.

An internal 16-bit transaction generation distinguishes accepted requests even
when caller tags repeat. Cancellation preserves that generation, resets the
shared multiplier through a clock edge and suppresses abandoned completion.
After generation 65,535, admission fails closed and reports exhaustion. Reset
requires the external service to drain prior traffic and clears exhaustion.
These bounded tags do not establish unlimited-lifetime identity across resets
in the presence of indefinitely retained responses.

The result holds all eight registers, the selected register, caller tag and
success/error metadata until accepted. An error preserves the committed register
prefix and returns zero as the selected value. Retirement observation exposes the actual
post-instruction register state for differential comparison. Captured operation
and modeled-cycle counts support component analysis; external response stalls
are reported separately from the ideal service profile.

## Validation and limits

The focused native oracle uses the unchanged pinned native executor, actual
generated superscalar programs and prepared reciprocal-index rewriting. It
exports input state, instructions, reciprocal bindings, every intermediate
register state and final state. It does not send expected output registers as
device inputs. Hand-built valid programs cover arithmetic corners and control
boundaries; generated programs exercise the actual preparation path without
allocating or initializing a 256 MiB cache.

Correctness is checked before synthesis and mapped comparison under the existing
single-slot local runner and exact source/tool/input bindings. Every attempt,
including failures, remains retained. Execution, synthesis and cycle claims are
pending until linked evidence records a completed, verified attempt.

Generic synthesis counts exclude external image/table storage, cache memory and
service, program preparation and dataset control. They establish no process,
frequency, physical area/power, memory-technology selection or whole-machine
efficiency. No new default full 8×2,048 connected hash measurement follows.
