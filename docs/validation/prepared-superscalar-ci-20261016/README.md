# Prepared superscalar hosted validation correction

This additive record explains the toolchain correction above draft PR #79 head
`b9283fde8d109cf2a3deafc6dec1fde2137aa9cd`. The original
[component evidence](../prepared-superscalar-20261016/README.md), source,
fixtures, receipts, failed attempts and generated models remain preserved.

The additive [package index](diagnosis/package-index.json) binds five portable
bundles: both failed hosted attempts, the two bounded probes and the conditional
toolchain proposal's data-only provenance. Each has an explicit selection and
complete original inventory; omitted bytes remain in the identified retained
originals. Typed path substitutions identify public derivatives separately from
raw receipt hashes. Host runner verification applies to the retained originals.
The package itself has acceptance false and grants no full scientific pass.

## Observed failure and bounded diagnosis

Hosted run `38969870368` on `0beab95f` failed the mapped cancel mode at its
1,800-second limit. Its ten RTL modes, native generation, synthesis and six
other mapped modes passed. Reducing concurrency to two workers in `b9283fde`
did not resolve the failure: run `38974202910` timed out both mapped reset and
cancel; the other five mapped modes and all ten RTL modes passed. Neither
failed attempt becomes a pass.

The exact retained hosted mapping contains 14,459 generic cells, including
1,387 synchronous state cells and no latches. The accepted local Yosys 0.9
mapping is distinct: 19,604 generic cells, 1,410 flops and no latches. Counts
describe tool-specific generic mappings, not physical area or PPA.

Verified bounded probe `20261016T231549Z-82a7c5e5e919` compared those retained
models using the same local Icarus, unchanged original bench and fixtures.
The local model reached the 8,192-clock cap in 13.38 seconds. The hosted model
hit its 60-second wall cap, with its last flushed checkpoint at 3,072 clocks
and 201 native-checked commits. All ten shared checkpoints match. At the
identical 3,072-clock checkpoint its sampled CPU cost was conservatively
6.97–10.18 times the local model's cost. The bounds account for asynchronous
sampling. This establishes substantial model execution cost without requiring
host contention to explain it; it does not exclude a later functional hang.

Probe `20261016T233427Z-f2e3247583c0` tested a separate ordinary-process-lowered
plain-DFF emission. Its actual 45 ports and 1,387 positive-edge state bits
passed structural guards. It also hit the 60-second cap, with only seven early
checkpoints recorded, last at clock 46. This last flushed value is a lower
bound, not an exact final time or proof of zero-time nontermination. The
candidate is rejected as a production cost fix. Neither probe is a complete
validation pass: both remain raw scientific-unverified, partial observations
with acceptance false. Their temporary observer and transformation are not
part of the production validation driver.

## Correction and acceptance boundary

The hosted job now keeps its Ubuntu 24.04 runner and uses an isolated official
Ubuntu 22.04 container pinned by OCI index digest. It downloads three exact
official packages, checks their SHA-256 values, and installs the package bytes:

| Package | Version |
| --- | --- |
| Yosys | `0.9-2` |
| Berkeley ABC | `1.01+20211229git48498af+dfsg-2` |
| Icarus | `11.0-1.1` |

Data-only inspection found all 200 regular payload files in these official
packages byte-identical to the installed reference packages. This supports
reproducing the completed local toolchain; it does not retroactively add
dependencies to an older receipt. Building the upstream Yosys 0.9 tag alone
would select a different bundled ABC revision and is not the same pin.

`scripts/check_superscalar_toolchain.py` fails closed on package versions,
resolved Yosys/ABC/Icarus/VVP binaries, 98 official Yosys source/model/map files
and 37 Icarus support files. Generated `__pycache__/*.pyc` under the Yosys share
directory is separately hash-recorded and excluded from equality; it is not
part of the official package payload. The native/RTL/mapped output artifact
keeps its original layout; a separate artifact retains the downloaded packages,
checksums and actual tool identity report.

All 178 original scientific source inputs remain byte-identical. The RTL,
oracle, native fixtures, four-state Icarus bench, ten RTL and seven mapped
modes, intermediate/native/transport assertions, two workers, 1,800-second
per-mode limit and 60-minute job limit remain unchanged. There is no production
normalization, simulator substitution, mode skip, timeout increase or new local
full-mode rerun. Focused file-identity and syntax checks support this correction;
new container setup and the new exact-head hosted results remain separate,
unproven gates until they actually pass.

The exact published head and independent review are recorded on
[draft PR #79](https://github.com/jliu67/OpenRX/pull/79). Do not merge under the
current parent direction. Program/table preparation, cache initialization and
memory service remain external. No new full hash, physical ASIC/PPA result or
architecture selection follows.
