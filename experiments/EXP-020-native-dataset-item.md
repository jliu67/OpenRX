# EXP-020: native cache-backed dataset-item controller

Status: first admitted native/RTL correctness run passed and independently
accepted; separate synthesis and all seven mapped comparisons passed and received
independent bounded scientific acceptance. Publication gates remain separate.

This bounded component starts above accepted main
`74a24e239b938ebaf4874ebd4dae47dd072ad41d` (PR #79). It wraps the unchanged
prepared superscalar executor and multiplier to compute one 64-byte native
RandomX dataset item from a full 64-bit item number, eight immutable prepared
program descriptors, their global reciprocal table, and an immutable native cache.
It does not change existing VM or lifecycle defaults.

The controller captures the cache index before each program, executes that
program, XORs the matching eight cache words, then selects the next address
from the post-XOR registers. Register seeding and unsigned wraparound follow
pinned v2.0.1 `dataset.cpp`; all eight programs and the final eighth XOR are
required. See [the interface](../rtl/dataset/DATASET_ITEM.md).

## Validation method

The native oracle initializes two fixed real 256 MiB caches using the unchanged
pinned library. It exports actual cache bytes, the eight prepared programs and
shared reciprocal table, and compares independently traced stages with native
`initDatasetItem`. Full-width helper corner items are explicitly distinguished
from legal full-dataset item indices. Golden registers are assertions only;
the cache provider reads by the actual requested index.

The first admitted correctness run is `20261018T175827Z-447be94ead08`,
from clean source `76d3ee59b3d02fccb258973d4a0b74dd4adb5d3f`, tree
`ef38f9820985a150cd2d569bc43cec6b59b76e53`. All 4,793 actual regular files,
Git blob bytes and execute bits match that tree. Both accepted executor and
multiplier bytes remain unchanged.

Twenty native cases pass all 61,568 instruction states and 160 completed cache
XOR stages, including sixteen full generated-program items over two real cache
keys. Four canonical first-word anchors pass. All 160 traced stages distinguish
the post-XOR address from the pre-XOR selected register. The separately labeled
crafted maximum case executes eight 512-instruction multiply programs, returning
4,096 retirements and 4,096 multiplies. An empty eight-program context still
performs all eight cache XORs.

All twelve RTL profiles pass. Matching service/descriptor errors return the
specified prefixes and counters; cancellation and reset each cover eighteen
aborts plus eighteen changed-item/epoch completions. Real public transfers
exhaust the executor and outer identity namespaces, including the final legal
item and fail-closed cancellation behavior. Two direct-multiplier profiles
retain a separately scoped five-case comparison.

Verified receipt SHA256 is
`f3ced2d4f48eaa7c49359cea893c65666377c7f0a84386c035736357bfb59ad8`;
manifest SHA256 is
`08a0a963c68dec495201c3c82020db2d7cfdaca796ac9f6ff433af5474573bc7`.
Original runner scientific acceptance remains `unverified`; integrity verification
and bounded independent scientific acceptance are separate records. Complete
sources, all 898 fixture files (including both 256 MiB cache images), executables,
commands, logs, measurements and receipts remain retained.

## Measured component clocks

| Actual complete native item | Retirements | Program multiplies | Ideal iterative clocks | Controlled stalled clocks | Direct ideal clocks |
|---|---:|---:|---:|---:|---:|
| Canonical key, item 0 | 3,563 | 1,254 | 53,399 | 71,265 | 13,239 |
| Binary key, item 0 | 3,615 | 1,240 | 53,079 | 71,207 | 13,367 |

Every successful ideal default result closes exactly as `74 + 3*N + 34*M`;
the five-case direct profile closes as `42 + 3*N + 2*M`. The fixed part includes
seed multiplication and control/cache handshakes. The two controlled stalled
native items add 17,811/18,073 executor-service clocks and 55 outer-service clocks
each. Executor time is a subset of total time, not an additional charge.
Held result clocks are excluded. These are modeled hardware clocks with declared
service behavior, not physical elapsed time or a full-hash latency equation.

Native cache initialization is separately measured host software: 0.848457 and
0.833535 seconds in this run, with export durations retained separately. The
existing pinned native archive is reused; no completed library build, earlier
PR79 validation or full connected hash was rerun.

Separate admitted execution `20261018T180710Z-118e10af1b32` passes actual default
generic synthesis and all seven mapped profiles over the same exact source and
all 898 verified fixtures, with no native/Argon initialization or completed RTL
regeneration. Its five-case mapped corpus contains two complete generated-program
native items and three crafted controls; other full native items, the 4,096-count
maximum and real generation-exhaustion profiles remain RTL-only. Raw PASS strings
and per-success latency bytes match the original RTL references.

Actual mapping gives 42,132 generic cells, 4,234 DFF cells and zero latches. The
mapped five-case ideal/stalled totals are 107,388/143,787 modeled item clocks,
including 107,018/143,142 executor clocks respectively. These executor values
are subsets of each total. Root integrity verifies 951 receipt artifacts;
receipt SHA256 is
`5872e251d8c345f3ef4327b5c64ba023862c5c8cc7f8a2d7901ce7571ab19815`,
manifest SHA256 is
`feb803e55f01fdac7ad90c4ab126f7cf905f400dc57200cf14b3980d97d70d7c`.
Original runner scientific-unverified status stays unchanged. Independent mapped
review SHA256 is
`acbf8ff5b8bf631e408d28f52c5a5d24e68e3feaa0efefb5aff0082950cbe871`;
public derivative audit and final exact-head/hosted checks remain separate gates.

## Boundaries

Argon2 cache initialization, native program generation and reciprocal preparation
remain software. Prepared images and physical cache-read service remain external.
The finite transaction-generation budget requires admission reservation and a
quiescent reset before identity reuse. This is one item component, not a full
streaming dataset initializer or a newly connected full hash.

Modeled hardware clocks, host command duration and generic synthesis counts are
separate quantities. No physical frequency, area, power, memory technology,
engine count or issue width is selected. The whole-machine target of 1 MH/s
below 2,500 W remains unproven.
