# Retained read-grant correction evidence

[Independent review](https://github.com/jliu67/OpenRX/pull/53#pullrequestreview-5497704738)
rejected bd193092's overlapping read/write handshake. The unchanged original
controller fails the new directed test; the corrected retained-grant controller
passes four RTL and both actual A/C mapped configurations. Eight RTL/four mapped
native differential logs remain byte-identical to the original serialized replay.

[summary.json](summary.json), [resources.json](resources.json) and [index.json](index.json)
bind current generic cells, unchanged native cycles, raw/public exports, the exact
original fatal result, corrected source/commands/netlists and measured resource
limits/pressure. Gzip exports are lossless; verify both public and decompressed
raw SHA-256. All prior evidence and source remain immutable. The old failure is
not replaced by a pass or assigned a performance result. See
[interface](../../../rtl/engine/README.md) and [EXP-005](../../../experiments/EXP-005-iteration-engine.md)
for the contract and broader scope. Same-reviewer delta acceptance and final CI
remain required; no merge is authorized.
