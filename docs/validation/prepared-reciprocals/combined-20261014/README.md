# PR70 combined-source validation and interrupted-run recovery

[Task #69](https://github.com/jliu67/OpenRX/issues/69) reconciles reviewed PR70
`35c2cae61092107acb2c684bbca308aca8fb280b` with merged main
`5f28dd4363504ecf33a8f10451c53405773c564f`, retaining both parents and accepted
PR65/68. The executed source is the complete 3,309-file frozen tree
`29ac1af8dff303dddd8f84ce0a79fb369f333ec0`; its original-mode source archive SHA-256 is
`1002c56e3e1bbcb6bb07a995d9a41114ed6a14eddb6b07565461bd7220d33911`.
The publication adds only declared documentation/evidence successors. Every executed
scientific/provenance input retains its tested bytes and execute bits.

The additive [combined declaration](../combined-source-bindings.json) pins exact
reviewed execution RTL successors, staged driver/CI successors and historical
manifest identities. The original declaration and every old manifest remain
unchanged. All 219 original preparation inputs and 73 original program-sequence
regression inputs match their preserved executions. Their results are retained
original-base proof; those suites were not rerun in this recovery. Actual
native/mapped CI gates remain unconditional, with binding checks added alongside.

## Actual execution and recovery

Original immutable-runner execution `20261014T194137Z-8451bfb57fac` completed 362
repository unit tests and the seed driver with return code zero. It then failed
with `KeyError: 'status'` in its external orchestration wrapper: the accepted seed
summary schema has no generic `status` field. Finalization had not started. The
runner, failed process result, exact traceback, complete outputs, source and old
wrapper remain preserved. The usage interruption did not cancel this payload.

Finalization-only recovery `20261015T194652Z-334cfc1d0428` uses the identical frozen
source and a separately bound wrapper/request. It runs only the missing existing
`test_scratchpad_finalization.py --synthesize` command. The original failed wrapper
is never relabeled successful. Composite closeout requires separate runner
integrity, terminal/drain, source and component checks for both attempts.

| Verified scope | RTL modes | Mapped modes | Actual synthesis jobs | Attempt |
| --- | ---: | ---: | ---: | --- |
| Seed/register-file hashing | 18 | 17 | 3 | Original completed component |
| Scratchpad finalization | 41 | 19 | 3 | Finalization-only recovery |
| Total component modes | 59 | 36 | 6 | Two separately verified attempts |

All 362 repository unit tests passed in the original attempt. The recovered
component records and native fixture bytes match the preserved original results;
mapped outputs agree with RTL. The original orchestration failure remains explicit.
No skipped or expected-failure case is counted as a positive pass.

Seed coverage includes 524 native register frames per digest size, independent
digest comparison, v1/v2 hardware-seed chains, held/reset/errors and cancellation.
Exactly seven hardware seeds per eight programs add 414 fixture clocks. Connected
v2 ideal/stalled clocks are 111,348/185,810; v1 clocks are 70,524/121,278. These
chains execute eight programs × four iterations with an addressed fixture dataset
and the default runtime-reciprocal backend, not a complete prepared hardware hash.

Finalization covers 14 native cases, actual scratchpad bytes, four full 2 MiB RTL
trials in case order actual/pattern/pattern/actual (ABBA), with memory profiles
ideal/stalled/ideal/stalled, bounded controls and mapped checks. Each full case is
exercised under both memory profiles.
Each full trial performs 131,072 reads; ideal/stalled primary-response latency is
393,284/1,048,649 modeled clocks. Default 2 MiB mapped checks are restart-only;
they do not complete a full native mapped finalization. Both original-IP expected
failures, six malformed-native cases and four invalid hardware-parameter guards
are recorded separately from positive passes.

Both attempts used immutable runner657, actual CPU `600000/100000`,
4,294,967,296-byte RAM, 2,147,483,648-byte swap, Tasks256 and six allowed CPUs.
Fresh admission checked the global lock, kernel/ancestor constraints and headroom;
the recovery worker observed 8,349,945,856 available bytes before launch. One
scientific command ran at a time. The inherited sequential simulator workloads
use one core; the quota permits six. Observed payload-stage memory peaks were
1,097,007,104 bytes for the original unit/seed attempt and 1,921,708,032 bytes for
finalization. Recorded stages show zero swap, memory-limit/OOM or CPU-throttle
events. Terminal verification confirms both attempts drained before postprocessing.
These resource and duration records are operational evidence, not controlled
native throughput, physical timing or power measurements.

## Evidence and preservation

- [Composite terminal verification](coordination/raw/combined-terminal01.json)
  keeps the failed original attempt and successful recovery distinct.
- [Exact evidence comparison](coordination/raw/combined-evidence-comparison01.json)
  checks actual logs, native bytes, mapped/RTL equality, synthesis/netlists and the
  unchanged original 219/73 inputs. This is coauthor verification, not independent review.
- [Scientific ledger](science-ledger.json) records every actual positive PASS,
  mapping result, profile and scoped boundary.
- [Complete source/output retention](source-output-retention.json) identifies two
  complete runner archives and the component member prefixes. All original bytes,
  execute bits, failed attempts and prior evidence remain retained on the server.
- [Raw/public preservation map](raw-public-preservation-map.json) distinguishes
  exact raw hashes, lossless compressed logs and separately hashed portable JSON
  derivatives. Portable copies are not original receipts.
- [Exported public-file hashes](public-files.sha256.json) cover the export payload;
  this README is the subsequent publication description. Opaque binaries,
  netlists and large memory images require access to the full retained archives.

The original directed reciprocal results remain in the [parent evidence](../README.md):
preparation plus execution is 370,444→159,376 ideal clocks and
398,580→187,512 stalled clocks, including 70,356 preparation clocks and all reloads.
Prepared mode adds 3 KiB constants. Original generic cache/control mapping and
these directed cycle savings establish no full-hash throughput or physical power.

The whole-machine goal remains 1 MH/s under approximately 2,500 W, including logic,
scratchpad/dataset memory, controllers/interconnect, clocking and conversion/cooling.
Complete prepared 8×2,048 integration, actual dataset, calibrated timing and physical
PPA remain open. No full-v2 rerun or complete-pipeline/efficiency acceptance follows.
Hosted verification and new independent review apply to the final exact PR head;
their later records belong on task #69. No own merge is authorized.
