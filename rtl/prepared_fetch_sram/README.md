# Prepared-fetch SRAM read-port adapter

This standalone component connects one explicitly synchronous, immutable prepared
image read port to the accepted shared dataset channel. It preserves the captured
65-bit owner/full tag and 28-bit epoch/program/PC descriptor, holds replies under
backpressure, and leaves cancellation draining to the unchanged channel.

`randomx_prepared_fetch_sram_port.v` is the adapter. The two files in `tests/`
provide a validation-only frozen behavioral row store and finite standalone bench.
The model uses offline `$readmemh` preload and has no runtime write or reload API.
It is not a characterized SRAM macro or autonomous hardware initialization.

The complete [contract](../../docs/validation/prepared-fetch-sram-port-20261022/source/CONTRACT.md),
[executed source snapshot](../../docs/validation/prepared-fetch-sram-port-20261022/source/)
and [validation evidence](../../docs/validation/prepared-fetch-sram-port-20261022/README.md)
bind the exact implementation and one admitted retained cache0 image. The three
Verilog files here are byte-identical copies of that executed snapshot. Accepted
channel/arithmetic, existing defaults and older evidence remain unchanged.

Validation returned exact payloads for both owners over all 3,563 active rows,
held tagged errors for inactive slots and three cancellation drains. Its
continuous32-request test observed three modeled clocks per capture interval:
capture E0, synchronous row read E1, consume E2, next capture E3. This is a result for
this particular controller and behavioral port. It does not replace PR94's
necessary two-clock floor or establish physical SRAM timing, frequency or hashing
performance.

Counts, transport tags/echo/error and control metadata remain outside the logical
128 KiB row capacity. The accepted image and metadata must stay immutable while
sealed. Reset is legal only after genuine client/channel/provider quiescence;
it clears transport diagnostics, not the image or external full-tag history.
Full tags may not be reused while an old packet with that identity remains.
See the bound contract for the exact one-cycle/sticky-valid read-port assumption.

This is not whole-core integration, cache service, arithmetic validation, generic
synthesis, a physical memory design or a new full hash. Process/PVT/SRAM
characterization, controller/PHY service and tails, physical area/energy/frequency,
wall power, achieved hashes/s and architecture selection remain open.
