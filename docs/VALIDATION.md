# Foundation validation — 2026-10-08 UTC

Host: x86_64 virtualized Intel Xeon Platinum 8573C, GCC/G++ 13.3.0, CMake 4.4.4, Release ARCH=native. This is not SG2042 or hardware simulation.

- Vendor integrity: all 171 vendored files match the SHA-256 manifest.
- Shell syntax and Python compilation checks passed.
- Native RandomX build completed. Upstream assembly emitted a linker warning about a missing GNU-stack note; preserved in the build log. Vendor source was not changed.
- Upstream randomx-tests: 107 tests passed, zero skipped, process exit 0. Includes v1/v2 interpreter and JIT, rare ISUB_R edge cases, rounding preservation and version switching.
- Verification smoke: v1 and v2, 2 nonces each, JIT, exit 0. No upstream 2-nonce reference is supplied; correctness evidence comes from the upstream test suite.
- Full-dataset check: v1 and v2, 1000 nonces each, seed 0, one hashing thread, two initialization threads. Both calculated aggregate hashes matched their respective upstream references, exit 0.

Raw build log, test log, commands, machine metadata and run outputs are under docs/validation/foundation/. These runs were functional validation only, with no power measurement, no warmup protocol, and only one repetition. Do not use their timing to claim mining efficiency or identify RISC-V bottlenecks. Initial run metadata precedes the final foundation commit; source pin remains exact.

GitHub remote creation and CI execution remain pending. Local validation is not a claim that GitHub Actions ran.
