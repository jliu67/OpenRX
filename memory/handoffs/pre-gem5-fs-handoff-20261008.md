# Handoff — repaired power import and Linux runtime gate

2026-10-08 UTC / Edmonton. Base `bac3a0698d9ed3c308662c14c303cec9d56021c7`.
User requested continued OpenRX. [PR #17](https://github.com/jliu67/OpenRandomX/pull/17)
contains independent importer repair/review and explicit Linux runtime
controls; gem5 full-system #16 is a separate continuing package.

## Reviewed outcomes

Original P1-06S crashed without promised reports on malformed versions and
two Decimal classes. Narrow fixes preserve formulas and valid reports.
Two reviews under docs/validation/p1-06 s retain64 importer tests,
327 type/13 Decimal failures, 10 valid comparisons, 9,024 mathematical checks.
Software acceptance does not establish actual meter calibration or M1.

Independent runtime reviewer fixed sigsetjmp context before publication.
Nine controls pass native/QEMU RV64 GC: SIGILL, W^X, generated code and explicit
flush return.Implementation `288cebbc284f304e216cfcc907a544e2706198f3`
passed foundation37803105632 and RISC-V37803105634:219 Python/107 upstream/6 native,
original 39 exact checks plus9 runtime each.
Artifact11561518954 ZIP SHA256
`a4cd49b7f6f54a94fed9d6b3087714eaa00063ad5f732c201b54464b0cc94d05`
matched. Root independently replayed four streams. See
docs/validation/m3-fs/RUNTIME-CI.md and RUNTIME-REVIEW.md.

No vendor/native benchmark/RTL changes. Local snapshot lacks four vendored
binary audit PDFs because text connector cannot fetch them; fetched text
bytes match and actual CI verified171 files. Local runtime is standalone;
RandomX native/cross builds occurred in complete CI checkout.

## Continue

Inspect live main/PR/issue state and receipts. #13 claim
`codex/20261008-p106-review` must release into review/done and close after
final integration/checks. #16 claim `codex/20261008-fs` covers pinned build/
configuration/guest preparation/boot attempt.Session helpers are bounded,
not permanent roles.

For #16 execute explicit runtime gate before unchanged RandomX light controls.
Retain pinned image/toolchain/source/config/binary provenance and bounded
errors.Generic atomic NoCache boot is not RTL or calibrated timing proof.
Full dataset follows light correctness;selected-core acceptance remains.
M3/M4/M5 gates stay open.Controlled host/meter/counters #8/#10/#11,
hardware #2 and activation #4 remain unresolved.

Previous state/handoff preserved under
memory/handoffs/pre-linux-runtime-*-20261008.md;session history prefix intact.
Next #16 work package must supersede this intermediate checkpoint with actual
outcomes, not planned results.
