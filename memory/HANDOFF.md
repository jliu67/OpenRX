# Handoff — integrated runtime controls and full-system exploration

2026-10-08 UTC / Edmonton. User requested continued OpenRX work. PR #17 is
merged at `973cd0d94f987ad4a46b85f7b6d66170104c64a1`; #13 is closed as completed.
[Draft PR #18](https://github.com/jliu67/OpenRandomX/pull/18) targets main and
contains the separately reviewed gem5 configuration/runner for task #16.

## Accepted results

Three power-import failure-report defects are repaired without changing energy
formulas. The two reviews under `docs/validation/p1-06s/` retain 64 importer
tests, malformed inputs, valid-report comparisons and 9,024 numerical controls.

The standalone Linux runtime probe passes nine native/QEMU controls including
SIGILL recovery, RW/RX page permissions, generated code overwrite/re-execution and explicit RV64
cache-flush syscall return. Final PR/main CI also passes 219 Python, 107
upstream and six native tests, plus the existing 39 exact RandomX checks per
native/QEMU environment. Optional hardware AES is explicitly skipped.
The final main artifact `11563570169` matched ZIP SHA-256
`0af776da4540bc9be627d0f768b59a4c675bbdf93830527633fd9b05e560e21a`;
all four streams were independently replayed. See
[final CI audit](../docs/validation/m3-fs/RUNTIME-CI.md).

## Full-system outcome

Pinned gem5 is v25.1.0.1,
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9`.
The exact OpenSBI/kernel/Ubuntu resources were downloaded and verified, and
both cross-built probes passed a static guest-library compatibility audit.
[Preparation](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/PREPARATION.md) records commands and
digests; [independent review](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/GEM5-REVIEW.md) accepts
scaffolding after cache and input-integrity fixes.

The selected recipe uses one AtomicSimpleCPU, RVV off, the upstream example's
classic private L1/L2/walk-cache hierarchy and 4 GiB RAM. Hypercall 3 alone
cannot pass: the wrapper needs the complete event sequence and exact validated
guest streams, statuses, stderr, completion marker and stable input identities.

The local source build stopped at its final bound on 2026-10-08T16:50:20Z.
Three six-worker 20-minute windows exited 124; 2,266 `.o`/`.pyo` paths were
retained, ending in generated RISC-V instruction execution/decoder compilation.
No compiler source error or OOM was observed, but no simulator binary linked.
Both 45-minute hosted builds also timed out. All guest stages were skipped.
See [actual results](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/README.md),
[local build provenance](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/build-20261008/build-provenance.json)
and [verified CI failures](https://github.com/jliu67/OpenRandomX/blob/f44cd47ca2061c39fa45d031a307f6df4b4f535d/docs/validation/m3-fs/CI-BUILD.md).
There is no gem5 Linux boot/runtime/hash result.

The independent scaffold review passes; the draft PR is retained for execution.
Final documentation commits intentionally avoid repeating the already failed
cold builds. No runtime/configuration implementation changed after its review;
the heavy workflow's duplicate push trigger was removed and separately reviewed.

## Dated network source result

[PR #19](https://github.com/jliu67/OpenRandomX/pull/19) merged at
`0592c630fb9b2d05d00550e0a387a3a89c0819f5`; #4 is closed for dated
primary-source research. The released mainnet consensus targets RandomX v1,
inferred from pinned stable/master source rather than a separately synced tip.
No v2 mainnet date appears in the audited schedule. October 5 refers to the
separate beta stressnet; its mainnet heights are explicitly mock test values.
Beta HF17 adds PoW commitment beyond raw RandomX. Keep the v2-first project
direction and exact v1 controls. [Source audit](../docs/validation/monero-activation/REVIEW-20261008.md)
and peer review record reproducible source/metadata checks. The manifest records
30 captures; 18 immutable files are refetchable; time-varying raw responses
remain temporary.

## Resume and acceptance

Read live main, PR #18, task #16 and bot receipts before selecting work. The
session claim `codex/20261008-fs` was released in comment 6064988893; inspect its
actual receipt and obtain a fresh claim before editing. There are no permanent
roles or implied running agents.

After a successful exact build, run the explicit runtime gate first using
`simulator/gem5/run.py`; commands and dependency environment are documented
in preparation/build evidence. Retain serial/stdout/stderr, report, phase
snapshots, DTB/configuration, source/toolchain provenance and binary digests.
Then attempt the unchanged light-mode probe with `--hash-binary`, preserving
runtime partial results if later hashes exceed the declared bound. Do not
shrink RandomX constants or accept a partial hash matrix.

M3 selected-core/full-dataset and M1/M4/M5 gates stay open. Generic atomic/O3
does not model BOOM, C920 or SG2042, and host elapsed time is not simulated
throughput or physical efficiency. Controlled host/meter/counters #8/#10/#11,
hardware #2, future v2 activation and direct live-tip corroboration remain unresolved.

Local text snapshot lacks four vendored audit PDFs because the connector cannot
fetch binary source files; real CI verified all 171 vendor files. Full native
and cross RandomX builds ran in complete CI checkouts. Vendor and RTL are
unchanged. Earlier state/handoff snapshots and session history are retained.

The concurrent [inspection report](../docs/inspection/2026-10-08-incident.md) remains on main. Its complete session history and exact STATE/HANDOFF snapshots are preserved; this handoff reconciles its bounded-build findings with final local evidence.
