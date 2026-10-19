# EXP-022: default-size dataset session capacity

Status: bounded validation, terminal integrity and independent scientific review
accepted with no blockers. Publication-head review and hosted checks are separate.
Base is normal PR #81 merge `a84602c5348723e4c388ccd50f3a16096f3054f9`. Public executed code
is [`aa6fe690`](https://github.com/jliu67/OpenRX/commit/aa6fe690d3a811440c75a501988f17df887ccd90),
exact tree `1bcde0790ca3bd05c4acc0cb7a8b35eea7752ca3`.

The accepted private executor namespace admits 65,535 programs between quiescent
resets. A default 8×2,048 hash needs 16,384 dataset items and 131,072 private program
admissions. A 17-bit nonzero namespace still falls one program short. The former
8,191-item guard is a real dependency.

The [new capacity namespace](../rtl/dataset_capacity/DATASET_CAPACITY.md) preserves
accepted modules byte-for-byte. A session adapter captures the complete descriptor,
allocates a monotonically increasing 32-bit namespace, privately resets the unchanged
item/executor, and launches on the next edge. External cache/fetch tags are full
64-bit `{session, private_tag}`. Old prefixes are filtered before private IDs are
reused. Cancellation and errors burn allocations; the namespace fails closed before
wrap. A real outer reset requires externally quiescent providers. Wider checked
reservations burn each whole admitted batch without refunds.

The default hardware workload now elaborates. Actual bounded checks pass 16,384
identity-derived item completions and 131,072 observed private program admissions,
60 new units, poisoned descriptor capture, exact reduced-namespace exhaustion,
one complete real native item, short mapped parity, two complete native 2×1 profiles
and five recovery prefixes. No old component campaign or native gold/cache/program
preparation is repeated. Nineteen deterministic gold files and 52 unique prepared
context/test files are reused and actually verified.

The adapter adds one measured launch clock per item. Native case0 measures
53,325 executor / 53,399 core / 53,400 session clocks. Ideal/stalled 2×1 outer totals
are 641,182 / 1,754,985; item availability is 106,800 / 171,084, nested in execution.
The ideal outer and dataset-wait delta against the retained software baseline is
exactly 106,800. Reduced SESSION_BITS4/N1 mapping is 48,190 generic cells, 5,199
DFF cells and zero latches; it does not establish full-capacity or physical PPA.

The stress uses two explicit zero-effect instructions and retained native-empty
assertions. It is a protocol-capacity proof, not a completed default RandomX hash.
Connected control recovery ends at a changed native seed/generation prefix; full
recovered hashes are not claimed. Complete raw originals and original runner
scientific-unverified flags remain preserved, with independent bounded acceptance
recorded separately in [evidence](../docs/validation/dataset-capacity-20261019/README.md).

Before any default full-hash run, use its own reviewed resource/runtime admission.
The known cache0 item model suggests 874,905,600 session clocks; adding retained
full-hash baseline and known input/program deltas gives a conditional 915,887,592
modeled-clock scenario. Retained simulator scenarios suggest about 15.22 hours in
Verilator or 5.68 days in VVP; they are not measured full-hash results or reliable
bounds. This increment launches no long default hash. Autonomous cache/program/
global reciprocal preparation, physical services, full canonical hardware hash,
physical PPA and architecture selection remain unresolved. Parent owns merge.
