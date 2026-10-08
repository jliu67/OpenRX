# Simulator acquisition and reuse audit — 2026-10-08

**No compatible prebuilt executable for the pinned gem5 v25.1.0.1 revision was
verified. The official development container contains a real prebuilt ALL
simulator, but its documented simulator version is v24.1.0.1 and it is not a
drop-in replacement for this guest/configuration.** This audit downloaded only
registry/API metadata. It did not pull containers, install packages, compile,
or execute a simulator.

## Official distributions checked

| Distribution | Observed evidence | Consequence |
|---|---|---|
| [v25.1.0.1 release](https://github.com/gem5/gem5/releases/tag/v25.1.0.1), commit `c8222cc67a399bfc01e8658dd14b30d5bfd634f9` | [GitHub release API](https://api.github.com/repos/gem5/gem5/releases/tags/v25.1.0.1) returned release 311890774, `assets: []`; the two UI downloads are generated source tar/zip archives | No official executable release asset |
| Official Ubuntu dependency containers | The [pinned all-dependencies Dockerfile](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/util/dockerfiles/ubuntu-24.04_all-dependencies/Dockerfile) and [minimal Dockerfile](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/util/dockerfiles/ubuntu-24.04_min-dependencies/Dockerfile) install host dependencies without fetching/building gem5 | Pulling these does not remove the simulator build |
| Official `gpu-fs` and `gcn-gpu` containers | [Pinned GPU FS Dockerfile](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/util/dockerfiles/gpu-fs/Dockerfile) and [GPU SE Dockerfile](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/util/dockerfiles/gcn-gpu/Dockerfile) install dependencies/ROCm; no gem5 build or binary copy | Examples mount a separate gem5 checkout; these are not verified RISC-V simulator binary distributions |
| Official `devcontainer` | [Pinned Dockerfile](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/util/dockerfiles/devcontainer/Dockerfile), also checked on current `stable`, downloads `v24.1.0.1.tar.gz`, builds `build/ALL/gem5.opt`, and copies it to `/usr/local/bin/gem5`; registry image history confirms that copy | Genuine prebuilt simulator, but old version; container tag `v25-1` is not the binary version |
| conda-forge | [Package API](https://api.anaconda.org/package/conda-forge/gem5) and `conda-forge/gem5-feedstock` GitHub repository returned 404 | No verified conda-forge acquisition route |
| Guix / distro packages | [Official gem5 Guix article](https://www.gem5.org/project/2022/05/23/guix.html) describes a 2022 proof of concept and future upstream binary substitution. Current gem5 package/substitute identity was not verified. Ubuntu package lookup timed out; Debian lookup returned a JavaScript challenge | No actionable current exact-version package was established; these failures do not prove universal package absence |

## Verified development-container identity

Anonymous GHCR API queries used a temporary pull token held in process memory;
no credential/token was logged or persisted. The registry's content digests
matched SHA-256 of the returned manifest bytes. Published package page:
[gem5 devcontainer](https://github.com/gem5/gem5/pkgs/container/devcontainer).

| Item | Observed value |
|---|---|
| Tag | `ghcr.io/gem5/devcontainer:v25-1` |
| OCI index digest | `sha256:269014879d34173a017876be468476cf5dafa3832c08b6b3dd229ebe9459e0de` |
| Linux amd64 manifest | `sha256:68a976fe4dc918bd4a4f535f79be79aa30a0b58eaf2461a3cd1ea45d21f4aaab` |
| Linux arm64 manifest | `sha256:c740d80c8c825db6f048a6c357904966a1725813fe7b86d05f94142b22286790` |
| amd64 compressed layer total | 2,303,975,022 bytes (2.15 GiB); expanded size not measured |
| amd64 image config digest | `sha256:9b03f9cc913be4bd620ca96db31fc4cc05abff7489113c8c14270120d8b53544` |
| amd64 creation time | `2025-12-14T08:02:05.621411136Z` |
| Binary destination / guest ISA build | `/usr/local/bin/gem5` / `ALL` according to Dockerfile and image history |
| Source label | `https://github.com/gem5/gem5`; no simulator source-revision label |
| Version label | `24.04` refers to Ubuntu, not gem5 |

The `latest` index was also inspected:
`sha256:025ca544f062ad149a46592cc9d2784596dadd60cde1834f9447630d31a3c29c`,
amd64 `sha256:d337a22f1682f0285690159adfeb0394c8f3770042e331577a998110aeb1fb11`,
2,306,132,805 compressed layer bytes, created 2026-03-14. Neither image was
executed, so no observed binary version or standalone ELF SHA-256 is claimed.
The Dockerfile's v24.1.0.1 source pin establishes a candidate, not a substitute
for checking the actual binary and provenance after acquisition.

A Docker-equipped host can inspect the immutable amd64 candidate without
rebuilding it:

```bash
docker pull --platform linux/amd64 ghcr.io/gem5/devcontainer@sha256:68a976fe4dc918bd4a4f535f79be79aa30a0b58eaf2461a3cd1ea45d21f4aaab
docker run --rm --platform linux/amd64 ghcr.io/gem5/devcontainer@sha256:68a976fe4dc918bd4a4f535f79be79aa30a0b58eaf2461a3cd1ea45d21f4aaab /usr/local/bin/gem5 --build-info
```

These commands were not run. No Docker, Podman, Singularity, Apptainer, conda,
micromamba, mamba, skopeo or oras executable was available locally. Host amd64
is separate from simulated guest RISC-V: an ALL host binary can model RISC-V,
whereas a host package being named `linux-riscv64` would not make it runnable on
this amd64 host.

## Compatibility and recommended exact-version route

The current `fs.py` imports `gem5.simulate.exit_handler.ExitHandler` and binds
numbered hypercalls 1/2/3 emitted by the inspected Ubuntu guest. The v24.1.0.1
source has no `exit_handler.py`; its simulator implements the older
`ExitEvent`/generator mechanism. The [pinned release notes](https://github.com/gem5/gem5/blob/c8222cc67a399bfc01e8658dd14b30d5bfd634f9/RELEASE-NOTES.md)
place the new hypercall handlers in v25.0 and specifically record the v25.1
RISC-V fix [#2464](https://github.com/gem5/gem5/pull/2464) for gem5-bridge
`readfile`. An older container therefore requires a separately reviewed
guest/configuration and cannot be accepted by silently changing the source pin.

The fastest credible route for the current configuration is to finish the
already retained, nearly linked **unchanged** pinned build, then preserve and
reuse its executable plus source/configuration/build provenance. A successful
same-repository build artifact should be reusable by digest on later guest runs;
ordinary PR checks should not repeatedly cold-build the simulator. Source
integrity, binary identity and actual guest runtime controls remain required.
The new incremental attempt and any guest execution belong in separate records;
the earlier timeout evidence remains unchanged.
