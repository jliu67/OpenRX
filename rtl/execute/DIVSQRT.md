# Exact native division and square root

Task [#60](https://github.com/jliu67/OpenRX/issues/60) stacks on accepted unmerged
PR #59 at `ce788d11285c901b52fd3cf0b450489d13b3f2f5`. New independent review is required;
no merge is authorized. This completes native instruction-family coverage, with
full VM/hash, selected core, physical memories and calibrated PPA still open.

## Arithmetic and native controls

The byte-identical licensed Berkeley HardFloat1 `divSqrtRecFN_small.v` is the
twelfth selected [upstream source](vendor/hardfloat/manifest.json), from retained
archive SHA-256 `6b3757c9fbfa2230c6a2b84605e39372cb589dd7500e979c4f0b8ecc8a03b14b`.
Its binary64 11/53 iterative arithmetic uses the retained 8086-SSE specialization.
Accepted `randomx_fp64` / `randomx_fp128` bytes remain unchanged. No new installed
tool, altered native reference body or approximate arithmetic is used.

`randomx_divsqrt64` takes tagged ready/valid requests: boolean `req_sqrt`, binary64
A/B, native rounding mode and standalone strict-IEEE versus DAZ/FTZ control.
The four native modes map to HardFloat 0/2/3/1. Integration always uses native
DAZ/FTZ. Subnormal inputs become signed zero; an encoded subnormal or upstream
underflow (including a rounded minimum-normal encoding) becomes signed zero
with underflow/inexact. Five per-operation flags expose invalid/divzero/overflow/
underflow/inexact; native raw MXCSR retains its separate denormal-operand flag.
RandomX exposes rounding state, rather than sticky IEEE exceptions.

The first reset special-case attempt is preserved: upstream exponent/rounding
storage is initialized only on normal arithmetic, so a first NaN could inherit
unknown payload bits. The wrapper resolves NaN/inf/signed-zero encodings and
flags before launching finite work. NaN propagation preserves the first relevant
operand's sign/payload and quiets signaling NaNs; invalid finite operations use
negative default NaN. Sqrt ignores B. Every upstream byte remains unchanged.
Finite work captures tag/FTZ state, consumes the IP's completion pulse once, and
holds its result under backpressure. Native flags/bits cover first-after-reset
specials as well as ordinary finite work.

## Atomic vector and connected execution

`randomx_divsqrt128 #(LANES=1/2)` returns an atomic two-lane result and ORed flags.
Parallel lanes accept together, hold independently when one finishes early, and
consume together. Shared scheduling captures operands/mode/tag and keeps low
results private while high work runs. Reset cancels running, partial and held work.
Bad lane parameters fail elaboration. No bytecode encoding is unsupported: all
256 raw opcodes decode to the 29 native families. Existing error paths remain;
the executor also routes an impossible state to its held error path. This is
not a claim of tested physical fault tolerance.

The core and iteration wrapper expose independent `DIVSQRT_LANES=1/2` (default 2),
while accepted `FP_LANES` controls add/sub/multiply. FDIV_M always addresses
R[src%8] + signed imm32 under L1/L2, including src/dst aliases. It converts the
selected two signed32 words using the accepted exact converter, then applies
`(bits & 0x00ffffffffffffff) | captured_eMask[lane]` and divides E[dst%4]. The mask
retains 52 fraction plus four dynamic exponent bits. FSQRT_R updates E[dst%4].
Neither operation changes integer lexical usage. Both retire E atomically with
native mode and PC; the controller/AES/tail input bindings remain unchanged.
The immutable-program/backward-branch/unique-live-generation contract is inherited.

Measured primitive response latency is operand-dependent: scalar and parallel
1–56 clocks; shared 5–114 on the reversed-pair native corpus. Shared latency is
L0+L1+3, parallel is max(L0,L1); the observed shared maximum is not a universal
bound for every possible lane pair. The mixed connected fixture saves 17,228
clocks with parallel units (45,671/28,443 ideal; 62,637/45,409 stalled). These
controlled schedules emphasize the new operations and do not estimate full-hash performance.

## Reproduction and measured scope

```sh
python3 scripts/test_divsqrt_execute.py --output /tmp/openrx-divsqrt-fresh --synthesize
```

Use a fresh output directory outside source. The driver verifies all 171 pinned
RandomX files, twelve unchanged HardFloat sources, accepted FP unit bytes and
19/17/22 protected AES/tail/controller bindings. A pinned native SSE oracle tests
13,312 balanced division/sqrt records per variant across all four modes and both
strict IEEE and native DAZ/FTZ. Mapped selection keeps 2,560 balanced edge/random
records and all relevant exception categories. Actual unchanged native compile/
execute/iteration code produces assertion-only retirement/denominator traces.
Hardware fetches the raw words and computes results; golden files never drive
arithmetic, PC or register updates.

All 2,856 R/F/E/mode/PC retirements, 152 observed native masked denominators,
146 square roots, 418 loads, 82 stores, 64 tail writes and all 2 MiB match, for
four v2/four v1 contexts, four chains and four aliases. All 256 raw values,
integer/CF rotations, branch conditions, address masks, CF v1/v2 guards, rounding
modes, held/reset/partial replies and stale transport are checked. Twelve RTL
and eleven mapped modes pass. Shared/parallel vector mappings are
8,690/12,942 cells and 779/558 flops; whole default is
274,346 cells / 10,504 flops. Shared whole-top mapping and expanded
old integer/FP-sharing combinations are absent. Tool versions differ on hosted
CI; compare generic counts only within the same tool configuration.
[Evidence](../../docs/validation/divsqrt-execute-20261013/README.md) retains inputs,
commands, licenses, logs, actual netlists, failed attempts and verified archives.


## Icarus 12 compatibility correction — 2026-10-13

The initial PR #61 hosted run rejected the original HardFloat duplicate scalar
`wire sqrtOpOut` declaration: its ANSI output port already declares that net.
The current 53-entry harness generates a separately labeled, checksum-bound
compile view replacing exactly this redundant declaration with an empty CRLF
line. Every other byte and full license notice is preserved. All twelve upstream
files remain unchanged; Yosys continues to synthesize the original source.
Twelve local compatibility RTL PASS records and nineteen native fixture files
match the original run exactly. The hardware/native/oracle/stimulus sources and
eleven original mapped results are reused; no mathematical change or repeat
whole synthesis is involved. The first hosted failure's complete 46-file archive
is retained and verified. Fresh hosted validation and independent review are
required at the corrected PR head.
