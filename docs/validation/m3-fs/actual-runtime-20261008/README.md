# Executed gem5 Linux runtime controls — 2026-10-08

**The real pinned gem5 full-system run passed all nine scalar RISC-V Linux
runtime controls.** Child exit was 0, framed probe stderr was empty, the guest
completion marker was present, and the independent wrapper validated all
expected values and the complete kernel/after-boot hypercall sequence 1/2/3.
The [independent replay](../actual-runtime-review-20261008/replay-runtime.json)
also passed. This run did not request RandomX hashes or a full dataset.

The original source-built simulator was gem5 v25.1.0.1,
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9`, binary SHA-256
`3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`.
[Link/source identity evidence](../link-recovery-20261008/README.md) establishes
all 10,933 archived source files unchanged and canonical build configuration
`e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5`.
The guest runtime ELF was the already reviewed CI binary, SHA-256
`8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`.
Firmware/kernel/disk and simulator/configuration/payload/probe identities were
checked both before and after execution; [report.json](report.json) binds them.

| Actual runtime oracle | Actual / expected | Result |
|---|---|---|
| SIGILL recovery | 4 / 4 | pass |
| Executing RW memory denied | 11 / 11 | pass |
| Initial Linux RISC-V instruction-cache flush | 0 / 0 | pass |
| Generated code return | 7 / 7 | pass |
| Writing RX memory denied | 11 / 11 | pass |
| Flush after generated-code overwrite | 0 / 0 | pass |
| Overwritten code return | 19 / 19 | pass |
| Flush after restoring generated code | 0 / 0 | pass |
| Restored code return | 7 / 7 | pass |

The selected model was one Atomic RV64 core, RVV disabled, 4 GiB RAM,
16 KiB private L1 instruction/data caches, 256 KiB L2 and walk caches. This is
functional evidence on the selected configuration. It does not calibrate a
timing core, validate BOOM/RTL or real-silicon cache behavior, establish
throughput, or measure hardware power.

## Bound and observed progress

The simulator's wall limit was 1,200 seconds. The wrapper completed in
958.249 seconds including streaming input checks before/after the child;
gem5's [actual stats](m5out/stats.txt) record 917.34 host seconds. Peak child
RSS reported by the wrapper was 357,088 KiB. These are host resource costs,
not hardware performance claims.

The first several minutes were silent after OpenSBI's S-mode kernel handoff.
By 17:48:43 UTC Linux console output reached driver/network initialization;
by 17:49:42 it mounted the ext4 root and launched the inspected init script.
Hypercall 1 was observed by 17:50:30 at tick 379,381,390,000. User bash startup
then remained quiet while running its ordinary profile/completion setup;
hypercall 2 was observed by 17:56:45 at tick 674,367,239,000. Readfile succeeded
and the actual payload executed. Final hypercall 3 occurred at tick
749,723,178,000. [Progress samples](progress.jsonl) are polling observations,
not exact timestamps of first console writes. No duplicate guest was launched.

The source audit found SIGUSR1 schedules a non-terminating stats dump, but no
signal was actually sent: the independent command could not inspect the
process executable through procfs, and the target had already exited by its
subsequent command identity check. The final stats file was emitted by normal
simulator completion. No intermediate stats sample is claimed.

## Retained evidence

[command.txt](command.txt) records the exact launch and native-library path.
[runtime.jsonl](runtime.jsonl) preserves the probe's raw JSONL and
[runtime-stderr.log](runtime-stderr.log) its empty stderr. Full serial output,
stdout/stderr, simulation phases, actual config, generated DTS and base64-encoded
DTB, and stats
are retained under this directory. The [artifact manifest](artifact-manifest.json)
records byte counts and SHA-256 identities. `guest.sh` is the actual small
readfile transfer payload, including the encoded probe and its guest-side
digest check; OS images and the large simulator executable are not copied here.

The original 2,206-byte binary DTB remains in the execution output directory;
its exact bytes are recoverable from the committed text representation:

```bash
base64 --decode docs/validation/m3-fs/actual-runtime-20261008/m5out/device.dtb.base64 > /tmp/openrx-runtime-device.dtb
```

The manifest separately binds both encoded text and decoded DTB SHA-256.

[Execution-source snapshots](execution-source/manifest.json) bind the exact
original wrapper/configuration/preparation/validators used for this run. Its
guest script printed probe stdout after completion. The later streamed-output
repair is a separate offline-verified change; these logs do not claim that
repair executed in gem5.

The unchanged light-mode v2/v1 interpreter/JIT matrix is a separate next gate,
with a separate declared bound and evidence directory. Task #16 remains open
until that execution is accepted; full-dataset and intended timing-core/RTL
requirements remain separate.
