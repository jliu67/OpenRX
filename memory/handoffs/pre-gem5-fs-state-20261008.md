# Current state

Updated 2026-10-08 UTC / Edmonton, sessions `codex/20261008-fs` and
`codex/20261008-p106-review`. **M0 complete; M1–M5 acceptance remains open.**
No controlled hardware power/efficiency result or processor RTL exists.

## Latest reviewed work — PR #17

[PR #17](https://github.com/jliu67/OpenRandomX/pull/17), implementation
`288cebbc284f304e216cfcc907a544e2706198f3`, repairs P1-06S malformed-input
failure reporting and adds explicit Linux runtime controls. Independent
review accepts the repaired **software**, not physical power collection.

- P1-06S fixes three demonstrated crashes: non-string saved versions,
  context-sensitive Decimal absolute-value overflow, invalid JSON Decimal
  exponent. Formulas and vendor/native harness remain unchanged.
- 64 importer tests, 327 malformed-type cases, 13 Decimal cases, 10 unchanged
  valid-report comparisons and 9,024 numerical checks pass. Two separate
  reviews retain original failures and repaired acceptance. [Review](../docs/validation/p1-06s/PATCH-REVIEW-20261008.md).
- Actual [foundation CI 37803105632](https://github.com/jliu67/OpenRandomX/actions/runs/37803105632)
  and [RISC-V CI 37803105634](https://github.com/jliu67/OpenRandomX/actions/runs/37803105634)
  passed: 219 Python, 107 upstream, six native; original 39 exact native/QEMU
  RandomX checks plus nine runtime controls each. Optional hardware-AES skip
  remains explicit. [Evidence](../docs/validation/m3-fs/RUNTIME-CI.md).
- Runtime covers SIGILL recovery, denied RW execution/RX writes, generated
  code 7 → 19 → 7 with permission transitions and cache flush; RV64 explicitly
  checks Linux flush-icache syscall. Root downloaded/digest-checked artifact
  and independently replayed all four streams.
- QEMU is emulator evidence. Combined transition/flush tests do not isolate
  cache-flush semantics or establish SMP/migration/real core coherence.

## Full-system exploration — #16

Current accepted claim is `codex/20261008-fs` on #16, not parent #3. Pinned gem5
build and guest preparation are being executed separately from PR #17.
Preparation/build alone is not boot. Actual outcomes and failures belong in
the next scoped work package. Never infer success or active workers from this
summary.

Candidate direction remains Chipyard 1.14.0/MediumBoomV3Config for RTL research
and gem5 v25.1.0.1 full-system Linux for exploration. Generic atomic/O3 is not
BOOM/C920/SG2042. Selected-core boot, full dataset, calibrated timing and measured
wall power remain unvalidated.

## Remaining gates

- #13 software can close after reviewed PR #17 integration/final checks.
- #8 controlled-host matrix, #10 wall power, #11 profiling remain externally
  blocked. Software acceptance does not supply calibrated host/meter.M1 #1 open.
- #2 X5 implementation evidence and #4 Monero activation remain open.
- #16 requires executed pinned guest/runtime/hash evidence and review;
  BOOM/Chipyard boot/full workload remains separate core acceptance.
- #14 M4 depends completed #1/#3;#12 M5 depends #1/#3/#14.

Protocol v2 has no coordinator, permanent roles or always-running workers.
Claims/status live in task issue comments. Prior
[state](handoffs/pre-linux-runtime-state-20261008.md) and
[handoff](handoffs/pre-linux-runtime-handoff-20261008.md) preserve M3 history
byte-for-byte; earlier snapshots/session prefix are retained.
