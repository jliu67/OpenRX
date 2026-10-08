# Guest ELF and dynamic-library review

Independent offline review on 2026-10-08. Both retrieved CI guest binaries
can resolve their versioned dependencies using the actual pinned Ubuntu
24.04 guest image. This establishes a prerequisite for execution, not Linux
boot, target-core correctness, calibrated timing or measured power.

## Binary identity and provenance

The retrieved CI archive has SHA-256
`a4cd49b7f6f54a94fed9d6b3087714eaa00063ad5f732c201b54464b0cc94d05`.
Its environment records GCC 14.2.0, binutils 2.42, QEMU 8.2.2 and checkout
`82398b9545c1bfc1d80bb7f79c41f783048fb89c`. Record this checkout alongside
the implementation commit in [runtime-ci-audit.json](runtime-ci-audit.json);
the two are distinct source identities. This review does not independently
establish their Git ancestry.

| Binary | Bytes | SHA-256 |
|---|---:|---|
| `openrx-runtime-probe` | 13,760 | `8fa3f0de97cf3df9aaecebe9deb92c3dfd8c8e7bcd18fe87e090b746e57b28ac` |
| `openrx-riscv-probe` | 376,824 | `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657` |

Both digests match their retrieved CI report. Both are ELF64 little-endian
RISC-V PIEs with RVC and double-float ABI flags. Both use
`/lib/ld-linux-riscv64-lp64d.so.1`; neither is static.

The runtime workflow uses
`riscv64-linux-gnu-gcc-14 -std=c11 -O2 -Wall -Wextra -Werror -march=rv64gc -mabi=lp64d`.
The hash probe's actual compile-command entry uses
`riscv64-linux-gnu-g++-14 -march=rv64gc -mabi=lp64d -O3 -DNDEBUG -Wall -Wextra -Werror -frounding-math -fno-fast-math -ffp-contract=off`.
The retrieved `compile_commands.json` SHA-256 is
`79514d0b414a652ced79fcaddd3a2a101746e04671171c95fe177b2135009a93`.

## Exact guest image and linkage

The prepared whole disk is pinned to SHA-256
`ddf1ebb56454ef37e88d6de8aefdef7180fc9a2328a3bf8cff02f7a043e7127b`.
GPT root partition 1 spans sectors 235520–10239966 (512-byte sectors),
starting at byte 120586240 and containing 5122276864 bytes.
Independent streaming SHA-256 of those bytes and the inspected extracted
root partition agreed:
`f248678270188fb39c62977ed83d96c3e415cc5b6ed40fad2761e0bfbafbc614`.
The extraction includes 16896 additional trailing disk bytes outside that
partition, which were excluded from this comparison.

`debugfs` read `/usr/lib/os-release` as Ubuntu 24.04 LTS. The guest has
`/lib -> usr/lib` and
`/usr/lib/ld-linux-riscv64-lp64d.so.1 -> riscv64-linux-gnu/ld-linux-riscv64-lp64d.so.1`.
`libstdc++.so.6` resolves to `libstdc++.so.6.0.33`.

| Extracted guest provider | SHA-256 |
|---|---|
| `libc.so.6` | `1d577103e808d8457224b37097c0ecf94f4b0c3bab25f8dc0a1576679e7c3cf8` |
| `libm.so.6` | `1720f57a384a55ca7b2443013e8e4439c70b3a719cd64b017f677a3a60de2dd1` |
| `libgcc_s.so.1` | `187b4949857344b99b069fb25cbeeef181f4ae259cd045da98514fdb5d84067e` |
| `libstdc++.so.6.0.33` | `61d3215ef127c6ae90114ac9c478d8bcd85bb91c28a78c4ad356956dcbb0d1e1` |
| `ld-linux-riscv64-lp64d.so.1` | `861150abbef0a669bc3d475ca2f71b89371b3dc3e13731367a5549a492d78caa` |

All required version nodes and **345 versioned-symbol imports across 15
direct/transitive dependency pairs** are present in the inspected provider
ELFs. The runtime contributes 21 required imports and the hash probe 77;
the remaining 247 are transitive guest-library imports. In particular, the
hash probe's `GLIBCXX_3.4.32` requirement is present, as are its
`GLIBC_2.34` and `GLIBC_2.27` requirements. The guest libc provides version
nodes through `GLIBC_2.39`.

This comparison uses `readelf -h -l -d -A`, `readelf --version-info` and
`readelf --dyn-syms --wide`. Library version indexes bind each imported
symbol to its named provider; matching only the highest version string
would be insufficient. Raw outputs and the machine-readable audit were
retained during this review. No guest library or disk-image write occurred.

## ISA limitation

The runtime's ELF ISA attribute is scalar RV64 with M/A/F/D/C, Zicsr,
Zifencei and Zmmul. The hash probe's aggregate ELF attribute additionally
advertises V/Zve/Zvkned/Zvl because unchanged upstream links optional vector
and crypto translation units. Actual compile commands include
`-march=rv64gcv` and `-march=rv64gcv_zvkned` on those specific units.

The existing QEMU CI executed this same binary with `-cpu rv64,v=false`.
gem5 must also explicitly disable RVV so upstream's SIGILL-protected ISA
detection selects the scalar JIT fallback. Passing the preceding Linux
runtime controls remains necessary: ELF/library compatibility alone cannot
establish signal recovery, JIT coherence, permissions or correct hashes.
