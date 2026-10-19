# EXP-021: prepared dataset service in the bounded hash lifecycle

Three native-equivalent 2×1 profiles, five recovery prefixes, 32 unit checks
and service RTL pass. Mapped outcomes match RTL; terminal integrity is verified and independent
bounded review accepts the results with no blockers. Public code `f22ad4b722ba6f04fcff4d56f425b6e84f124220`
has the exact frozen executed tree `bbadcf7edcaecad946ad91cbabf60f9dbac81cc6`,
above merged [PR #80](https://github.com/jliu67/OpenRX/pull/80).

The [service/wrapper](../rtl/dataset_service/DATASET_SERVICE.md) captures immutable
asset epoch/descriptors for a whole hash, preserves DS byte addresses and full
32-bit transaction tags, and returns raw items for the engine's one XOR.
Cancel/error drains stale traffic without resetting transaction identities.
Every admitted hash burns all `PROGRAMS*ITERATIONS` item reservations, including
failed/canceled attempts, from an 8,191-item reset-lifetime budget. Only a
quiescent hard reset restores capacity. Legacy `HARDWARE_DATASET=0` remains
default; hardware default 8×2,048 fails elaboration explicitly.

Cache-0 for `test key 000`, eight superscalar programs, 239 reciprocal entries
and the retained native PIC archive are reused. No Argon/cache/superscalar
preparation or archive rebuild was repeated. Two new bounded native gold items
feed comparison of every VM retirement, program boundary, complete 2 MiB
scratchpad and final digest. Recovery controls are prefixes, not completed hashes.

| Normal profile | Outer modeled clocks | Item availability clocks | Live native dataset calls |
|---|---:|---:|---:|
| Software dataset, ideal | 534,382 | 0 | 2 |
| Hardware dataset, ideal | 641,180 | 106,798 | 0 |
| Hardware dataset, controlled stalls | 1,754,983 | 171,082 | 0 |

The ideal outer/execution/dataset-wait deltas each equal 106,798: two items at
53,399 clocks, each 53,325 executor + 74 item-control clocks. Dataset phase bins
include two response-handshake clocks; availability excludes held-return time.
Item/executor/stall costs are nested inside execution. The stalled profile also
delays other services; its full outer delta is not a dataset-only measurement.

Service-top synthesis includes the unchanged item/executor/multiplier children:
45,670 generic cells, 4,761 DFF cells, zero latches. This excludes whole-lifecycle
mapping and physical timing/power/area. Read [compact evidence](../docs/validation/dataset-lifecycle-20261018/README.md)
for source identity, provider separation, exact clocks and remaining gates.
The controlled oracle keeps `canonical_randomx_calculate_hash_verified=false`.
Native assertions and direct reference setup remain host work; live input/fill/
program/dataset callbacks are zero on hardware normal profiles. Autonomous
cache/superscalar-program/global-reciprocal preparation, tagged physical cache/program/table/scratchpad
services, full default hardware-dataset validation and physical PPA remain open.
Original scientific-unverified flags and all complete originals are preserved.
