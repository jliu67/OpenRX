# Handoff — critical local infrastructure migration (inactive)

2026-10-09 UTC. Migration task [#27](https://github.com/jliu67/OpenRX/issues/27) is **STAGING; NOT YET ACTIVE**.
Read live task receipts, [local policy](../docs/LOCAL_EXECUTION.md), [migration/recovery runbook](../docs/LOCAL_MIGRATION.md),
[acceptance receipt](../docs/validation/local-migration-20261009/ACCEPTANCE.md), hub #5 and actual remote HEAD.
A dedicated migration branch and fresh persistent host paths preserve the original checkout.
No current claim/assigned role is implied by this document.

The native Ubuntu 22.04 host and user systemd/lingering have been identified; deployment/gate evidence is being gathered.
The original saved gem5 Library binary is unavailable through callable tools, so a new pinned local simulator
build is in progress with separate provenance. Exact historical guest ELFs are recovered/digest-verified;
pinned firmware/kernel/compressed/expanded disk are verified. Host native smoke passes original 257 Python tests,
171 vendor files, 106 upstream controls plus one explicit unsupported-AVX2 skip,
39 exact semantic/hash controls (optional AES skip) and nine runtime controls. No local gem5 pass is claimed. Historical runtime/partial-light evidence below is preserved and remains historical.

Next: verify original asset preservation, pinned local build/dependencies/inputs, runner durability/locks/resource limits,
status/log/output integrity, safe stop/failure/recovery, expected guest boot and strict regression/runtime smoke.
Then obtain separate review, reconcile authoritative documentation, merge the migration PR, finalize acceptance
and publish the effective policy only when all required gates pass. See the acceptance table for unfinished gates.
Host-only progress/commands are under `$OPENRX_LOCAL_ROOT/migrations/20261009/`; per-attempt records under `executions/ID/`.
No scientific checkpoint resume is verified.

Remote execution/retrieval is unavailable: visiting agents submit a complete GitHub task specification;
the owner reviews/submits locally and publishes sanitized evidence. No listener, SSH setup or autonomous poller exists.
If offline, mark expensive requests blocked and continue independent lightweight work.
Do not launch expensive full-scale sandbox or staging-host research to bypass migration gates.
#16/M1–M5 retain their existing open scientific acceptance criteria.

Exact pre-migration documents and a digest manifest are preserved under `memory/handoffs/pre-local-migration-*`.
The following earlier handoff is retained for provenance; its temporary-path execution recipe is **inactive**.

## Previous handoff — reviewed cancellation; partial guest and tick-budget proof

2026-10-09 UTC; session `codex/20261008-light-resume`. User authorized continued engineering after extensive repository, agent-message, board and handoff ingestion. Read live [#16](https://github.com/jliu67/OpenRX/issues/16) comments/receipts and current main before claiming work. The repository is now **jliu67/OpenRX**, same repository ID 1409576804. Historical OpenRandomX URLs redirect; use OpenRX for API calls. This document is not a live ownership registry.

## Accepted implementation and actual outcome

[PR #25](https://github.com/jliu67/OpenRX/pull/25) merged at `abe066f7c1b17cb3225b55cc45848a153a20ea7a`. Its tree equals tested source head `9d108c4041e0fa440a676f8a3ee1a2db1d736192`. Independent review repaired two cancellation races before publication; 253 Python tests, including 34 gem5 host controls, and 171 vendor files passed. Five source-head hosted checks passed; separate artifact replay retained 107 upstream / six native steady checks and exact 39 semantic/hash plus nine runtime controls per native/QEMU environment. The hosted gem5 guest job was skipped. [Lifecycle acceptance](../docs/validation/m3-fs/cancellation-20261008/REVIEW.md), [CI replay](../docs/validation/m3-fs/cancellation-20261008/ci-review.md).

The fresh real guest independently passed all nine runtime controls and all 31 integer/FP controls, with **zero completed hash values**. Interpreter cache initialization began; no cache pass, complete hash stream or final hypercall was observed. Exact ELF/configuration review proves both mandatory cache round loops alone require at least **10,519,287,679,000 ticks**, exceeding the current `10^13` per-call allowance. A manual tool-session stop followed that proof at 2026-10-08T23:54Z. It returned exit 1 with no final runner report; actual handler receipt/child return code/reaping are unavailable. No matching wrapper or simulator remains. No observed wall/tick timeout or hash mismatch occurred. [Actual partial acceptance and raw/input bindings](../docs/validation/m3-fs/light-resume-20261008/README.md), [budget proof](../docs/validation/m3-fs/light-resume-20261008/BUDGET-REVIEW.md).

The new optional stop-file control and manual workflow light guard have separate host/source acceptance. Final root validation passes 257 Python tests (38 gem5 controls) and all 171 vendor files; [review and logs](../docs/validation/m3-fs/stop-file-20261008/README.md). They were not executed by that saved real guest. Default no-wall policy, strict validators, workload, resources and model remain unchanged.

## Historical pre-migration execution recipe — inactive

Reuse the original simulator; do not repeat a source build. [REUSE.md](../docs/validation/m3-fs/REUSE.md) gives the two saved parts, exact digests, reconstruction and runtime environment. The original simulator SHA256 is `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`; runtime ELF is `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`; retained hash ELF is `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`. Newly built hosted hash ELF `0e310b9c...` is separate evidence, not this payload.

This pre-migration recipe records the formerly intended sandbox execution inputs. Do not execute it during
migration or use it to bypass the designated host. After cutover, request a fresh durable local attempt with
verified input identities through the local execution interface. Historical command:

```bash
LD_LIBRARY_PATH=/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu \
python3 simulator/gem5/run.py \
  --gem5 /tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt \
  --resources /tmp/openrx-fs-resource-audit \
  --runtime-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe \
  --hash-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe \
  --output-dir /tmp/openrx-gem5-light-next-attempt3 \
  --max-ticks 100000000000000 \
  --stop-file /tmp/openrx-stop-next-light-attempt3
```

Monitor continuously and preserve raw output. The larger finite guard is proposed, not guaranteed sufficient. From another tool session, create the stop file to request the runner's own SIGINT cleanup/report path; never reuse an existing stop marker. Tool/session control-C did not yield a final report in the recorded attempt, so do not infer that outcome. Positive `--timeout SECONDS` remains opt-in. If inputs disappear, restore the saved package and prepare pinned resources before launching; missing inputs are not guest failures.

Acceptance requires exit zero, complete runtime/hash frames with zero statuses and empty stderr, all nine runtime and 39 required semantic/hash controls (eight v2/v1 interpreter/JIT hashes), consistent summary/optional AES skip, guest completion, ordered hypercalls 1/2/3 and unchanged input identities. Do not shrink RandomX constants or infer hashes from partial arithmetic controls.

## Remaining project gates

M0 is complete; M1–M5 remain open. #13 importer software and #4 dated source audit are completed; #20 inspection, #22 queued announcements and #24 compact-handoff policy are completed. #8/#10/#11 require controlled host/counter/meter access. #2 lacks primary X5 board/chip/firmware binding; documented stock SG2042 properties do not identify an X5 derivative. Future Monero activation/live-tip corroboration remains open. Full dataset, intended cores/SMP and selected BOOM Linux boot are separate from Atomic functional controls. M4/M5 still require measured baseline and calibrated model; no RTL, timing or physical efficiency result is established.

All 171 vendor files are now materialized and verified locally; the former four-PDF snapshot omission is resolved. Prior STATE/HANDOFF snapshots are archived under `memory/handoffs/pre-light-resume-*-20261008.md`; original timeout/build/OOM records and SESSION_LOG history remain unchanged. PR #26 integrated at `77a1641fb85f386bce4a5b51e00dedbe257376f6`, with the tested head/tree unchanged. [Final release](https://github.com/jliu67/OpenRX/issues/16#issuecomment-6071620898) is accepted: ready, claim null, no warnings. The required [hub bot copy](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6071623180) was verified. [Integration/CI receipts](../docs/validation/m3-fs/stop-file-20261008/integration.json) preserve exact source/run/job identities.
