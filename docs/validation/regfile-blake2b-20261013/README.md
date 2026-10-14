# Register-file BLAKE2b evidence — task #64

The independently accepted parent is PR63 `990f36830c5a9854bf8e2cf1fe7fd7d4ccf7f192`, [review 5505712453](https://github.com/jliu67/OpenRX/pull/63#pullrequestreview-5505712453). This new draft stage requires its own independent review and has no merge authorization. At initial publication, hosted verification is pending. Subsequent hosted results are recorded on [task #64](https://github.com/jliu67/OpenRX/issues/64) and the draft PR checks, preserving this executed source head.

All 18 RTL modes and 17 mapped modes pass. Both digest sizes use the same 524 native messages. Digest latency is 56 modeled clocks; the held seed bridge adds its capture/return stages and has 58-clock hash latency, zero-clock final bypass, 459 hashes/65 bypasses in its corpus, four resets and three invalid iteration counts. Eight native cancellation modes cover both compression blocks and held seed/final/batch responses, retaining all 2 MiB of committed memory and restarting the opposite version. Existing backend reset/error scenarios also pass.

Four native v1/v2 ideal/stalled eight-program × four-iteration chains use exactly seven actual hardware seeds, with full state/events and all 2 MiB checked at each program boundary. V2 clocks are 111348/185810; v1 clocks are 70524/121278. Each is 414 clocks above the accepted software-seed fixture. These fixture model clocks omit software initialization, program generation and finalization and establish no full-count or physical throughput.

Actual server mapping uses Yosys 0.9 (git sha1 1979e0b). Counts include inherited G operand latches and exclude the accepted execution backend, external memories and software providers.

| New stage | Generic cells | Flip-flops | Latches |
| --- | ---: | ---: | ---: |
| hash-64 | 45,891 | 5,156 | 1,024 |
| hash-32 | 45,635 | 5,156 | 1,024 |
| seed | 57,378 | 7,755 | 1,024 |

Mapped digest and seed gates reproduce their RTL records exactly, including connected transitions, held/error/reset behavior and cancellation. The connected backend remains accepted RTL; there is no regenerated whole-core or full 16K gate run. The corpus reuses eight assertion-only register-file frames from the accepted full native-v2 PR63 run; the new connected tests use eight programs × four iterations.

## Exact reproduction and preservation

[Commands](server/commands.json), [tools and model](server/tools.json), [source inputs](server/inputs.json), [summary](server/summary.json), [complete output digests](server/artifacts.sha256.json), [raw/compressed log map](server/raw-public-map.json) and [kernel resource witness](server/resource.json) bind the executed result. [Complete source/output retention](source-output-retention.json) verifies every archived byte/mode before freezing snapshots and preserves executable bits. Raw logs are retained under server/logs as deterministic gzip; each decompression must match its original digest. Native bodies, fixtures, binaries and all gate netlists remain in the complete server output archive and the hosted artifact.

The payload used one serial worker, actual CPU quota 600000/100000, 2 GiB RAM, 512 MiB swap, 128 tasks, six-CPU affinity, fresh 1 GiB headroom and the global resource lock. Actual peak memory was 1044688896 bytes; final swap/events/throttling are recorded in the witness. These resource records are not physical-power measurements.

The command transport disconnected during an observer wait; the systemd unit remained active with the same process and start time, and the payload was not restarted. [Recovery record](server/command-connection-recovery.json) preserves this separately from test results. The outer wrapper time file is incomplete; per-command timing and the kernel resource receipt remain the timing/resource evidence.

[Original upstream retention](upstream-original-preservation.json) preserves all 13 files at `36f00fd6351f82cb476fd82af8d615f28aaf677d`; the five selected IP originals remain unchanged. [Preserved input guard](server/preserved-inputs.json) covers 69 accepted inputs, 171 native files and five IP originals. [Accepted full-register vector source](server/accepted-full-register-vector-source.json) separates the accepted full-v2 frames from newly generated short connected fixtures. [Independent vector crosscheck](server/independent-vector-crosscheck.json) checks native C against hashlib and verifies digest32 is not truncated64.

The complete successful source is a successor of failed execution snapshots. Original guard preparation, client include, EOF, pilot summary, numeric-literal frontend and missing cell-model attempts remain separate complete archives, with completed per-command passes distinguished from failed overall scripts. The original IP mismatch is an expected negative proof, not accepted hardware. All older source/evidence/build assets remain retained; no retired editable checkout or Git sync was restored.

Initial input hashing, scratchpad AES fill, program AES generation, final scratchpad AES reduction, addressed fixture dataset, full actual dataset, complete hardware finalization and physical PPA remain explicit boundaries. [Design](../../../rtl/hash/README.md) describes the exact message, digest parameters, handshake/tag and reset semantics; [EXP-011](../../../experiments/EXP-011-native-regfile-blake2b.md) reports measured/model scope.
