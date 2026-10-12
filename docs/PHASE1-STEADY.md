# Phase 1 addendum: same-process instrumentation

P1-05 is complete at implementation `59b469c6b9a56aecc1e5ab8e82901e281ebe4676`, validated by CI run `37722277487`. This dated addendum supersedes the initial report's mentions of P1-05 as pending; its source-derived workload analysis remains unchanged.

The original [Phase 1 report](PHASE1.md) describes the initial `scripts/benchmark.py` path. That runner still uses separate processes for warmups and inferred timing. The new opt-in [steady adapter](../benchmarks/steady/README.md) reuses its initialized dataset, VMs and worker threads, checks both algorithms, and records explicit hashing-envelope timestamps. It does not alter the upstream source or replace the original control harness.

[Validation evidence](validation/p1-05/README.md) includes 64 tooling tests, 107 upstream tests, six new native tests and independently downloaded/revalidated raw results. No controlled throughput or energy baseline is claimed. The declared envelope includes scheduling/bookkeeping and excludes initialization/logging; clocks alone do not measure or synchronize a power meter.

Next work is authoritative in [the board](TASKS.md) and [handoff](../memory/HANDOFF.md): P1-06S power-data import software is completed and independently accepted in [#13 / merged PR #17](https://github.com/jliu67/OpenRX/issues/13); reuse it. Current next work is controlled #8 measurements, real #10 wall-power readings and #11 dynamic profiles under their existing prerequisites. Do not reimplement the importer. **Phase 1/M1 is still open.**
