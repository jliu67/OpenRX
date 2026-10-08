# OpenRX decentralized GitHub coordination — validation

Date: 2026-10-08 UTC / 2026-10-07 Edmonton.
Scope: agent communication/issue workflow only, no processor performance claims.
Reviewed main base: d1883195b6a258434d7910deb8ed39c43d56fb16.
Published implementation: [c387b82409b3](https://github.com/jliu67/OpenRandomX/commit/c387b82409b3d945f8107e5bfc71e1abfcae3ebe). Main was updated with a non-force expected-head check. Existing native source, P1-05, vendor data and prior results remain preserved.

## Reproducible checks

- [Agent message router run 37724872630](https://github.com/jliu67/OpenRandomX/actions/runs/37724872630), job 113140830221: **success**. Python command: python3 -m unittest discover -s tests -p test_agent_router.py -v. **57 tests passed**, no failures. The job used contents:read / issues:write and reported **8 reconciled agent threads** at initial installation; no AI workers were invoked.
- [Combined foundation + Phase 1 run 37724872611](https://github.com/jliu67/OpenRandomX/actions/runs/37724872611), job 113140641436: **success**. **121 Python tests passed** (the 57 router tests are a subset), pinned-source integrity and static-profile reproducibility succeeded, native pinned source and P1-05 steady adapter built, all **107 upstream** tests passed, and **six** steady-native integration tests passed. Both algorithm smoke and full-dataset reference controls passed; artifact upload succeeded.
- Full GitHub job/step status and relevant output were inspected. Exact log/artifact retention is controlled by GitHub and may expire; links and this summary preserve observed results, not a substitute for raw test evidence.

## Live issue-state checks

The router processed a real session claim on [task #7](https://github.com/jliu67/OpenRandomX/issues/7), manual environmental blocker on [#8](https://github.com/jliu67/OpenRandomX/issues/8), dependency-blocked tasks [#10](https://github.com/jliu67/OpenRandomX/issues/10), [#11](https://github.com/jliu67/OpenRandomX/issues/11), [#12](https://github.com/jliu67/OpenRandomX/issues/12), [#14](https://github.com/jliu67/OpenRandomX/issues/14), and unclaimed ready importer [#13](https://github.com/jliu67/OpenRandomX/issues/13). [#9](https://github.com/jliu67/OpenRandomX/issues/9) was closed as completed because P1-05 had already been integrated by another session. Research issues [#2](https://github.com/jliu67/OpenRandomX/issues/2), [#3](https://github.com/jliu67/OpenRandomX/issues/3), [#4](https://github.com/jliu67/OpenRandomX/issues/4) were enrolled via new first-line /openrx join comments without changing original research descriptions. Closed v1 task #6 retained its original comments while old agent:to:coordinator recipient label was removed.

Unit coverage includes conflicting same-account/different-account sessions, unauthorized writers, edited/future commands, claim expiry and heartbeats, completion/review/blocking state transitions, malformed/missing/not-planned/self dependencies, closed-completed prerequisite satisfaction, missing templates and historic commands, recipient-label cleanup, no-op idempotence, pagination/permission failure handling and message/task separation. These are primarily synthetic API fixtures; they do **not** demonstrate two independently running AI agents.

## Design decisions and limitations

- No central coordinator, persistent roles or assigned owners. Every capable periodic visitor can choose the highest-value feasible task from one shared pool.
- The **specific task issue** is the one authoritative claim record. Issue comments preserve history; router labels/bot receipts and docs/TASKS.md are views, not independent registries. Four-hour leases remain advisory; Git does not offer transactional editing locks.
- Linked issue dependencies must be closed with state reason completed; missing, malformed, not-planned and open dependencies fail closed. External hardware/meter/ISA evidence gates remain independent human checks. M4 #14 is now a real dependency for M5 #12.
- GitHub v1 issue marker and route ROLE commands remain usable as an alias for joining the shared pool; historical comments and decisions were not erased. Obsolete role labels are no longer assigned by the workflow.
- No external database, model credentials, paid service, autonomous worker, scheduled agent loop or automatic AI-to-AI conversation was installed. The router only indexes GitHub events. Manual recovery dispatch was not independently exercised through this connector. A full four-hour live expiry was not waited out; tests simulate timestamps.
- M1 remains open: no controlled native machine, synchronized whole-system wattmeter, hardware energy measurement, calibrated RISC-V simulation or RTL speed/efficiency evidence was obtained. CI smoke correctness does not establish hashes per joule.

See [protocol](../../COMMUNICATION.md), [current board](../../TASKS.md), [latest handoff](../../../memory/HANDOFF.md) and [original communication validation](../communication/README.md).