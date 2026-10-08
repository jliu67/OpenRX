# Linux runtime controls and gem5 progress — 2026-10-08

**Actual gem5 Linux boot and all nine standalone runtime controls passed and
were independently accepted. Task #16 remains open for the complete unchanged
light-mode v2/v1 hash matrix, whose separate 1,200-second attempt timed out.**

Native Linux and scalar QEMU controls already pass. PR #18 at
`53933bac18e1c1ef0128ee8bd4f40c356dcf1165` also passed the foundation, RISC-V and
new offline acquisition checks. Its guest job was intentionally skipped:
actual hosted simulator acquisition/boot is manual.

A subsequent runner repair streams each flushed probe record through `tee`
while retaining its guest JSONL and exact child status. Capture failures and
incomplete frames still fail closed. This prevents a future timeout from
hiding all partial hash records behind the old post-exit `cat`. Generated-Bash
host controls pass, including early output, producer failure and capture
failure; [26 gem5 / 245 total tests](streaming-controls-20261008/controls.json)
are retained separately. The actual guest records below used the preserved
earlier runner; they do not claim this streaming revision ran inside gem5.

| Evidence stage | Current actual outcome | Durable record |
|---|---|---|
| Native/QEMU controls | Each passes 39 unchanged RandomX controls and nine Linux runtime controls; one optional AES skip per workload | [Prior executed runtime CI](RUNTIME-CI.md), [current PR CI ledger](acquisition-review-20261008/ci-review.json) |
| Guest input preparation | Exact firmware/kernel/disk bytes downloaded and pinned; all SHA-256/upstream MD5 checks passed | [Preparation](PREPARATION.md), [resource report](resource-preparation-20261008.json) |
| Guest ELF/library prerequisites | All 15 provider checks and 345 versioned symbols present in the inspected guest image | [ELF review](CROSS-ELF-REVIEW.md), [audit](guest-elf-audit-20261008.json) |
| Initial source builds | Original hosted/local windows timed out; historical outcomes preserved | [Hosted failure review](CI-BUILD.md), [original local build](build-20261008/README.md) |
| Incremental source completion | Remaining large translation units completed; ordinary final link was OOM-killed at the 8 GiB host limit | [Resume/OOM evidence](resume-20261008/README.md) |
| Supported link recovery | Exit 0 after 248.76 seconds; original canonical objects/source/config reused; real build-info and loader checks passed | [Link recovery](link-recovery-20261008/README.md), [binary identity](link-recovery-20261008/binary-identity.json) |
| Durable executable reuse | Original binary/source/notices/runtime package verified and saved in two ordered parts | [Reuse instructions](REUSE.md), [saved identities](reusable-package-20261008.json) |
| Acquisition implementation | Independent review accepted; 23 offline controls pass in actual PR CI | [Acquisition audit](ACQUISITION-20261008.md), [independent review](ACQUISITION-REVIEW-20261008.md), [CI ledger](acquisition-review-20261008/ci-review.json) |
| Local gem5 startup/configuration | Real executable imported the configuration; generated core/cache/RAM/DTB and encoded RV64 ELF checked | [Startup/payload review](actual-runtime-review-20261008/startup-config-payload.json) |
| Local gem5 Linux boot/runtime | Linux 6.8.12 booted; all nine fixed runtime oracles passed; child exit 0 and hypercalls 1/2/3 completed | [Actual execution](actual-runtime-20261008/README.md), [report](actual-runtime-20261008/report.json), [independent acceptance](ACTUAL-GEM5-REVIEW-20261008.md) |
| gem5 unchanged light hashes | Declared 1,200-second timeout; all nine runtime controls repeated, hash ELF verified/launched, no complete hash stream or hypercall 3 | [Raw timeout](actual-light-20261008/README.md), [independent review](ACTUAL-LIGHT-REVIEW-20261008.md) |
| Full dataset, intended timing core, RTL, calibration | Not established by this functional attempt | Independent acceptance gates remain open |

The successful executable is the unchanged, unstripped 957,300,488-byte
`build/RISCV/gem5.opt`, SHA-256
`3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`.
Actual `--build-info` returned gem5 25.1.0.1 and exit 0. All 10,933 archived
regular source files still match the pinned archive; the canonical generated
config retains SHA-256
`e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5`.

The recovery used the upstream `--limit-ld-memory-usage` option, which enables
GNU ld `--no-keep-memory`; no source, ISA or Kconfig change was made. It executed
no target C++ compilations and reported no new OOM kill. Sparse memory samples
do not establish an exact peak. The successful local build uses its recorded
Python/native-library environment and `--without-tcmalloc`; it is separate
from the new hosted Ubuntu builder recipe.

The [original execution-status snapshot](execution-status-20261008.json),
earlier logs and build reports remain historical records from before recovery.
Their “not linked/not run” state is superseded by the new build/progress
records above, without rewriting those earlier outcomes.

The runtime-only guest attempt completed in 958.25 host seconds within its
1,200-second bound. Independent replay accepted exactly one runtime frame,
nine fixed oracles, zero child status, empty framed stderr, completion and the
ordered hypercalls. The guest used the explicit Linux RISC-V flush-icache path;
generated returns were 7 → 19 → 7. Source/binary/configuration/payload and all
firmware/kernel/disk bindings were independently rechecked. These combined
permission/overwrite/flush controls do not isolate the flush mechanism or prove
SMP, migration or intended timing-core coherence.

## Acquisition and CI boundary

Pull requests now run fast vendor/offline controls. The new manual consumer
requires a successful same-repository manual simulator-build run ID and an
independently reviewed binary SHA-256. It validates source/configuration/build
records and bytes before execution, then runs actual guest tests without
rebuilding gem5. The separate manual fallback preserves matching partial SCons
work on timeout and records the supported low-memory linker recipe.

**The hosted manual builder, cache service operations and manual artifact
download/guest path have not run end to end.** Their acceptance here covers
reviewed code and executed offline controls. The locally completed executable,
durable package and completed local Linux runtime attempt are separate evidence, and are not
represented as an Actions-produced simulator artifact. Source assertions and
self-digests are consistency records, not source reproducibility proof.

The current [CI ledger](acquisition-review-20261008/ci-review.json) binds the
three run/job IDs, retained log hashes, tested merge commit and frozen code
digests. The foundation job passed 242 Python tests, 107 upstream controls and
six same-process native controls. RISC-V CI passed the 39+9 native/QEMU controls;
the gem5 job passed 23 offline controls and skipped actual guest execution by
its manual-dispatch guard. No QEMU result is promoted to gem5 or processor
evidence. These two current README status updates were made after that CI head.
The CI ledger's documentation digests remain historical; no functional
implementation changed in this documentation update.

## Next commands: reuse the executable

Follow [REUSE.md](REUSE.md) to retrieve the two saved parts, verify each part
and the reconstructed archive, and restore the original binary plus its
recorded runtime. That recipe initializes host Python before supplying the
bundled Python environment to the gem5 child. **A new source build is not
required.** Guest resources and payloads remain separately pinned inputs.

If the current temporary inputs still exist, run from the repository root with
the already reviewed original executable and a fresh output directory:

```bash
REVIEWED_GEM5_BINARY=/tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt
printf '%s  %s\n' 3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6 "$REVIEWED_GEM5_BINARY" | sha256sum -c -
LD_LIBRARY_PATH=/tmp/openrx-gem5-source/native-libs:/tmp/openrx-gem5-source/apt-root/usr/lib/x86_64-linux-gnu \
python3 simulator/gem5/run.py --gem5 "$REVIEWED_GEM5_BINARY" --resources /tmp/openrx-fs-resource-audit --runtime-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe --output-dir /tmp/openrx-gem5-runtime-next-attempt
```

The completed light timeout consumed most of its bound in boot/payload setup. Reuse the built simulator and reviewed streaming runner with the current no-wall-cutoff default, monitor actual progress, and declare the separate simulated tick budget. Positive `--timeout SECONDS` remains an opt-in; do not repeat the identical 20-minute attempt expecting a complete matrix. If
temporary inputs are absent, restore the saved simulator package and acquire
the pinned resources with `simulator/gem5/prepare.py`; retain each attempt in
a new output directory. Do not treat host loader or missing-input failures as
guest results.

The guest transfer verifies the decoded payload inside Linux and requires all
nine runtime controls, empty stderr, zero child status, completion marker and
the complete hypercall sequence 1/2/3. Hypercall 3 alone cannot pass because the
image emits it even after script failure. The runtime stage has passed. To
reproduce the separate unchanged light-mode attempt, add
`--hash-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe` and use a
new output directory. Preserve timeout and partial output honestly; that
matrix was not completed within the first bound. The old script withheld hash stdout until exit, so no partial hash records were exposed; this is not evidence of a semantic mismatch. The streaming repair addresses that observability gap for future attempts.

The actual startup review confirms one Atomic RISC-V core, RVV disabled,
4 GiB RAM and private L1/L2/walk caches. This is a functional candidate.
Full-dataset correctness, intended timing-core coherence, selected RTL boot
and M1/M4 calibration remain independent gates. No physical throughput, power,
hashes per joule or silicon advantage is established.

## Final streaming revision CI

All checks at `4f4cf17880ccfa2e904eb9d2dc23892b828bce12` passed: 245 Python, 107 upstream, six native steady and 26 gem5 offline controls; 39 RandomX and nine runtime controls in each native/QEMU environment. The [final CI ledger](streaming-ci-20261008/ci-review.json) binds all five successful push/PR runs, full decoded logs and final functional source digests. The guest CI job remains explicitly skipped. [Independent streaming acceptance](STREAMING-REVIEW-20261008.md) covers executed host Bash interruption/failure controls; actual gem5 runs retain the old runner snapshot.
