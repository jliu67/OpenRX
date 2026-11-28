# Architecture audit snapshot — 2026-11-28

This publication-only snapshot supports the external audit tracked on
[issue #72](https://github.com/jliu67/OpenRX/issues/72). Engineering is paused.
**1 MH/s below 2,500 W wall, physical memory service, achieved full-hash residence,
silicon area and Fmax remain unvalidated.** No new scientific experiment was run
to prepare this snapshot; golden RTL, acceptance criteria and safeguards are unchanged.

| Evidence | Exact scope and disposition |
| --- | --- |
| [Unified model](../../tools/architecture/machine.py)¹ | Four immutable native v2 inputs; A in-order, B program-resident, C shared-resource and D tiered accounting. Latency and II, logical front and macro traffic, class-specific credits, physical-corner applicability and residence-driven engine/context costs stay separate. All 48 baseline wall powers are unknown. v1 coverage is the existing historical baseline, not new candidate equivalence. |
| [Capacity66 native output](evidence/capacity66/native.jsonl) | Two canonical hashes, exact inherited policy/event-hash parity. Static 1 MiB requires 9.84–10.79 TB/s versus 5.59–5.71 TB/s at 1.5 MiB, including dataset and partial-store RMW sensitivity at the target rate. Counts are source-order policies, not achieved service. Local macro accesses include fill/final; cache macro/refill/metadata traffic remains unknown where incomplete. |
| [Conditional frontier](capacity66/frontier.py) | 10.80/5.72 TB/s rounded design envelopes. Under assumed 100 ns usable backing child-response/ack and two credits/context, the retained B sensitivity requires 7,614/4,000 contexts and 7.44/5.86 GiB local data. These are necessary conditions, not schedules. Source-bound HBM2 timing/address/refresh/energy calibration remains incomplete; DQ peak is not sustained mixed payload. |
| [Service67 result](evidence/service67/result.json) | Twelve finite-window sensitivities, two native nonce windows and identical candidate resources. At assumed 100 ns, 1.5 MiB reduces batch cycles 16.8% early and 39.1% later, but capacity-weighted window residence is +30.14%/−0.74%. Parent-chain credits differ from capacity66 child-credit sensitivities. Neither capacity is selected. |
| [Isolation68 failure](evidence/isolation68/handoff.json) | Compile and VVP functional miter passed 12 native-result vectors, 192 corners and 209 accepted pairs. The collector rejected 88 initial idle X/Z transitions; zero binary transitions did not satisfy all-state stability. Both generic syntheses were unrun. Original status remains `FAILED_NO_RETRY`; no accepted switching/power benefit. |
| [Correction source](isolation68/correction01/) | Continuous conservative gate predicates and bounded known-state/history diagnostics. Source-only, uncompiled, unrun and unadmitted. Full miter coverage and all-state-zero criterion remain; no waiver or demonstrated fix. |
| [Reconciliation receipt](evidence/reconciliation/result.json) | Owner-authorized administrative recovery only. Exact failed marker and executed source were archived, fresh ownership/quiescence checked under the original lock, only that marker cleared and its parent fsynced. Seven durable journal stages are included. All failed evidence and `FAILED_NO_RETRY` remain; recovery authorizes no workload. |

¹ Model path from repository root: `tools/architecture/machine.py`.

## Ordinary reproduction

From a fresh checkout, using Python's standard library:

```sh
python3 -B -m unittest tests.test_machine_feasibility tests.test_audit_frontier tests.test_audit_snapshot
python3 -B -m experiments.audit_20261128.check_snapshot
python3 -B -m tools.architecture.machine --input tools/architecture/fixtures/machine-baseline.json --output /tmp/openrx-machine-audit.json --verify-sources
```

The output path must be fresh. These commands verify publication hashes, exact
native-count projections, retained capacity parity, lossless trace decoding,
conditional arithmetic and failure/recovery consistency. They do not execute a
native observer, HDL, scheduler, synthesis, recovery action or external tool.

## Provenance and limits

[PROVENANCE.json](PROVENANCE.json) binds each public file to its public byte count
and SHA256, plus the original hash where supplied. It distinguishes byte-exact
copies, sanitized copies, selected fields, lossless token pools and portable
path/import rebindings. Original unredacted records remain retained locally.
An original hash does **not** establish byte identity with a sanitized copy.

The two [native windows](evidence/windows/) reconstruct their complete original
bytes and hashes. They cover two carried iterations of program 0 and program 1,
not a complete hash, hardware arrival stream or population calibration. Published
source-order traffic, finite modeled schedules and physical measurements are
separate evidence classes. Published physical anchors retain their original
incompatible/unknown operating-point limits; no PVT corners are silently joined.

[Reference sources](reference/) expose the retained scheduler/service/recovery
logic for inspection. Host-specific entrypoints are disabled and private bindings
are redacted; they are **not** runnable launch/recovery recipes or fresh-clone
scientific reproduction claims. Native observer preparation also requires external
qualified assets not bundled here. No executable binaries, full runtime inventories,
credentials, machine identifiers or waveform dumps are included. Sanitized kernel
witnesses support cross-record consistency, not independent re-observation of the host.

The FP bench retains its original observed-output switching proxy, not internal
cell capacitance or a representative duty cycle. Shared recoders remain active.
No boundary toggle reduction can be converted to watts without a compatible
characterized implementation, activity model and full system overheads.
