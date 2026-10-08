# Executed gem5 light attempt — 2026-10-08

**The separate unchanged light-mode matrix attempt hit its declared
1,200-second simulator wall limit. Its overall result is fail/incomplete.**
Linux boot and all nine runtime controls passed again, but no complete hash
output or summary was captured. No RandomX hash/semantic pass or mismatch is
established by this attempt; task #16 remains open.

[report.json](report.json) is the unmodified actual wrapper report. The observed
wrapper exit was 1. It records `timed_out: true` and child `returncode: null`;
the original wrapper kills the child process group with SIGKILL on timeout and
does not preserve the numeric post-kill child status. Total wrapper elapsed was
1,261.236 seconds including pre/post streaming input checks; peak child RSS was
374,172 KiB. The declared simulator CPU/core/cache/RAM configuration remained
the accepted functional candidate, not a calibrated timing/RTL or power model.

## What actually completed

The original simulator SHA-256 remained
`3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`,
with pinned source/build provenance in the [link recovery record](../link-recovery-20261008/README.md).
Firmware/kernel/disk, actual config, readfile and both guest binaries matched
their bound identities before and after the run. The guest hash ELF was the
unchanged reviewed CI artifact, SHA-256
`61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`.
Its aggregate ELF attributes include optional V objects; the simulator's
emitted configuration disables RVV. No claim is made that all of that ELF's
optional instructions were exercised.

The actual serial log shows Linux mounted root, loaded the bridge and emitted
kernel boot hypercall 1 at tick 379,381,390,000, then after-boot hypercall 2 at
674,367,239,000. These match the accepted first runtime attempt. It emitted the
complete nine-control runtime summary with status 0 and empty framed stderr.
The wrapper independently revalidated those controls after checking inputs.
The guest then printed `hash: OK`, verifying the transferred hash ELF, followed
by `OPENRX_HASH_BEGIN`. The frame start was observed by 18:17:50 UTC, about
17.4 minutes after the simulator child started. There was no hash frame end,
hash summary, guest completion marker or final hypercall 3 before timeout.

The [phase snapshot](m5out/simulation.json) records the last completed hypercall
at tick 674,367,239,000. It is **not** a measurement of the final current tick
when the host killed the simulator. [Progress samples](progress.jsonl) preserve
polling timestamps, console progress and an active CPU through the bound.

## Observability and retained inputs

This attempt used the original wrapper, which redirected each probe's stdout
into a guest file and copied it to serial only after the probe exited. Thus
partial hash records may have existed inside the guest but were not captured;
the source and absent end frame do not identify which internal hash stage was
reached. The later streamed-output repair was developed while this old-code
attempt ran and was not executed in a new gem5 guest during this record.

[Original execution-source snapshots](execution-source/manifest.json) bind
`run.py`, `fs.py`, `prepare.py`, resources and both semantic validators before
that repair. The actual `guest.sh` remained immutable. The full small serial,
stdout/stderr, report, runtime JSONL, actual configuration, DTS, encoded DTB,
source snapshots and transfer script are retained with byte/SHA-256 bindings
in [artifact-manifest.json](artifact-manifest.json). OS images, simulator and
standalone guest ELFs are not copied here. The encoded DTB reconstructs exactly:

```bash
base64 --decode docs/validation/m3-fs/actual-light-20261008/m5out/device.dtb.base64 > /tmp/openrx-light-device.dtb
```

The source-mapped non-terminating SIGUSR1 stats diagnostic could not be
delivered from an independent exec PID namespace; the actual ESRCH/target
identity is retained in [diagnostics.jsonl](diagnostics.jsonl). No signal was
sent and no intermediate stats sample is claimed. Normal-completion stats were
not produced by the killed guest.

## Next gate

Reuse the verified simulator artifact rather than cold-building it for every
guest run. Run the reviewed streamed-output wrapper in a **new** evidence
directory with an explicitly recorded wall bound and the same pinned resources
and unchanged guest ELF. Streaming should expose flushed configuration,
semantic checks and cache-init stages while still requiring complete frames,
the existing 39 required semantic/hash controls, guest completion and the
accepted exit sequence for success. A complete eight-hash v2/v1
interpreter/JIT matrix, full-dataset validation and intended timing-core/RTL
correctness remain unaccepted by this timeout record. This record closes the
one authorized bounded light attempt.
