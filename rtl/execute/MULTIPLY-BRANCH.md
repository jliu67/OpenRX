# Native multiplication, reciprocal and branch extension

This extension stacks on independently accepted, unmerged PR #55 at
`2b14e4f9a726c1f7e066576bbe8fc351c87d158c`. It preserves that head and adds the
seven missing multiplication families plus CBRANCH. Nineteen integer/branch
families occupy 161 raw values. The remaining 95 floating/CFROUND values still
produce the existing explicit error; no complete VM/hash or physical PPA is
accepted. [Task #56](https://github.com/jliu67/OpenRX/issues/56) requires a separate
new-work review and has no merge authorization.

## Exact arithmetic and tradeoff

`randomx_mul64` reuses one unsigned 64×64→128 product for all forms. Low products
wrap modulo 2^64. Unsigned high selects bits 127:64. Signed high uses the exact
two's-complement correction: unsigned-high minus B when A is negative, minus A
when B is negative, all modulo 2^64. High register forms always use the source
register, including equal src/dst; IMUL_R uses sign-extended imm32 when equal.
Memory forms retain native zero-base/L3 addressing when equal, otherwise L1/L2,
with actual aligned 128-bit memory responses selecting the addressed 64-bit half.

`MUL_RADIX4=0` (default) maps a direct product. `MUL_RADIX4=1` shifts two multiplier
bits per cycle, accumulating the selected 0/1/2/3 multiple over 32 steps. The tagged
ready/valid unit holds captured results under backpressure and cancels on reset.
Request-to-response-handshake latency is 1 clock for direct and 33 for iterative;
this includes the handshake clock. Only the multiplier tradeoff is measured here;
IADD_RS keeps the reviewed fast schedule. No technology or clock-frequency claim
follows from generic cell counts or these clock counts.

The reciprocal unit computes the same integer quantity as unchanged native
`randomx_reciprocal`: `floor(2^(63+bit_length(d))/d)`, for a nonzero/non-power-of-two
imm32 divisor. It starts with remainder `2^(bit_length(d)-1)`, which is below D,
then performs 64 exact shift/compare/subtract steps, collecting 64 quotient bits.
It uses no approximate divider, floating point or software-precomputed operand.
Native zero and power-of-two divisors are NOPs: the executor skips division and
multiplication, preserves R and does not mark a new lexical register write.
Standalone reciprocal requests expose a NOP flag. Valid non-NOP requests have
65 clock request-to-response-handshake latency; held replies and reset are tested.

## Native branch compilation in hardware

Upstream computes each CBRANCH target from the last *lexical* integer-register
write, then marks all eight registers used at that branch's instruction index.
Execution increments PC after jumping to that index. Hardware stores the equivalent
next-PC values, with initial zero representing upstream target−1 / jump-to-zero.
Stores, equal-register swaps and reciprocal NOPs do not update lexical usage.
Other integer instructions update destination usage even when their numerical
result happens to be unchanged; nontrivial swaps also update source usage.

The immutable program has no forward branch targets. First visits therefore arrive
in increasing lexical PC order. The tracker updates only when PC equals the next
uncompiled index; replayed instructions leave it unchanged. Every branch marks all
usage entries as PC+1, so a later branch's target is after the previous branch:
it cannot replay that earlier branch. One cached latest branch target is therefore
sufficient, with no program-sized target table or extra ROM compilation pass.
Reset/new descriptors clear all tracker/cache state. Program bytes must remain
unchanged for the generation, as in the native compile-then-execute model.

Branch arithmetic sign-extends imm32, sets bit `modCond+8`, clears the bit below,
adds modulo 2^64 and tests the native eight-bit condition mask at that shift. A taken
branch uses the cached/first-visit target; fallthrough uses PC+1. Last-slot branch
retirement depends on the resulting next PC, so a taken last branch can still loop.
`commit_next_pc` and `commit_branch_target` are diagnostic fields latched with the
existing one-clock instruction commit pulse. Golden targets/next-PC values only
assert; they are never hardware inputs or a predecoded ROM.

## Differential validation

```sh
python3 scripts/test_integer_multiply.py --output /tmp/openrx-multiply-fresh --synthesize
```

Use fresh external output under the shared slot and current resource admission.
The driver verifies all 171 vendor files and accepted controller/converter/AES/tail
bindings, reuses the six verbatim licensed native bodies and invokes unchanged
native compile/execute/mulh/smulh/reciprocal. Original PR #55 fixtures/evidence/source
remain retained; no baseline or old synthesis is rerun for acceptance. The parent
subset driver/fixtures preserve PR #55's smaller opcode contract and reproduce at
that preserved head. Use this extension driver for the expanded current source.
Both multiplier variants use `SERIAL_IADD=0`; the expanded matrix for the older
shared-IADD option is not repeated.

Eight controlled full-size programs cover all 161 raw values, four chains/aliases,
every shift/rotation/address mask and all 16 branch condition shifts. Native traces
record execution order rather than one expected R per lexical PC. Every actual
retirement, native compiled target, dynamic next PC, memory event, architecture
result and complete 2 MiB image are compared. Cases include jump-to-zero, self loops,
consecutive branch barriers, forced one/two-taken loops, fallthroughs and replayed
actual stores. ROM serves actual requested bytes; SRAM receives actual RTL stores;
chaining uses actual previous hardware retirement. No golden result/target enters
the DUT. The declared dataset-line fixture remains distinct from full dataset/hash.

Separate unchanged-native arithmetic vectors cover 2,304 products at low/unsigned-high/
signed-high extremes and 609 divisors, including all 33 NOP classes and power-of-two
neighbors. Both variants test held results, inactive request changes and reset.
Connected errors still test all 95 unsupported raw value, held error/abort/restart,
held fetch, pending load, held store, cancelled multiply/reciprocal, late packets
and committed-prefix persistence. The reviewed transport fixture still covers
all four rounding modes, arbitrary F/E bits and held return; no FP execution is
claimed. Invalid arithmetic parameters fail elaboration.

Actual synthesized arithmetic units run the primitive vectors and connected
native tests. The complete direct/default integrated top is separately synthesized
and tested. Iterative full-top synthesis is absent; its mapped arithmetic units
run with RTL controller/executor. Full source/input/command/tool/log/license/failure,
fixture, netlist and resource retention accompanies the stacked draft.

The initial expanded fixture did not retain every inherited rotate operand. Strict
coverage rejected it before DUT runs; its original source/output is preserved.
Adding 64 explicit native rotations kept that check strict without changing RTL.
Existing protected inputs and all previous failures/builds/data/receipts remain.
