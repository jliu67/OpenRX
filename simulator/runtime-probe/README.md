# Linux runtime gate

`main.c` is a standalone functional control for Linux x86-64 and RV64. It
does not link RandomX or measure throughput. Run it before the unchanged
RandomX arithmetic/hash probe on each selected simulator/core runtime.

It deliberately executes an illegal instruction and recovers through Linux
SIGILL delivery. A generated function must return 7, then 19 after overwrite,
then 7 after restoration. Each update uses a writable-to-executable transition
and cache flush. Execution from RW pages and writes to RX pages must produce
SIGSEGV. On RISC-V, every flush explicitly invokes Linux
`riscv_flush_icache(start,end,flags=0)` and checks the syscall return value.

Native control:

```bash
mkdir -p build/runtime-native
gcc -std=c11 -O2 -Wall -Wextra -Werror simulator/runtime-probe/main.c -o build/runtime-native/openrx-runtime-probe
python3 tests/native_runtime_probe.py --binary build/runtime-native/openrx-runtime-probe --output-dir build/runtime-native/evidence
```

Cross control uses `riscv64-linux-gnu-gcc-14`, `-march=rv64gc -mabi=lp64d`,
then the runner's `--qemu qemu-riscv64 --sysroot /usr/riscv64-linux-gnu` options.
Retain compiler versions, binary digest, raw JSONL and stderr. The runner
rejects missing, reordered, duplicated or self-consistently incorrect checks.

Passing under QEMU is emulator/runtime evidence. QEMU automatically handles
self-modifying code; its flush-icache return does not establish hardware cache
coherence. Repeat the controls in gem5 full-system Linux and on the exact
selected RTL configuration. This single-thread test does not test hart
migration, SMP shootdowns, all memory-order cases or calibrated timing.

The native execution fixture is retained in
`docs/validation/m3-fs/runtime-native.jsonl`. Mutation tests exercise the
validator; they are not target-core execution evidence.
