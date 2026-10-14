# EXP-013: immutable-program reciprocal preparation candidate

[Task #69](https://github.com/jliu67/OpenRX/issues/69) applies the owner-approved reciprocal priority above accepted main `8f3b9bc3d7f0182d66185abe95310f0bab00274b`. The unchanged RandomX pin and exact integer/floating/rounding/memory criteria remain.

Test the hypothesis that active IMUL_RCP preparation at admission removes repeated reciprocal work while preserving native results. Pair identical immutable program storage/fetch paths, exact native workload and event-ordinal memory profiles; charge every reload. Balance configurations ABBA. Reject nonclosing clocks, different common work, runtime recalculation, missing preparation charges and unknown stages represented as zero.

[Design and evidence](../docs/validation/prepared-reciprocals/README.md) records eight accounting tests, 48 native iterations/12 admissions, 11 RTL/four mapped checks, three intentional invalid elaborations, one skipped complete-pipeline gate and four retained failed attempts. Final unexpected failures: zero.

| Profile | Baseline clocks | Prepared clocks | Added preparation | Saved execution | Net saved |
| --- | ---: | ---: | ---: | ---: | ---: |
| ideal | 370,444 | 159,376 | 70,356 | 281,424 | 211,068 |
| stalled | 398,580 | 187,512 | 70,356 | 281,424 | 211,068 |

These are measured RTL clocks on a directed reciprocal-heavy native corpus. Preparation costs 70,356 clocks and execution saves 281,424, calibrated to 66 clocks per active reciprocal; the net stage delta is 211,068 in either memory profile. No full-hash performance acceptance follows.

| Actual default mapped target | Generic cells | Flops | Latches |
| --- | ---: | ---: | ---: |
| cache-0 | 75,979 | 24,877 | 0 |
| cache-1 | 152,277 | 49,640 | 0 |
| guard | 390 | 0 | 0 |

Actual generic default new-store/control and guard mapping is distinct from complete prepared-backend mapping and physical PPA. Both modes retain 3 KiB instruction storage; prepared mode adds 3 KiB constants. All protected originals and failed/executed sources remain retained.

[Surrounding stage ledger](../docs/validation/prepared-reciprocals/surrounding-stages.json) binds exact draft PR65/68 evidence without changing their refs or acceptance. Complete pipeline costs remain null: initial input hash/fill, program AES generation, actual dataset/calibrated memory, connected 8×2048 prepared execution plus interprogram/final hash, intended-core timing and physical PPA are missing. EXP-001 controlled native throughput/energy criteria remain unchanged.

Next: independent exact-head implementation/evidence review; integrate a complete comparable baseline before any full-hash claim. Then evaluate 1/2/4/8/16-context single-issue blocking/nonblocking, dependency-proven overlap and justified dual/wider issue as separately bounded work. This task implements none of those architectures and authorizes no own merge.


The postpublication CI successor preserves all scientific input bytes and original
acceptance manifests. Hosted run 38502375710 failed the inherited strict binding
before native compilation; its complete record is retained. Exactly two executor
successors now have an explicit old/new declaration and rejection guards. Candidate
hosted checks are bounded source/evidence checks; inherited complete program-sequence
native/synthesis replay remains deferred and unexecuted pending a fresh authorized
serial server admission. See the [CI correction](../docs/validation/prepared-reciprocals/README.md#hosted-source-binding-correction).

Bounded CI successor checks pass 12 parent rejection tests and eight accounting tests with the source/evidence guard. Fresh metadata payload wall837ms/peak21762048bytes, no swap or limit/OOM/throttle events; all219 science inputs unchanged. These checks do not replay the inherited scientific suite.
