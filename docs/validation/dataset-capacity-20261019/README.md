# Dataset session capacity evidence — 2026-10-19

Pre-admission scaffold. No new runtime, mapped pass, default full hash or physical
performance is claimed. Read [EXP-022](../../../experiments/EXP-022-dataset-session-capacity.md)
and the [session contract](../../../rtl/dataset_capacity/DATASET_CAPACITY.md).

Base is merged PR #81, `a84602c5348723e4c388ccd50f3a16096f3054f9` / tree
`17b01d8f9bf0aeeaa8cf5b75f73f2b8b2be6df63`. Accepted item, executor, multiplier,
service, wrapper and their original tests remain unchanged. New integration lives
under `rtl/dataset_capacity/`, with full 64-bit provider tags and checked wider
reservations. Raw child clocks and measured session availability remain separate.

Planned checks cover the actual 16,384-item reservation/completion capacity,
131,072 private program admissions, stale packets with identical low tags and
metadata, cancellation/error/held responses, exact reduced-namespace exhaustion,
default hardware elaboration, bounded native 2×1 equivalence and short mapped
parity. The capacity stress is an explicit protocol derivative; it is not a
reference-correct default RandomX hash.

The [reference lock](../../../rtl/dataset_capacity/reference-2x1.lock.json) binds
nineteen deterministic reused 2×1 native gold files. Prepared asset identities
come from the accepted context lock and public fixture index. Lock-only identity
and raw original journal verification remain separate modes; original scientific
flags are unchanged. Complete private journals remain local. Public closeout
will contain compact technical results and public source identities.

A six-CPU/4-GiB-RAM/2-GiB-swap candidate fits the current observed host headroom
and prior 2.08-GB peak, subject to fresh under-lock admission checks. No resource
or workload reservation is implied by this estimate. Full-hash time estimates
remain conditional scenarios; no long default hash is scheduled here. Native
assertions remain host work; cache/superscalar/global-reciprocal preparation,
physical services, canonical full hardware hash and physical PPA remain open.
