# OpenRX

OpenRX researches and implements hardware for exact **RandomX v2**, with v1
regression coverage and licensed reusable IP. The target is **1 MH/s below
2,500 W for the whole machine**. That target, a final architecture and physical
power/performance/area remain unvalidated.

[Current status](docs/STATUS.md) separates accepted functional results from
conditional models and open physical gates. [Issue #72](https://github.com/jliu67/OpenRX/issues/72)
tracks current architecture research and review.

## What is here

- [RTL components](rtl/) for arithmetic, memory service and the connected hash
  lifecycle, with source-bound [validation evidence](docs/validation/).
- [Shared-context VM experiments](experiments/shared_context_vm/) with native
  checkpoint checks, shared execution/fetch resources and a bounded reproduction
  runner. Their README states the exact accepted scope and external prerequisites.
- [Architecture tools](tools/architecture/), native references and
  [measurement tooling](benchmarks/) for reproducible comparisons.

One default 8×2,048 functional hardware-dataset hash is
[independently accepted](docs/validation/dataset-fullhash-20261020/README.md).
Its modeled clocks and retained preparation/services establish functional
correctness within that scope, not physical throughput or energy efficiency.

## Start here

| Need | Read |
| --- | --- |
| Current results, limitations and next research | [Status](docs/STATUS.md), [issue #72](https://github.com/jliu67/OpenRX/issues/72) |
| Experiment plans and source-bound outcomes | [Experiment index](experiments/README.md), [validation records](docs/validation/) |
| Workload and source provenance | [RandomX baseline](docs/RANDOMX.md), [third-party notices](THIRD_PARTY_NOTICES.md) |
| Timing and power measurement boundaries | [Steady-state protocol](benchmarks/steady/README.md), [power-import protocol](benchmarks/power/README.md) |
| Scientific acceptance and milestones | [Roadmap](docs/ROADMAP.md), [task board](docs/TASKS.md) |
| Agent work and retained project memory | [Agent instructions](AGENTS.md), [communication](docs/COMMUNICATION.md), [project memory](memory/PROJECT.md) |
| Local execution and source retention | [Execution policy](docs/LOCAL_EXECUTION.md), [resource policy](docs/LOCAL_RESOURCE_POLICY.md), [publication policy](docs/PROGRESS_PUBLICATION_POLICY.md) |

## Quick start (Linux)

Use Python 3.10+, Git, CMake, a C/C++ toolchain and Make. From the repository root:

```sh
python3 scripts/verify_vendor.py
python3 scripts/workload_profile.py
```

For an authorized local build and functional check:

```sh
bash scripts/build.sh
bash scripts/test.sh
python3 scripts/benchmark.py --mode verify --versions v1 v2 --nonces 2 --repeats 1
```

Follow the [execution policy](docs/LOCAL_EXECUTION.md) before builds or workloads.
Full-dataset and same-process controls allocate over 2 GiB and require a reviewed
local request, fresh admission/resource checks and the existing exclusive slot.
Functional smoke runs and synthetic power-import tests do not measure efficiency;
see the [measurement boundaries](benchmarks/README.md) before reporting results.

RandomX v2.0.1 is included in `vendor/randomx/` at upstream commit
`aaafe71322df6602c21a5c72937ac284724ae561`; no submodule download is required.
Original BSD-3-Clause licenses/notices are retained. Project directories also
include `scripts/` and `tests/` for tooling and checks, `simulator/` for retained
simulator work, and `.github/` for existing CI and collaboration workflows.

## History

Detailed results stay in their experiment/evidence records. The complete
[pre-cleanup README](https://github.com/jliu67/OpenRX/blob/fee4e697741ce520fa917405a58ec9914f071498/README.md)
and [delivery timeline](https://github.com/jliu67/OpenRX/blob/fee4e697741ce520fa917405a58ec9914f071498/docs/STATUS.md)
remain available at the pinned prior main commit. Dated records describe their
original sources and acceptance boundaries; current navigation does not replace
those records or change any scientific criterion.
