# Independent stdout-streaming review — 2026-10-08

**Accept the streaming fix for PR #18.** This is source review and executed
host-only synthetic Bash evidence. It is not a second gem5/Linux execution.

The generated guest script now pipes already-flushed probe stdout through `tee`
to serial and the guest JSONL capture. It saves `PIPESTATUS` immediately, before
another command can overwrite it. Successful capture preserves the exact child
exit status in the frame and script exit. Capture failure exits before the frame
can close or the guest completion marker can appear. Existing complete-stream
extraction and all nine/39 exact control requirements remain unchanged.

Reviewed inputs:

| File | SHA-256 |
|---|---|
| `simulator/gem5/run.py` | `26c32c0537f8b7982e512faa6680115f8e4946faf9c1a5c8d28df727f6d1d7b5` |
| `tests/test_gem5_fs.py` | `2b6b7451aa6a7a12112c59823d84d52307cd4d4e824d0cfbfe6698c18099031e` |

The reviewer independently ran the three new generated-Bash tests and six
additional synthetic cases using real host Bash and GNU `tee`:

| Case | Actual exit | Independent result |
|---|---:|---|
| Complete successful producer | 0 | One complete frame; serial/capture equal |
| Child fails while capture succeeds | 42 | Exact child status 42 retained; rejected |
| Capture path is a directory; child succeeds | 1 | Frame remains open; rejected |
| Both child and capture fail | 1 | Capture failure takes priority; frame remains open; rejected |
| Child writes stderr | 0 | Framed stderr retained; strict extractor rejects |
| Kill blocked producer after observing its flushed record | -9 | Partial record reaches serial/capture before exit; open frame rejected |

The separate-write scheduling race in the new test is fixed: both serial and
capture must contain the first record before the blocking child is released.
The kill control likewise waits for both destinations. Guest-image read-only
inspection confirms `/usr/bin/tee` is an executable regular file.

Full commands, generated synthetic scripts, payload text, stdout/stderr/capture,
results and digests are under
[`streaming-review-20261008/`](streaming-review-20261008/), including the
[reproducible helper](streaming-review-20261008/check_streaming.py),
[six-case results](streaming-review-20261008/controls.json) and
[three-test log](streaming-review-20261008/three-tests.stderr.log).
The extra helper relocates guest scratch paths and omits inventory output; the
generated injection, pipeline/status handling, frames and completion are kept.

This change preserves output that the probe flushes. It cannot expose data still
buffered inside a process. The accepted first actual runtime and the concurrent
bounded light attempt used the retained original runner
`7ae0fd2c8c3364cd8f3fc8ff2c082c810e112cd9c71395ab04b89c4915dfcd0a`.
Neither executed this streaming revision. No timing, power, complete light
matrix, selected-core or RTL acceptance follows from these host controls.
