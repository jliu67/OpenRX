# RandomX execution components

Current accepted main includes all 29 native instruction families/256 encodings,
[division/square root](execute/DIVSQRT.md) and accepted
[complete program sequencing](execute/PROGRAM_SEQUENCE.md). The separate draft
[register hashing](hash/README.md) and new [scratchpad finalization](hash/FINALIZATION.md)
stages retain their own validation/review boundaries. Full actual dataset, initial
fill/program AES generation, complete hardware hash and physical PPA remain open.

The component-subset summaries below retain their original publication context;
they do not describe the current complete execution opcode coverage.


Accepted hardware includes the [v2 AES mixer](aes/README.md),
[ordered iteration stores](iteration/README.md) and [iteration memory engine](engine/README.md).
The new [native integer executor](execute/README.md) connects actual bounded bytecode
arithmetic; task54's independent new-work review remains pending. Complete core/FP,
branch/multiply, physical-memory, full-hash and calibrated-PPA gates remain open.

Earlier planning entry (retained verbatim):

```text
# Future RTL work

No processor RTL implemented. Advance after M3/M4 gates; isolate core, cache and SoC changes and document verification interfaces.
```

The [task #56 extension](execute/MULTIPLY-BRANCH.md) supplies multiplication,
reciprocal and conditional branches on reviewed/unmerged PR #55. FP/CFROUND and
complete VM/hash/physical acceptance remain open; new-work review is pending.


[Task #58 FP subset/CFROUND](execute/FLOATING.md) reuses licensed binary64 arithmetic;
division/sqrt remain errors and full-hash/physical-PPA gates remain open.
