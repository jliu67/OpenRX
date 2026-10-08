# Bounded local gem5 source build — 2026-10-08

**Outcome: incomplete, timeout 124.** The pinned source configured and made healthy compilation progress, but `build/RISCV/gem5.opt` did not link. No Linux boot, guest runtime control, RandomX hash, full-dataset or calibrated performance result was produced by this local build.

Source: gem5 `c8222cc67a399bfc01e8658dd14b30d5bfd634f9` (source version 25.1.0.1). The exact codeload archive digest is retained in `build-provenance.json`; `source-consistency.json` confirms all 10,933 archived regular files remain byte-for-byte unchanged.

| Attempt | Jobs | Result | Evidence |
|---|---:|---|---|
| Initial configuration | 2 | Failed, exit 1: runtime Python's unversioned library symlink is broken | build-attempt-1.log |
| Repaired library path | 2 | Failed, exit 1: versioned SONAME alias was missing | build-attempt-2.log |
| Working configuration/partial compile | 2 | Interrupted, exit 130, to increase workers with observed headroom | build-j2-interrupted.log |
| Canonical incremental window 1 | 6 | Timeout 124 after 1,200 seconds | build-j6-window-1.log |
| Canonical incremental window 2 | 6 | Timeout 124 after 1,200 seconds | build-j6-window-2.log |
| Canonical incremental window 3 | 6 | Timeout 124 after 1,200 seconds | build-j6-window-3.log |

All three windows used the same unchanged source, `build/RISCV` directory, canonical config and compiler command. The effective config retains Ruby MI_example, SystemC, KVM and the RISC-V ISA. The final path count is 2,266 `.o`/`.pyo` outputs; a path count is not evidence that objects are valid, linked, or executed. The final active actions were generated RISC-V execution/decoder/instruction compilation. Cgroup OOM/kill counters remained zero.

`commands.txt`, `host-config.json`, `canonical-config`, `source-build-opts-RISCV`, `scons-config.log`, full per-attempt build logs and dependency logs retain commands, versions, configuration and failures. Dependency debs were extracted into scratch after ordinary package installation failed; no successful system package installation occurred. Optional protobuf tracing, PNG, HDF5 and capstone support were unavailable.

The final incremental command can resume the retained local source build. A fresh environment must recreate the pinned dependencies and source. `minimal-future-build.txt` describes source-reviewed configuration reductions for a future build; they were **not applied** to this attempt. Changing Ruby/SystemC mid-build can invalidate most ordinary and helper compile signatures, so this session preserved the canonical configuration.

Next acceptance: a successful link, actual executable/version/config/digest verification, then the bounded full-system runner against pinned images and independently verified guest binaries. Keep #16/M3 open until actual boot and required correctness evidence pass.
