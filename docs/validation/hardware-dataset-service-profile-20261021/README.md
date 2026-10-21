# Hardware-dataset service-demand profile — 2026-10-21

This is an independently reviewed **bounded analytical result**, built from
the accepted PR86 full-hash counters and existing PR74 envelope helpers.
[EXP-024](../../../experiments/EXP-024-hardware-dataset-service-profile.md)
records the method; [task #72](https://github.com/jliu67/OpenRX/issues/72)
remains open. Publication-head review and applicable hosted checks are separate
gates. No native/RTL workload or full hash was repeated.

## Inputs and provenance

The accepted functional source is public
`e8277c63504ef035bb82791263b6842c0cc51f51`, tree
`cb3e0615f9df861a081ba2cbb1d47c65603b84cd`, accepted in
[the PR86 review](https://github.com/jliu67/OpenRX/pull/86#pullrequestreview-5588318967).
The new sanitized [fixture](../../../tools/architecture/fixtures/accepted_hardware_dataset_v2.json)
is 2,581 B, SHA256 `fb6a6302dd6c57e835515c9e23ad39e2462e41885dc92bc49b48b056e0e96130`.
It contains reviewed aggregate counters and vectors, not private execution
journals or full traces. The module binds actual bytes before granting accepted
attribution, then validates schema, counts and nested clock relationships.

The original PR74 evidence/portable fixture bindings and comparison/sensitivity
gold remain unchanged. Its c96 software-assisted full result and bounded VM
bytecode windows are separate evidence domains; the new profile does not turn
those windows into an alternative complete-hash timing model.

## Result and scientific limits

[service-demand.json](service-demand.json) is the exact generated report;
[provenance.json](provenance.json) and [artifacts.sha256.json](artifacts.sha256.json)
bind its input and output bytes. [validation-summary.json](validation-summary.json)
is a sanitized summary of the bounded execution and review.

| Separate interface | Responses/hash | Minimum data B/hash |
| --- | ---: | ---: |
| Logical VM dataset output | 16,384 | 1,048,576 |
| Prepared-cache responses | 131,072 | 8,388,608 |
| Prepared instruction responses | 58,376,192 | 467,009,536 |

These are distinct nested links, not additive physical off-chip traffic.
Instruction payload counts only raw 64-bit words. Actual replies include optional
reciprocal validity, 32-bit index, 64-bit value and transport metadata. The 239
reciprocal entries describe retained data capacity, not independent requests.
Program/cache placement, local reuse, complete wire widths and physical traffic
remain unknown. The report separately records 256 MiB cache data, 32 KiB prepared
instruction capacity, 1,912 B reciprocal values and 2 MiB scratchpad per context;
metadata, ECC, queues and physical macro overhead are uncharacterized.

The modeled baseline is 918,672,902 outer clocks. Dataset availability 874,905,600
is nested in execution; core 874,889,216, superscalar executor 873,676,800 and
session-launch 16,384 are nested subdomains. Do not add them to the outer total.
All 36 latency rows are necessary conditional bounds using assumed latency and
ready-request capacity. They do not demonstrate overlap or physical supply.
Target 1 MH/s and 2.5 mJ/hash are requirements, not achieved performance or power.
Physical frequency, latency/service supply, achieved hashes/s, whole-wall power,
aggregate off-chip traffic and alternative full-hash cycles remain null or
unresolved. No physical PPA, memory technology or final architecture is accepted.

## Executed validation

The [approved request](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6306625245)
used the existing serialized local admission mechanism. All three commands
returned 0: 86 architecture tests including 19 new methods, historical reproduction
with both gold JSONs byte-identical, and the new profile CLI. All 32 bound source
files remained unchanged. Separate independent result review verified the
receipt, sources, fixture projection, counts, conditional bounds and limits;
acceptance is limited to this analytical profile. Original raw process receipts
remain scientific-unverified and do not themselves certify acceptance.

Observed command wall times were approximately 1.473 s, 57.551 s and 0.064 s.
These are validation costs, not RandomX throughput measurements. Actual prelaunch
kernel limits were CPU 600%, RAM 1 GiB, swap 2 GiB and Tasks 256; one payload slot was
used, with fresh available-memory/headroom and ancestor-limit checks. The
reproducer used six workers and reported 391% aggregate CPU. Its uneven bounded
windows and serial work do not guarantee six continuously busy cores. GNU time
reported maximum RSS 32,224 KiB for units, 32,008 KiB for reproduction and 16,264 KiB
for the CLI, with zero swaps; these per-command maxima are not aggregate pool
memory. The 1 GiB budget exceeded prior measured needs and remained enforced.

## Reproduction

From this repository, with a new output directory:

```bash
python3 -B -m unittest discover -s tests -p 'test_architecture*.py' -v
python3 -B -m tools.architecture.hardware_dataset \
  --evidence tools/architecture/fixtures/accepted_hardware_dataset_v2.json \
  --output NEW_OUTPUT_DIRECTORY
```

For historical reproduction, retain the unchanged commands in the
[architecture README](../../../tools/architecture/README.md). Significant local
execution still requires existing source/input binding and resource admission.
Preserve historical failures, accepted originals and all source/evidence records;
no additional long simulation follows from this profile.
