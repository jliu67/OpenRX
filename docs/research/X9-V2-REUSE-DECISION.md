# X9/v2 target envelope and AES reuse decision

[Task #41](https://github.com/jliu67/OpenRX/issues/41), source-only inspection on
2026-10-12 UTC; OpenRX base `fb5c37fa4529ad360b68bee046eb78e94d9a74ef`.
This is a bounded planning record pending independent review. It supplies no
new execution, selected-core acceptance, calibrated timing or competitive PPA.

**Decision:** retain the unchanged scalar RISC-V/software-AES backend as the
functional reference for the provisional BOOMV3 assessment. A future AES reuse
proposal must serve the VM's raw register-bit round transformations as well as
scratchpad setup; hardware crypto capability alone does not redirect that backend.
Resolve whether such a proposal is warranted from the profiling and exact-core
prerequisites below. No final core, AES IP block or hardware interface is selected.

## Traceable X9 comparison envelope

The [first-party product entry][P] is available as a search-indexed excerpt;
direct product retrieval returns a JavaScript application shell. The [BITMAIN
announcement][N] likewise has an indexed RandomX/XMR description but no readable
article body in direct retrieval. This limited retrieval establishes advertised
machine claims, not a tested unit or current sale/shipment/cancellation status.

| Dimension | Traceable claim / boundary | What remains unknown |
|---|---|---|
| Workload | Product/announcement market RandomX for XMR. [product][P], [announcement][N] | No exact v2 revision, flags, firmware or independently checked hashes in the retrieved material. |
| Machine throughput | Indexed product lists 1,000 kH/s. [product][P] | Sustained measured v2 throughput, duration/thermal conditions and chip/core contributions. |
| Power | Indexed product lists 2,472 W at the wall at 25 °C. [product][P] | Independently measured power and conversion/cooling accounting for an exact v2 run. |
| Ratio | 2,472 W / 1,000 kH/s = **2.472 J/kH**, arithmetic on advertised values; the entry rounds its efficiency label to 2.47. [product][P] | A measured v2 efficiency result or an ASIC power/area budget. |
| Silicon and implementation | Not established by this bounded first-party read. | Chip identity/count, core topology, proprietary RTL, internal AES/memory design and competitive chip/core PPA. |

Use these machine-level advertisements only as a comparison envelope. BOOM is
provisional open IP, not identified X9 silicon; generic gem5 Atomic/O3 is not a
calibrated BOOM model. Independent exact-workload, sustained whole-system
measurement would be needed to make a v2 comparison. No per-core scaling is inferred.

## Reuse, gaps and required evidence

Reuse the existing [core-source ledger](../../simulator/CORE-FEASIBILITY.md),
[EXP-002 controls](../../experiments/EXP-002-riscv-functional-preflight.md),
[accepted native infrastructure](../validation/native-staging-20261012/README.md)
and preserved simulator builds. Their separate scientific limits still apply.

| Contract | Existing source / reuse | Gap or unknown to resolve |
|---|---|---|
| ISA and JIT/runtime | Pinned RV64 backend emits scalar integer/FP/compressed code; v2 selects its software-AES suffix. [scalar JIT][RV] Linux signals, mappings/protection and instruction-cache controls already exist in EXP-002. | Exact selected BOOM configuration, unsupported-instruction dispatch, generated-code overwrite/flush, intended-core/SMP behavior and unchanged full-dataset v1/v2 hashes remain acceptance work. Dormant vector/crypto objects do not prove runtime support. |
| FP and rounding | MediumBoomV3 enables divide/sqrt; shared Rocket FPU defaults to binary64. BOOM FP/divide paths wire dynamic CSR rounding. [Medium config][B], [FP][F], [divide/sqrt][D], [shared FPU][RF] | Reuse Rocket/HardFloat, retaining exact four-mode, divide/sqrt and CSR-ordering tests. Source wiring does not prove bit-exact execution; AES transport must preserve raw FP-register bits without numeric conversion. |
| v2 main-loop AES | Interpreter mixes four 128-bit F values with four E-derived round keys: eight encrypt and eight decrypt rounds each iteration. [interpreter][VM] Scalar RV64 JIT makes matching software round calls. [scalar suffix][RS] The existing RISC-V bulk AES helpers use vector `Zvkned`. [AES helpers][AH] | BOOMV3 sets `useVector=false`. [parameters][BP] Unchanged scalar JIT has no automatic scalar-crypto/AES-accelerator dispatch. A reusable round primitive needs a separately reviewed backend and register/latency integration; an initializer-only engine leaves the VM-loop requirement unresolved. |
| Scratchpad/dataset/memory | Pins retain 2 MiB per-VM scratchpad, 256 MiB cache, 2,181,038,016-byte full dataset, 384 v2 program slots and two-iteration dataset prefetch semantics. [constants][C], [interpreter][VM] Reuse existing SoC memory framework and preserved full-system tools. | Stock Chipyard/BOOM parent defaults to 256 MiB external memory. [memory default][M] Guest, backing, address decode/cacheability and device tree must agree with unchanged full-memory allocations; source capacity overlays are not executed proof or a timing model. |
| Licenses/provenance | Retain pinned RandomX's BSD notices, BOOM's BSD root and applicable Apache notices, and Rocket/HardFloat dependencies. [RandomX notices][L], [BOOM BSD][BL], [Apache terms][BA], [core ledger](../../simulator/CORE-FEASIBILITY.md#license-feasibility) | Before later reuse/distribution, inventory applicable file/submodule notices, exact generated dependency set and tool/source bindings. No top-level license relabels all IP; no proprietary X9 RTL access or binary reproducibility is assumed. |

The AES count above is a fixed source operation count, not measured cycles,
bottleneck attribution or a speedup prediction. The pinned scalar suffix moves
64-bit FP-register halves into integer registers, calls the round helpers and
stores/reinstates the resulting bits. Its data movement is part of any future
reuse cost. AES only in scratchpad initialization would not satisfy v2 semantics.

## One next bounded decision

**Whether to scope a reviewed VM-loop AES-round backend reuse proposal.** Hold
that proposal until controlled #8/#11 evidence separates VM-loop software AES,
scratchpad fill/hash, JIT/setup and memory/FP costs with actual dispatch recorded.
Use exact workload/flags, declared interval/host configuration, balanced v1/v2
repetitions and uncertainty under the existing protocol; a native hardware-AES
rate cannot be transplanted into BOOM. Include #10's physical power prerequisites
for energy claims. A fixed AES count alone does not decide priority.

Before choosing an implementation, #3 must establish the exact selected-core
Linux/runtime, integer/FP/rounding, AES bit transport and unchanged light/full
v1/v2 controls; task #16 is separate and is not duplicated here. A candidate
round primitive/backend must match independent encrypt/decrypt-round references,
word/byte order, FP/integer bit moves and complete hashes. Account for data-transfer
cost and latency overlap in the declared calibrated #14 model before #12 RTL
optimization. This task authorizes none of those executions or changes.

Stop this assessment here: source evidence identifies an integration/dispatch
gap and a concrete evidence prerequisite, without disqualifying BOOM or opening
a broader core/IP survey. [Current roadmap](../ROADMAP.md#current-priority-path--2026-10-12)
and all #16/#8/#10/#11/#3/#14/#12 gates remain intact.

## Versions and inspection record

RandomX v2.0.1: `aaafe71322df6602c21a5c72937ac284724ae561` (v2 primary, v1 regression).
Chipyard 1.14.0: `0acc1e1de2d3284bcd4d876956932a013ffe1949` / `MediumBoomV3Config`;
its inspected gitlinks bind BOOM `5223e44cfeb26f41380057a2eb4d651197475f69`, Rocket
`55bcad0f59436de98ea510334121de8546b9e9d7` and HardFloat
`0ecaef097ce2accbd16a61613699450ed5533f29`. Selected files, configuration/rounding
wiring, gitlinks, unchanged source constants and the 8+8 scalar round calls were
read; licenses and existing acceptance reports were reused. Full dependency
closure, elaboration, boot, profiles and component RTL acceptance were not run.

Representative read-only commands (actual source versions above):

```text
gh api repos/jliu67/OpenRX/contents/vendor/randomx/src/vm_interpreted.cpp?ref=fb5c37fa4529ad360b68bee046eb78e94d9a74ef
gh api repos/ucb-bar/chipyard/contents/generators/boom?ref=0acc1e1de2d3284bcd4d876956932a013ffe1949
gh api repos/riscv-boom/riscv-boom/contents/src/main/scala/v3/common/parameters.scala?ref=5223e44cfeb26f41380057a2eb4d651197475f69
```

Primary search queried the exact X9 product and announcement with `1000`, `2472`
and wall-power terms. Direct retrieval exposed shells; indexed fields are
qualified above. An initial HardFloat lookup used the wrong directory name and
returned 404; `.gitmodules` identified `generators/hardfloat`, whose exact gitlink
was then verified. No local tests/builds/simulations, downloads of large resources,
installations, code/vendor edits or scientific workloads were performed.
Applicable PR checks and a different-agent exact-head review are required; green
CI will not upgrade these source-only findings into measured performance.
The task issue carries the bounded persistent state/session/review handoff.

[P]: https://m.bitmain.com/zh/product/detail?pid=00020251226185131923DUjfvPIO06BC
[N]: https://www.bitmain.com/news-detail/bitmain-launches-antminer-x9-430
[VM]: https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/src/vm_interpreted.cpp#L102-L125
[RV]: https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/src/jit_compiler_rv64.cpp#L505-L511
[RS]: https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/src/jit_compiler_rv64_static.S#L551-L641
[AH]: https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/src/aes_hash.cpp#L70-L78
[C]: https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/src/configuration.h#L50-L74
[B]: https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/common/config-mixins.scala#L131-L169
[BP]: https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/common/parameters.scala#L123
[F]: https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/exu/execution-units/fpu.scala#L185
[D]: https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/src/main/scala/v3/exu/execution-units/fdiv.scala#L127-L164
[RF]: https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/src/main/scala/tile/FPU.scala#L17-L26
[M]: https://github.com/chipsalliance/rocket-chip/blob/55bcad0f59436de98ea510334121de8546b9e9d7/src/main/scala/subsystem/Configs.scala#L268-L273
[L]: https://github.com/tevador/RandomX/blob/aaafe71322df6602c21a5c72937ac284724ae561/LICENSE
[BL]: https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/LICENSE
[BA]: https://github.com/riscv-boom/riscv-boom/blob/5223e44cfeb26f41380057a2eb4d651197475f69/LICENSE.SiFive
