# EXP-009: native iterative division and square root

Status: all twelve RTL and eleven applicable mapped modes pass; independent review pending.
Parent: accepted unmerged PR #59 `ce788d11285c901b52fd3cf0b450489d13b3f2f5`.
Task: [#60](https://github.com/jliu67/OpenRX/issues/60). No merge is authorized.

[Design](../rtl/execute/DIVSQRT.md) records native masks, rounding, DAZ/FTZ,
special-value initialization handling, ready/valid scheduling and reproduction.
The independent pinned native oracle covers all 256 raw encodings/29 families,
2,856 actual retirements including 152 divides/146 roots, all four rounding modes,
all 2 MiB memory, branches/CFROUND, four chains and four aliases. Primitive
13,312 full / 2,560 mapped balanced records verify bits and flags. Arithmetic
from accepted PR #59 is retained byte-for-byte and its full primitive evidence
reused; mixed native traces validate integration. No unrelated baseline/core/hash expansion.

Shared/parallel units map to 8,690/12,942 generic cells and
779/558 flip-flops. The shared schedule costs 17,228 extra
clocks in both controlled ideal/stalled fixtures. Whole default is 274,346
cells / 10,504 flops. Variable operand latency is reported as measured;
there is no fixed per-operation assumption or physical/full-hash claim.

The unit payload used checked CPU 600%, 2 GiB RAM, 512 MiB swap, Tasks 128,
six-CPU affinity and one worker under the global slot/fresh 1 GiB reserve.
Cgroup peak 640,303,104 bytes, swap zero, max/OOM/throttle events zero.
Whole default used checked CPU 600%, 7.5 GiB RAM,
2 GiB swap and the same tasks/affinity/worker/ancestor/fresh-reserve checks.
Measured peak 8,053,063,680 bytes, swap peak 593,715,200, memory-limit events 585,
OOM/kills zero. All six CPUs were available; largely serial tools used one worker.
Actual timings/pressure/drainage are retained. The initial upstream special-value
wrapper failure and coverage/cancellation fixture corrections are archived with
exact source, outputs and hashes; no requirement was relaxed. [Complete evidence](../docs/validation/divsqrt-execute-20261013/README.md)
binds licenses, inputs, native/mapped records, failures, resources and archives.
Complete VM/hash, selected-core and physical/calibrated PPA gates remain open.
