# Supported low-memory link recovery, 2026-10-08

The one authorized 600-second incremental retry succeeded with SCons exit 0 at 17:40:32 UTC after 248.76 seconds. It reused all three large generated RISC-V objects and executed no target C++ compilations. It relinked the two Python helpers and `gem5.opt` using upstream `--limit-ld-memory-usage`, which adds GNU ld `--no-keep-memory`. No source or Kconfig changes were made.

The prior canonical linker OOM is preserved separately in `../resume-20261008/`. This retry had no additional OOM kills. Thirty-second samples observed anonymous memory up to approximately 4.86 GiB; they do not establish an exact peak. `actual-linker-argv-42107.json` records the full real linker command.

The original unstripped executable is 957,300,488 bytes with mode 0755 and SHA-256 `3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6`. Actual `--build-info` returned 0 and reported gem5 25.1.0.1. `ldd` resolved all required libraries with the recorded native-library environment. No stripped copy was measured or substituted.

All 10,933 archived regular source files match the immutable source archive before and after the build. The canonical RISC-V config SHA-256 remains `e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5`. `binary-identity.json` binds the source/config verification, binary digest, actual version command and loader checks.

The initial forced-cache dry run exited 2 only because the new linker feature probe had no cached result. An existing config-file target then populated tiny Configure tests without building simulator targets; the second forced-cache dry run exited 0 and scheduled only three links and version tags. All probe, retry and verification commands and raw logs are retained.

These files establish a successful local simulator build and executable preflight. Guest execution is recorded independently; no guest boot result is implied by build success. The large upstream binary and reusable package are intentionally outside the project Git working tree.

A standalone reusable package is retained outside Git at `/tmp/openrx-gem5-reuse/gem5-c8222cc-linux-x86_64-20261008.tar.gz`. It contains the unchanged original binary, immutable upstream source archive/full per-file licenses, complete build records and a minimal Python 3.12.14 shared library/standard library excluding site-packages. The relative-path wrapper passed `--build-info` and loader checks with an otherwise clean environment. Package size is 936,569,944 bytes; SHA-256 is `b9536aa9dbce308edcdb735c518395ebf2e02d20ecdf53b181deeded19d07769`. Package portability beyond this host was not tested. `package-archive.json`, `package-provenance.json`, clean-environment logs and archive verification bind the reuse record.
