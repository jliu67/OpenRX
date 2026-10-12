# Focused v2 iteration-tail backpressure tests

[PR #51 baseline 623d2498 passed independent review](https://github.com/jliu67/OpenRX/pull/51#pullrequestreview-5496629211). Its coverage qualification was that existing stalls exercised v1, while v2 supplied the no-stall comparison and reset cases. This addendum closes that narrow test gap. Focused independent review of the new delta remains pending; no merge is authorized.

`tb_iteration` adds a separate `STALL_V2=1` mode. Each of the 64 v2 iterations holds every R/F write beat for two valid cycles and retirement for three. Coverage assertions require 512 R-write stalls, 512 F-write stalls and 192 retirement stalls, including the final F beat. Existing valid/data/address/byte-enable stability, store order, final F/cursors, 32 aliases, both partial resets and the full 2 MiB scratchpad comparison all run. The later 64 v1 iterations retain their previous stalls.

The default no-stall mode remains separate. All four original logs are byte-identical to the reviewed baseline, as [the identity check](no-stall-baseline-log-identity.json) records: serial/overlap intervals remain 25/21 for one lane and 13/9 for four. Directed-stall elapsed cycles are coverage diagnostics and excluded from the performance comparison.

All four RTL lane/scheduling configurations pass both modes. Both exact reviewed overlap mapped netlists pass both modes, with logs identical to corresponding RTL. [mapped-summary.json](mapped-summary.json) verifies all six unchanged synthesizable RTL files and exact original fixture/netlist digests before replay. All 19 PR #49 core input bindings, oracle and [original baseline evidence](../iteration-tail-20261012/README.md) remain unchanged.

| Evidence | Artifact |
|---|---|
| Four RTL configurations and coverage | [rtl-summary.json](rtl-summary.json); rtl-v2-stalls-1-0.log, rtl-v2-stalls-1-1.log, rtl-v2-stalls-4-0.log, rtl-v2-stalls-4-1.log |
| Both exact mapped netlists | [mapped-summary.json](mapped-summary.json); mapped-1-stalls-1.log, mapped-4-stalls-1.log |
| Commands and exact inputs | [rtl-commands.json](rtl-commands.json), [mapped-commands.json](mapped-commands.json), [inputs.json](inputs.json), [tools.json](tools.json) |
| Resource and export bindings | [resources.json](resources.json), [mapped-resource-time.txt](mapped-resource-time.txt), [index.json](index.json) |

Reproduce the complete updated flow, including synthesis and both test modes:

```bash
python3 scripts/test_iteration_tail.py --output /tmp/openrx-tail-v2-stalls-fresh --synthesize
```

The unchanged hosted workflow runs that command and retains licensed outputs. Local focused checks reused exact reviewed mapped netlists because RTL is unchanged; no new local synthesis result is claimed. Both checks acquired the shared lock, used one worker with all six CPUs available, and peaked at 160,452 KiB (RTL) /385,340 KiB (mapped replay). Full new outputs, including unexported generated/binary artifacts indexed by their manifests, and all originals remain retained. No full core/hash, physical SRAM/fabric, frequency, power or PPA acceptance follows.
