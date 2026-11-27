# Shared-context VM experiment

This experimental RTL banks four contexts around one integer datapath, one
multiply unit, one two-lane FP unit and one two-lane divide/sqrt unit. The shared
fetch variant adds four non-speculative one-entry instruction queues. The
iteration bench adds actual entry reads/conversion, precomputed dataset/XOR and
one shared AES lane with ordered tail stores. Golden `rtl/` and vendor sources
are unchanged. Current work and review state are tracked in
[issue #72](https://github.com/jliu67/OpenRX/issues/72).

## Accepted scope

These independently reviewed **simulated batch clocks** use 8 MiB of behavioral
private scratchpad, one 16-byte SP request/return port and one instruction
request/return port. The iteration bench has one precomputed 64-byte dataset
request/return port with minimum response latency 1. All preparation and initial
SP loading are untimed.

| Bench | Work per batch | SP minimum | Serial | Interleaved, fetch off | Shared fetch |
| --- | --- | ---: | ---: | ---: | ---: |
| contexts16 / fetch18 | Four replicas of program-0's 384-instruction kernel | 1 | 9,892 | 6,676 | 5,266 |
| iterations20 | First complete iteration of native programs 0–3 | 1 | 11,477 | 7,070 | 5,910 |
| iterations20 | Same four checkpoints | 10 | unrun | 7,413 | 6,277 |

The four iteration checkpoints come from **one input**, not four nonces. Their
executed instruction counts are 384/384/393/384 and bytecode memory-event counts
are 80/90/82/91. Initial FP rounding is 0/1/1/1 because rounding carries across
programs of that canonical hash. Each independently initialized checkpoint runs
one iteration; this delivery does not implement consecutive iteration carry.

Contexts16 retains its old core interface and is compiled separately. Fetch18
includes late-response cancellation, all four queues full, held transfers and
four rejection fixtures. These component checks do not certify cancellation
through the iteration shell. The finite FU sequence rejects request 255;
fetch18's per-context fetch budget is 1,024 requests/epoch. This is not an
unbounded service. Fixed configuration: v2, prepared reciprocals, scalar integer
add, radix-4 multiply disabled, two FP/divide lanes.

Standalone fetch synthesis reported 1,140 register bits and 4,243 generic cells;
that is not whole-core area, frequency or energy. No full-hash throughput,
physical memory capacity/service, calibrated PPA or 1 MH/s below 2,500 W result
is claimed. Two-state Verilator results do not supply v1/four-state regression.

## Reproduce against admitted external assets

The accepted source/review hashes, native input/cache identity, exact HDL closure
and tool bindings are in `fixtures/provenance.json`. `native-pins.json` binds the
external canonical native-reference files by name, length and SHA256. Bulk SP,
dataset/cache images, binaries and raw logs are deliberately not in this PR.
Original accepted/failing evidence remains local under the experiment IDs and
review hashes, with concise public milestones on issue #72.

A fresh clone alone is insufficient: supply those exact native-reference assets
and the pinned Verilator commit `5c5314b39cd888f427807d626e1502cbf222c292` (including
its 56 pinned runtime-source files), plus an existing C++20 compiler and make.
Do not substitute arbitrary native fixtures or another simulator version. The
repo's existing `scripts/hardfloat_compile_view.py` creates the exact temporary
compile view without editing vendor bytes. Runtime objects are rebuilt from
source; no private object blobs are needed.

From the repository root, with `NATIVE_DIR` and a fresh `OUT` supplied:

```sh
python3 experiments/shared_context_vm/tools/prepare_kernel.py \
  --native-dir "$NATIVE_DIR" --output "$OUT/kernel"
python3 experiments/shared_context_vm/tools/prepare_iterations.py \
  --native-dir "$NATIVE_DIR" --output "$OUT/iterations"
python3 experiments/shared_context_vm/tools/test_shared_vm.py
python3 experiments/shared_context_vm/tools/run_shared_vm.py --suite fetch18 --list-cases
```

The generators reproduce the accepted small headers/tables/event slices exactly
and reject missing or changed native inputs. Their JSON provenance uses relative
names. No native full hash or old experiment is replayed.

The Linux runner requires a previously approved host exclusion lock and its
device/inode identity, six allowed CPUs 0–5, an owned `codex-openrx-*.scope` and
actual cgroup-v2 leaf/ancestor limits. It refuses an uncapped caller. It retains
the reviewed 600% CPU / 1 GiB RAM / 2 GiB swap / 256-task limits, 512 MiB process
address space, 60 s process CPU, 115 s outer wall and 5 s cleanup envelope,
4 MiB file and complete suite-output caps, and first-failure stop. It never
creates an exclusion lock, installs dependencies or changes system settings.

For example, run this payload in an already approved resource-only user scope
with those properties, `taskset -c 0-5`, and a clean environment containing only
the account's `HOME`, `PATH=/usr/bin:/bin`, `LC_ALL=C`, `LANG=C` and
`XDG_RUNTIME_DIR=/run/user/<uid>`:

```sh
python3 experiments/shared_context_vm/tools/run_shared_vm.py \
  --suite iterations20 --fixtures "$OUT/iterations" --native-dir "$NATIVE_DIR" \
  --verilator-root "$VERILATOR_ROOT" --output "$OUT/iterations20-run" \
  --lock "$APPROVED_LOCK" --lock-identity "$LOCK_MAJOR" "$LOCK_MINOR" "$LOCK_INODE" \
  --unit "$OWNED_SCOPE" build
```

Then use a fresh owned scope and replace `build` with `case 1 1 1 0 0 0`.
Each suite's `--list-cases` supplies its closed matrix: 5 contexts16 cases,
10 fetch18 cases and 6 iterations20 cases. Use separate build/output directories
for all three same-named tops. Never overwrite prior output or automatically
retry a failure. Logs and generated C++ are retained outside Git; complete
component captures are losslessly compressed. Exit success remains pending
independent scientific review and does not expand the accepted scope.
