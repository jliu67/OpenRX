# Prepared native superscalar executor: bounded evidence

Source `6f65049c32e5e065a711d105cf2eb42204ed2285` (tree
`19ac91c6bbcab959cfeae9fc1305ff137d9fdf3a`) executes one externally prepared
native superscalar program with the unchanged accepted multiplier. The production
controller executes instructions in order. It implements all 14 native opcodes;
program/table preparation, the immutable instruction service, Argon2/cache setup,
cache-line reads and the eight-step dataset-item controller remain external.

[Design](../../../rtl/execute/SUPERSCALAR.md),
[EXP-019](../../../experiments/EXP-019-prepared-superscalar-execute.md) and
[actual source bindings](executed-source.json) describe the contract and claims.
The publication successor adds declared documentation/evidence/memory only;
actual runtime bytes must match the executed bindings. Independent exact-head
review and hosted checks are additional publication/merge gates.

## Original executions and complete coverage

| Package | Original outcome | Receipt artifacts selected / retained | ZIP bytes |
| --- | --- | ---: | ---: |
| [correctness01](correctness01/summary.json) | 130 native cases, 7,779 retirements, ten RTL modes pass | 1,234 / 4 | 3,261,043 |
| [synthesis01](synthesis01/summary.json) | Actual synthesis and seven mapped modes pass; no native/RTL repeat | 1,223 / 5 | 3,427,941 |

Both receipts verify against the immutable host journal. The first receipt is
`f7598ff088d64e4be511cc9c6e8d89a5e67a14c9b1c591856757e5aea058e060`;
the second is `27591eb90d4e8f06d90dca641d830a1f9c9fd35dd57c656a7b93e4db05c2231c`.
The second actual manifest explicitly consumes the first complete output,
receipt and root-verification inputs. All 1,178 fixture files match byte for byte;
no prior native generation or RTL simulation is repeated.

The [package index](package-index.json) SHA256 is
`e4386a5060250ed117ee7873b9d7dd7257e2d8999cdba6ce1153f5f9ec222c69`.
The two archive hashes are
`58883c0e12fa60e79de78018562988cf5edb6a3ff083944ed709e77b53cbe00c` and
`e180a1be12f9643561614aeb7a26d1ca43c3ec96ed9d1f5abdc601fe24c17bc3`.
They contain 1,282/1,272 entries, including every actual fixture and 24 supporting
records per package. Complete selected/retained partitions cover all 2,466
original artifacts. Only nine compiled/other retained artifacts are excluded
from these compact copies; original files remain retained and hash-indexed.

Each package provides the exact source/input/fixture bindings, native coverage,
resources, observed summary, root integrity result, archive index and export
index. Each archive entry identifies its original bytes and public bytes and is
classified as verbatim, a reversible portable copy, or derived metadata. Raw
source, native programs, reciprocal contexts, all intermediate registers, complete
mode logs, timing/RSS, commands, compiler/simulator outputs, cell-model identities
and statistics remain available through these indexed records or the explicitly
retained-only inventory. Full original execution directories and sources remain
untouched.

Public copies use unique typed prefix aliases; opaque hashes and numeric values
are preserved. The private map digest is recorded in the package index. One data
packaging attempt stopped before writing output because preexisting generic
alias tokens conflicted with a strict reversal check. Its record remains
retained. A new unique alias map resolved that packaging issue; no scientific
attempt or original source/receipt was changed. Deterministic ZIP reconstruction
and all raw/public hashes passed the separate
[package audit](independent-package-audit.json).

Original runner receipts still say `scientific_acceptance: unverified`.
Runner integrity, strict native/mapped comparisons and the separately preserved
[independent bounded scientific review](independent-review.json) establish
different facts. These portable derivatives cannot be passed to the host's raw
receipt verifier as if they were byte-identical originals.

## Arithmetic, lifecycle and measurement scope

The corpus contains sixteen complete generated native programs, 112 one-op
corners, one crafted 512-instruction program and an empty program. Two exact
continuous eight-program preparation contexts are distinct from the hand-built
65,538-entry index-width context. Valid reciprocal indices include
0/1/2/4/511/512/513/65537; they are indices, not divisors or VM no-ops.
Every retirement and final state matches unchanged native execution. The seven
mapped modes cover the explicit 116-case subset, including two complete native
programs; the other fourteen complete native programs are RTL-only cases.

Malformed, held, stalled, stale, early-reply, cancel/reset and generation
exhaustion checks are explicit. Cancel/reset mode aggregates count returned
requests and exclude abandoned prefixes. No whole-mode cost is inferred from
those aggregates.

Actual default synthesis gives 19,604 generic cells, 1,410 flops and zero latches. These counts belong to the
recorded local toolchain.
The [component profile](component-profile.json) retains opcode/instruction/
multiply/fetch counts and each actual measured program latency. The sixteen
complete generated programs measure 6,511–6,749 modeled clocks with ideal
instruction service and the iterative multiplier. The exact counter equation is
`3*retired + 34*muls`; the bounded direct comparison uses `3*retired + 2*muls`.
Held result clocks are excluded, and external service stalls are charged
separately. Unmeasured direct/mapped rows remain null.

The profile and final independent review/audit are separately indexed
[supplements](supplemental-index.json), with explicit origin records. The profile
is a derived post-execution artifact, not an original runner output or a new
whole-hash feasibility result.

## Reproduction and remaining boundary

Use the existing reviewed local admission and global payload slot for a fresh
output directory outside source. The exact two-phase request records are on
[task71 correctness](https://github.com/jliu67/OpenRX/issues/71#issuecomment-6224635511)
and [task71 synthesis](https://github.com/jliu67/OpenRX/issues/71#issuecomment-6224765511).
They bind the actual source, runner, command arrays, tools, prior receipt and
resources. The standalone driver also supports correctness followed by mapping
inside one admitted payload. A local six-worker invocation is:

```text
python3 -B scripts/test_superscalar_execute.py --out FRESH_OUTSIDE_SOURCE --jobs 6 --synthesize
```

The hosted workflow explicitly uses `--jobs 2` with the same driver, cases,
assertions and 1,800-second command limit. Its first six-worker run at publication
head `0beab95f65ffdee5b1b831e2f3c432d152a1ae4d` failed when `mapped-cancel`
reached that limit. Native generation, all ten RTL modes, synthesis and the other
six mapped modes passed; all 1,178 hosted fixture files exactly matched the
retained local bytes. The failed log and complete artifact remain retained.
The lower-concurrency hosted result requires its own completed check; this
change does not turn the first failed run into a pass or repeat local science.

The local correctness attempt reuses the exact retained native archive; hosted
reproduction compiles five unchanged pinned native translation units. Neither
initializes a cache. The separate synthesis-only mode requires all four actual
prior-output/receipt/receipt-SHA/root-verify arguments and validates their bytes
before reuse. A public derivative is not a replacement for a trusted raw receipt.

No complete dataset generator, physical memory technology, device frequency,
area/power, architecture choice, whole-machine efficiency or new default full
8×2,048 hash is accepted here. The next gap is the eight-step dataset-item
controller with exact seed, matching cache-line XOR and post-XOR address
recurrence, plus a bound immutable prepared-cache/program/table export and
memory-service contract. No next-stage code or workload was started.
