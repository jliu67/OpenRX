# Independent bounded gem5 light-attempt review — 2026-10-08

**Accept the retained partial execution record. Do not accept the complete
RandomX light matrix; task #16 remains open.** The reviewer launched no guest
and changed no workload, simulator or resource.

The separate actual attempt booted Linux and completed all nine standalone
runtime controls again. Its declared 1,200-second child bound expired after the
hash-stage start marker. The host wrapper exited 1; its report records timeout,
a null normal child return code and only exit hypercalls 1/2. No hash JSON body,
end/status, summary, guest-completion marker or hypercall 3 is retained.

An independent line-based replay accepted the nine exact runtime oracles, status
zero and empty framed runtime stderr. It rejected the complete light gate and
matched the wrapper's reported failure. **Zero hash records are exposed.** The
original script captured stdout in a guest file and displayed it after process
exit; the timeout prevents counting internal progress. This record establishes
neither a semantic/hash pass nor a hash mismatch.

## Exact bindings

- Same linked gem5 ELF: SHA-256
  `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`.
  The earlier independent full source-archive/binary review remains applicable;
  this replay independently rehashed the actual executable after the light run.
- The executing runner is preserved as SHA-256
  `7ae0fd2c8c3364cd8f3fc8ff2c082c810e112cd9c71395ab04b89c4915dfcd0a`.
  All six original source/validator snapshots match their manifest. The current
  streaming revision differs and was not executed by this attempt.
- Readfile SHA-256:
  `403fa537df55303f74793a5c9e27c735d812eb128f70e2d97c4d46441fa9fae2`.
  Both decoded payloads equal the real RV64 ELFs and report hashes. The light
  payload is 376,824 bytes, SHA-256
  `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`;
  it matches both retained CI archives and the successful scalar QEMU report.
- The actual emitted configuration again has one Atomic core/thread, RVV off,
  4 GiB mapped RAM, 16 KiB L1I/D, 256 KiB L2 and 8 KiB walker caches, with the
  pinned root/init arguments. The full firmware/kernel/5 GiB disk were rehashed
  independently after execution; byte counts, SHA-256 and upstream MD5 all match.
- Complete partial serial SHA-256:
  `85266d1d25617c6fea1f3df8326e795549cbf8c116b89c480c8d6751dbcbbae8`.

The light ELF has merged attributes from optional unchanged vector library
objects. Its main compile uses GCC 14.2.0, RV64GC/lp64d and precise FP flags;
the passing QEMU run disabled V. This is scalar executed-path evidence, not a
claim that every instruction in the ELF is RV64GC. All 167 locally present
vendor files match the 171-file manifest; four audit PDFs are absent locally,
and retained CI logs record all 171 integrity checks. The historical CI checkout
Git object is unavailable locally, so no fresh source-reproducible build is claimed.

Reviewer commands, full output/errors, input provenance, strict replay helper
and results are under
[`actual-light-review-20261008/`](actual-light-review-20261008/), including
[`replay-light.json`](actual-light-review-20261008/replay-light.json) and
[`light-payload-binding.json`](actual-light-review-20261008/light-payload-binding.json).
The replay's `status: pass` means the review agrees with the failure record;
its `full_light_gate_accepted: false` is the workload acceptance result.
The original actual attempt is retained separately under
[`actual-light-20261008/`](actual-light-20261008/), including the
[failed report](actual-light-20261008/report.json) and
[complete partial serial](actual-light-20261008/m5out/board.platform.terminal).
The reviewer checked all 27 retained manifest entries and the decoded DTB.
Raw outputs and executing sources match the original attempt byte for byte;
publication README/command/base64/wrapper-status records match their manifest
hashes. [The copy audit](actual-light-review-20261008/retained-copy.json) records
the exact comparisons. Frozen manifest SHA-256 is
`fb95f5c0cbfad9fecb3c3cdd1f8d239e90df0f1031b6566968b69a74edb386b5`.

## Next acceptance

Use the independently reviewed stdout-streaming runner for a separately bounded
attempt with the same unchanged light constants and input identities. Acceptance
still requires all 39 required semantic/hash controls, eight v2/v1
interpreter/JIT software-AES hash cases, zero child exit, empty framed stderr,
complete guest marker and hypercalls 1/2/3. A visible start or partial matrix is
insufficient. The already accepted complete Linux runtime stage remains valid.

This outcome is functional evidence only. It does not calibrate timing or power,
prove full-dataset execution, or satisfy selected-core/RTL and M1/M4/M5 gates.
The new hosted manual cache/build/artifact-reuse paths remain unexecuted here.
