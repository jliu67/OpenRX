# Open questions

- Which board/chip markings establish the X5 processor identity? Does it use a stock SG2042 or a customized derivative?
- What are the actual firmware/JIT, ISA extensions, frequency and per-chip power?
- Is any X9 independently available, and what is the original Bitmain specification source?
- What is Monero mainnet's current PoW version and upgrade schedule?
- The pinned scalar RV64GC JIT passed bounded QEMU v1/v2 light controls. Will the exact selected BOOM/Chipyard configuration boot Linux, support SIGILL/cache flushing and preserve full-dataset hashes?
- Can pinned gem5 full-system Linux execute the unchanged probes/JIT after the documented SE signal/cache-flush gaps? See #16; rounding source support alone is not executed correctness.
- Will MediumBoomV3Config remain preferable after exact emitted memory/cache configuration, per-component license review, full workload runtime and calibrated evidence? Selection is provisional, not a performance ranking.
- Is v2 limited by dataset latency, scratchpad capacity, AES throughput, or execution width for each configuration?
- What realistic synthesis library/process and calibration hardware can support power estimates?
