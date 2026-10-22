# Prepared-fetch SRAM-port validation — 2026-10-22

Execution `20261022T213322Z-acbfc58fe1e4` completed the approved four-command
validation once. All36 Python test methods, the offline image/oracle comparison,
one Icarus compile and all 12 standalone scenarios passed, with no skips,
timeouts, fallback or retry. The result concerns one immutable image and one
behavioral synchronous port, not physical SRAM performance.

The [approved public plan](https://github.com/jliu67/OpenRX/issues/72#issuecomment-6351774332)
binds the exact frozen [source manifest](source/SOURCE-MANIFEST01.json), SHA256
`6a4f3bd1f58fd96573519e931e472abacdef9fcbec6e85bf82058c5c50eb694f`:
84 listed files/493,441 bytes plus manifest,85 physical source files. Base main is
`90b87f55220151a2bb43ed097c8d55e62a534e0b`, tree
`e7f91fe69109afae537b7905c7d75866afb63e9c`. The 71 copied inputs and 41 tool bindings
remained exact. All 85 source files are preserved byte-for-byte under `source/`,
including their dated pre-execution PREPARED/UNRUN labels. Those labels describe
the frozen preparation snapshot; current execution outcomes are recorded here.
In particular, `source/README.md` and `source/CONTRACT.md` are preserved
pre-execution source snapshots containing dated UNRUN/proposed wording. This
current summary supersedes their execution-status interpretation only, without
changing source bytes or scientific acceptance criteria.

## Question and result

The falsifiable question was whether an explicitly clocked immutable row port
could preserve complete row data, captured owner/full tag and address echo,
held replies and cancellation drain through the unchanged accepted channel,
while closing its controller-specific cadence and reset/occupied-clock ledgers.

The [standalone result](simulation.json) records 170,056 checks over 21,648 modeled
clocks. All3,563 active rows were queried through both clients,7126exhaustive
active-row queries in total. The complete directed experiment issued 7,199 requests:
7,167 active row reads, 32 bounds errors without memory reads and 3 cancelled replies
drained without client delivery. Accepted counts are [3,599, 3,600]; delivered
counts are [3,598, 3,598], so delivered 7,196 plus cancelled 3 equals all 7,199 responses.

Coverage includes sealed-image issue blocking, active rows and first/last padding
errors, captured-input replacement, held replies, queued/issued/held cancellation,
nonowner cancellation, opaque epoch echo, continuous two-client service and
quiescent reset retaining the image. Finite test tags never wrap or reuse.
The accepted session-generation/nonreuse contract is unchanged; this experiment
does not broaden its previously validated capacity.

Continuous traffic made 32 captures with 31 intervals spanning 93 modeled clocks,
exactly three clocks per interval. For this controller the sequence is capture E0,
registered row read E1, consume E2, next capture E3. Cumulative occupied clocks close
as 14,445 = 14,443 before the last reset + 2 after reset. Cumulative and post-reset domains
are emitted separately in `clock_ledger`, `last_reset_baseline` and
`post_reset_counters`; occupied clocks are nested within the 21,648 elapsed clocks,
not an extra term to add to them.
The elapsed domain reconstructs 21,648 = 14,445 occupied + 7,199 capture/idle + 4 reset clocks.
The 93 cadence-interval clocks are an observed nested window, not another addend.

This measured modeled cadence is implementation-specific. It leaves PR94's
necessary two-clock floor unchanged and establishes no physical clock period,
frequency, one/four-bank speedup or hashes-per-second result.

## Image and independent comparison

Only the retained cache0 prepared image from execution
`20261018T175827Z-447be94ead08` is admitted. Cases000/001 share the32program/
reciprocal arrays exactly. Program counts are [447, 438, 449, 447, 444, 449, 452, 437],
3,563 active rows and 533 zero padding rows. There are 239 prepared reciprocal entries
with global indices 0–238. This is no general image-capacity acceptance.

Logical storage is 4,096 × 256 bits = 128 KiB. Each row holds 161 payload bits and 95 zero
reserved bits: instruction 64, reciprocal 64, global index 32 andvalid 1. The
eight 10-bit counts and transport echo/error/tags/control remain outside that
capacity. Values are denormalized into instruction rows; no live reciprocal-table
lookup or separate reciprocal-row API exists.

The offline exporter checked both retained cases. The separately implemented
oracle reconstructed payloads from original fields by byte assembly, compared all
4096packed rows and counts, and emitted independent gold. The oracle does not
import exporter code; command2's wrapper imports both modules into one process,
so no process-isolation claim is made. See [oracle report](image/oracle.json),
[export report](image/export.json), exact [rows](image/rows.mem),
[counts](image/counts.mem) and [gold payloads](image/gold-payload.mem).
The oracle report preserves its stage-specific wording that RTL validation was
then separate/unrun; command4 and the later independent review record the actual
behavioral outcome without rewriting that earlier report.

The 36 actual Python methods comprise 24 exporter checks and 12 oracle mutation
checks. They reject malformed identities/counts/rows, reciprocal inconsistencies,
packing-field corruption, nonzero padding/reserved data and output reuse.
Actual test names and footer are retained in [the unit log](logs/units/stderr.txt).

## Runtime and resources

| Command | Outcome | Wall seconds | Peak RSS KiB |
| --- | --- | ---: | ---: |
| 36 Python methods | pass | 1.6725624359678477 | 19500 |
| Offline image plus oracle | pass | 0.16473297495394945 | 17056 |
| Icarus compile | pass | 0.03204533993266523 | 8956 |
| Standalone simulation | pass | 2.4272930389270186 | 8960 |

Sum of command wall times is 4.296633789781481 seconds. These are validation costs,
not RandomX throughput measurements. GNUtime reports CPU 93/99/105/100 percent and
zero swaps for the four sequential commands. Six CPUs were available under the
approved 600 percent quota; the dependent tools did not require six concurrent jobs.

Immutable runner657 verified one global worker slot and actual kernel limits
CPU 600000/100000, RAM 1,073,741,824 B, swap 2,147,483,648 B and Tasks 256, CPUs 0–5, no tighter
visible ancestors and fresh memory headroom. Each command had120seconds plus
5 seconds supervisory grace; the finite bench had a 100,000-clock watchdog.
All process groups drained. See [runtime resources](runtime-resources.json),
[sanitized summary](validation-summary.json) and full per-command
stdout/stderr/GNUtime/status records under `logs/`.
Whole-cgroup peak memory is unknown; the table reports per-command GNUtime RSS.
This successful run did not exercise timeout/failure cleanup branches. Their
static preparation review is not live timeout-recovery acceptance.

Public logs replace only bound absolute source/results/execution/preparation
prefixes with SOURCE/OUTPUT/EXECUTION/PREPARATION. [Provenance](provenance.json)
retains raw bytes/hashes and the transformation rule. Original logs, immutable
manifest/receipt and compiled bench remain locally preserved. Raw private
journals, runtime paths and account/approval transcripts are not exported.
The self-excluded [artifact index](artifact-index.json) binds all public evidence
and source files in this directory; component-copy hashes are in provenance.

## Review, retention and scientific limits

Separate AI [actual-result review](independent-result-review.json) accepted
`PASS_FUNCTIONAL_BEHAVIORAL_PORT_ONLY` at 21:37:39 UTC with no blockers. The reviewer
authored none of the candidate, reran no payload and independently checked the
34finalized artifacts and file/hash set, receipt/event chains, source/tool/original
bindings, every packed/gold row, actual test/scenario sets and clock/counter
arithmetic. This accepts only the logical storage/transport result and specific
modeled controller cadence stated above. It is not human/account-holder approval.
Exact-publication-head review and applicable hosted checks remain separate later
gates; no merge is claimed.

Original receipt scientific acceptance remains `unverified`; the driver's
scientific-acceptance flag remains `unverified_pending_independent_review`.
Its actual driver status is `pass_functional_behavioral_port_only`.
Those raw flags are preserved alongside
the bounded pass result rather than rewritten as acceptance. Earlier failed
full-hash/mapping attempts, cancelled CI and skipped controls retain their own
original status. This experiment introduced no new failed or skipped command.

The memory model is a declared one-cycle synchronous host-modeled service with
offline `$readmemh` preload, immutable counts/rows and no runtime write/reload API.
It is not autonomous hardware preparation or a characterized SRAM macro. No live
software input/fill/program/dataset-generation callbacks, cache.bin generation or
load, native regeneration, whole-core build, synthesis/mapped campaign or new
full hash occurred. Accepted channel/arithmetic/defaults and historical evidence
remain unchanged; component files are exact copies of the executed source.

Characterized process/PVT/SRAM and its real port timing, controller/PHY service
and tails, physical area/energy/frequency, wall power, achieved hashes/s,
architecture selection and the whole-machine target remain open. The prior
hypothetical CACTI 45 nm/1 V/360 K estimate is not physical timing for this model.
Broader issue #72 remains open. Next integration or physical work requires its own
evidence-backed scope and admission; this result creates no new execution promise.
