# Prepared native dataset-item controller

`randomx_dataset_item #(MUL_RADIX4=1)` computes one 64-byte native dataset item
from eight immutable, externally prepared superscalar programs, their shared
reciprocal table, and an externally prepared 256 MiB cache. It instantiates the
unchanged `randomx_superscalar_execute` and a separate unchanged `randomx_mul64`
for seeding. `MUL_RADIX4` accepts the existing multiplier's values 0 and 1.

## Port contract

Every transfer occurs on a rising clock edge with both valid and ready high.
`rst` and `cancel` are active high. They suppress all interface transfer enables
and observation valids immediately; clearing internal state requires a rising
edge. Requests and responses remain stable while held. One item is owned at a
time; no new item is accepted until the held result has been consumed.

| Ports | Width and meaning |
|---|---|
| `clk`, `rst`, `cancel` | Clock, hard reset, current-item cancellation |
| `req_valid`, `req_ready` | Item descriptor handshake |
| `req_tag`, `req_epoch` | 16 bits each; caller identity and immutable prepared-image epoch |
| `req_item` | Full unsigned 64-bit native helper item number |
| `req_counts` | 80 bits; program `i` count at `[10*i +: 10]`, allowed 0–512 |
| `req_address_regs` | 64 bits; program `i` full address-register byte at `[8*i +: 8]`, allowed 0–7 |
| `req_rcp_count` | Unsigned 32-bit size of the shared prepared reciprocal table |
| `rsp_valid`, `rsp_ready` | Held result handshake |
| `rsp_tag`, `rsp_epoch` | Captured 16-bit caller tag and epoch |
| `rsp_data` | 512 bits; successful final item or documented error prefix below |
| `rsp_error`, `rsp_error_stage`, `rsp_error_pc` | Error flag, 3-bit stage, 9-bit instruction PC |
| `rsp_completed_stages` | 4 bits; number of completed cache XORs, 0–8 |
| `rsp_retired`, `rsp_muls` | 13 bits each; aggregate actual superscalar retirements/multiplications, up to 4096 |
| `rsp_cycles`, `rsp_exec_cycles` | 64 bits each; item availability latency and summed terminal executor latency |
| `cache_req_valid`, `cache_req_ready` | One immutable cache-line request handshake |
| `cache_req_tag`, `cache_req_epoch` | 32-bit outer transaction identity, captured 16-bit epoch |
| `cache_req_program`, `cache_req_index` | 3-bit program/stage and 22-bit cache-line index |
| `cache_rsp_valid`, `cache_rsp_ready` | Cache packet handshake |
| `cache_rsp_tag`, `cache_rsp_epoch`, `cache_rsp_program`, `cache_rsp_index` | Exact request identity/metadata echoes |
| `cache_rsp_data`, `cache_rsp_error` | 512-bit cache line and provider error flag |
| `fetch_valid`, `fetch_ready`, `fetch_tag`, `fetch_epoch`, `fetch_pc` | Unchanged executor fetch handshake, 32-bit tag, 16-bit epoch, 9-bit PC |
| `fetch_program` | Added 3-bit program selector, stable with a held fetch |
| `fetch_rsp_valid`, `fetch_rsp_ready` | Instruction packet handshake |
| `fetch_rsp_tag`, `fetch_rsp_epoch`, `fetch_rsp_program`, `fetch_rsp_pc` | Echoed 32/16/3/9-bit instruction identity |
| `fetch_rsp_instruction`, `fetch_rsp_error` | Raw prepared 64-bit instruction and provider error |
| `fetch_rsp_rcp_valid`, `fetch_rsp_rcp_index`, `fetch_rsp_rcp_value` | Prepared reciprocal validity, full 32-bit index, full 64-bit value |
| `commit_valid`, `commit_program`, `commit_pc`, `commit_opcode`, `commit_r` | One-cycle actual native instruction observation: stage 3, PC 9, opcode 8, post-instruction registers 512 bits |
| `stage_valid`, `stage_program`, `stage_cache_index` | One-cycle completed-XOR observation and saved 3/22-bit stage/index |
| `stage_r`, `stage_selected`, `stage_program_cycles` | Post-XOR registers 512, post-XOR selected register 64, this program's terminal executor cycles 64 |
| `generation_exhausted` | Fail-closed future-item admission status; current owned item may still finish |
| `phase` | 4-bit public control state, encoded below |

All descriptor fields are captured together. All eight count/address bytes are
validated before arithmetic or external requests. The first invalid stage in
ascending order returns a held error with zero data, zero counters and PC zero.
Counts zero and 512 are supported. The image epoch binds the eight descriptors,
program instructions, shared reciprocal table and cache to one immutable
prepared snapshot. The external owner must establish this binding; transport
echoes do not establish how the images were generated.

Register `q` occupies bits `[64*q +: 64]`; byte zero is bits `[7:0]`. Cache
exports and native comparison explicitly use little-endian 64-bit lanes.

## Exact native operation

The source is pinned RandomX `aaafe71322df6602c21a5c72937ac284724ae561`,
[`dataset.cpp`](../../vendor/randomx/src/dataset.cpp), lines 150–189. With all
addition/multiplication modulo `2^64`, initialization is:

```text
v = item
r[0] = (item + 1) * 0x5851f42d4c957f2d
r[1] = r[0] XOR 0x810a978a59f5a1fc
r[2] = r[0] XOR 0xa77099df38c2d846
r[3] = r[0] XOR 0x8126b91cbf22495c
r[4] = r[0] XOR 0x494d2597179f8a62
r[5] = r[0] XOR 0x9237efb9ceaaec0c
r[6] = r[0] XOR 0x2f2a56746ce62d78
r[7] = r[0] XOR 0x84853bf7b62ce54e
for i = 0..7:
    saved_index = v & 0x003fffff
    r_exec = executeSuperscalar(r, prepared_program[i], shared_reciprocals)
    cache_line = immutable_cache[saved_index]
    r = r_exec XOR cache_line
    v = r[address_reg[i]]
return r
```

The implementation saves the old address index before execution, then requests
the cache line after execution. This serialization preserves native semantics
because the cache is immutable. The next address is selected after XOR;
executor `rsp_selected` is deliberately unused. Registers carry between stages;
there is no reseeding or ninth cache read.

The default cache is 268,435,456 bytes with 4,194,304 lines of 64 bytes. A line's
byte offset is `{cache_req_index,6'b0}`; its maximum is `0x0fffffc0`. The mask is
applied to the old register value before multiplying by 64. It is distinct from
the VM dataset byte-alignment mask. `initDatasetItem` accepts any `uint64_t`, so
this controller does not truncate or clamp item numbers. In particular item
`0xffffffffffffffff` seeds register zero with zero. Bounds for writing an actual
dataset allocation remain the external caller's responsibility.

## Transaction identity and cancellation

Every accepted outer descriptor advances a retained 16-bit generation, including
invalid descriptors. Cache tag is `{generation, caller_tag}`. A cache request
also carries epoch, program/stage and line index. Only a current-tag response in
`CACHE_WAIT`, following an accepted request, can update cache data. Incorrect
epoch/stage/index or a provider error produces a held error before XOR. An old
stage packet with the same outer tag is malformed matching traffic, even when
the line index happens to repeat.

Other outer cache tags drain in every active state. Current-tag packets are held
during seed/execution/request/XOR states until `CACHE_WAIT`; IDLE and RETURN may
drain them without effects. A matching early cache response remains held through
the cache-request acceptance edge and can transfer on the following edge.

The unchanged executor allocates a distinct 16-bit generation for each accepted
program and retains it across cancel. Instruction requests additionally expose
the current program number. A wrong echoed program is forwarded as a provider
error to the executor, which checks it only for an accepted current-tag fetch.
Stale executor transaction tags drain through the unchanged executor.

The controller mirrors actual accepted executor descriptors. New item admission
requires this ledger to be at most `65527` (`0xfff7`), reserving eight remaining
program generations, and requires the outer generation to be below `0xffff`.
Cancellation does not refund accepted program or outer generations. Admission
fails closed before either namespace can wrap; a currently owned item still
uses its reserved capacity to finish. No ordinary cancellation, stage boundary
or item boundary resets the executor generation.

Cancellation clears current control, data, counters and observations, and
resets the private seed multiplier and current executor operation on a clock
edge. It produces no result. Both generation ledgers survive. Hard reset clears
both ledgers and the executor generation, and therefore requires the external
instruction/cache services to discard all pre-reset replies before reuse.

## Errors, observations and clocks

`rsp_data` changes only at successful seed completion and completed cache XORs.
Descriptor/seed errors return zero. Instruction/service errors before the first
XOR return the seeded register vector; later errors return the last completed
post-XOR vector. No partially executed program register vector replaces this
item prefix. Instruction errors carry the executor's actual PC; descriptor,
seed and cache errors use PC zero. Error stage identifies the first invalid
descriptor or the active stage; seed failure uses stage zero.

Retirement/multiplication counters are accumulated at each terminal executor
response, including a failing program's committed instruction prefix. Cache
failure includes all current-program retirements but no current-stage XOR.
`rsp_exec_cycles` likewise includes terminal executor error cycles. Seeding's
one multiply is excluded from native program multiplication counts.

Commit observations report each actual native instruction write independently
of the item prefix. Stage observations report each completed cache XOR,
including the final XOR on the same cycle as successful result availability.
They have no ready/backpressure input and are suppressed by reset/cancel.

`rsp_cycles` counts owned control clocks after descriptor acceptance through
result availability, including seed/execution/cache stalls, and excludes held
RETURN clocks. Invalid descriptors have zero latency. `rsp_exec_cycles` sums
only executor clocks; `stage_program_cycles` is the completed stage's executor
latency, including instruction-service waits. Counters and response data freeze
while the terminal response is held.

| Phase | Code |
|---|---:|
| IDLE | 0 |
| SEED_REQ | 1 |
| SEED_WAIT | 2 |
| EXEC_REQ | 3 |
| EXEC_WAIT | 4 |
| CACHE_REQ | 5 |
| CACHE_WAIT | 6 |
| XOR_STAGE | 7 |
| RETURN | 8 |

## Boundary and validation status

This component requires prepared programs, reciprocal values and actual cache
bytes. Program generation, Argon2/cache initialization, external memory service,
complete dataset allocation and complete hash integration remain external.
Source preparation alone establishes no simulation, synthesis, physical PPA or
whole-dataset result. Validation results must bind the exact executed source,
native input/export provenance, all intermediate states and retained receipts.
