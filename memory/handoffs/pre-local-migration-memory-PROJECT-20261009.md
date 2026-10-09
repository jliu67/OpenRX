# Project memory

## User intent
Build an organized research project toward a programmable RISC-V mining processor that improves on the Antminer X5 and explores the X9's advertised performance ambition. Use AI assistance for research, implementation, testing and experiment tracking. Persistent Markdown memory and the actual RandomX v2 code are requested.

The user has named the project OpenRX and designated this repository as the canonical project board, persistent memory and communication surface for collaborating agents. Keep progress, tested results, blockers, consequential decisions and explicit handoffs in version-controlled files and linked GitHub issues, not only in chat. The remote was renamed to jliu67/OpenRX on 2026-10-08; repository ID 1409576804 and its history are unchanged. Historical OpenRandomX links may redirect, but connector API calls must use the current name.

## Durable constraints
- RandomX v2 is the primary target; retain v1 comparison and compatibility.
- Start with reproducible workload measurements and architecture research.
- Aim for hashes per joule at a declared measurement boundary, while considering silicon area and total system cost.
- Avoid premature fabrication or hardware spending.
- RISC-V is an open ISA, not a guarantee that any processor's implementation is open.
- Programmability supports updates but cannot guarantee future mining competitiveness.

## Scope now
Pinned upstream source, correctness checks, benchmark tooling, evidence tracking, simulator shortlist, and a first experiment. Phase 1 source analysis and tooling are recorded in docs/PHASE1.md; current completion/remaining work is authoritative in memory/STATE.md and docs/TASKS.md. No RTL or made-up X5 model.

## Prior conversation claims requiring validation
X5 uses SG2042; X9 achieves 1 MH/s at 2472 W; public X9 shipments were cancelled; Monero has not activated v2. These are leads, not verified project facts. Recheck current primary sources before relying on them.
