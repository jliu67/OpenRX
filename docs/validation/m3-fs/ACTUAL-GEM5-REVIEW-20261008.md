# Independent actual gem5 Linux runtime review — 2026-10-08

**Accept PR #18's implementation and the executed local Linux runtime stage for
merge. Keep task #16 open for the complete unchanged v2/v1 light hash matrix.**
Reviewer `/root/gem5_review` independently checked the actual source, executable,
emitted configuration, payload, resources and completed serial/report stream.
No simulator or second guest was launched by the reviewer.

## Executed acceptance

The sole runtime-only attempt used pinned gem5
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9` with one active Atomic core, RVV off,
4 GiB mapped RAM, 16 KiB instruction/data L1, 256 KiB L2 and 8 KiB walker caches.
The actual config and DTB match that declaration. RAM is mapped at
`[0x80000000, 0x180000000)`; the guest booted Linux 6.8.12 with the specified
root partition, init script and `no_systemd` arguments.

All nine exact standalone runtime controls passed: SIGILL recovery, denied RW
execution/RX writes, generated returns 7 → 19 → 7, permission transitions and
three successful flush calls. The payload identifies the explicit RISC-V Linux
flush-icache syscall path. Serial has exactly one complete runtime frame, status
zero, empty framed stderr and the completion marker. The actual child exited
zero, and all three exit hypercalls arrived in order:

| Phase | Hypercall | Tick |
|---|---:|---:|
| Kernel/init booted | 1 | 379381390000 |
| After-boot script started | 2 | 674367239000 |
| After-boot script finished | 3 | 749723178000 |

Ticks describe this functional simulation. They are not calibrated timing,
throughput, physical power or efficiency results.

## Independent bindings and replay

- The linked ELF is 957,300,488 bytes, SHA-256
  `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`.
  Actual build-info reports version 25.1.0.1 and passes the frozen bundle parser;
  the actual prefixless canonical Kconfig also passes.
- All 10,933 regular source archive members match independently, with no
  changed/missing files. The archive SHA matches its retained source pin.
  This is byte consistency, not source reproducibility or independent attestation.
- Decoding the actual host readfile produces the exact RV64 guest ELF, SHA-256
  `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`.
  It is the same digest-checked payload that previously passed scalar QEMU CI.
- The reviewer independently rehashed firmware, kernel and the complete 5 GiB
  disk after execution. Byte counts, upstream MD5, SHA-256 and retained runner
  observations all match. Config, manifest, readfile and payload identities match.
- Raw serial SHA-256 is
  `92a28e6b6700fae6638ab771c687a3a988c0464fe8cfa002d930d11fdb1dc37b`.
  An independent line-based replay checked exact frames, all nine fixed oracles,
  the extracted JSONL, empty errors, completion, child status and exit sequence.

Full reviewer commands, results and reproducible helpers are retained under
[`actual-runtime-review-20261008/`](actual-runtime-review-20261008/):
[`source-binary-binding.json`](actual-runtime-review-20261008/source-binary-binding.json),
[`startup-config-payload.json`](actual-runtime-review-20261008/startup-config-payload.json)
and [`replay-runtime.json`](actual-runtime-review-20261008/replay-runtime.json).
The replay helper only reads evidence and hashes inputs; it never executes an ELF.
Original attempt stdout/stderr, serial, report, configuration, encoded DTB and
progress are retained in
[`actual-runtime-20261008/`](actual-runtime-20261008/), including the
[`report`](actual-runtime-20261008/report.json),
[`complete serial`](actual-runtime-20261008/m5out/board.platform.terminal) and
[`emitted configuration`](actual-runtime-20261008/m5out/config.json).
The reviewer checked all 24 retained manifest entries and the decoded DTB.
Raw outputs and source snapshots match the original attempt byte for byte;
the source-manifest publication timestamp differs, with all other fields equal.
Publication README/command/base64 wrappers match their manifest hashes.
[The copy check](actual-runtime-review-20261008/retained-copy.json) records these
exact hashes and comparisons.
The original runner was SHA-256
`7ae0fd2c8c3364cd8f3fc8ff2c082c810e112cd9c71395ab04b89c4915dfcd0a`;
the [retained executing sources](actual-runtime-20261008/execution-source/manifest.json)
preserve those bytes before the subsequent stdout-streaming change. The
[preservation check](actual-runtime-review-20261008/source-preservation.json)
matches the runner/config/resource files against the earlier startup capture.
This guest result does not execute the later streaming revision.

## Boundaries

The declared host bound was 1,200 seconds. Early silent kernel startup and later
shell setup were followed by genuine progress and complete controls within that
bound. The original inputs were kept. Static inspection of guest startup entry
scripts found no explicit sleep, prompt or network prerequisite; this did not
measure the cost of sourced shell completion. Full inspection commands/errors
are retained in the reviewer package.

The nonfatal Python `exec_prefix` warning remains in host logs; configuration
import and actual execution succeeded. DRAM device capacity warnings remain:
the model geometry declares more capacity than its assigned channel ranges.
The actual mapped guest RAM is 4 GiB. No calibrated memory-system claim follows.

These controls establish combined signal/protection/overwrite/flush behavior in
this declared one-core Atomic configuration. Permission transitions can also
synchronize instructions; they do not isolate the flush mechanism or prove SMP,
migration or intended timing-core coherence. Unchanged RandomX hashes, full
dataset, selected-core/RTL boot and M1/M4/M5 gates remain separate.

The new acquisition workflows are independently accepted scaffolding. Their
manual hosted cache/build/artifact-reuse and guest paths were not executed by
this local attempt. Existing CI results remain offline/native/QEMU controls;
they must not be relabeled as this local gem5 guest execution.
