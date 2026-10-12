# EXP-003: required v2 F/E AES execution stage

Status: implementation, reference tests and generic synthesis complete;
independent implementation review pending on [#48](https://github.com/jliu67/OpenRX/issues/48).

## Hypothesis

Four round lanes can preserve the exact required v2 register-mixing semantics
while reducing cycles compared with a shared round lane. This is a component
comparison. It does not assume AES is the full-hash bottleneck or establish a
physical clock frequency.

## Controls and configuration

The software oracle calls unchanged `soft_aesenc`/`soft_aesdec` from RandomX
v2.0.1 commit `aaafe71322df6602c21a5c72937ac284724ae561`. The mixing contract is
the same four ascending raw E keys applied to four raw F states, alternating
ENC/DEC lanes, from `vm_interpreted.cpp`. secworks S-box IP is pinned at
`80dc4718e1dcbbdb4b0dd1bdb393d8f7b98981dc`, with unchanged BSD-2-Clause notices.

Only `LANES=1` versus `LANES=4` changes. Both integrate at the same per-program-iteration completion
to F scratchpad-write boundary; v1 performs raw F XOR E. Identical deterministic
vectors use seed `0x4f70656e52587632`. There are no dataset, JIT, processor-model,
wall-power, PMU or native hash-rate measurements in this experiment.

Local tools are GCC 11.4.0, Icarus Verilog 11.0 and Yosys 0.9/ABC; full versions,
commands and 19 executed source/input digests are in the
[evidence](../docs/validation/aes-rtl-corrected-20261012/README.md). Code is based on main
`10482be038cffc95f09a14e309f40fd33e3f8619`. The initial draft’s v1 identity expectation was rejected by independent review.
The corrected per-iteration interface performs raw F XOR E for v1; complete
attempt10 regenerated both integrated configurations and netlists successfully.
The initial sources/attempts07/08 remain retained as superseded evidence.

## Acceptance and correctness

```bash
python3 scripts/test_aes_rtl.py --output /tmp/openrx-aes-fresh-attempt --synthesize
```

Use adequate RAM for the recorded tool version: four-lane Yosys/ABC exceeded
2 GiB; the successful local retry used a checked 4 GiB job budget. On the shared
OpenRX host, obtain the existing global payload slot and fresh resource admission.
Run this engineering test flow separately from native scientific measurements.

Required acceptance: 1,024 AES round vectors; both mixers' 256 full-mix vectors,
32 directed stalls and two reset aborts; integration's 256 all-v2 transactions
and 128-v2/128-v1 interleaving; same integration results/cycles from the actual
mapped netlists. Unsupported lane counts and outputs inside the source or an
existing attempt must fail. All these checks passed. Vendor/IP manifests passed;
no scientific workload or acceptance receipt was changed.

## Results

| Integrated configuration | v2 result availability | No-stall request interval | 256 v2 transactions, elapsed cycles | Generic cells | Flip-flop cells |
|---|---:|---:|---:|---:|---:|
| Shared lane | 16 cycles | 17 cycles | 4,352 | 40,848 | 1,545 |
| Four lanes | 4 cycles | 5 cycles | 1,280 | 84,999 | 1,543 |

The request interval includes response consumption and simultaneous next-request
acceptance. Counts include the v1 bypass and execution boundary. Cell counts come
from the actual flattened ABC-mapped netlist, and textual statistics agree.
The four-lane variant has 3.4× transactions per clock at 2.0809× generic cell
count. This is not a physical area ratio or hashes-per-second improvement.
Backpressured mixed-version tests complete in 2,513 versus 940 cycles with exact
v1 XOR and v2 oracle outputs.

The initial inverse-column coefficient ordering errors, the unsupported
Yosys-0.9 `stat -json` option, and the 2-GiB four-lane job OOM are preserved in
[failure exports](../docs/validation/aes-rtl-corrected-20261012/index.json). Statistics now
come from compatible text output and mapped JSON cell counts. The failing
memory budget and initial focused retry are retained. After the v1 correction,
the full flow succeeded in attempt10 under 4 GiB.
The corrected run kept all six CPUs available with one worker, 4 GiB RAM,
512 MiB swap and 128 tasks. Exact limits, utilization, RSS and cleanup are in
[resources.json](../docs/validation/aes-rtl-corrected-20261012/resources.json).

## Interpretation and next action

Both configurations are correct synthesizable execution components with an
explicit integration interface. No technology library, physical timing, chip
area, physical power, FPGA measurement or full-VM/hash speedup is established.
Generic Yosys flop libraries are not a calibrated ASIC library. Independent
review of this new exact implementation head is required before acceptance.
Broader #8/#16, selected-core, model and PPA gates remain open; no replacement
baseline batch or repeated source research is part of this delivery.
