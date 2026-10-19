# Prepared dataset service and hash wrapper

`randomx_dataset_service` translates one tagged dataset byte-address request into
one call to the unchanged [`randomx_dataset_item`](../dataset/DATASET_ITEM.md). The optional
`randomx_prepared_dataset_hash_lifecycle` wraps the unchanged
[`randomx_prepared_hash_lifecycle`](../hash/randomx_prepared_hash_lifecycle.v).
It connects this service to the existing dataset port without modifying the
accepted lifecycle, engine, item, superscalar executor or multiplier.

## Service ports and transfers

The service parameters are `ITEMS_PER_BATCH=1` and `MUL_RADIX4=1`. The first must
be 1–8191; unsupported values instantiate a descriptive elaboration error.
`MUL_RADIX4` is passed to the accepted item core and preserves its 0/1 contract.
All transfers occur on rising edges with valid and ready asserted. Reset and
cancel suppress transfer enables immediately and clear current state on an edge.

| Ports | Meaning |
|---|---|
| `clk`, `rst`, `cancel` | Clock, quiescent hard reset and current-batch abort |
| `batch_valid`, `batch_ready`, `batch_end` | Atomic batch admission and successful-batch release |
| `batch_generation[15:0]`, `image_epoch[15:0]` | Expected high half of lifecycle dataset tags; independently captured immutable prepared-image identity |
| `counts[79:0]`, `address_regs[63:0]`, `rcp_count[31:0]` | Eight 10-bit program counts, eight full address-register bytes and shared reciprocal-table count; captured only at batch admission |
| `ds_req_valid`, `ds_req_ready`, `ds_req_addr[63:0]`, `ds_req_tag[31:0]` | One full-width dataset byte-address request |
| `ds_rsp_valid`, `ds_rsp_ready`, `ds_rsp_tag[31:0]`, `ds_rsp_data[511:0]`, `ds_rsp_error` | Held dataset line or matching zero-data error |
| `cache_req_*`, `cache_rsp_*`, `fetch_*`, `fetch_rsp_*` | Unchanged item core's externally prepared cache and instruction/reciprocal services; exact widths and metadata are in the item contract |
| `phase[1:0]`, `item_phase[3:0]` | Service states IDLE=0, ITEM=1, ERROR=2; accepted item control state |
| `generation_exhausted`, `batch_active` | Future-batch admission exhausted; current context owned |
| `items_reserved[13:0]`, `items_remaining[13:0]` | Lifetime conservative reservation and `8191-items_reserved` |
| `items_requested[63:0]`, `items_completed[63:0]` | Actual child requests and successful child result transfers |
| `ds_requests[63:0]`, `ds_responses[63:0]` | Actual dataset-port request and response transfers, including errors |
| `item_req_*`, `item_rsp_*`, `item_commit_*`, `item_stage_*` | Passive child-boundary and native-instruction/cache-XOR observations described below |

The service captures all descriptors and the epoch on the batch handshake.
They remain fixed until that batch ends or is canceled, regardless of later
changes at the input ports. Each item still validates all eight captured
program descriptors before execution. The external owner must bind the epoch
to one immutable cache, program set and global reciprocal table; echoed metadata
alone does not establish those assets' provenance.

A valid dataset request satisfies all three conditions:

```text
address[5:0] = 0
address <= 0x0000000081ffff80
tag[31:16] = captured batch_generation
```

The bound is the last complete 64-byte line in the pinned native dataset size
`0x81ffffc0`. No address bits are discarded during validation. The native item
number is the unsigned full-width `address >> 6`; `item_req_tag` is the original
`ds_req_tag[15:0]`, and `item_req_epoch` is the captured image epoch. The original
full 32-bit dataset tag is saved and echoed unchanged on the response.

At most one item is outstanding. For a valid request, dataset acceptance and
child acceptance occur on the same edge. No launch FIFO or response register
adds a clock. The item core owns the held result, including its data, tag and
counters. A following request waits until that result has been consumed.
An invalid address/tag or a request beyond this batch's reserved count instead
returns a held error without launching the item core.

A successful child result must echo the low 16-bit caller tag and captured
epoch, report no error and have exactly eight completed stages. Otherwise the
service returns `ds_rsp_error=1`, zero data and the saved matching dataset tag.
The item's diagnostic prefix and counters remain visible on `item_rsp_*` but
are never supplied as a usable dataset line. The bridge performs no register
XOR: the unchanged engine applies the architectural dataset XOR exactly once.
Prefetch hints do not launch extra items or consume reservations.

## Batch budget, cancellation and reset

Every accepted batch burns its full `ITEMS_PER_BATCH` reservation immediately,
including an attempt later rejected by initialization or aborted before its
first dataset request. Ordinary success, item/provider error, invalid request
and cancellation never refund reservations. Before admission,

```text
items_reserved + ITEMS_PER_BATCH <= 8191
```

must hold and the child must still admit a future item. The entire lifetime
reservation ledger survives `cancel`. `generation_exhausted` can become true
while a final admitted batch is active; it gates future batches and does not
truncate already reserved work. For example `ITEMS_PER_BATCH=2` with one item
remaining blocks another batch. Actual-transfer counters are separate from
this reservation and also survive cancellation.

This conservative limit bounds child superscalar generation use by
`8*8191=65528`, even if every requested item executes eight programs. The child
also retains and independently checks its exact accepted-generation ledgers.
No generation is recycled at a hash, item, stage or cancel boundary. `rst` is
the sole ledger reset and requires the external instruction/cache services to
be quiescent and discard all pre-reset packets before reuse.

`cancel` abandons the current batch and current child with no result. All
accepted generation IDs and batch reservations stay burned. Instruction/cache
stale-packet handling remains that of the unchanged item/executor: old
transaction tags drain; malformed current-tag epoch/program/index/PC packets
produce an item error. `batch_end` releases an ordinarily completed batch when
the service is idle. It is not an abort input and must not be used while an
item or held service response is pending.

## Wrapper ports and modes

`randomx_prepared_dataset_hash_lifecycle` retains every existing lifecycle
parameter and port, and adds `HARDWARE_DATASET=0` and
`DATASET_MUL_RADIX4=1`. Its accepted primary instance is named `lifecycle`.

In mode zero, the primary lifecycle's dataset inputs and outputs are passed
through unchanged. The service is not instantiated, so the historical default
8-program × 2048-iteration configuration remains elaboratable. Prepared-service
outputs and child observations are zero; extra prepared-service inputs are
ignored. The `dataset_req_ready` and `dataset_rsp_*` observations still report
the actual selected legacy dataset bus.

In mode one, `N=PROGRAMS*ITERATIONS` is the service's `ITEMS_PER_BATCH`; it must
be 1–8191. Thus the historical default `N=16384` is explicitly unsupported in
hardware-dataset mode and fails elaboration rather than deadlocking admission.
A bounded configuration such as two programs and one iteration uses `N=2`.

| Added wrapper ports | Meaning |
|---|---|
| `req_dataset_epoch[15:0]`, `req_dataset_counts[79:0]`, `req_dataset_address_regs[63:0]`, `req_dataset_rcp_count[31:0]` | Prepared context captured on the outer hash request handshake |
| `dataset_cache_req_*`, `dataset_cache_rsp_*`, `dataset_fetch_*`, `dataset_fetch_rsp_*` | External cache and prepared instruction/reciprocal services |
| `dataset_service_phase`, `dataset_item_phase`, `dataset_generation_exhausted`, `dataset_batch_active` | Prefixed service status |
| `dataset_items_reserved`, `dataset_items_remaining`, `dataset_items_requested`, `dataset_items_completed`, `dataset_ds_requests`, `dataset_ds_responses` | Prefixed lifetime ledgers and transfer statistics |
| `dataset_item_req_*`, `dataset_item_rsp_*`, `dataset_item_commit_*`, `dataset_item_stage_*` | Prefixed passive item observations |
| `dataset_req_ready`, `dataset_rsp_valid`, `dataset_rsp_ready`, `dataset_rsp_tag`, `dataset_rsp_data`, `dataset_rsp_error` | Actual selected dataset transport observed by the primary lifecycle |

Outer `req_ready` requires both primary readiness and complete service batch
capacity. The primary request acceptance and service batch acceptance occur on
the same edge. A separate wrapper counter mirrors the primary's exact accepted
hash generation, retains it over cancel and supplies counter+1 to that batch.
It does not derive identity from the primary's cancel-cleared current context.
The prepared epoch is independent of this transport generation. The wrapper's
original `generation_exhausted` output combines the primary and dataset
admission limits; `dataset_generation_exhausted` reports the latter separately.

The original `ds_req_valid/addr/tag` and `ds_prefetch_valid/addr` outputs remain
visible as observations in mode one. External legacy `ds_req_ready` is ignored.
Legacy `ds_rsp_*` packets drain whenever reset/cancel permits transfers, and
none of their data, tags or error flags affect the primary lifecycle. The
selected internal service bus is exposed on `dataset_req_ready/dataset_rsp_*`.
No live software native-Light dataset callback is required in this mode.

The service receives `cancel || lifecycle.error_valid`. Every lifecycle error
therefore abandons any private item and clears the captured batch context while
retaining reservation/generation ledgers. Ordinary success only releases the
batch when the held hash result is consumed; it never resets or cancels the
child. The original held hash error/result behavior remains in the primary.

## Observations, clocks and scope

`item_req_*` exposes valid/ready, caller tag, epoch and native item number.
`item_rsp_*` exposes valid/ready, raw data/error/stage/PC, completed stages,
retired/multiply counts, item cycles and executor cycles, with exactly the item
contract's widths. `item_commit_*` and `item_stage_*` expose actual native
instruction writes and completed cache XORs. They do not drive providers.

On the valid request path the bridge adds no launch or return clock. Child
availability latency is measured from its accepted descriptor to result
availability; response backpressure is separate. Item cycles, summed executor
cycles and provider stalls are nested subsets of hash execution time. They
must not be added to the existing disjoint outer hash phase totals. Malformed
transport errors are bridge responses, not successful item measurements.

The new boundary still requires externally prepared Argon2 cache bytes, native
superscalar programs, the global reciprocal table and correctly tagged immutable
cache/instruction services. It adds no cache initialization, program preparation,
physical memory implementation, full default-hash validation or physical PPA
claim. Source-level contracts here require separate admitted RTL/native/mapped
validation and independent review before a measured acceptance claim.
