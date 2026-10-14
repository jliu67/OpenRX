# Immutable program reciprocal candidate — task #69

## Restored integration gate — 2026-10-14

The source-only CI route at historical head `1345db6d6abaf9d6a372b37325ec946eb870f56a`
skipped inherited program-sequence integration. This successor removes that route.
The existing `integer-differential` job now unconditionally installs official HDL
tools and executes `scripts/test_program_sequence.py --synthesize`; binding and
rejection checks remain additional guards. The companion job describes only its
own source/evidence checks. The declaration changes reason prose only: all old/new
digests, schema fields and 219 original science inputs retain their bytes.

The fresh authorized server regression passes nine RTL modes, nine mapped modes,
four rejected invalid parameter sets and three actual synthesis targets. All nine
mapped PASS records equal their RTL counterparts. It uses the unchanged eight-program,
four-iteration native v1/v2 profiles, plus resets/cancellation and default8×2048
control contract. Actual default whole-top gates cover one native v2 iteration
and cancellation. No full8×2048 native or gate rerun is claimed; `--full-v2` was
not requested. Dataset fixtures and software generation/interprogram hashing
remain boundaries, and full-pipeline performance remains unaccepted.

[Terminal receipt](program-sequence-regression/terminal-pass01.json),
[raw summary](program-sequence-regression/summary.json),
[commands](program-sequence-regression/commands.json),
[truthful parent bindings](program-sequence-regression/preserved-inputs.json),
[effective kernel receipt](program-sequence-regression/resource01.json),
[source retention](program-sequence-regression/regression-source01.json) and
[complete output retention](program-sequence-regression/complete-output-retention.json) retain actual
execution separately from the earlier prepared-cache suite. Every source/driver
input and generated HardFloat view/native extraction is checked after execution;
full output manifest/TAR inventories, bytes and original modes are verified.
Three mappings contain only generic cells, with exact stat/JSON accounting.
Resource peaks, swap and pressure counters are measured in the kernel receipt. The complete119,156,140-byte output archive exceeds [GitHub’s100MiB file limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github), so its complete verified bytes and readonly output tree remain on the authorized server, with full inventory/checksum receipt published. No archive is discarded or split. Actual kernel peak was7,516,192,768bytes RAM and1,597,886,464bytes swap; memory.max pressure events2117, OOM/kill and CPU throttling0. Wall runtime52min41.878s, one serial worker, all6CPUs available/600%,7GiB RAM/2GiB swap/Tasks128, fresh1GiB OS reserve and global nonblocking lock.
The original source-only ZIPs/checks/workflow/declaration and all previous failed,
skipped and successful sources/archives remain preserved. Independent exact-head
review is required before acceptance; no merge is authorized.


This candidate computes each active `IMUL_RCP` constant once when admitting an
immutable program image, then uses the existing unsigned low64 multiplier at
each retirement. The unchanged RandomX source pin is
`aaafe71322df6602c21a5c72937ac284724ae561`.
[Task #69](https://github.com/jliu67/OpenRX/issues/69) owns this bounded change.
Independent exact-head review is required before acceptance.

## Interface and lifetime

`randomx_program_reciprocals` loads all 384 v2 or 256 v1 instructions into a common
384×64-bit image. Prepared mode adds384×64-bit constants and reuses the existing
native reciprocal unit. Raw immediate bits are unsigned 32-bit. Zero and every power
of two remain lexical NOPs, with zero stored value; non-RCP metadata is zero.
Every accepted admission reloads and recomputes, even at the same address or
with identical bytes. Repeated iterations reuse only that completed image.

Load tags are `{epoch16, pc9}`. Matching replies are accepted after the matching
request; stale replies, including error flags, are drained. Image validity is
published only after the full program and its constants are stored. Fetches
return a synchronous held packet carrying epoch, PC, instruction and metadata.
Invalid generations/PCs return held error packets with zero data. Reset or whole
cancel invalidates the image and replies without resetting the physical arrays;
a full refill precedes reuse. Callers must not reuse generations while old
replies can arrive. The 16-bit epoch is a lifetime token, not a content hash.

`randomx_prepared_rcp_guard` checks epoch/PC/error and the raw instruction's kind,
divisor and NOP classification before the executor proceeds. It does not
recompute an arbitrary corrupted active constant. Correct values come from the
private loader and its separately native-tested reciprocal arithmetic. This is
not an integrity mechanism for an untrusted external metadata provider.

The executor's default `PREPARED_RCP=0` retains runtime computation. Prepared
mode routes active RCP through the existing multiplier. Other integer/floating
instructions, rounding, branch history, no-op semantics and memory operations
retain their original paths. Parameters outside 0/1 are rejected. The legacy
`INTEGER_EXECUTE_NETLIST` ABI cannot carry prepared metadata and rejects mode 1;
there is no mapped prepared-backend claim.

`randomx_prepared_integer_iteration` owns one completed image through execution
and held result/error consumption. Epoch, version and base must match an
accepted descriptor. Mismatch produces a held local error without launching the
iteration. Replacement is blocked while owned. `exec_cancel` releases execution
and held fetch data while retaining the image; whole `cancel` and reset invalidate
the image. Cancellation does not undo external stores already committed.
Iteration transport tags retain their existing nonreuse contract. Narrower
legacy program fabrics need an explicit load-tag/reservation adapter.

## Native and RTL validation

The serialized server command is:

```sh
python3 scripts/test_prepared_reciprocals.py --output /tmp/openrx-prepared-reciprocal-validation-UNIQUE --synthesize
```

Use a fresh output outside source, an authorized server payload, fresh effective
kernel/resource checks and the global nonblocking execution lock. No tools are
installed by the driver. It retains commands, tool executable hashes, full
stdout/stderr, `/usr/bin/time`, failures, input/fixture hashes, synthesized
netlists/statistics and a complete final artifact manifest. Native source,
HardFloat and secworks originals are verified before compilation.

The corpus has 12 admissions and 48 native iterations, split equally between v2
and v1. A,A,B,C,D,A per version tests identical reload and same-address replacement.
It covers all 33 zero/power-of-two divisors across all 8 RCP opcode encodings,
512 active encoding/register-alias tuples per version, unsigned bit31 edge
immediates, low64 wraparound, mixed native instructions and NOP/branch replay.
Every retirement, memory event, dataset address/feedback, AES/store tail,
round/control state and 12 final full 2 MiB scratchpads is compared to native.
Golden constants are assertion-only; the DUT receives raw program words.

Primitive tests exercise load/fetch/result stalls, stale generations and PC tags,
invalid fetch/load errors, v2→v1 replacement, reset/cancel during preparation and
held results, guard packet rejection and malformed metadata in the real core.
Integration controls check descriptor errors, active/held ownership and reset,
execution cancellation and whole cancellation separately from the native cost
window. Default-mode transport regressions protect the existing ABI. Actual
default baseline/prepared cache and guard mapping is validated on the same
primitive vectors; complete prepared-core mapping and physical PPA are skipped.

## Measured clock accounting and acceptance boundary

Paired modes share identical immutable instruction storage, fetch latency,
native corpus and event-ordinal memory profiles. Balanced configuration order is
baseline ideal, prepared stalled, prepared ideal, baseline stalled. Each mode
emits disjoint preparation/execution/controller phases and per-admission clocks.
FSM occupancy and memory/fetch/AES waits are nested observers; do not add them
again. Control-only tests and fixture overhead are separately reported, and the
whole elapsed ledger must close.

`scripts/reciprocal_cycle_model.py` calibrates reciprocal cost from actual request
and wait occupancies in both modes/profiles. It verifies every preparation is
charged, all common phases/workloads match, runtime computation is absent in
prepared mode, and paired preparation+execution delta equals calibrated cost
times(dynamic active RCPs−static active RCPs). Negative savings remain negative.
No extrapolation from four iterations to 2048 is presented as measured.

The [surrounding stage ledger](surrounding-stages.json) binds preserved draft
PR #65 register-file/interprogram hash and PR #68 full scratchpad finalization
measurements. Their different fixture boundaries/providers cannot be summed
into a measured hash. Initial input hash, scratchpad AES fill, program generation,
actual complete dataset, calibrated memory, connected 8×2048 execution and
interprogram/final hash, intended-core timing and physical PPA remain missing.
Full-hash clocks/speedup remain null. All resulting performance evidence is
iteration-stage candidate evidence until complete-pipeline acceptance is met.

Subsequent architectural work requires that baseline first, then measured
1/2/4/8/16-context single-issue blocking/nonblocking comparisons, dependency-proven
overlap and justified dual/wider issue. None is implemented by this task.

## Verified server result — 2026-10-14

The complete successor passes eight Python accounting guards, 48 native iterations
in 12 admissions, 11 RTL checks, four mapped checks and three intentional invalid
parameter/ABI elaboration checks. Each integration profile compares 15,424 native
retirements, 1,744 bytecode memory events, 384 tail stores and all 12 final 2 MiB
scratchpads. The four mapped PASS records equal their RTL counterparts exactly.
There are zero unexpected failures in this final run and one declared skipped
complete-pipeline performance gate. Full prepared-backend mapping, physical
memory/timing/power and full-hash performance remain unexecuted boundaries.
Four earlier failed attempts are retained below; their partial mappings/results
are not accepted. Only testbench sampling/order and synthesis-driver/provenance
corrections separate them; the new DUT arithmetic is unchanged across attempts.

Measured preparation plus execution clocks on this **directed native corpus**:

| Profile | Baseline clocks | Prepared clocks | Added preparation | Saved execution | Net saved |
| --- | ---: | ---: | ---: | ---: | ---: |
| ideal | 370,444 | 159,376 | 70,356 | 281,424 | 211,068 |
| stalled | 398,580 | 187,512 | 70,356 | 281,424 | 211,068 |


Actual unit occupancy is one request clock plus 65 wait clocks per active RCP in
both memory profiles. All 1,066 static active RCPs are charged at admission;
baseline executes 4,264 active RCP requests, prepared mode executes zero runtime
requests. Non-RCP phases and all common work match. Costs include program reads,
fetches, entry conversion, memory/dataset waits and AES/store completion. Separate
control and fixture overhead remain reported in the closing whole-elapsed ledger.
This corpus is for correctness and stage calibration; no representative full-hash
speedup or extrapolated 2,048-iteration measurement is claimed.

| Actual default mapped target | Generic cells | Flops | Latches |
| --- | ---: | ---: | ---: |
| cache-0 | 75,979 | 24,877 | 0 |
| cache-1 | 152,277 | 49,640 | 0 |
| guard | 390 | 0 | 0 |


Installed Yosys 0.9 (`1979e0b`) performs real default cache/store and guard mapping
with no unmapped cells. Maximum instruction storage is 384×64 bits (3 KiB) in both
modes; prepared mode adds 384×64-bit constants (3 KiB). The generic mapping uses
flip-flops/muxes, not a physical SRAM macro or complete prepared-core area model.
Icarus 11.0, GCC 11.4 and Python 3.10.12 tool hashes/version streams are retained.
All 171 RandomX originals, 12 HardFloat originals, three secworks originals and the
generated Icarus compatibility view/receipt pass their unchanged-byte guards.

One serial worker had all six affinity CPUs and actual CPU quota 600000/100000,
RAM 4 GiB, swap 512 MiB and Tasks128, with no tighter visible ancestor ceilings,
fresh OS reserve and inherited nonblocking global lock. Measured cgroup peak is
1,276,846,080 bytes; swap peak is 0 bytes and
memory max/OOM/kill events and CPU throttling are zero. Aggregate CPU use is
5203.765 seconds; wall duration is recorded in commands and the service receipt.
Six CPUs were available; individual tools/simulations ran serially. The compute
slot is released after the payload; publication preservation also holds that lock.

[Summary](server/summary.json), [per-admission model](server/cycle-model.json),
[command journal](server/commands.json), [tool identities](server/tools.json),
[actual kernel receipt](server/resource05.json), [complete output archive](server/complete-output.tar.gz)
and [complete artifact manifest](server/artifacts.sha256.json) retain exact evidence.
[Source retention](server/source-attempt05.json) binds all 2,548 frozen source files
and the full local source archive, which remains retained outside Git. Published
executed input bytes equal [published-head bindings](server/published-head-inputs.json);
publication adds only evidence/prose/memory, without an executed-code correction.

Failed attempts: [01 syntax](failed-attempt-01/attempt01-failure.json),
[02 retirement observer](failed-attempt-02/attempt02-failure.json),
[03 reset sampling](failed-attempt-03/attempt03-failure.json),
[04 rejected partial mapping](failed-attempt-04/attempt04-failure.json). Each folder
retains complete outputs, source bindings, resource receipt and executed changed
harness files. Independent exact-head review remains required. The hosted source-binding failure and its bounded CI successor are recorded below.


## Hosted source-binding correction

Draft PR #70 originally published at `3ce88a6104ee79894da823cfff28280fc5b5cd75`.
[Run 38502375710](https://github.com/jliu67/OpenRX/actions/runs/38502375710)
stopped before native compilation at the inherited 53-path accepted compatibility
manifest: the optional executor and iteration extensions intentionally have new
bytes. The original accepted manifest remains unchanged. The complete failed job,
original four-file artifact ZIP and its digest/inventory are preserved in
[failed hosted evidence](failed-hosted-binding-01/artifacts.sha256.json).
Foundation, RISC-V preflight and prepared model checks passed on that original head.

The [explicit successor declaration](parent-source-bindings.json) binds exactly
those two intended paths to both the old accepted digests and the unchanged
[219 server input bindings](server/inputs.json). Every other accepted path retains
its original digest. Default `PREPARED_RCP=0` and optional prepared mode are checked.
No RTL, native oracle, golden, workload, server result or accepted manifest changes
in this successor. All 219 executed source bindings remain byte-for-byte identical.
New CI/helper/test changes are validated separately from the scientific payload.

At historical head1345, candidate hosted checks validated source bindings, rejection tests and retained
server evidence. Their successful status means those bounded checks pass.
The inherited full native program-sequence/synthesis replay is **deferred and
unexecuted** at that historical head, superseded by the actual regression above; reproduction still requires fresh authorized serialized server
admission. Noncandidate workflow behavior remains unchanged. Source guards and
retained result validation do not establish full-hash or independent acceptance.
[Correction scope](ci-successor/scope.json) records the distinction. Independent
review must cover the final exact head, including this CI correction.


The bounded successor payload passes one source/evidence guard, all 12 parent
rejection tests and the eight unchanged accounting tests with zero unexpected
failures. [Check summary](ci-successor/summary.json), [command journal](ci-successor/commands.json),
[full service log](ci-successor/complete-service.log), [actual kernel receipt](ci-successor/resource.json)
and [complete check output](ci-successor/complete-output.tar.gz) retain results
separately from the scientific server evidence. One serial worker used all six
affinity CPUs/600% quota, 1 GiB RAM/128 MiB swap/Tasks64, fresh 1 GiB OS reserve,
no tighter ancestors and the nonblocking global lock. Kernel peak was 21,762,048
bytes, swap and limit/OOM/kill/throttle events zero; service wall time was 837 ms.
The lower RAM budget reflects small metadata inputs and measured Python peak.
The frozen complete check source/archive is [retained](ci-successor/source-retention.json);
all six new CI input hashes match the published successor. Compute slot released.
