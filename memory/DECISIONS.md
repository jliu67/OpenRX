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
| D012 | Use GitHub issue threads for conversations and Markdown for durable memory | Avoid a single shared mutable chat file; preserve reviewable task-specific communication | Repository scale or user workflow changes |
| D013 | Separate deterministic message routing from AI execution | Installing an inbox must not silently provision paid model workers or imply agents are running | User authorizes a bounded model/runtime configuration |
| D014 | Use advisory four-hour actor/session claims and full-history reconciliation | Reduce accidental overlapping work and recover superseded events without claiming transactional locks | Real usage exposes lease, scale or stronger isolation requirements |
