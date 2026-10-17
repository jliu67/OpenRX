# EXP-019: prepared native superscalar-program executor

Status: bounded native/RTL/mapped validation passed; publication, exact-head review
and hosted checks are separate gates recorded on the feature PR.

The component is above accepted merge
`9d28cd8e6467fcc6eee9d3a623c38fd796c3cb2a` (PR #78). It executes one externally
prepared native superscalar program with the unchanged accepted
`randomx_mul64`. The controller processes instructions in order, one at a time;
`MUL_RADIX4=1` is its default, and a bounded direct-variant comparison is retained.
Existing VM and lifecycle defaults remain unchanged. See the
[contract](../rtl/execute/SUPERSCALAR.md),
[evidence](../docs/validation/prepared-superscalar-20261016/README.md) and
[component profile](../docs/validation/prepared-superscalar-20261016/component-profile.json).

## Exact executed source

Both admitted attempts use clean source
`6f65049c32e5e065a711d105cf2eb42204ed2285`, tree
`19ac91c6bbcab959cfeae9fc1305ff137d9fdf3a`, 4,718 tracked files and full source
identity `0fc0f7acc491d9afce219893fbb52131dc684d03781da2dc247edda81bfe439f`.
The four new runtime/test files and existing multiplier are bound explicitly; all 171 native
files match pinned v2.0.1 `aaafe71322df6602c21a5c72937ac284724ae561`.
The accepted multiplier SHA256 remains
`e0a42d6005fac370cb431fd8cdb0cfe8138a8260306b57a0ee428743569d1b0f`.
Publication additions describe the completed evidence and integration contract;
executed RTL, oracle, bench and driver bytes remain exact.

The native oracle reuses the existing library at SHA256
`bddb3f9a206b1ec34ca78d3a9b13a9388d7312d6660b7d148d4ed514958fb8d6`;
only the new oracle is compiled. Hosted reproduction can compile its five
unchanged native translation units. Neither path allocates a 256 MiB cache or
calls Argon2/dataset initialization.

## Correctness before mapping

[Request](https://github.com/jliu67/OpenRX/issues/71#issuecomment-6224635511)
launched `20261016T210802Z-d50e99dbfb16`, with verified receipt SHA256
`f7598ff088d64e4be511cc9c6e8d89a5e67a14c9b1c591856757e5aea058e060` and
manifest `6da3cb365c3b505a507a49d4a499c203749d22224738aa53a90d43bfb9d76032`.
It passes 130 native cases, all 7,779 intermediate retirements and ten RTL modes.
Sixteen complete programs come from two fixed, continuous eight-program native
generator contexts. Another 112 one-op cases, a crafted 512-instruction program
and an empty program cover all 14 opcodes, aliases, ignored source fields,
sign extension, shifted add, rotates 0/63 and signed/unsigned products.

Two native preparation tables retain the exact global reciprocal-index rewrite.
A separately labeled, hand-built 65,538-entry table tests indices
0/1/2/4/511/512/513/65537 without index truncation or VM divisor/no-op rules.
Singleton native stepping, full prepared execution and raw-divisor native
execution agree. Golden intermediate/final registers are assertion-only.

Default iterative RTL controls reject all opcode bytes 14–255, malformed used
register fields, rotate values above 63, descriptor bounds, wrong matching-context
metadata and reciprocal/provider errors. They check held transfers, early matching replies
through request acceptance, stale packets in every state, exact error prefixes,
cancel/reset in phases 1–6 and multiply offsets 0/16/31/32, and fresh complete
native successors. A real 65,535-request sequence reaches fail-closed generation
exhaustion, including a final nonempty program; cancellation cannot recycle it.
A quiescent reset clears exhaustion. Malformed mode returns 273 errors and one
fresh success; cancel and reset modes each test 18 aborts and 18 successors.
Aborted-prefix work is checked but excluded from their returned-request totals.

## Separate synthesis and mapped comparison

Only after correctness and receipt integrity passed,
[request](https://github.com/jliu67/OpenRX/issues/71#issuecomment-6224765511)
launched `20261016T211324Z-b1d24eb3f1fe`. Verified receipt SHA256 is
`27591eb90d4e8f06d90dca641d830a1f9c9fd35dd57c656a7b93e4db05c2231c`;
manifest is `7069e13dea4e314dd09c0bfeec5e668a128ac6c28585678b88aaf5835d054cec`.
It consumes all 1,178 prior fixture files through the exact prior receipt and
root-verification bindings. It performs no native generation or completed RTL
repeat. All seven mapped modes match prior RTL records and latency files exactly.

The mapped corpus has 116 cases: 112 corners, two complete generated programs,
the 512-instruction program and empty program. Every retirement and final state
is checked. Held, stalled, malformed, stale, cancellation and reset modes also
pass. The other 14 complete generated programs were checked in RTL and are not
claimed as mapped cases.

Actual default Yosys synthesis of the executor and unchanged multiplier yields
19,604 generic cells, 1,410 flop cells and zero latches. These counts belong to the
recorded local toolchain. Complete netlist, cell
model, cell-type counts and statistics are retained. External program/table
storage and service, cache memory, preparation and dataset control are excluded.

## Measured component clocks and operations

| Completed corpus/profile | Retirements | Multiplies | Modeled clocks |
| --- | ---: | ---: | ---: |
| 130-case iterative corpus | 7,779 | 2,724 | 115,953 |
| 116-case iterative/mapped subset | 1,517 | 549 | 23,217 |
| Same 116 cases, direct multiplier RTL | 1,517 | 549 | 5,649 |
| Two generated programs, ideal service | 893 | 309 | 13,185 |
| Same two programs, controlled stalled service | 893 | 309 | 17,649 |

Each of the sixteen complete generated programs measures 6,511–6,749 clocks
with ideal instruction service and the iterative multiplier. The counter closes
as `3*retired + 34*muls`; the direct comparison closes as
`3*retired + 2*muls`. Stalled service adds exactly 1,786 request-stall and 2,678
response-stall clocks in the two-program profile. Descriptor acceptance is time
zero; held return clocks are excluded. These are modeled hardware clocks,
independent of host execution time and physical frequency.

The machine-readable component profile preserves each program's instruction,
opcode, multiplication and instruction-request counts, selected register,
reciprocal-table context and actual measured clocks. Unmeasured direct/mapped
rows remain null. These measurements can support later feasibility work; they do
not close a full dataset or full-hash timing equation.

## Resources, provenance and remaining boundary

Both attempts use immutable runner657 and the single global payload lock, with
actual under-lock CPU600000/100000, RAM4GiB, swap2GiB, Tasks256, six CPUs and no
tighter visible ancestor limit. Up to six independent modes run within one
payload; compilation/generation/synthesis are sequential phases. Observed
synthesis cgroup peak was 536,395,776 bytes with no OOM events; largest per-command
RSS was 160,128 KiB for correctness and 344,788 KiB for synthesis. Yosys synthesis
took 44.224 seconds; the long mapped cancel/reset modes took 238.648/230.809
seconds. These host resource observations establish no device power or speed.

Both original runner records remain `scientific_acceptance: unverified`.
Integrity verification, strict native/mapped checks and independent scientific
review are separately documented. Both first attempts passed; complete sources,
fixtures, logs, outputs, commands, binaries, resources and all earlier assets are
retained. Compact public derivatives have separate origin and public digests.

Program preparation, reciprocal ownership, Argon2/cache initialization and cache
memory service remain external. The next concrete gap is an eight-step dataset
item controller: exact item-register seed, prepared program execution, matching
cache-line XOR, then address selection from the post-XOR register state. It also
needs an immutable prepared-cache/program/table export and tagged service
contract. No next-stage implementation or execution is launched here. No complete
dataset generator, new default full 8×2,048 hash, memory-technology choice,
architecture selection, physical PPA or whole-machine efficiency follows.

Existing task #71 retains the execution and handoff records without changing its
completed state. No new issue, hub notice, standing editable mirror or Git sync
is created.
