"""Pinned gem5 v25.1.0.1 scalar full-system functional configuration.

Run through run.py. Resource files must already match resources.json. This
configuration is not BOOM RTL, a calibrated timing model, or a power model.
"""
import argparse
import json
from pathlib import Path

import m5
from gem5.components.boards.riscv_board import RiscvBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import (
    PrivateL1PrivateL2WalkCacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import BootloaderResource, DiskImageResource, KernelResource
from gem5.simulate.exit_handler import ExitHandler
from gem5.simulate.simulator import Simulator

parser = argparse.ArgumentParser()
parser.add_argument("--resources", type=Path, required=True)
parser.add_argument("--readfile", type=Path, required=True)
parser.add_argument("--max-ticks", type=int, default=10**13)
args = parser.parse_args()
if args.max_ticks <= 0:
    parser.error("max-ticks must be positive")

processor = SimpleProcessor(cpu_type=CPUTypes.ATOMIC, isa=ISA.RISCV, num_cores=1)
# Pinned gem5 defaults to RVV enabled. Make scalar execution explicit, including
# its generated DTB. Other implemented scalar extensions remain in config.ini.
for core in processor.get_cores():
    core.core.isa[0].enable_rvv = False
board = RiscvBoard(clk_freq="1GHz", processor=processor,
                   memory=DualChannelDDR4_2400(size="4GiB"),
                   cache_hierarchy=PrivateL1PrivateL2WalkCacheHierarchy(
                       l1d_size="16KiB", l1i_size="16KiB", l2_size="256KiB"))
board.set_kernel_disk_workload(
    kernel=KernelResource(local_path=str(args.resources / "vmlinux")),
    bootloader=BootloaderResource(local_path=str(args.resources / "opensbi")),
    disk_image=DiskImageResource(local_path=str(args.resources / "ubuntu.img"), root_partition="1"),
    readfile=str(args.readfile),
    kernel_args=board.get_default_kernel_args() + ["init=/sbin/gem5_init.sh", "no_systemd"],
)

events = []
report = {"schema_version": 1, "evidence_class": "full-system-functional",
          "cpu": "AtomicSimpleCPU", "cores": 1, "rvv": False, "guest_ram": "4GiB",
          "cache_hierarchy": "PrivateL1PrivateL2WalkCacheHierarchy",
          "l1d_size": "16KiB", "l1i_size": "16KiB", "l2_size": "256KiB",
          "timing_calibrated": False, "power_measured": False,
          "events": events, "execution_stage": "configured",
          "max_ticks_per_simulate_call": args.max_ticks}


def save_progress(simulator=None):
    report["last_tick"] = m5.curTick()
    if simulator is not None:
        report["last_exit_cause"] = simulator.get_last_exit_event_cause()
        report["last_exit_code"] = simulator.get_last_exit_event_code()
    # Preserve completed boot phases if the host later kills a long hash run.
    # Rename makes each small checkpoint complete rather than partly written.
    destination = Path(m5.options.outdir, "simulation.json")
    temporary = destination.with_suffix(".json.partial")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(destination)


class KernelBooted(ExitHandler, hypercall_num=1):
    def _process(self, simulator):
        events.append({"event": "kernel-booted", "hypercall": 1, "tick": m5.curTick()})
        save_progress(simulator)

    def _exit_simulation(self):
        return False


class AfterBoot(ExitHandler, hypercall_num=2):
    def _process(self, simulator):
        events.append({"event": "after-boot-started", "hypercall": 2, "tick": m5.curTick()})
        save_progress(simulator)

    def _exit_simulation(self):
        return False


class ScriptFinished(ExitHandler, hypercall_num=3):
    def _process(self, simulator):
        events.append({"event": "after-boot-finished", "hypercall": 3, "tick": m5.curTick()})
        save_progress(simulator)

    def _exit_simulation(self):
        return True


simulator = Simulator(board=board)
report["execution_stage"] = "running"
save_progress()
simulator.run(max_ticks=args.max_ticks)
report["execution_stage"] = "finished"
save_progress(simulator)
# Hypercall 3 alone is insufficient: upstream after_boot.sh also sends it when
# a child script fails. run.py independently requires complete validated output.
if [event["hypercall"] for event in events] != [1, 2, 3]:
    raise RuntimeError("Did not observe the complete kernel/after-boot exit sequence")
