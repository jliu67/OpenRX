# RandomX v2 F/E execution stage

This hardware implements the post-VM register mixing required by the unchanged
[RandomX v2.0.1 interpreter](https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/src/vm_interpreted.cpp#L99).
It is a reusable execution stage for the larger RandomX architecture. The selected
processor/register file is still an open project gate; this change supplies its
VM-completion to F-writeback boundary and tests that boundary without inventing a
proprietary X9 interface. AES being required does not establish it as the hash-rate
bottleneck.

For each of the four raw E keys in ascending order, apply AESENC to F0/F2 and
AESDEC to F1/F3. Each round includes its column mixing and XORs its key at the end.
There is no key expansion, initial key XOR, reversed decrypt key order or
final-round exception. F/E are raw register bits; floating-point conversion would
change the workload.

`randomx_aes_round.v` uses the unchanged, BSD-2-Clause secworks S-box and inverse
S-box at commit `80dc4718e1dcbbdb4b0dd1bdb393d8f7b98981dc`; their license, notices,
upstream paths and SHA-256 pins are in [vendor/secworks](vendor/secworks/UPSTREAM.json).
The new round glue, control logic and tests are BSD-3-Clause under
[this component license](LICENSE).

## Integration contract

`randomx_exec_aes_commit` accepts one completed VM's raw F/E operand bundle and
version bit. Its output writes the four F registers. v2 goes through
`randomx_v2_aes_mix`; v1 forwards F unchanged because this post-VM stage is absent
from that version. E is read only and stays in the architectural register file.
The surrounding core must retire this writeback before consuming the resulting
F state for the existing scratchpad/hash path. This does not implement the VM's
instructions, floating-point arithmetic, scratchpad, hash, CPU or SoC.

| Port | Contract |
|---|---|
| `clk`, `rst` | One clock; synchronous active-high reset aborts pending work and clears valid state. |
| `vm_valid`, `vm_ready` | Transfer operands/version on a rising edge with both asserted. Producer holds operands while valid and stalled. |
| `vm_v2` | 1 selects v2 mixing; 0 selects v1 identity bypass. |
| `vm_f`, `vm_e` | 512 bits each: lane0 at `[127:0]`, lane1 at `[255:128]`, lane2 at `[383:256]`, lane3 at `[511:384]`. |
| `wb_valid`, `wb_ready`, `wb_f` | Writeback transfer on a rising edge with both asserted; output stays stable under backpressure. |

Within a lane, byte j is `[8*j +: 8]`; AES matrix element row r/column c is byte
`4*c+r`. Only one transaction is outstanding. There is no internal request queue
or tag; a consuming core can retain its existing context until writeback. A new
request can transfer on the same edge as the prior writeback. Ready depends on
downstream ready in that case; integration must avoid a combinational ready loop.
Reset suppresses both handshake directions while asserted. Outputs are meaningful
only while their valid signal is asserted.

`LANES=1` shares one round unit across four F lanes and supports both directions.
`LANES=4` supplies four round units with fixed alternating directions. Other values
are rejected during elaboration. Both use the same interface and oracle.

## Reproduce

Install official distribution packages for `g++`, Icarus Verilog and Yosys/ABC.
The recorded local tool versions and exact inputs are in the linked evidence.
Use a fresh output directory outside the source; earlier attempts are preserved.
Four-lane Yosys 0.9 exceeded a 2-GiB job budget; the successful local retry used
4 GiB. Shared-host execution requires its existing resource slot and admission.

```bash
python3 scripts/test_aes_rtl.py --output /tmp/openrx-aes-new-attempt --synthesize
```

The command verifies the complete RandomX vendor manifest and the reused IP,
compiles only the unchanged software AES source plus a small oracle, generates
deterministic vectors with seed `0x4f70656e52587632`, runs round/mixer/integration
tests, and synthesizes both integrated configurations with Yosys/ABC. The mapped
netlists run the same integration tests. No RandomX dataset or scientific native
benchmark runs. Hosted [AES RTL CI](../../.github/workflows/aes-rtl.yml) repeats this
flow and retains its raw artifacts; hosted distribution versions may differ and
are recorded on each run.

Tests cover every S-box input value at every byte position in both directions,
random raw keys/states, zero/ones/incrementing/IEEE bit-pattern bundles, full
ascending-key mixing, cycle counts, reset aborts, output stalls, simultaneous
writeback/re-request, mixed v1/v2 ordering, v1 identity and invalid parameters.

See [EXP-003](../../experiments/EXP-003-v2-aes-rtl.md) and the
[actual synthesis/test evidence](../../docs/validation/aes-rtl-20261012/README.md)
for measured component cycles and generic cell counts. Generic gate counts and
zero-delay simulation do not establish physical timing, silicon area, power,
FPGA frequency, whole-hash throughput, or an accepted full v2 baseline.
