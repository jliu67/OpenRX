# Independent gem5 full-system scaffolding review — 2026-10-08

Reviewer: session subagent `/root/gem5_review`, independent of the implementation
author. Task: [#16](https://github.com/jliu67/OpenRandomX/issues/16). Scope:
`simulator/gem5/`, `tests/test_gem5_fs.py` and `.github/workflows/gem5-fs.yml`.

**Result: acceptable as pinned, bounded full-system preparation and execution
scaffolding after the corrections below. Actual gem5 Linux boot and RandomX
execution are not accepted by this review.** No full-system run was performed
by this reviewer. Image inspection, source review and wrapper controls do not
establish executed simulator compatibility, M3 completion or M4 calibration.

## Corrections requested and verified

1. The initial configuration used `NoCache`. Its pinned implementation warns
   that full-system use is unsupported and records an x86 snoop-filter panic.
   That warning does not prove this RISC-V configuration fails, but is a poor
   basis for an unexecuted boot path. The author adopted the exact upstream
   RISC-V example's `PrivateL1PrivateL2WalkCacheHierarchy` and geometry:
   16-KiB L1I/L1D and 256-KiB L2. The one-core AtomicSimpleCPU, RVV-off and
   4-GiB functional choices remain explicit. This is still an uncalibrated
   configuration; it is not BOOM/C920 RTL or a timing-core acceptance result.
2. The runner now rechecks the resource manifest, host readfile, configuration,
   firmware/kernel/disk, guest payloads and simulator binary before validating
   even a partially completed control stream. A timeout cannot bypass input
   identity checks. The retained serial log remains available on failure.
3. Progress snapshots now record hypercalls 1/2/3 through an atomic rename,
   preserving an observed completed phase if a later workload is killed.
   The pinned gem5 entry point initializes the event queue and output directory
   before loading the configuration, so the initial `m5.curTick()` snapshot
   does not require an already instantiated board.
4. Documentation explicitly separates observed binary identity from source
   build provenance, records empty resource-catalog license strings, and keeps
   full-dataset, intended-core coherence and calibration gates open.

## Pinned source/API audit

Reviewed local primary source archive for gem5
`c8222cc67a399bfc01e8658dd14b30d5bfd634f9` (v25.1.0.1), at
`/tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9`.
The separate build provenance records the archive identity and source-file
comparison; this review does not infer a source revision from an executable.
Exact primary-source links are in the [implementation README](../../../simulator/gem5/README.md).

- `RiscvBoard._setup_memory_ranges` applies the memory object's size starting
  at `0x80000000`; 4 GiB therefore occupies `[0x80000000, 0x180000000)`.
  The generated DTB uses two address and size cells and the same memory ranges.
  This is configuration-source proof, not proof that Linux saw all the RAM.
- Setting `core.core.isa[0].enable_rvv = False` removes V from the generated
  ISA string. Other implemented scalar extensions remain enabled: RV64GC
  compilation does not imply the simulator implements only RV64GC.
- The kernel/disk API supports the local resource types, `root_partition="1"`,
  explicit `init=/sbin/gem5_init.sh`, `no_systemd` and host `readfile`.
  RiscvBoard uses a copy-on-write wrapper around a read-only base disk.
- `ExitHandler` metaclass registration and `Simulator.run` support the three
  custom handlers. Returning false for 1/2 continues execution; true for 3
  stops it. The tick limit is per `m5.simulate` call and resets at an earlier
  exit event, as declared in the report; the independent host wall limit
  bounds the whole subprocess.

## Actual image identity and read-only inspection

Independently reread all downloaded resource bytes through `prepare.verify`.
The byte counts, upstream MD5 and pinned SHA-256 matched the manifest:

| Resource | Bytes | SHA-256 |
|---|---:|---|
| OpenSBI | 1,292,496 | `510f5b9cbc6d2c8c97dacc395b29d47e897c1abe91e4df5a7d8893c0fad8ae0a` |
| Linux kernel | 19,749,472 | `57e9a7ab9553fb6c58078913b12687455bc46c072539266b14cbb0142b7bffdd` |
| Ubuntu compressed disk | 1,517,651,202 | `217f9a700742f136255bb715066f3665c523187350583bbd1c7b95b5a7322d27` |
| Ubuntu expanded disk | 5,242,880,000 | `ddf1ebb56454ef37e88d6de8aefdef7180fc9a2328a3bf8cff02f7a043e7127b` |

Parsed the actual GPT: partition 1 starts at sector 235520 (115 MiB), ending
at sector 10239966. Extracted that partition into a disposable sparse scratch
file and inspected it with `debugfs 1.47.0`, without mounting, modifying or
executing guest contents. Relevant commands:

```bash
dd if=/tmp/openrx-fs-resource-audit/ubuntu.img \
  of=/tmp/openrx-review-root.img bs=1M skip=115 conv=sparse status=none
debugfs -R 'cat /sbin/gem5_init.sh' /tmp/openrx-review-root.img
debugfs -R 'stat /sbin/init' /tmp/openrx-review-root.img
debugfs -R 'cat /home/gem5/after_boot.sh' /tmp/openrx-review-root.img
debugfs -R 'cat /home/gem5/.bashrc' /tmp/openrx-review-root.img
debugfs -R 'ls -l /usr/lib/modules/6.8.12' /tmp/openrx-review-root.img
debugfs -R 'cat /usr/lib/os-release' /tmp/openrx-review-root.img
```

Confirmed `/sbin/init` links to `/sbin/gem5_init.sh`; the init mounts proc/sys,
loads the guest bridge, emits hypercall 1 and enters the gem5 user's shell.
Its bashrc invokes `/home/gem5/after_boot.sh`, which emits 2, reads the host
script, executes it and emits 3. **The script emits 3 even if its child fails.**
The runner correctly requires independently validated output and child status
in addition to that event sequence. The actual image contains the bridge
executable, Linux 6.8.12 module directory, base64/sha256sum and Ubuntu 24.04
OS metadata. These are static image facts; runtime `uname` and successful
bridge calls still need execution evidence.

| Inspected guest file | SHA-256 |
|---|---|
| `/sbin/gem5_init.sh` | `f281f7ae77b8c362cb3422f9aa8e57ec28c7739503f089219bb0db40a589f916` |
| `/home/gem5/after_boot.sh` | `05c5b7824942fa0ada6eacd271e9c205c87e63fe81654778aa2167bebcd22965` |

## Independently executed wrapper controls

`python3 -m unittest discover -s tests -p test_gem5_fs.py -v` passed all
**seven tests**. Python AST parsing, manifest JSON parsing and workflow YAML
parsing passed. Workflow source checkout verifies the expected commit and
clean tracked source, bounds the build and run, and uploads failures with
`if: always()`. Source build metadata and observed dependency versions remain
necessary alongside simulator reports; distro packages are not frozen pins.
The final trigger-only revision retains filtered `pull_request` and explicit
`workflow_dispatch` execution and removes `push`, avoiding duplicate heavy
builds for a PR update. It changes no build, resource or execution logic.

Separately executed the generated base64 transfer script locally using the
independently built **x86-64 native runtime payload**. Guest-script SHA-256
verification, execution, stdout/stderr framing and completion marker worked;
the extracted native stream passed all nine runtime oracles. This validates
the shell transfer mechanism on the host; it is not RV64 or guest Linux proof.

Ten independent **synthetic wrapper fault-injection cases** also behaved as
expected: one deliberately synthetic complete control passed; guest nonzero
status, guest stderr, truncation, missing completion, incomplete events,
simulator nonzero status, wall timeout, missing later hash output and readfile
mutation during timeout all failed. The test stub supplied a known RV64 JSONL
fixture and mocked resource verification; it did not execute Linux or RV64.
The unchanged-input timeout and missing-hash cases retained the completed
runtime validation while leaving the overall report failed. The mutated-input
timeout correctly refused even partial runtime validation. Complete unit-test
logs, a reproducible synthetic fault helper, its fixture/commands/results/raw
logs, native transfer output and compact input/source audits are retained in
[`review-controls-20261008/`](review-controls-20261008/README.md). They retain
explicit host/synthetic/non-boot classifications; generated binaries, images,
base64 transfer scripts and caches are excluded.

## Reviewed file identities and remaining acceptance

| File | SHA-256 |
|---|---|
| `simulator/gem5/fs.py` | `5608189a6f2a41a45e86f117f10af8408ab87ea1aab600294a336ab31375e7c5` |
| `simulator/gem5/prepare.py` | `dc1fa2b1714a40ea7f5805963c689e64cd44149a3314cac312b45ed9bdf23763` |
| `simulator/gem5/run.py` | `7ae0fd2c8c3364cd8f3fc8ff2c082c810e112cd9c71395ab04b89c4915dfcd0a` |
| `simulator/gem5/resources.json` | `67c3838d04b617b3a4f34a874f84cc2c5517eca51c9049456bc6df19312404bb` |
| `tests/test_gem5_fs.py` | `97a4d4fb8da0fbc3bbc142adc8e29e2179ee04e1c6af6f9a23417f8aad69feed` |
| `.github/workflows/gem5-fs.yml` | `47af80591102076d556b2a2d860965bc3670b5942a720c7e814571e2207d21ed` |

No implementation blocker remains in this reviewed scaffolding scope. Task
#16 still needs an actual pinned gem5 build and Linux boot, retained device
tree/configuration/serial/runtime controls, complete unchanged light-mode
v2/v1 interpreter/JIT hashes and its full acceptance evidence. Full-dataset
execution, intended timing-core/cache behavior, multithreading and calibrated
performance remain separate gates. Neither atomic simulated timing nor host
elapsed time/RSS establishes physical throughput, power or hashes per joule.

## Future supported classic-only build alternative

Read-only audit of the same pin found a supported way to omit unused Ruby,
SystemC and KVM components. It does **not** produce an Atomic-only binary:
`src/cpu/{simple,o3,minor}/SConscript` gates all these models only on
`BUILD_ISA`, and `RiscvCPU.py` and the stdlib processor import their base
classes. No CPU whitelist Kconfig or `CPU_MODELS` setting exists in this pin.
Removing those source registrations would be a separate source modification.

For a fresh, separate build directory, from the exact source checkout and
its recorded build environment:

```bash
scons defconfig build/RISCV_CLASSIC build_opts/RISCV
scons setconfig build/RISCV_CLASSIC RUBY=n USE_SYSTEMC=n USE_KVM=n
timeout --signal=TERM --kill-after=30s 45m \
  scons build/RISCV_CLASSIC/gem5.opt -j2
```

Changing an existing directory is also a supported incremental operation,
**only after its active build and all compiler descendants have stopped**:

```bash
scons setconfig build/RISCV RUBY=n USE_SYSTEMC=n USE_KVM=n
timeout --signal=TERM --kill-after=30s 45m scons build/RISCV/gem5.opt -j2
```

Preserve the exact before/after generated config, source integrity comparison,
commands/environment, build logs and resulting binary digest. Do not rerun
`defconfig` on an existing directory if the intention is to preserve its
other configured options. `SConstruct` uses an existing config rather than
reapplying `build_opts/RISCV`; `setconfig` validates values through Kconfiglib.
The ConfigFile builder models each generated header's value as a SCons Value
dependency, and the linker takes the newly registered source list. Stale
disabled-module objects left on disk are not automatically linked.

The reviewer additionally loaded the pinned Kconfiglib in memory, using the
current recorded feature environment and generated config, and applied these
three assignments **without writing source or build configuration files**.
All three took value `n`; `BUILD_ISA=y`, `USE_RISCV_ISA=y`, `BUILD_GPU=n` and
`USE_TEST_OBJECTS=n` remained. The local result is
[`kconfig-source-audit.json`](review-controls-20261008/kconfig-source-audit.json).

The RISC-V ISA/FP implementation, Atomic CPU, classic cache/memory system,
boot workload, DTB builder, HiFive/CLINT/PLIC/RTC/UART, virtio block/RNG, PCI
host and Ethernet objects used by `RiscvBoard` remain outside those disabled
gates. `BaseCPUCore.is_kvm_core` explicitly tolerates the missing KVM class.
Lost capabilities are Ruby protocols/networks, SystemC/TLM integration and
KVM acceleration; none is requested by the reviewed full-system configuration.
Actual compilation and guest boot are still required to validate a resulting
reduced binary.

Static AST counting found 71 literal `Source` declarations under
`src/mem/ruby`, 90 under `src/systemc` and five under `src/cpu/kvm`, plus
generated protocols, parameters, embedded Python and debug code. These are
source-scope counts, not an exact object reduction: conditional declarations
and generated outputs differ by build configuration. O3, Minor, timing-simple
and the full RISC-V decoder still compile.

**Do not assume a mid-build switch saves this session's remaining time.**
Ruby's common SConscript globally adds `NUMBER_BITS_PER_SET` to CPPDEFINES;
SystemC globally adds include paths, which also propagate to `gem5py_env`.
Disabling them changes compile signatures and can invalidate already built
ordinary and embedded-Python objects. SCons handles this for correctness,
but reuse is not assured. The session therefore continued its canonical
incremental build unchanged until the retained time-limit failure; this
reduced recipe remains an unexecuted future alternative.
No build-time or simulation-performance advantage was measured or inferred.
