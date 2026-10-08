# Hardware evidence and targets

## X5 baseline
Prior discussion identifies Sophgo SG2042 / T-Head C920 as a candidate based on a public teardown discussion. This setup has not independently inspected board images or firmware. Do not call the exact silicon, processor count, cache topology or mining software verified.

Research leads:
- Teardown discussion: https://bitcointalk.org/index.php?topic=5468681.0
- Vendor hardware resources: https://github.com/sophgo/sophgo-hardware
- Pioneer documentation: https://github.com/sophgocommunity/Pioneer_Doc

Record evidence ID, direct quotation or precise location, revision/date, measured versus advertised status, and uncertainty. Separate SG2042 specifications from what an actual X5 board implements.

## Aspirational comparisons
Prior conversation cites X5 212 kH/s at 1350 W and X9 1000 kH/s at 2472 W. These are unverified leads in this repository. Arithmetic on those values gives 6.368 J/kH and 2.472 J/kH respectively. Neither is a measured v2 comparison. No X9 architecture or cancellation fact is established here.

Actual acceptance requires same workload version, sustained operation, declared whole-system power, thermal conditions, costs, and correctness. Per-core simulation cannot be scaled linearly into a whole-miner claim without memory, interconnect, PSU and cooling accounting.
