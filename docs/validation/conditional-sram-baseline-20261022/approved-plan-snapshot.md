# Proposed issue72 execution request — conditional SRAM baseline

PREPARED ONLY. Not posted, claimed, submitted, built or executed. This file is a proposed public plan for separate approval, not an authorization or a scientific result.

Destination: existing https://github.com/jliu67/OpenRX/issues/72 . Proposed session codex/20261022-conditional-sram01 and new request key issue72-conditional-sram-baseline-20261022-01. Before any submission, obtain specific approval for public coordination/request publication and this bounded payload; check for intervening publication/execution, overlapping work, current task dependencies/claim, fresh source/tool/input pins, LOCAL_ACTIVE, global lock and resource headroom. Current issue72 review status may require an approved reopen/claim transition. Do not post any such command under preparation-only permission.

## One falsifiable question

For a fixed hypothetical CACTI6.5 UCA RAM at the retained 2010 ITRS45nm HP projection, nominal model1.0V and360K, does four-bank instead of one-bank organization reduce the optimistic one-outstanding-fetch service interval? Report read energy, area and correctly scoped leakage alongside timing. Four banks may improve, worsen or trade these quantities; a win is not an acceptance requirement.

Both organizations have128KiB total capacity,4096 logical32-byte words,256-bit output, one read/write port per bank, no additional ports and one global outstanding credit. Each word holds instruction64 + reciprocal-valid1 + index32 + reciprocal-value64 =161 content bits, plus95 explicit padding bits. The29 echo/status bits and65 client/owner tag bits remain transient outside this array. Raw expanded content requires82432B before padding, so no64KiB complete-record claim is made. The239-entry unique reciprocal table is retained preparation, not239 transactions or another per-fetch read on this declared denormalized path. Loading/denormalizing the image and autonomous setup remain outside this experiment.

Use pureRAM, no cache tags, ECC disabled, fixedGlobal wires, semi-global inside/outside mats and conservative interconnect projection. Force partition Ndwl2/Ndbl2/Nspd1/Ndcm1/Ndsam1=2/Ndsam2=1, UCA and NTHREADS=1. The logical4096 words are not a characterized4096x256 SRAM macro. Static subarray guards give2048 versus512 rows and128 columns, but actual valid evaluation is unrun. Preserve source wording 'Best' in raw output while describing these as forced candidates, not proven optima. Keep Printinput=false: this retained infile path prints its input identity once unconditionally; enabling the flag duplicates it.

## Placement and unknowns

Only the prepared-fetch SRAM is evaluated. The256MiB prepared cache is provisionally an external-memory address partition. The accepted hardware dataset path recomputes items from that cache; no materialized2GiB dataset placement is assumed. Each VM scratchpad is2MiB, outside this comparison with physical banking/ports unresolved.

The retained gem5 DDR4_2400_8x8 class is a static annotation only, with no gem5/DRAM simulation:8GiB/rank,16GiB/channel, nominal64-byte burst and datasheet-derived timings. That is not a selected module, allocated cache size, random-service guarantee or end-to-end transaction model. Its7.8us refresh annotation applies at<=85C; DRAM temperature is unmodeled and is not coupled to the separate360K SRAM assumption. Bank-group approximations, controller scheduling, conflicts, queues, refresh/tails, PHY/I/O/termination and controller energy remain unresolved.

CACTI's ITRS projection is not a foundry PVT corner or characterized SRAM/cell library. Physical frequency, area, service supply, complete latency, controller/PHY power, whole-machine wall power, achieved hashes/s, engine count and alternative full-hash timing remain unknown. No RTL, two-VM or scratchpad correctness follows.

## Exact source and tool bindings

Frozen candidate SOURCE-MANIFEST01.json SHA256505b787884969c0312910fcc989f84b4eb5a2c54a04146d35445b9e707b0fee4 binds57 files/1016790B; its own file is separately bound in admission. Contract SHA256087a18367ddd65bf930e2030070995f0d8e8e2e1adb246d2284be724e7583346.

- Adapter:1efe3b615e034a46dde561b2d80963faf810028b2a4073fcb8046b3f1617b79d.
-16 expected unit methods, all UNRUN: test source9085322af7246fa23dc324abb06547bff1bc4ad31968033cf0808f84dddf8335.
- Driver:219ea2ff8b4b50e0d0b618f90ca446fad240894afea562082421af53afd9c4a9.
- Bank1 config:a1281741b5a4dea674555d64369a95868a4f0f3c47ab9d813ad6a7317350a908; bank4:abf91a0f813747c5fa5ac3bcce4a9fb82bda62d5459b93a90ed2b3a1eb68d7eb.6045B each; only active bank count differs.
- Accepted PR87 report:694b153e2220218c95c84579dfba930707abb439fa1cadce4d42195148f7c42a; PR91 report:d6baa3de036273b1ac3918ffb5c3418b98f0130acdb43652380c06648eea81ce.

All52 model/data/config inputs are copied byte-exact from retained files or declared new configurations. CACTI and DRAM sources carry original copyright/license notices. The gem5 revision label is c8222cc67a399bfc01e8658dd14b30d5bfd634f9; this preparation did not recompare the entire upstream tree, so current copied-file SHA256 bindings are authoritative. Preserve that provenance limit.

Tool-bindings.json pins actual Python3.10, GNUtime, make, GCC/G++, assembler and linker bytes/resolved paths plus installed package metadata. This is not complete hermetic header/shared-library closure. The installed immutable runner is runner-v1-657b23f1, SHA256657b23f16aabbadb534c108ba3d233e7922db70d01dbb5cf7073d594b0e4292b; reverify it before submission. No installation or download is included.

## Five sequential timed commands

Let S be the frozen candidate directory and R the new execution's results directory. These are literal driver argv templates; all working directories must be new as specified.

1. cwdS: `/usr/bin/python3.10 -B -m unittest discover -s tests -p test_memory_baseline.py -v`. Expected16 methods; actual tests remain unrun. Synthetic numeric fixtures test parser/accounting behavior only and are never model evidence. No CACTI/gem5/native/RTL process is launched by these tests.
2. Copy S/inputs/cacti to new R/build/cacti, preserving every original source byte. In that build copy run `/usr/bin/make -j1 NTHREADS=1 CXX=/usr/bin/g++ CC=/usr/bin/gcc 'CXXFLAGS=-O3 -std=gnu++98 -msse2 -mfpmath=sse -DNTHREADS=1 -Wno-unknown-pragmas'`. This overrides historical-m32 without editing source. It compiles20 C++ translation units with one compute pthread plus main. Actual build compatibility/runtime/RSS are unmeasured; GNU/glibc log2 and development/runtime dependencies remain build gates.
3. In new R/cases/bank1, copy frozen bank1.cfg as input.cfg and run `R/build/cacti/cacti -infile R/cases/bank1/input.cfg`.
4. In separate new R/cases/bank4, copy frozen bank4.cfg as input.cfg and run `R/build/cacti/cacti -infile R/cases/bank4/input.cfg`.
5. cwdS: `/usr/bin/python3.10 -B adapter/memory_baseline.py --contract S/contract.json --inputs S/inputs --cases R/cases --output R/conditional-report`.

Strict output parsing after each model is bounded driver bookkeeping, not another model run. CACTI can exit0 on errors and appends out.csv, so require new directories, one exact CSV header/data row,31 input-identity guards, matching forced partition, no diagnostics, unchanged generated binary SHA, finite correctly signed metrics, stdout/CSV agreement and height*width versus organization-area consistency. Invalid bank1 stops bank4 and the final report. Record skipped later commands as unrun, never passed. The driver does not repair, retry, expand search or increase limits.

## Bounds, retention and admission

One worker and one global payload slot; CPU600%, RAM1073741824B(1GiB), swap2147483648B(2GiB), Tasks256. Each command gets120 seconds plus5 seconds supervisory shutdown grace, then kill/reap on timeout. Five commands allow at most600 seconds active timeout budget and25 seconds grace, plus staging/finalization/bookkeeping; actual duration is unmeasured and no fixed end-to-end deadline is promised. Retain the installed runner's kernel/ancestor/headroom checks and bind the whole frozen source, manifest, driver, tools and current approved public request/claim receipts. Use kind=simulation with no validation-scope, because this bundle includes a build and two analytical-model evaluations. Explicit memory budget is mandatory. Never submit before fresh matching approval/admission.

Retain full stdout/stderr/time/status for all commands, raw per-case CSVs, generated binary and hash, writable build/source copy, actual configuration echoes, source/tool before/after checks, report/provenance/index, raw runner request/manifest/result/receipt and independent review. Verify original/frozen sources independently after any failure or interruption, including cases where hard termination bypasses driver finally checks. Preserve all old and new failed attempts. Do not modify raw scientific flags. Publish only approved sanitized scientific evidence after independent review; never private journals.

## Result meaning

For each valid case, T=max(access_ns,cycle_ns), optimistic single-credit requests/s=1e9/T and local rowB/s=requests/s*32. Protocol, response assembly and held-reply overheads are explicitly zero for this upper bound. The actual channel holds its only credit until reply consumption and forbids same-edge refill. Do not multiply supply by bank count or infer four outstanding requests.

The accepted full hash has58376192 fetch requests/hash. The declared32B-row mapping therefore requires1868038144 local rowB/hash. At the1MH/s objective these are58376192000000 requests/s and1868038144000000 local rowB/s: necessary aggregate demand only, not measured off-chip traffic, projected achieved throughput or a selected engine count. Do not apply the bounded PR91 descriptor width as a historical full-hash wire measurement. Preserve per-bank leakage scope; complete-organization area is a different quantity. Do not turn read energy or leakage into whole-machine wall power.

Correct byte/source-bound comparison can be accepted as CONDITIONAL MODEL COMPARISON ONLY, whether bank4 wins, loses or trades metrics. Build/parser/model failures are not passes. Broader issue72 and all physical/performance/scientific gates remain open. No full hash, native/cache generation, RTL/synthesis/mapped simulation, gem5 workload, historical campaign, new hardware/library installation, download, spending, deployment, settings/access/security change, standing clone or Git sync is included.
