# Linux runtime control execution — 2026-10-08

Implementation `288cebbc284f304e216cfcc907a544e2706198f3`, PR #17, was
executed by [RISC-V CI run 37803105634](https://github.com/jliu67/OpenRandomX/actions/runs/37803105634)
and [foundation CI run 37803105632](https://github.com/jliu67/OpenRandomX/actions/runs/37803105632).
Both completed successfully. The PR head implementation is distinct from the
actual merge checkout `82398b9545c1bfc1d80bb7f79c41f783048fb89c`,
retained in the environment and audit ledger. This is preparatory execution for #16, not a
gem5 full-system boot or completed M3 milestone.

The new runtime probe passed all **nine required controls** natively and
under QEMU scalar RV64GC. It recovered from an actual illegal instruction,
observed denied RW execution and RX writes, checked each explicit Linux
RISC-V cache-flush syscall return, and executed generated values 7 → 19 → 7.
The existing exact RandomX probe still passed **39 required controls per
environment**, with one explicitly unrequested hardware-AES skip each.

The root downloaded artifact 11561518954, checked its ZIP SHA-256 against
GitHub's digest, extracted only safe relative members, and independently
replayed all four native/QEMU runtime and RandomX streams through their
current validators. Reports returned success. The runtime RISC-V binary
SHA-256 was `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`;
the unchanged RandomX cross probe was
`61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`.
Compact raw runtime streams/reports and actual environment are committed
alongside `runtime-ci-audit.json`. Full configuration, binary, disassembly
and compiler database remain in the linked artifact, expiring 2027-01-06.

Locally, native runtime was independently rebuilt and tested by a separate
reviewer; its digest and output matched the root's retained capture. See
[RUNTIME-REVIEW.md](RUNTIME-REVIEW.md). Reviewer corrected a portability issue
in the original sigsetjmp context before CI publication.

Limits: memory permission transitions can themselves synchronize
instructions. These checks establish the combined transition/flush
workflow, not isolation of flush semantics. QEMU automatically detects
self-modifying code; its results do not certify real cache coherence.
Single-thread execution does not establish hart migration or SMP shootdowns.
Repeat on pinned gem5 full-system Linux and the selected RTL/core before
acceptance. No timing calibration, hardware power, full-dataset RISC-V
execution or architecture advantage is established.

## Final PR and main integration audit

Independent reviewer `/root/runtime_review` inspected the final job logs and
fetched committed files at merge
`973cd0d94f987ad4a46b85f7b6d66170104c64a1` on 2026-10-08. Both main
jobs finished successfully; this supersedes earlier in-progress status.

| Checkout | Foundation run / job | RISC-V run / job | Result |
|---|---|---|---|
| Final PR merge test `b4603869a5b99c6adfb54a0819e04a114f3e09d7`, head `87309b203865d16076e17818b516b6399caddc6a` | [37804856030](https://github.com/jliu67/OpenRandomX/actions/runs/37804856030) / `113406342652` | [37804856052](https://github.com/jliu67/OpenRandomX/actions/runs/37804856052) / `113406342129` | Both successful |
| Published main `973cd0d94f987ad4a46b85f7b6d66170104c64a1` | [37805551737](https://github.com/jliu67/OpenRandomX/actions/runs/37805551737) / `113408747066` | [37805551604](https://github.com/jliu67/OpenRandomX/actions/runs/37805551604) / `113408744357` | Both successful |

Each foundation job recorded **171 verified vendor files, 219 passing
Python tests, 107 passing upstream tests and six passing native steady
tests**, plus successful v1/v2 smoke/full-dataset reference steps. The native
steady suite also recorded matching three-worker software-AES differential
controls for both versions. These are hosted functional controls, not a
controlled M1 hardware measurement.

Each RISC-V job recorded **39 required RandomX checks and nine runtime
checks per native/QEMU environment**; the RandomX matrix contains eight
software-AES hash cases and one explicit optional hardware-AES skip. Reports
showed zero exit status. QEMU was 8.2.2, package
`1:8.2.2+ds-0ubuntu1.18`; cross GCC was 14.2.0, and execution used
`rv64,v=false` with the declared RISC-V sysroot.

The reviewer downloaded the final main artifact `11563570169`, verified its
ZIP SHA-256
`0af776da4540bc9be627d0f768b59a4c675bbdf93830527633fd9b05e560e21a`
against GitHub, safely extracted it and independently replayed **all four
complete native/QEMU RandomX/runtime streams**. All passed current validators
with empty stderr. Both included cross binaries are ELF64 little-endian
RISC-V (machine 243); their digests match the runtime/RandomX digests above.
The final runtime stream digests also match the retained compact captures.
The artifact expires `2027-01-06T16:01:46Z`.

The following remote files at the published merge match the reviewed local
bytes exactly. Runtime hashes match [the independent review](RUNTIME-REVIEW.md);
importer hashes match the retained
[patch review](../p1-06s/patch-review-20261008.json).

| File | SHA-256 |
|---|---|
| `simulator/runtime-probe/main.c` | `c05ca5f23a81e8a60f528bdd4052fe63746eb1e1550a11872ed7885a4f5e4fc4` |
| `tests/native_runtime_probe.py` | `99f178b3f8ad84cf0b7542b108338a498a3d23d33a5738839eff96916c284617` |
| `tests/test_runtime_probe.py` | `3bd3a8fc252a6db46ace2da9c84e03c7c6b81ec5c9c694c532a95923c3e16aa0` |
| `scripts/power_import.py` | `612d20c6e4b3cae80be1231d0c41c5ece29ece23a286f347482adf23f35cfbf7` |
| `tests/test_power_import.py` | `91ea2a5806a9235823caacc6cb97f69c456e504999bbf6e0feab8c505ead81d8` |

Local full fetched logs, remote snapshots, archive and replay ledger are in
`build/runtime-final-ci/`. This audit adds final integration evidence; the
gem5, full-dataset RISC-V, timing and power limitations above still apply.
