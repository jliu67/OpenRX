# Corrected per-iteration execution-stage evidence

[Task #48](https://github.com/jliu67/OpenRX/issues/48) / [draft PR #49](https://github.com/jliu67/OpenRX/pull/49)
delivers the required v2 F/E AES mixer at each VM program iteration, before its F
scratchpad write. v1 performs corresponding-lane raw F XOR E at the same boundary.
Independent review rejected the initial identity expectation; [original exports](../aes-rtl-20261012/README.md)
and the initial source remain retained. This corrected record is one complete
successful oracle/RTL/synthesis/netlist harness run: attempt10.

[summary.json](summary.json) contains both configurations’ actual cycles and cell
counts. The mapped `randomx_exec_aes_commit` top includes the AES mixer, v1 XOR
path and writeback control: 40,848/84,999 generic cells and 1,545/1,543 flip-flops.
No-stall v2 request intervals are 17/5 cycles (3.4× transactions per clock).
Physical timing, area, power and whole-hash speedup are unmeasured.

| Evidence | Files |
|---|---|
| Exact executed source/tool bindings | [inputs.json](inputs.json), [tools.json](tools.json) |
| Full command sequence | [commands.json](commands.json) |
| Software vectors | [rounds.hex](rounds.hex), [v2 mixes](mixes.hex), [v1 XOR](v1.hex) |
| Integrated RTL results | [one lane](commit-1.log), [four lanes](commit-4.log) |
| Mapped-netlist results | [one lane](netlist-1.log), [four lanes](netlist-4.log) |
| Real generic synthesis statistics | [one lane](stat-1.txt), [four lanes](stat-4.txt) |
| Complete synthesis logs | [one lane](synth-1.log.gz), [four lanes](synth-4.log.gz) |
| Complete mapped Verilog | [one lane](netlist-1.v.gz), [four lanes](netlist-4.v.gz) |
| Complete mapped JSON | [one lane](netlist-1.json.gz), [four lanes](netlist-4.json.gz) |
| Exact limits, RSS, utilization and closure | [resources.json](resources.json) |
| Raw/public digests | [index.json](index.json), [all raw artifacts](artifacts.sha256.json) |

Gzip is lossless. The 19 input digests match the final feature files; all 256 v1
reference outputs independently match F XOR E, and the v2/round vectors are
byte-identical to the retained original run. Unsupported lane counts, outputs
inside source and reuse of an earlier output directory fail. The global slot is
free and job cgroup absent. Full local outputs are preserved; hosted CI regenerates
and retains fresh full outputs with [OpenRX](LICENSE-OpenRX),
[secworks](LICENSE-secworks) and [RandomX](LICENSE-RandomX) licenses.

Reproduce from the feature source with a fresh outside-source output directory:

```bash
python3 scripts/test_aes_rtl.py --output /tmp/openrx-aes-fresh-attempt --synthesize
```

Use adequate memory and the existing shared-host slot/admission rules; the
successful local run used 4 GiB and all six CPUs with one worker. Source/core/full
baseline and PPA acceptance remain distinct. Independent final-head review is
recorded separately on the task/PR; no protected push or merge is performed.
