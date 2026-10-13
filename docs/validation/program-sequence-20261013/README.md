# Native program-sequence evidence

[Task #62](https://github.com/jliu67/OpenRX/issues/62) retains original accepted
base `7f299c74f81332257eefd775086b355969ad85f3`. The owner's separate parent-PR
merge coordination changes no running workload. This new work requires independent
review and has no merge authorization.

[Index](index.json) binds every raw/public export and complete retained source/output
archive. Large text/HDL/JSON uses lossless gzip. [Resources](resources.json) records
actual kernel/ancestor/affinity/headroom/slot checks and measured job outcomes.
All original sources, builds, data, failures and receipts remain preserved.

The complete native-v2 eight-program ×2,048-iteration RTL run passes: 16,384
iterations, 6,305,764 instruction retirements, 1,282,660 bytecode memory events,
131,072 tail stores, full R/F/E/A/round/memory/control checks each iteration,
and all 2 MiB compared at all eight program boundaries. Full modeled clocks:54,705,599. Programs contain all 256
raw encodings; native preparation spans all four round modes. Current main `9bbda64098bc6dfc999a67e1fdf9333abe0959d3` has the exact reviewed base tree; PR63 targets main with unchanged feature history. Instruction routes
are checked with 64-bit FNV signatures and exact counts; the existing accepted
executor supplies the earlier instruction-level arithmetic/branch proofs.

Current server reproduction and corrected hosted run 38406447341 both pass nine
RTL modes; hosted actual mapping passes nine applicable modes. All mapped PASS
records match RTL, all four short cycle records match the original server pilot,
and 70 native fixture files match. Complete artifact 11820835337 has197
verified digests and 69 verified source inputs. Both initial and corrected hosted
ZIPs and original source snapshots are retained.

Actual Yosys0.33 default control:4500 generic cells/2383 flops; short control:
4506/2383; actual default whole top:249196/12526. Short v2 ideal/stalled clocks
110934/185396; v1 clocks70110/120864. Whole-top gates validate one native v2
iteration and cancellation; full count/feedback is tested on default mapped
control, and native program transitions on short mapped control. The control
backend stub is not arithmetic proof. No full 16k-iteration whole-top gate pass
is claimed. These generic counts/model clocks establish no physical/full-hash PPA.

Initial scratchpad fill/program generation/interprogram BLAKE2b/final hash remain
external software, and dataset replies use an addressed fixture. Full actual
dataset/hardware hash, full v1 8×2048 and calibrated physical timing/power remain
open. [Design](../../../rtl/execute/PROGRAM_SEQUENCE.md) records the original pre-merge design snapshot and exact interfaces,
tag-span reservation, reset/error/partial-store semantics and commands; its initial
draft result section retains its dated publication context. Current results are here.
