# Independent peer review of the Monero activation source audit

Date: 2026-10-08 UTC / Edmonton. Issue: [#4](https://github.com/jliu67/OpenRandomX/issues/4).
Author: `activation_review`; separate reviewer: `power_patch_review`.

**Verdict: accept the [dated source audit](REVIEW-20261008.md).** Its conclusion that the audited released mainnet consensus uses RandomX v1 is supported by primary release and consensus sources. The report correctly labels that conclusion as a source inference and explicitly excludes a directly observed live chain tip. No contradictory activation evidence was found in the sources examined.

I independently retrieved the official stable-release announcement and GitHub release/tag/submodule/code sources, rather than relying solely on the author's extracted conclusions. **Twenty independently fetched records match the author's manifest digests.** I also checked all **30** raw capture digests in the author's source cache and replayed the supplied reproducer: **30 verified captures and 21 passing source/API assertions**. [peer-checks-20261008.json](peer-checks-20261008.json) records the independent URL/digest comparisons; [peer-replay-20261008.json](peer-replay-20261008.json) retains my reproduction result.

## Findings verified

| Claim | Independent finding |
|---|---|
| Latest observed stable software | Release API reports Monero v0.18.5.3, non-prerelease, published 2026-10-06T09:31:49Z; the official announcement identifies the RandomX library update as v1.2.3 |
| Stable source identity | Annotated tag `a759b82b13ebb48eaf3ef3a8a4e01391a7b13eec` resolves to `22578c3f7d7b4b6dd85ff7daa42a827d97cc53d0` |
| Released mainnet rules | The mainnet table ends at HF16 / height 2,689,608; `RX_BLOCK_VERSION` is 12; the actual longhash path calls the legacy RandomX API, whose bundled header has no v2-selection flag |
| Bundled algorithm source | Stable and observed master `7778a369afdb788af245ba5ac4d5b17d5a2cc4c5` both pin RandomX `12f2c2ffe2108d6cf54c391fee33c8bc3646cdab` |
| October 5 reference | Beta 3.0's prerelease announcement concerns a separate FCMP++/Carrot stressnet fork from **testnet** at height 3,102,800, not a mainnet upgrade |
| Beta source behavior | At `d816367cb1aa405bfa68a20ac3e034d0759d968e`, HF17 selects variant 2 and the RandomX v2 flag; beta mainnet HF17/HF18 entries are explicitly mock test values |
| Beta 3.1 | Lightweight tag resolves to `b13ab0cabadeb301b2ce5282b077945e9ab3a7ba`; audited hardfork/configuration/hash-selection files match beta 3.0 bytes. A tag's existence does not imply a mainnet release |
| Full PoW scope | Beta HF17 also applies `rx_commitment` after the raw RandomX hash. OpenRX's raw API controls do not demonstrate complete beta block-PoW compatibility |

The release and master mainnet table bodies match. Their full hardfork source files differ in the copyright year; the review did not assume whole-file identity. The author's pin/digest ledger records each correctly. The roadmap claim is consistent with the author's retained official HTML; my independent web fetch of that page timed out, so I do not claim a second successful HTTP roadmap capture.

## Acceptance limits and reproduction

This review does not execute Monero, verify chain history, independently authenticate release signatures, observe miner deployment, or demonstrate that the stressnet actually passed its scheduled fork height. A scheduled date/height and algorithm-support code establish published intent and software behavior; they do not constitute a tip observation. Absence of a v2 mainnet schedule is limited to the audited sources, as stated in the report.

The command I actually executed was:

```bash
python3 docs/validation/monero-activation/reproduce.py \
  --capture-dir /tmp/openrx-monero-activation
```

The report's pinned-source refetch mode can reconstruct the immutable code checks. Keep the dated API/website raw bodies in durable evidence storage as well: their endpoints can change, and hashes alone cannot reconstruct an earlier response. That is an evidence-retention improvement, not a conflicting consensus finding.

The documented research question on #4 is resolved for this dated source snapshot. Keep OpenRX's v2-first research scope and v1 controls; refresh published mainnet scheduling and separately capture an independently synced tip before deployment or claims about live network activation.
