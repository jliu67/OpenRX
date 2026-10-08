# P1-05 validation: same-process warmup and timing

Date: 2026-10-08 UTC / 2026-10-07 Edmonton. Implementation: `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`; reviewed base: `ea90554c486ed6c7eae6fafc2e1c16b90193b1d2`. Development branch: `openrx/p1-05-steady-timing`. The documentation/evidence handoff does not change this tested implementation.

## Executed checks

[GitHub Actions run 37722277487](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487), job `113132440545`, completed successfully. All configured steps passed. The downloaded test logs and individual native JSONL/run.json records were inspected, not just the green badge.

| Check | Observed result |
|---|---|
| Vendor integrity | 171 files; vendor source unchanged |
| Python tooling suite | 64 passed, zero skips: prior 42 plus 22 new harness tests |
| Static profile reproduction | Passed |
| Native library and adapter build | Passed |
| Upstream RandomX suite | 107 passed, zero skips |
| Existing v1/v2 smoke and full-dataset controls | Passed |
| New native test suite | 6 passed, zero skips; includes 16 invalid-argument cases |
| Adapter reference controls | All 8 version/configuration controls matched pinned 1,000-nonce references |
| Repeated known inputs | One-worker hardware trials reproduced both known references |
| Independent upstream-harness comparison | Both 17-nonce, three-worker, software-AES aggregates matched |
| Duration rejection | Four intentionally short measurement-phase intervals rejected; native exit 2 and wrapper failure retained as expected |

The native correctness configurations were one-worker hardware AES, one-worker software AES, three-worker software AES with uneven nonce partitioning, and two-worker hardware AES with an intentionally impossible duration threshold. Both algorithms were selected in each process. There were **36 native interval records: 8 controls, 12 warmups and 16 measurement-phase records**. These schema phase names do not turn the short controls into a performance baseline.

The CI host reported Linux x86_64 under Microsoft's hypervisor, AMD EPYC 9V45 model text, **two visible logical CPUs**, and GNU C++ 13.3.0. The three-worker case intentionally oversubscribed those visible CPUs for correctness coverage; it is not thread-scaling evidence. Compiler/cache/CPU/resource metadata remains in each archived run.json and CMake cache.

## Downloaded artifact and local revalidation

[Correctness artifact 11526487498](https://github.com/jliu67/OpenRandomX/actions/runs/37722277487/artifacts/11526487498) was downloaded in this session. Its 66,083-byte ZIP SHA-256 was independently calculated as:

`98c2a158d5ad3795c31fb4fd1fb52fc5f199bc34604ba979a4078fa0788844a3`

That matched the GitHub-reported digest. All four native JSONL logs were revalidated locally with the checked wrapper; resulting summaries matched the archived reports. Raw JSONL/stderr checksums were recomputed and matched. The locally checked C++/Python/build source hashes matched the CI metadata; the core C++ and Python wrapper Git blob SHAs were also checked through the connector.

[checks.json](checks.json) retains the observed configuration/status/checksum ledger and the two differential hashes. [native-tests.log](native-tests.log) preserves the actual native-suite output. Full raw intervals, stderr, run metadata, CMake caches, upstream/tooling logs and differential-oracle outputs are in the artifact. GitHub reports expiration at **2027-01-06T03:20:48Z**. Preserve any additional raw files needed for later claims in reviewed Git history before expiration; never use these short CI rates as hardware-efficiency evidence.

## Local execution boundary and failures

The 22 new synthetic record/process tests passed locally using Python 3.13.5; they test validation, aggregation, timeout cleanup and failure retention, not cryptographic throughput. A C++ syntax check used explicitly synthetic API declarations. The local source download again failed at DNS resolution, and public-web retrieval was unavailable. **No local RandomX library build or local native benchmark is claimed.** The actual native execution occurred in CI; artifact revalidation was local data checking, not a second native run.

The timeout fixture was killed and reaped with return code -9. Deliberate malformed-output/nonzero-exit/short-duration cases were retained and rejected by tests. No unexpected native correctness failure or hidden test skip occurred. Existing vendored code and the older upstream-harness runner were not modified to suppress warnings or change the workload.

## Exact reproduction

```bash
python3 -m unittest discover -s tests -v
bash scripts/build_steady.sh
bash scripts/test.sh
python3 tests/native_steady.py
```

The existing CI also reproduces the static profile and invokes the older runner's smoke and full-dataset reference controls. See [adapter protocol](../../../benchmarks/steady/README.md) for all measurement-boundary details and real-host pilot commands.

**P1-05 is complete for this scoped adapter. M1/Phase 1 is not complete.** A controlled host matrix, useful dynamic profiles, a tested power-sample import path and real synchronized wall-power observations are still outstanding. Clock brackets are not meter synchronization; scheduling/batch/bookkeeping overhead remains inside the declared interval. No hashes/J, calibrated timing model, RISC-V result, RTL or X5/X9 competitiveness claim is established.
