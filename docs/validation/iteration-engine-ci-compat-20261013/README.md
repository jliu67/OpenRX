# Icarus 12 successful-finish log compatibility

The initial [engine CI](https://github.com/jliu67/OpenRX/actions/runs/38328901245)
on a04b9163 ran and passed the native 4,096-vector conversion test, then the
harness rejected Icarus 12's appended `$finish` diagnostic. [Actual output](hosted-native-i32.log)
and [failure](hosted-failure.json) are retained. The correction requires the
exact first PASS record and a successful process exit, while allowing the
simulator's trailing finish diagnostic. Counts and scientific checks are unchanged.

[Focused recognition checks](ci-compat-recognition-tests.json) accept captured
Icarus 11/12 output and reject incorrect vector counts, rounding coverage or
missing PASS. All eight corrected-driver RTL modes pass with byte-identical
logs to the original; all six hosted native fixture files also match the
original bytes. [index.json](index.json) binds the only changed execution input,
complete logs/failure artifact and focused local provenance. Every RTL/C++/vendor
input, original source, raw output and [mapped evidence](../iteration-engine-20261013/README.md)
remains unchanged. No local synthesis was repeated for this log-only correction;
the full hosted flow validates the final feature tip. One independent new-work
review remains pending; no merge is authorized.
