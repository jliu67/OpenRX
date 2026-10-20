# Accepted default hardware-dataset hash — 2026-10-20

One RandomX v2 default 8×2,048 functional hardware-dataset hash is
[independently accepted](https://github.com/jliu67/OpenRX/pull/86#pullrequestreview-5588318967)
at public [source `e8277c63504ef035bb82791263b6842c0cc51f51`](https://github.com/jliu67/OpenRX/commit/e8277c63504ef035bb82791263b6842c0cc51f51),
tree `cb3e0615f9df861a081ba2cbb1d47c65603b84cd`, above
[PR83](https://github.com/jliu67/OpenRX/pull/83). The separate reviewer's shared-account
technical COMMENT accepts this functional result; source publication, hosted checks
and normal merge are separate evidence gates.

[PR86's normal dependency merge `af1e23d3`](https://github.com/jliu67/OpenRX/commit/af1e23d384c4d23d007da816bd8b97ff12712a34)
retains the accepted tree on PR83's feature branch. [Current status](../../STATUS.md)
records source publication separately from accepted execution and preserves
[PR85](https://github.com/jliu67/OpenRX/pull/85)'s earlier documentation reconciliation.

## Coverage and evidence boundary

Successful termination and pinned source/model/native-reference provenance support
16,384 iteration-state assertions, 16,384 dataset-result assertions, 1,346,699
bytecode-access assertions, eight complete 2 MiB scratchpad boundaries, seven
hardware seed transitions and canonical final-digest equality. Both testbench PASS
records and the full-hash validator passed.

The validator and a fresh independent reviewer each streamed all 28,026,133 retained
trace records. Exported addresses, instruction/access counts and order, port-byte
totals and outer/iteration/executor phase closure agree. Data/register values absent
from exports remain exact bound-testbench assertion evidence. Native assertion-oracle
program images come from DUT-derived seeds; the bound testbench separately compares
the hardware-generated images and fetched words.

## Modeled clock accounting

The measured modeled total is 918,672,902 clocks. Dataset availability is nested
within execution; core and executor clocks are further nested, not extra outer cost.

| Quantity | Modeled clocks | Accounting relationship |
| --- | ---: | --- |
| Whole hash | 918,672,902 | Outer total |
| Execution stage | 918,128,359 | Within outer total |
| Dataset availability | 874,905,600 | Within execution |
| Dataset core | 874,889,216 | Within availability |
| Dataset executor | 873,676,800 | Within core |
| Dataset launch | 16,384 | Within availability, alongside core |

Actual 3/3/9 dataset phase vectors were emitted and checked against the complete
nested ledger. Source-derived expected vectors remain equations; their agreement
with emitted vectors does not turn the earlier failed attempt into a measurement.

## Preserved history and remaining boundaries

The earlier failed full attempt remains failed and scientifically unverified. Its
missing original dataset ledger and phase vectors remain absent. Preparation,
prefix, EOF and closeout failures are retained. Original runner scientific flags
remain unchanged; the validator and independent technical review record separate
functional acceptance. The earlier software-assisted c96 result remains a distinct,
source-specific result.

Live software input/fill/program/dataset provider calls, including assertion-only
dataset callbacks, are zero. Separately allowed input/program assertion counts are
one/eight. Retained cache/superscalar/reciprocal preparation and modeled host
cache/program/table/scratchpad memory services remain explicit. Autonomous setup,
physical memory/controller services, frequency, physical PPA, architecture selection
and the whole-machine 1 MH/s below 2,500 W objective remain unvalidated. This accepted
hash needs no additional scientific run.
