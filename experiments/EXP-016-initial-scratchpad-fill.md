# EXP-016: hardware initial scratchpad AES fill

The [fill stage](../rtl/hash/INITIAL_FILL.md) replaces the connected lifecycle's
software initial AES fill in explicit `HARDWARE_FILL=1` mode. It reuses the
existing licensed AES round and S-box RTL, with the unchanged pinned RandomX
keys, lane order and DEC/ENC/DEC/ENC recurrence. The base is merged main
`b8cd07070f4e38a0e784e0b123225856c7879f6f`.

The core accepts a raw host input-hash seed and tag, offers ascending 16-byte
writes and advances state only on accepted writes. It holds the last 64-byte
state as its response. The lifecycle retains exclusive INIT ownership and a
fresh hash generation until the full image and returned seed are accepted.
Actual program generation consumes that hardware post-fill seed. The legacy
provider mode remains available to preserve historical reproduction.

Reset and cancellation suppress transfers and invalidate control without
rolling back accepted memory writes. Stale initial transfers drain. Matching
unsolicited writes after request acceptance are errors and cannot reach memory.
The seed-only provider may offer its response alongside request acceptance;
hardware holds matching response-ready low until the seed can be consumed.
Static review found and corrected an inherited early-response acknowledgement
hazard before connected validation. The new bench explicitly exercises that
offer, held payload and exactly one live input-hash callback.

The native differential oracle calls unchanged `fillAes1Rx4<true>` on aligned
raw seeds. Full images, final seeds and split-call continuation are checked.
Standalone control tests cover stalls, held requests/responses, cancellation,
reset, accepted-write persistence, restart and malformed capacities. Actual
default-component synthesis and a separate bounded mapped-netlist test exercise
different scopes; bounded mapped tests are not a full mapped 2 MiB proof.

The connected test plan uses two programs and one iteration per program,
actual native light dataset values and DUT-derived program seeds. Four-state
and two-state ideal ledgers/digests must agree. Stalled completion, changed-input
initialization cancellation/restart, seed-provider error and unsolicited-write
error are separately checked. Default recovery selections still run all earlier
checks; focused selections are recorded explicitly.

Hardware fill has one disjoint outer initialization stage with nested provider
wait/fill phases. It replaces the old initialization-transport stage. The
preserved default full measurement remains `c96e96ab` and 40,975,538
hardware/transport clocks, including 131,074 initial-transport clocks. Any stage
substitution subtracts those old clocks before adding measured new initialization
cost; it does not create a new full-workload measurement at the changed source.

Input BLAKE2b, AES program generation and native light dataset generation remain
untimed host providers. Software fill remains an assertion oracle and explicit
legacy option. No completely autonomous hardware hash, architecture selection,
physical memory service, MHz, silicon area, wall power or physical feasibility is
accepted. The next bounded AES implementation is program generation from actual
post-fill and interprogram seeds, with the remaining provider boundaries retained.

Validation complete at the declared executed sources: 12 native cases, 30 RTL modes including four full 2 MiB images, 18 bounded mapped modes, malformed input/capacity guards and 37 cheap unit checks pass. Actual default fill mapping is 36,168 generic cells / 547 flops / zero latches. Connected 2×1 Icarus ideal and Verilator ideal/stalled plus one changed-input cancellation/two initialization errors pass; ideal cross-backend digest/ledger equality is exact. Both successful execution receipts integrity verify. [Complete evidence](../docs/validation/initial-scratchpad-fill-20261016/README.md) preserves exact sources, commands, hash indices, retained complete outputs and first failed vendor-snapshot attempt.

New ideal initialization measures131,076clocks. `40,975,538 -131,074 +131,076 =40,975,540` is only a historical stage substitution, not a changed-source full-hash measurement. No default 8×2,048 rerun occurred. Independent final-head review/hosted gates remain required; [task #75](https://github.com/jliu67/OpenRX/issues/75) records the final draft publication and hosted review gates.
