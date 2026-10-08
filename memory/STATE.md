# Current state

**M0 complete; Phase 1 source/tooling and P1-05 same-process instrumentation complete; M1 measured hardware baseline remains OPEN.** Project name is OpenRX; private remote remains `jliu67/OpenRandomX`.

## Engineering completed

- Unmodified RandomX v2.0.1 pinned at `aaafe71322df6602c21a5c72937ac284724ae561`; source manifest, build/test tools, v1/v2 controls and initial profile retained.
- Initial Phase 1 implementation `360a925`: [source analysis](../docs/PHASE1.md), static profile and hardened upstream runner schema 2. The older runner still has separate-process warmups.
- P1-05 implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`: [separate adapter](../benchmarks/steady/README.md), persistent dataset/VM/worker reuse, same-process warmups, alternating version order, known-hash controls, precise interval boundaries, strict output validation and retained failures.
- P1-05 evidence/handoff commit `fee2a3bd74a8d4f3a5e7fdc592c33edc760cc89e` was reconciled with concurrent main `9d1a8e3920d74a4dee75e66fe4df048876d11953`. Router/templates, AGENTS, communication evidence and session history were preserved. No force-push or vendor/old-runner modification.

## Evidence

[CI run 37722277487](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487), job 113132440545, passed on P1-05 implementation `59b469c`: 171-file integrity, 64 tooling tests, deterministic profile, native builds, 107 upstream tests, all prior smoke/full-dataset controls, and six new native tests; no skips. Eight known-reference controls and both 17-nonce differential comparisons matched. Expected duration rejection was retained.

Artifact 11526487498 (66,083 bytes) was downloaded and SHA-256 checked against GitHub. All four native streams/36 intervals were revalidated locally and summaries/raw checksums matched. Exact evidence, native log and retention deadline: [P1-05 validation](../docs/validation/p1-05/README.md). Local new synthetic tooling tests passed (22); no local native build was possible due to source-download DNS failure. Native execution was in CI.

**No controlled hardware experiment, wall-power samples, dynamic bottleneck attribution, RISC-V simulation or RTL result exists.** Hosted short controls are not an efficiency baseline; the three-worker case used two exposed CPUs. Clock brackets are not meter calibration. Power/hashes-per-joule fields remain null.

## GitHub communication package retained

Implementation `d3c503a5ad4154ba50e6f38119bb904cb41322d8`, handoff `9d1a8e3`: [protocol](../docs/COMMUNICATION.md), [hub #5](https://github.com/jliu67/OpenRandomX/issues/5), task/message templates, role/status inboxes, actor/session leases and deterministic router. Its 45 tests and live claim/conflict/no-op probes are documented in [communication validation](../docs/validation/communication/README.md). This is not an autonomous AI worker or a model runtime. Existing research issues are preserved. Combined integration CI is separate from the two previously verified component runs.

## Next actions

1. Claim P1-06S: implement strict power-data import/validation with declared units, clock mapping, coverage/gap checks, integration and clearly labeled synthetic tests.
2. P1-04: obtain authorized access to a controlled host, rerun references and collect balanced sufficiently long v1/v2/thread/AES measurements.
3. P1-06: validate the importer against real synchronized whole-system meter readings; no meter is provisioned.
4. P1-07: profile actual bottlenecks on a controlled host with documented counter support and overhead.
5. Continue hardware/network evidence and simulator feasibility through existing issues #2/#4/#3 without bypassing gates.

Read [board](../docs/TASKS.md), [handoff](HANDOFF.md), AGENTS and current task comments before work. Post session-scoped claims and release them at handoff. No automatic spending, external worker provisioning, account changes or fabricated results. P1-05's final editing claim release belongs on #1; no background work is promised.


## Decentralized GitHub task pool — 2026-10-08 UTC

The user clarified OpenRX has **no coordinator, permanent agent roles or automatic assignments**. A new protocol v2 is implemented on main at [c387b824](https://github.com/jliu67/OpenRandomX/commit/c387b82409b3d945f8107e5bfc71e1abfcae3ebe) without modifying vendor/randomx, benchmark algorithms or P1-05. The previous role-based communication section above is historical; see current [COMMUNICATION.md](../docs/COMMUNICATION.md) and [hub #5](https://github.com/jliu67/OpenRandomX/issues/5).

- GitHub task issue comments are the single live authority for actor/session claims; labels and bot receipts are derived views. docs/TASKS.md remains a summary, not a second ledger.
- Task v2 and Note v2 templates, legacy v1 compatibility, no role inbox, four-hour advisory leases and strict dependency checks (all referenced issues closed as completed). Unknown external hardware and M4 validation remain human evidence gates.
- Existing research issues #2/#3/#4 joined the shared pool without modifying original research bodies. #1 remains the milestone parent and its independent Phase 1 work is separated into #8 (controlled-host run, blocked), #13 (P1-06S importer, ready), #10 (wall power, blocked) and #11 (dynamic profile, blocked). #9 was closed as completed because P1-05 was already merged. #14 tracks M4 calibration; M5 #12 depends on #1, #3 and #14.
- [Router run 37724872630](https://github.com/jliu67/OpenRandomX/actions/runs/37724872630) passed 57 protocol tests and live GitHub reconciliation; issue #7 had a matching claim, #8 was blocked, #13 ready, and original #6 became a closed shared-task record with obsolete recipient label removed.
- [Combined CI 37724872611](https://github.com/jliu67/OpenRandomX/actions/runs/37724872611) succeeded on the exact upgrade commit: 121 Python tooling tests, source integrity, static profile, native builds, 107 upstream tests, v1/v2 smoke/full-dataset reference controls and six native steady tests. These are correctness/protocol results, **not measured hashes/J or RISC-V silicon evidence**.

Communication alone does not provision a model, agent host, paid service, or real-time worker. Manual router workflow-dispatch was not tested live; real four-hour expiration was tested synthetically, not via a four-hour waiting experiment. M1's host, synchronized meter and dynamic profiling remain open. Latest handoff and exact next actions: [memory/HANDOFF.md](HANDOFF.md).
