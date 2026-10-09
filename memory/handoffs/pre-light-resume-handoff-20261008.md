# Handoff — actual Linux runtime accepted; reuse the simulator

2026-10-08 UTC / Edmonton. The user requested another review of repository, messages and board, followed by fixes and continued implementation. Read live main, task [#16](https://github.com/jliu67/OpenRandomX/issues/16), [PR #18](https://github.com/jliu67/OpenRandomX/pull/18) and actual bot receipts before choosing work. Claims are issue-specific and advisory; no permanent coordinator or running worker is implied.

## Accepted progress

The pinned gem5 v25.1.0.1 build now succeeds. Incremental compilation reused prior work; the ordinary link hit the 8-GiB host limit. The upstream-supported low-memory linker option recovered in 248.76 seconds with unchanged source/canonical config and no new OOM. All 10,933 archived source files match. The exact executable SHA-256 is `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`.

**Real full-system Linux boot and all nine scalar runtime controls passed**, independently replayed from actual serial/report and rehashed inputs. The test covered signal recovery, page permissions, explicit RV64 Linux flush-icache returns and generated code 7 → 19 → 7; child/status/stderr/completion and hypercalls 1/2/3 all passed. It used one Atomic core, RVV off, classic private caches and 4 GiB RAM. [Actual run](../docs/validation/m3-fs/actual-runtime-20261008/README.md), [separate acceptance](../docs/validation/m3-fs/ACTUAL-GEM5-REVIEW-20261008.md), [source/build recovery](../docs/validation/m3-fs/link-recovery-20261008/README.md).

PR #18's final tested implementation at `4f4cf178` passed 245 Python, 107 upstream and six native tests, 39 RandomX plus nine runtime controls per native/QEMU environment, and 26 offline gem5 controls. [Exact CI ledger](../docs/validation/m3-fs/streaming-ci-20261008/ci-review.json). A later independently reviewed runner repair streams flushed probe output while preserving exact child status and rejecting capture failures. Its generated-Bash host controls pass; the actual guest runs retain the original runner snapshot and are not claimed to execute that revision. Ordinary PRs no longer start expensive source builds. The separate hosted manual builder and cache/artifact consumer are reviewed but have not run end to end; the actual local guest is distinct evidence.

The unchanged light-mode attempt timed out at its declared 1,200-second child limit (1,261.24 seconds including wrapper checks). It repeated all nine runtime controls and verified/launched the hash ELF, but exposed no complete hash body/END/summary or final hypercall. Independent replay confirms exact inputs and truthful timeout; no hash mismatch is established. [Raw attempt](../docs/validation/m3-fs/actual-light-20261008/README.md), [review](../docs/validation/m3-fs/ACTUAL-LIGHT-REVIEW-20261008.md). Keep #16 and M3 open. No local gem5 build or guest remains running at this handoff.

## Reuse, do not rebuild

The verified original binary, source archive/licenses, minimal Python runtime and complete build records are saved in two ordered archive parts. [REUSE.md](../docs/validation/m3-fs/REUSE.md) gives filenames, retrieval identities, SHA-256 checks, reconstruction and launch commands. The complete archive SHA-256 is `b9536aa9dbce308edcdb735c518395ebf2e02d20ecdf53b181deeded19d07769`. Clean-environment preflight and all 918 package file checks passed on this host; portability elsewhere was not tested.

If temporary inputs remain, the executable is at `/tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt`; exact launch environment is in the actual run's `command.txt`. Runtime ELF SHA-256 is `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`. Unchanged hash ELF is `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`. Acquire pinned guest resources through `simulator/gem5/prepare.py` if absent; verify all identities, use a new output directory and retain raw failures as well as successes.

The first runtime wrapper completed in 958.249 host seconds, including input hashing; actual simulator host time was 917.34 seconds. Early firmware/kernel and shell startup can remain silent for minutes before progress. These are resource observations, not calibrated hardware throughput. The light run spent most of its budget reaching the probe. Current main defaults to no wall-clock cutoff after `50ba831`; reuse the binary and streaming runner, monitor phase/serial progress, and declare the separate simulated tick budget. Positive `--timeout SECONDS` is an explicit opt-in. Preserve historical timeout evidence; do not shrink the algorithm or infer missing hashes.

## Board and message fixes

#13 importer software and #4 dated source audit remain completed; their accepted PRs #17/#19 and historical artifacts are unchanged. #20's inspection was separately accepted and closed.

#22 is completed: merged PR #23 queues eligible bot announcements and requires separate-agent acceptance evidence. Actual deployment passed eight tests and bot repost verification. The source review identified a potential pending-message replacement, not an observed missing message. #24's compact major-handoff announcement policy is independently accepted and closed; original-author correction `a2128b9` gives it unique D030. Our later decisions are D031/D032.

The exact concurrent `511e173` SESSION_LOG prefix and policy are preserved. Earlier state/handoff files are archived exactly under `pre-fs-reuse-*-20261008.md`; original timeout/OOM reports stay historical. Major final handoffs require a concise hub #5 announcement and verified bot copy; full evidence and claim transitions remain on the task issue.

## Open acceptance boundaries

M1 #1 still needs controlled host matrix #8, real synchronized meter #10 and counters/profiling #11; completed importer #13 supplies software only. Hardware #2 and future Monero activation/live-tip corroboration remain open. The dated Monero audit supports released v1 from source; beta v2 stressnet dates are not mainnet activation.

Complete unchanged light hashes, full dataset, intended timing-core/SMP coherence and selected BOOM/Chipyard boot remain separate. Atomic runtime controls do not establish BOOM/C920/SG2042 behavior, physical power or calibrated timing. M4/M5 remain gated; no RTL optimization, vendor edits, paid compute or account changes were made.

This local text snapshot lacks four vendored audit PDFs; real hosted CI verified all 171 vendor files. Connector tree updates preserve those remote blobs. Consult original issue histories and final claim receipt before starting a new attempt.

Session `codex/20261008-fs-reuse` records this work on #16; consult its final release/receipt before starting another attempt. This document is not a live ownership registry.
