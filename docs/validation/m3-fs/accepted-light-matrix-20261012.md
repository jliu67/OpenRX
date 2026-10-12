# Independently accepted bounded light matrix — 2026-10-12

[Task #16 terminal acceptance](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891) and the
[verified hub bot](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6129544314)
record the actual completed execution below. This note is a non-identifying
summary of those accepted results, not a substitute for retained private review,
raw serial, request, inputs or immutable runner receipts.

| Binding / result | Accepted record |
|---|---|
| Execution | `20261012T032030Z-65cbb4c0cf9e` |
| Executed scientific source | `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726` |
| Required light controls | 39 passes: 31 arithmetic + eight v2/v1 interpreter/JIT software hashes |
| Linux runtime controls | Nine passes |
| Optional hardware AES | One explicit skip; not passed |
| Guest/wrapper completion | Both guest statuses zero; wrapper/gem5 return zero |
| Serial acceptance | Complete stdout/stderr frames, empty guest stderr, completion and ordered hypercalls 1/2/3 |
| Reviewed integrity | 23 input/source bindings; 26 receipt artifacts; exact request mapping/journal chains and final stability checked |
| Lifecycle | Actual execution processes/cgroup gone; heavy slot released; no successor launched by the closeout |
| Broader issue status | #16 open; monitoring claim released and router-ready/unclaimed at terminal readback |

Retained independent raw review SHA-256:
`aab23d1db1a8f51e4b92b7434bc42d6fab3fdcb16823a2ef1a55f29b65b61042`.
Immutable runner receipt SHA-256:
`272095c1988874437aff62fbcb7b64e1a5432474d20f8d25e1f81cdf55dcb679`.
Detailed host records and private review artifacts remain retained privately.
The digest of this selected summary differs from both raw records; do not treat
it as an identical receipt or a new scientific/source acceptance.

The independent terminal review accepted all recorded request/source/input,
receipt/journal, generated-payload, raw-frame, runtime/hash, completion/drain and
stability gates. Earlier intermediate/partial observations, timeout/OOM/stop
attempts and original builds remain under their own immutable identities. The
newer repository documentation head does not identify the executed source,
relabel a rebuilt binary or rewrite any acceptance receipt.

This accepts functional **light-mode** correctness in the declared scalar gem5
Linux configuration. Full-dataset, intended-core/SMP, BOOM/selected-core,
calibrated timing, physical power, RTL, ASIC design and M1–M5 remain open.
No throughput, efficiency, competitive PPA or isolated cache-flush/SMP mechanism
is inferred from completion. A skipped optional case remains unexecuted.

The documentation author verified the live public result/release and hub bot
and the byte identities/status/source of small retained private review and
receipt records. The author did not rerun the matrix, replay the simulator,
rehash large scientific inputs or independently repeat the accepted science.
The public note exports only the already published selected counts, source/
execution IDs, digests and acceptance boundaries; private host detail is omitted.

Next native work is only diagnostic tiny-supervisor-fixture preparation/
validation, not a launched or accepted benchmark pilot. Any future scientific
payload needs its own reviewed request/source/runner/input bindings, fresh
host/kernel resource admission and serialized slot. Current host health or a
later free slot is not established by this dated terminal record.

Related records: [current board](../../TASKS.md), [handoff](../../../memory/HANDOFF.md),
[EXP-002](../../../experiments/EXP-002-riscv-functional-preflight.md) and
[retained earlier attempt index](README.md). The review/CI/merge state of this
documentation proposal belongs to [task #45](https://github.com/jliu67/OpenRX/issues/45),
not to the executed science's receipt or gate status.
