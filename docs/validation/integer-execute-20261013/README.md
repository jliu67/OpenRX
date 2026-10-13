# Actual native integer execution — local evidence

[Task54](https://github.com/jliu67/OpenRX/issues/54) / [EXP-006](../../../experiments/EXP-006-native-integer-execute.md)
adds actual hardware fetch, weighted decode and eleven native integer families to
the unchanged accepted iteration controller. [Interface](../../../rtl/execute/README.md)
describes supported operations, tagged ROM/memory/error/return and partial-store
semantics. All158 other raw values trap; FP/CFROUND/multiply/branch, complete VM/hash,
physical memory, selected core and calibrated timing/power remain open.

The [export index](index.json) binds every published byte and its complete original.
`full-*` is the original full native/RTL/two-kernel/whole-top synthesis and mapped
validation. `final-rtl-*` is the final driver with added raw-field/held-return tests.
`transport-*` validates both unchanged mapped kernels with those new tests, verifying
all RTL/header digests and original netlist hashes before reuse. The twelve native
fixture files are byte-identical between original and final drivers; the synthesis
sources never changed. Compiled oracle/vvp binaries, entire sources/attempts and
full detailed host witnesses remain privately retained and archived.

Eight final RTL modes and eleven applicable mapped modes pass. Full supported runs
compare2,560 actual instruction retirements,700 loads,228 stores,64 tail writes,
four chains/four aliases and every final2MiB byte with unchanged native execution.
Stalled runs inject2,560 old ROM,748 old SRAM and eight old dataset packets. Error
runs reject all158 raw unsupported values and test160 held errors, abort/restart,
reset held fetch/pending load/held store, late replies and committed-prefix
persistence. Standalone transport checks8v1/v2 contexts, every rounding mode,
2,560 native equal-register swap NOPs,2,560 stale ROM packets,24 return-stall clocks,
arbitrary raw F/E bits and inactive request-bus changes. Golden outputs are never
executor inputs. The first transport fixture sampled ready in the reset-release
delta cycle and failed before accepting a descriptor; its exact source/fatal is
retained. A one-time-unit settle fixes the fixture; every RTL input is unchanged.

| Mapping | Generic cells | Flops |
| --- | --- | --- |
| Fast integer kernel | 25885 | 1727 |
| Shared-add integer kernel | 25925 | 1792 |
| Complete fast/default connected top | 154145 | 7921 |

Fast/shared ideal integrated clocks are9,524/9,760; stalled26,712/26,948. Both whole
and execute intervals differ by236, one per IADD_RS. Fast has40 fewer generic cells
and65 fewer flops in these actual mappings; sharing is not an area improvement.
There is no frequency, physical-area/power or full-hash-rate inference. Shared
whole-top synthesis is absent; its actual mapped kernel runs with the RTL
controller. Default whole-top mapping is separately delivered and tested.

[Resource summary](resources.json) retains actual kernel limits/peaks/CPU/swap and
original private witness hashes. The full29m20s job used CPU600%, RAM5GiB,
swap512MiB and Tasks128, all six CPUs available, one worker, fresh1GiB OS reserve
and no tighter visible ancestors. Peak cgroup RAM was5,080,702,976 bytes, peak RSS
3,821,160KiB, swap0, no OOM/max events or CPU-quota throttle. Focused mapped
transport and final lightweight native/RTL checks used measured1GiB budgets. Units
are inactive/dead with success and the slot is free. Yosys/Icarus are single-threaded;
one worker keeps worst-case integrated memory bounded, with no artificial CPU cap.
No settings/access/install change, native baseline rerun, force push or code merge.

Reproduce the entire current driver from a temporary source under fresh admission:

```sh
python3 scripts/test_integer_execute.py --output /tmp/openrx-integer-fresh --synthesize
```

Only an additional transport check may reuse unchanged, digest-verified old mappings:

```sh
python3 scripts/test_integer_execute.py --output /tmp/openrx-transport-fresh \
  --transport-only --mapped-from /tmp/openrx-integer-full-prior
```

Every acceptance log, command, tool version, license, extracted native body, input,
coverage record, fixture, failure and actual netlist is preserved. The old converter
regression is reused through its unchanged accepted manifest; generated i32 vectors
in this native wrapper are retained but are not a new converter pass. Independent
new-work review is pending, with no further merge authorization.
