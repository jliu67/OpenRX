# Native scratchpad finalization evidence

Task [#67](https://github.com/jliu67/OpenRX/issues/67) implements the standalone
post-execution boundary in [the design](../../../rtl/hash/FINALIZATION.md): actual
scratchpad AES reduction, complete 64-byte A replacement, then independently
parameterized BLAKE2b-256 over 256 little-endian R/F/E/A bytes.
Parent `4f095fc147b5bc78de79746a0a172f38e34d6450` is validated/frozen draft PR65;
it is not independently accepted or merged. The full program-7 input was separately
accepted in PR63. No PR65 public review is published here.

## Local validation

The executed readonly source is `/tmp/openrx-scratchpad-finalizer-fixed-ak52i1dk`. All 41 RTL / 19 mapped
modes pass. Four full 2 MiB RTL trials use ABBA actual/pattern/pattern/actual order
and ideal/stalled/ideal/stalled profiles. Every trial performs 131,072 reads from
0 through `0x1ffff0`, agrees with unchanged native `hashAes1Rx4<true>` and native
BLAKE2b-256, preserves R/F/E/round mode and rejects truncation of BLAKE2b-512.
Python independently agrees for all 14 cases. Full ideal/stalled primary latency
is 393,284 / 1,048,649 modeled clocks; elapsed records also include setup and held
completion. Directed tests cover captured inputs, all rounding modes, stalls,
wrong-generation/index errors, first/last read errors, invalid size, held results,
and request/read/AES/hash/return reset with fresh-tag restart. Six malformed-native
cases and four invalid-size elaborations fail as intended.

The mapped 256-byte component completes six native ideal/stalled cases and nine
directed controls. Four default mapped controls check errors/cancellation and
only the first restart read, explicitly `restart_only=1, native_success=0`.
No full mapped 2 MiB hash is claimed. Actual default stage mapping uses Yosys 0.9:

| Component | Scratchpad bytes | Generic cells | Flop cells | Latch cells |
| --- | ---: | ---: | ---: | ---: |
| scanner-default | 2,097,152 | 41,321 | 1,195 | 0 |
| finalizer-default | 2,097,152 | 100,485 | 8,958 | 1,024 |
| finalizer-bounded256 | 256 | 100,497 | 8,958 | 1,024 |

Latches are inherited BLAKE G operand storage and are reported separately.
Generic cells and modeled clocks do not establish physical area, timing or power.
The global nonblocking lock serialized one worker. Actual CPU `600000 100000`,
RAM4GiB, swap512MiB, Tasks128 and affinity0–5 were verified, with fresh ≥1GiB OS
reserve and no tighter visible ancestor. Measured cgroup peak is 1,902,161,920 bytes;
see [resource receipt](server/resource01.json) for limits, ancestor and final events.

## Exact records and declared successor

[Raw summary](server/summary.json), [PASS records](server/pass-records.json),
[commands](server/commands.json), [input bindings](server/inputs.json), and
[complete tool version streams/status](server/post-run-tool-versions.json) are
preserved. Raw legacy `accepted_parent` labels mean validated/frozen draft PR65;
the raw scanner `digest_bytes=32` field is a metadata error. Separate
[normalized summary](server/summary-normalized.json) reports scanner AES64 output
and the actual parent status without rewriting original records.

The publication successor corrects those labels, tool stdout/stderr/status capture,
binds the consumed full artifact manifest through the final source guard, and
adds the executed staging-test file to CI triggers. Eleven focused successor tests
pass. All RTL/native/oracle/fixture/bench bytes remain exact; scientific run,
compile/simulate functions and synthesis command construction are identical.
The locally executed driver differs in these declared metadata/guard changes;
[old/new digests](server/successor-corrections.json) and targeted logs record that
distinction. Hosted full validation of the published head and new independent
exact-head review remain required. Coauthor checks are not acceptance.

## Retention and reproduction

The [public map](raw-public-map.json) binds every lossless selected export to its
complete-output counterpart. Public fixture summaries retain all RF/AES/digest
expectations, case/native provenance and bounded scratchpad inputs. Both complete
full inputs are retained in the verified local archive and reproduced by
[exact accepted source/deterministic seed references](fixtures-summary/full-input-references.json).
Raw fixture manifests describe the complete original output, not this selected
export directory. Complete binaries, raw inputs and netlists are preserved in
`/home/server/Documents/Codex/2026-10-11/task-2/aes-finalization-implementation-evidence/validation01-complete-output.tar.gz` with SHA256 `72f5603477e19945f9dbc155e5a7bdd684296f0e5495c9e221878aad1360cfdf`;
all 383 output files and original modes were verified before
readonly retention. [Retention receipt](source-output-retention.json) also binds
complete original source01/source02 archives. The duplicate BLAKE-module
preparation elaboration failure is retained under `preparation/`; only the
redundant compiler input list changed in the fresh execution source02.
All 246 frozen parent bindings, 171 RandomX originals, three secworks originals
and five BLAKE originals remain unchanged. No accepted full program chain reran.

Use the publication source in a fresh admitted per-execution staging tree:

```bash
python3 -B -m unittest discover -s tests -p test_scratchpad_finalization_staging.py -v
python3 scripts/test_scratchpad_finalization.py --output /tmp/openrx-finalization-UNIQUE --synthesize
```

Retain exact tools/licenses, complete outputs, all input hashes, resource receipts,
source snapshots and failures. Initial scratchpad fill, program AES generation,
full actual dataset, complete hardware hash, selected core and physical/calibrated
PPA remain open. This feature does not change execution, `(v & 60)==0`, address
recurrence or rounding propagation across programs. No merge is authorized.
