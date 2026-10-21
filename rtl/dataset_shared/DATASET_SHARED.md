# Finite shared dataset-service transport

This directory adds a bounded two-client experiment above the unchanged accepted
[`randomx_dataset_item_session`](../dataset_capacity/randomx_dataset_item_session.v).
Two independently arbitrated channels share prepared instruction and cache
services. Each channel has one credit, including its captured request, issued
request, response wait and held response. This is not a production engine-count
decision or a physical service/performance result.

## Generic channel

`randomx_dataset_shared_channel` has `TAG_WIDTH=64`, `REQ_WIDTH=28` and
`RSP_WIDTH=190` defaults. Widths must be positive; the two-client count is fixed.
Each packed client vector puts client 0 in the low slice and client 1 in the high
slice. Request and response tags are separate from opaque payloads.

| Ports | Width / meaning |
| --- | --- |
| `client_cancel` | One bit per client |
| `client_req_valid`, `client_req_ready` | Two ready/valid request lanes |
| `client_req_tag`, `client_req_payload` | Two tag and request payload slices |
| `client_rsp_valid`, `client_rsp_ready` | Two ready/valid response lanes |
| `client_rsp_tag`, `client_rsp_payload` | Two tag and response payload slices |
| `backend_req_valid`, `backend_req_ready` | One request ready/valid channel |
| `backend_req_tag` | `TAG_WIDTH+1`: `{captured_client_id, full_client_tag}` |
| `backend_req_payload` | Captured opaque request payload |
| `backend_rsp_valid`, `backend_rsp_ready` | One response ready/valid channel |
| `backend_rsp_tag`, `backend_rsp_payload` | Echoed complete backend identity and opaque response |

At an empty-channel frontend handshake, the channel captures the complete tag,
payload and owner. It never reads live frontend descriptor fields afterward.
Request readiness selects one offered, uncancelled lane. Round-robin preference
starts at client 0 after hard reset and moves to the other client only when a
frontend request is captured. There is no same-edge credit refill when a reply
completes. Finite-backpressure fairness assumes that accepted backend requests
eventually return and that an uncancelled owner eventually accepts its response;
arbitration cannot overcome an indefinitely withheld service or response consume.

The stored backend descriptor and request valid remain stable until the backend
request handshake. The extra client bit is mandatory: independent accepted
session clients may generate identical 64-bit tags. A response matches only the
complete client-qualified identity. Wrong identities drain as orphans without
releasing the current credit, even when their lower 64 bits match an owner.

Each generic caller must not reuse its own full tag while any packet bearing
that identity may remain. The extra client bit cannot distinguish identical
65-bit packets after illegal same-client identity reuse. The accepted session's
non-recycled namespace, no-refund cancellation and fail-closed exhaustion provide
that lifetime guarantee, subject to its genuinely quiescent hard-reset contract.
This fabric is not a replacement generation allocator and does not extend that
lifetime or make arbitrary duplicated identities safe.

A matching response arriving early is held until the backend request is
accepted. Same-edge backend request and matching response handshakes are
supported; no frontend response can be accepted before that backend request
handshake. A matching response payload is passed unchanged to the owning client.
The fabric does not validate epoch, program, PC, cache index, error or reciprocal
metadata. The unchanged accepted core owns those checks, including error
behavior; a matching malformed packet must not be silently reclassified as an
orphan. Inactive client response lanes are zero.

Backend response valid, full tag and payload must remain stable while response
ready is low. The response path is transparent rather than a second response
queue. Its producer must obey that existing ready/valid rule. A ready/valid
provider must also avoid a combinational acceptance loop between its request
ready and response ready; a finite registered service satisfies that condition.

## Cancellation and hard reset

Cancellation suppresses the affected client's returned valid immediately and
prevents capture of a new request from that lane. If it owns the credit, a sticky
cancelled-owner flag retains the captured descriptor and identity. A queued
backend request continues unchanged until accepted. Its matching reply then
drains independently of the cancelled client's readiness before the credit is
released. Cancellation wins over a same-edge response delivery. It never clears
diagnostics, changes a captured tag, refunds a namespace or resets the accepted
session's lifetime counter.

The existing [session reset contract](../dataset_capacity/DATASET_CAPACITY.md)
is unchanged. External hard reset recycles the session namespace, so both
clients, both fabric channels and every provider must be genuinely quiescent,
with every pre-reset packet removed. A client-qualified 65-bit tag does not make
arbitrary late pre-hard-reset packets safe. The wrapper's `quiescent` output is
only `!fetch_busy && !cache_busy`; it does not certify client inactivity, absence
of a held final item, or an empty external provider. Hard reset must not be used
as a shortcut to discard an outstanding cancelled request.

## Two-channel wrapper and packing

`randomx_dataset_shared_fabric` instantiates independent fetch and cache channels.
It exposes the generic channel ports with `fetch_` and `cache_` prefixes, plus
shared `clk`, `rst`, `client_cancel[1:0]` and fabric-local `quiescent`. It performs
no arithmetic, instruction decoding, cache access or metadata interpretation.

| Channel | Client tag | Backend tag | Request payload | Response payload |
| --- | ---: | ---: | ---: | ---: |
| Fetch | 64 | 65 | 28 | 190 |
| Cache | 64 | 65 | 41 | 554 |

Payload concatenations, from most to least significant field:

```text
fetch request  = {epoch[15:0], program[2:0], pc[8:0]}
fetch response = {epoch[15:0], program[2:0], pc[8:0], error, rcp_valid,
                  rcp_index[31:0], rcp_value[63:0], instruction[63:0]}
cache request  = {epoch[15:0], program[2:0], index[21:0]}
cache response = {epoch[15:0], program[2:0], index[21:0], error, data[511:0]}
```

These transport widths describe this experiment's RTL interface, including
metadata. They do not establish an off-chip bus, physical placement, controller
capacity, latency, energy or achieved RandomX throughput.

## Diagnostics and clock domains

`busy`, `issued`, `owner` and `owner_cancelled` expose credit ownership. `owner`
is meaningful only while busy. The sticky cancellation also appears immediately
when the live owner cancel input is asserted. One observed busy credit is the
channel's maximum queue high-water mark; the bench must separately observe any
external provider queue and per-client architectural state.

All counters are 64-bit unsigned values, with per-client pairs packed into
128-bit vectors, client 0 low. They reset only on genuine hard reset, persist
across cancel, and wrap modulo 2^64. Bounded validation must not confuse these
diagnostic counters with a reusable transport identity allocator.
Generic cell counts include the always-on 64-bit diagnostic counters and wide
payload gating; they are not optimized production-control or physical PPA results.

| Counter | Edge counted |
| --- | --- |
| `accepted_count` | Frontend request handshakes, per client |
| `delivered_count` | Uncancelled frontend response handshakes, per client |
| `arbitration_wait_cycles` | Uncancelled frontend valid with readiness low, per client; includes full-credit wait, not only a simultaneous tie |
| `backend_request_count` | Backend request handshakes |
| `backend_response_count` | Every backend response handshake, including cancelled and orphan packets |
| `cancelled_response_count` | Matching owned response drained after cancellation |
| `orphan_response_count` | Backend response handshake with a different complete identity, or no current owner |
| `occupied_cycles` | Each non-reset edge with pre-edge busy, including backend request wait, response wait and held response; excludes the initial capture edge |

At any non-reset observation edge, without counter wrap:

```text
sum(accepted_count) = sum(delivered_count) + cancelled_response_count + busy
backend_request_count = sum(delivered_count) + cancelled_response_count + issued
backend_response_count = sum(delivered_count)
                       + cancelled_response_count + orphan_response_count
```

At genuine quiescence these reduce to:

```text
sum(accepted_count) = backend_request_count
                   = sum(delivered_count) + cancelled_response_count
backend_response_count = sum(delivered_count)
                       + cancelled_response_count + orphan_response_count
```

Batch elapsed clocks, each accepted core's availability/held-result clocks,
fabric occupancy and arbitration waits are distinct, overlapping measurements.
Do not add nested client or channel clocks to batch elapsed clocks. Successful
native comparisons, mapped parity and generic cell counts must remain separate
from physical PPA/frequency, memory-service and whole-machine feasibility gates.
