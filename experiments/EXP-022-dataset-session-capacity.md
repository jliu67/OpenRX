# EXP-022: default-size dataset session capacity

Status: implementation and initial static review only. Runtime, mapping and
independent result acceptance are pending. Base is normal PR #81 merge
`a84602c5348723e4c388ccd50f3a16096f3054f9`, tree
`17b01d8f9bf0aeeaa8cf5b75f73f2b8b2be6df63`.

The accepted 16-bit executor namespace admits 65,535 programs between quiescent
resets. A default 8×2,048 hash needs 16,384 dataset items and 131,072 superscalar
program admissions. A 17-bit nonzero namespace still falls one program short.
The existing 8,191-item guard is therefore a real dependency, not a tuning knob.

The [new capacity namespace](../rtl/dataset_capacity/DATASET_CAPACITY.md) preserves
all accepted modules byte-for-byte. A session adapter captures an item descriptor,
allocates a monotonically increasing 32-bit namespace, privately resets the
unchanged item/executor, and launches it on the next edge. External cache and
instruction identities are the full 64-bit `{session, private_tag}`. Old sessions
are filtered before a response can reach a recycled private identity. Cancellation
and errors burn allocations; the namespace fails closed before wrap. A real
outer reset still requires externally quiescent providers.

The service widens reservation and seen ledgers to 32 bits and checks additions
in 64 bits. Every batch burns its full reservation at admission, with no refund.
The new wrapper elaborates the default workload with hardware dataset service;
legacy mode remains explicit and the old wrapper/accepted campaigns are preserved.
The adapter is expected to add one measured launch clock per item; raw child,
executor and session availability are separate, nested counters.

Planned evidence is one 16,384-item protocol stress batch, smaller exact exhaustion
and recovery cases, a short mapped subset and two native-equivalent 2×1 connected
profiles. The stress uses an explicitly declared identity-program derivative of
retained native-empty data; it is not a completed RandomX hash. Nineteen existing
deterministic reference files and accepted prepared cache/program/reciprocal data
are reused. No old component campaign or native gold generation is repeated.

Before any default full-hash run, use an admitted resource/runtime plan. The
known cache-0 item work alone suggests 874,905,600 session clocks for 16,384 items
(53,399 accepted-core + one adapter launch each). Adding an earlier full-hash
baseline and known input/program deltas gives a conditional scenario around
915.9 million modeled clocks. Different work/preparation/transport may change it;
this is an estimate, not a demonstrated default hash. Retained simulator-rate
scenarios suggest hours in Verilator or days in VVP, not a reliable time bound.
This increment does not launch that run.

[Evidence](../docs/validation/dataset-capacity-20261019/README.md) will record the
actual frozen source, consumed inputs, commands, results and independent review.
Host cache/superscalar/global reciprocal preparation, immutable physical memory
services, full canonical hardware hash and physical PPA remain unresolved.
