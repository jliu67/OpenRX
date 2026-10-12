# Open questions

## Current bounded questions — X9/v2 priority, 2026-10-12

[Source-only #41](https://github.com/jliu67/OpenRX/issues/41) owns a bounded evidence/
reuse decision, not a workload or broad survey:

- Which primary X9 machine claims can be traced, and which silicon/topology/v2 facts remain unknown?
- What exact v2 main-loop AES behavior versus scalar software AES, FP/rounding, JIT and memory interfaces must reusable IP support?
- What source/license gap prevents the provisional BOOMV3/open-IP baseline from supplying one required capability, and what evidence resolves the next decision?

Follow the [narrowed roadmap](../docs/ROADMAP.md#current-priority-path--2026-10-12).
Keep #16/#8/#10/#11/#3/#14/#12 gates intact. The X5-first questions below are retained,
deferred under #2's owner-priority block; their presence is not a ready-work instruction.

## Retained questions — unresolved history and later gates

- Which board/chip markings establish the X5 processor identity? Does it use a stock SG2042 or a customized derivative?
- What are the actual firmware/JIT, ISA extensions, frequency and per-chip power?
- Is any X9 independently available, and what is the original Bitmain specification source?
- When will Monero mainnet publish a RandomX v2 activation height/date? The [2026-10-08 source audit](../docs/validation/monero-activation/REVIEW-20261008.md) identifies RandomX v1 in the current released mainnet consensus and no dated v2 activation in the audited schedule. An independently synced tip should corroborate this source-backed inference; the beta stressnet fork is separate.
- How will a future mainnet PoW pipeline incorporate the beta HF17 commitment step? OpenRX's raw v1/v2 hash controls do not validate complete beta block PoW.
- The pinned scalar RV64GC JIT passed bounded QEMU v1/v2 light controls. Will the exact selected BOOM/Chipyard configuration boot Linux, support SIGILL/cache flushing and preserve full-dataset hashes?
- Pinned gem5 full-system Linux now passes nine standalone signal/protection/overwrite/flush controls on one Atomic core. Can it complete the unchanged v2/v1 light hash matrix, then full dataset and intended-core/SMP coherence? See #16 and [actual runtime review](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md); runtime success alone does not establish RandomX or timing-core correctness.
- Will MediumBoomV3Config remain preferable after exact emitted memory/cache configuration, per-component license review, full workload runtime and calibrated evidence? Selection is provisional, not a performance ranking.
- Is v2 limited by dataset latency, scratchpad capacity, AES throughput, or execution width for each configuration?
- What realistic synthesis library/process and calibration hardware can support power estimates?
