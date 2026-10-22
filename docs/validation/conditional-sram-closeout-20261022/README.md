# Conditional SRAM delivery closeout — 2026-10-22

This separate delivery record preserves the original indexed
[conditional baseline evidence](../conditional-sram-baseline-20261022/README.md)
and its 91 files unchanged. No source, model, report/provenance digest, raw
scientific flag or acceptance criterion changes here. Earlier draft and pending
statements remain dated publication snapshots, superseded only for current
delivery by the verified records below.

## PR92 merge and review

[PR92](https://github.com/jliu67/OpenRX/pull/92) merged normally at
2026-10-22 14:30:25 UTC:

- Merge commit: `0cb7c7fcc26b9b6d0d0b46453cba6acbbd3bc69e`.
- Ordered parents: `6888f8293a4a4703f714f755cb0c45f15fd1f6f3` and
  `73c5d08ecd3b3a9dca9935c6f6a35cff848356e9`.
- Merge tree: `9f9a1d68539a74c4529cf9697aded6754a11631a`, equal to the
  accepted publication head tree.
- [Independent final-head review](https://github.com/jliu67/OpenRX/pull/92#pullrequestreview-5615633520)
  passed; all four applicable checks at that exact head passed.

## Exact-merge checks

Both expected exact-merge push checks passed, confirmed at 14:47 UTC across
workflow-run, job and check records. The earlier metadata lag resolved without
reruns or dispatches. [Machine-readable merge/check bindings](merge-checks.json)
retain exact source and receipt identities. Foundation's full-dataset reference
and same-process native controls remain explicitly skipped, not passed.

| Exact-merge push check | Verified result | Job |
| --- | --- | --- |
| Foundation | PASS | [39796233107 / 119884020642](https://github.com/jliu67/OpenRX/actions/runs/39796233107/job/119884020642) |
| RISC-V | PASS | [39796233131 / 119884021166](https://github.com/jliu67/OpenRX/actions/runs/39796233131/job/119884021166) |

Independent review and applicable checks for any documentation closeout
publication remain separate from these PR92 merge checks.

## Scientific boundary retained

[EXP-027](../../../experiments/EXP-027-conditional-sram-baseline.md) remains an
accepted conditional comparison of one versus four banks at fixed 128 KiB under
hypothetical CACTI6.5 ITRS45nm HP / 1.0 V / 360 K assumptions. The actual original
five-command run, 16 tests, fresh build, two cases and strict report are retained
without repetition. Report SHA256 stays
`67deb5c947d346f84c48db5e30b7000a76a8fdd9c8b0fe67bfa81621d81c9bde`;
separate result acceptance remains `PASS_CONDITIONAL_MODEL_COMPARISON_ONLY`.
Raw `unverified` and pending-review flags are preserved as recorded.

This delivery does not provide characterized SRAM/process/PVT, physical PPA or
frequency, controller/PHY sustainable random service, complete wall power,
achieved hashes/s or architecture selection. Broader issue #72 and these
scientific gates remain open. No CACTI/full-hash rerun or new local validation
workload is performed for this documentation record; applicable hosted checks
remain separate.
