# Session log

## Foundation session — 2026-10-08 UTC
Requested: new GitHub repository, persistent Markdown memory, RandomX v2 source, project organization.
Account verified: jliu67. Upstream v2.0.1 release metadata and source retrieved. Source commit pinned. Repository authoring underway; validation and remote creation status are recorded in STATE.md.

Validation completed: source integrity, build, all 107 upstream tests (no skips), two algorithm smoke runs, and full-dataset 1000-nonce reference checks for v1/v2 passed. Logs retained in docs/validation/foundation/. No power or RISC-V performance claims. Remote creation blocked on missing connector capability; prepared repository package available for review.

## Remote setup — 2026-10-08 UTC
User authorized browser fallback. GitHub sign-in and device verification completed. Private jliu67/OpenRandomX created. Four initial research issues opened for native baseline, X5 evidence, simulator/core selection and Monero activation verification. Foundation upload and CI verification in progress.

Remote foundation uploaded: commit 60f9cf6772f415e51306e609631c75d45c5ddfeb, 213 files, exact tree match ae045776f5cdb41d2fa3afbf9d39ddf08f7bf29a. GitHub Actions run 37716942121 passed all steps and preserved artifacts. Final documentation handoff records completion; next step is measured native baseline (issue #1), then evidence and simulator selection. Repository remains private.

## Phase 1 source characterization and tooling — 2026-10-08 UTC
Agent: ChatGPT. User requested Phase 1 implementation and durable progress/communication for collaborating agents. Reviewed remote base `2e6f3653883c4a8b344be4c4c7e4b1d8dfec0df4`; posted a scoped claim on issue #1 before editing.

Read the project instructions/memory, existing experiment and benchmark infrastructure, and pinned configuration, hash API, interpreter loop, register definitions, benchmark and v2 rationale. Produced docs/PHASE1.md and a deterministic static profile. Identified upstream single-thread affinity being ignored and multithread affinity failures not being rejected by the old wrapper.

Committed implementation `360a9255703a28845a799cfcc1086d1fb84a2c48` to main with an expected-head check. Added profile tooling, 42 regression tests, stricter benchmark/reference validation, separated warmups, duration gates, summaries and resource context. Extended existing CI with these tests and bounded full-dataset reference controls. Vendor source unchanged.

Validation: 42 local tooling tests passed (no skips); local configuration copy matched the actual Git blob. Direct native-source download failed due to DNS/network restrictions, so no local native build was claimed. Existing GitHub CI actually executed native integration: run 37719337133/job 113123130624 passed all 171-file integrity checks, 42 tooling tests, profile reproduction, build, 107 upstream tests, both smoke runs, both full-dataset controls and artifact upload. Full CI job log inspected; individual benchmark artifacts not independently downloaded. Artifact ID 11524827413 and Actions-reported digest are recorded in docs/validation/phase1/.

Added the task board, evidence entries, decisions and actionable handoff. Preserved observed build/action warnings and the local network failure. M1 remains open: controlled host/AES/thread measurements, dynamic profiling and real time-aligned wall power are not available. No hardware spending, RTL, simulation or competitiveness claim. Session editing claim released at handoff; no additional agent or background process was launched. Next commands and ownership rules: memory/HANDOFF.md and docs/TASKS.md.

## GitHub-native agent communication — 2026-10-08 UTC / 2026-10-07 Edmonton

Agent/session: `chatgpt/20261008-comms`. User requested building the GitHub-only agent communication system. Reviewed existing AGENTS.md, project memory, task board, handoff and CI at `ea90554c486ed6c7eae6fafc2e1c16b90193b1d2`. Created the persistent hub #5 and installation task #6, and posted scoped claim comment 6051389366 before implementation.

Published commit `d3c503a5ad4154ba50e6f38119bb904cb41322d8` through a non-force expected-head update. Added a deterministic Python router, 45 regression tests, issue task/message templates, role/status labels, a bounded GitHub Actions workflow, communication protocol, validation evidence and discoverability links. Existing vendor, mining, benchmark, RTL, research issues and foundation CI code were preserved.

Local new-suite validation: 45 tests passed with no skips; Python compilation and YAML structural checks passed. The isolated workspace did not rerun existing Phase 1/native tests locally. Live router run 37722591259/job 113133439307 completed successfully, passed all 45 tests, and reconciled the actual claim with the declared minimal permissions. The complete router job log was inspected. Existing foundation/native CI run 37722591236/job 113133438813 and every reported step also passed; its complete log and individual artifacts were not independently downloaded in this communication session.

Live test: the original claim was accepted and controlled competing session `test/conflict-probe` (comment 6051534472) was rejected. This test was not a second running agent. Ordinary comment 6051553320 and later successful event-driven reconciliation (including run 37722850149) left the same bot receipt 6051531399 unchanged at its test-time timestamp, demonstrating no duplicate/no-op writes. Final claim lifecycle and handoff are recorded on #6. The hub contains role inbox and queue links.

Preserved results, limitations, decisions and Phase 1 priorities in this documentation handoff. Manual dispatch is provided but not independently exercised; four-hour lease expiry was tested synthetically, not by waiting four hours. No model endpoint, autonomous worker, external queue, paid service, schedule, account-setting change or hardware measurement was created. Communication is operational; M1 remains open. Future agents must read docs/COMMUNICATION.md and the current issue receipts rather than infer activity from a role name or old session log.

## P1-05 implementation and concurrent-work reconciliation — 2026-10-08 UTC

Agent/session: `chatgpt/20261008-p105`. User asked to continue Phase 1. Claim and progress on #1: comments 6051307610 and 6051530103. Starting base was `ea90554`; implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676` was validated on branch `openrx/p1-05-steady-timing`. Evidence-only handoff commit: `fee2a3bd74a8d4f3a5e7fdc592c33edc760cc89e`. The full branch session record is retained in [handoffs/p1-05-session-log-20261008.md](handoffs/p1-05-session-log-20261008.md).

Added the opt-in same-process adapter, build helper, evidence runner, 22 synthetic harness tests and six native tests. Pinned source and old benchmark runner stayed unchanged. Persistent dataset/VM/workers, exact completed counts, same-process warmup, balanced v1/v2 order, monotonic/realtime brackets, FP restoration, strict failure retention and declared timing limitations are documented in benchmarks/steady/README.md.

Actual CI run `37722277487` / job `113132440545` passed: 171 vendor files, 64 tooling tests, profile reproduction, native builds, 107 upstream tests, previous controls and six native tests. No skips. Eight known-reference controls, repeated known hashes and both 17-nonce differential comparisons matched. Four duration rejections were expected tests. Local work was 22 synthetic tests/syntax checks and downloaded-artifact revalidation; direct source downloads failed, so no local RandomX build was claimed.

Downloaded artifact `11526487498`, 66,083 bytes, SHA-256 `98c2a158d5ad3795c31fb4fd1fb52fc5f199bc34604ba979a4078fa0788844a3`, was independently checked. All four raw streams/36 intervals were revalidated and raw/summary/source checks matched. Evidence and retention deadline are in docs/validation/p1-05/. The CI runner exposed two logical CPUs; three-worker correctness oversubscription is not scaling data.

The final expected-head check found main had advanced to `9d1a8e3920d74a4dee75e66fe4df048876d11953` with communication work. No update was attempted against the stale base. Read its commits/protocol/AGENTS and hub handoff; acknowledged on hub #5 comment 6051704360. Reconciled documentation on the fresh main tree, reusing exact tested code/evidence blobs while preserving the router, templates, instructions, communication evidence and the entire existing session log. Existing communication D012-D014 were retained; branch-only P1-05 decisions became D015-D017. Full previous handoffs were preserved as historical snapshots under memory/handoffs/.

P1-05 is done; P1-06S importer software is the next unblocked coding task. M1 still needs controlled host/AES/thread measurements, dynamic profiling and real synchronized whole-system power. Combined integration CI is to be recorded at the actual merge SHA rather than inferred from separate component runs. No force-push, paid compute, new model worker, hardware purchase, account change, RTL or competitiveness claim. Final publication/claim release is recorded on #1 and hub #5.


## Decentralized GitHub agent coordination — 2026-10-08 UTC / 2026-10-07 Edmonton

Agent/session: chatgpt/20261008-decentral. User clarified autonomous periodic agents without a coordinator/roles, and requested compatibility with the Phase 1 GitHub board. Reviewed current main, preserved concurrent P1-05 work including integration 960b8b52 and later d1883195, opened and claimed task #7. Migrated communication protocol to a shared task pool, per-task authoritative session claims, old role-command compatibility, task dependencies and no fixed recipient assumption; published [c387b824](https://github.com/jliu67/OpenRandomX/commit/c387b82409b3d945f8107e5bfc71e1abfcae3ebe) via non-force expected-head update.

New scoped task issues: #8 controlled-host baseline (externally blocked), #9 integration review (closed as completed since P1-05 had already merged), #10 synchronized wall power (depends #8/#9/#13, plus a meter), #11 dynamic profile (depends #8), #12 M5 RTL gate (depends #1/#3/#14), #13 P1-06S importer (ready), #14 M4 calibrated simulation (depends #1/#3). Existing #2/#3/#4 joined the pool via additive /openrx join comments. Parent #1 and original history left intact. Hub #5 updated from obsolete role inboxes to unassigned task views.

Remote validation: [router 37724872630](https://github.com/jliu67/OpenRandomX/actions/runs/37724872630), job 113140830221, passed all **57** protocol tests and live reconciliation; [native CI 37724872611](https://github.com/jliu67/OpenRandomX/actions/runs/37724872611), job 113140641436, passed **121** Python tests, all **107** upstream tests and **6** native steady tests, as well as source integrity/build/profile and v1/v2 reference controls. Complete job-step status and log excerpts inspected. The router's 57 tests are included in the 121 Python tests. No model or agent worker was launched, no host/meter setup was invented, and there are no new performance/energy claims. Manual dispatch and multi-hour live expiry remain untested beyond synthetic fixtures; GitHub labels are cached projections.

All source and previous evidence were preserved, new engineering decisions D018-D021 recorded, and the current handoff precedes previous handoffs. Next unblocked task: P1-06S #13 or independent #2/#3/#4 research; complete M1 measurement gates before design optimization.

## P1-06S power-data import and validation — 2026-10-08 UTC / 2026-10-07 Edmonton

Agent/session `chatgpt/20261008-p106s`. User requested continuing Phase 1. Read live main `7b7ec36a37035bde56db487288a48e122516959f`, AGENTS, current protocol/board/memory, experiment, native adapter and task #13. Posted task-specific claim comment 6051949333; bot receipt 6051828603 accepted the matching session with expiry 2026-10-08T08:04:01Z. No claim was placed on parent #1 or other independent tasks.

Implemented `scripts/power_import.py` and 61 synthetic tests in `tests/test_power_import.py`; commit `2b28d6fb4604a2b861241d38678e24c8541aed02` on `openrx/p1-06s-power-import`. Scope: revalidate complete saved steady run and digests, strict whole-system AC point-power schema, calibrated affine clock mapping and declared bounds, sample order/gap/coverage/clock checks, exact rational clipped trapezoids, conservative conditional error bounds, ratio-of-totals summaries, explicit synthetic opt-in/output separation, immutable snapshots and retained failure reports. No vendor, native adapter, old runner, router, workflow, simulator or RTL changes.

Local new suite passed 61 tests with no skips on Python 3.13.5, including final revalidation. Source/test Git blobs matched actual connector-read implementation. Existing read-only steady validator matched its exact pinned blob/SHA-256. Native execution occurred through existing CI, not locally. CI run 37726645625/job 113146214930 passed all steps: **182 Python tests, 107 upstream tests and six native tests**, no skips, plus source integrity/profile/build and prior reference controls. Counts were read from downloaded logs rather than inferred.

Downloaded artifact 11528236706 (68,046 bytes) independently hashed to `1eacda6564e038bc5933b04bc5030b20b5373b629551e801a64e6bed946a6358`, matching GitHub. Inspected actual test logs and run metadata. Three successful saved native runs joined to generated, explicitly synthetic constant-power traces; 12 measurement intervals matched the exact integration oracle and retained null measured fields. The duration-rejected native run was refused. This audit first ran against the prior P1-05 integration archive and then the current implementation archive. No short CI rate or synthetic energy was promoted to real measurement.

An initial audit assertion incorrectly matched the word 'skipped' in a passing router test name. Corrected to match outcome positions, reran and recorded the false positive. It was not a failing/skipped CI test and did not require production code changes. The committed evidence reproduction helper was executed locally; its ledger matched ci-checks.json byte-for-byte. Full CI job/build log was not downloaded; actual named artifact logs and job/step outcomes were inspected. Artifact retention ends 2027-01-06T04:15:51Z; full raw inputs need retention beyond that deadline.

Prepared protocol, validation ledger/local log/reproduction helper, D022-D023, current state/board/experiment/README and a task-specific handoff. Preserved the complete prior SESSION_LOG prefix and archived previous state/handoff blobs byte-for-byte. Main publication uses a fresh non-force expected-head check. Application/test bytes remain those of the passing implementation; the evidence helper was tested locally. Final commit links and `/openrx review chatgpt/20261008-p106s` handoff belong on #13, with acknowledgement on hub #5.

Implementation/testing complete; independent software review/acceptance remains open on #13. No independent reviewer was launched or impersonated. Physical #8/#10/#11 and parent M1 remain open. The importer cannot certify meter/calibration/clock provenance and deliberately excludes generic CSV, interval-average and cumulative-energy formats without separate reviewed conversion/model work. No real wall-power reading, controlled host matrix, dynamic bottleneck profile, hardware purchase, paid service, account change, external worker, RISC-V result or RTL optimization was obtained.


## M3 scalar RISC-V functional preflight and source-backed selection — 2026-10-08 UTC / Edmonton

Session codex/20261008-m3. User requested continued OpenRX work after the progress report. Read actual main d9e41cd07766e9c990641605dff1145d2f035d7d, mandatory memory/roadmap/protocol, issue/branch histories; claimed ready #3 via comment6061588658 and verified matching four-hour receipt. No claim on parent #1 or unrelated tasks.

Independent bounded agents researched core/simulator sources, implemented the portable probe and separately reviewed arithmetic/source/evidence. Source pins and licenses support provisional Chipyard1.14.0/MediumBoomV3Config; gem5 full-system Linux exploration addresses SE startup-SIGILL and cache-flush/mprotect gaps. CVA6 div/sqrt and memory-map concerns documented. No permanent coordinator/roles or background workers were installed.

Implemented unchanged-RandomX C++ light probe (39 required integer/FP/v2-v1 interpreter/JIT checks), GCC14 RV64GC/lp64d cross toolchain, complete-stream independent validator, 17 rejection regressions and QEMU CI. Initial implementation e5eafde50d074f19afb37d08ccec4c59dd88a33d was published on isolated branch openrx/m3-riscv-preflight as draft PR #15, using fresh expected-head non-force updates.

Initial PR RISC-V CI37790683112/job113356939599 passed native and actual QEMU controls:39 required each, eight exact software-AES hashes each, one optional hardware-AES skip each. Existing CI37790683131/job113356939659 passed all source/build/profile/reference/upstream/steady steps. Initial artifact11555544301 (452645bytes) was downloaded and SHA256 matched5f042957866115a6eeb488953ec8d52c892896fd359353efac9da9d9334fadcb. Linked ELF machine243 and binary61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657 matched report. Root and independent reviewer revalidated native/QEMU raw output with stricter current validator. Artifact expires2027-01-06T14:13:21Z; compact evidence committed. Actual QEMU8.2.2/GCC14.2.0/binutils2.42 differs from upstream review pins.

Local GCC13 manual unchanged-source native build passed39; local full Python suite passed199 (182 existing+17 new), no unittest skips. No CMake/cross compiler/QEMU available locally. Binary PDFs refused by text-only connector prevented full local manifest verification; all167 text/source files were exact and real CI verified171 files. Git clone lacked CLI authentication; GitHub connector/Git object API supplied reads and branch updates. Initial probe-validator stage mismatch was corrected before first execution/publication. Independent review then hardened exact names/oracles, source/config/VM flag binding, malformed optional outcomes and capture of compile_commands (missing from initial archive). Native assembly linker warning preserved without vendor changes.

Created independently ready #16 for pinned gem5 full-system Linux startup/JIT correctness; selected BOOM Linux/config/full-dataset correctness remains unexecuted. Updated board/README/evidence/decisions/state/questions/handoff and EXP002; archived previous state/handoff byte-for-byte and preserved SESSION_LOG prefix. Final tested revision/CI/review and claim-release receipts are on #3/PR #15. M3 remains open; M1 measured hardware and #13 importer acceptance remain outstanding; M4/M5 gates unchanged. No modeled timing/power, hardware efficiency, RTL optimization, purchase, paid compute, account change or autonomous agent provisioning.

Final acceptance/publication: reviewed code f9c3ee7debc94807a4a82b537079bdf455aea551 passed RISC-V CI37791921197/job113361273431 and foundation CI37791921307/job113361273371. Actual decoded logs counted199 Python,107 upstream and6 native steady tests;39 required probe checks passed on both native and QEMU RISC-V, with1 optional hardware-AES skip per probe. Final artifact11557345367 ZIP455549bytes digestca14f2e811cf6570d989928c0eafcbd046851b05830e08e624c569721ffafb99 matched GitHub. Root and reviewer verified final raw streams/ELF/stable binary digest and per-file compile commands. Preserve PR checkoutdc6de662bedc6136c4b1ae045ff7fc9b45f7fb92 separately from headf9c3ee7; expiry2027-01-06T14:22:28Z. All required-control review fixes were resolved before merge. PR #15 merged at83cbb3ec279a9fab9c5bb18b567fbbd7591f1aed; final audit/memory publication is docs-only. #3 review/release keeps milestone open and #16 is ready for independently claimed full-system research.


## 2026-10-08 — independent P1-06S repair and Linux runtime gate

User requested continued engineering. Base bac3a069. Accepted claims #13 codex/20261008-p106-review and #16 codex/20261008-fs. Review demonstrated three malformed-input crashes; narrow fixes preserve formulas/vendor/native source. Separate patch reviewer accepted64 importer tests,327 type/13Decimal cases,10 valid-report comparisons and9,024 numerical checks. Runtime reviewer corrected sigsetjmp context; native9/QEMU9 pass. PR17 implementation288cebbc passed foundation37803105632/RISC-V37803105634:219Python/107upstream/6native,original39 semantic/hash checks each; root downloaded artifact11561518954,digest-checked and replayed four streams. No physical power/RTL/core timing claim. Prior memory snapshots retained. Pinned gem5 build/guest work continues separately; boot not yet accepted.


## Independent inspection: chat citation artifacts and gem5 CI timeout — 2026-10-08 UTC

Session `chatgpt/20261008-incident`; scope task #20, no overlap with active task #16 branch. User-provided screenshot displayed raw citation/widget markup and repeated progress messages; this is a chat-rendering symptom, not independently diagnosed model-state failure. Reviewed latest issue board, commit comparison (no changes to vendor/randomx since `bac3a069`), merged PR #17 and #19 evidence, active PR #18 CI and direct official Monero release material.

Both gem5 full-system workflow runs `37805009018` and `37805005108` failed at the explicit 45-minute build timeout (exit 124) while still compiling SCons objects. Guest prep/boot/JIT/hash stages did not execute. Prior and independent RISC-V correctness CI at merged PR #17 passed. PR #18 and issue #16 received inspector evidence/mitigation comments; no branch takeover or unchanged rerun was initiated. Issue #4 closed as a dated primary-source audit and issue #13 as reviewed software, not measured physical results. Updated board/state/handoff to correct stale statements; report in docs/inspection/2026-10-08-incident.md. The Monero source replay from committed files covers 18 immutable Git captures but additional time-varying API/website captures remain in temporary storage; follow-up archival recommended. No model runtime, credentials or permissions changed.


## Final integrated results and bounded gem5 execution — 2026-10-08 UTC

Session `codex/20261008-fs` finishes the work authorized by the user to continue OpenRX. PR #17 merged at `973cd0d94f987ad4a46b85f7b6d66170104c64a1`; #13 is independently reviewed and closed as completed software. Final merged-main foundation run37805551737 and RISC-V run37805551604 passed 219 Python, 107 upstream and six native steady tests, 39 required unchanged RandomX checks and nine Linux runtime checks in each native/QEMU environment. Optional hardware AES remains one explicit skip per RandomX probe. Artifact11563570169 ZIP SHA-256 `0af776da4540bc9be627d0f768b59a4c675bbdf93830527633fd9b05e560e21a` matched the downloaded archive; all four streams and five source identities were independently replayed. These tests establish software behavior, not physical energy or selected-core timing.

PR #19 merged at `0592c630fb9b2d05d00550e0a387a3a89c0819f5`; #4 is closed as completed dated source research. Independent audit checked 30 captured-payload digests, 21 assertions and 18 immutable source refetches. Released Monero consensus targets v1 by source-backed inference rather than a separately observed chain tip; the beta v2 schedule belongs to a separate stressnet/testnet and supplies no actual mainnet activation date. Keep v2-first research with exact v1 controls. Time-varying raw API/site captures remain in a temporary source cache; committed manifests and reproduction helpers do not supply full offline replay.

Draft PR #18 retains independently reviewed pinned gem5 v25.1.0.1 (`c8222cc67a399bfc01e8658dd14b30d5bfd634f9`) scaffolding and final execution evidence at `f44cd47ca2061c39fa45d031a307f6df4b4f535d`. The one-core AtomicSimpleCPU/RVV-off/classic-cache/4-GiB recipe is functional exploration. Exact guest resources were downloaded and verified; static guest ABI checks, seven offline wrapper tests and ten independent synthetic failure cases pass. No Linux boot follows from those checks.

Three canonical six-worker local 20-minute windows exited124 after earlier configuration failures were corrected; the final build stopped2026-10-08T16:50:20Z. Both actual hosted cold two-worker45-minute builds, runs37805009018 and37805005108, also exited124 before linking. No gem5.opt exists; no guest boot, runtime control or RandomX hash ran. Full local logs/configuration/source-consistency/exit evidence and independently downloaded/digest-verified CI artifacts/action logs are retained on the draft. The duplicate expensive push trigger was removed; filtered PR/manual dispatch remains. Final evidence/docs commits use [skip ci] to avoid unchanged known-failing cold builds. Source/configuration implementation did not change after acceptance.

Concurrent inspector main commit `259db038650faaa53c39e4964358acd771d07f42` was read before publication. Its report remains under docs/inspection/2026-10-08-incident.md; its complete SESSION_LOG prefix is preserved and exact STATE/HANDOFF snapshots are archived under memory/handoffs/pre-final-fs-inspector-*. Main summaries link the immutable draft evidence rather than nonexistent mainline FS-only files. Current wording distinguishes tested RW/RX page permissions from global W^X policy, and L2 capacity from walker-cache capacity.

Posted matching release6064988893 on #16; the task remains open for a fresh capable visitor. All local compilation processes are stopped. Next: resume the exact incremental source build with recorded dependency environment or establish a larger-budget source-verified build; verify the resulting simulator before running actual guest runtime controls, then the unchanged complete light hash matrix. The alternative classic-only source recipe is documented as unexecuted and does not imply a known speedup. Full dataset/intended-core runtime and controlled host/meter/counter #8/#10/#11 remain open. No paid compute, hardware purchase, vendor changes, physical measurement, RTL optimization or M1/M3/M4/M5 completion.


## Compact cross-task announcement policy — 2026-10-08 UTC

User approved making concise hub #5 announcements a required handoff practice for significant completed packages, major failures/blockers and milestone changes. Inspector session `chatgpt/20261008-hub-handoffs` claimed #24, scoped to policy/template/board/decision updates only. Protocol specifies 2–4 sentences with task/PR, verified outcome, remaining blocker/next action; full evidence remains on the task issue. Existing `/openrx announce` requests the GitHub Actions bot repost and receipt verification. Not an automatic task-close/merge gate; emails remain subject to subscriptions. No fixed roles, simulated work, spending or changes to runtime/router were introduced.

## Repository, board and simulator reuse review — 2026-10-08 UTC

User requested another review of the repository, messages and project board, followed by fixes and continued work. Refreshed actual main, hub #5, task claims, PRs and CI before choosing #16 under accepted session `codex/20261008-fs-reuse`. Corrected the hub's stale #13/#4 summaries and #10 dependency status. #20's incident report was independently verified against actual prior build failures and closed as completed. The earlier inspector report and exact STATE/HANDOFF snapshots remain preserved.

Separate task #22 addressed a source-identified announcement replacement risk: top-level single-pending concurrency could replace an eligible request. Merged PR #23 at `b562a941bec39c3a0747a2129903dd33bb471f62` moves queuing to eligible announcement jobs with the supported maximum queue, preserving publisher authorization and trusted checkout. Eight tests and actual workflow run 37815826807 passed; source 6065291820 has bot receipt 6065295258. No observed lost message is claimed. A different capable agent accepted the change; #22 is completed. Concurrent #24's compact major-handoff policy at 511e173 is retained. Separate review found duplicate D029; its original author corrected only the new policy ID to D030 at `a2128b9ee9dd93acdfc392bc4752e412f5e5a3d2`. Root refreshed rather than overwriting that correction. #24 is independently accepted and closed; its exact prior SESSION_LOG prefix remains intact. New decisions D031/D032 record simulator reuse and queue/review semantics.

The retained canonical gem5 build completed its remaining generated translation units in one bounded incremental resume, then the ordinary final link hit the 8-GiB host memory limit. One 600-second supported recovery using upstream `--limit-ld-memory-usage` succeeded in 248.76 seconds, executing no target C++ compilations and causing no new OOM kill. All 10,933 archived source files and canonical config remain unchanged. The original unstripped 957,300,488-byte simulator SHA-256 is `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`; actual build-info/version/loader checks pass. Complete timeouts, OOM, recovery/config/toolchain/source records are retained. The reusable 936,569,944-byte archive contains original binary, immutable source/notices, build evidence and minimal Python runtime. Its 918 files and clean-environment wrapper passed. A whole-file save exceeded the 512-MiB service limit before transfer; two ordered parts and manifest then saved successfully. Archive SHA-256 `b9536aa9dbce308edcdb735c518395ebf2e02d20ecdf53b181deeded19d07769`, identities and reconstruction are in REUSE.md. Portability beyond this host is untested; no large binary entered Git.

Actual full-system Linux 6.8.12 boot and all nine standalone RV64 runtime controls passed using one Atomic core, RVV disabled, classic 16-KiB L1/256-KiB L2/walker caches and 4 GiB RAM. Exact signal/protection/flush/overwrite oracles, child 0, empty framed stderr, completion and hypercalls 1/2/3 passed. A distinct agent independently replayed serial/report and rehashed simulator/source/config/payload plus firmware/kernel/disk identities. The runtime wrapper took 958.249 host seconds including hashing, with 917.34 seconds in simulator stats; these are host resource observations, not modeled processor performance. Raw serial/report/config/DTS and encoded DTB, source snapshots, full logs and independent acceptance are under actual-runtime-20261008/ and ACTUAL-GEM5-REVIEW-20261008.md.

One separate unchanged light attempt used the already audited hash ELF `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`. It timed out at its declared 1,200-second child bound, wrapper 1,261.24 seconds. Linux boot and all nine runtime controls passed again, and the hash ELF was verified/launched, but the old post-exit capture exposed no hash body/END/summary or completion/hypercall 3. Independent replay accepts that partial record and exact input identities, not complete hashes or a semantic mismatch. Full raw timeout and original executing-source snapshots are preserved separately in actual-light-20261008/ and ACTUAL-LIGHT-REVIEW-20261008.md. Final stats are empty; no final simulated tick is inferred. No further local gem5 build or guest remains running.

This attempt exposed an observability defect: redirecting stdout until probe completion hid partial hash progress on timeout. The reviewed runner now tees already-flushed records to serial and guest capture, preserves immediate PIPESTATUS, retains exact child failure and refuses completion if capture fails. Strict nine/39-control oracles remain unchanged. Real generated-Bash controls and independent interruption/failure tests pass; this new script was not executed by the retained old-runner guest attempts. Final functional head `4f4cf17880ccfa2e904eb9d2dc23892b828bce12` passed all five push/PR CI runs: 245 Python, 107 upstream, 6 native, 26 offline gem5, 171 vendor files, 39 RandomX + 9 runtime each native/QEMU with explicit optional AES skips. Exact logs, reviewed source digests and tested merge `efd3084d1a29cc2f5dcae317c3b9eb6dae5b52de` are in streaming-ci-20261008/ci-review.json. The actual hosted gem5 guest job was skipped by its manual guard; new hosted manual build/cache/artifact reuse remains unexecuted.

PR #18 integrates the accepted implementation and actual runtime stage with separately reviewed evidence. Final updates after 4f4 are documentation/evidence only, with functional digests rechecked. Main instructions/template/policy are preserved from the refreshed concurrent head; publication uses expected-head non-force updates and retains all remote vendor blobs. Task #16 remains open for a complete unchanged light matrix, then separate full-dataset/intended-core gates. Next: reuse the exact saved simulator and streaming runner with a new explicit bound justified by observed startup/workload progress; do not repeat the identical cold build or 20-minute attempt. #8/#10/#11 still need controlled host/counter/meter access; #2 hardware evidence and future activation/live-tip questions remain open. M1/M3/M4/M5, physical efficiency and RTL gates stay open. No vendor changes, fabricated hash results, paid compute or account changes were introduced.

## Extended unchanged guest and reliable stop control — 2026-10-08/09 UTC

Session `codex/20261008-light-resume`; user authorized continued engineering after exhaustive board/messages/handoffs/code ingestion. Base `50ba83166a9df0fca243af57a7c889ec752a59fc`; #16 claim comment 6070689194 had a matching accepted receipt through 2026-10-09T02:56:39Z. The repository was renamed to `jliu67/OpenRX`, retaining repository ID 1409576804. Exact prior state/handoff snapshots are archived under pre-light-resume-*-20261008.md; earlier session history is preserved.

Reused the verified original simulator and restored both saved archive parts with matching digests. Restored two committed fixtures and four original vendor PDFs omitted from the initial text snapshot; all 171 vendor files now verify locally. Independent review found two signal transition races in the initial exception-raising cancellation draft; they were corrected before publication and never executed by the real guest. Final PR #25 passed 253 Python / 34 gem5 host controls and 171 vendor files; five hosted checks and four artifacts were independently replayed. PR #25 merged at `abe066f7c1b17cb3225b55cc45848a153a20ea7a` with the exact tested `9d108c4` tree. Staging failures, final logs and independent source/CI review remain in cancellation-20261008.

Launched the unchanged actual guest at 2026-10-08T23:09Z with no wall cutoff and a per-call simulated guard of `10^13`. Eight source snapshots, preflight and the command were retained. Actual runtime frames independently pass nine controls; all 31 integer/FP checks match exact independent oracles. No hash values, cache pass, complete hash summary/END, guest completion or hypercall 3 were observed. Independent exact-ELF/configuration review proves the mandatory cache round loops alone require at least 10,519,287,679,000 ticks, exceeding the guard. Root replayed counts; separate reviewers confirmed pointer invariants, reference Argon fill count and ordinary Atomic scheduling.

Requested one tracked-tool control-C at 23:54:06Z after that proof. The tool returned exit 1 with `^C`, without a final runner report. Exact termination mechanism, handler receipt, simulator child code and runner-performed reaping are unavailable; none were invented. Root and independent reviewer observed no matching simulator/wrapper afterward. No wall/tick timeout event or hash mismatch was observed. Raw serial/configuration/script/DTB/stdlogs, manifests, monitoring observations, extracted complete runtime and incomplete hash streams, and independent partial acceptance are preserved in light-resume-20261008. A separately timestamped post-session audit verified all eight source bindings, simulator, three resources and byte-exact embedded ELF payloads; it is not a runner report.

Added optional fresh stop-file requests through the runner's own wait/signal/cleanup/report path for future monitoring across PID namespaces. Independent review found a late-marker completion race in the initial polling patch; it was corrected before publication. Final root validation passes 257 Python tests (38 gem5 host controls) in 9.628 seconds and all 171 vendor files. Separate review, exact source digests and full logs are in stop-file-20261008. The manual workflow light path now declares `10^14`; runtime-only remains `10^13`, and host shell controls verify both paths. The larger finite allowance is proposed, not guaranteed sufficient. New stop-file source was not executed by the saved actual guest.

Publish this separate reviewed source/evidence package from refreshed main using non-force expected-head updates. Final integration, claim transition and verified compact hub copy are indexed on #16/#5. Keep #16/M3 open for complete unchanged 39 semantic/hash plus nine runtime controls, then full dataset/intended-core work. M1 physical host/counter/meter and M4/M5 gates remain open. No simulator rebuild, vendor/workload/RTL change, paid compute or account change was made.

Final integration: PR #26 merged at `77a1641fb85f386bce4a5b51e00dedbe257376f6`; its whole tree equals source head `78599e2812053c85037401e3f2e4d00191428427` and synthetic PR checkout `72e0e67588c9d19457a3ff95457a457a4850fb88`. All five hosted checks passed and were independently checked from decoded logs; exact job/run/count/source identities are recorded in stop-file-20261008/integration.json. Claim release 6071620898 is accepted with ready status, null claim and no warnings. Hub request 6071621109 produced verified bot copy 6071623180. No matching simulator/wrapper remains; #16 and remaining milestone gates stay open.


## Critical local infrastructure migration — staging, 2026-10-09 UTC

User authorized a loss-intolerant infrastructure migration from temporary sandboxes to the owner's Ubuntu host.
Task #27 and initial inactive hub announcement were published. Native Ubuntu 22.04, physical hardware,
persistent storage and user systemd/lingering were identified; a fresh versioned migration checkout/install tree
is separate from the preserved original checkout. This entry records **STAGING, not activation or completion**.

Exact pre-migration AGENTS/README/board/roadmap/project/state/handoff snapshots were saved and digest-verified
under `memory/handoffs/pre-local-migration-*`; prior experiment/milestone and session-log history is retained.
Draft policy/runbook/incomplete acceptance receipt now describe local-only expensive execution after cutover,
owner-mediated GitHub submission/results, unavailable remote access, duplicate/resource locks, lifecycle recovery
and unverified checkpoint resume. Historic sandbox next-run recipes are retained but explicitly inactive.

The saved 936,569,944-byte simulator package is not currently retrievable through callable tools; its earlier
save IDs/digests and original 957,300,488-byte binary identity remain preserved. A new build from pinned gem5
c8222cc67a399bfc01e8658dd14b30d5bfd634f9 is in progress with separate Ubuntu 22.04/toolchain provenance.
Exact guest/resource recovery, local boot/runtime/regressions, durable-runner/lifecycle/integrity gates,
independent review and merged migration PR remain pending. No expensive research run, scientific milestone
closure, new timing/power claim, resume guarantee, remote listener or permanent coordinator is asserted.


## Local staging evidence and preserved source-build OOM — 2026-10-09 UTC

Independent review verifies all 694 original tracked scientific files and 10,933 pinned simulator source
entries unchanged; exact guest ELFs and all pinned firmware/kernel/compressed/expanded disk identities
are recovered/verified. Selected 41 toolchain archives and installed versions match; no complete offline
dependency closure is claimed. Native strict39/hash8/runtime9 controls, vendor171 and upstream106 plus
one valid unsupported-AVX2 skip are accepted, without completing gem5 or M1–M5.

Host runner lifecycle evidence retains exact source snapshots: v4 ten fixtures/full277 tests bind
24717a7f, final cd90f1d0 inventory safety correction has separately reviewed22 focused tests and targetedv6
regular-output/FIFO evidence. Launching process absence, advancing logs and host-manager ancestry establish
observed launch-session independence; whole ChatGPT termination/host reboot were not performed.
Malformed/torn files or broken ledgers require preserved additive forensic records and manual reconciliation,
never overwritten records, invented acceptance or automatic scientific replay.

Persistent build attempt02 failed with actual systemd Result=oom-kill at6GiB while compiling generated
RISC-V units. Source, partial state and full logs are preserved. No final build-result.json was created;
the waiting pipeline failed on that missing record and launched no simulator or state transition.
Sanitized failure evidence retains separate host/public digests under local-migration-20261009/build-failure-02/.
A separate copied partial-build attempt03 is being prepared with one worker and a recorded larger memory
budget. Migration remains STAGING and execution policy inactive; local boot/runtime and reviewed merged
cutover remain required. No build or simulator correctness was fabricated from partial progress.


## Additive build recovery and durability-runner revision — 2026-10-09 UTC

Attempt03 begins in a separate full copy of preserved attempt02 partial build state with one SCons worker,
8GiB RAM/2GiB swap/100% CPU limits and no wall cutoff; normal runner defaults remain6GiB/1GiB/200%.
Its build/config/toolchain records remain separate and no completed simulator or guest result is asserted.
Final durability runner916b6b0d is stored as a new immutable release. It adds fsync of retained output files/
directories before receipt publication and passes23 focused tests including injected flush failure with
preserved outputs/no false receipt. Independent latest-source review is pending; old v4/full277 and
cd90/full279/22focused/v6 evidence retain their exact snapshots.

Runtime request revision02 on #27 binds new key issue-27-local-runtime-6f54052-attempt-02,
request specification b0117492ebcf3681fcd28d5b0ae04c7ede200a1deb341566890647d09fdf8ecd and
runner916b6b0d. The earlier cd90 request was never submitted after build02 OOM. Revised request/pipeline
prerequisites still require completed simulator/loader/source/input review and evidence-backed local validation.
Migration remains STAGING/inactive; neither a request comment nor build progress authorizes full-scale research.


Latest runner916b6b0d durability revision is independently accepted in runner-durability-independent-review.json:
23 focused controls pass13.357s with unchanged source identities, including preserved flush failure/no receipt.
Architecture session independence is accepted from observed launcher exit, continued host-manager logs and
systemd ancestry; whole ChatGPT daemon termination and host reboot were not performed. Reviewed pipelinev2
binds runner916/specb011/new runtime request attempt02 and immutable scientific source6f54052, with enforced
build/loader/toolchain/input/local-validation prerequisites. This is guard/source review, not executed guest
acceptance or cutover. Earlier test/fixture snapshots remain intact; no final full280-suite claim is made.


The reviewed pipelinev2 runs as openrx-migration-validation-pipeline-v2-20261009.service, waiting for
build03 and every pinned preflight; this fixed owner-authorized driver does not poll remote issues or
claim any guest outcome. Major failure hub request produced verified botcopy6085149398.
Staged documentation links current reviews/evidence and retains STAGING/inactive with no fabricated
state advance. Remote direct execution remains unavailable; final technical/cutover gates still apply.


## Preventive staging signal-safety hold — 2026-10-09 UTC

Root identified a post-reap numerical PID/process-group reuse hazard in the previously reviewed916
runner. Pipelinev2 was stopped before preflight/guest execution and overall916 future execution acceptance
was withdrawn on #27/PR28; the fsync-only review remains scoped historical evidence. No expensive guest
request ran and keys01/02 were never submitted. A controlled true-child fixture confirmed the same race
in the untouched frozen6f gem5 wrapper, intercepting signals without signaling any host group.

Runner988cf13f candidate uses append-only signal recording/sole-main-loop reaping and private finalizer
NotifyAccess=exec timeout extension; worker45-second stop remains unchanged. Wrapper5c275bf3 alters
only run_process lifecycle ownership, not model/resources/scientific oracles. Independent f6ea signal-only
25tests and tiny notify components are separate proof; final28/wrapper40/full287/actual55-second-finalizer
proof and fresh reviewed-code readonly checkout/new request/pipelinev3 binding remain pending.
Original source, historical evidence and ongoing build03 are preserved. Migration stays STAGING/inactive.


Corrected final runner988cf13f and wrapper5c275bf3 are independently accepted for local validation:
287 complete repository controls including28 runner tests,40 targeted gem5 host controls and stable exact
source identities. Actual private finalizer delayed55.1219 seconds with six manager notifications and
verified receipt integrity proves extension beyond its45-second grace; original false harness result and
corrected audit are preserved. Terminal manager properties were not captured; actual large-output
throughput/physical I/O-failure recovery and guest correctness are not asserted. Final immutable codecommit/
execution checkout/request03/pipeline3 bindings still need review before guest submission. Migration stays
STAGING/inactive; old execution acceptance withdrawals and every prior snapshot remain preserved.


## Reviewed immutable source and waiting pipelinev3 — 2026-10-09 UTC

Readonly sourceb4b5ffc5c5ee3f59e0e862a6979d265fd410d726/runner988/wrapper5c and runtime request03
are independently binding-reviewed, including clean byte-exact checkout,41 current package versions/archive
identities and all input pins. Owner runtime key issue-27-local-runtime-b4b5ffc-attempt-01 specification
SHA d11d6f4e5043e3d51a73a0ecf52fc8aa95eb459c6546e46d4136f78013da7972 is published on #27;
exact-head PR28 review5473259439 is recorded. Fixed driverace55beda… runs in user-systemd pipelinev3,
waiting for active build03 and successful actual binary/loader/source/input/local-validation prerequisites.
No guest, scientific pass or policy activation is asserted from reviewed source or a waiting service.

The separate fixed stop controller1d65cc6e…/spec76218e47… is independently reviewed but unlaunched
until first verified capture and exact preflight/source/input/cgroup ownership gates exist. Old keys01/02
were never submitted; stoppedpipelinev2, withdrawn916 overall acceptance and earlier snapshots remain
preserved. Current docs add conditional activation authority: only verified merge-bound LOCAL_ACTIVE and
final acceptance on #27 make expensive execution effective; dated staged/pre-cutover snapshots never do.
Migration stays STAGING/inactive; actual guest/stop/reviewed merge/final acceptance remain pending.


Hosted execution audit found retained expensive full gem5 build/full-system and foundation full-dataset/
native steady commands. The migration branch is adding literal skip guards, preserving every command
and scientific criterion while deferring expensive controls to reviewed local requests. Skipped controls
are explicitly unexecuted, never counted as passed. Lightweight Python/vendor/upstream and small verify/
one-cache native/QEMU correctness stay available. Main is not changed by a branch-only guard before
reviewed merge; no self-hosted GitHub Actions runner or new remote execution channel is provisioned.


Owner CLI documentation now selects the immutable installed runner988 release from the installation
receipt via OPENRX_RUNNER; mutable scripts/local_execution.py remains source reference only.
The fixed stop request is published/readback-verified on #27 at6085930183 but still unlaunched pending
first-capture and exact ownership/preflight gates. Public source/driver exports are sanitized derivatives;
actual local execution binds untouched host bytes. No simulator or stop outcome is inferred from publication.

## Exact final988 actual host controls independently accepted — 2026-10-09 UTC

The immutable runner988cf13f release now has independent acceptance of ten actual host-only lifecycle
controls: receipt/source integrity, expected stop/exit7/hard-kill/OOM failure statuses, retained logs,
exited-launcher/systemd-owned progress, fresh-process duplicate rejection and serialized payload/descendant
drain. Five live property samples use tiny64-MiB/48-MiB OOM, CPU10%, swap0, tasks16 overrides; they do
not measure the unchanged production6G/1G/200%/256 baseline. Observed first FINALIZED before the second
child is empirical only; the actual admission contract is global flock plus drained workload/descendants.

Public evidence is under docs/validation/local-migration-20261009/runner-final988-actual-v3/;
index6cf8987c… binds152 exports, public independent reviewfcb2d305… corresponds to raw978aec36…,
and public replay1348c4c3… corresponds to raw930729e0…. All public export hashes were rechecked before
the additive staging documentation update; untouched originals remain retained. Reviewer schema-error/
correction records are preserved. Whole Codex daemon termination/host reboot and scientific validation
were not performed;55-second finalizer proof remains separate. Migration stays STAGING/inactive,
build03 continues and successful build/loader/preflight/guest/actual gem5 stop/reviewed merge/final
cutover remain pending. No repository history or prior scientific acceptance criterion was changed.

## Verified build03 and actual LOCAL_VALIDATING runtime-only submission — 2026-10-09 UTC

Distinct pinned simulator build03 completed19:37:51.079045Z with returncode0/source_changed[] and
unchanged configf839a59b…. Build-info and loader exit0 are recorded; build-result raw SHA
8eef5987f056d1090d85ece94ee120da5ac35c8828a92b406d119c98730a9c3f identifies retained bytes.
New binary1,036,720,416bytes/SHAe4129f16377346f02b7d68cd508644e5a77cc2daec84a303cc788cb301c05902
is distinct from the unavailable original. Failed build02/source/partial/logs and every safety withdrawal
remain preserved. No original simulator restoration or scientific acceptance is inferred.

Actual preflight19:38:51.228039Z/SHA d2043b278dbb1fabf69b220989414cb8c850ea8a5e56dcfa675dbab44ca31626
bound b4b5ffc source/runner988/request03,41 package pins, exact resources/runtime ELF and
runtime-library profilefda84e15…. Matching migration/runner journals record LOCAL_VALIDATING.
Pipelinev3 submitted runtime-only execution20261009T193937Z-576aa858c033 at19:39:37Z; the last bounded
manager/process observations find it running without accepted complete guest/runtime correctness.
Actual gem5 stop/final outputs, final independent reviews, merged PR and release/cutover remain pending.

Current discoverability docs are reconciled to LOCAL_VALIDATING/NOT YET ACTIVE. Exact preceding37f
STATE/HANDOFF snapshots and16 documentation digests are retained in
memory/handoffs/pre-local-validating-20261009-37f7564-manifest.json; prior SESSION_LOG prefix/historical
handoff/science records are preserved. Conditional instructions now require matching independently
verified acceptance/LOCAL_ACTIVE and explicit #27 release bound to actual reviewed merge/merged-document
audit before expensive submissions; local active state alone is insufficient. Effective-policy hub notice
and final synchronized acceptance remain future steps. No expensive research, milestone closure,
checkpoint resume, remote access or fabricated pass is authorized by this validation transition.

Public local-validating-live-v1/index.json SHA c455b22636766d319a7132c3b330b3322765409d0f4fa6857a7c3886965c2bc1
now binds15 selected metadata/source exports (133,605 raw bytes) using exactly two ordered prefix substitutions.
Independent postbuild raw review8e7452af…/public4989e8cd… accepts build/preflight integrity after new binary,
694 original files,10,933 simulator source entries,41 package/archive pins,43 runtime-library bindings and
exact guest assets were freshly rehashed. Public preflight/build-result digests remain unchanged because
their bytes contained no substituted prefixes. Both bounded production observations and the listener-source
audit retain explicit active-manager/nonperpetual-socket/ancestry/UID limitations. This is not guest/runtime
correctness, actual stop or cutover acceptance. Current docs link actual existing exports; no future proof link
or full-scale authorization was created.


## 2026-10-10T06:10Z — urgent owner-requested migration handoff

Recovered existing migration rather than repeating the build/guest. Complete guest9 and stronger running-firmware stop03 independently accepted; all artifacts/history preserved. Resource-only candidate657b23f1/tests3528d954 independently statically reviewed; 38 focused and297 full cheap tests passed/source stable. Corrected cached CPU-controller availability by controlled user-manager reexecution preservingPID825/all44 running service PIDs. New resource candidate remains uninstalled and final live kernel-limit proof is pending. Migration stays LOCAL_VALIDATING/NOTACTIVE, PR28 draft/unmerged, task27 open; no full-scale science or execution-policy release. Owner requested fast wrap at time limit. Exact receipts/next gates: https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094515657 . Complete originals of STATE/HANDOFF/SESSION_LOG preserved under the new host urgent-memory-before namespace; dated previous log prefix unchanged. Resume from newest migrations/20261009/resume-record-*.


## Verified technical pre-cutover snapshot — 2026-10-10T08:41:07.234399+00:00

Actual technical stateCUTOVER_PENDING since2026-10-10T08:40:10.191934+00:00; transition
proof `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095767946`. New-host expected Ubuntu24.04/Linux6.8.12
and all9 unchanged runtime controls accepted20:04:52Z for193937 execution with zero guest status/empty
framed stderr/completion and hypercalls1/2/3. Exact source/input/model/output and external receipt witness
rechecked; runtime index157ca184… retains39 small exports/744273rawbytes, strict scientific rows/serial
byte-identical and one declared anchored stdout-hostname field redaction. No RandomX matrix/timing/power
claim. Initial200904 stop remains initialization-only; broader stopINDEPENDENTLY ACCEPTED FIRMWARE-SEEN GEM5 LIFECYCLE STOP (868-byte OpenSBI observed before marker; child -9 / wrapper 1; no Linux/runtime/scientific pass or graceful checkpoint/statistics-flush claim)
for execution20261009T202537Z-a1ca7df2cf1c, integrityINDEPENDENTLY VERIFIED: all21 artifacts,890 source entries and9 pinned inputs; partial interrupted outputs preserved, real
evidence `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`. No checkpoint or graceful flush inferred.

Conditional16-doc snapshot remains unreleased at this UTC: actual reviewed merge/D_merged/F/Q/C/R/E/V,
explicit #27 L/release, effective-policy hub/bot and W/Z/externalR_Z/final publication/protocol completion
remain future work. Current science/M1-M5 and all previous assets/failures/safety withdrawals/history are
preserved, preceding688 exact archives `memory/handoffs/pre-cutover-20261010-d40f912-manifest.json and immutable d40f912 history`. Dated docs never
authorize expensive work; only verified matching eligibility/LOCAL_ACTIVE and explicit actual merge-bound
release do. No remote access/autonomous poller/self-hosted runner or scientific milestone closure added.

The [owner resource directive](../docs/LOCAL_RESOURCE_POLICY.md) authorizes aggressive use of all six CPU cores and 16 GiB RAM
with swap where useful, retaining only measured necessary OS/agent headroom. Per-job allocations must
reflect current host load, memory availability and workload parallelism; 14 GiB is a candidate, not a
universal safe limit. Keep one payload slot and all migration/scientific gates.
The old runner988 validation records retain their actual memory and manager-reported 200% CPUQuota.
A later CPU-delegation audit found that historical quota was not kernel-enforced; old property receipts
are preserved and do not prove CPU enforcement. The new CPU delegation configuration is additive.
CPU-delegation evidence: `independently reviewed CPU delegation f12aec1f/67de0d92 and actual runner kernel witness, docs/validation/local-migration-20261009/resource-kernel-20261010/index.json`. The approved owner-local-max-v1 candidate
uses CPU600%, memory no greater than min(14 GiB, fresh MemAvailable minus 1 GiB), optional lower positive
explicit budget, 2-GiB swap, Tasks256 and the same one-slot/45-second stop semantics. Admission must bind
current host metrics and recheck available headroom before launching. Exact new-release/kernel-budget
verification is recorded by the operational profile evidence; it is independently accepted for the exact installed release and tiny live proof below.

The operational implementation must check each payload's actual kernel CPU, memory, swap and task
limits, including effective ancestor ceilings, under admission/resource safeguards before launch. It must
fail closed on unavailable controllers, mismatched constraints, tighter inherited ceilings or lost fresh
memory headroom. Manager properties and controller availability alone do not establish enforcement.
The exact installed operational release enforces these per-payload kernel checks; the independent
resource proof below accepts the observed normal profile. Each future payload is checked again.

Operational resource-profile outcome/evidence: `INDEPENDENTLY ACCEPTED exact runner657 and normal-profile tiny execution20261010T083746Z-6bc7037f04ef: actual CPU600000/100000, RAM5637144576 bytes (5.25GiB selected from measured headroom), swap2147483648, tasks256, six-CPU affinity, no tighter visible ancestors; rc0 and receipt integrity verified. Independent review951622749d40a9bf467e48ee3f6581cc52393569b8db60c87e63d57bee8ee00b; resource-kernel-20261010/index.json`.
Operational release: `runner-v1-657b23f1`, SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`. The verified profile and immutable release are reconciled. This dated preactivation snapshot
retains the expensive-work hold until the explicit merge-bound release.

Resource-policy adaptation: reviewed PR29 additions remain byte-exact; no source/service/state change is made by this documentation preparation.



## 2026-10-10T08:56:25.052452+00:00 — actual LOCAL_ACTIVE / released designated local policy

The actual transition E at `2026-10-10T08:51:50.953900+00:00`, eligibility C, reviewed merge M and merged
document audit are externally published: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817`, `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`,
`f90ac65964bc0138711e4b6d45bcb7e26dff3cc9` / `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`, `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095847617`.
The explicit release L and effective hub/bot H are verified: `https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095873817`,
`https://github.com/jliu67/OpenRX/issues/5#issuecomment-6095882106`, `https://github.com/jliu67/OpenRX/issues/5#issuecomment-6095883184`. STATE/HANDOFF now record
the actual dated LOCAL_ACTIVE state; their prior CP snapshots are exclusively archived byte-exact at
`memory/handoffs/pre-postcutover-20261010-f90ac65-manifest.json`. No historical science/session entry is rewritten.

Operational release/profile: `runner-v1-657b23f1`, SHA-256
`657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b`; actual resource/kernel proof
`https://github.com/jliu67/OpenRX/blob/20c2e7b873d291689b86a9e28cdb06a527467032/docs/validation/local-migration-20261009/resource-kernel-20261010/index.json`. Owner policy additions remain byte-identical, old988
CPU200 manager-only evidence remains historical, and one resource lock/no direct remote access/no resume
continue. Accepted guest9 and separately scoped safe stop evidence stay exact-source/output-bound;
`https://github.com/jliu67/OpenRX/issues/27#issuecomment-6094390003`, `20261009T202537Z-a1ca7df2cf1c`,
`independently accepted firmware-seen gem5 lifecycle stop; child-9/wrapper1, preserved partial outputs; no scientific pass or graceful checkpoint/statistics flush`. Scientific #16/M1–M5 remain open.

This entry precedes its own reviewed postcutover documentation integration, which must be evidenced
externally on #27. At this entry's dated publication, final W/Z migration completion has not yet been published. Consult
live #27 for the later final receipt after this actual merge/readback and independent synchronization review;
this pre-Z statement records its dated history rather than an enduring blocker. No self-review, self-hash, future-merge assertion or expensive
scientific execution is performed by this documentation update.

The resource evidence must bind actual per-payload kernel/ancestor limit checks and fail-closed admission, not merely manager properties or configured controller availability.


## 2026-10-10 — current-status reconciliation, task #33

GitHub-only audit at main `f97b16bb9ff7ce9d8db50f5f97cd6f4d2258a437` verified completed [migration #27](https://github.com/jliu67/OpenRX/issues/27#issuecomment-6095961454) and [cleanup/publication #31](https://github.com/jliu67/OpenRX/issues/31#issuecomment-6099136057). This docs-only work adds current closeout pointers ahead of preserved dated snapshots and corrects stale task/layout summaries. Prior SESSION_LOG bytes and scientific evidence are unchanged. No local checkout, host inspection or scientific execution was performed; no current host-health claim is made.

[Task #33](https://github.com/jliu67/OpenRX/issues/33) records the scoped claim, draft PR, subsequent independent exact-head review, CI and targeted issue/hub handoff. These publication checks must be read there once available, not inferred from this entry. No merge or scientific acceptance is asserted. #8/#10/#11 remain blocked by their distinct measurement/configuration/access prerequisites; #16/M1–M5 remain open. Relation to EXP-002 is discoverability of unchanged existing runtime/hash evidence only; no new experimental result or consequential policy decision is introduced.

## 2026-10-12 — native staging preparation, task #35

Session `codex/native-staging-20261012`, base main `3ee72cc4840b35b7a4e655276f100ab699c8f4cb`.
Owner approved implementing the native staging adapter/tests and publishing a draft PR at 00:21:41 UTC.
Read repository AGENTS, current memory, hub/issue #8, protocol, publication/local/resource policies and EXP-001.
Created scoped preparatory [#35](https://github.com/jliu67/OpenRX/issues/35), with an accepted advisory claim
until 04:24:10 UTC. Temporary /tmp authoring from a pinned source archive only; six omitted vendor manifest
entries were copied from preserved originals after exact digest checks. No retained source or asset was changed.

Added fresh external native build staging with complete logs/tool versions/caches and artifact bindings;
explicit steady/control binary/build/output locations preserve the scientific validator and options.
A focused guard prevents post-reap numerical-group signaling on native-wrapper interruption.
[Evidence](../docs/validation/native-staging-20261012/README.md): 313 lightweight tests exercised, 312 passing
under the sandbox and one existing Unix-socket permission error; its authorized targeted rerun passed.
Final 16 staging fixtures, 171 vendor files, Bash syntax and CLI help checks pass. Heavy native compilation,
upstream/full-dataset controls, controlled measurements and power/PMU work were unexecuted. Parent messaging
returned `thread not found`, so no shared compute-slot approval was received or heavy request submitted.

Different-agent review remains pending for the draft PR. No acceptance, merge, protected-branch push, Git sync,
settings/install/access/credential changes or new agent task occurred. STATE/HANDOFF, EXP-001 and board connect
software preparation to the unchanged open #8/M1 gates. Actual PR/review-state/bot-announcement readbacks and
recoverable retirement archive are recorded on #35 after publication, never inferred from this log entry.

## 2026-10-12 — independently accepted native build and supported correctness

Task #35 / draft PR #36 retains executed source `4a4e30bbbda47cce7713c280d87f1506f7c6f954`. Different agents accepted the source, isolated build `20261012T013303Z-848c58102f71` and supported correctness `20261012T024840Z-8c34147db074`. The [selected public result summary](../docs/validation/native-staging-20261012/accepted-results.json) preserves raw receipt identities and clearly distinguishes non-identifying derivative fields from privately retained host records. Build review checked169receipt artifacts/sixstaged artifacts/sevenlogs; supported correctness review checked44receipt artifacts and exact source/binary/journal bindings.

Observed supported correctness is106upstream passes plus one original conditional skip, six unchanged native cases/four configurations, eight exact references, two17-nonce differential matches,16invalid-CLI checks and four intended duration rejections. Unexecuted configuration coverage remains open. No diagnostic rate is promoted into controlled throughput/power; #8/EXP-001/M1 remain open. Both final receipts verified; descendants drained and native slots released. Earlier optional-telemetry pre-compile failure, no-child admission denial, held packets and permanent request mappings remain preserved; no reserve/admission bypass or scientific/vendor change.

This session reconciles only branch documentation/PR description with actual accepted outcomes and explicit deadline/bytecode examples. Runtime scripts/tests/vendor and all execution-bound inputs remain byte-identical. Temporary authoring only; source/output retention and disabled sync remain intact. Identifying host inventory and exact conditional capability witnesses stay private following automatic-publication review. No workload, source build, performance pilot, simulator run, protected/force push, merge, settings/access/credential/install change or additional model task is performed. Current PR head/checks and a fresh independent documentation-diff review must be published externally on #35 after verified readback. Root currently coordinates any separate payload; this documentation claim allocates no CPU.

## 2026-10-12 — owner-directed X9-class RandomX v2 ASIC scope alignment

Task #39, session `codex/x9-refocus-20261012`, base main `eaa8f1cabc97855c6377d5e2b82ea85f28619ec6`.
The owner asked to narrow the goal and align the mission, current agent information,
repository board, goal issues and message board non-destructively. Temporary /tmp
API authoring updates only current mission/priority sections and appends memory;
prior historical/evidence records and executed source `4a4e30bb` stay unchanged.

The proposal targets an X9-class ASIC adapted to exact v2, retaining v1 regressions.
Reuse pinned RandomX, accepted tools, preserved builds and suitable licensed open
IP; BOOMV3 is a provisional baseline, not X9 silicon. Bounded evidence/profiling
must address v2 main-loop AES versus scalar software AES and memory/FP costs before
any design decision. Broad surveys and X5 reconstruction are deferred without
closing science. Every correctness, controlled-baseline, physical-power,
selected-core and calibrated-model gate remains intact; no competitive PPA claim.

The Bitmain announcement URL returns a JS shell in direct retrieval; its indexed
announcement is not a silicon/topology or measured-v2 report. This proposal adds
no numerical performance target. Distinct GitHub Projects lookup lacks read access;
its existence/status was not verified or updated. Repository docs/TASKS and relevant
issue/hub intent annotations are within the available coordination surface.

No code, source build, scientific workload, active #16 request, settings, access,
credentials or installation was changed. The draft head, exact checks, targeted
issue readbacks and bot hub receipt must be verified on [#39](https://github.com/jliu67/OpenRX/issues/39)
after publication; independent review is required before a later merge. No merge,
scientific acceptance or completed external board update is asserted here.

### 2026-10-12 — audited shared-pool/task-selection correction before PR40 merge

The original nine-file draft remained unmerged while independent audit found that
#2 was still the sole router-ready task despite its prose deferral. The supported
[/openrx block](https://github.com/jliu67/OpenRX/issues/2#issuecomment-6118574647) was
accepted with null claim/unchanged dependencies; #2 remains open and unresolved.
[Source-only #41](https://github.com/jliu67/OpenRX/issues/41) was enrolled ready for
one bounded X9/v2 target-envelope and reusable-IP/AES gap decision, not execution
or final hardware selection. Task #39 was reopened/reclaimed for the correction.

The consolidated document revision fixes live numeric-milestone/ready-pool routing
in AGENTS, README and COMMUNICATION; current TASKS/hub promotions; X5-first hardware/
question priority; and the stale PHASE1-STEADY importer-next-work wording. Substantive
historical hardware questions, milestone acceptance and prior log bytes remain.
The shared pool is Issues plus router-generated labels/bot JSON, with no separate
active JSON/YAML taskpool found. A generic About description is left unchanged.

Previous review at head871 is retained and does not accept this new head. PR40
remains draft pending fresh exact-head review and checks. Distinct Projects access
is still unavailable: CLI lacks Projects scope, connector exposes no Projects
operations, and this task has no browser session; no actual board URL/ID was found.
No account-level board denial, board absence or update is inferred. No credentials,
settings, router/code, workload, active #16 request or scientific gate was changed.


## 2026-10-12 — accepted #16 light-matrix current-status reconciliation

Documentation session `codex/light-matrix-docs-20261012`, task #45, base main
`d284e927f13a331e3079232681760847aa30e32f`. Verified the [public terminal acceptance](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6129532891),
matching released/null-claim #16 receipt and hub bot, and small retained independent
review/acceptance/runner-receipt byte identities without replay or a heavy rehash.
All 39 required controls (31 arithmetic + eight software hashes), nine runtime
controls and terminal completion/integrity/drain gates are independently accepted;
the optional hardware-AES case is skipped. Execution `20261012T032030Z-65cbb4c0cf9e`
retains scientific source `b4b5ffc5c5ee3f59e0e862a6979d265fd410d726`.

This docs-only proposal updates current discovery/board/state/handoff/evidence
pointers and appends this log; original partial/timeout/migration sections and
exact preceding board rows remain as dated history. #16 is not closed: full dataset,
intended-core/SMP, BOOM, timing, power, RTL and M1–M5 remain open. Diagnostic native
work is only tiny-supervisor-fixture preparation/validation, not a launched
benchmark pilot. No protected original, source/input/build/data/receipt, code,
scientific criterion, host setting or resource policy was changed. No workload,
installation, credential/access change, standing clone, sync or merge occurred.
Task #45 records the draft head, exact checks and independent review handoff;
no future review/merge or new host-health claim is asserted by this entry.


## 2026-10-12 — actual native pilot terminal/status reconciliation

Base main `54da42cca7f79f330e0c8b5403d3fe8e589a8a4b`. The owner requested current
issue/hub status corrections without router/claim changes, then one minimal
reviewed repository reconciliation after the actual pilot terminal. A new
[owner terminal record](https://github.com/jliu67/OpenRX/issues/8#issuecomment-6130740969) arrived before running-status publication,
so no transient running-pilot PR was created. #8's source `4a4e30bbbda47cce7713c280d87f1506f7c6f954` execution
`20261012T185152Z-97e747b1f6c4` is independently accepted only as a two-repeat,
one-setting exploratory pilot; formal #8/EXP-001 and M1 remain open.

Additive current prefixes on #8/#16/hub #5 retain complete earlier bodies and
unchanged states/labels/claims. This one docs-only proposal updates the P1-04 row
(its exact prior row retained as history), current discovery/state/handoff and
a selected evidence note, preserving every prior log byte. #16's accepted 39+9
light result/source b4b5ffc and optional AES skip remain distinct from its broader
full-dataset/intended-core/SMP gates. M1–M5, power/PMU, selected-core/calibration
and RTL requirements are unchanged. The long pilot aggregate has no independent
trusted oracle; controls and repeat determinism are its declared evidence.

The explicit owner instruction preserves router/claim state, so no new lease or
transition was posted for this isolated documentation branch; pilot-owner review/
source/receipt ownership is respected. No workload, heavy rehash, local build/test,
install/settings/auth change, standing clone, sync, source/receipt rewrite or merge
is performed. Current draft head/checks and different-agent review belong in the
#8 documentation handoff; no future review/merge or fresh host health is asserted.

## 2026-10-12 — first v2 AES execution implementation, task #48

Executed the owner's 20:49 UTC directive within one required component, using an isolated feature workspace from main 10482be0. Added pinned BSD secworks S-box/inverse IP, exact AES round glue, shared/four-lane F/E mixing, VM-completion/F-writeback integration with v1 XOR path, standalone unchanged-software oracle, focused tests and synthesis CI. Local round/mixer/integration and both actual mapped-netlist tests pass; request interval 17→5 cycles and generic cells 39,824→83,975. No physical timing/area/power or full-hash claim.

Official Icarus 11.0/Yosys 0.9 packages resolved missing tools. Retained coefficient failures, `stat -json` compatibility failure and 2-GiB cgroup OOM. Reused passing shared-lane results; focused four-lane synthesis/netlist retry passed with identical 19 source bindings and vectors under checked CPU 600%, RAM 4 GiB, swap 512 MiB, tasks 128. Retry peak RSS 2,029,500KiB, CPU 100%, runtime 183.873s; single worker matches tool parallelism, and global slot/cgroups are released. No additional baseline batch, workload/vendor/receipt mutation, settings/access change, standing editable clone, Git sync, protected push or merge. [EXP-003](../experiments/EXP-003-v2-aes-rtl.md) retains raw/public artifacts and reproducible commands. Publish draft feature PR, request independent exact-head review and retire temporary authoring at handoff.

Correction within the same new-work review: draft 603b01e7's raw-boundary v1 identity expectation was wrong; upstream performs F XOR E. Preserved that source read-only and all original outputs, then corrected a fresh feature workspace, added pinned-software XOR vectors and regenerated integrated RTL/netlist checks and resource counts. No earlier scientific receipt was rewritten; superseded artifacts remain accessible.

Final corrected attempt10: complete oracle/RTL/synthesis/netlist flow passed in 346.892s, with one worker and verified 4-GiB/600%-CPU/512-MiB-swap/128-task limits. Integrated top cell counts 40,848/84,999 (flops 1,545/1,543); v2 request cycles 17/5 unchanged. Peak RSS 2,032,356KiB. Software XOR vectors and per-program-iteration trigger are explicit; initial sources/data retained. The same review will bind final head and revised evidence. Owner’s 21:24 UTC repo alignment request is included in this feature: manager-led build-first delivery, reusable IP, blocker-only timeboxed research, minimal overhead, real correctness/synthesis/integration checks and preserved genuine scientific gates.

## 2026-10-12 — ordered scratchpad iteration tail, task #50

Created a separate temporary feature branch from immutable 9a3271d5. Added ordered 128-bit R-before-F stores, overlap scheduling, final-F/cursor completion and partial-reset semantics. A verbatim pinned iteration body plus real BytecodeMachine drives 128 controlled differential fixtures (64 v2/64 v1) with virtual dataset lines; source/vendor/core 19 identities stay exact. All four RTL variants compare 1,024 transfers, 32 alias cases and the full 2 MiB memory; both delivered mapped netlists pass. Intervals 25→21/shared and 13→9/four-lane; generic cells 46,510/90,661 and flops 2,605/2,603 exclude physical SRAM. Full successful attempt 03, generated source notices, traces/netlists and prior development outputs retained. One checked 4 GiB/600%-CPU payload, peak RSS 2,252,132KiB; slot/cgroup released. No PR49/main changes, installations, extra agents, full dataset/hash run, paid compute or security changes. Draft new feature handoff requires independent review; next integration requires concrete core/register-file and ordered memory, with timing/PPA still unmeasured.

## 2026-10-13 — iteration memory/execute integration, task #52

[Task #52](https://github.com/jliu67/OpenRX/issues/52) implements entry loads,
exact signed conversion, tagged execution/memory traffic and dataset feedback,
reusing the independently accepted PR49/51 code now merged at main 5a688512.
[EXP-005](../experiments/EXP-005-iteration-engine.md) and [interface](../rtl/engine/README.md)
record eight passing RTL modes and four passing actual mapped modes. Each mode
checks 32 native differential iterations (16 v2/16 v1), 2,880 bytecode reads,
720 bytecode stores, 256 tail writes, eight aliases, 16 chained contexts, all
2 MiB memory, stale/stalled traffic and three reset aborts. The separate signed
conversion differential passes 4,096 vectors across four rounding modes.

LANES=4 entry clocks are A/B/C=1,056/544/480 across 32 fixtures: parallel conversion
saves 16 per iteration; equal-line coalescing saves four reads/eight clocks per
alias under the stated minimum-latency private-memory contract. Generic A/C
counts are 126,810/130,589 cells and
7,733/6,704 flops. Arithmetic kernel, instruction fetch,
physical SRAM/cache and dataset remain external; these are controller/replay
cycles, not calibrated PPA or hash throughput.

One kernel-verified six-CPU/4 GiB/512 MiB-swap/128-task payload used one worker,
peak RSS 2,630,284 KiB; source/vendor/core/tail inputs and all
original assets remain retained. New source/attempts are archived and temporary
authoring retired read-only at handoff. The first reset testbench sampling failure
is retained with its correction. Next: one independent review of this new draft
feature. Reproduce with `python3 scripts/test_iteration_engine.py --output
/tmp/openrx-engine-fresh --synthesize`, using the global slot and fresh admission.
No code merge is authorized. Earlier dated component/status entries below retain
their original bytes; live task/PR records supply subsequent review and CI status.


## 2026-10-13 — Icarus12 finish diagnostic correction

Initial draft head a04b9163 has the complete passing local RTL/mapped result
below. Its hosted converter test also passed, but Icarus12 appended a successful
finish diagnostic that the harness's exact-whole-log check rejected. The focused
[compatibility correction](../docs/validation/iteration-engine-ci-compat-20261013/README.md)
requires the same exact PASS record plus successful exit. All eight corrected-driver
RTL modes pass with identical logs; all six hosted native fixture files match.
Every RTL/C++/vendor input and original mapped result remains unchanged. The full
hosted flow must pass on the final draft tip before one independent new-work
review accepts it; no merge is authorized. Earlier original evidence is preserved.


## 2026-10-13 — P2 stalled read grant correction

[PR53 review](https://github.com/jliu67/OpenRX/pull/53#pullrequestreview-5497704738)
blocked original bd193092: an arriving write could retract a scratchpad read
already held under backpressure. The same author reproduced the exact failure
on unchanged original RTL, preserved its source/test/input hashes/fatal log,
and added one retained read-grant bit. Fresh competing requests still give
writes priority; an already presented read retains valid/address/tag until
acceptance and blocks writes until the response is consumed. Reset/new descriptor
clears the grant; architectural return cannot bypass a pending grant.

The new directed regression runs v1/v2, overlapping requests in both orders,
12 read-stall clocks, eight write-stall clocks, six response-stall clocks,
six stale-generation drops and reset of a held grant. It verifies five reads,
three ordered byte-strobe writes and committed-byte persistence. It fails the
rejected RTL and passes all four RTL configurations plus both actual A/C netlists.
The eight native RTL and four native mapped modes remain byte-identical to the
original serialized replay; every native/vendor/AES/store-tail input is unchanged.
Entry totals A/B/C=1056/544/480 and native replay cycles are unchanged.

Corrected generic A/C counts are 126,820/130,599 cells and
7,734/6,705 flops. Compared with the rejected source,
deltas are +10/+10
cells and +1/+1 flops.
The original failing overlap sequence has no valid cycle result to compare.
[Focused evidence](../docs/validation/iteration-engine-read-grant-20261013/README.md)
binds raw failures, corrected source, commands/versions, actual netlists and
resource receipts, retaining every earlier source/result/archive/review.

The initial 4 GiB candidate did not fit fresh headroom. Standalone A synthesis
used kernel-verified CPU600%, RAM3 GiB, swap512 MiB and Tasks128, after a fresh
1 GiB host reserve check; measured memory pressure/swap increased wall time
without an OOM or CPU-quota throttle. Freshly regained headroom admitted C at
4 GiB. Mapped-only checks used 1 GiB based on measured compile/simulation RSS.
All six CPUs remained available, one worker, global slot serialized. Detailed
resource witnesses stay private; sanitized measured limits/peaks/elapsed/swap
are public. Source and attempts are verified/archived and retired read-only at
publication. Prior sources/receipts are preserved; no extra tasks/agents,
install/access/settings change, repeated baseline, force push or merge.

Next: all final-head hosted checks, then the same reviewer's focused delta review.
This author handoff does not establish acceptance or authorize merge. Arithmetic
kernel, physical memories, calibrated PPA and full-hash requirements remain
external. Earlier evidence below records its original source and is retained.


## Native integer execution — task54, 2026-10-13

Implemented actual native fetch/decode and eleven integer families behind unchanged
accepted controller/converter/AES/store tail. Unknown raw operations terminate with
held tagged error, preserving committed-prefix semantics; no silent approximation.
The reproducible driver compares2,560 actual hardware instruction retirements and
all2MiB against unchanged native semantics, with v2 primary/v1 regression. Eight
RTL and eleven actual mapped modes pass, including unsupported/error/reset and
raw-field/all-rounding-mode/held-return coverage. Fast/shared clocks9,524/9,760 and
26,712/26,948 differ by236, one per IADD_RS. Generic fast/shared kernels25,885/1,727
and25,925/1,792; complete default top154,145/7,921. No full hash or physical PPA.

All protected inputs/source/results/receipts retained. Initial transport fixture
sampling failure preserved with source/fatal; RTL unchanged by its settle repair.
One serialized5GiB/six-CPU payload completed29m20s, peak cgroup5,080,702,976 bytes,
no OOM/swap/quota throttle. Focused transport and final RTL used measured1GiB.
Sources/attempts archived, authoring retired read-only at handoff. Concise current
summary corrections share this code PR; archived/vendor links are not rewritten.
Next: final-head hosted checks then one independent new-work review; no merge
approval. [Evidence](../docs/validation/integer-execute-20261013/README.md) binds the
complete artifacts and license/source provenance. Earlier stages remain historical.


## Native multiply and branch handoff — task #56, 2026-10-13

[Task #56](https://github.com/jliu67/OpenRX/issues/56) /
[EXP-007](../experiments/EXP-007-native-multiply-branch.md) extends independently
accepted, unmerged PR #55 at `2b14e4f9` on a separate stacked draft. All 19 integer/branch
families (161 raw values) now execute actual native semantics; all 95 FP/CFROUND
values still return explicit held errors. Nine RTL and eleven applicable mapped
modes pass against unchanged native arithmetic/compilation/execution, including
2,736 retirements, native targets/dynamic PC, complete 2 MiB, stores/chains, held
traffic/stale tags/error/reset and unchanged raw-FE/all-rounding-mode transport.

Direct/iterative clocks are 12,036/30,596 ideal and 29,502/48,062 stalled, exactly
32 extra per each of 580 products. Actual unit cells/flops are 25,723/81 versus
5,528/537; reciprocal 1,374/153. Complete default mapping is 189,296/8,396.
Iterative full-top synthesis is absent; its mapped arithmetic units run with RTL
controller/executor. Fixture clocks/generic cells do not establish physical PPA
or full-hash performance. [Licensed evidence](../docs/validation/multiply-branch-20261013/README.md)
binds exact source/commands/tools/fixtures/logs/netlists/failures/resources.

One serialized worker used actual CPU 600%, RAM 6 GiB, swap 512 MiB, Tasks 128,
six-CPU affinity and fresh 1 GiB OS reserve; measured full-run peak cgroup 5,853,196,288 bytes,
peak swap 0 bytes, no OOM/limit hits/quota throttle. Payload/descendants
drained; source and complete attempts are archived/verified and retired read-only
at handoff, preserving execute bits. All prior pinned/bound assets remain. Strict
coverage rejected the first fixture before DUT tests; explicit rotations repaired
coverage without changing production RTL. A terminal disconnect stopped the first
driver at a progress print after successful synthesis (rc120/BrokenPipe). The
three remaining mapped tests reused the exact netlist in a fresh checked 1 GiB
payload (rc0), peak 1,013,276,672 cgroup bytes and zero swap/OOM/limit hits/CPU
throttles, with durable console output and no synthesis rerun. Both original
failure and completion evidence are retained. Next: exact-head hosted checks and one
independent review of this new extension. No merge is authorized; PR #55 remains
draft/unmerged. FP, complete VM/hash, physical memories, selected core and calibrated
timing/power gates remain open. Earlier summaries retain dated publication context.



## Exact native floating execution handoff — task #58, 2026-10-13

[Task #58](https://github.com/jliu67/OpenRX/issues/58) /
[EXP-008](../experiments/EXP-008-native-floating-execute.md) extends independently
accepted, unmerged PR #57 at `d62c4495`, preserving both reviewed PR #55/#57 heads.
Unmodified licensed HardFloat1/8086-SSE supplies exact binary64 add/subtract/multiply;
FSWAP/FSCAL and native v1/v2 CFROUND/masks/DAZ+FTZ retain their exact semantics.
All 246 supported raw values execute; ten division/sqrt values still return held
errors. Complete VM/hash, selected core, physical memories and calibrated PPA remain open.

Twelve RTL and eleven applicable mapped modes pass: 19,968 full native primitive
vectors per variant, explicit balanced 3,840 mapped corner vectors, 2,928 actual
R/F/E/mode retirements, targets/dynamic PC, 872 arithmetic FP/584 CFROUND operations,
338 loads/104 stores/64 tail writes, four chains/aliases and all 2 MiB. All arithmetic
modes/64 CFROUND rotations/v2 apply+skip, unsupported/errors/reset/stale traffic,
atomic FP cancellation and unchanged raw-field/held-return transport are covered.

Shared/parallel units are 26,522/49,363 generic cells and 571/156 flops, with five/one
clock response latency. Integrated clocks 16,604/13,116 ideal, 33,574/30,086 stalled
differ by 3,488, exactly four per arithmetic FP operation. Complete default mapping
is 260,110/9,826. Shared whole-top and expanded old integer-sharing
matrices are absent; these controlled clocks/generic mappings are not physical PPA.
[Complete licensed evidence](../docs/validation/floating-execute-20261013/README.md)
binds inputs/commands/tools/fixtures/netlists/failures/resources/verified archives.

Original/pinned source/build/data/receipt assets remain retained. All 171 RandomX,
eleven HardFloat and 19/17/22 accepted component bindings are unchanged. Two own
wrapper-boundary failures and strict five-raw-value fixture correction are retained;
no criterion was relaxed. Twelve RTL modes and both actual mapped units passed
before complete top mapping reused their frozen code/fixtures. Source and complete
attempts are archived/verified, retired read-only preserving execute bits at handoff.
Unit/integration budgets were checked 2 GiB/6.5 GiB, CPU 600%, swap 512 MiB/2 GiB, Tasks 128,
six CPUs/one worker/fresh 1 GiB reserve; peaks 1,114,402,816/6,979,321,856,
integration swap 1,136,898,048, limit events 1202, no OOM/kills, CPU throttles 0.
Both payloads/descendants drained. Next: exact-head hosted checks then one independent
review of this new stacked draft. Neither reviewed parent nor new code is authorized
to merge. Earlier summaries retain dated publication context.



## Native division and square root — task #60, 2026-10-13

[Task #60](https://github.com/jliu67/OpenRX/issues/60) extends independently
accepted, unmerged [PR #59](https://github.com/jliu67/OpenRX/pull/59#pullrequestreview-5501107360)
at `ce788d11285c901b52fd3cf0b450489d13b3f2f5` on a separate stacked draft.
All 29 native instruction families / 256 raw encodings now execute, including
masked FDIV_M and FSQRT_R. Reviewed PR #55/#57/#59 and main remain unchanged.
New code requires independent review; no merge is authorized. Complete VM/hash,
selected core, physical memories and calibrated timing/power remain open.
[Design](../rtl/execute/DIVSQRT.md) and [EXP-009](../experiments/EXP-009-native-divsqrt.md)
bind reproducible tests and actual mapping. Earlier component summaries retain
their dated source/evidence context; historical subset test drivers require their
accepted frozen heads. Current reproduction uses `scripts/test_divsqrt_execute.py`.

Twelve RTL and eleven applicable mapped modes pass: 13,312 balanced native
primitive vectors per scalar/shared/parallel variant, 2,560 balanced mapped
corner vectors, 2,856 native retirements including 152 divisions / 146 square
roots, 418 loads / 82 stores / 64 tail writes, four chains/aliases and all 2 MiB.
All rounding modes, DAZ/FTZ, IEEE exception bits, masks, held/reset/stale behavior
match. Shared/parallel divide-sqrt units are 8,690/12,942
generic cells and 779/558 flops. Controlled integration clocks
are 45,671/28,443 ideal and 62,637/45,409 stalled; shared adds 17,228 clocks.
Complete default mapping is 274,346 cells / 10,504 flops.
Operand latency is variable; these fixtures and generic gates establish no physical PPA or full-hash throughput.



## Icarus 12 compatibility correction — 2026-10-13

The initial PR #61 hosted run rejected the original HardFloat duplicate scalar
`wire sqrtOpOut` declaration: its ANSI output port already declares that net.
The current 53-entry harness generates a separately labeled, checksum-bound
compile view replacing exactly this redundant declaration with an empty CRLF
line. Every other byte and full license notice is preserved. All twelve upstream
files remain unchanged; Yosys continues to synthesize the original source.
Twelve local compatibility RTL PASS records and nineteen native fixture files
match the original run exactly. The hardware/native/oracle/stimulus sources and
eleven original mapped results are reused; no mathematical change or repeat
whole synthesis is involved. The first hosted failure's complete 46-file archive
is retained and verified. Fresh hosted validation and independent review are
required at the corrected PR head.

## 2026-10-13 — Task62 native program-sequence initial draft

Temporary staging extends accepted PR61 with native initialization/program-loop control, independent native oracle/provider and focused tests. Four measured short v1/v2 pilots pass; the full v2 run and new control/mapped checks remain pending. Original sources/failures preserved; independent review and no-merge gates remain. See [EXP-010](../experiments/EXP-010-native-program-sequence.md).

## 2026-10-13 — Task62 complete native program-loop validation

Full native-v2 8×2048 RTL and nine current RTL/nine mapped modes pass; exact code, outputs, sources, failed fixtures and resource receipts retained. Parent merges are a separately authorized reviewer action; this workload stays pinned. [EXP-010](../experiments/EXP-010-native-program-sequence.md) and [evidence](../docs/validation/program-sequence-20261013/README.md) carry exact counts/tool scopes/limitations. New independent review of PR63 remains required; no merge authorization.

## 2026-10-14 — Task69 reciprocal preparation candidate

Owner-approved bounded implementation and complete serial validation use temporary source/no Git sync. Eight model tests, 48 native iterations/12 reloads, 11 RTL/four mapped checks and three intentional invalid elaborations pass; final unexpected failures 0, complete-pipeline performance gate skipped 1. Four failed attempts and all original assets retained. Measured active reciprocal cost is 66 clocks (1 request +65 wait), with preparation 70356/execution savings 281424/net 211068 on the directed corpus. Kernel CPU 600%, RAM 4 GiB/swap 512 MiB/Tasks128/six affinity and no tighter ancestors verified; full receipts/peak in [evidence](../docs/validation/prepared-reciprocals/README.md). Main 8f,65 exact4f,68 exacta4 untouched. [EXP-013](../experiments/EXP-013-prepared-program-reciprocals.md) keeps complete-pipeline/physical PPA acceptance open. Independent review next; slot released, claim/review receipt indexed on task #69, no own merge.


## 2026-10-14 — Task69 bounded CI source-binding successor

PR70 original head3ce88 passed foundation/preflight/model checks but hosted run38502375710 rejected an intentionally changed executor digest before native compilation. Preserve the full failed log/original four-file ZIP and every original acceptance manifest. Fresh advisory CI claim accepted after append-only reopen; bounded successor declares exactly two executor old/new bindings and tests rejections/default0/retained server evidence. All219 scientific input bytes remain unchanged; inherited full native program-sequence/synthesis replay is deferred, not passed, and needs fresh authorized serial server admission. Final exact-head independent review remains required; no merge or full-hash acceptance. [Evidence](../docs/validation/prepared-reciprocals/README.md#hosted-source-binding-correction).

Bounded successor payload passes12parent rejection tests/8accounting tests/source-evidence guard in837ms, peak21762048bytes, swap/limit/OOM/kill/throttle0. All219scientific and six new CI input bindings verified against separately frozen sources; complete failed hosted and successful check outputs archived. Slot released.


## 2026-10-14 — Restore PR70 actual program-sequence regression gate

The historical head1345 source-only route skipped native/mapped integration.
The corrected gate unconditionally runs the existing --synthesize regression;
binding/rejection checks remain additional guards. Fresh serial server validation
passes9RTL/9mapped/4invalid/3actualsynthesis, with exact mapped/RTL PASS equality.
All219 original science inputs and accepted manifests/old-new binding digests stay
unchanged. Existing8×4 native v1/v2 tests, default8×2048 control contract and bounded
whole-top native gates are separate scopes; no --full-v2 rerun or full-pipeline
performance acceptance. Sources/complete outputs and superseded binding-only CI
artifacts are preserved. [Evidence](../docs/validation/prepared-reciprocals/README.md#restored-integration-gate--2026-10-14).
Independent exact-head review remains required; no merge. Compute slot released.

## 2026-10-13 — task #64 native register-file hashing

Implemented the fixed 256-byte digest and buffered seven-seed program chain above accepted 990f368, with all 69 accepted inputs/171 native files and five IP originals unchanged. Server 18 RTL / 17 mapped modes pass; actual mapping and complete archived outputs are bound in [evidence](../docs/validation/regfile-blake2b-20261013/README.md). Preserve all original negative/preparation/harness/frontend/cell-model failures. At initial publication, hosted checks/new independent review remain pending; subsequent results are recorded on task #64 and the draft PR. No merge. Temporary authoring will be archived/frozen after exact draft publication, retaining original sources/assets and disabled sync.

## 2026-10-13 — task67 scratchpad finalization preparation

Resumed actual engineering after the completed owner-requested repository sweep,
which remains preserved separately. Claimed #67 above exact PR65 head4f095fc in
a temporary per-task source, with no Git checkout/sync or retired source restore.
Added native scratchpad scanner/finalizer, unchanged-IP/native oracle and fixtures,
control bench/driver, and dependency-trigger/reproduction clarifications. Eight
focused preparation checks pass; native/HDL/synthesis and independent review are
pending at this snapshot. Shared compute requested: one worker, CPU600%,4GiB RAM,
512MiB swap,Tasks128,six-CPU affinity, fresh1GiB reserve/global lock; execution needs
actual admission and kernel/ancestor checks. No public PR65 review or merge occurred.

## 2026-10-14 — task #67 local validation and publication preparation

One manager-admitted serial service passed 41 RTL / 19 mapped modes, 14 native/Python
cases, four balanced full 2 MiB trials, six native malformed-input guards and four
invalid hardware elaborations. Actual kernel CPU600%, RAM4GiB, swap512MiB,
Tasks128 and six-CPU affinity were checked with fresh reserve/global lock;
measured cgroup peak 1,902,161,920 bytes. Complete source/output bytes and original
modes were archived, verified and retained read-only with execute bits. Original
duplicate-module elaboration failure remains preserved. Declared metadata/CI
successor corrections pass 11 focused tests; scientific sources and commands stay
exact. [Evidence](../docs/validation/scratchpad-finalization-20261013/README.md) separates local execution, successor checks,
and pending hosted/independent verification. No main/parent change, PR65 public
review publication or merge occurred.

## 2026-10-14 — Task69 combined PR70/65/68 reconciliation

Owner resumed working engineering. Advisory claim6176527891 accepted through
23:26:09UTC for exact PR70 head35c and main5f; temporary server feature worktree
only, no standing mirror or Git sync. Merge --no-commit --no-ff retained both
parents; four memory conflicts were resolved by retaining both original sections.
Original conflict stages, tree identities, manifests and all earlier archives are
preserved. No RTL/math/native/oracle change is intended. Strict additive combined
bindings and affected actual execution/seed/finalization regressions are pending
at this snapshot. No historical pass is relabeled combined; no skip is a pass.
Actual runs require fresh kernel/ancestor/headroom and the existing nonblocking
global lock. Publish only a nonforce successor on PR70 for independent review;
no selfmerge or physical-efficiency acceptance. Unrelated sweep findings are parked.


### 2026-10-15 — interrupted PR70 integration recovered

## 2026-10-15 — PR70 combined-source recovery closeout

[Task #69](https://github.com/jliu67/OpenRX/issues/69) reconciles reviewed PR70
`35c2cae61092107acb2c684bbca308aca8fb280b` with merged main
`5f28dd4363504ecf33a8f10451c53405773c564f`, preserving both parents and accepted
PR65/68. Strict combined bindings retain every historical manifest, all 219
original preparation inputs and 73 original sequence-regression inputs. Actual
native/mapped CI gates remain unconditional.

Verified server closeout covers 362 unit tests, seed18RTL/17mapped/3synthesis and
finalizer41RTL/19mapped/3synthesis, with native bytes and mapped/RTL records exact.
Original runner20261014T194137Z-8451bfb57fac remains PROCESS_FAILED: after unit/seed
commands returned0, an external wrapper KeyError:status prevented finalization.
Recovery20261015T194652Z-334cfc1d0428 ran only missing finalization from the same
3309-file frozen source. Both full receipts, sources, outputs and failure survive;
composite verification never relabels the original wrapper successful.

[Combined evidence](../docs/validation/prepared-reciprocals/combined-20261014/README.md)
binds commands, native/negative cases, complete archives, source/publication deltas
and resource checks. Both payloads used actual600%CPU/4GiBRAM/2GiBswap/Tasks256;
observed stage peaks1,097,007,104/1,921,708,032bytes, zero recorded swap/limit/OOM/
throttle events. Inherited simulation commands are sequential; no wall-time
throughput inference follows. Original prepared and sequence results are retained
exact-input proof, not newly rerun suites. Full-v2/full prepared pipeline, actual
dataset, calibrated timing and physical power remain unaccepted.

Next: hosted verification and a new independent review of the final exact draft
[PR #70](https://github.com/jliu67/OpenRX/pull/70) head, recorded on task #69. No own
merge or new milestone is authorized. This interrupted integration closes here;
recurring checks remain paused. Earlier dated sections retain their original context.


## 2026-10-16 — first default connected native-v2 RTL hash

Task71/draftPR73 source c96e96ab passes 8×2,048 with actual native light dataset
values, all iteration states/bytecode events, seven hardware seeds, every 2 MiB
program boundary and native final32-byte digest. Full immutable execution
20261016T010320Z-b2c8ed47ab4c exits0; integrity verification passes; 4,106 complete
public source blobs/sizes/execute bits match its frozen source. Total known
hardware/transport clocks40,975,538; provider device cost, frequency, watts and
area remain unknown. Initial duplicate-module compile, failed tool symlink
finalization and unadmitted tool-reuse attempt remain retained unchanged.
Serial successor execution20261016T014629Z-8c43e1ea115d passes four8×2 hash
modes, six cancellations, eight matching errors, capacity/reset and31 unit checks;
receipt integrity verifies. A fresh Icarus capacity-only check separately covers
four-state behavior. Source deltas distinguish this successor from full c96; the
default full hash was not rerun on it. Independent final-head review remains.
[Experiment/evidence](../experiments/EXP-014-connected-v2-lifecycle.md). No own merge
or architectural commitment. Earlier stopped/audit work is not resumed.

## 2026-10-16 — task #72 executable feasibility model

Implemented stdlib trace/ledger/locality extraction, source protocol calibration,
dependency/resource-constrained scheduling, scratchpad/dataset/concurrency and
whole-wall-energy necessary bounds. Reused accepted full c96 native-dataset
and detailed short successor evidence, preserving all originals. Initial parser
failure exposed missing nested transitions in the older sparse observer; those
CSV timings remain null and accepted per-clock counters are explicitly separate.
Corrected admitted extraction and compact reproduction both verify; all 488
comparison rows and sensitivity artifacts match byte-for-byte. Eight scalar
protocol windows have zero residual with measured FU spans explicit; 58 focused
tests and 171-file vendor integrity pass. No new RTL/native simulation, physical
PPA, alternative full-hash timing or target acceptance is claimed. Delivery uses
a feature draft PR for independent review; no merge, settings, credentials or
spending change. Next: configurable context-tagged blocking hardware and actual
readiness/resource instrumentation before more aggressive issue/queues.

## 2026-10-16 — task #72 focused recovery and draft publication

Recovered clean model head46fa0737/tree1059a182 above mainf13e5b5 in a separate
temporary feature branch; original author workspace and every output remain
unchanged. Replaced embedded-hash recognition with actual full-evidence and
12-file fixture digest binding; untrusted inputs preserve provenance and stop
before accepted-run comparisons. Added transaction-rate, bank-port and explicit
controller-service constraints to the rejection gate. Missing physical/service
terms stay unresolved. Focused independent review found no remaining blocker in
these two fixes and verified all trusted bindings; 16 targeted tests pass.

All67 architecture tests pass. Admitted compact execution
20261016T065700Z-fe5c0263613b exits0 and integrity verifies: 488 comparison rows
and eight scalar equations remain byte-identical, while sensitivity gains only
three unknown gate fields. Actual prelaunch CPU600%/RAM1GiB/swap2GiB/Tasks256;
one worker, 217.60s, child peak RSS32,244KiB. During-run samples show no throttle
or memory-limit/OOM event; no final cgroup/whole-host utilization measurement.
No full trace, native build, RTL/hash simulation, architecture selection or
physical/alternative full-hash acceptance. Original artifact index still verifies.
The [additive recovery evidence](../docs/validation/architecture-feasibility-20261016/recovery/README.md)
binds tests, inputs, code and receipt. Draft PR and exact head are handed off on
task72 for independent final review; no merge or standing mirror/sync is created.


## 2026-10-16 — hardware initial AES fill implementation and bounded proof

Implemented on temporary feature branch above `b8cd0707`, preserving originals. Native `fillAes1Rx4` semantics reuse proven AES RTL, with transaction handshakes, held seed, accepted write persistence, INIT ownership/generation and post-fill seed integration. Independent static review caught/fixed same-cycle seed response acknowledgement before actual connected tests. Standalone execution `20261016T082316Z-86c364941cf5` passes 12 native / 30 RTL / four full 2 MiB / 18 bounded mapped checks and capacity guards, maps actual default 36,168 cells / 547 flops / zero latches and integrity verifies. First vendor-snapshot preflight failure `20261016T082210Z-a670422823b2` is retained; fresh snapshot restored six unchanged export-ignored assets. Connected execution `20261016T084736Z-e61113d5b84c` passes bounded 2×1 ideal cross-backend / stalled plus focused cancellation/errors and integrity verifies. All 37 cheap unit checks pass. No full 8×2,048 repeat or physical claim. New ideal initialization 131,076 replaces old 131,074 only; derived historical total 40,975,540 is not a new full measurement. Complete [evidence](../docs/validation/initial-scratchpad-fill-20261016/README.md) and exact code 825/e22 remain retained. Draft publication / final-head review outcome follows separately; no merge requested. Hub5 remains forbidden.


## 2026-10-16 — initial-fill publication authorization resolved

Explicit owner engineering/repository authorization permitted one retry of the scoped issue action. It created [task #75](https://github.com/jliu67/OpenRX/issues/75); claim session `codex/initial-fill-20261016-0915` and comment6212225342 record bounded ownership. The already accepted local headfe2/e22 sources and all execution outputs remain untouched. The publication successor updates only issue/publication metadata; read task75 for the final public draft head, independent review and hosted gates. No new payload, full-hash performance/physical claim, hub5 post or merge is part of publication.

## 2026-10-16 — native AES program generation candidate

Accepted main is `548ed2d31fe6be7d2edc2036961dc7745e9e7219`: PR #76 merged after exact-head review and all applicable checks; [task #75 closed completed](https://github.com/jliu67/OpenRX/issues/75#issuecomment-6213667417). Above it, [EXP-017](../experiments/EXP-017-native-program-generation.md) implements pinned fillAes4Rx4 with existing AES IP and explicit `HARDWARE_PROGRAM=1`; default `0` preserves historical reproduction. [Evidence](../docs/validation/program-generation-20261016/README.md) binds standalone `0d70bf0`, connected `8100bee`, retained outputs and verified receipts.

The 15 native, 44 RTL and 24 bounded mapped checks pass, including ten complete 3,200-byte profiles and 800 ideal generator clocks. Generator-only mapping is 36,836 cells, 540 flop cells and zero latches, excluding the image buffer, preparation and execution. Connected 2×1 ideal/stalled/focused recovery and 45 unit checks pass. Complete ideal four-state/two-state ledger, trace, digest and native corpus agree. Measured totals are 534,012 ideal and 1,583,537 stalled clocks; two program generations account for 1,606, including metadata overhead. Live software generation calls are zero; native generation is assertion-only.

Input BLAKE2b and native Light dataset/device service remain host/device gaps. No new default full hash, complete recovery matrix, full mapped Program/connected engine, physical PPA or architecture acceptance follows. Independent bounded review is preserved; exact publication-head review and hosted checks are separate draft gates. Parent handles normal merge gates. Ownership was checked for duplicates; separate task-issue registration remains pending. Hub #5 remains blocked and task #72 board notices are handled separately. Earlier dated records preserve their original context.


## Bounded hardware input BLAKE2b — 2026-10-16

Above accepted main `eed374b28e9e2efa71bc16f5ba15e999e2940415` (merged PR #77),
[EXP-018](../experiments/EXP-018-bounded-input-blake2b.md) and
[evidence](../docs/validation/input-blake2b-20261016/README.md) record the 0–80-byte
input BLAKE2b-512 wrapper using the unchanged accepted compression core.
Explicit `HARDWARE_INPUT_HASH=1` requires hardware fill; default zero preserves
historical reproduction. Unsupported lengths 81–127 return held errors.

Standalone validation passes 614 native vectors, 18 RTL and 16 bounded mapped
modes; actual wrapper/core mapping is 38,538 generic cells, 3,753 flop cells and
1,024 inherited latch cells. Result availability is 28 modeled clocks. The
connected 2×1 composite passes ideal cross-backend/stalled/reference checks,
input-stage cancellation/held error and both-backend boundary prefixes, plus
56 unit checks. Ideal/stalled totals are 534,040/1,583,565 clocks; the disjoint
input stage is 30 clocks, with zero live input/fill/program provider calls.
Original failed attempts remain failed; exact sources, two boundary-helper
settling delays, raw receipts and retained-subresult reuse are explicitly bound.

Native Light cache/dataset and physical device service remain external/untimed.
No new default 8×2,048 run, whole-engine mapping, physical PPA or architecture
selection follows. The feature PR records independent exact-head review, hosted
checks and normal merge/postmerge outcome. Existing task #71 records execution
requests; no new issue, hub notice or standing Git mirror is created. Next
concrete component is one prepared native superscalar-program executor; cache
export/service and autonomous setup remain separate work. Earlier dated sections
retain their source-specific historical context.


## 2026-10-16 — input-hash CI binding metadata correction

Hosted publication `f17fc8ce` passed the new standalone input gate but failed
five strict source checks because the staged workflow digest was stale. The
successor updates only that existing metadata digest; guard/historical/runtime
bytes stay exact. Eighteen source-only tests and both substitution rejections
pass with verified receipt `20261016T184732Z-7c6f2889a8e8`. Failed hosted logs and
complete archives remain retained; current PR78 checks and exact-head review are
the final publication/merge authority.


## 2026-10-16 — prepared native superscalar program executor

The owner-authorized continuation above accepted PR #78 uses a separate
`feature/prepared-superscalar-executor` temporary checkout. Pinned v2.0.1 native
semantics and ownership were checked first: no overlapping open PR or active
claim. Existing completed task #71 retains plain execution requests. No new
issue, hub notice, settings/credentials change, cleanup or synchronization was
performed. Prior accepted sources and original data remain retained.

Clean source `6f65049c` / tree `19ac91c6` passes correctness execution
`20261016T210802Z-d50e99dbfb16`: 130 native cases, 7,779 retirements and ten RTL
modes. Receipt `f7598ff0` verifies against the immutable journal. Only the new
oracle was compiled, reusing the exact retained native library. Separate
`20261016T211324Z-b1d24eb3f1fe` consumes the verified receipt and all 1,178 actual
fixtures, with no native generation or completed RTL repeat. Verified receipt
`27591eb9` binds seven mapped modes over 116 cases and actual synthesis of
19,604 generic cells, 1,410 flops and zero latches. Both first attempts passed.

Actual under-lock CPU600%, RAM4GiB, swap2GiB, Tasks256 and six-CPU checks pass.
Six independent modes share one admitted payload. Observed synthesis cgroup peak
was 536,395,776 bytes with no OOM events. Complete commands, timing/RSS, sources
and outputs remain retained. Independent bounded science accepts the component;
separate package audit covers all 2,466 artifact partitions and every fixture.
The component profile preserves opcode counts and actual per-program ideal
modeled clocks of 6,511–6,749, without extrapolating to dataset/full-hash cost.

Publication additions document the exact prepared-image/reciprocal contract;
the five runtime bindings remain byte-identical to `6f65049c`. The feature PR
records final publication-head review, hosted CI and normal merge outcome.
Program preparation, cache initialization, cache service and eight-step item
control remain external. The next controller/export gap is documented only;
no next-stage code/job, full-hash/PPA or memory choice follows.

## 2026-10-18 — native cache-backed dataset-item correctness

The new bounded controller starts above merged PR #79 / main
`74a24e239b938ebaf4874ebd4dae47dd072ad41d`; that PR's nine premerge and two
postmerge checks were already complete and were not repeated. Executed source
`76d3ee59b3d02fccb258973d4a0b74dd4adb5d3f`, tree
`ef38f9820985a150cd2d569bc43cec6b59b76e53`, reuses the unchanged accepted
superscalar executor and multiplier. See
[EXP-020](../experiments/EXP-020-native-dataset-item.md), the
[interface](../rtl/dataset/DATASET_ITEM.md) and
[evidence](../docs/validation/dataset-item-20261018/README.md).

Correctness execution `20261018T175827Z-447be94ead08` passes 20 native cases,
61,568 instruction states, 160 completed cache-XOR stages and twelve RTL
profiles, with independent bounded scientific acceptance. Verified receipt is
`f3ced2d4f48eaa7c49359cea893c65666377c7f0a84386c035736357bfb59ad8`;
manifest is `08a0a963c68dec495201c3c82020db2d7cfdaca796ac9f6ff433af5474573bc7`.
Original runner scientific flags, source snapshots, fixtures and outputs remain
unchanged. Ideal native items measure 53,079–53,399 modeled clocks; the first two
controlled stalled items measure 71,265/71,207.

Separate mapping execution `20261018T180710Z-118e10af1b32` finishes all seven
mapped profiles PASS and all nine commands rc0, retaining 951 artifacts. Root
integrity verification binds receipt
`5872e251d8c345f3ef4327b5c64ba023862c5c8cc7f8a2d7901ce7571ab19815` and manifest
`feb803e55f01fdac7ad90c4ab126f7cf905f400dc57200cf14b3980d97d70d7c`.
All 181 source bindings and 898 fixture files are byte-identical; no Argon/native
preparation or completed RTL work was repeated. Default component synthesis
reports 42,132 generic cells, 4,234 DFF cells and zero latches. Original runner
scientific acceptance remains `unverified`; separate independent bounded review
accepts the mapped run with no blockers, bound by review SHA256
`acbf8ff5b8bf631e408d28f52c5a5d24e68e3feaa0efefb5aff0082950cbe871`.
The [mapped records](../docs/validation/dataset-item-20261018/synthesis01/)
retain this run separately from correctness. Final publication-head review and
six hosted checks remain separate gates; the feature PR records the actual head
and publication outcome. This scope ends at a draft PR. Autonomous Argon2/cache
initialization, native program/global
reciprocal preparation, physical tagged cache service and lifecycle integration
remain external. No new full-hash measurement, physical PPA, architecture
selection or 1 MH/s below 2,500 W proof follows.

## 2026-10-18 — bounded dataset lifecycle integration

PR #80 merged normally to `901c6557`, with six head/two postmerge checks passed.
[EXP-021](../experiments/EXP-021-native-dataset-lifecycle.md) reuses retained assets;
three 2×1 native comparisons, five recovery prefixes, 32 unit checks and service
RTL pass. Mapped functionality passes; independent bounded review accepts the results.
Executed public code `f22ad4b7` / tree `bbadcf7e` measures ideal hardware 641,180
modeled clocks, including 106,798 nested item availability clocks. Service-only
synthesis reports 45,670 generic cells, 4,761 DFF cells and zero latches.
[Evidence](../docs/validation/dataset-lifecycle-20261018/README.md) retains capacity,
provider boundaries and physical unknowns; original scientific flags stay unchanged.
