# Independent wrapper-control evidence — 2026-10-08

These files preserve the independent reviewer controls from
[`GEM5-REVIEW.md`](../GEM5-REVIEW.md). **None establishes a gem5 Linux boot,
RV64 full-system execution, RandomX execution, timing calibration or power.**

| Evidence | Classification |
|---|---|
| `seven-tests.log` and metadata | Actual host execution of all seven wrapper unit tests |
| `fault_controls.py`, fixture and `recorded-faults/` | Ten synthetic wrapper cases; no gem5, guest Linux or RV64 code executed |
| `host-native-transfer-*` | Actual x86-64 host payload transfer and nine runtime checks; no guest boot |
| Resource/compressed-resource verification JSON | Actual independent file rehashes; no boot |
| `disk-inspection.json` | Read-only inspection of actual downloaded disk contents; no guest execution |
| `kconfig-source-audit.json` | In-memory source/Kconfig audit; no source/config-file write or build |

## Synthetic fault cases and complete logs

The helper gives `run.py` a disposable **host Python stub**, an invalid 40-byte
ELF-shaped payload and mocked resource verification. It replays the saved
runtime JSONL fixture; it does not execute that payload. The fixture is copied
from `../ci-runtime-qemu-runtime.jsonl`, whose actual QEMU provenance is
separately recorded in the parent validation package. Reusing its bytes here
creates only synthetic evidence for the wrapper.

`recorded-faults/results.json` retains the exact helper invocation, Python/host
versions, fixture/helper/stub and reviewed-source digests, each runner command,
observed exit/status and error. Expected outcomes are shown below and asserted
by the helper. Each case directory preserves
the complete captured runner stdout and stub stdout/stderr. The runner logs
carry an explicit synthetic label. Any embedded `boot_observed` or
`runtime_validated` field refers solely to **stub-supplied serial markers and
replayed JSONL**, never an executed guest.

| Case | Expected wrapper outcome |
|---|---|
| `baseline-synthetic` | Pass complete synthetic framing/oracles |
| `guest-exit` | Reject nonzero guest status |
| `guest-stderr` | Reject guest stderr |
| `truncated` | Reject incomplete framing |
| `missing-completion` | Reject absent final completion marker |
| `incomplete-events` | Reject missing hypercall 3 |
| `simulator-exit` | Reject nonzero host stub exit |
| `timeout` | Reject actual host subprocess timeout; retain completed replay validation |
| `later-hash-missing` | Reject missing requested hash stream; retain completed replay validation |
| `timeout-readfile-mutated` | Reject changed readfile before retaining partial replay validation |

All ten cases met these expectations. To reproduce from the repository root,
use a new output directory; the helper refuses to overwrite existing evidence:

```bash
python3 -m unittest discover -s tests -p test_gem5_fs.py -v
python3 docs/validation/m3-fs/review-controls-20261008/fault_controls.py \
  --output-dir build/gem5-review-replay-20261008
```

The two timeout cases spawn a sleeping host stub and exercise the real
process-group termination path. Default timeout is one second. Other cases
do not deliberately sleep. Resource verification is mocked only for this
wrapper test; separate retained rehashes validate actual downloaded inputs.

## Host-native transfer and retained inputs

Complete native transfer stdout/stderr and metadata are retained without the
generated base64 shell script or executable. The metadata binds the exact
native payload, generated-script identity, command and nine validated x86-64
oracles. Reconstruct the script with `run.guest_script` and the independently
compiled native payload described in [`RUNTIME-REVIEW.md`](../RUNTIME-REVIEW.md).
This proves the host shell transfer/framing mechanism, not Linux guest support.

No stub binaries, guest images, simulator binaries, generated transfer payloads
or caches are committed in this evidence directory. Source/library build and
actual simulator execution evidence remain separate acceptance requirements.
