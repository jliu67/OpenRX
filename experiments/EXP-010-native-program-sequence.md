# EXP-010: Native program initialization and sequencing

[Task #62](https://github.com/jliu67/OpenRX/issues/62) / [draft PR63](https://github.com/jliu67/OpenRX/pull/63)
preserve original accepted base `7f299c74f81332257eefd775086b355969ad85f3`.
[Design](../rtl/execute/PROGRAM_SEQUENCE.md) / [complete evidence](../docs/validation/program-sequence-20261013/README.md)
define interfaces and raw/public/source/resource provenance.

The unchanged full native-v2 eight-program ×2048-iteration workload passes 16,384
iterations,6,305,764 instruction retirements,1,282,660 bytecode events,131,072 tail
stores and full register/round/control/memory assertions at every iteration;
all 2 MiB is compared after each of eight programs. Actual DUT registers seed each
next externally generated native program. Current server and hosted nine RTL
modes pass; nine mapped modes match. Yosys0.33 maps default control 4500/2383
cells/flops and default whole top 249196/12526. Short v2 ideal/stalled clocks
110934/185396, v1 70110/120864. These model clocks omit software preparation and
finalization and use the stated ready/valid responder delays.

Default mapped control checks 8×2048 counts with an explicitly identified backend
stub; short mapped control checks complete native v1/v2 program transitions.
Default whole gates check one native v2 iteration plus connected resets/errors,
including a committed store prefix. No full whole-top 16k gate run is claimed.
The original full-run harness, later cancellation extensions, both original
fixture failures, initial/corrected publications and hosted artifacts remain
exactly bound and archived. All69 current inputs/197 hosted output digests and 70
native fixture files are verified; accepted parent53 inputs remain unchanged.

Software scratchpad/program/hash stages and addressed fixture dataset remain
outside hardware. Full actual dataset/hardware hash/full v1 8×2048/physical PPA
remain open. Original accepted base/evidence are preserved through separately
owner-authorized parent merges. New independent review is required; PR63 merge
is not authorized.
