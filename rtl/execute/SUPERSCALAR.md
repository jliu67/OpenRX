# Prepared native superscalar program execution

This component executes one already prepared RandomX superscalar program on eight
64-bit integer registers. It follows the pinned native `executeSuperscalar`
semantics in `vendor/randomx/src/superscalar.cpp`; it does not use the VM's
frequency-coded instruction decoder. The accepted `randomx_mul64` supplies low,
unsigned-high and signed-high products without modifying that IP.
The controller processes instructions in order, with one instruction executing
at a time. The default wrapper selects the existing iterative multiplier;
`MUL_RADIX4=0` exposes the unchanged direct variant for bounded comparison.

Program generation, reciprocal preparation, the immutable instruction image and
its response service are external. Argon2/cache initialization, cache-line reads,
the eight-program dataset-item controller and the final dataset response are
also external. This executor is not a complete dataset generator.

| Port group | Width and meaning |
| --- | --- |
| `req_r`, `rsp_r`, `commit_r` | 512 bits; r0 occupies bits 63:0 and r7 bits 511:448. |
| `req_tag`, `req_epoch` | Caller tag and immutable prepared-image epoch, 16 bits each. |
| `req_count`, `req_address_reg`, `req_rcp_count` | 10-bit instruction count, full 8-bit register index and full 32-bit reciprocal-table count. |
| `fetch_tag`, `fetch_epoch`, `fetch_pc` | 32-bit transaction identity, captured 16-bit epoch and 9-bit instruction index. Tag bits 31:16 are the internal generation; bits 15:0 are the caller tag. |
| `fetch_rsp_instruction` | Native 64-bit word: opcode, destination, source and modifier in the low four bytes, followed by little-endian imm32. |
| `fetch_rsp_rcp_valid`, `fetch_rsp_rcp_index`, `fetch_rsp_rcp_value` | Prepared reciprocal association: valid bit, full 32-bit index and full 64-bit value. |
| `rsp_selected`, `rsp_error`, `rsp_error_pc` | Selected 64-bit raw register, error bit and 9-bit failing PC; invalid descriptors report PC zero. |
| `rsp_cycles`, `rsp_retired`, `rsp_muls` | Held 64-bit availability-cycle count and 10-bit committed instruction/multiply counts. |
| `commit_valid`, `commit_pc`, `commit_opcode` | One post-writeback observation pulse with the 9-bit PC and raw 8-bit native opcode. |
| `phase`, `generation_exhausted` | Control observation and fail-closed admission status; exhaustion does not abort the last accepted program. |

Each request, fetch and response uses its accompanying valid/ready handshake.
The fetch response echoes transaction tag, image epoch and PC, and can report an
external service error. Caller inputs may change after acceptance. Cancellation
must remain asserted through a rising clock edge to reset multiplier work.

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

| Native opcode byte | Operation |
| --- | --- |
| 0, 1, 2, 3 | Register subtract, XOR, shifted add, low multiply. |
| 4 | Immediate rotate right. |
| 5 / 7 / 9 | Sign-extended immediate add (C7 / C8 / C9). |
| 6 / 8 / 10 | Sign-extended immediate XOR (C7 / C8 / C9). |
| 11, 12 | Unsigned-high and signed-high register multiply. |
| 13 | Low multiply by the supplied prepared reciprocal value. |

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

Availability cycles run from descriptor acceptance to the first valid result and
exclude every held-return clock. Empty programs and rejected descriptors have
zero availability clocks. The final commit pulse can coincide with the first
valid result. Control-test aggregate counters cover returned requests; aborted
prefix work is checked for correctness but is excluded from those aggregates.

## Validation and limits

The focused native oracle uses the unchanged pinned native executor, actual
generated superscalar programs and prepared reciprocal-index rewriting. It
exports input state, instructions, reciprocal bindings, every intermediate
register state and final state. It does not send expected output registers as
device inputs. Hand-built valid programs cover arithmetic corners and control
boundaries; generated programs exercise the actual preparation path without
allocating or initializing a 256 MiB cache.

Correctness is checked before synthesis and mapped comparison under the existing
single-slot local runner and exact source/tool/input bindings. Both first
attempts pass: 130 native cases / 7,779 retirements / ten RTL modes, then seven
mapped modes over the explicit 116-case subset with no completed-work rerun.
See [EXP-019](../../experiments/EXP-019-prepared-superscalar-execute.md) and the
[evidence](../../docs/validation/prepared-superscalar-20261016/README.md) for exact
source/receipt identities, opcode counts and measured per-program clocks.
Every original attempt and its status remain retained.

Generic synthesis counts exclude external image/table storage, cache memory and
service, program preparation and dataset control. They establish no process,
frequency, physical area/power, memory-technology selection or whole-machine
efficiency. No new default full 8×2,048 connected hash measurement follows.
