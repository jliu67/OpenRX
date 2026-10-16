# EXP-018 — Bounded input BLAKE2b-512

Date: 2026-10-16. Existing lifecycle task: [#71](https://github.com/jliu67/OpenRX/issues/71).
Accepted base: `eed374b28e9e2efa71bc16f5ba15e999e2940415` (merged PR #77).

## Question and implementation

Can the existing unkeyed BLAKE2b compression core supply the captured 0–80-byte
input seed directly to hardware initial fill, preserving native bytes, request
ownership, recovery and historical reproduction?

[Design](../rtl/hash/INPUT_HASH.md) records the bounded one-final-block contract,
exact byte count/zero padding, native byte order and held errors for lengths
81–127. Existing compression arithmetic, original licensed IP, pinned RandomX,
execution and preparation semantics remain unchanged. Explicit
`HARDWARE_INPUT_HASH=1` requires hardware fill; default zero retains the historical
provider path. Hardware program generation remains independently selectable.

## Executed sources and preserved attempts

The first clean standalone source is `aa7c804e8f3ae9496a61427d316de7a5e3818bc6`,
tree `d19c5afdfa5a65f9ca45ec2fcb9689698730ec56`. Execution
`20261016T174934Z-6e9224e12533` failed while compiling the new oracle: the pinned
native header requires `size_t` to be declared before inclusion. No native
vectors, RTL or mapped gate ran. Its original source, logs, failed receipt and
verified integrity remain preserved.

Connected code was separately frozen at
`90fb0e7f6d314e432d64328f41ac4e5994fe1840`. The next fix adds `<stddef.h>` before
the native oracle header. Successful standalone and the first connected request
use `307cc9ceef0328021aa7063b0930120b72884099`, tree
`aa082fb5255320aba24f25c28a212fd8608e83ba`, with clean preserved full snapshots.

Standalone retry `20261016T175348Z-0d85cf342e1a` completes with exit zero and
verified original receipt integrity. Connected request
`20261016T175815Z-3eb05e9e8f2a` retains 56 passing units and successful Verilator
ideal, stalled, input-stage cancellation and invalid-length error profiles. It
then fails in the boundary-prefix bench, which read continuously assigned
readiness immediately after cancel deassertion. Icarus had not run. The original
process remains failed, with verified receipt integrity; no success summary is
invented for that attempt.

Recovery source `2b33e60d039a9a50cb540ef2c41561de8f4035a1`, tree
`44139b83a1d3754da1aa54a78b92b5c308a4ae42`, adds only two `#1` settling delays
inside the boundary-only helper. Every assertion and all production RTL remain
unchanged; the delays add no clock edge. Independent review verifies that the
completed parameter-zero normal/cancel/error profiles are unaffected. The
remaining Verilator boundary, Icarus ideal/boundary and complete parity gates are
a new admitted request, explicitly composing retained subresults rather than
relabeling the failed process. Recovery `20261016T181450Z-21a4c330bba8`
exits zero and original receipt integrity verifies. The bounded composite passes
all declared gates; both original failed processes retain their failed status.

## Standalone measurements

| Gate | Actual result |
|---|---:|
| Native differential vectors / valid lengths | 614 / 81 |
| Poisoned unused tails / arbitrary cases | 162 / 128 |
| RTL modes / unsupported lengths rejected | 18 / 47 |
| Focused mapped vectors / mapped modes | 26 / 16 |
| Mapped unsupported lengths | 81 and 127 |
| Valid result availability | 28 clocks |
| Wrapper plus existing core generic cells | 38,538 |
| Flop cells / inherited latch cells | 3,753 / 1,024 |

Reset/cancel controls span before start, early/middle/final computation and held
return. Held request/result, descriptor mutation and changed-length restart
checks pass. Mapped control records equal their RTL records. Source and fixture
hashes remain unchanged. The original compression G operand latches are
reported separately, and no arithmetic/IP rewrite is implied.

## Connected gates and accounting

The bounded request covers hardware input/fill/program mode with two programs
and one iteration: Verilator ideal/stalled and Icarus ideal; complete ideal
ledger, PASS record, raw trace, digest and all 18 native assertion files must
agree. It also covers input-stage cancel/restart, held invalid-length terminal
error, and both-backend empty/max80/changed-input/invalid81/127 prefixes with zero
accepted SRAM writes. Prefix recovery is not a second completed hash.

The input seed must be complete and match the current generation before any
scratchpad work. Removed initialization responses/writes drain without supplying
data or errors. Native input hashing and AES generation in these checks are
assertion-only; live input/fill/program provider calls must be zero. Input stage
clocks are disjoint from fill, with nested phase counters partitioning that
stage and zero host provider wait. Native dataset callback time remains separate.

Measured totals are 534,040 ideal and 1,583,565 stalled clocks. Input hashing is
30 disjoint clocks, partitioned `[1, 28, 1]`; the normal input has 55 bytes.
Complete ideal backend ledger/PASS/trace/digest and all 18 native corpus files
agree. Both boundary-only profiles pass empty/max80/changed80/cancel/reject81/127
checks with zero SRAM writes. All 56 focused lifecycle checks pass. The native
final digest is `8d260e80e2d3541ae84a3fef610a6475e3f8373fcc437ce246181f51d8481da1`.

## Retention, resources and limits

[Evidence](../docs/validation/input-blake2b-20261016/README.md) binds exact
commands, inputs, fixtures, tools, resource witnesses, complete retained outputs,
portable derivatives and original receipt hashes. Immutable runner657 serializes
each payload. Admission verifies actual CPU600000/100000, 4 GiB RAM, 2 GiB swap,
Tasks256, six-CPU affinity, effective ancestor ceilings and fresh OS headroom.
The budget reuses prior measured compilation/simulation peaks; parallel compiler
work can use six workers while simulators are mostly serial.

Only input lengths 0–80 are supported. No new default 8×2,048 run, complete
recovery matrix, whole connected mapping, hardware Light cache/dataset service,
physical PPA, architecture selection or whole-machine target follows. The
historical full measurement remains source `c96e96ab` at 40,975,538
hardware/transport clocks; it is not relabeled as this source or hardware mode.
Independent scientific/final-head review and hosted CI remain separate gates.

## Hosted binding metadata successor

The first public head's new standalone CI step passed, but its historical source
guard rejected the unchanged declaration's stale workflow digest. The correction
updates only that existing staged digest; guard code, original/historical maps
and all hardware inputs stay unchanged. Eighteen source-only tests and explicit
workflow/stale-digest rejection cases pass under verified runner receipt
`20261016T184732Z-7c6f2889a8e8`. Complete failed hosted logs/archives remain
retained; no result is relabeled. See the evidence record for distinct hosted
mapping counts, prelaunch interpreter-binding rejection and successor gates.
