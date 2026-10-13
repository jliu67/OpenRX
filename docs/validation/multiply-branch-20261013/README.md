# Native multiplication, reciprocal and branch validation — 2026-10-13

[Task #56](https://github.com/jliu67/OpenRX/issues/56) stacks on independently accepted,
unmerged PR #55 at `2b14e4f9a726c1f7e066576bbe8fc351c87d158c`. Its reviewed head and
all earlier sources/results/builds/receipts remain preserved. This extension requires
its own independent review; no merge is authorized.

[EXP-007](../../../experiments/EXP-007-native-multiply-branch.md) and
[design/interface](../../../rtl/execute/MULTIPLY-BRANCH.md) explain exact arithmetic,
lexical branch compilation, immutable program ownership and limits. All 19 integer/
branch families (161 raw values) execute in hardware. The remaining 95 FP/CFROUND
values still produce the held tagged error. Complete VM/hash, selected core,
physical memory and calibrated timing/power remain open.

Nine RTL and eleven applicable mapped modes pass across the exact frozen code and
retained netlists. Eight full-size v2/v1 contexts compare 2,736 actual retirements,
580 products, 218 branches/90 taken, 562 loads, 272 stores, 64 tail writes, chained
contexts/aliases, every native target/dynamic PC and all 2 MiB. All raw values,
64 rotations, four shifts, three address masks and sixteen condition shifts are
covered. Primitive vectors compare 2,304 products and 609 divisors, including all
33 reciprocal NOP classes. Held/inactive inputs, stalls/stale tags, unsupported
errors, abort/reset, arithmetic cancellation, committed prefixes and unchanged
raw-FE/all-rounding-mode transport are checked. Golden results/targets assert only.

Actual unit cells/flops are 25,723/81 direct versus 5,528/537 iterative; reciprocal
1,374/153. Complete direct/default mapping is 189,296/8,396. The iterative units
run native primitive and connected tests with RTL controller/executor; iterative
whole-top synthesis is absent. Both variants use the reviewed fast IADD schedule.
Ideal/stalled integrated clocks are 12,036/29,502 direct and 30,596/48,062 iterative:
32 extra per product. Generic cells and controlled fixture cycles do not establish
physical timing, power or full-hash throughput.

The first expanded fixture failed strict inherited rotate coverage before any DUT
run. Its `coverage-failure-*` exports preserve inputs, complete native traces/logs,
failed driver/oracle source and failure. Adding explicit native rotations retained
the strict requirement without changing RTL.

The serialized full driver then passed all nine RTL and eight mapped primitive/
connected modes and completed whole-top synthesis (Yosys rc0). The terminal
transport disconnected; its next progress print raised `BrokenPipeError`, stopping
the driver at rc120. All `full-*` bytes, including this failure, are retained.
The fresh `completion-*` attempt verifies the exact source/fixture/netlist hashes
and runs only the three remaining complete mapped tests (rc0). Their first PASS
records and every cycle count equal RTL. No synthesis is rerun. The published
[mapped completion driver](mapped-completion-driver.py), its actual commands,
input proof and assembled [completion summary](completion-summary.json) make this
continuity explicit. A normal fresh run uses:

```sh
python3 scripts/test_integer_multiply.py --output /tmp/openrx-multiply-fresh --synthesize
```

Use fresh external output, serialized execution and current resource admission.
The parent subset driver preserves its older opcode contract and reproduces at
PR #55's preserved head; use this extension driver for the expanded current source.

[index.json](index.json) records raw/public digests, byte lengths and lossless gzip
encoding. `full-inputs.json` binds all 31 source inputs, `full-preserved-inputs.json`
verifies accepted AES/tail/controller manifests and the driver checks all 171 vendor
files. Complete licensed native bodies, seeds/fixtures, commands/tool versions,
actual Verilog/JSON netlists, statistics, logs and failures are exported. Gzip files
decompress to the exact recorded raw SHA-256. Original compiled oracles/vvp, complete
attempts, source snapshots and detailed host witnesses remain privately retained in
verified complete archives; [retention.json](retention.json) binds them. Temporary
authoring/output copies are retired read-only while preserving original execute bits.

[resources.json](resources.json) separates the interrupted 6 GiB full run from its
1 GiB mapped-only completion. Both use actual checked CPU 600%, swap 512 MiB,
Tasks 128, six-CPU affinity, verified ancestor limits, fresh 1 GiB OS reserve and one
worker. Full and focused raw timing/counters are retained, with sanitized measured
limits/peaks/events/drainage public. No OOM, memory-limit hits or CPU quota throttles
occurred. Hosted exact-head checks and new independent review precede acceptance.
