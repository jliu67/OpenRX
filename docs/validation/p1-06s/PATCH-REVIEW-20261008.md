# Independent P1-06S software acceptance review

Date: 2026-10-08 UTC / Edmonton. Task: [#13](https://github.com/jliu67/OpenRandomX/issues/13).
Reviewer: separate `power_patch_review` agent; application/test author: `power_review`.

**Verdict: accept the repaired P1-06S software package. No remaining software blocker was found in this review.** This accepts the offline importer and its documented conditional calculations; it does not accept a physical experiment, meter, calibrated host, measured efficiency result, or M1 completion.

The reviewed local snapshot is `3f06f87b970cd1f8fc06f06dff9e9aa06cb5aad4`, supplied for review as a snapshot of remote `bac3a069`. The historical importer bytes have SHA-256 `91f51352e98699c3fef9f0a8805d6946a780aa6218445928aa9c7304d34dd2e6`. The verdict is pinned to these repaired file digests:

| Reviewed file | SHA-256 |
|---|---|
| `scripts/power_import.py` | `612d20c6e4b3cae80be1231d0c41c5ece29ece23a286f347482adf23f35cfbf7` |
| `tests/test_power_import.py` | `91ea2a5806a9235823caacc6cb97f69c456e504999bbf6e0feab8c505ead81d8` |

## Defects and repair assessment

The original importer crashed without writing `energy-report.json` for three classes of malformed input. The author retained original/fixed CLI reproductions in [independent-audit-20261008.json](independent-audit-20261008.json). I inspected and replayed that audit and independently exercised the fixed CLI.

| Reproduced defect | Repair | Review finding |
|---|---|---|
| Nonstring saved `configuration.versions`, including null/array, reaches `.split()` and raises uncaught `AttributeError` | Require an actual string before splitting | Correct format validation; legitimate version strings retain existing command/stream checks |
| JSON rate correction `1e1000000` reaches context-sensitive Decimal `abs()` and raises `decimal.Overflow` | Exact `Decimal.copy_abs()` followed by existing finite/precision/range cap | Rejects the value before rational conversion; preserves signed mapping and legitimate inputs |
| Unrepresentable JSON exponent such as `1e999999999999999999999` raises `decimal.InvalidOperation` during parsing | Translate `DecimalException` from JSON decoding into a validation `ValueError` | Narrow to decoding; writes a failed evidence report rather than suppressing an arithmetic or integration defect |

The integration, uncertainty model, metric bounds, synthetic/measured field routing, source-validator identity checks, and original file preservation are unchanged. The repairs do not add blanket exception handling around analysis or accept malformed input. Regression tests drive the actual CLI, inspect failed report status/null efficiency, and compare every copied input byte with its source. The new cases therefore verify the public failure contract, not just a helper's implementation.

## Independently executed checks

Environment: Python **3.12.14**, Linux container. Every power trace in this review is synthetic. No native RandomX execution or physical meter was performed by this reviewer.

| Check | Observed result | Retained evidence |
|---|---|---|
| Importer regression suite | **64 tests passed**, no skips | [patch-review-tests-20261008.log](patch-review-tests-20261008.log) |
| Separately authored type/metadata probes | **327 rejected inputs** return 1, preserve bytes, write failed report, and retain null efficiency; no uncaught error | [patch_review.py](patch_review.py), [patch-review-20261008.json](patch-review-20261008.json) |
| Additional Decimal probes | **13 rejected cases**, including both signs, cap overshoot, 19 fractional digits, and huge positive/negative exponents | Same separate review script/report |
| Valid-input compatibility | **10 accepted reports match the historical importer exactly except importer digest** | Same separate review script/report |
| Replayed author's mathematical audit | **500 exact spline integrations, 8,000 conditional perturbed-waveform cases, 500 outward-serialization checks, 24 affine linear-trace intervals passed** | [independent_audit.py](independent_audit.py), [patch-review-math-20261008.json](patch-review-math-20261008.json) |
| Whitespace/diff check for repaired application/tests | Passed | `git diff --check -- scripts/power_import.py tests/test_power_import.py` |

The compatibility cases include ±10000 ppm, both signs of an 18-place fractional correction, ±1e-18 ppm, negative zero, zero with a large positive exponent, and 18-place power readings. They preserve the existing rate sign, rational timestamps, energy, bounds, summary totals, and synthetic safeguards. Complete serialized analysis reports were compared, rather than only success codes or rounded energy values.

The mathematical audit uses a global hinge-spline primitive as an oracle, distinct from the importer's clipped segment trapezoids. Its deterministic seed is `2026100813`. Signed affine checks use nonconstant traces, which expose rate-sign mistakes that constant-power tests would conceal. These synthetic cases support software correctness; their finite perturbation set is not a proof of every physical waveform or of meter calibration.

An initial reviewer probe incorrectly expected an empty `boundary.excludes` list to fail. The documented schema permits it. The probe was corrected to omit that valid case; no production change was requested or made. This was a review-script assertion error, not an importer defect.

## Reproduce

From the repository root:

```bash
python3 -m unittest discover -s tests -p test_power_import.py -v
python3 docs/validation/p1-06s/patch_review.py --baseline bac3a069
python3 docs/validation/p1-06s/independent_audit.py --baseline bac3a069
git diff --check -- scripts/power_import.py tests/test_power_import.py
```

The actual local commands for the saved reports used `--baseline 3f06f87b970cd1f8fc06f06dff9e9aa06cb5aad4` for `patch_review.py` and `--baseline HEAD` for `independent_audit.py` while HEAD was that unchanged snapshot. The remote historical commit was not present in this local snapshot's Git object database. The review report records baseline and current file digests; use a historical revision with the baseline importer digest above when reproducing elsewhere. Output destinations were the linked JSON/log files. Scripts write only temporary synthetic inputs while executing their checks.

## Remaining project gates

Task #13 may close after the exact reviewed repair/evidence package is integrated and required repository checks pass. Task #10 still needs a real meter, explicit acquisition/clock calibration evidence, justified response/interpolation bounds, and physical validation. Task #8 still needs a controlled host; #11 still needs dynamic counters/profiling. Parent M1/#1 remains incomplete. Operator-declared measured input remains explicitly uncertified; hashes/J from the retained fixtures are synthetic calculations only.
