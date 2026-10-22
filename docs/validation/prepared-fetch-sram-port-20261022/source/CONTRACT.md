# Prepared-fetch SRAM-port candidate — PREPARED / UNRUN

This candidate extends no accepted scientific claim. Base main is PR95 merge
`90b87f55220151a2bb43ed097c8d55e62a534e0b`. The accepted shared channel is reused
byte-for-byte in inputs/channel.v. No accepted arithmetic, cache service,
dataset controller, whole-hash integration or historical evidence is modified.

## Falsifiable question

Can one explicitly clocked read port return the single admitted prepared image
through the unchanged two-client shared channel with exact row data, owner/full
tag/address echo, held replies and cancellation drain? Does this particular
one-credit controller attain its designed three-clock continuous capture spacing
while its request/response/occupied-clock ledgers close exactly?

Expected answers are assertions to be tested, not results. No tests, compiler or
simulator have run. PR94's necessary two-clock floor is unchanged. Adding this
specific synchronous storage port is expected to yield capture E0, row read E1,
consume E2, next capture E3, with 31 intervals spanning93 modeled clocks for32
continuous requests. These are interface-clock statements, not physical seconds
or achievable chip frequency.

## One admitted immutable image

Only the retained cache0 program image from execution20261018T175827Z-447be94ead08
is admitted. Cases000/001 share the32 array files byte-for-byte. Eight program
counts are [447,438,449,447,444,449,452,437]:3563active rows and533padding rows.
There are239 reciprocal rows, global indices0–238 in traversal order. This
demonstrates no general capacity for all program images or the larger global
reciprocal namespace tested by earlier executor work.

Logical storage is4096rows ×256bits=128KiB. Address bits11:9 select program0–7;
bits8:0 select slot0–511. Row bits63:0 are instruction;127:64 reciprocal;159:128
global reciprocal index;160 validity;255:161 reserved zero. Offline preparation
requires opcode13 iff reciprocal-valid, immediate upper32 equal to global index,
value equal to the retained table and exact integer reciprocal identity, and
zero index/value on nonreciprocal instructions. All inactive tuples and reserved
bits are zero. No separate reciprocal-row interface or live table lookup exists.

Eight10-bit counts,29 response echo/error bits and65 owner/tag bits reside
outside SRAM; their registers, queues, ECC, wiring and other overhead are not
included in the128KiB payload capacity. Epoch16 is opaque echoed metadata; it
does not select another image or change row address.

The exporter checks both cases and refuses an existing output directory. The
independent oracle reads the original fixture fields, exact native descriptors,
cache metadata and reciprocal table, and reconstructs gold by byte assembly
without importing exporter code. Command2's wrapper imports both modules in one
process; this is independent implementation, not process isolation. The oracle
consumes37 source files; the frozen source manifest/outer driver binds every
candidate file, including all71 copied inputs. Original input bindings remain
outside the candidate in input-bindings01.json for root pre/post verification.

## Port, hold and cancellation contract

The adapter accepts fixed28-bit requests {epoch16,program3,pc9} and65-bit tags
{owner1,client-tag64}; replies are190 bits {echo28,error1,valid1,index32,
reciprocal64,instruction64}. Metadata is captured on request handshake and cannot
follow replacement inputs. One pending credit excludes another request and a
new request on the consume edge. A synchronous port captures read enable/address
on that handshake edge, updates its registered data/valid after the edge, and
keeps them stable until the next read. This exact one-cycle/sticky-valid port is
the admitted contract; arbitrary delayed/stale row-valid protocols are outside it.

Only sealed images may issue requests. Counts and rows remain immutable while
sealed, including across cancel and reset. A PC at/above its admitted count
returns the captured full tag/address with error1 and zero161-bit data, held
until consumed; it issues no row read. Padded slots never execute. Adapter also
flags nonzero row reserved bits, but trusted offline admission handles image kind,
counts, opcode and reciprocal semantic validation before traffic.

Cancellation stays in the unchanged shared channel: a captured transaction
retains its owner/full tag, issues if still queued, and drains exactly one reply
without delivery. A nonowner cancel must not affect it. The adapter has no cancel
or runtime image-write/reload port. Quiescent reset is permitted only after
clients/channel/provider have genuinely drained and no pre-reset packet remains.
It clears transport diagnostics but leaves the frozen image and external tag
namespace history intact. Full tags may not be reused while a packet with that
identity survives. The finite bench allocates unique tags without wrapping; this
candidate does not change or exhaustively revalidate accepted session-generation
capacity logic or permit reset to recycle live identities.

## Planned validation and acceptance boundary

Exactly4 sequential timed commands in validation-plan.json:36 Python methods
(24 exporter +12 independent-oracle mutation checks), offline image export and
independent roundtrip report, one Icarus compile, one finite VVP run. The bench
contains12 named scenarios and expects7199requests:7167active reads (including
7126exhaustive both-owner queries),32bounds errors and3cancellation drains.
It checks held replies, captured descriptor replacement, queued/issued/held
cancel, nonowner cancel, epoch echo, continuous cadence, quiescent reset and final
counter/clock closure. Hard watchdog100000 modeled clocks. Expected counts are
not observed counts until execution.

One worker/global slot; CPU600%, RAM1073741824B, swap2147483648B, Tasks256;
120seconds plus5seconds TERM/KILL/reap grace per command. Maximum command timeout
budget480seconds plus20seconds grace, excluding staging/finalization/admission;
no fixed overall deadline is promised. Stop first failure/timeout/postcondition
or binding mismatch, preserve all outputs and leave later commands unrun. No
fallback, retry, search expansion or automatic repair/rerun. Future admission
requires specific execution approval, matching public claim/request, immutable
runner657, LOCAL_ACTIVE, fresh host/overlap/locks, kernel/ancestor/affinity and
resource-headroom checks; none are granted by this preparation document.

The driver requires the canonical execution/results output, exact execution-ID
service cgroup, and every frozen source/manifest/tool file to be listed with its
matching bytes/hash in immutable admission. On timeout or any exception after
launch, it supervises the entire subprocess group for one total5-second grace:
TERM immediately, KILL by4seconds if still present, nonblocking reap/group checks
until5seconds. It never blocks waiting after that deadline or starts a later
command after an orphaned descendant. If a group still cannot drain, failure
remains explicit and the immutable outer runner retains cgroup/slot cleanup
ownership. Hard termination can bypass finally; root must independently recheck
all frozen/original/tool bindings afterward before result acceptance.

External SIGTERM (default Python disposition), SIGKILL, host loss or supervisor
termination may bypass Python exception/finally cleanup. They are outer-runner
cleanup and root posthash cases, never successful payload completions. No
subprocess or resource-slot drain is claimed from driver finally in those cases.
The finite bench emits cumulative occupied clocks, the last-reset occupied-clock
baseline, post-reset occupied clocks and transport counters separately, so later
review can audit reset-domain closure without reconstructing every waveform.

## Behavioral services and physical unknowns

The validation-only SRAM model uses offline $readmemh preload, then has no runtime
write or reload API. This is retained preparation plus a declared behavioral
one-cycle host-modeled memory service. It is not autonomous hardware initialization
or a characterized SRAM macro. There are no live software input/fill/program/
dataset generation callbacks, no cache.bin load/generation and no full-hash run.

No process, PVT, voltage, cell library, characterized SRAM latency/ports, timing
closure, area, energy, sustainable service/tails, controller/PHY cost, wall power
or achieved hashes/s is established. The prior hypothetical CACTI45nm/1V/360K
estimates are not substituted for this model's physical timing. This port's
modeled cadence cannot establish physical throughput or a one/four-bank speedup.
All previous scientific criteria/raw flags and broader issue72 stay unchanged.

Later result acceptance requires actual successful commands with measured wall
time/RSS, complete outputs/source/tool checks and independent result review.
Publication-head review and applicable checks remain separate merge gates.
