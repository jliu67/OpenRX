# Task #72 focused recovery

Recovery starts from preserved clean head
`46fa0737f0e818c9147a687613d38aedd6b0cf0d`, tree
`1059a182633f9dd82fa5aa67eaee5840b8906187`, above main
`f13e5b5223e87c91a848adedc23502b5a42d4754`. It uses a separate temporary
feature branch. The original author workspace, run01/run02/run03 outputs,
sources, builds, data, failures and checkpoints remain preserved.

Only two review blockers change:

- Actual full-evidence SHA-256 and all 12 portable fixture-file digests must
  match trusted bindings independent of embedded hash claims. Changed timing,
  counts, native/trace bytes, missing/extra files and source-map rehashing cannot
  retain accepted attribution. `reproduce` preserves untrusted provenance and
  stops before replay/comparisons. Location-dependent extraction metadata also
  changes byte identity; it remains untrusted until new bindings are reviewed.
- Conditional passes now require transaction-rate and bank-port demand/supply
  plus controller-service constraints for the same traffic and operating point.
  Those constraints cover timing/conflicts, turnaround, refresh and latency
  tails. Missing fields stay unresolved; failed/insufficient service rejects.

The trusted full-evidence binding remains
`33f4cbe95805d33068fa9eceee90820f230cd0457d06f35407f9323d1d547ecf`.
All fixture bytes match saved `46fa0737`; no fixture or original result is edited.

## Focused checks

`unit-tests.log` records all 67 architecture tests passing. These include seven
new input-identity tests and the tightened gate tests. `focused-review.json`
records a separate read-only review of both fixes, 16 independently run focused
tests and verification of all trusted input bindings. This is a focused source
review, with the final exact-head handoff requesting review of the complete PR.

The serial admitted compact check is execution
`20261016T065700Z-fe5c0263613b`, using the unchanged installed runner SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`.
`checks.json` records numerical reproduction and exact source hashes.
`execution.json` records the receipt verification and observed resource limits.
One Python worker is used for this bounded deterministic replay; all six host
CPUs remain available under the verified 600% ceiling, with 1 GiB RAM, 2 GiB
swap and Tasks256. No full-trace scan, native build, dataset generation, RTL or
hash simulation is repeated.
The check completes in 217.60 seconds with child peak RSS 32,244 KiB. During-run
cgroup samples showed no CPU throttle or memory limit/OOM event; final cgroup
peak and whole-host utilization are not measured here. Receipt integrity verifies
and process exit is zero; the runner's generic scientific-acceptance flag remains
unverified, while the explicit focused assertions in `checks.json` pass.

All 488 scheduling rows and eight scalar-calibration equations retain their
original bytes. `sensitivity.json` differs only in three additional gate
unknowns. `provenance.json` verifies actual input identity. Comparison and scalar
artifacts remain in the parent directory; recovery artifacts are additive and
their digests appear in `artifacts.sha256.json`.

Reproduce with the commands in the [model contract](../../../../tools/architecture/README.md).
The old 58-test record and original artifact index remain historical evidence.
The full accepted run remains source `c96e96ab`: 40,975,538 hardware/transport
clocks, with measured unpredicted executor aggregate 39,946,977. Host input hash,
fill, program and dataset generation remain untimed. Neither 488 analytical
rows nor eight bounded equations validate alternative full-hash performance.
Physical inputs and the complete target remain unresolved. No ASIC feasibility,
architecture selection or merge is claimed.
