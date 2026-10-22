# Finite-fabric service-profile validation — 2026-10-22

Execution `20261022T023803Z-dd124df0248e` completed the separately approved
[issue #72 plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6331310442),
under its [matching claim](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6331297362).
All three analytical commands returned zero without timeout. Separate independent
review accepts **`PASS_ANALYTICAL_COMPONENT_REPORT_ONLY`**, with no findings.
[EXP-026](../../../experiments/EXP-026-finite-fabric-service-profile.md) gives the
scientific interpretation. Publication-head review and applicable exact-head
checks remain future gates; broader issue #72 remains open.

## Portable public records

| File | Meaning |
| --- | --- |
| [finite-fabric-service-profile.json](finite-fabric-service-profile.json) | Exact emitted source-bound logical component report |
| [provenance.json](provenance.json) | Exact emitted accepted-input identity record |
| [artifacts.sha256.json](artifacts.sha256.json) | Exact emitted report/provenance digest index |
| [source-bindings.json](source-bindings.json) | Portable executed 59-file map and source/driver pins |
| [public-summary.json](public-summary.json) | Sanitized execution outcome, command timing/RSS and scientific limits |
| [verification-summary.json](verification-summary.json) | Sanitized integrity, receipt and unchanged-byte checks |
| [independent-result-review.json](independent-result-review.json) | Separate bounded analytical result acceptance |

The complete raw execution, command stdout/stderr/GNU time logs, runner records,
receipt and root integrity proof remain retained privately. The receipt binds
26 artifacts. These portable summaries do not publish raw private journals or
duplicate the 22 already published recovery inputs. Original prepared `UNRUN`
metadata remains preserved privately; later actual execution and review are
recorded separately here.

## Source and accepted-input identity

The accepted component source is [PR89](https://github.com/jliu67/OpenRX/pull/89),
head `f495a34fc8a67f69b7f3e407cc4b509b96b84d64`, tree
`d4455f073c858c7df5bd4d2ea7373fa52650df56`, normal merge
`b6e71b467bc3c51e1c6734853a08b11412c8653a`, accepted by its
[independent final-head review](https://github.com/jliu67/OpenRX/pull/89#pullrequestreview-5607170870).
The registry checks 22 actual public JSON inputs totaling 145,352 bytes, accepted
recovery source/tool identities and explicit logical port widths. Embedded hash
claims alone cannot establish accepted identity. The recovery source-bindings
publication parent remains historical and is not rewritten to the accepted head.
Existing [recovery records](../shared-dataset-fabric-20261021/README.md) preserve
the original failed mapping and accepted prefix/matrix/mapped parity separately.

| Binding | SHA-256 |
| --- | --- |
| Prepared 59-file source manifest | `bdf9150ebe1366f70f1eaea54932e7e948aa0cb30e1b46b3ec5192d2f4016c65` |
| `tools/architecture/finite_fabric.py` | `e6666fc9c5e92410507a57d378f1b38982cb2508845e9e52ad3728f90bf2a152` |
| Registry | `b8cc39f65341320c18adb64ab2b2ea05db262938de6de5aca91add7d69ed9828` |
| `tests/test_architecture_finite_fabric.py` | `eb4298b316935466e9a2c66942d886b72678f49d5bbfcb2f7eda920e34f5f414` |
| Validation driver | `dec0c338c0a8a8fb35fa1b1c0098b10483d35af4c13fea56e6958e668f6e6c4e` |
| Receipt | `c559b9c620d9a4c12250b72f9a3d98a9214a94147cb26640e2a93885ebfd32c9` |
| Root integrity postcheck | `60c1f7a8ed1d38dc2da3eddcfaed8b7ec656d9e70c780f54fa12365da6c10837` |
| Independent result review | `f48ec328b04e494db02cf2fe0a46b736bf4a0df7f982f62637b7a0912193fb16` |
| Emitted report | `d6baa3de036273b1ac3918ffb5c3418b98f0130acdb43652380c06648eea81ce` |
| Emitted provenance | `f6a545471c0fd19001290e8be4c2e592027d27d97bf8031c9a99ab63d780a37d` |

Root's integrity postcheck reports all 68 frozen files and tool pins unchanged,
including the complete 59-file prepared source manifest. The three new source
files remain exact executed bytes. Later publication documentation does not
change those scientific source/input bindings.

## Actual commands and resources

| Sequential command | Actual outcome | Driver wall seconds | GNU time max RSS KiB |
| --- | --- | ---: | ---: |
| Architecture unittest discovery (`test_architecture*.py`) | 98 methods OK: 86 retained + 12 new; no failures/errors/skips | 2.075045420 | 32,168 |
| `tools.architecture.finite_fabric` with accepted registry | rc0; report/provenance/index emitted | 0.114317417 | 16,888 |
| Unchanged `tools.architecture.hardware_dataset` with accepted v2 fixture | rc0; both PR87 JSON gold files byte-exact | 0.064191188 | 16,172 |

Combined driver-measured command wall time was 2.253554025 seconds. The unittest
footer reports `Ran 98 tests in 1.571s; OK`; this differs from the containing
command's driver wall interval. GNU time RSS values are per-command process
observations, not aggregate/cgroup peak memory. No post-run cgroup peak is claimed.
These host validation durations do not measure chip latency or RandomX throughput.

Actual prelaunch kernel checks enforced one sequential worker/global slot,
CPU600% with a six-CPU allowance, RAM 1,073,741,824 bytes (1 GiB), swap
2,147,483,648 bytes (2 GiB), Tasks256 and 120 seconds plus five seconds supervisory
shutdown grace per command. Limits are admission constraints, not measured
physical resource requirements. No timeout or scope increase occurred.

The old [PR87](https://github.com/jliu67/OpenRX/pull/87) output bindings are unchanged:
`service-demand.json` SHA256
`694b153e2220218c95c84579dfba930707abb439fa1cadce4d42195148f7c42a`
and `provenance.json` SHA256
`3d1a7b0ea16c570b3b7ddbe4a31469e48c95dcd6bb6221d9f6b040a97895c753`.
The historical scheduler reproduction was not repeated because its source,
fixture and gold were unchanged. No native/cache generation, RTL simulation,
synthesis or full hash was launched by this analytical validation.

## Separate result acceptance and limits

The independent review checked actual logs, accepted input bytes, report
arithmetic, source/tool bindings, receipt/root proof and unchanged PR74/PR87
domains. It accepts correct byte/source-bound logical reporting only. The
report's `accepted_bounded_component_transport_observations` classification
attributes retained PR89 input observations; it is distinct from this new
execution's independent review decision. Raw runner `unverified` and driver
`unverified_pending_independent_review` remain exact original fields.

Fetch descriptors are 93 request/255 response bits; cache descriptors are
106/619 bits, excluding handshake/cancel/diagnostic wires. Ideal serial/concurrent
batch clocks are 113,953/61,595; stalled clocks are 149,685/83,537. Keep these
bounded two-item fractions separate from full-hash timing. Owner-credit occupancy
includes held/protocol time. Distinct links and nested batch/client/channel
clocks are not summed into physical traffic or elapsed time. Routing proof is
attributed to pinned RTL/testbench assertions and accepted reviews, rather than
inferred from aggregate counters.

The channel's 6,581 generic cells are contained in the 14,498-cell fabric scope;
the counts do not establish physical area. Two dataset clients do not validate
two VM contexts or independent 2 MiB scratchpads. Physical traffic, service
supply/latency, frequency, area, wall power, achieved hashes/s, complete-hash
alternatives, engine count and ASIC feasibility remain unknown or unresolved.
Original failed mapping/full-hash records, accepted records and scientific
criteria remain preserved. The complete-machine 1 MH/s below 2,500 W objective
and broader issue #72 gates remain open. A future scoped draft PR still requires
independent final-head review and applicable exact-head checks before normal merge.
