# Independent simulator acquisition review — 2026-10-08

**Accept the acquisition/scaffolding change.** Reviewer `/root/gem5_review`
independently read the implementation, pinned gem5 source, workflows, controls
and documentation. This accepts neither a Linux boot nor executed compatibility.
The new manual hosted build/cache/artifact-reuse path has not executed yet.
Local linking and observed executable build-info are separate build evidence.

## Reviewed behavior

Pull requests run vendor integrity and offline tests only. Actual guest execution
is manual and requires a successful same-repository manual producer run plus an
externally supplied binary SHA-256. The consumer validates run/attempt/project
commit, exact bundle members/digests, pinned source/build options, canonical
configuration and recorded build environment before chmod, loader checks or
executable startup. It never builds a simulator implicitly. Environment variables
and quoted arguments handle user inputs; strict decimal/hex checks precede API
and artifact requests. Repository permissions remain read-only. Checkout
credentials are not persisted.

The separate manual builder uses supported upstream SCons commands. Its cache
namespace contains the source pin, target, linker recipe, full installed-package
digest and generated configuration digest. Only that prefix is restored, with a
new immutable run/attempt key for each checkpoint. The final checkpoint guard
suppresses saves on configuration/toolchain drift. Logs, exit codes, source status,
configuration and absolute paths are retained after failure. The same repository
workspace/build paths are required for reuse; eviction, scope or environment
changes can require a deliberate cold build. No resumed-build speed is promised.

Producer metadata and self-digests establish consistency with the selected run.
They are not independent source attestation or reproducibility proof. The operator
must review the producer project commit and expected binary digest. Neither cache
reuse nor successful simulator startup establishes guest execution.

## Independent controls and limits

- All **23 gem5 offline tests** passed: 16 bundle controls and seven existing
  full-system runner controls. Bundle ELFs are synthetic header-only data and
  are never executed. Full stdout/stderr and commands are retained below.
- Both workflow YAML files and all 18 Bash run scripts parsed successfully.
  Static checks confirm the manual/PR split, read-only permissions, absent
  consumer source build and validation-before-execution ordering.
- Actual retained prefixless Kconfig and generated `buildEnv` contain the
  required options. Pinned `m5/main.py` prints these options as expected.
  Observed executable output remains a separate check after a successful link.
- A host-only synthetic timeout pipeline retained exit 124 despite successful
  log capture. The exact final workflow checkpoint script accepted matching
  synthetic configuration and suppressed drifted/missing configuration.
- Pinned `SConstruct` defines `--limit-ld-memory-usage` and checks linker support
  before appending `-Wl,--no-keep-memory`. This affects host linking, not the
  declared simulator features. No memory or build-time improvement is claimed.

The review fixed prefixless Kconfig compatibility, documented API workflow-path
`@ref` compatibility, exact cache identities, timeout evidence retention and the
cache drift guard. The loader check uses Python rather than an undeclared tool.
The source pin, guest configuration, resources and existing runner are unchanged.

Complete control inputs, commands, errors and logs are in
[`acquisition-review-20261008/review-controls.json`](acquisition-review-20261008/review-controls.json),
[`23-tests.stderr`](acquisition-review-20261008/23-tests.stderr) and
[`synthetic-timeout.log`](acquisition-review-20261008/synthetic-timeout.log).
No source build, cache service operation, downloaded simulator execution or guest
execution was performed by these review controls. Full dataset, intended-core
coherence, calibrated timing and physical power remain outside acceptance.

## Reviewed bytes

| File | SHA-256 |
|---|---|
| `.github/workflows/gem5-build.yml` | `248a9f47ac79920e1f3387bcb7f61880df69d10dfb8a4eb7bdd0706697a8589a` |
| `.github/workflows/gem5-fs.yml` | `4fc824189cc35f5c5da6a5108a0224ed20bef51804bdfb73a7ad2e57b613c755` |
| `simulator/gem5/bundle.py` | `bac76036889773dc05861cfa9050f4cbf161424dda8b40fcbcc2f878de0ac6b1` |
| `tests/test_gem5_bundle.py` | `f699c51fde4f221874796630455fbf2d537b14b064d383a9681fdd61129da7e6` |
| `tests/fixtures/gem5-riscv-config.txt` | `e8b427ddf7a991883020766f90f8f2a08bed769f831d43d448c8f68845ab39b5` |
| `simulator/gem5/README.md` | `9621575fb2c6b23117ae76281b33970f94cb8a03a29e7f9f5ba7a5002a5a9597` |

## Primary references

- [Pinned gem5 SConstruct](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/SConstruct): config generation, signature storage and linker option.
- [Pinned Kconfig wrapper](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/site_scons/gem5_scons/kconfig.py): empty `CONFIG_` prefix.
- [Pinned build-info output](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/src/python/m5/main.py).
- [GitHub workflow-run API](https://docs.github.com/en/rest/actions/workflow-runs): authenticated metadata and documented path/ref form.
- [GitHub cache reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching): prefix matching, immutable keys, branch restrictions and unsigned cache boundary.
- [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use), [workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) and [artifact retrieval](https://docs.github.com/en/actions/tutorials/store-and-share-data).
