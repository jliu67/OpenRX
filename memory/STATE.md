# Current state

Updated 2026-10-08 UTC / Edmonton. **M0 is complete; M1–M5 acceptance remains open.**
The pinned gem5 Linux runtime now passes its nine controls. There is still no controlled hardware power/efficiency result or processor RTL.

## Actual gem5 Linux runtime — PR #18 / task #16

[PR #18](https://github.com/jliu67/OpenRandomX/pull/18) contains the independently accepted configuration, runner, simulator acquisition workflow and actual runtime evidence. The declared model is one AtomicSimpleCPU, RVV disabled, 16-KiB L1I/L1D, 256-KiB L2, walker caches and 4 GiB RAM. It is functional exploration, not a BOOM/C920/SG2042 or calibrated timing model.

The original local and hosted builds timed out. One incremental resume completed the remaining large compilation units but hit an 8-GiB host linker OOM. A bounded recovery using upstream `--limit-ld-memory-usage` then linked successfully in 248.76 seconds, without recompiling target C++ or changing source/configuration. All 10,933 archived source files match. [Build and recovery evidence](../docs/validation/m3-fs/link-recovery-20261008/README.md) preserves both failure and success.

The original executable is 957,300,488 bytes, SHA-256 `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`. Real build-info identifies gem5 25.1.0.1. A verified package containing the original binary, immutable source/notices, build evidence and minimal Python runtime is saved in two parts. [Reuse it](../docs/validation/m3-fs/REUSE.md); another source build is unnecessary.

**Actual Linux 6.8.12 boot and all nine RV64 runtime controls passed.** SIGILL recovery, RW/RX page permissions, explicit Linux flush-icache returns and generated-code execution 7 → 19 → 7 matched their exact oracles. The child exited zero with empty framed stderr, a completion marker and ordered hypercalls 1/2/3. A different agent independently replayed the raw serial/report and rehashed the simulator, firmware, kernel, disk and payload bindings. [Executed evidence](../docs/validation/m3-fs/actual-runtime-20261008/README.md) and [acceptance](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md).

The separate unchanged light-mode attempt reached its 1,200-second child limit. It repeated all nine runtime controls and verified/launched the hash ELF, but supplied no complete hash stream or hypercall 3. Independent replay confirms timeout and exact input bindings; it does not establish a hash mismatch. [Light outcome](../docs/validation/m3-fs/ACTUAL-LIGHT-REVIEW-20261008.md). **No complete gem5 RandomX matrix or full dataset is accepted yet.** Task #16 stays open. The nine runtime controls establish combined behavior in this single-core configuration; they do not isolate cache-flush causality or establish SMP/migration or intended timing-core coherence.

Final PR CI at `4f4cf17880ccfa2e904eb9d2dc23892b828bce12` passed 245 Python tests, 107 upstream tests, six native steady controls, 39 exact RandomX checks plus nine runtime checks per native/QEMU environment, and 26 gem5 offline controls. Optional hardware AES has one explicit skip per RandomX probe. [CI ledger](../docs/validation/m3-fs/streaming-ci-20261008/ci-review.json) distinguishes that CI from the actual local gem5 guest. Hosted manual builder/cache/artifact reuse remains unexecuted; its reviewed workflow no longer recompiles gem5 on ordinary PRs. A later separately reviewed runner fix streams flushed records before probe exit and preserves exact child/capture failure behavior; 245 total / 26 gem5 host tests pass. The actual guest evidence remains bound to the original runner snapshot.

## Integrated software and dated research

[PR #17](https://github.com/jliu67/OpenRandomX/pull/17) merged at `973cd0d94f987ad4a46b85f7b6d66170104c64a1`; #13 is completed. Separate review repaired three malformed-input failure-report crashes without changing energy formulas. The importer passed 64 tests, valid-report preservation and 9,024 numerical checks. [Software acceptance](../docs/validation/p1-06s/PATCH-REVIEW-20261008.md) does not certify physical power collection. Earlier native/QEMU artifacts and independent replay remain in [RUNTIME-CI.md](../docs/validation/m3-fs/RUNTIME-CI.md).

[PR #19](https://github.com/jliu67/OpenRandomX/pull/19) merged at `0592c630fb9b2d05d00550e0a387a3a89c0819f5`; #4 is completed for dated source research. Released Monero consensus uses RandomX v1 by source-backed inference, not an independently observed tip. No actual mainnet v2 date appears in the audited schedule; the October 5 beta schedule is a separate stressnet with mock mainnet values. Keep v2-first research and exact v1 controls. [Audit](../docs/validation/monero-activation/REVIEW-20261008.md) retains 30 capture identities and 18 refetchable immutable files; time-varying raw responses remain temporary.

## Coordination review

Hub #5 and dependency summaries were corrected: #13 and #4 are completed; #10 now waits on #8 plus real host/meter access. Incident #20 was separately reviewed and closed as completed.

[PR #23](https://github.com/jliu67/OpenRandomX/pull/23), merged at `b562a941bec39c3a0747a2129903dd33bb471f62`, queues eligible announcements rather than allowing a single pending request to be replaced. Eight announcement tests and actual bot publication passed; #22 is completed. This was a source-identified loss risk, not proof an observed message had been lost. [Deployment evidence](../docs/validation/coordination/DEPLOYMENT-20261008.json).

The concurrent #24 policy and its session history are preserved. A separate agent accepted its compact major-handoff announcements; the original author corrected the duplicate decision ID at `a2128b9ee9dd93acdfc392bc4752e412f5e5a3d2`. #24 is completed. [Policy review](../docs/validation/coordination/POLICY-REVIEW-20261008.md). Announcements remain procedural; the router neither verifies engineering results nor launches AI workers.

## Remaining gates and next work

- #16: complete unchanged light v2/v1 interpreter/JIT controls using the retained binary; preserve partial/timeout results. Then address full dataset and every intended core/runtime separately.
- #8/#10/#11: controlled host matrix, synchronized wall power and dynamic profiling require actual host/counter/meter access. #13's software dependency is satisfied; parent M1 #1 stays open.
- #2: hardware identity/evidence remains open. Future Monero mainnet v2 activation and direct live-tip corroboration remain questions.
- #14 M4 requires completed #1/#3; #12 M5 requires #1/#3/#14. No RTL optimization before measured baseline and calibrated model acceptance.

Read live task comments and bot receipts for claims. Exact prior STATE/HANDOFF snapshots are archived under `memory/handoffs/pre-fs-reuse-*-20261008.md`; earlier snapshots and the full session-log prefix, including the concurrent inspector/policy entries, remain preserved.
