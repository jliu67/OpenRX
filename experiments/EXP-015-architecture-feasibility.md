# EXP-015: executable RandomX v2 architectural feasibility gate

[Task #72](https://github.com/jliu67/OpenRX/issues/72) adds
[executable Python model and reproduction commands](../tools/architecture/README.md),
focused tests, a portable actual native/RTL fixture, constrained comparison
outputs and necessary scratchpad/dataset/whole-wall-energy bounds. The accepted
parent is main `f13e5b5223e87c91a848adedc23502b5a42d4754`. No existing RTL, vendor
source, provider, reference workload or accepted evidence is modified.

The full-workload measurement remains the default 8×2,048 native-reference-correct
connected run at `c96e96ab1eb46cb727b21befffa526e637ebed4a`: 40,975,538 simulated
hardware/transport clocks. Its exact outer event trace is checked against the
accepted SHA and ledger. Nested iteration timing comes from the separately
identified per-clock bench counters, because that run's sparse CSV omitted
iteration and executor transitions. Fixed-state equations close without fitted
constants while retaining the measured 39,946,977-clock executor aggregate as
an explicit unpredicted input. This is partial source-state calibration.

The first parser attempt rejected an incorrect nested-phase inference. That
failed attempt and frozen source remain preserved. The correction leaves nested
CSV durations null, labels the accepted direct counters and saves scan diagnostics
before validation gates. The retry reprocesses preserved inputs; it does not
repeat any RTL or native hash simulation.

The accepted short successor supplies 3,081 exact instructions in eight disjoint
bytecode windows. Native route checksums, memory order/addresses and store lanes
are verified. Its bounded seed lineage differs from the full default hash after
program zero. Scheduling preserves RAW/WAR/WAW, branch and rounding barriers,
nonpipelined FU occupancy/II, finite issue width/window, memory ordering, banks,
ports, bandwidth and outstanding queue limits. Repeated contexts have separate
mutable state but identical replayed paths. New hardware correctness and timing
are unvalidated. These windows exclude outer AES/entry/tail and dataset service;
no full-hash speed ratio, MHz, hashes/s, power or ASIC feasibility is inferred.

The model sweeps blocking, multicontext blocking, limited nonblocking and dual
issue; 1/2/4/8/16 contexts; abstract response latency; FU II, banks/ports,
bandwidth and queues. Full-workload necessary bounds separately account for
2 MiB per live context, prefix placement/backing, transfer granules/RMW,
fill/scan, dataset bytes, request concurrency and full-image save/restore.
Whole-wall power remains unknown unless every compute/memory/provider/fabric,
leakage/refresh, controller/PHY, VRM, fan, auxiliary and PSU term is supplied.
At the requested target the strict complete energy ceiling is 2.5 mJ/hash.

[Machine-readable results and validation notes](../docs/validation/architecture-feasibility-20261016/README.md)
retain measured, source-derived, assumed and unknown provenance. No physical
frequency, process, memory technology, SRAM macro or production engine count is
selected. The next justified hardware experiment is a parameterized context-tagged
blocking dispatcher with independent scratchpad namespaces, explicit resource
arbitration and issue/completion/readiness instrumentation, validated against
native values and the existing complete lifecycle. Evidence from that wrapper
should gate additional nonblocking queues or wider issue.

Independent review is required before merge; this task performs no merge.
