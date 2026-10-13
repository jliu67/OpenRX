# Native floating-point execution subset

## Native division and square root — task #60, 2026-10-13

[Task #60](https://github.com/jliu67/OpenRX/issues/60) extends independently
accepted, unmerged [PR #59](https://github.com/jliu67/OpenRX/pull/59#pullrequestreview-5501107360)
at `ce788d11285c901b52fd3cf0b450489d13b3f2f5` on a separate stacked draft.
All 29 native instruction families / 256 raw encodings now execute, including
masked FDIV_M and FSQRT_R. Reviewed PR #55/#57/#59 and main remain unchanged.
New code requires independent review; no merge is authorized. Complete VM/hash,
selected core, physical memories and calibrated timing/power remain open.
[Design](DIVSQRT.md) and [EXP-009](../../experiments/EXP-009-native-divsqrt.md)
bind reproducible tests and actual mapping. Earlier component summaries retain
their dated source/evidence context; historical subset test drivers require their
accepted frozen heads. Current reproduction uses `scripts/test_divsqrt_execute.py`.

Twelve RTL and eleven applicable mapped modes pass: 13,312 balanced native
primitive vectors per scalar/shared/parallel variant, 2,560 balanced mapped
corner vectors, 2,856 native retirements including 152 divisions / 146 square
roots, 418 loads / 82 stores / 64 tail writes, four chains/aliases and all 2 MiB.
All rounding modes, DAZ/FTZ, IEEE exception bits, masks, held/reset/stale behavior
match. Shared/parallel divide-sqrt units are 8,690/12,942
generic cells and 779/558 flops. Controlled integration clocks
are 45,671/28,443 ideal and 62,637/45,409 stalled; shared adds 17,228 clocks.
Complete default mapping is 274,346 cells / 10,504 flops.
Operand latency is variable; these fixtures and generic gates establish no physical PPA or full-hash throughput.

[Task #58](https://github.com/jliu67/OpenRX/issues/58) stacks on independently
accepted, unmerged PR #57 at `d62c449574e1f5434aa6809040a02fabfb74dc09`.
Both reviewed PR #55/#57 heads are preserved. This extension requires a new
independent review and has no merge authorization.

The existing integer/branch executor now executes FSWAP_R, FADD_R/M, FSUB_R/M,
FSCAL_R, FMUL_R and CFROUND: 27 native families, 246 raw opcode values. The ten
FDIV_M/FSQRT_R raw values still return the explicit held tagged error. Complete
VM/hash, selected core, physical memory and calibrated timing/power remain open.

## Reused arithmetic and native controls

Binary64 add/subtract/multiply use unchanged Berkeley HardFloat Release 1,
11-bit exponent/53-bit significand and its supplied 8086-SSE specialization.
Eleven selected source files retain their original bytes and full BSD-3-Clause
notices; [manifest](vendor/hardfloat/manifest.json) binds the original upstream
archive and every selected source. The original archive is retained. No Scala,
large unrelated core, new installed package, custom approximate arithmetic,
FMA substitution or changed native reference body is involved.
[Upstream documentation](https://www.jhauser.us/arithmetic/HardFloat-1/doc/HardFloat-Verilog.html)
describes its binary64 encoding, exception/rounding support and specialization.

RandomX native SSE resets MXCSR to `0x9fc0`, enabling DAZ and FTZ while masking
exceptions. The adapter replaces subnormal inputs with signed zero and flushes
an underflow result or encoded subnormal to signed zero, setting underflow and
inexact. The underflow flag is essential when IEEE rounding encodes the minimum
normal value but native FTZ still returns zero. HardFloat's supplied SSE default
selects after-rounding tininess detection and first-operand NaN payload propagation.
The four native modes nearest/down/up/toward-zero map to HardFloat 0/2/3/1.

The standalone unit also exposes strict IEEE mode for differential boundary
coverage. Its five per-operation flags are invalid/divide-by-zero/overflow/
underflow/inexact; SSE's extra denormal-operand status is retained in native
fixtures, not represented as an IEEE exception flag. RandomX architecture exposes
only the two-bit rounding state; it does not return sticky exception status.

CFROUND rotates integer R[src%8] by `imm32&63`. V1 always selects its low two bits;
v2 changes mode only when rotated bits 5:2 are zero. Active descriptors capture
A and rounding state; inactive external bus changes cannot affect computation.

FADD/FSUB register forms address F[dst%4] and A[src%4]. FMUL uses E[dst%4] and A.
FADD/FSUB memory forms always use R[src%8]+signed imm32 under L1/L2 masks, including
numerically equal src/dst. They convert the addressed two signed32 words exactly
with the already accepted integer-to-binary64 converter. They do not apply E masks.
FSCAL XORs both F lanes with `0x80f0000000000000`; FSWAP exchanges the two lanes in
F[dst%8] below 4, otherwise E[dst%8−4]. Existing controller E masks and AES/tail remain
unchanged. Masked FDIV_M is unimplemented and traps before arithmetic/memory side effects.

Floating operations and CFROUND never mark lexical integer-register usage.
Every first visited PC still advances the native branch compilation tracker;
replayed FP/stores/CFROUND between an integer write and its branch are real execution.
The parent's immutable-program/backward-branch/one-latest-target contract remains.

## Vector schedule and protocol

`randomx_fp64` has one-cycle request-to-response-handshake latency and a held tagged
result. `randomx_fp128` atomically executes two native lanes. `FP_LANES=2` uses two
coupled units with one-clock response latency. `FP_LANES=1` captures operands/mode/tag,
uses one unit twice and returns after five clocks. The shared low-lane result remains
private until the high lane completes. Reset cancels either held parallel reply or
shared work between lanes. Invalid lane parameters fail elaboration. Arithmetic
unit request opcodes are 0:add,1:subtract,2:multiply; other encodings are outside its
internal contract. The executor never offers unimplemented native operations to it.

`commit_f`, `commit_e` and `commit_round_mode` join the existing retirement diagnostic
fields, with the same one-clock commit pulse. They are assertions/observability;
no software arithmetic or predecoded targets enter hardware. Raw F/E and all four
rounding modes still pass the unchanged parent transport test when no FP executes.

## Validation scope and reproduction

```sh
python3 scripts/test_floating_execute.py --output /tmp/openrx-floating-fresh --synthesize
```

Use fresh external output and the serialized, currently admitted local resource slot.
The parent subset drivers/fixtures retain their earlier opcode contracts and reproduce
at the preserved reviewed heads. Use this expanded driver for this source tree.

Native SSE primitive vectors compare 19,968 scalar and two-lane operations per
variant, all three operators/four modes and strict IEEE/RandomX DAZ+FTZ models,
including signed zeros, normal/subnormal boundaries, ties, arbitrary bits, overflow,
infinities, quiet/signaling NaNs and payload priority. Bits and IEEE flags match;
held replies/inactive inputs and vector reset atomicity are tested. Mapped primitives
use a declared 3,840-vector balanced corpus with every edge pattern in both operand
positions, directed boundary/NaN/zero/overflow/tie pairs and 32 seeded arbitrary pairs;
all operator/mode/DAZ+FTZ combinations and relevant exception categories are retained.
The complete larger RTL corpus remains preserved, with the selection/digests explicit.

Eight full-size native programs execute 2,928 actual retirements, 872 vector arithmetic
FP operations, 584 CFROUNDs, 202 integer products, 102 branches/42 taken, 338 loads,
104 stores and 64 tail writes. Four chains/four aliases, every R/F/E/mode retirement,
native compiled target/dynamic PC, memory event and all 2 MiB are checked. All 246 raw
values, 64 integer rotates/four shifts/three masks, 16 branch conditions, 64 CFROUND
rotates, all arithmetic modes and v2 apply/skip versus v1 unconditional behavior are
covered. Paired modes inject 2,928 old ROM, 386 old SRAM and eight old dataset replies.
Ten unsupported values/twelve held errors, abort/restart, committed prefixes, held
fetch/load/store, integer arithmetic reset and FP cancellation before atomic retirement
pass. Expanded integer radix4/shared-IADD combinations are not repeated; protected
integer primitives and all prior evidence remain retained.

Initial own-wrapper failures selected the wrong tininess control and incomplete FTZ
flush rule; their exact source/output are retained and source archives verified/read-only.
The first controlled fixture lost five raw variants to the explicit suffix/barrier
fixtures. Five explicit native prefix words retained the strict 246-value requirement,
without changing production behavior. Every old source/build/data/receipt remains.
Actual mapped units and complete default synthesis/evidence are recorded in EXP-008
when those serialized payloads complete; shared whole-top synthesis is not supplied.
