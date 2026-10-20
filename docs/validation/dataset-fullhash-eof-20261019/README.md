# Native dataset gold EOF validation

## Later full-result acceptance — 2026-10-20

After the bounded repair and corrected-model preparation below, one complete
default 8×2,048 functional hardware-dataset hash is
[independently accepted](https://github.com/jliu67/OpenRX/pull/86#pullrequestreview-5588318967)
at public `e8277c6`/tree `cb3e0615`. The
[result summary](../dataset-fullhash-20261020/README.md) records complete native
assertions and actual nested phase closure. Original failures, raw scientific
flags, acceptance criteria and prepared host-service boundaries remain unchanged.

## Retained bounded EOF method — 2026-10-19

The full hardware-dataset testbench must consume every required native row and
reject additional data. A scanner return value alone cannot distinguish valid
EOF from malformed trailing input consistently across the supported simulators.

The EOF task checks the descriptor, reads each remaining byte as a signed integer,
permits only ASCII whitespace, and requires a confirmed EOF. The pinned Verilator
backend needs a null-safe empty-format scan before seeking because its seek
implementation can dereference a closed handle. Icarus uses its safe seek check
directly; its empty-format scanner has different EOF behavior. The common byte
loop rejects extra complete or partial rows, malformed suffixes and binary data.

The focused regression extracts the exact production file-reading tasks into a
tiny top and exercises valid endings, extra or malformed input, missing or
truncated rows, and invalid descriptors on both backends. An optional extracted
historical footer demonstrates the prior EOF convention mismatch. Synthetic
fixture value checks do not claim a new strict lexical parser. Existing
per-demand address/data comparisons and full-result checks remain unchanged.

## Retained reference and corrected model

The prepare-only reference-reuse option verifies externally pinned original gold,
its successful command ledger, receipt, integrity record, native executable and
source-extraction provenance. It copies the gold byte-for-byte into fresh output
and compiles the corrected model without regenerating the native reference.

Only the explicit validation-file changes and new EOF regression script may
differ from the original preparation dependency inventory. Every other changed,
added or missing dependency is rejected. A distinct rebuilt-model manifest binds
the current exact source tree, actual commands and new simulator; the original
model cannot be relabeled as rebuilt. Ordinary prepared-input checks stay strict.

The EOF regression and prepare-only result establish bounded validation and model
readiness. They do not complete a hardware-dataset full hash. Earlier failures
retain their original status. Full acceptance still requires a fresh admitted
full run, all native comparisons and scratchpad boundaries, the canonical digest,
complete nested clock ledgers, zero live software-provider callbacks and
independent review. Retained preparation and modeled host memory services remain
explicit; simulated clocks do not establish physical PPA or architecture selection.
