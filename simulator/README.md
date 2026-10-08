# Simulator and core candidates

Candidates to investigate, not selections:

| Candidate | Role | Main feasibility question |
|---|---|---|
| gem5 RISC-V | Architectural modeling | Does the selected model implement the pinned binary's exact ISA/FP/crypto needs? |
| Chipyard / BOOM | Configurable RISC-V RTL and simulation | RandomX JIT support, caches, memory model, verification effort and license terms |
| CVA6 | Linux-capable open RISC-V RTL | Throughput, FP behavior and accelerator integration versus area |
| Verilator | RTL functional simulation | Full workload speed and a manageable reduced correctness harness |
| Yosys / physical-design flow | Supported RTL synthesis and area/timing investigation | Compatibility and realistic technology/library constraints |

Primary starting points: https://www.gem5.org/ ; https://chipyard.readthedocs.io/ ; https://github.com/riscv-boom/riscv-boom ; https://github.com/openhwgroup/cva6 ; https://verilator.org/ ; https://yosyshq.net/yosys/

Before selecting: record source/license revision, ISA extensions, FP rounding semantics, Linux boot path, crypto implementation, workload support, memory timing, runtime cost, and model calibration. Functional simulation alone does not yield credible energy estimates.
