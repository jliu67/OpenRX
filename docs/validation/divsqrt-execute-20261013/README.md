# Native division and square-root evidence

[Task #60](https://github.com/jliu67/OpenRX/issues/60) stacks on independently
accepted, unmerged PR #59 `ce788d11285c901b52fd3cf0b450489d13b3f2f5`.
New independent review is required; no merge is authorized.

[Index](index.json) binds raw/public SHA-256 values. Large text/HDL/JSON traces
use lossless gzip; decompress before inspecting their original bytes.
[Summary](integration-summary.json) records all twelve RTL and eleven applicable
mapped modes; [resources](resources.json) retain actual checked budgets, measured
peaks, memory/swap pressure, worker counts and drainage.

The native oracle checks exact bits/IEEE flags, all rounding modes and strict IEEE
versus RandomX DAZ/FTZ, with 13,312 full records per variant and 2,560 balanced
mapped corner records. Hardware executes all 256 raw encodings / 29 families,
2,856 native retirements (152 divisions / 146 roots), 418 loads / 82 stores /
64 tail writes, four v2/four v1 contexts, four chains/aliases and all 2 MiB memory.
Programs, assertion-only traces, native denominator masks and complete actual
unit/top netlists are retained. Input manifests verify all 52 scientific sources,
171 pinned RandomX files, 12 unchanged upstream HardFloat sources, accepted
FP64/FP128 bytes and 19/17/22 protected component bindings.

Shared/parallel units: 8,690/12,942 generic cells, 779/558 flops. Whole default:
274,346 cells / 10,504 flops. Native/RTL/mapped cycle records agree: shared versus
parallel 45,671/28,443 ideal and 62,637/45,409 stalled. Operand latency is variable.
These controlled fixtures and generic mappings establish no physical PPA or
full-hash throughput. Full VM/hash, selected core and calibrated timing/power
remain open; shared whole-top/expanded older sharing combinations are absent.

All failures remain: first-after-reset special-value wrapper, missing branch
condition coverage, cancellation entry-line roles and observer event order.
Original/pinned sources, binaries, outputs, commands, licenses, logs and receipts
are preserved with complete verified archives. Temporary source/output staging
is retired read-only, preserving execute bits; no standing editable clone/Git sync.

Reproduce from this source with:

```sh
python3 scripts/test_divsqrt_execute.py --output /tmp/openrx-divsqrt-fresh --synthesize
```

Use fresh output outside source. Historical subset tests/evidence retain their
accepted-head context; the current hosted workflow runs this full-family driver.


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
