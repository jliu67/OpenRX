# Native integer execution

Current FP extension: [exact HardFloat-backed native subset](FLOATING.md), 246 raw
values; division/sqrt remain errors. Reviewed PR #55/#57 heads remain unmerged.
Earlier integer-only sections retain their parent publication context.

Current stacked extension (task #56): [multiplication/reciprocal/branch hardware](MULTIPLY-BRANCH.md)
supports all161native integer/branch raw values;95FP/CFROUND values remain errors.
PR #55 is independently accepted but unmerged; this extension needs its own review.
The original eleven-family interface/results below retain their reviewed context.

`randomx_integer_execute` fetches and executes an exact bounded subset of native
RandomX bytecode. `randomx_integer_iteration` connects it directly to the accepted
[iteration memory engine](../engine/README.md), signed conversion, dataset feedback
and unchanged AES/store tail. Actual RTL produces the integer registers and
scratchpad stores. The software oracle supplies test assertions only.

The supported families are IADD_RS, IADD_M, ISUB_R, ISUB_M, INEG_R, IXOR_R, IXOR_M,
IROR_R, IROL_R, ISWAP_R and ISTORE. They occupy 98 raw opcode values in the unchanged
weighted configuration. All 158 other values produce an explicit error: multiply,
high multiply, reciprocal, floating point, CFROUND and branch execution are absent.
Even an unsupported instruction that native compilation could reduce to a NOP is
rejected. Equal-register ISWAP_R retains its native NOP behavior.

This is native bytecode hardware, not a RISC-V core, complete RandomX VM or full-hash
implementation. No selected-core, calibrated timing, physical PPA or hash-rate gate
is accepted by this component. F/E and rounding mode pass unchanged through the
integer kernel; entry conversion and the iteration AES tail still run in hardware.

## Instructions and ports

Program requests return one 64-bit word at `program_address + 8 * PC`. Its low bytes
are opcode, destination, source and modifier, followed by the little-endian imm32.
The destination/source normalize modulo eight. The RTL ceilings are checked
against pinned `configuration.h` before any test; vendor files are unchanged.
Programs have their native sizes: 384 instructions for v2 and 256 for v1.

All arithmetic wraps to 64 bits. IADD_RS uses modifier bits2–3 for its shift and
sign-extended imm32 displacement only for destination R5. Equal src/dst SUB/XOR
forms use sign-extended imm32, while equal src/dst rotates use unsigned imm32 modulo
64. Rotate zero preserves the original word. Other rotate operands use Rsrc modulo
64. Loads use zero base and the L3 mask when src equals dst; other loads select L1
or L2 from modMem. Stores use Rdst+imm32 and modCond>=14 selects L3. The masks are
`0x3ff8`, `0x3fff8` and `0x1ffff8`; their low32 addition matches native modulo64
addition after masking. Each 64-bit access selects a half of the aligned 128-bit
memory port, with `00ff` or `ff00` write strobes.

The standalone execute request/return and memory ports match the accepted engine.
The connected top exposes its descriptor, scratchpad, dataset and retirement
ports, plus tagged program fetch, error and instruction-commit diagnostics. There
is one outstanding program request. A program response has at least one clock of
latency, echoes the tag and contains bytes from the actual requested address.
Senders keep valid/payload stable under backpressure. Responses with an old tag are
consumed and dropped. Reuse the engine's private ordered-memory contract: write
ready means committed bytes, reserve generation zero, and never reuse a generation
until cancelled traffic has drained. ROM, SRAM and dataset are external models or
adapters, not physical memory macros delivered here.

`error_valid/tag/pc/opcode` remains stable until acknowledged. There is no normal
retirement for that program. The connected wrapper registers the acknowledgement
as an abort/reset on the next clock, then accepts a new descriptor. External reset
also cancels active state and suppresses output handshakes. Neither error nor reset
rolls back an already committed scratchpad store; the caller must discard the
cancelled architectural context and arrange safe memory restart.

`commit_valid` is a one-clock observation pulse after each actual instruction,
with tag, PC, raw opcode and resulting R. It is not a ready/valid transport and is
not backpressured. No golden register result enters either hardware module.

## Schedules and reproduction

`SERIAL_IADD=0` uses two additions in one IADD_RS execute clock; `SERIAL_IADD=1`
shares that addition path across two clocks. Only IADD_RS is claimed to share
resources. Other integer operations retain their normal RTL implementation.
Invalid parameter values fail elaboration. The connected controller defaults to
LANES=4, parallel conversion and equal-private-line coalescing.

```sh
python3 scripts/test_integer_execute.py --output /tmp/openrx-integer-fresh --synthesize
```

Use a fresh output outside the temporary source. Substantial local runs require
the shared slot and fresh host/kernel/ancestor resource admission. The driver
verifies 171 vendor files and the accepted AES/tail/engine manifests (19/17/22),
reuses six verbatim licensed native includes, and invokes unchanged native
compile/execute semantics. The controlled full-size programs cover every supported
raw opcode, every rotation, every shift, all memory masks, wrapping arithmetic,
immediate/displacement forms and both store halves.

Four connected RTL modes compare every actual instruction retirement, actual
memory address/data/strobe, chained hardware context, dataset feedback, AES/tail
result and all 2 MiB final bytes against native execution. The ROM serves requested
instruction bytes, SRAM serves actual addressed contents and accepts actual RTL
writes, and the declared dataset fixture is computed from the requested address.
Golden results are only assertions. Stalled modes hold all command/retirement
payloads and inject stale ROM/SRAM/dataset replies. Standalone RTL/mapped kernel transport tests exercise all four rounding modes,
arbitrary raw F/E bits (including NaN payloads and signed zero), inactive request
bus changes, native equal-register swap NOPs and held returns. Both schedules also test every
unsupported value, held errors, abort/restart, reset of a held fetch, pending load
and uncommitted store, late replies and committed-prefix persistence.

Both actual synthesized integer kernels run those connected tests with the
unchanged RTL controller. The complete fast/default integrated top is separately
synthesized and runs the same tests as a wholly mapped netlist. The shared complete
top is not separately synthesized; its kernel is mapped and its controller remains
RTL in that validation. Logs compare exact PASS/cycle records, allowing only the
HDL tool's extra successful finish diagnostic. Full commands, versions, inputs,
coverage, logs, licenses, failures and actual netlists are retained.

The fetch-to-last-commit interval includes real ROM and scratchpad model latency;
whole iteration cycles also include entry loads, dataset feedback and AES/tail.
The execute interval is inclusive from first accepted ROM request to the observed
last instruction commit; it excludes the first request’s pre-acceptance wait.
These fixture/port cycle counts and generic cell counts are not calibrated clock
timing, physical area, power or complete-hash throughput. See
[EXP-006](../../experiments/EXP-006-native-integer-execute.md) for measured results.
