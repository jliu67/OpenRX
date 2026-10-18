# Native cache-backed dataset item: bounded evidence

Executed source `76d3ee59b3d02fccb258973d4a0b74dd4adb5d3f` (tree
`ef38f9820985a150cd2d569bc43cec6b59b76e53`) implements one eight-program
RandomX dataset item above merged PR #79, main `74a24e239b938ebaf4874ebd4dae47dd072ad41d`.
It wraps the unchanged accepted superscalar executor and multiplier. The
[interface](../../../rtl/dataset/DATASET_ITEM.md),
[experiment](../../../experiments/EXP-020-native-dataset-item.md) and
[actual source bindings](executed-source.json) define its scope.

All 4,793 actual regular files, Git blob bytes and execute modes match the clean
execution tree. All 181 consumed files remain bound to actual execution manifests;
the publication successor adds documentation, evidence and memory only.

## Correctness and evidence

The first admitted run, `20261018T175827Z-447be94ead08`, passes twenty native cases,
61,568 instruction states and 160 complete cache-XOR stages. Sixteen cases use
complete generated programs over two actual 256 MiB native caches; four cases
are separately labeled crafted controls, including eight 512-instruction multiply
programs and eight empty programs. Four upstream first-word anchors pass.
The provider reads actual cache bytes at the DUT-requested address; golden states
serve as assertions. Every traced stage distinguishes post-XOR address selection.

All twelve RTL profiles pass, including held/stale/malformed services, canceled
and reset work with changed-item/epoch recovery, full real transaction-generation
exhaustion, and bounded direct-multiplier comparisons. The native oracle calls
unchanged pinned v2.0.1 `initDatasetItem` and `executeSuperscalar`; it also verifies
the actual native prepared program and global reciprocal images.

The [correctness package index](correctness01/package-index.json) binds eight
public paths. Its two archives contain 896 verbatim fixtures and 52 records.
The origin inventory covers every one of 967 receipt artifacts: 896 fixture
copies, 49 selected original records, two retained raw cache images and twenty
other retained originals. The two 256 MiB cache files, executables and complete
raw execution remain retained and hash-bound. Their omission from the compact
Git package is not a missing scientific input.

Original correctness receipt SHA256:
`f3ced2d4f48eaa7c49359cea893c65666377c7f0a84386c035736357bfb59ad8`.
Manifest SHA256:
`08a0a963c68dec495201c3c82020db2d7cfdaca796ac9f6ff433af5474573bc7`.
The immutable runner's receipt still says `scientific_acceptance: unverified`.
Integrity verification and separate independent bounded scientific acceptance
establish different facts; the original receipt has not been relabeled.

Public metadata uses declared, reversible typed path aliases. Every exported
record binds original and public bytes. Portable receipts are derivatives and
cannot substitute for the original host-journal-bound receipt verification.
The correctness package's historical `mapping_pending` field describes that
package's scope; later mapping belongs to a separate supplement.

Both frozen packages passed separate independent audits. The correctness audit
is among the mapping archive's supplemental records; the
[final mapping-package audit](independent-mapping-package-audit.json) and its
[derivative provenance](audit-provenance.json) are indexed outside the frozen
seven-file mapping package. The mapping archive has 75 members: 39 selected
runner origins, 34 separately bound supplemental records, and two original
receipt/root-verification anchors. All 951 raw artifacts partition into 898
retained duplicate fixtures, 39 selected records and fourteen other retained
files. One metadata-only packaging attempt stopped on a resource-witness schema
mismatch before writing public files; its failure and the corrected helper
version are retained. No scientific payload was rerun or relabeled.

The [outer evidence index](evidence-index.json) binds these immutable packages,
source bindings and audit derivatives. Final publication-head identity/review
and hosted check outcomes are recorded on the draft PR.

## Component clocks and synthesis

| Actual full native item | Retired | Program multiplies | Ideal iterative clocks | Controlled stalled clocks | Direct ideal clocks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Canonical key, item 0 | 3,563 | 1,254 | 53,399 | 71,265 | 13,239 |
| Binary key, item 0 | 3,615 | 1,240 | 53,079 | 71,207 | 13,367 |

The [correctness component profile](correctness01/component-profile.json) derives
all sixteen actual full native item rows and separately labeled controls from
raw counters. Ideal default clocks close as `74 + 3*N + 34*M`; the bounded direct
comparison closes as `42 + 3*N + 2*M`. Executor clocks are a subset of total
clocks. Program-service and outer-service delays are disjoint additions;
held return clocks are excluded. These are modeled hardware clocks with declared
service behavior, separate from host command durations or physical timing.

Actual default generic synthesis produces 42,132 cells, 4,234 flops and zero
latches. The separate admitted mapping execution is
`20261018T180710Z-118e10af1b32`. All seven mapped comparisons pass, with raw PASS
records and per-success latency files matching the accepted RTL references.
The five-case mapped corpus includes two complete native items and three
crafted controls; the remaining fourteen full native items, 4,096-retirement
maximum and namespace-exhaustion modes are RTL-only. Separate independent
bounded scientific review accepts the actual terminal mapping evidence.

The [mapping supplement](synthesis01/package-index.json) covers all 951 original
receipt artifacts and binds the actual source/fixture reuse, synthesis outputs,
raw seven-mode comparisons, resource observations and independent reviews.
Duplicated fixtures, netlists and executables remain retained and explicitly
indexed. The original mapped receipt is
`5872e251d8c345f3ef4327b5c64ba023862c5c8cc7f8a2d7901ce7571ab19815`;
its original scientific-unverified classification is preserved.

The first correctness run used six independent simulator workers. Its largest
retained live cgroup `memory.peak` sample was 950,812,672 bytes; the final cgroup
was absent when sampled after completion. Both requests use the existing
one-slot immutable runner with actual six-CPU affinity, CPU quota 600%, memory
4 GiB, swap allowance 2 GiB and TasksMax256; admission rechecks actual kernel and
ancestor constraints and fresh headroom. These are measured workload budgets,
not host-wide settings changes or device resource measurements.
The mapping request's largest captured live cgroup `memory.peak` value was
1,288,343,552 bytes, with zero captured OOM/swap usage. Final observation found
the payload cgroup and owned PIDs gone and the global slot free. Captured live
peaks and periodic process samples are not a final absent-cgroup peak or complete
unsampled descendant accounting.

## Reproduction and remaining dependencies

The reviewed local requests and exact commands are on task #71:
[correctness request](https://github.com/jliu67/OpenRX/issues/71#issuecomment-6253220021)
and [mapping request](https://github.com/jliu67/OpenRX/issues/71#issuecomment-6253313573).
Use fresh output outside source through the existing reviewed admission and
global payload slot. For a complete reproduction with the pinned native CMake
fallback:

```text
python3 -B scripts/test_dataset_item.py --out FRESH_OUTSIDE_SOURCE --jobs 6 --synthesize
```

The hosted gate uses two workers, identical cases/assertions and the same command
timeouts, with the accepted pinned official Ubuntu container/toolchain. Local
correctness reused the exact retained `ARCH=native` native archive; hosted
reproduction builds the unchanged pin with `ARCH=default`. Build identities are
distinct and fixture equality must be checked from actual hosted artifacts.
Synthesis-only reuse requires the prior complete output, original receipt,
externally bound receipt SHA and original root verification, validating actual
source and all 898 fixture bytes before reuse. No native initialization or
completed RTL mode is repeated in that request.

Argon2 cache initialization, superscalar program generation and global reciprocal
preparation remain host software. Prepared immutable image export, tagged cache/
program/table service, the lifecycle bridge and a fully connected hash remain
external. The finite transaction-generation budget requires admission reservation
and a quiescent drain/reset before identity reuse. No full 2 GiB dataset image,
streaming dataset initializer, new full 8×2,048 hash, physical frequency/area/power,
memory technology or architecture choice is established. The whole-machine
1 MH/s below 2,500 W target remains unproven. Draft publication and independent
review do not authorize the author to merge this feature.
