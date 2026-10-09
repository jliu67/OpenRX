# Independent actual guest evidence review

The stopped attempt supplies accepted partial functional evidence: all nine runtime controls and all 31 integer/FP semantic controls passed independent replay. It supplies **zero hash values** and does not pass the complete light gate. The larger proposed `100000000000000` tick allowance has not been executed.

`matrix_review` replayed the saved raw evidence and bindings on 2026-10-08T23:56–23:58Z. The machine-readable result is [review.json](review.json).

| Acceptance item | Observed result |
|---|---|
| Runtime controls | 9/9 exact passes; guest exit 0; one complete frame and empty stderr frame |
| Integer/FP controls | 31/31 exact passes: seven integer and 24 FP controls |
| Required software-AES hashes | 0/8 values present |
| Cache stages | Interpreter `cache-init` begin with flags 0; no cache pass record |
| Complete light summary | Absent; strict full validator rejects the partial stream |
| Hash end and stderr frames | Absent |
| Guest completion marker | Absent |
| Linux/after-boot sequence | Hypercalls 1 and 2 only; hypercall 3 absent |
| Successful simulator exit | Not established; actual child return code unavailable |

## Raw replay and source binding

All 11 entries in [raw-manifest.json](raw-manifest.json) matched their saved checksums and original attempt files. The base64-encoded DTB also matched its original bytes after decoding. The final raw serial is 23,713 bytes with SHA256 `9092252d20ff4767d92cff0b89980b9df034afd5070f927cb46a8d835ac1ce84`.

The executing runtime validator accepted the uniquely framed runtime JSONL with architecture `riscv64` and flush path `linux-riscv-flush-icache`. The saved `runtime.jsonl` exactly matches that frame. The hash prefix has 33 records: one configuration, 31 semantic checks and one cache-init begin. Every semantic name, requirement, status, actual value and expected value matches the executing validator's independent exact oracle. Its configuration matches the pinned key, two upstream vectors, revision, light-cache scope and software-AES request. The strict full hash validator rejected this prefix with `Missing initial config or final summary`; no summary was synthesized.

Execution is bound to commit `9d108c4041e0fa440a676f8a3ee1a2db1d736192` and the eight [executing-source](executing-source/) snapshots in `preflight.json`. Snapshot/live source checks passed during runtime review and again at the post-stop raw replay. The timestamped [post-inputs.json](post-inputs.json) audit records all eight source bindings unchanged at 2026-10-08T23:55:54Z, along with matching simulator, guest ELF and resource digests. The reviewer independently decoded both exact ELF payloads from saved `raw/guest.sh` and matched their bytes and digests. This audit is separate from a runner report. Later runner changes are not treated as code executed by this attempt.

The retained simulation checkpoint records kernel-booted hypercall 1 at tick `379381390000` and after-boot-started hypercall 2 at tick `674367239000`. Its `execution_stage=running` and `last_tick` describe that saved checkpoint, not the final stopped host process state.

## Why the attempt stopped

[BUDGET-REVIEW.md](BUDGET-REVIEW.md) proves from the exact ELF, cache driver and actual CPU configuration that the two mandatory Argon round loops alone span at least `10519287679000` ticks. This exceeds the configured per-call `10000000000000` allowance before adding any other work. `state_review` and `runner_review` independently confirmed the proof; root also replayed it. This finding supersedes the initial recommendation to retain the default guard, which was based on the previous attempt's wall timeout and absence of an observed tick-limit failure.

Root requested one control-C through the tracked execution session at 2026-10-08T23:54:06Z to stop the now-proven insufficient attempt. The tool reported session exit 1 and only `^C`. [cancellation.json](cancellation.json) and [host-disposition.json](host-disposition.json) preserve the observed outcome and limits. No final runner `report.json` was generated; actual runner signal receipt, child return code and runner-performed reaping are unavailable. Production subprocess tests establish the handler's behavior separately and do not convert this actual tool-level termination into a verified handler receipt.

Root observed no matching wrapper or gem5 processes after the stop. The reviewer independently found no process with this exact output directory argument at 2026-10-08T23:58:20Z. No wall timeout, tick-guard exit or hash mismatch was observed. The static proof is not an observed MAX_TICK result.

## Remaining acceptance

The proposed next unchanged light run must explicitly declare a larger finite tick allowance, retain no default wall timeout, and still produce all 39 required light controls, all nine runtime controls, complete guest frames, hypercalls `[1, 2, 3]` and simulator exit 0. The proposed `100000000000000` allowance is not a completion guarantee. This evidence does not establish full-dataset operation, selected-core timing, calibrated performance, measured power or RTL readiness.
