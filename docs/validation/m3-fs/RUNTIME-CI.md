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
