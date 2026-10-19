# Dataset item sessions and bounded hash capacity

This protocol extension adds a retained outer item namespace around the accepted
[`randomx_dataset_item`](../dataset/DATASET_ITEM.md). The accepted item, superscalar
executor, multiplier, dataset service and hash wrapper remain byte-identical.
The new modules are `randomx_dataset_item_session`,
`randomx_dataset_capacity_service` and
`randomx_prepared_dataset_capacity_hash_lifecycle`, all in this directory.

## Session adapter

`randomx_dataset_item_session #(MUL_RADIX4=1, SESSION_BITS=32)` preserves the
accepted item's request, result, cache/fetch metadata and commit/stage ports.
The four external cache/fetch request/response tag ports widen from 32 to 64 bits:

```text
external_tag[63:32] = current item-session namespace
external_tag[31:0]  = unchanged private item's accepted transport tag
```

Caller tags and image epochs remain 16 bits. The complete descriptor (caller
tag, epoch, full 64-bit item number, all eight counts and address-register bytes,
and reciprocal-table count) is captured on the outer item handshake. It is not
read live during launch or execution.

`SESSION_BITS` must be 1–32. The limit is calculated with a 64-bit shift:

```text
MAX_SESSIONS = (64'd1 << SESSION_BITS) - 1
```

The namespace counter starts at zero and allocates one through MAX_SESSIONS.
Every accepted descriptor consumes the next namespace, including an invalid
descriptor and work subsequently canceled or returning an error. Cancellation
never refunds or resets this counter. Once it reaches MAX_SESSIONS, future item
admission fails closed before wrap. The last accepted item and its held result
may still finish. Outputs `session_namespace[31:0]` and `sessions_used[31:0]`
expose the current captured namespace and lifetime accepted-descriptor count.
Unused upper namespace bits are zero in reduced-width configurations.

The independent `session_phase[1:0]` states are IDLE=0, LAUNCH=1 and ACTIVE=2.
The accepted item's original `phase[3:0]` output remains separate and unchanged.
A held child result remains in session ACTIVE until consumed; there is no
additional result-buffer state.

The private accepted item core is held in reset in IDLE. Thus the outer request
acceptance edge also samples that private reset. The captured descriptor is
presented in LAUNCH and accepted on the following edge, then the session enters
ACTIVE. Private item/executor generations may restart for each item because
none of their external packets can bypass the non-recycled outer namespace.
No accepted arithmetic or instruction decoder is changed.

Response valid reaches the private core only in ACTIVE and only when the full
outer 32-bit prefix matches the captured session namespace. Old namespaces drain
in every active session state before the low 32 bits are interpreted by the
core. IDLE drains all packets, including the most recently retired namespace.
A matching-prefix packet in LAUNCH is held until ACTIVE. Within ACTIVE, the
unchanged core owns low-tag, epoch, program, index and PC checks, matching early
responses, stale low tags and provider-error handling. All cache/fetch tags and
metadata must remain stable under backpressure.

Reset/cancel suppress transfer enables and commit/stage valids immediately;
current control clears on a rising edge. Cancel abandons the item without a
result and retains the outer namespace counter. The next IDLE/request edge
resets the private child before reuse. External `rst` resets the outer namespace
as well, so it still requires genuine provider quiescence and removal of all
pre-reset packets. Private reset is not permission to recycle the outer namespace.

`rsp_cycles[63:0]` is an independent measured counter from outer descriptor
acceptance to child-result availability. It counts LAUNCH and subsequent ACTIVE
clocks until the first child result is available, then freezes across held
response clocks. `rsp_core_cycles[63:0]` exposes the accepted child's unchanged
counter; `rsp_exec_cycles` remains the unchanged sum of terminal executor cycles.
With the intended one-edge launch, session latency is expected to exceed raw
child latency by one clock, including invalid-descriptor returns. This is a
validation expectation, not a synthetic addition to the child counter.

## Capacity service

`randomx_dataset_capacity_service` derives from the accepted service, replacing
its direct item instance with the session adapter. Parameters are
`ITEMS_PER_BATCH=1`, `MUL_RADIX4=1` and `SESSION_BITS=32`.
`ITEMS_PER_BATCH` must be positive and at most both 65,535 and MAX_SESSIONS.
Invalid widths or batches produce explicit elaboration errors; a reduced-width
batch larger than its namespace is not silently denied forever.

The full batch reservation is burned on batch admission, before any item is
requested. Errors, cancellation and successful completion do not refund it.
`items_reserved[31:0]`, `items_remaining[31:0]` and the per-batch seen counter
are widened to 32 bits. Admission checks the 64-bit sum before assigning its
32-bit result:

```text
{32'b0, items_reserved} + ITEMS_PER_BATCH <= MAX_SESSIONS
items_remaining = MAX_SESSIONS - items_reserved
```

At most one item is owned at once, and at most ITEMS_PER_BATCH valid item
requests can consume namespaces in a batch. The actual namespace count is
therefore bounded by conservative reservations, including aborted attempts.
Future-batch exhaustion does not gate the requests or result of an already
reserved batch. Actual request/completion statistics remain separate 64-bit
counters and survive cancel.

All accepted service behavior otherwise remains: captured immutable descriptors,
full-width aligned dataset address bound `0x0000000081ffff80`, item number
`address >> 6`, full 32-bit dataset tag echo, zero-data matching error responses,
one architectural dataset XOR in the existing engine, and no work for prefetch
hints. The original service phase and item observations retain their names.
`item_req_*` now observes the session descriptor boundary; `item_rsp_cycles`
reports measured session availability. Additional passive diagnostics are:

| Service ports | Meaning |
|---|---|
| `item_session_phase[1:0]` | Session IDLE/LAUNCH/ACTIVE state |
| `item_namespace[31:0]` | Captured current namespace |
| `item_sessions_used[31:0]` | All accepted session descriptors, retained across cancel |
| `item_rsp_core_cycles[63:0]` | Unchanged private item availability count |

`item_phase`, instruction commits and completed-XOR stage observations continue
to describe the actual accepted child. Cache/fetch tags are 64 bits throughout
the new service and its providers; truncating an external replay tag is invalid.

## Capacity hash wrapper

`randomx_prepared_dataset_capacity_hash_lifecycle` is a separate derivative of
the accepted wrapper. Its original lifecycle instance is still `lifecycle`.
It keeps `HARDWARE_DATASET=0`, the existing workload defaults (8 programs and
2048 iterations), and all old dataset-service behavior in disabled mode. It adds
`DATASET_SESSION_BITS=32` and passes it to the capacity service. Added prepared
cache/fetch tag ports are 64 bits, budget observations are 32 bits, and the four
session diagnostics above have the `dataset_` prefix.

In hardware mode a complete `N=PROGRAMS*ITERATIONS` reservation is required on
the same edge as hash acceptance. A default `N=16384` now fits the default
session namespace; legal elaboration and admission do not establish a completed
full-hash result. The primary lifecycle's own generation and other admission
limits remain in force. Mode zero omits the capacity service and preserves the
primary lifecycle's legacy ports and behavior.

The existing cancel-retained hash-generation mirror still binds the high half
of the original 32-bit dataset tag. Prepared image epoch and session namespace
are separate identities. Legacy dataset replies drain without affecting
hardware-mode results. Lifecycle error cancels the service; normal result
consumption only ends its batch. Neither event refunds reservations/namespaces.

Session and raw child cycles are nested measurements inside dataset/hash
execution time. They are not extra disjoint phases to add to the outer hash
total. A dedicated session-phase ledger can account for its one launch clock
without changing the accepted child's phase definitions.

## Scope and validation boundary

Native item arithmetic, cache-XOR recurrence and program semantics are reused
unchanged. Prepared cache bytes, superscalar programs, the global reciprocal
table and their immutable tagged services remain external. Capacity validation
can cross the former 8191-item boundary with small public descriptors and test
final fail-closed exhaustion using a reduced SESSION_BITS value. Passive RTL
hierarchical observation of actual child executor handshakes may substantiate
that stress count; it is not a mapped public-port observation or forced state.
A bounded retained-gold connected check is separate from a full default hash.
No autonomous preparation, physical cache implementation, physical PPA or
architecture selection follows from this capacity increment. Runtime evidence
and independent review must qualify all measured acceptance claims separately.
