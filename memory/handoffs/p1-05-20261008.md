# Phase 1 handoff — P1-05 completed

Session: 2026-10-08 UTC / 2026-10-07 Edmonton. Agent: ChatGPT. User instruction: continue Phase 1 and keep persistent progress/communication in the repository.

## Resume here

1. Read AGENTS.md, memory/PROJECT.md, STATE.md, DECISIONS.md, OPEN_QUESTIONS.md, [docs/TASKS.md](../docs/TASKS.md), and current issue #1 comments. This session's editing claim is released at handoff; no background agent is running.
2. Review implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676` (base `ea90554c486ed6c7eae6fafc2e1c16b90193b1d2`), the [adapter protocol](../benchmarks/steady/README.md) and [validation](../docs/validation/p1-05/README.md).
3. Claim the next scoped task on #1 with identity, current base commit, files and acceptance criteria. Refresh actual main before publishing; do not force-push over concurrent work.

## Completed and actually verified

P1-05 adds an opt-in Linux/C++17 adapter linked to unchanged pinned RandomX. Dataset, VMs and workers persist through known controls, warmups and balanced v1/v2 trials. It records explicit monotonic/realtime clock brackets, restores worker FP state, counts completed hashes and separates logging/setup from the timed envelope. The older upstream harness is untouched. The new static-stride and public `first/next/last` batch schedule has different overhead; do not combine its rates with the older harness's rates.

CI run **37722277487**, job **113132440545**, passed on `59b469c`: all 171 vendor files, 64 tooling tests, reproducible profile, native builds, all 107 upstream tests, existing smoke/full-dataset checks, and 6 new native tests. No skipped tests. Native coverage includes 8 reference controls across version/configuration pairs, repeated known hashes, hardware/software AES, 1/2/3 workers, 16 invalid-argument cases, expected short-duration failures, and two differential 17-nonce checks against upstream.

Downloaded artifact **11526487498**, SHA-256 **98c2a158d5ad3795c31fb4fd1fb52fc5f199bc34604ba979a4078fa0788844a3**, was rehashed successfully. All four raw streams/36 intervals were revalidated locally and their raw checksums/archived summaries matched. Core local source matched the published blob hashes and CI source metadata. Native-suite log/check ledger are committed; the full artifact expires **2027-01-06T03:20:48Z** unless retention changes. Promote additional raw files into reviewed Git history before relying on them after expiry.

## Reproduce

```bash
python3 -m unittest discover -s tests -v
bash scripts/build_steady.sh
bash scripts/test.sh
python3 tests/native_steady.py
```

For actual host trials use `scripts/steady_benchmark.py` and the protocol's pilot/duration/placement requirements. Example counts are not a guarantee of adequate duration. Use even repeats for balanced order and retain all rejected trials. Controls are not a thermal soak.

## Next unblocked software task: P1-06S

Design and implement a strict power-sample importer and validator. Require explicit time/units/device/boundary metadata, a defensible clock mapping to the recorded brackets, complete interval coverage, gap and clock-step rejection, tested numerical integration and uncertainty handling. Power-model estimates, CPU telemetry and wall-meter observations must remain distinct. Use labeled synthetic fixtures to test parsing/integration; do not populate real power or hashes/J from fixtures. Real meter access is still needed to validate the physical measurement chain.

A hardware-capable agent can independently claim P1-04 (controlled host thread/AES trials), then P1-07 (dynamic profiling). Coordinate shared files on #1. P1-06 physical wall-power measurement is blocked on host/meter access and the import path. No other agent, host or meter has been provisioned in this session. M1/Phase 1 remains open.

## Caveats and preserved limitations

The local workspace again could not resolve the upstream source-download host; public-web retrieval was unavailable. Therefore only 22 new synthetic harness tests, syntax checks and downloaded-artifact validation ran locally. The real RandomX builds and native controls ran in CI. A synthetic compile-only header is not vendored source or a real build.

The hosted runner exposed two logical CPUs (AMD EPYC model text, Microsoft hypervisor). The three-worker correctness case is deliberate oversubscription, not scaling evidence. Clock bracket widths/resolution do not certify meter synchronization; the timing envelope includes worker scheduling, per-worker aggregation and FP restoration. Native logs were emitted outside it. Dataset initialization is excluded, not amortized into energy.

No controlled hardware efficiency result, PMU profile, RISC-V simulation, RTL implementation or competitiveness claim was produced. No vendor modifications, paid compute, hardware purchase, account permission or visibility change occurred.
