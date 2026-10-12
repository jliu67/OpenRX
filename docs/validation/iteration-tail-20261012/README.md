# Iteration-tail differential and synthesis evidence

[Task #50](https://github.com/jliu67/OpenRX/issues/50) extends immutable reviewed
PR49 with actual R/F scratchpad stores. See [interface](../../../rtl/iteration/README.md)
and [EXP-004](../../../experiments/EXP-004-iteration-tail.md) for boundaries and
observed cycles. New independent review remains pending.

The reference executes unchanged pinned interpreter iteration/bytecode code with
a controlled program and dataset-line fixture. The hardware covers only the
post-dataset tail; there is no accepted selected core/cache/fabric or SRAM macro.
An ordered in-memory write acceptance contract is supplied and tested. Counts
exclude the 2-MiB simulation memory and do not establish physical timing or PPA.

| Record | Artifact |
|---|---|
| Actual four-configuration results | [summary.json](summary.json) |
| Exact commands/tools/inputs | [commands.json](commands.json), [tools.json](tools.json), [inputs.json](inputs.json) |
| Verbatim upstream extraction and identities | [extraction.json](extraction.json), pinned_iteration.inc, pinned_dataset_read.inc, pinned_destructor.inc |
| Software reference | [oracle.log](oracle.log), iterations.hex.gz, initial.hex.gz, final.hex.gz |
| RTL pass logs | [1/serial](rtl-1-0.log), [1/overlap](rtl-1-1.log), [4/serial](rtl-4-0.log), [4/overlap](rtl-4-1.log) |
| Actual mapped pass logs | [one lane](netlist-1.log), [four lanes](netlist-4.log) |
| Actual generic statistics | [one lane](stat-1.txt), [four lanes](stat-4.txt) |
| Complete synthesis/netlist exports | synth-1.log.gz, synth-4.log.gz, netlist-1.v.gz, netlist-4.v.gz, netlist-1.json.gz, netlist-4.json.gz |
| Source/raw/public digests and resource closure | [index.json](index.json), [resources.json](resources.json) |

Gzip files are lossless; the index binds original and public digests. The full
successful attempt 03, binaries and prior development outputs remain retained.
Original BSD notices accompany extracted source; OpenRX, secworks and RandomX
licenses accompany redistributed outputs. All 19 PR49 core input bindings remain
exact, and its branch/head/evidence are unchanged. The global slot is released
and the job cgroup is absent. Source authoring is temporary and retired at handoff.

```bash
python3 scripts/test_iteration_tail.py --output /tmp/openrx-tail-fresh-attempt --synthesize
```

Use a full feature snapshot, a fresh outside-source output directory, adequate
memory and shared-host slot/admission rules. Selected-core, real SRAM/fabric,
full dataset/hash and physical measurements remain separate acceptance gates.
