# Exact native floating-point subset validation — 2026-10-13

[Task #58](https://github.com/jliu67/OpenRX/issues/58) stacks on independently
accepted, unmerged PR #57 at `d62c449574e1f5434aa6809040a02fabfb74dc09`.
Both reviewed PR #55/#57 heads and all prior source/build/data/receipt assets are
preserved. This new code requires separate independent review; no merge is authorized.

[Design/interface](../../../rtl/execute/FLOATING.md) and
[EXP-008](../../../experiments/EXP-008-native-floating-execute.md) describe the
concrete licensed HardFloat1/8086-SSE choice and exact native DAZ/FTZ/NaN/rounding,
register/memory masks and CFROUND. All 27 integer/branch/FP families (246 raw values)
execute actual semantics. Ten FDIV_M/FSQRT_R values still return explicit held errors.
Complete VM/hash, selected core, physical memories and calibrated PPA remain open.

Twelve RTL and eleven applicable actual mapped modes pass. The 19,968-case full
scalar/two-lane primitive corpora cover three operators, four modes, strict IEEE and
native DAZ/FTZ, signed zeros, normal/subnormal/tie/overflow boundaries, infinities,
quiet/signaling NaN payload priority, bits/IEEE flags, held/inactive inputs and
atomic reset. Mapped primitive tests use a separately declared 3,840-case balanced
corpus: all 24 edge patterns in both positions against ±1/self, directed
NaN/zero/underflow-round-to-normal/overflow/tie pairs and reversals, 32 seeded arbitrary
pairs, every operator/mode/DAZ+FTZ combination and relevant exception category.
[Selection/digests](rtl-mapped-primitive-selection.json) are explicit; the complete
larger corpus remains retained. Per-operation IEEE flags exclude SSE's extra
non-IEEE denormal-operand status, whose raw MXCSR bits remain in native fixtures.
RandomX architecture exposes the two-bit rounding state, not sticky exception status.

Eight full-size v2/v1 contexts compare 2,928 actual R/F/E/mode retirements, 872 vector
FP operations, 584 CFROUNDs, 202 integer products, 102 branches/42 taken, 338 loads,
104 stores, 64 tail writes, chains/aliases, every native compiled target/dynamic PC
and all 2 MiB. All supported raw values, inherited rotate/shift/address coverage,
64 CFROUND rotates/four arithmetic modes/v2 apply+skip versus v1 unconditional
behavior, held/stale traffic, all unsupported/errors, abort/reset, committed
prefixes and unchanged raw-FE/all-rounding-mode transport are checked. Golden
arithmetic/results/targets assert only and never enter hardware.

Actual shared/parallel FP128 unit mappings are 26,522/49,363 generic cells and
571/156 flops, with five/one-clock response latency. Integrated ideal clocks are
16,604/13,116; stalled 33,574/30,086: four extra per each arithmetic FP instruction.
Complete default mapping is 260,110 generic cells/9,826 flops. Both actual mapped units run primitives and connected ideal/
stalled/error tests. The complete parallel/default top is separately mapped and
simulated; shared whole-top synthesis and expanded old integer-sharing matrices
are absent. Generic cells/controlled clocks do not establish physical timing,
power, natural mix, hash rate or selected-core acceptance.

The first two own-wrapper attempts selected before-rounding tininess and omitted
FTZ flushing when IEEE rounded to minimum normal despite underflow. Their complete
source/output and both fatal logs are preserved; upstream bytes were never changed.
Using the supplied SSE default and upstream underflow flag resolves both against
unchanged native operations. The first connected controlled fixture lost five raw
values to explicit suffix/barrier cases. Five native prefix words retained the
strict 246-value criterion, changing no production behavior. A missing-helper
invocation failed before driver execution/output creation and is also retained.

Reproduce under fresh admission and the shared serialized slot:

```sh
python3 scripts/test_floating_execute.py --output /tmp/openrx-floating-fresh --synthesize
```

The parent subset drivers/fixtures retain older opcode contracts and reproduce at
the preserved reviewed heads. Use this driver for the expanded current source.
The local complete default mapping reused the frozen successful RTL/native inputs
and unit mappings, with [unit](mapped-unit-driver.py) and
[integration](mapped-integration-driver.py) actual helper/command provenance. No
accepted old baseline or large unrelated core is rerun for this work.

[index.json](index.json) records raw/public SHA-256, byte lengths and lossless gzip.
`rtl-inputs.json` binds every code input; `rtl-preserved-inputs.json` verifies all
171 RandomX files, eleven unmodified HardFloat sources and accepted AES/tail/
controller/converter manifests 19/17/22. Complete original licensed bodies, inputs,
seeds/fixtures, command/tool logs, actual Verilog/JSON netlists, statistics and
failures are exported. Gzip decompresses to the recorded raw digest. Original
compiled oracles/vvp, source snapshots, complete attempts and detailed host
witnesses remain privately retained in verified archives bound by
[retention.json](retention.json). Temporary source/output copies are read-only at
handoff, preserving original execute bits.

[resources.json](resources.json) separates the 2 GiB mapped-unit job from complete
integration's 6.5 GiB/2 GiB-swap candidate after fresh headroom rejected 7.5 GiB RAM.
Both use actual CPU 600%, Tasks 128, six-CPU affinity, one worker, verified ancestors
and fresh 1 GiB OS reserve. Raw timing and sanitized peaks/swap/events/drainage record
actual pressure. Current hosted checks/new independent review govern acceptance;
local validation and a coordination status alone are not independent acceptance.
