# EXP-004: actual iteration-tail stores and AES overlap

Status: local differential RTL and synthesized-netlist checks passed;
new-work independent review pending on [task #50](https://github.com/jliu67/OpenRX/issues/50).

## Hypothesis and scope

The R stores at the pinned interpreter's post-dataset boundary use independent
captured registers. They can proceed while the reviewed AES stage computes F,
provided every R store commits before any F store. This should hide four 128-bit
R-store beats without changing scratchpad or architectural F results.

This implements that **iteration tail**, not a full core. The actual selected
processor/cache/fabric and technology SRAM macro are missing accepted interfaces.
The new top supplies an explicit ordered 128-bit SRAM write boundary, final F,
cursor reset and completion. The simulated 2-MiB scratchpad is excluded from
generic synthesis counts; no physical frequency, area, power or hash-rate result
is established.

## Pinned differential reference

Parent source is immutable reviewed PR49 head
`9a3271d515b8bf4c3f25ec43571b495fe3cb8f5c`; its code and branch remain unchanged.
RandomX v2.0.1 is pinned at `aaafe71322df6602c21a5c72937ac284724ae561`.
The harness verifies all 19 reviewed core input identities and the complete vendor
manifest. It extracts the original interpreter iteration body, dataset-read body
and base destructor **verbatim**, retaining original notices and body digests.

The software fixture compiles and runs the unchanged `BytecodeMachine` with full
version-specific program lengths and eight controlled instruction families:
IADD_RS, IXOR_R, IMUL_R, INEG_R, FADD_R, FSUB_R, FMUL_R and FSWAP_R. A virtual
dataset provider maps the actual read address to a deterministic 64-byte fixture
line, then uses the pinned dataset-read XOR body. It captures post-dataset R/F/E
and masked addresses; the original iteration code continues through real R/F
stores and cursor reset. This is neither a full dataset nor a full RandomX hash.
The controlled prefix has no scratchpad stores, so its scratchpad effects are
exactly the tail covered by the RTL.

Seed `0x697465722d746169` generates 128 controlled iterations: 64 v2 then 64 v1.
The trace includes 32 equal-address cases, line 0 and the last valid line.
Every configuration compares 1,024 committed beats, post-iteration memory regions,
final F/cursors, and all 2,097,152 final scratchpad bytes. It also checks memory
and completion backpressure and two partial-reset cases. Reset aborts control
without undoing already committed stores; no transactional rollback is claimed.

## Configuration and reproduction

```bash
python3 scripts/test_iteration_tail.py --output /tmp/openrx-tail-fresh-attempt --synthesize
```

Icarus 11.0/GCC 11.4/Yosys 0.9 versions, commands, generated upstream bodies, exact
inputs, images, traces and full mapped netlists are retained in
[the evidence](../docs/validation/iteration-tail-20261012/README.md).
Serial references (`OVERLAP_R=0`) wait for AES availability before writing R/F;
delivered configurations (`OVERLAP_R=1`) issue R stores during compute. Both
preserve R-before-F visibility. The ordered memory interface accepts one 16-byte
beat per clock for the v2 comparison; operands arrive as a complete bundle and
completion transfers without stalls. The later v1 trace exercises deterministic
backpressure. An out-of-order fabric needs a separate ordered-commit adapter.

## Observed results

| LANES | R scheduling | No-stall v2 interval | 64 v2 iterations, cycles | Generic top cells | Flip-flops |
|---|---|---:|---:|---:|---:|
| 1 | Serial reference | 25 | 1,600 | Not synthesized | Not synthesized |
| 1 | Overlap | 21 | 1,344 | 46,510 | 2,605 |
| 4 | Serial reference | 13 | 832 | Not synthesized | Not synthesized |
| 4 | Overlap | 9 | 576 | 90,661 | 2,603 |

All four RTL configurations pass the same reference trace and full-memory
comparison. Both delivered overlap configurations are synthesized and their
actual mapped netlists pass the identical differential tests. R overlap removes
four cycles from each lane configuration: 25/21=1.1905× and 13/9=1.4444× transactions
per clock. Four-lane versus shared overlap is 21/9=2.3333×; this is smaller than
the register-only stage ratio because F stores and retirement are now included.
Generic cell counts include AES and the new controller/retirement storage, with
physical scratchpad memory excluded.

The run used checked CPU 600%, RAM 4 GiB, swap 512 MiB and 128 tasks, one worker and the
existing global slot; capacity and measured RSS/utilization are recorded in
[resources.json](../docs/validation/iteration-tail-20261012/resources.json).
Full successful attempt 03 and earlier development outputs remain retained.
No tool installation, standing editable mirror, protected push, merge or original
scientific source/build/data/receipt mutation occurred.

## Interpretation and next action

This closes the component's memory-store boundary under an explicit SRAM contract
and actual pinned software differential. It does not close selected-core,
dataset, whole-hash or calibrated-PPA gates. Independent new-work review remains
required. The next integration needs a concrete core/register-file and ordered
scratchpad-memory interface, not another broad survey or a massive SoC build.
