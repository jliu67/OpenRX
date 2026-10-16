# Executable architecture feasibility gate — task #72

This standard-library Python model reuses accepted native/RTL evidence. It
produces constrained scheduling scenarios and necessary resource bounds. It
does not demonstrate ASIC performance, select a process, frequency, memory
technology or production engine count, or establish the 1 MH/s / <2,500 W target.

## Reproduce

From the repository root, with Python 3.10 or later:

```sh
python3 -B -m unittest discover -s tests -p 'test_architecture*.py' -v
python3 -B -m tools.architecture.run reproduce \
  --fixture tools/architecture/fixtures/successor-first-iterations \
  --evidence docs/validation/architecture-feasibility-20261016/full-evidence.json \
  --output /tmp/openrx-architecture-reproduction-new --workers 1
diff -u docs/validation/architecture-feasibility-20261016/comparisons.json \
  /tmp/openrx-architecture-reproduction-new/comparisons.json
diff -u docs/validation/architecture-feasibility-20261016/sensitivity.json \
  /tmp/openrx-architecture-reproduction-new/sensitivity.json
```

The output directory must be new. On the designated project server, submit this
payload through the installed admission/global lock and substitute its execution
output directory; the portable `/tmp` example describes standalone reproduction.
`--workers 1..6` changes host parallelism,
not modeled hardware. Full trace extraction uses `run extract --help`, retained
accepted evidence and the installed server admission/global lock. Reproduction
needs only the compact committed fixture and derived full-workload counts.
No workload or RTL simulation is launched by these commands.

Accepted-run attribution requires the actual full-evidence SHA-256 and every
portable fixture file digest to match the trusted bindings in `run.py`, recorded
from preserved run03 and source `46fa0737`. Embedded trace/source-map hash claims
cannot establish identity. `reproduce` writes `provenance.json` and rejects an
untrusted input before replay or comparisons. Different extraction metadata also
changes byte identity: `extract` preserves its extracted inputs and untrusted
provenance, then stops before accepted-run comparisons. Extending these bindings
requires review of the new exact inputs; changing a source-map claim is insufficient.

## Evidence and timing boundaries

The full 8×2,048 v2 connected run executed source `c96e96ab1eb46cb727b21befffa526e637ebed4a`
and matched unchanged canonical `randomx_calculate_hash`. Its 40,975,538 clocks
measure simulated hardware and transport. Main `f13e5b5` merges the independently
reviewed successor `d3ed898`; the full run was not repeated at that successor.
Its accepted normal-path transfer does not turn the successor's short tests into
a new full measurement. Existing exact-source evidence remains in
[EXP-014](../../experiments/EXP-014-connected-v2-lifecycle.md).

`evidence.py` streams the original sparse event CSV once, checks its accepted
SHA256, counts committed instructions/accepted transactions, independently
extracts native address locality and compares outer stage durations with the
accepted ledger. Nested iteration durations come from the accepted per-clock
bench counters, separately identified from the event CSV. Fixed-state equations explain transport,
preparation, seeds, finalization, metadata and nonexecutor iteration costs.
The execution model retains the measured **39,946,977-clock executor aggregate**
as an explicit unpredicted input. The full CSV omits internal iteration and
executor state transitions; sampled nested states cannot be integrated into timing.
Zero fixed-stage residual is a partial source-state replay calibration, not an
independent full-hash timing prediction. There are no fitted residual constants.

The accepted 8×2 successor's richer trace supplies the first complete bytecode
iteration from each of eight programs: 3,081 instructions in eight **disjoint**
windows. `native_trace.py` checks their committed PC paths, legal lexical branch
targets, native route checksums, memory order/addresses and store byte lanes.
Per-operation nonmemory service spans come from observed executor transitions.
Native arithmetic/register values are not recomputed by this scheduler; their
correctness comes from the existing accepted RTL/native tests. Bounded programs
1–7 follow a different seed lineage from the default full run. The windows are
neither contiguous full-hash work nor a representative workload distribution.

Input BLAKE2b, initial AES fill, AES program generation and dataset generation
remain untimed host providers. Dataset values came from native light mode using
a 256 MiB cache; no complete dataset was materialized and no physical DRAM was
modeled. Host seconds are not device clocks. Their device latency, energy and
internal physical traffic stay unknown. The final hardware scan/digest and
initial image transport are measured separately from generating that image.

## Scheduler contract

`scheduler.py` is a deterministic event scheduler with explicit integer cycle
latency, FU count, initiation interval and nonpipelined occupancy. Issue and
completion differ. Each context has distinct register and mutable memory state.
The read-only dataset fabric is shared. RAW, WAR and WAW dependencies constrain
completion; register renaming and branch speculation are absent. CBRANCH and
CFROUND drain older work and hold younger work, conservatively preserving
conditional rounding-mode behavior. Strict per-context memory ordering is the
comparison default; optional address ordering preserves aliases and unknowns.

All scenarios share one nonpipelined unit per class. Blocking contexts have one
operation in flight. Limited nonblocking and dual issue use eight trace positions
of lookahead, including holes already issued. Dual issue retains the same FU
pool; width alone grants neither extra units nor more independent reads.
Memory enforces bank ports, aggregate bytes/cycle, outstanding queue capacity
through complete memory-macro completion, and finite response latency. Queue
slots remain reserved during the post-response compute portion too, a conservative
occupancy assumption. The reference scenario has eight
shared banks, one port each, 16 B/cycle and eight outstanding requests. These are
assumptions, not an implementation commitment. Bank mapping is address/8 modulo
bank count; repeated contexts replay the same window and therefore its correlated
bank pattern, rather than an invented IID conflict rate.

Memory macroops charge nonmemory service plus transfer/response serially and
hold their FU throughout. For stores, the real address EXEC precedes transfer;
the summed macro abstraction conservatively charges that work without predicting
phase placement. Splitting address/load/FU service is a future refinement requiring
explicit readiness traces and validation. The model supplies no forwarding,
cache hit rate or unlimited request queue. Stall counters count blocked candidate
checks and are not disjoint elapsed-cycle categories.

`comparisons.json` covers single-issue blocking, multicontext blocking, limited
nonblocking and dual issue, with 1/2/4/8/16 contexts and response delays 0/10/50
abstract cycles. Separate one-factor sweeps vary banks, ports, bandwidth, queue
capacity and II. Results are per-window batch completion and cycles/window job.
The JSON deliberately leaves full-hash cycles, hashes/s and watts null. Outer
entry/AES/tail and dataset dependencies are absent from these scheduling windows;
their full-hash alternatives remain unvalidated. Do not extrapolate a window
speed ratio to the whole hash or combine independent sweep minima into a design.

`baseline-calibration.json` separately checks each detailed scalar window against
`2*instructions + measured nonmemory service + 2*loads + stores` clocks from
first fetch to final commit, plus one RETURN clock for executor wait. The two
fetch states and load request/reply states each consume one ideal clock; accepted
stores consume one. All eight residuals are zero. FU service remains a measured
operand-dependent input, rather than an independently predicted latency. The
architectural scenarios omit these RTL fetch/protocol costs and therefore model
a changed interface; their scalar scenario is not presented as the RTL baseline.

## Resource and energy rejection tests

`envelope.py` adapts the preserved scratchpad handoff helpers, replacing their
synthetic-dataset fixture counts with accepted full native-dataset address counts.
The nested 16 KiB/256 KiB address ranges share one 2 MiB image. Resident capacity
is `contexts × 2 MiB`; shared banking does not share mutable image bits. Static
hot-prefix placement charges the rest to external backing, plus unknown metadata,
ECC, queues, program/register state and physical macro overhead. Full local SRAM,
shared resident banking, static hot prefix with backing and full-image save/restore
are explicit alternatives. Dynamic cache/reconstruction/compression behavior is
unknown and receives no savings assumption.

Placement sweeps include bytecode accesses, two outer 64-byte reads and writes
per iteration, cold fill and final scan, 8/16/32/64-byte transfer granules and
optional partial-store RMW. They assume no reuse, combining or dynamic caching.
Dataset consumption is separate: 16,384 logical 64-byte requests/hash, or
1,048,576 bytes/hash and 1.048576 TB/s at 1 MH/s before extra physical traffic.
No extra transfer is automatically charged for a prefetch and its consumption.
Dataset and scratch latency sweeps use Little's-law necessary outstanding bounds;
`ready_per_context` is an assumption to validate, not a result from issue width.
Sustainable random bytes/s **and transactions/s**, bank timing/turnaround/refresh,
tail latency, queues and ports must all be checked against characterized supply.
Peak bandwidth and assumed random/peak efficiency are not measured service.

At 1 MH/s below 2,500 W the strict complete wall-energy ceiling is **2.5 mJ/hash**.
The pJ/bit entries are optimistic rejection ceilings assigning all wall energy
to scenario transfers, not memory-energy estimates. Compute and every remaining
term tighten them. `full_wall_power` requires compute, SRAM/dataset dynamic,
controller/PHY, fabric/clock, provider energy; logic/SRAM leakage, memory refresh,
VRM losses, fans/auxiliaries; PSU efficiency and AC auxiliaries. Missing terms
produce null power. Unexpected terms are rejected to prevent silently dropping
costs. Avoid double counting PHY energy already included in a memory term.

Reject correctness/order loss, capacity/independent-outstanding/bandwidth demand
above validated supply, throughput below 1 MH/s, or wall power **>=2,500 W**.
`rejection_gate` also requires separate transactions/s and bank-port operations/s
demand/supply bounds and `controller_service_constraints_satisfied`. The latter
must cover bank timing/conflicts, turnaround, refresh and tail latency for the
same traffic pattern and operating point; false rejects and missing stays unknown.
Bytes/s alone cannot satisfy these checks. Unknown required fields keep the gate
unresolved. Even complete hypothetical
inputs passing these necessary conditions are only conditional; they never prove
ASIC feasibility. Clock, process, SRAM macro area/access/leakage and physical
memory service/energy remain unknown. Generic cell counts do not establish them.

The next justified hardware experiment is a bounded context-tagged blocking
execution wrapper with independent scratchpad namespaces and explicit issue,
completion and memory-wait instrumentation, checked against native values and
the existing complete lifecycle. It tests actual context overlap before adopting
nonblocking queues or wider issue. It does not select a production engine count.
