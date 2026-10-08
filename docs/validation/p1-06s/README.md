# P1-06S validation and handoff

Date: 2026-10-08 UTC / 2026-10-07 Edmonton. Task [#13](https://github.com/jliu67/OpenRandomX/issues/13); agent/session `chatgpt/20261008-p106s`. Reviewed base `7b7ec36a37035bde56db487288a48e122516959f`. Application/test implementation: **`2b28d6fb4604a2b861241d38678e24c8541aed02`**, developed on `openrx/p1-06s-power-import`. This documentation/evidence package does not change those tested application or test bytes.

## Delivered and scope

`/scripts/power_import.py` validates the saved steady run, raw digests and source-validator version; binds a strict whole-system AC point-power trace to that run; validates explicit time mapping, uncertainty, sample order, gaps, coverage and clock diagnostics; integrates clipped timestamp-weighted energy with conditional worst-case error bounds. It preserves input snapshots/failures and prevents synthetic inputs from filling measured efficiency fields. See [full protocol and limitations](../../../benchmarks/power/README.md).

The native adapter, upstream runner, vendor/randomx, simulator, RTL and decentralized communication implementation were not modified. No devices, paid services or external agents were provisioned. **No real power samples, controlled CPU performance matrix, dynamic profile or hardware efficiency result was obtained.**

## Checks actually executed

| Check | Evidence / observed outcome |
|---|---|
| New local regression suite | **61 passed**, no skips; Python 3.13.5; [local-tests.log](local-tests.log) |
| Local source identity | Importer Git blob `756d18b9cda2ab5c6429bd96b24c51c951e9b0c2`; test blob `0dab53b56df3f94152808fd87e10845c0ab668e2`; both matched connector-read committed blobs |
| Existing validator identity | Local read-only copy matched Git blob `9f3c3b1d15f39cc0da4cc3f50bbd0d0c193a1f6d` / SHA-256 `c1aded35e291cddb9207210410ae0ba8916c1beba7dc3438e7a112aa63177d49` |
| Actual combined CI | [Run 37726645625](https://github.com/jliu67/OpenRandomX/actions/runs/37726645625), job `113146214930`, all steps succeeded on the implementation commit |
| Python suites in CI | **182 passed**, no skips (121 existing + 61 new; count read from actual log) |
| Upstream RandomX suite | **107 passed**, no skips, read from artifact log |
| Native steady suite | **6 passed**, no skips, including the expected duration-rejection case |
| Other integration gates | Source integrity, static profile, native builds and prior smoke/full-dataset controls all passed |
| Saved native inputs + synthetic power | Three successful native runs accepted, **12 measurement intervals** checked against exact constant-trace integrals; duration-rejected run refused; measured fields remained null |

Local suite execution tested validation, numerical calculations and temporary-file CLI behavior; **it did not execute RandomX natively**. Native execution occurred in the existing GitHub Actions workflow. The new fixture tests construct both the synthetic-output branch and the operator-declared-measured branch, but all those fixture data remain synthetic. Counts from different test suites are not new architectural evidence.

## Downloaded and inspected CI evidence

[Artifact 11528236706](https://github.com/jliu67/OpenRandomX/actions/runs/37726645625/artifacts/11528236706): **68,046 bytes**. Independently calculated ZIP SHA-256:

`1eacda6564e038bc5933b04bc5030b20b5373b629551e801a64e6bed946a6358`

It matched the GitHub-reported digest. The Python, upstream and native test logs were read. Every saved native run identified implementation commit `2b28d6f`. Raw stream/stderr digests were checked by the importer. The known controls/completeness of successful runs were revalidated before joining generated synthetic power. The failed run was rejected before any energy result was produced.

[ci-checks.json](ci-checks.json) records the artifact identity, log hashes, observed counts, raw-input digests and acceptance/rejection outcomes. This audit was first exercised on the prior P1-05 integration artifact and then repeated on this implementation's new artifact. The latter is authoritative for the reported 182/107/6 counts. No artifact rates are promoted to real performance/energy results.

GitHub reports expiration **2027-01-06T04:15:51Z**. The digest ledger does not replace raw evidence: retain the archive and referenced physical evidence before relying on it beyond retention. [reproduce.py](reproduce.py) recreates the canonical synthetic trace bytes and audit ledger from that exact archive, saving native inputs, synthetic power and computed reports in a new directory. It reads saved data only; it does not run a native benchmark or contact a meter.

```bash
python3 -m unittest discover -s tests -p test_power_import.py -v
python3 docs/validation/p1-06s/reproduce.py /path/to/correctness-logs.zip \
  --output-dir /tmp/openrx-p106s-reproduced
```

The checked archive must have the SHA-256 above. The reproduction script was actually executed locally and its ledger matched `ci-checks.json` byte-for-byte. Python compilation checks passed. The full CI job/build log was not downloaded; job/step completion and the named artifact contents were inspected, so this record does not assert that every build warning was independently reviewed.

## Preserved audit error and limitations

An initial local log-audit assertion searched for the word `skipped` anywhere and falsely matched `test_pull_requests_skipped ... ok` in the existing router suite. This was an **audit-script false positive, not a failing or skipped CI test**. It was corrected to match outcome positions; all suite summaries and individual outcome lines then passed. The committed reproduction script contains that correction. No production importer/test code was changed to hide a failure.

Uncertainty bounds are operator-supplied physical assumptions, not a certification service or confidence interval. There is no generic CSV, interval-average meter, accumulated-energy counter, meter driver or automatic clock calibration. Whole-system AC point-power import is the deliberate v1 scope. Physical acceptance must verify model/response limits, source/host clock identity, calibration records, unsampled excursions and valid host measurements. The code cannot detect forged declarations or prove physical provenance from SHA-256 alone.

**Implementation and software validation are complete; independent task review is requested on #13.** Inspect the conditional error model and physical-input contract before closing it as completed. Parent M1 #1 remains open, #8 still needs a controlled host, #10 needs meter/synchronization access and prerequisite acceptance, and #11 needs host counters. Do not reimplement the importer or claim Phase 1 completion from a green test run.
