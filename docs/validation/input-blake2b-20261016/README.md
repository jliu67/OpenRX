# Bounded input BLAKE2b evidence — 2026-10-16

This feature moves the existing **0–80-byte** input seed across the live host
provider boundary using the accepted BLAKE2b compression core. It rejects
unsupported lengths 81–127. It does not implement arbitrary-length input,
hardware Light cache/dataset service or a physical ASIC target.

[Design](../../../rtl/hash/INPUT_HASH.md) and
[EXP-018](../../../experiments/EXP-018-bounded-input-blake2b.md) describe the
interface, ownership, byte order, stage accounting and reproduction boundary.
Accepted base is `eed374b28e9e2efa71bc16f5ba15e999e2940415` (PR #77).
Existing [task #71](https://github.com/jliu67/OpenRX/issues/71) records the exact
execution requests; no new issue or reopening was needed.

## Attempts and exact sources

| Package | Original execution / source | Result and retained scope |
|---|---|---|
| `failed01` | `20261016T174934Z-6e9224e12533` / `aa7c804e8f3ae9496a61427d316de7a5e3818bc6` | Failed native-oracle compilation: missing `size_t` declaration before the pinned header; no native vectors, RTL or mapping ran. |
| `standalone02` | `20261016T175348Z-0d85cf342e1a` / `307cc9ceef0328021aa7063b0930120b72884099` | Successful standalone oracle, RTL, synthesis and mapped controls after the one-line `<stddef.h>` fix. |
| `connected01-partial` | `20261016T175815Z-3eb05e9e8f2a` / `307cc9ceef0328021aa7063b0930120b72884099` | Process remains failed. Fifty-six units and Verilator ideal/stalled/cancel8/error7 passed; the boundary-prefix bench then failed before Icarus. |
| `connected02-recovery` | `20261016T181450Z-21a4c330bba8` / `2b33e60d039a9a50cb540ef2c41561de8f4035a1` | Exit zero and original receipt integrity verified. Only the missing Verilator boundary, Icarus ideal/boundary and complete parity gates ran; their bounded composite passes. |

The connected failure was an immediate readiness read after cancel deassertion.
The recovery adds exactly two `#1` settling delays inside the boundary-only
helper. It preserves every assertion, adds no clock edge and changes no
production RTL. Independent source/artifact review verifies that original
normal/cancel/error profiles compiled with `INPUT_HASH_BOUNDARY_TEST=0` are
unaffected. The recovery driver pins the original failed receipt, checks actual
consumed artifact bytes against it, compares the complete helper delta and
revalidates raw ledgers and PASS/return-code records. It does not assume or invent
an end-of-run summary for the failed process.

[Executed-source bindings](executed-source.json) name all 11 runtime/test paths
and the sole boundary-helper successor. The [package-set index](package-index.json) binds each compact
export; its full inventories retain every original artifact.

Original failed statuses and machine `scientific_acceptance: unverified` fields
remain intact. A successful composite, original receipt integrity and independent
scientific acceptance are separate facts.

[Independent bounded review](independent/final-bounded-review.json) accepts the
code, standalone evidence, connected composite and compact exports with no
blocking findings. Its [provenance index](independent/index.json) binds the
retained original and explicitly portable render. Final publication-head review
and hosted CI are recorded separately on the feature PR.

## Standalone measurements

The native oracle calls the unchanged pinned `blake2b.c`: 614 main vectors cover
all 81 valid lengths, four patterns per length, 162 poisoned unused tails and
128 arbitrary cases. Empty input is also checked with a null native pointer.
The RTL corpus and controls pass in 18 modes; all 47 unsupported lengths are
rejected with held zero-seed errors. Sixteen mapped modes use 26 focused boundary
vectors and the corresponding held/reset/cancel/restart controls, including
invalid lengths 81 and 127. Their PASS records equal RTL records.

Valid response availability is **28 testbench clocks**. Actual generic synthesis
of the new wrapper plus unchanged compression core is **38,538 cells, 3,753 flop
cells and 1,024 inherited latch cells**. The G operand latches are retained and
reported separately. This mapping excludes the lifecycle, scratchpad and internal
Program image buffer. Source and fixture hashes remain unchanged after the run.

## Connected acceptance boundary

The verified bounded composite has three normal 2-program ×1-iteration profiles:
preserved Verilator ideal/stalled and new Icarus ideal. It requires complete ideal
ledger/PASS/raw-trace/digest equality and all 18 native assertion files equal
across old Verilator, recovery Verilator and Icarus. Preserved cancellation8 and
invalid-length error7 are separate successful subresults of the failed attempt.

Both backends additionally check native empty/max80/changed-input seed prefixes,
input-stage cancellation, invalid lengths 81/127 and removed-provider draining
with zero accepted SRAM writes. These recovery prefixes do not claim another
completed hash. Native input hashing and AES program generation in the bench are
assertion-only; live input/fill/program provider calls must be zero. Native Light
dataset callbacks remain live and their host seconds are not device clocks.

Completed Verilator normal profiles measure 534,040 ideal / 1,583,565 stalled
clocks, with a disjoint **30-clock input stage**, nested `[1, 28, 1]`, and zero
initialization host-provider wait. The supported request used 55 input bytes.
Icarus confirms the complete ideal ledger, PASS record, raw trace and digest;
all 18 native assertion files agree across the three retained/generated corpora.
The final digest is `8d260e80e2d3541ae84a3fef610a6475e3f8373fcc437ce246181f51d8481da1`.
All 56 focused lifecycle unit checks pass. The original failed connected payload
remains failed; the receipt-bound `checks.json` in the recovery archive names
the composite scope.

## Portable packages and retained originals

Each package has a deterministic `records.zip`, per-member archive index,
complete selected-versus-retained original-receipt inventory, execution/resource
metadata and a few readable records. Expanded staging copies are also retained.
The failed connected package's `summary.json` represents its actual failure
record; successful subprofile facts are separately derived from original raw
ledgers/logs. It is not a fabricated original success summary.

Verbatim copies retain original byte hashes. Portable or selected metadata is
explicitly derived, with original hashes, public hashes and ordered logical
prefix-replacement rules. A private alias map remains retained locally and has a
public hash binding; private prefix values are not published. Opaque hashes and
numeric measurements are unchanged. Portable receipts are not original host
receipts and cannot be passed to the host integrity verifier as originals.

Complete source snapshots, manifests, original receipts, raw traces, full images,
native cache/corpus, compiler objects, simulator binaries, netlists, failures and
checkpoints stay retained in their original locations. The receipt inventories
account for every original artifact without overlap or omission. Compact public
copies are not complete host executions.

## Reproduction and resources

Execute only through the existing admitted runner/global payload slot, with a
clean pinned source, fresh external output directory and bound tools/resources.
The component command is:

```sh
python3 -B scripts/test_input_blake2b.py --output "$OUT/standalone" --synthesize
```

The connected driver is `scripts/test_prepared_hash_lifecycle.py` with
`--hardware-input-hash --hardware-fill --hardware-program --programs 2
--iterations 1 --variants prepared --event-trace --input-hash-boundaries`.
Icarus uses `--backend icarus --profiles ideal`; Verilator normal profiles use
`--backend verilator --profiles ideal stalled --cancellation
--cancellation-phases 8 --matching-errors --error-ports 7` plus the verified
Verilator root/build receipt. The missing boundary-only recovery uses
`--interfaces-only --backend verilator --profiles ideal`.

Recorded requests bind the reused native library/build receipt and Verilator
tree, source directories and exact external orchestration driver. Public
orchestration renders are identified as portable derivatives; retained originals
and their hashes remain the executed authority. Fresh builds on another host are
new artifacts with separate tool/provenance identities.

Immutable runner657 verifies actual CPU600000/100000, 4 GiB RAM, 2 GiB swap,
Tasks256, six-CPU affinity, effective ancestor limits and fresh memory headroom
before launch. Compiler workers can use all six cores; the simulators are mostly
serial. Peak command RSS is an observed process measurement, not aggregate job
memory or physical ASIC memory. Every request is distinct and retained; completed
historical jobs are not interrupted or restarted.

There is no new default 8×2,048 measurement, complete new-mode recovery matrix,
whole-engine mapping, hardware Light cache/dataset implementation, physical PPA,
architecture selection or whole-machine target acceptance. The historical full
record stays attributed to `c96e96ab` at 40,975,538 hardware/transport clocks.
Final independent exact-head review, applicable hosted CI and normal merge
safeguards remain separate from the local component evidence.

## Hosted source-binding correction

[CI recovery export](ci-binding-recovery/execution.json),
[package index](ci-binding-recovery-package-index.json) and
[independent source-only validation](ci-binding-recovery-independent-validation-review.json)
bind the focused correction and preserved failure history.

Initial publication `f17fc8ce1c3e1937a403f810739276fb50a2b178` added the
unconditional standalone input check but retained the earlier staged workflow
SHA in the combined-source declaration. Five hosted jobs rejected the changed
workflow at that guard; their complete original logs and five artifact ZIPs
(222,621,518 bytes) remain retained with GitHub digest matches. The hosted input
step itself passed 614 native, 18 RTL and 16 mapped modes before the subsequent
historical gate rejected the stale declaration. Hosted mapping is separately
33,177 generic cells, 3,366 flop cells and 1,024 inherited latches; it does not
replace the earlier local tool/result identity or establish physical PPA.

Source `3d81d80c4c3eff798a5354470470f4bc1a0eed0d` changes exactly the existing
staged workflow digest from `9119d790…` to actual `d1990ab5…`. Kind, staged state,
guard code, immutable historical maps, native sources and all 11 runtime/test
paths remain unchanged. A first tiny request was rejected before launch because
its Python input was a symlink; the revised request binds the regular interpreter.
No payload or scientific failure is attributed to that prelaunch rejection.

Admitted source-only execution `20261016T184732Z-7c6f2889a8e8` passes all 18
existing binding tests, the positive guard and isolated mutated-workflow/stale-
digest rejection cases in 3.345 seconds. Its original receipt integrity verifies.
Actual kernel limits are CPU600000/100000, 1 GiB RAM, 2 GiB swap and Tasks256;
allowed CPUs are0–5 with no tighter ancestor ceilings. No native/HDL/synthesis
work was performed. The original hosted jobs retain their actual outcomes;
normal successor-head CI and independent exact-head review remain separate.
