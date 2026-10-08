# Actual gem5 guest preparation — 2026-10-08

**Executed: resource downloads, digest verification and independent ELF/guest
library inspection. This evidence does not establish a gem5 Linux boot.**

The exact three guest inputs from
[`resources.json`](../../../simulator/gem5/resources.json) were downloaded from
the gem5 distribution URLs. The firmware/kernel upstream MD5 values matched;
the gzip disk expanded to 5,242,880,000 bytes and its MD5 matched the exact
catalog resource. SHA-256 values of every downloaded input, including both disk
representations, are now pinned. The final scripted preparation command below
revalidated those already downloaded files; its observed output is retained in
[`resource-preparation-20261008.json`](resource-preparation-20261008.json).
The catalog MD5 values are upstream metadata; these SHA-256 pins are independently
computed identities of the observed downloads.

The independent [guest ELF audit](guest-elf-audit-20261008.json) binds the actual
CI runtime/hash executables to the inspected GPT root partition and its extracted
dynamic libraries. All 15 direct/transitive provider checks passed, including
345 required versioned symbols. Runtime ELF SHA-256 is
`8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac`;
the unchanged workload ELF SHA-256 is
`61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`.
They are dynamic ELF64 RISC-V/LP64D executables. The workload's aggregate ISA
attribute includes V/Zvkned because unchanged upstream builds optional objects;
startup SIGILL recovery and actual scalar execution remain required.

The review inspected the exact image's GPT partition 1, init script, shell
startup, bridge executable and after-boot script. `/sbin/gem5_init.sh` is present,
`/sbin/init` points to it, and `no_systemd` leads to the gem5 shell/readfile path.
The partition and library audit is not a substitute for executing that path.
See [independent review](GEM5-REVIEW.md).

The local host was Linux 6.18.44 x86-64/glibc 2.39, Python 3.12.14, OpenSSL 3.5.8,
GNU readelf 2.42. Exact JSON record digests and the resource-manifest digest are
retained in [preparation-evidence-index.json](preparation-evidence-index.json).
No disk images, runtime ELFs or extracted operating-system libraries are
committed by this evidence package.

Actual verification commands run from the repository root:

```bash
python3 simulator/gem5/prepare.py --output-dir /tmp/openrx-fs-resource-audit
python3 -m unittest discover -s tests -p test_gem5_fs.py -v
python3 -m py_compile simulator/gem5/prepare.py simulator/gem5/fs.py simulator/gem5/run.py
python3 --version
readelf --version
ldd --version
sha256sum /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe /tmp/openrx-fs-resource-audit/preparation.json
bash -n /tmp/openrx-fs-resource-audit/test-guest.sh
bash -n /tmp/openrx-fs-resource-audit/test-guest-light.sh
```

Both generated transfer scripts passed shell syntax inspection (18,993 and
521,870 bytes). Offline identity/framing tests passed seven tests. See
[runtime CI](RUNTIME-CI.md) for actual native/QEMU execution of the cross-built
probe; this preparation report makes no gem5 execution claim.

The next bounded command, after a successful pinned source build, is:

```bash
python3 simulator/gem5/run.py --gem5 /tmp/openrx-gem5-source/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt --resources /tmp/openrx-fs-resource-audit --runtime-binary /tmp/openrx-runtime-ci/probe-riscv/openrx-runtime-probe --output-dir /tmp/openrx-gem5-runtime-attempt --timeout 1200
```

The local source-build environment needs its retained scratch native-library
path in `LD_LIBRARY_PATH`; this is an environment dependency, not a gem5 source
patch. The source-build record will identify the actual executable, flags,
toolchain, dependency workarounds and outcome. A real attempt must retain
`report.json`, serial/stdout/stderr logs, simulation phase snapshots, generated
DTB/configuration and the source-build record. Until those executed criteria
pass, task #16 remains open and M3/M4/M5 remain gated.
