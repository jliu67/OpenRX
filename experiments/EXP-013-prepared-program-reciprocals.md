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


## 2026-10-14 — Restore PR70 actual program-sequence regression gate

The historical head1345 source-only route skipped native/mapped integration.
The corrected gate unconditionally runs the existing --synthesize regression;
binding/rejection checks remain additional guards. Fresh serial server validation
passes9RTL/9mapped/4invalid/3actualsynthesis, with exact mapped/RTL PASS equality.
All219 original science inputs and accepted manifests/old-new binding digests stay
unchanged. Existing8×4 native v1/v2 tests, default8×2048 control contract and bounded
whole-top native gates are separate scopes; no --full-v2 rerun or full-pipeline
performance acceptance. Sources/complete outputs and superseded binding-only CI
artifacts are preserved. [Evidence](../docs/validation/prepared-reciprocals/README.md#restored-integration-gate--2026-10-14).
Independent exact-head review remains required; no merge. Compute slot released.


## 2026-10-15 — PR70 combined-source recovery closeout

[Task #69](https://github.com/jliu67/OpenRX/issues/69) reconciles reviewed PR70
`35c2cae61092107acb2c684bbca308aca8fb280b` with merged main
`5f28dd4363504ecf33a8f10451c53405773c564f`, preserving both parents and accepted
PR65/68. Strict combined bindings retain every historical manifest, all 219
original preparation inputs and 73 original sequence-regression inputs. Actual
native/mapped CI gates remain unconditional.

Verified server closeout covers 362 unit tests, seed18RTL/17mapped/3synthesis and
finalizer41RTL/19mapped/3synthesis, with native bytes and mapped/RTL records exact.
Original runner20261014T194137Z-8451bfb57fac remains PROCESS_FAILED: after unit/seed
commands returned0, an external wrapper KeyError:status prevented finalization.
Recovery20261015T194652Z-334cfc1d0428 ran only missing finalization from the same
3309-file frozen source. Both full receipts, sources, outputs and failure survive;
composite verification never relabels the original wrapper successful.

[Combined evidence](../docs/validation/prepared-reciprocals/combined-20261014/README.md)
binds commands, native/negative cases, complete archives, source/publication deltas
and resource checks. Both payloads used actual600%CPU/4GiBRAM/2GiBswap/Tasks256;
observed stage peaks1,097,007,104/1,921,708,032bytes, zero recorded swap/limit/OOM/
throttle events. Inherited simulation commands are sequential; no wall-time
throughput inference follows. Original prepared and sequence results are retained
exact-input proof, not newly rerun suites. Full-v2/full prepared pipeline, actual
dataset, calibrated timing and physical power remain unaccepted.

Next: hosted verification and a new independent review of the final exact draft
[PR #70](https://github.com/jliu67/OpenRX/pull/70) head, recorded on task #69. No own
merge or new milestone is authorized. This interrupted integration closes here;
recurring checks remain paused. Earlier dated sections retain their original context.
