# EXP-019: prepared native superscalar-program executor

Status: implementation in progress; no new execution or synthesis result yet.

Base is accepted merge `9d28cd8e6467fcc6eee9d3a623c38fd796c3cb2a`
(PR #78). This experiment implements one prepared native superscalar program
with the existing accepted integer multiplier. See the
[component contract](../rtl/execute/SUPERSCALAR.md).

The focused correctness gate will compare all 14 native opcode semantics, actual
generated prepared programs, every retirement and final registers against the
pinned native v2 reference. It will cover zero/512 instruction boundaries,
reciprocal metadata, aliases, sign extension, high products, held transfers,
service stalls, cancellation/reset and malformed inputs. Synthesis and mapped
comparison follow successful bounded correctness, with exact source, tools,
inputs, commands, resources and original failures retained.

Program preparation, reciprocal-table/image ownership, Argon2/cache initialization
and cache-line memory service remain explicit external inputs. The executor does
not implement the eight dependent program/XOR/address steps of a dataset item.
Measured component cycles and operation counts will be retained for the existing
feasibility work; generic synthesis will not select memory technology or imply
whole-machine performance, physical area or power.

Existing task #71 provides the execution-request and handoff record. Its completed
state is preserved. No new task issue, standing source mirror or automatic Git
synchronization is created. All earlier accepted sources and evidence remain
untouched.
