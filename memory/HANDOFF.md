# Latest handoff — M3 scalar RISC-V preflight and candidate research

Session `codex/20261008-m3`, 2026-10-08 UTC / Edmonton. User requested continuing OpenRX after the progress report. Base `d9e41cd07766e9c990641605dff1145d2f035d7d`; [PR #15](https://github.com/jliu67/OpenRandomX/pull/15), isolated branch `openrx/m3-riscv-preflight`. **M3 work package implemented/tested; M3 acceptance remains open.**

## Delivered

Final implementation `f9c3ee7debc94807a4a82b537079bdf455aea551` passed RISC-V run37791921197/job113361273431 and foundation run37791921307/job113361273371. Actual logs show **199 Python, 107 upstream and six native tests**, plus **39 required native and 39 required emulated-RISC-V checks**. Separate code/source/evidence review is complete. PR #15 merged on main at `83cbb3ec279a9fab9c5bb18b567fbbd7591f1aed`; milestone #3 remains open.

Final artifact11557345367 (455549bytes) SHA256 matched `ca14f2e811cf6570d989928c0eafcbd046851b05830e08e624c569721ffafb99`. Native/QEMU streams, empty stderr, stable RISC-V binary digest and now-present compile_commands were revalidated. PR checkout SHA was `dc6de662bedc6136c4b1ae045ff7fc9b45f7fb92`, distinct from implementation/head SHA. [Final audit](../docs/validation/m3/final-ci-audit.json) retains both identities and expiry2027-01-06T14:22:28Z. Final evidence publication is docs-only; no further implementation or test changes.

- Pinned-source core and simulator reports with exact revisions, licenses and confidence limits; provisional MediumBoomV3Config RTL candidate, gem5 exploration candidate, QEMU functional preflight.
- Unchanged-RandomX light-mode C++ probe: seven integer, 24 FP and eight v2/v1 interpreter/JIT exact hash checks.
- Independent complete-stream validator, retained failures/digests/commands, 17 malformed/tampered-evidence regressions.
- GCC14 RV64GC/lp64d cross toolchain and QEMU CI with vector execution disabled. Dormant vector/crypto upstream objects still require capable compilation tools.
- [EXP-002](../experiments/EXP-002-riscv-functional-preflight.md), [validation](../docs/validation/m3/README.md) and [independent review](../docs/validation/m3/REVIEW.md).

## Executed and audited

Initial implementation `e5eafde50d074f19afb37d08ccec4c59dd88a33d`: RISC-V [run 37790683112](https://github.com/jliu67/OpenRandomX/actions/runs/37790683112), job 113356939599 passed native and QEMU **39 required checks each**, one optional hardware-AES skip each. Existing native run 37790683131 passed source/build/profile/reference/upstream/steady checks. Local final suite passed **199 Python tests**. Updated validator was replayed against downloaded native and RISC-V raw streams; subsequent CI receipts are on #3/PR #15.

Artifact 11555544301 ZIP SHA-256 `5f042957866115a6eeb488953ec8d52c892896fd359353efac9da9d9334fadcb` matched GitHub. RISC-V binary SHA-256 `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657` matched report and machine-243 ELF identity. Initial archive expires 2027-01-06T14:13:21Z. Raw compact evidence is committed; CI artifact includes binary/config/disassembly. Later workflow now also exports compile_commands.json after independent review identified the omission.

Local runtime had GCC13 but no CMake/cross compiler/QEMU. The native library/probe were manually compiled from all exact vendored text sources; all 39 passed. Four vendored binary audit PDFs could not be fetched by the UTF-8-only connector, so local full-manifest verification failed solely on their absence. Native source files were exact; full 171-file integrity passed in actual CI checkout. No vendor file is changed by the PR.

Independent agents performed source research, probe implementation and separate code/source/evidence review this session. This is a bounded invoked session, not new permanent roles or an always-on workforce. Reviewer found and verified fixes for stage-record validation, independent semantic identities/oracles, flags/configuration binding, malformed outcomes and compile-command capture.

## Continue

Start with AGENTS, protocol, current STATE, #3 and PR #15. Inspect actual current HEAD, CI and claim receipts. The final `/openrx review codex/20261008-m3` on #3 releases the matching claim. No claim was placed on milestone #1 or #16.

New [#16](https://github.com/jliu67/OpenRandomX/issues/16) is independently ready for gem5 full-system Linux feasibility. Source audit shows SE cannot recover RandomX startup SIGILL probes, lacks syscall259 and ignores mprotect. QEMU automatically handles self-modifying code; its successful JIT hashes do not certify hardware fence.i coherence. Before M3 acceptance: exact selected runtime/boot, candidate core configuration, FP/JIT controls, upstream/full-dataset hashes and sufficient consistent guest memory. BOOM memory defaults are insufficient for unchanged full mode.

M1 controlled host/power/profile and P1-06S #13 acceptance remain outstanding; M4 #14 and M5 #12 gates remain intact. No timing/power estimate, silicon performance claim, RTL optimization, purchase, paid compute, account change or autonomous worker was produced.

Previous [P1-06S handoff](handoffs/pre-m3-20261008.md) and [state](handoffs/pre-m3-state-20261008.md) are archived byte-for-byte.

Archived relative links retain their historical locations; use the current STATE/HANDOFF entrypoints for working links.
