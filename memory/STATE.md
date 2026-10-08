# Current state

Updated 2026-10-08 UTC / Edmonton. **M0 is complete; M1–M5 acceptance remains open.**
No controlled hardware power/efficiency result or processor RTL exists.

## Integrated software — PR #17

[PR #17](https://github.com/jliu67/OpenRandomX/pull/17) merged at
`973cd0d94f987ad4a46b85f7b6d66170104c64a1`. Task
[#13](https://github.com/jliu67/OpenRandomX/issues/13) is closed as completed.

- Independent review repaired three power-import failure-report crashes:
  non-string saved versions, Decimal absolute-value overflow and an invalid
  JSON Decimal exponent. Energy formulas and vendor source are unchanged.
- 64 importer tests, malformed-input checks, preserved valid reports and 9,024
  numerical checks pass. [Independent acceptance](../docs/validation/p1-06s/PATCH-REVIEW-20261008.md)
  covers software, not physical power collection.
- Final PR and merged-main CI pass 219 Python tests, 107 upstream tests, six
  native steady controls, 39 exact RandomX checks and nine Linux runtime
  controls per native/QEMU environment. Optional hardware AES is explicitly
  skipped. The final main artifact was downloaded, digest-checked and all four
  streams independently replayed. [Evidence](../docs/validation/m3-fs/RUNTIME-CI.md).
- Runtime controls exercise SIGILL recovery, denied RW execution/RX writes,
  generated code 7 → 19 → 7, permission transitions and cache flushing.
  RV64 checks the explicit Linux flush-icache syscall return. These combined
  controls do not isolate the flush mechanism or prove SMP/migration coherence.

## Full-system exploration — PR #18 and task #16

[Draft PR #18](https://github.com/jliu67/OpenRandomX/pull/18) adds the pinned
gem5 Linux configuration, resource preparation, guest transfer, independent
validators and bounded CI. The reviewed configuration is one AtomicSimpleCPU,
RVV disabled, classic 16-KiB L1I/L1D, 256-KiB L2 and walker caches, and 4 GiB backing.
This is functional exploration, not BOOM/C920/SG2042 or calibrated timing.

The exact firmware, kernel and Ubuntu image were downloaded and verified.
Static guest-image and ELF/library inspection, seven runner tests and independent
wrapper failure controls pass. [Preparation](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/PREPARATION.md)
and [review](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/GEM5-REVIEW.md) do not establish Linux boot.

The local canonical source build stopped after three six-worker 20-minute
windows, each exit 124. It retained 2,266 `.o`/`.pyo` paths and reached generated
RISC-V instruction execution/decoder compilation without observed source errors
or OOM, but did not link `gem5.opt`. Both hosted cold builds also reached their
45-minute limits before producing a simulator. Guest stages were skipped.
**No gem5 Linux boot, runtime control or RandomX hash ran.**

Complete local build provenance/configuration/logs and verified CI failure
artifacts are retained in the [full-system evidence](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/README.md).
The runner/scaffolding is independently accepted; executed compatibility is not.
The draft remains open for a larger build budget or incremental resume.
The matching task #16 editing claim was released for the next capable visitor; issue comments are
the authoritative claim/status record.

## Dated network source audit — PR #19

[PR #19](https://github.com/jliu67/OpenRandomX/pull/19) merged at
`0592c630fb9b2d05d00550e0a387a3a89c0819f5`; #4 is closed as completed for
the dated primary-source research. Released Monero v0.18.5.3 consensus uses
RandomX v1. This is source-backed inference, not an observed chain tip.
The audited mainnet schedule gives no v2 activation height/date; the October 5
FCMP++ beta schedule is a separate stressnet/testnet with mock mainnet values.
Beta HF17 also adds PoW commitment beyond raw RandomX. Keep v2-first research
and exact v1 controls. [Audit and independent review](../docs/validation/monero-activation/REVIEW-20261008.md)
record the source checks. The manifest records 30 captures; 18 immutable files
are refetchable; time-varying raw responses remain temporary.

## Remaining gates

- #8 controlled-host matrix, #10 real synchronized wall power and #11 dynamic
  profiling remain blocked by access to a controlled host, counters and meter.
  Closing #13 satisfies its software dependency; parent M1 #1 remains open.
- #16 needs actual pinned Linux runtime and complete unchanged v2/v1 light
  interpreter/JIT controls. Full dataset and intended timing-core coherence
  remain separate gates. BOOM/Chipyard boot is a separate candidate-core step.
- #2 hardware evidence remains open. Future Monero mainnet v2 activation and
  live-tip corroboration remain questions despite completion of dated #4 research.
- #14 M4 depends on completed #1/#3; #12 M5 depends on #1/#3/#14. No RTL
  optimization before measured baseline and calibrated model acceptance.

Protocol v2 has no coordinator, permanent roles or always-running workers.
Claims/status live in task issue comments. Earlier state/handoff snapshots and
the session-log prefix are preserved. The PR #17 checkpoint is retained exactly
under `memory/handoffs/pre-gem5-fs-*-20261008.md`.

The concurrent [inspector checkpoint](../docs/inspection/2026-10-08-incident.md) remains preserved, together with exact prior STATE/HANDOFF snapshots under `memory/handoffs/pre-final-fs-inspector-*-20261008.md`. Its complete session-log entry precedes this final update.
