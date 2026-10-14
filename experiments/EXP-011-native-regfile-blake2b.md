# EXP-011: Native register-file BLAKE2b

[Task #64](https://github.com/jliu67/OpenRX/issues/64) extends independently accepted PR63 `990f36830c5a9854bf8e2cf1fe7fd7d4ccf7f192` with native 256-byte register-file hashing and hardware interprogram seeds. [Design](../rtl/hash/README.md) and [evidence](../docs/validation/regfile-blake2b-20261013/README.md) bind exact inputs, commands, results, failures, resources and retained archives.

All 18 RTL modes and 17 mapped modes pass. Both digest sizes use the same 524 native messages. Digest latency is 56 modeled clocks; the held seed bridge adds its capture/return stages and has 58-clock hash latency, zero-clock final bypass, 459 hashes/65 bypasses in its corpus, four resets and three invalid iteration counts. Eight native cancellation modes cover both compression blocks and held seed/final/batch responses, retaining all 2 MiB of committed memory and restarting the opposite version. Existing backend reset/error scenarios also pass.

Four native v1/v2 ideal/stalled eight-program × four-iteration chains use exactly seven actual hardware seeds, with full state/events and all 2 MiB checked at each program boundary. V2 clocks are 111348/185810; v1 clocks are 70524/121278. Each is 414 clocks above the accepted software-seed fixture. These fixture model clocks omit software initialization, program generation and finalization and establish no full-count or physical throughput.

Actual server mapping uses Yosys 0.9 (git sha1 1979e0b). Counts include inherited G operand latches and exclude the accepted execution backend, external memories and software providers.

| New stage | Generic cells | Flip-flops | Latches |
| --- | ---: | ---: | ---: |
| hash-64 | 45,891 | 5,156 | 1,024 |
| hash-32 | 45,635 | 5,156 | 1,024 |
| seed | 57,378 | 7,755 | 1,024 |

Mapped digest and seed gates reproduce their RTL records exactly, including connected transitions, held/error/reset behavior and cancellation. The connected backend remains accepted RTL; there is no regenerated whole-core or full 16K gate run. The corpus reuses eight assertion-only register-file frames from the accepted full native-v2 PR63 run; the new connected tests use eight programs × four iterations.

The original BSD-2-Clause core fails the native two-block digest because its next-block path restarts the chaining value. A declared derivative corrects continuation; all five original IP files, arithmetic/message schedule, 171 native vendor files and 69 accepted execution inputs remain byte-identical. Both original negative tests and every local preparation/harness/frontend/cell-model failure are preserved.

Initial input hashing, scratchpad AES fill, program AES generation, final scratchpad AES reduction, full actual dataset, complete hardware finalization and physical PPA remain external/open. The independently parameterized 32-byte primitive requires the caller's post-AES register file. New independent review is required; no merge is authorized.
