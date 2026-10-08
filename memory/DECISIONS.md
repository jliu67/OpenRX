# Decision log

| ID | Decision | Reason | Revisit when |
|---|---|---|---|
| D001 | Target v2 first; compare v1 | Avoid optimizing only an older workload | Upstream algorithm changes |
| D002 | Vendor unmodified v2.0.1 at a commit SHA | Complete code included, reproducible checkout, preserves licensing | Validated upstream update |
| D003 | Same release for v1/v2 comparisons | Controls library/JIT differences; v2 flag selects workload | Historical release comparison needed |
| D004 | Private remote initially | No user visibility preference given | User requests open publication |
| D005 | No RTL in foundation | Need correctness and credible workload model first | Baseline and simulator gates pass |
| D006 | No efficiency number without power measurement | Hashrate does not establish energy efficiency | Power sampling implemented |
| D007 | Separate source-derived slots/opcode weights from dynamic execution and performance | Static counts cannot identify a hardware bottleneck | Dynamic traces and calibrated model exist |
| D008 | Reject ignored single-thread affinity; preserve vendor source | Upstream dispatch passes CPU ID -1 in this path; silent acceptance corrupts comparisons | An explicitly reviewed affinity/backend change exists |
| D009 | Treat CI as correctness evidence; retain M1 as open | Hosted one-repeat controls have no controlled host/power baseline | Known-host matrix and time-aligned power meet acceptance |
| D010 | Use docs/TASKS.md, issue claims and memory/HANDOFF.md for collaboration | User made this repo the persistent project board for agents | User changes project workflow |
| D011 | Label separate-process warmup and inferred intervals explicitly | They are not same-VM cache warmup or synchronized meter timestamps | A tested steady-state measurement adapter is available |
| D012 | Add an opt-in same-process library adapter; retain the old upstream control harness | Obtain persistent dataset/VM/worker trials without modifying pinned algorithm source | Benchmark scope or platform support changes |
| D013 | Compare throughput only within one declared harness | New static-stride first/next/last batching has different overhead from upstream dynamic scheduling/tail; matching hashes do not imply equivalent timing | Controlled harness-overhead study justifies a comparison |
| D014 | Record monotonic/realtime brackets but leave power alignment unverified | Clock units/resolution and bracket widths are not a calibrated meter chain; duration excludes initialization and includes synchronization | A tested importer and real synchronized meter evidence exist |
