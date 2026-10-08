# Canonical incremental resume, 2026-10-08

The bounded 20-minute incremental build completed the three remaining generated RISC-V translation units and `src/base/date.cc`, then failed during the final link. SCons returned 2 before the timeout expired. GNU ld was killed with signal 9; the cgroup recorded its first OOM kill. The linker anonymous-memory observation was 8,212,676,608 bytes (7.65 GiB) against an 8 GiB memory limit.

No successful gem5 executable or guest result came from this attempt. The 74,441,559-byte partial output was mode 0644 and is not a verified executable. Completed objects remain available for a separately authorized recovery.

The immutable source archive and all 10,933 archived regular files matched before and after. The canonical RISC-V config SHA-256 remained `e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5`. No source or Kconfig changes were made. `--without-tcmalloc`, six workers, and the retained dependency environment match the previous build windows.

`resume.log`, `resume-exit-code.txt`, and `resume-provenance.json` are the outcome records. Resource observations are sparse checkpoints, not a complete time series. The initial dry run is retained; it predicted four main compilations and one final link, while actual execution also relinked the Python helper and regenerated headers. The exact failure wall timestamp was not logged by SCons; 17:29:22 UTC is the first post-failure observation.
