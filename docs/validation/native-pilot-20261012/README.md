# Independently accepted exploratory native pilot — 2026-10-12

[Owner terminal review](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969) and [verified hub publication](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6130767113)
accept execution `20261012T185152Z-97e747b1f6c4` for the scoped exploratory pilot.
It started at 18:51:54Z and exited zero at 18:55:54Z. This is one setting with
two balanced v2/v1 repeats, **not the complete formal #8/EXP-001 baseline or M1**.

Native source: `4a4e30bbbda47cce7713c280d87f1506f7c6f954`. Reused binary SHA-256:
`a1ebd867a845640e5d080be77806942dde0f6f51e45db7a9a93c5e6e047817cf`.
Request SHA-256: `f7b1dc10342cd324f69fd91226cf52398f9dd63b3e2dc670e48cb5f62b4871e5`.
Receipt SHA-256: `c40731805b4ad49b879402765bd8985066656d797632b8aa346b6110c37dda11`.
Separate independent review SHA-256:
`73b8703c1547b777d94806fdea0e0e61f05cf493df3948ab038377a82a7c87ae`.
Terminal index SHA-256:
`e59d8b88bee7f572debbd0d1c0b2149e858f726ded6f8374a0354903d4ddf3d1`.
The immutable runner receipt keeps `scientific_acceptance=unverified`; separate
review grants exploratory-pilot acceptance. No receipt/source is rewritten or
relabelled with this newer documentation head.

## Declared configuration and all interval observations

Six hash workers, two initialization workers, hardware AES, full-dataset/JIT,
seed 0, small pages; 1,000-nonce controls/warmups and 90,000 measured nonces.
Minimum interval 30 seconds, supervised outer deadline 1,200 seconds. One
scientific workload was admitted; no retry or scientific parameter change.

| Version/repeat in actual order | 90,000-hash interval (s) | Measured hashes/s |
|---|---:|---:|
| v2/1 | 62.997949 | 1428.618 |
| v1/1 | 49.577410 | 1815.343 |
| v1/2 | 49.619262 | 1813.812 |
| v2/2 | 59.534099 | 1511.739 |

Owner-reported medians: v2 **1470.178 H/s**, v1 **1814.577 H/s**.
Repeat range divided by mean: v2 **5.654%**, v1 **0.0844%**. These are observed
native-adapter interval measurements; two repeats supply no formal dispersion
or confidence claim. They are not whole-machine X9 comparisons, chip/core PPA,
BOOM/calibrated-model rates, power or energy efficiency.

## Scope of the independent acceptance

All 12 records were present: configuration, two known controls, four known
warmups, four measurements and completion. The independent review verified the
unchanged strict validator, order/counts/clocks/durations, known references,
same-version repeat digests, empty stderr, native/wrapper/outer return zero and
no interruption. The 90,000-hash aggregates have **no independent trusted
reference**; controls and repeat determinism provide the declared evidence.

After exit/drain, all 1,519 original executable/input/source bindings were
freshly rehashed under the immutable runner. Copied-runner/exclusive-request,
receipt/artifact/external-journal integrity and saved review proofs passed;
the named cgroup, original event processes and active managed units were gone,
and the execution lock was free. Complete 21 raw execution artifacts plus
post-run/review proofs remain retained under the owner's terminal index.
These are accepted owner/reviewer records, not a new rehash or replay by the
documentation author, nor a fresh current host-idle/health observation.

Preserved attempt04 rejected a redundant compiler symlink before request
reservation/execution creation. Attempt05 removed only that redundant input;
its bound regular compiler target and post-run alias resolution remain the
same. No failed attempt or duration/control rejection is deleted or converted
into a pass. Detailed host information and raw receipts remain retained;
this note exports already authorized rates and selected non-identifying fields.

## Remaining gates and next preparation

No thermal equilibrium, isolation, constant frequency, external clock alignment,
power, energy/hashes-per-joule or PMU result is established. Formal #8 needs the
complete balanced thread/AES matrix, at least four balanced repeats, sufficient
duration, controlled settings and retained raw evidence. #10/#11 retain their
physical-instrument/counter prerequisites; M1–M5 and selected-core/calibration/
RTL/ASIC gates are open. Prepare a separately reviewed formal request using
accepted tools/builds; this evidence note authorizes no workload or setting change.

The [accepted #16 light matrix](../m3-fs/accepted-light-matrix-20261012.md) remains
separate at scientific source `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`: 39 required
plus nine runtime controls, optional AES skipped, broader gem5 full-dataset/
intended-core/SMP open. Native full-dataset operation does not prove those gates.
Related [board](../../TASKS.md), [handoff](../../../memory/HANDOFF.md) and
[EXP-001](../../../experiments/EXP-001-native-baseline.md) preserve the unchanged
formal acceptance criteria and source/build/history identities.
