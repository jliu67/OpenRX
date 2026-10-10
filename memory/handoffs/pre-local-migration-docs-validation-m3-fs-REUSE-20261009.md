# Reuse the completed gem5 build

The exact local build succeeded on 2026-10-08. Reuse it before considering another source build. This is a locally built upstream executable, separate from the unexecuted manual GitHub build/artifact path.

The saved package is split into two ordered files because the artifact service accepts at most 512 MiB per file:

- `gem5-c8222cc-linux-x86_64-20261008.tar.gz.part01` — 503,316,480 bytes, SHA-256 `21b2411d3d03eeb7549f90e289d8ac4d70bc8b3c62ff395601bd14c1e5159a9f`.
- `gem5-c8222cc-linux-x86_64-20261008.tar.gz.part02` — 433,253,464 bytes, SHA-256 `39ef869beba8dba1a1eb26a399c69c838beacae6937fa449f093a2cdeaa78683`.

Both parts and `gem5-reuse-download-manifest.json` were successfully saved. [Save identities and digests](reusable-package-20261008.json) let a later session retrieve these exact files. Original unsplit archive SHA-256 is `b9536aa9dbce308edcdb735c518395ebf2e02d20ecdf53b181deeded19d07769`; its size is 936,569,944 bytes. The archive is not committed to Git.

After downloading both parts into one directory:

```bash
cat gem5-c8222cc-linux-x86_64-20261008.tar.gz.part01 gem5-c8222cc-linux-x86_64-20261008.tar.gz.part02 > gem5-c8222cc-linux-x86_64-20261008.tar.gz
printf '%s  %s\n' b9536aa9dbce308edcdb735c518395ebf2e02d20ecdf53b181deeded19d07769 gem5-c8222cc-linux-x86_64-20261008.tar.gz | sha256sum -c -
tar -xzf gem5-c8222cc-linux-x86_64-20261008.tar.gz
./gem5-c8222cc-linux-x86_64-20261008/bin/run-gem5 --build-info
```

The package includes the original unstripped executable, the immutable upstream source archive and notices, complete build logs, and a minimal Python 3.12.14 runtime. All 918 packaged regular files passed digest/size/mode verification. The relative-path wrapper passed build-info and loader checks in a clean environment on the current Ubuntu 24.04 x86-64 host. Other hosts were not tested. System glibc, zlib and GNU C++ libraries still must satisfy the recorded loader requirements.

For project execution, bind `run.py` to the real ELF rather than the wrapper so its report records the approved simulator digest. From the project root, with an absolute package directory:

```bash
GEM5_REUSE_DIR=/absolute/path/gem5-c8222cc-linux-x86_64-20261008
printf '%s  %s\n' 3f8728c9b72374ace0b3372f1ea5bab23bafbdcc15652fe466c4a00b2ddbc0a6 "$GEM5_REUSE_DIR/bin/gem5.opt" | sha256sum -c -
python3 - "$GEM5_REUSE_DIR" --gem5 "$GEM5_REUSE_DIR/bin/gem5.opt" \
  --resources /absolute/path/verified-resources \
  --runtime-binary /absolute/path/openrx-runtime-probe \
  --output-dir /absolute/path/new-runtime-attempt <<'PY'
import os, runpy, sys
bundle = sys.argv[1]
os.environ["LD_LIBRARY_PATH"] = bundle + "/python/lib"
os.environ["PYTHONHOME"] = bundle + "/python"
sys.argv = ["simulator/gem5/run.py", *sys.argv[2:]]
sys.path.insert(0, "simulator/gem5")
runpy.run_path(sys.argv[0], run_name="__main__")
PY
```

The small launcher initializes the installed host Python before setting the
bundled Python environment for the gem5 child. This avoids applying a Python
3.12 standard library to a host interpreter of a different version.

Use an existing verified guest ELF or build it using the project recipe. Pinned guest resources are acquired with `simulator/gem5/prepare.py`; they are not redistributed in this package. Retain each attempt in a new output directory. Add the unchanged light hash ELF only after the nine runtime controls pass. The package itself contains no guest pass, timing or power claim.

The current runner defaults to no wall-clock cutoff. Monitor the serial stream and preserve evidence; positive `--timeout SECONDS` is an explicit opt-in. The simulated `--max-ticks` guard remains separate from host elapsed time. Keep historical 1,200-second attempt records unchanged.

[Build and link evidence](link-recovery-20261008/README.md) and [latest execution results](README.md) are separate records. Hosted manual build/cache/download reuse has offline checks but has not been exercised end to end.


## Light matrix execution allowance

The extended unchanged attempt independently passed nine runtime and 31
arithmetic controls, then was manually stopped after proof that its `10^13`
per-call tick allowance cannot cover both mandatory cache initializations.
[Exact ELF/configuration budget review](light-resume-20261008/BUDGET-REVIEW.md)
establishes a conservative minimum of 10,519,287,679,000 ticks for the Argon
round loops alone. Use an explicit larger allowance such as
`--max-ticks 100000000000000` for the next unchanged light matrix, retaining
a fresh output directory and complete monitoring. This is a finite proposed
guard, not a guarantee of completion or a wall-time estimate.

The execution-session stop generated no final runner report;
[the saved actual review](light-resume-20261008/REVIEW.md) preserves that
limitation, complete runtime frames and incomplete hash output. The new
optional `--stop-file PATH` allows a stop request from a separate tool/PID
namespace: choose a nonexistent path at launch, then create it to request
the runner's own SIGINT/cleanup/report path. Use a fresh stop path for every
attempt. Tool/session termination itself must not be assumed to yield a
runner report.
