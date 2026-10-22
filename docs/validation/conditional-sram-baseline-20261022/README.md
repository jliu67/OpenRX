# Conditional SRAM bank comparison — 2026-10-22

The [approved issue #72 plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6342654553)
completed once as `20261022T140233Z-a4edfd2d9e92` above main
`6888f8293a4a4703f714f755cb0c45f15fd1f6f3`. All five commands returned zero:
16 focused tests, a fresh 20-translation-unit CACTI build, two model cases and
the strict report CLI. No command was skipped, retried or timed out.
[Separate independent review](independent-result-review.json) accepts **conditional
model comparison only**. Publication-head review and applicable hosted checks are
separate gates; this delivery is a draft PR.

## Result and useful tradeoff

At the declared hypothetical CACTI6.5 ITRS 45 nm HP / 1.0 V / 360 K assumptions,
four banks reduce the optimistic serialized service interval, at greater modeled
organization area. These are two forced UCA candidates, not an optimization sweep
or characterized SRAM macros. Both have **128 KiB total**, 4,096 logical 32-byte
rows, 256-bit output, one RW port per bank and **one global outstanding credit**.

| Conditional model quantity | One bank | Four banks |
| --- | ---: | ---: |
| Access time, ns | 2.74122 | 0.714793 |
| Random cycle time, ns | 1.40396 | 0.453356 |
| Optimistic one-credit interval, ns | 2.74122 | 0.714793 |
| Optimistic requests/s | 364,801,074 | 1,399,006,426 |
| Optimistic local row bytes/s | 11,673,634,367 | 44,768,205,620 |
| Read energy, nJ | 0.214913 | 0.126983 |
| Whole-organization area, mm² | 0.393586 | 0.588724 |
| Standby leakage **per bank**, mW | 169.571 | 58.8541 |

The four-bank/one-bank ratios are 0.260757 for access time, 0.322912 for cycle
time, 0.590858 for read energy and 1.495795 for area. The optimistic service
ceiling is 3.834984× higher **because modeled latency is lower**. No bank-count
multiplier is applied. This is a 40.9% modeled read-energy reduction with 49.6%
more modeled area for this pair. Per-bank leakage is preserved as reported;
neither an organization leakage total nor wall power is inferred.

The ceiling uses `1e9 / max(access_ns, cycle_ns)` with protocol, assembly,
response-hold and clock-quantization overheads explicitly zero. The actual
accepted channel holds its only credit until reply consumption and forbids
same-edge refill. The model therefore supplies a conditional upper bound,
not a sustainable physical service guarantee.

## Exact evidence and reproduction boundary

- [Raw generated report](memory-baseline.json), SHA256
  `67deb5c947d346f84c48db5e30b7000a76a8fdd9c8b0fe67bfa81621d81c9bde`;
  [provenance](provenance.json) and its unchanged [report index](artifacts.sha256.json).
- Both original model outputs/configs/CSVs are in [one-bank logs](logs/cases/bank1/)
  and [four-bank logs](logs/cases/bank4/). Their stdout includes the source's word
  “Best”; the partition was forced, so this does not establish an optimum.
- [Public execution summary](public-summary.json),
  [normalized validation summary](validation-summary-public.json), and complete
  [unit](logs/units/), [build](logs/build-log/) and [report](logs/report-log/) logs.
  Local `{SOURCE}`/`{EXECUTION}` prefixes are substituted in public command,
  status, GNU time and build-log stdout records. Original status hashes in raw report/provenance
  bind retained local originals, not the normalized `status-public.json` files.
- [Executed source snapshot](source/) includes the adapter, all 16 test methods,
  driver, contract, configs, accepted PR87/91 input reports and exact retained
  CACTI/gem5 files with original copyright/license notices. The
  [source manifest](source/SOURCE-MANIFEST01.json) binds 57 files / 1,016,790 B;
  it is separately pinned as
  `505b787884969c0312910fcc989f84b4eb5a2c54a04146d35445b9e707b0fee4`.
  Its `UNRUN` fields are the preserved **pre-execution preparation snapshot**;
  current actual outcomes are in the execution summary. Likewise the
  [approved plan snapshot](approved-plan-snapshot.md) preserves its original
  preparation wording; publication and execution subsequently occurred.
- Generated executable: 405,224 B, SHA256
  `5ba626bd84f0288a4ff54641b79fb159bad39a4a77200c0470de56aa776ab792`.
  Full binary, writable build, raw runner manifest/receipt/events, all old
  failures and original sources remain retained locally. No generated binary
  or private journal is published here.

The snapshot's test entry point is `python3 -B -m unittest discover -s tests -p
test_memory_baseline.py -v` from `source/`. Its fixtures use synthetic numbers
to test parser/accounting rejection, not to supply scientific model results.
Actual model values above come from the separately executed CACTI binary.
The exact approved five-command build/model/report recipe is preserved in the
plan and driver; the runner-bound driver requires fresh admitted metadata.
Neither this documentation nor copying the snapshot grants execution authority.

The retained gem5 revision `c8222cc67a399bfc01e8658dd14b30d5bfd634f9` is a
source/build label. Copied-file SHA256 identity is authoritative; a new complete
upstream-tree comparison was not performed. Tools are byte-pinned with installed
package metadata, without claiming hermetic headers/shared-library closure.
Original source modes were observed/copied, not manifest-pinned; Git publication
uses ordinary source-file mode. The retained `batch_tests` script was not run.

## Actual execution and limits

| Command | Return code | Wall seconds | Maximum command RSS, KiB |
| --- | ---: | ---: | ---: |
| 16 unit tests | 0 | 0.2655 | 18,688 |
| CACTI build | 0 | 20.2318 | 175,076 |
| One-bank model | 0 | 0.0037 | 4,736 |
| Four-bank model | 0 | 0.0036 | 4,736 |
| Conditional report | 0 | 0.1143 | 16,928 |

One worker/global slot, CPU600%, RAM1 GiB, swap2 GiB and Tasks256 were admitted.
The exact service kernel limits were `cpu.max=600000 100000`,
`memory.max=1073741824`, `memory.swap.max=2147483648`, `pids.max=256`, with
six allowed CPUs and no tighter visible ancestor ceiling. Locked headroom was
7,142,735,872 B available versus 2,147,483,648 B required. Each command retained
the approved 120-second timeout plus five-second supervisory grace; no fixed
overall deadline was promised. Summed timed stages took 20.619 seconds; that
excludes staging/finalization and is not chip timing.

Two legacy build warnings remain visible: NUCA's extra format argument and
crossbar's vexing parse. Neither model emitted diagnostics. CACTI exit zero was
insufficient by itself: each case passed 31 input-identity guards, single CSV
header/row, forced partition, finite signed metrics, stdout/CSV agreement,
height×width/area consistency and unchanged binary hash before the next stage.
Root and reviewer separately checked all 57 frozen files and seven tools;
root also checked 47 original retained CACTI/DRAM files unchanged. Runner
integrity verification passed over all 106 receipt-bound artifacts. Raw receipt
SHA256 is `546423d415f9366a65159d441151caeb5c3a3e847c25ea991fb14067d1e9447a`.
Its `scientific_acceptance=unverified` and the generated report's pending-review
flag remain unchanged beside the separate independent acceptance.

## What this leaves open

The proposed row holds 161 instruction/reciprocal content bits plus 95 padding;
transient echo/status/client/owner fields remain outside SRAM. The 239 unique
reciprocal entries describe retained preparation, with no extra per-fetch lookup
under the declared denormalized mapping. Setup/loading and autonomous
cache/program/table preparation remain outside this experiment.

PR87's accepted 58,376,192 fetches/hash imply 1,868,038,144 local row B/hash
**under this proposed 32-byte mapping**. At the 1 MH/s objective, the necessary
aggregate demand is 58,376,192,000,000 requests/s and
1,868,038,144,000,000 local row B/s. This is demand only: no achieved H/s,
engine count, physical service supply or historical off-chip wire traffic follows.
PR91's bounded descriptor width is not retroactively a full-hash measurement.

The 256 MiB cache is a provisional external address partition; the accepted
dataset path recomputes items from it without assuming a materialized 2 GiB
dataset. Each context's 2 MiB scratchpad banking/ports remain unmodeled. The
retained gem5 DDR4_2400_8x8 metadata is a **static annotation**, not a simulation:
8 GiB/rank, 16 GiB/channel and a nominal 64-byte burst. Its refresh basis at
≤85°C is independent of SRAM360K; DRAM temperature is unknown.

Foundry process/PVT and SRAM characterization, realistic protocol/clock costs,
cache random-service supply and tails, controller/PHY/I/O/termination, complete
power, physical area/frequency, architecture selection and achieved hashes/s
remain unresolved. No additional hash, RTL, synthesis, gem5 workload or hardware
purchase is implied. Issue #72 remains open for those broader gates.
