# EXP-001: controlled v1/v2 native baseline

Status: proposed; smoke execution is a prerequisite, not the final experiment.

Hypothesis: the v2/v1 throughput ratio depends on available execution and memory resources; measure instead of assuming SG2042 behavior.

Run upstream tests, then mine-mode v1/v2 with equal seeds/nonces at 1, 2, 4 and suitable higher thread counts. Alternate order, warm up, use at least three repeats of sufficient duration. Record CPU/cache/RAM/OS/toolchain details and thermal/power settings. Repeat hardware versus software AES only on an ISA that supports hardware AES.

Acceptance: every known reference matches; full logs and JSON stored; no skipped/failing correctness hidden. Report median and range for throughput, and hashes/J only with time-aligned power samples. Native measurements cannot establish SG2042 bottlenecks.

Follow-up: select a simulator that can reproduce exact workload behavior, then vary memory latency/cache/AES capacity independently in a calibrated model.
