# RandomX per-iteration scratchpad-store integration

`randomx_iteration_store` connects the reviewed [PR49 AES component](../aes/README.md)
to the pinned interpreter's actual iteration tail: eight post-dataset integer
stores to `spAddr1`, followed by four transformed F stores to `spAddr0`, then
iteration completion. It returns the final raw F state and zero address cursors.
It does not implement bytecode, dataset lookup, a selected CPU/cache/fabric, or a
physical SRAM macro. Those interfaces are not accepted project assets yet.

Both start addresses are 64-byte aligned in the pinned 2-MiB scratchpad. A
128-bit ordered SRAM write port groups each pair of little-endian integer 64-bit
stores into one beat; F lanes already use 128-bit stores. Four R beats must commit
before four F beats. When both lines coincide, F must overwrite R, exactly as in
the software. There is one outstanding iteration and no external observer or
fault/atomicity model between the grouped integer stores.

| Port | Contract |
|---|---|
| `req_valid/req_ready` | One rising-edge transfer supplies post-bytecode/post-dataset R/F/E and the two masked scratchpad addresses. Hold the bundle while stalled. |
| `req_v2` | v2 performs AES mixing; v1 performs raw F XOR E. |
| `req_r/req_f/req_e` | 512 bits each, low register/lane first, identical to the pinned software memory layout. |
| `req_f_line/req_r_line` | 15-bit line indices: respectively `spAddr0[20:6]` and `spAddr1[20:6]`. |
| `wr_valid/wr_ready` | Acceptance commits a 16-byte ordered scratchpad store on that edge. Ready must mean committed/in-order visibility, rather than merely queued for possible reordering. |
| `wr_addr/wr_data/wr_strb` | 21-bit byte address, 128-bit little-endian data, all 16 byte enables set; stable while stalled. |
| `done_valid/done_ready/done_f` | Completion only after all eight writes commit; final F stays stable while stalled. Next request may transfer on the completion-consumption edge. |
| `done_spaddr0/done_spaddr1` | Zero values at completion, matching the interpreter's cursor reset. |
| `rst` | Synchronous active-high reset aborts pending control/completion and suppresses handshakes. Already committed SRAM writes remain; reinitialize/restore an aborted context before reuse. |

`LANES=1/4` preserves the reviewed AES variants. `OVERLAP_R=1` lets R stores
progress while AES computes, using the independent captured R bundle; F stores
still wait for both AES and every R store. `OVERLAP_R=0` serializes the stores
behind AES availability as a controlled scheduling reference. Only 0/1 are valid.
No combinational ready loop may be introduced by the consuming core/memory system.

The differential fixture compiles the unchanged pinned `BytecodeMachine` and
executes the **verbatim extracted interpreter iteration body**. It uses full-size
controlled programs with eight instruction families and a deterministic virtual
dataset-line provider, not a full RandomX dataset or hash workload. The capture
point after dataset mixing supplies the hardware's raw operands and addresses;
the software continues through its actual R/F stores. Original licenses accompany
extracted code. The testbench applies writes to a full 2-MiB scratchpad, compares
per-iteration regions and all final bytes, and exercises equal addresses,
backpressure, retirement and partial resets. Prefix instructions perform no
scratchpad writes, so the hardware's covered effects are exactly the tail stores.

```bash
python3 scripts/test_iteration_tail.py --output /tmp/openrx-tail-fresh-attempt --synthesize
```

Use fresh outside-source outputs, the existing global slot and workload-based
resources on the shared host. The pinned AES/vendor identities are checked;
PR49's code and reviewed head remain unchanged. The delivered overlap tops are
synthesized and run the same differential memory tests; serial references are
tested in RTL. The test SRAM is a simulation memory, not synthesized physical
memory, and its area is excluded. See [EXP-004](../../experiments/EXP-004-iteration-tail.md)
for actual cycles/resources and remaining core/timing boundaries.
