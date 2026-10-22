# EXP-027 — Conditional prepared-fetch SRAM baseline

Date: 2026-10-22. Task: [issue #72](https://github.com/jliu67/OpenRX/issues/72).
Status: independently accepted conditional model comparison; draft delivery,
independent final-head review and applicable exact-head checks remain separate.

## Question and assumptions

Does four-bank organization reduce the optimistic one-outstanding-fetch interval
relative to one bank at fixed 128 KiB in the retained CACTI6.5 model? Use the
hypothetical 2010 ITRS45nm HP projection, 1.0 V and 360 K, pure UCA RAM,
4096 logical 32-byte words, 256-bit output, one RW port per bank and one global
credit. Each row holds 161 instruction/reciprocal content bits plus 95 padding
bits; transient echo/status and owner tags stay outside SRAM. This is a forced
partition pair, not a search for an optimum or a characterized SRAM macro.

The 256 MiB prepared cache is provisionally external; accepted dataset items
remain cache-backed recomputation, without a materialized 2 GiB dataset
assumption. Each 2 MiB VM scratchpad and its physical ports/banks are outside
this comparison. Retained gem5 DDR4 metadata is static annotation only, with
no gem5 or DRAM/controller simulation.

## Execution and observations

The [approved five-command plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6342654553)
ran once as `20261022T140233Z-a4edfd2d9e92`. Actual outcomes were 16 passing tests,
a fresh 20-C++-unit CACTI build in 20.232 seconds, two valid model cases and a
strict report. All five commands returned zero, without timeouts or skipped
stages. One worker/global slot used CPU600%, RAM1 GiB, swap2 GiB and Tasks256;
each command had a 120-second limit plus 5-second supervisory grace. Two retained
legacy compiler warnings remain in the build evidence.

| Conditional modeled quantity | One bank | Four banks |
| --- | ---: | ---: |
| Access time, ns | 2.74122 | 0.714793 |
| Random cycle time, ns | 1.40396 | 0.453356 |
| Read energy, nJ | 0.214913 | 0.126983 |
| Whole-organization area, mm² | 0.393586 | 0.588724 |
| Standby leakage per bank, mW | 169.571 | 58.8541 |

For both cases, the optimistic global-credit period is
`max(access_ns, cycle_ns)` and rate is `1e9 / period_ns` transactions/s.
Protocol, assembly, clock quantization and reply-hold overheads are zero only
for that bound. Four banks give 3.835× this rate through lower modeled latency,
40.9% lower read energy and 49.6% more organization area. Bank count is not a
throughput multiplier; per-bank leakage is not a whole-organization or wall-power
measurement. Accepted PR87 fetch counts and PR91 logical descriptor accounting
remain separate from physical supply and off-chip traffic.

## Evidence and limits

[Evidence and exact source snapshot](../docs/validation/conditional-sram-baseline-20261022/README.md)
retain configurations, raw cases, strict report/provenance, command results,
source/tool pins and independent result review
`PASS_CONDITIONAL_MODEL_COMPARISON_ONLY`, no blocking findings. Report SHA256 is
`67deb5c947d346f84c48db5e30b7000a76a8fdd9c8b0fe67bfa81621d81c9bde`.
Raw runner `unverified` and driver/report pending-review fields remain unchanged;
the separate review supplies the narrow acceptance statement.

No foundry/PVT or real SRAM macro characterization, physical PPA/frequency,
controller/PHY sustainable random service, whole-machine power or achieved
hash rate is accepted. Characterized SRAM/PVT and memory-system service data are
needed for a defensible target assessment. Broader issue #72 remains open.
All original failed and accepted records are preserved. This result authorizes
no follow-up run, full-hash rerun, installation or hardware purchase.
