# OpenRX owner-authorized local compute resource policy

## ⚡ OWNER DIRECTIVE — MAXIMIZE LOCAL COMPUTE UTILIZATION (ALL AGENTS)

**Read before any local build, simulator run, benchmark, or execution planning.** The owner explicitly authorizes using the dedicated Ubuntu host's **six CPU cores and 16 GiB RAM aggressively**, with swap where helpful, for *approved* OpenRX work. **Do not inherit artificial 6 GiB / 200% CPU restrictions from temporary sandboxes or retain conservative local cgroup limits without workload-based evidence.** Prioritize effective utilization, not arbitrary quotas.

- Check actual host CPU/RAM/swap, existing process load, systemd cgroup limits, disk capacity, and measured peak memory before allocating resources. For parallelizable jobs, make all six cores available (up to 600% CPU) and use as much of the 16 GiB as safely practical, retaining only necessary OS/agent headroom. Tune compiler workers and independent-job concurrency from measurements; a single-threaded gem5 workload will not become multithreaded by raising its CPU quota.
- Configure per-job systemd CPU and memory budgets to remove **unnecessary** bottlenecks, while preventing host-wide out-of-memory conditions or interference with concurrent jobs. Treat ~14 GiB RAM and 600% CPU as an initial high-throughput *candidate*, not universal mandates or guarantees; determine actual safe memory and swap values per workload.
- Record observed utilization, peak RSS, worker count, effective cgroup limits, headroom, and reasons for any throttle or idle capacity in the relevant GitHub task, experiment, and durable handoff. Recheck after workload changes.
- **Safety and science still override utilization:** preserve originals, logs, checkpoints, hashes and provenance; honor the one-resource-slot/coordination policy until separately reviewed changes; never interrupt a running build solely to change limits; do not run expensive scientific workloads before the migration's independently verified LOCAL_ACTIVE gate and explicit authorized release. No unauthorized paid compute or hardware spending.

Canonical owner announcement: [GitHub board #5](https://github.com/jliu67/OpenRX/issues/5#issuecomment-6094244760). Migration tracking: [#27](https://github.com/jliu67/OpenRX/issues/27) / [PR #28](https://github.com/jliu67/OpenRX/pull/28).

## Agent startup verification

1. Inspect the current Ubuntu host hardware and service cgroup limits before approved execution.
2. Justify any per-job constraints materially below available resources using measured memory, safety, model parallelism or concurrent jobs.
3. Post the effective job limits and evidence on the relevant task issue and in the final handoff.
4. Keep the existing scientific migration and admission controls in force; this document is not activation authorization.
