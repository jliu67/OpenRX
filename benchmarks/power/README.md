# P1-06S: offline whole-system power import

Task: [#13](https://github.com/jliu67/OpenRandomX/issues/13). This is **analysis software**, not a meter driver or a completed Phase 1 experiment. It joins operator-supplied point-power samples to saved P1-05 intervals without changing RandomX, the native adapter, the old benchmark runner, or system settings.

## Run it

```bash
python3 scripts/power_import.py \
  --run-dir benchmarks/results/YOUR-STEADY-RUN \
  --power YOUR-POWER-TRACE.json \
  --output-dir benchmarks/results/YOUR-NEW-ENERGY-REPORT
```

The output directory must not already exist. The command copies `run.json`, `adapter.jsonl`, `adapter.stderr`, and the supplied trace as `power.json`, then writes `energy-report.json`. Input bytes, digests, validator/importer digests, invocation and Python version are retained. A validation failure returns 1, preserves readable inputs and an error report, and produces no usable efficiency result. Bad CLI arguments/existing output return 2. Oversized inputs are rejected without copying a truncated file; originals remain untouched. No original input is rewritten.

Before joining power, the importer checks successful run/integrity status, source-validator identity, binary digest, raw checksums, empty stderr, command configuration, the full native stream, known controls, repeat consistency and the saved summary. It refuses failed/too-short/incomplete trials. Only `phase=measurement` intervals enter energy totals. Initialization, controls, warmups and inter-trial gaps are excluded. Hash correctness is exactly the existing adapter's controls and aggregate checks, **not new independent per-hash verification**. A long trial without a published expected aggregate still has that limitation.

### Executable synthetic demonstration

This creates test data, **not a benchmark or real power measurement**. Run from the repository root in a new scratch directory:

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'tests')
from test_power_import import fixture
out = Path('/tmp/openrx-power-SYNTHETIC-input')
out.mkdir(exist_ok=False)
for name, data in fixture().items():
    (out / name).write_bytes(data)
PY
python3 scripts/power_import.py \
  --run-dir /tmp/openrx-power-SYNTHETIC-input \
  --power /tmp/openrx-power-SYNTHETIC-input/power.json \
  --output-dir /tmp/openrx-power-SYNTHETIC-output --allow-synthetic
python3 -m unittest discover -s tests -p test_power_import.py -v
```

Either synthetic input makes the whole join synthetic. This requires `--allow-synthetic`; results use `synthetic_metrics` / `synthetic_totals`, while measured interval energy/efficiency fields stay null. An explicitly synthetic benchmark cannot be reclassified by changing only the power file. Tests also exercise the declared-measured output branch with constructed data; **all test fixtures remain synthetic regardless of the branch being tested**.

For operator-declared measured inputs, interval `measurement_metrics` and per-version `measurement_totals` are calculations from the supplied readings. `meter_evidence_independently_verified` and `baseline_accepted` always remain false. No JSON label proves that a physical meter exists, that its calibration is valid, or that the benchmark host was controlled. Top-level power/efficiency remain null rather than mixing versions or synthetic/physical interpretations.

## Strict input schema, version 1

The generated demonstration above is a complete machine-readable example. Do not reuse its calibration assumptions for real hardware. All listed fields are required; unrecognized power-metadata/sample fields fail rather than silently accepting a misspelling.

| Field | Required meaning |
|---|---|
| `schema_version` | Integer `1`, not a Boolean |
| `evidence_class`, `benchmark_evidence` | Each `synthetic` or `measured`; separate trace and benchmark declarations |
| `binding` | `adapter_sha256` and `run_sha256`, SHA-256 of the exact saved input bytes |
| `device` | Nonempty `id`, `model`, `calibration_reference`; `max_watts` is the maximum admissible indicated reading |
| `boundary` | `kind=whole_system_ac`, description, nonempty `includes` array and `excludes` array; identify PSU, cooling and peripherals explicitly |
| `units` | Exactly `{ "time": "ns", "power": "W" }`; no guessed conversions |
| `sample_semantics` | Exactly `instantaneous_active_power`: point estimates of active power at effective acquisition timestamps, after any validated response correction |
| `samples` | Ordered objects `{ "time_ns": INTEGER, "watts": NUMBER, "status": "ok" }` |
| `synchronization` | The mapping, bounds, validity and evidence below |
| `uncertainty` | Absolute/relative meter error, interpolation error, boundary uncertainty and justification below |
| `policy` | Explicit gap, clock and relative energy-error limits below |

This version deliberately rejects CPU-package telemetry, board-DC or idle-subtracted data, apparent power/VA, watt-hours/cumulative counters and interval-averaged meter exports. An averaging meter needs a separately justified format conversion/response model with a defensible interpolation bound, or a future interval-energy importer; **do not merely rename its fields**. No CSV/device-specific parser is implemented. Preserve the original meter export and calibration/synchronization evidence alongside the canonical JSON.

Times are nonnegative signed-64-bit integer nanoseconds; floats, strings and Booleans are rejected. Numeric power/error fields are finite JSON numbers, at most 18 fractional decimal places and within documented caps. JSON powers are decoded through Decimal then Fraction to avoid epoch-scale floating-point timestamp loss. Power must lie between zero and `device.max_watts`, which is positive and at most 1e9 W. Each input file is limited to 32 MiB; 2–200,000 power samples are allowed. These are defensive format limits, not recommended physical measurement ranges. NaN/Infinity, repeated keys, missing readings, clipped/error flags, duplicate/reversed timestamps and unsupported schema variants fail.

## Clock mapping and rejection

`synchronization` requires:

- `method=affine_to_monotonic`, `source_clock` identifying the actual device/clock instance and `target_clock=CLOCK_MONOTONIC` on the **same host boot** as the bound benchmark; `evidence_reference` identifies the alignment/calibration record.
- Integer `source_anchor_ns`, `target_anchor_ns`, `valid_from_ns`, `valid_to_ns`; anchor and every sample must be within the source-clock validity interval.
- Signed `rate_correction_ppm` in [-10000, 10000], and nonnegative `drift_bound_ppm` at most 10000. The correction is nominal; drift is the residual error bound after correction.
- Nonnegative integer `offset_bound_ns`, `timestamp_bound_ns`, `response_bound_ns`, expressed in **target-clock nanoseconds**. Response uncertainty includes remaining acquisition/averaging/transport latency after the externally established correction. Do not use arrival time as acquisition time without such evidence.

For source timestamp `s`, the nominal target timestamp is

```
t(s) = target_anchor_ns + (s - source_anchor_ns) * (1 + rate_correction_ppm / 1e6)
U = offset_bound_ns + timestamp_bound_ns + response_bound_ns
    + max(abs(s - source_anchor_ns)) * drift_bound_ppm / 1e6
```

Arithmetic remains rational until report serialization. No synchronization is inferred from coincident wall-clock labels. `policy.max_clock_uncertainty_ns` bounds U. Sample ordering must remain unambiguous: smallest mapped gap > 2U. Largest mapped gap + 2U must not exceed `policy.max_gap_ns`. This conservative policy checks the entire supplied trace, even between measured trials; split or justify discontinuous acquisitions rather than interpolate across a dropout.

The benchmark boundary uncertainty B is `uncertainty.benchmark_boundary_bound_ns`, positive and at least the reported monotonic resolution. Resolution is **not accuracy**; use a larger justified bound where needed. Coverage must include every measurement window expanded on both sides by U+B; no extrapolation or automatic gap filling occurs.

All recorded realtime-minus-monotonic midpoint offsets, including between trials, are checked: their range plus the widest bracket must not exceed `policy.max_wall_offset_change_ns`. This is an additional conservative step/slew/bracket diagnostic, not proof that an unobserved clock excursion did not happen. Linux monotonic time is boot-specific, affected by frequency correction, and excludes suspend; realtime can jump. A suspend, clock reset, calibration discontinuity or host mismatch invalidates a single affine mapping unless separately established otherwise. Those physical facts cannot be certified from metadata alone.

## Energy and conditional error bound

For each accepted interval `[start.mono_after_ns, end.mono_before_ns]`, the importer clips the first/last sample segments to the exact interval and integrates the piecewise-linear trace using timestamp-weighted trapezoids. It does not average sample values without time weights. With duration T in seconds and nominal integral E in joules, define:

- A = `absolute_watts`, r = `relative_fraction` (0..1), I = `interpolation_bound_watts`.
- Meter error at a sample is assumed bounded by A + r*P, where P is its **indicated** power.
- I bounds the residual between true power and the linear interpolation through true sample values at true acquisition times. It includes unresolved waveform/response/aliasing effects; it is **not inferred from the gap threshold or repeat scatter**.
- L is the maximum slope of the nominal reconstructed trace in W/ns, U is as above, B is the benchmark boundary bound, and Pmax is `device.max_watts`.

The implementation uses the conservative sum

```
error_J = (r*E + A*T) + I*T + (1+r)*L*U*T
          + (2*B/1e9) * ((1+r)*Pmax + A + I)
```

Explanation: monotone uncertain sample knots within U induce a piecewise-linear time warp no farther than U from the nominal time axis; its indicated-power discrepancy is bounded by L*U. Relative meter error also applies to that shifted indication, giving the factor (1+r). The last term bounds both uncertain interval edges using the largest true-power envelope allowed by the indicated range and error assumptions. The expanded coverage and ordering checks are prerequisites. This is a **conditional deterministic envelope**, not a statistically inferred confidence interval or a universal physical guarantee. Unsupported response/aliasing assumptions invalidate it.

`uncertainty.rationale` must identify the source and validity of these bounds. Measured inputs require nonzero meter uncertainty and a positive interpolation bound. `policy.max_relative_energy_error` must be in (0, 0.5]. Reject zero energy, a nonpositive lower energy bound, or an error/E above that limit. Output bounds are rounded outward; reported absolute error also includes rounding of the energy estimate.

Efficiency is completed hashes/E, with reciprocal bounds from E±error. Per-version summaries use **sum(hashes)/sum(E)**, not the average of trial ratios. Error bounds are summed across trials, so a shared calibration bias does not disappear with more repetitions. Configuration comparisons still require the fixed-host settings, adequate duration, warmup, even repetitions and independent evidence gates in EXP-001.

## Review and physical acceptance

Inspect the schema, conditional bound and failure tests before accepting task #13. Real-host repeatability, meter bandwidth/calibration, acquisition timing, clock alignment evidence and benchmark isolation belong to #8/#10. Dynamic bottleneck attribution remains #11. A passing importer test does not complete M1. No meter was accessed, hardware purchased, paid compute provisioned, or network mining performed by this implementation.

Primary implementation references checked 2026-10-08 UTC: [Linux timekeeping](https://docs.kernel.org/core-api/timekeeping.html), [Python JSON decoding/security](https://docs.python.org/3/library/json.html), [exact rational arithmetic](https://docs.python.org/3/library/fractions.html). The integration/error model above is a project-defined conditional calculation; these documentation links do not independently validate a physical meter or endorse the model.
