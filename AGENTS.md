# Agent instructions

Read README.md, memory/PROJECT.md, memory/STATE.md, memory/DECISIONS.md and memory/OPEN_QUESTIONS.md before work. Read the relevant experiment and evidence entries before making technical claims.

1. Work toward the next incomplete milestone in docs/ROADMAP.md. Keep changes scoped and reviewable.
2. Treat RandomX v2 as the primary workload and run v1 regression comparisons.
3. Do not modify vendor/randomx silently. Verify its manifest before building. Put proposed workload changes in separately reviewed patches with new test evidence and provenance.
4. Do not infer chip internals from RISC-V's open ISA. SG2042 RTL availability, X5 chip identity and X9 claims need evidence.
5. Preserve floating-point rounding, AES, integer wraparound, and exact hash behavior. Throughput improvements are worthless if hashes differ.
6. Run relevant checks. Store commands, tool versions, full logs, input seeds, configuration and failures. Record skipped tests explicitly.
7. Distinguish measured, simulated, estimated, reported, and unknown results. Never present modeled power as wall power. No performance claims from smoke runs.
8. Never automatically buy hardware, rent paid compute, fabricate silicon, change account permissions, or publish secrets. Routine code/research commits within the requested scope may proceed.
9. Before ending: update memory/STATE.md, append memory/SESSION_LOG.md, add consequential decisions, and connect results to an experiment. Git commits preserve this memory across sessions.
10. Leave clear next commands, blockers and acceptance criteria. Do not invent completed work or evidence.

Do not optimize processor RTL before establishing a validated workload baseline and agreeing a simulation model. This is a project phase gate, not a request to repeatedly ask permission for routine setup.
