# Same-process adapter (P1-05)

Opt-in Linux/C++17 harness linked against the **unmodified pinned RandomX library**.
The older `scripts/benchmark.py` remains the upstream-harness baseline. This adapter
is measurement infrastructure, not an optimized RandomX implementation or a miner.

## What is reused and what is timed

The dataset is initialized once with the upstream seed-0 four-byte key. Each worker
owns one VM for each selected version. The dataset, VMs and worker threads survive
all controls, warmups and measurements. Before measurement, both selected versions
must pass the upstream 1,000-nonce aggregate reference. A fresh nonce sequence and
aggregate are used in every trial. Warmup immediately precedes each measured trial
unless explicitly disabled. V1/V2 order reverses on alternate repetitions; use an
even repeat count (at least four for the formal baseline).

Every interval stores a CLOCK_REALTIME reading bracketed by two CLOCK_MONOTONIC
readings at each boundary. `elapsed_ns = end.mono_before_ns - start.mono_after_ns`.
The start is before releasing already-created workers; the end is after their
completion notification. Dataset/cache/VM initialization, thread creation, previous
warmups, log I/O and final cross-worker digest reduction are **outside** this
interval. Worker wakeup, scheduler delays, nonce/batch setup, per-worker digest
aggregation, FP environment restoration and completion synchronization are **inside**.
This is a precisely delimited harness interval, not pure instruction execution time.

Records are emitted **after** each interval, not as real-time external trigger
messages. Clock resolutions and both bracket widths are available in the raw
records. Nanosecond units do not establish nanosecond accuracy. The report records
wall-versus-monotonic discrepancy; neither a stable clock nor these markers prove
meter synchronization. CLOCK_REALTIME can step or slew. Any future power importer
must validate the clock mapping, sample coverage, meter response/latency, gaps and
measurement boundary. No energy calculation exists here; power and hashes/J stay
null. Initialization energy is excluded by this boundary, not silently amortized.

## Deliberate differences from upstream harness

Workers use disjoint static-stride nonce partitions and the public batch
`first/next/last` API. Upstream's benchmark dynamically distributes nonces and uses
`next` for its tail. Both must hash the same input set and match known aggregates,
but **their throughput numbers are not interchangeable**. Compare configurations
within the same adapter and retain the upstream harness as an independent control.
The nonce template and reference constants are checked against pinned
`vendor/randomx/src/tests/benchmark.cpp` in native tests. The inherited template's
BSD-3-Clause notice is retained in `main.cpp`.

The initial scope is full-dataset/JIT, seed 0, small pages, selectable v1/v2 and
hardware/software AES. Unsupported modes/flags fail; there is no automatic AES or
interpreter fallback. Hashing/init workers are bounded to 256 and nonce/repetition
inputs are range checked. Batch APIs alter worker rounding, so FP state is saved
and restored around every job. Use an external `taskset` CPU set on the intended
host; this constrains the process and inherited workers but does not pin each worker
to a unique CPU. No privileged tuning, huge-page configuration, paid resources,
network mining, RISC-V performance result or hardware-power access is introduced.

## Build and bounded correctness controls

```bash
bash scripts/build_steady.sh
python3 -m unittest discover -s tests -v
python3 tests/native_steady.py
```

Native tests require hardware AES/JIT support for the explicit hardware cases;
unsupported hardware fails rather than silently claiming coverage. They test
1-worker hardware/software, 2-worker duration rejection, 3-worker software with an
uneven nonce partition, repeated known hashes, invalid arguments and differential
17-nonce checks against the unmodified upstream benchmark. These are short CI
**correctness controls**, not the controlled hardware matrix of P1-04.

## Isolated local staging and controls

For retained read-only sources, pass `--build-root` to `build_steady.sh`. This
selects `scripts/stage_native.py`, which verifies the vendor manifest before
compilation, builds the unchanged library and adapter in a **fresh external**
directory, explicitly links that library and retains tool versions, complete
step logs, CMake caches, commands and artifact/source SHA-256 in `build.json`.
Existing destinations, including failed attempts and retired CMake caches, are
rejected and preserved. The no-argument build remains the legacy developer path.

The steady wrapper accepts `--binary`, `--build-root` and `--output-dir`.
`--build-root` requires a successful staging receipt and verifies its compiled
source and artifact bindings before launching. The selected caches and receipt
are copied into the trial evidence. `--binary` alone supports an independently
verified executable; its provenance still needs the operator's reviewed input
binding. These location options never reach the native scientific command or
change the strict JSONL validator. Explicit output destinations must be fresh,
external to the source and disjoint from build/input paths. Missing or altered
inputs retain a failed `run.json`; failed/too-short/incomplete trials retain raw
output. No explicit path option certifies a controlled host experiment.

`tests/native_steady.py` accepts the same build/binary/output locations plus
`--upstream-binary`. With a staged build, both executables must match its receipt.
An explicit output directory contains every control trial, CLI-error record and
upstream differential log; no control evidence is written into the retained
source or build. Its six native tests and original scientific options are
unchanged. Upstream tests can run directly as the staged `randomx/randomx-tests`
binary, with stdout/stderr retained by the local runner.

Only after independent source/request review, verified LOCAL_ACTIVE release,
fresh host/resource checks and the shared compute slot, submit through the
[immutable local runner](../../docs/LOCAL_EXECUTION.md). Example specification
(portable placeholders; use actual reviewed identities and fresh request keys):

```bash
# OPENRX_SOURCE is a verified pinned read-only source snapshot containing this PR.
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" submit \
  --request-key issue-35-native-build-SOURCE-attempt-01 --kind build \
  --cwd "$OPENRX_SOURCE" --source "$OPENRX_SOURCE" \
  --input /usr/bin/cmake --input /usr/bin/x86_64-linux-gnu-g++ \
  -- python3 "$OPENRX_SOURCE/scripts/stage_native.py" \
  --build-root '{execution_dir}/native-build' --jobs 6 --arch native

# Wait for the build receipt, run the runner's verify BUILD_ID, and independently
# review build.json/logs before assigning OPENRX_BUILD to that native-build path.
python3 "$OPENRX_RUNNER" --root "$OPENRX_LOCAL_ROOT" submit \
  --request-key issue-35-native-controls-SOURCE-attempt-01 \
  --kind validation --validation-scope regression-smoke \
  --cwd "$OPENRX_SOURCE" --source "$OPENRX_SOURCE" --input "$OPENRX_BUILD" \
  -- python3 "$OPENRX_SOURCE/tests/native_steady.py" \
  --build-root "$OPENRX_BUILD" --output-dir '{execution_dir}/controls'
```

The reviewed request must additionally bind the actual interpreter, compiler,
toolchain/dependencies, environment and scientific oracle. Use six compile
workers as an initial candidate; retain measured worker utilization and peak
memory and revise only from evidence. Controls initialize the full dataset
(over 2 GiB), so they remain a separate serialized local request. The unchanged
`owner-local-max-v1` profile and fresh kernel/headroom checks choose the allowed
budget; this adapter neither changes limits nor allocates the slot. Preserve the
build execution/receipt and complete source snapshot when later trials consume it.

Formal trials use the steady wrapper with `--build-root "$OPENRX_BUILD"` and
`--output-dir '{execution_dir}/trial'` in a separate approved local request. Keep
the same nonces/seeds, alternate v1/v2 order with an even repeat count of at least
four, compare the unchanged thread/AES matrix and retain duration failures.
Controlled settings, pilot duration, affinity and all EXP-001 acceptance remain
required. Compilation or the six correctness controls cannot complete #8/M1.

## Prepare a real-host trial

```bash
# Example workload count only: increase it until every measured interval clears
# the duration gate. Keep the SAME nonce count for compared versions/configurations.
python3 scripts/steady_benchmark.py --versions v1,v2 --threads 1 \
  --aes hardware --nonces 30000 --warmup-nonces 1000 \
  --repeats 4 --min-seconds 30 --timeout 1800
```

Choose an allowed CPU set, document host/cache/memory/NUMA/thermal/power settings,
repeat correctness on that host and run a pilot before formal trials. A warmup
count is not proof of thermal equilibrium. Both versions reuse one dataset and
same-key inputs; this is not a dataset-rekey experiment. A rejected duration is
retained and returns failure, not discarded or promoted into a summary. The total
process timeout includes dataset initialization and controls. Do not use defaults
or a green CI run as evidence that the formal M1 gates are met.

The Python wrapper verifies vendor integrity and saves `adapter.jsonl`, separate
stderr, `run.json`, binary/source SHA-256, CMake caches, CPU/affinity/cgroup context
before and after, commands and exit status in a unique `benchmarks/results/*-steady/`
directory. Its strict validator checks event order/completeness, exact counts,
known hashes, repeat determinism, command/config agreement, clock brackets and
minimum duration before summarizing only accepted measurements. Controls/warmups
are excluded. Timeouts and malformed/incomplete output retain raw evidence; timed
out process groups are killed and reaped. A large wall-clock discrepancy is
reported, not certified as usable for power alignment.

P1-06 still needs real synchronized power readings; P1-07 needs controlled dynamic
profiling. Evidence and current status belong in `docs/TASKS.md`, issue #1 and
`memory/HANDOFF.md`; do not mark all of Phase 1 complete from this adapter alone.
