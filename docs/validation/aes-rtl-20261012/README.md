# AES execution-stage test and synthesis evidence

[Task #48](https://github.com/jliu67/OpenRX/issues/48) delivers the required v2
F/E mixer and its VM-completion/writeback adapter. The component's
[interface and reproduction command](../../../rtl/aes/README.md) and
[EXP-003](../../../experiments/EXP-003-v2-aes-rtl.md) describe the exact scope.
Independent implementation review is pending; this record does not accept a
whole processor, calibrated PPA, native baseline or competitive ASIC.

[summary.json](summary.json) records passing round, mixer, v1/v2 integration and
mapped-netlist tests. Shared-lane results are from attempt07. Its four-lane
synthesis was stopped by the 2-GiB cgroup limit during ABC mapping; the focused
attempt08 completed that phase and netlist tests under 4 GiB with unchanged
inputs/vectors. This combined result preserves the failed attempt instead of
describing it as a complete successful run.

| Evidence | Files |
|---|---|
| Exact input/software/IP identities | [inputs.json](inputs.json), [tools.json](tools.json), pinned manifests in the source tree |
| Deterministic vectors | [rounds.hex](rounds.hex), [mixes.hex](mixes.hex) |
| Original commands | [attempt07](commands-attempt-07.json), [focused attempt08](commands-attempt-08.json), [guard checks](commands-guards.json) |
| Integrated RTL pass logs | [one lane](commit-1.log), [four lanes](commit-4.log) |
| Actual mapped-netlist pass logs | [one lane](netlist-1.log), [four lanes](netlist-4.log) |
| Generic cell statistics | [one lane](stat-1.txt), [four lanes](stat-4.txt) |
| Full synthesis logs | [one lane](synth-1.log.gz), [four lanes](synth-4.log.gz) |
| Complete mapped Verilog | [one lane](netlist-1.v.gz), [four lanes](netlist-4.v.gz) |
| Complete mapped JSON | [one lane](netlist-1.json.gz), [four lanes](netlist-4.json.gz) |
| Resource budget, retry and closure | [resources.json](resources.json) |
| Raw/public digests and retained failures | [index.json](index.json) |

Gzip exports are lossless; `index.json` binds their compressed and original
digests. Original attempt directories, commands, tool outputs, executables and
failure snapshots remain retained locally. Generated artifacts carry the
[OpenRX](LICENSE-OpenRX), [secworks](LICENSE-secworks) and
[RandomX](LICENSE-RandomX) licenses. Hosted AES RTL CI recreates the full flow and
uploads full outputs with licenses; it records its own distribution tool versions.

Commands use repository-relative source paths and the actual temporary output
directories. For a fresh reproduction, substitute a new outside-source output
directory using the harness command. No original output is overwritten. Local
scientific source/builds/data/receipts, RandomX vendor bytes and existing scientific
CI guards are unchanged.
