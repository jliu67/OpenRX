# Independent runtime-probe review — 2026-10-08

Reviewer: session subagent `/root/runtime_review`, independent of the runtime
probe author. Scope: `simulator/runtime-probe/main.c`,
`tests/native_runtime_probe.py` and `tests/test_runtime_probe.py` for task
[#16](https://github.com/jliu67/OpenRandomX/issues/16).

**Result: acceptable as bounded runtime-preflight scaffolding after the
signal-recovery correction below. This review does not accept gem5
full-system execution, selected-core compatibility or M3 completion.**

## Correction requested and verified

The first draft assigned the return from `sigsetjmp` in an initialization or
assignment expression. The author changed all three sites to
`if (sigsetjmp(recovery, 1) == 0)` and stored the received signal separately
in a static `volatile sig_atomic_t` object. This follows the allowed
invocation contexts of
[POSIX setjmp](https://pubs.opengroup.org/onlinepubs/009696899/functions/setjmp.html).
The [POSIX sigsetjmp text](https://www.man7.org/linux/man-pages/man3/sigsetjmp.3p.html)
defines it in terms of setjmp and explicitly carries the same usage
restrictions in its rationale.

The corrected handler only uses signal-safe exit/nonlocal-return operations
and signal-atomic state. Saving the mask with `sigsetjmp(..., 1)` allows the
second deliberate SIGSEGV to be delivered after recovering from the first.
No modified nonvolatile automatic variable is read after a recovery. The
reviewed generated code returns positive values 7 and 19 through `eax` on
x86-64 and `a0` on RV64; the RV64 immediates fit the ADDI encoding, and the
page returned by mmap supplies instruction alignment. Object-to-function
pointer conversion is an intentional Linux platform assumption.

## Independently executed checks

Observed host: `Linux-6.18.44-x86_64-with-glibc2.39`.
Compiler: `cc (Ubuntu 13.3.0-6ubuntu2~24.04) 13.3.0`.

```bash
cc -std=gnu11 -O2 -Wall -Wextra -Werror -Wclobbered \
  simulator/runtime-probe/main.c \
  -o build/runtime-review-independent/openrx-runtime-probe
python3 tests/native_runtime_probe.py \
  --binary build/runtime-review-independent/openrx-runtime-probe \
  --output-dir build/runtime-review-independent/execution
python3 -m unittest discover -s tests -p test_runtime_probe.py -v
```

Compilation produced no diagnostics. The independently compiled native
binary exited 0 with all **nine runtime checks passing** and empty stderr.
All **nine evidence-validator regression tests passed**. The native binary
and complete JSONL digests matched the author's refreshed retained native
capture and report.

| Reviewed item | SHA-256 |
|---|---|
| `simulator/runtime-probe/main.c` | `c05ca5f23a81e8a60f528bdd4052fe63746eb1e1550a11872ed7885a4f5e4fc4` |
| `tests/native_runtime_probe.py` | `99f178b3f8ad84cf0b7542b108338a498a3d23d33a5738839eff96916c284617` |
| `tests/test_runtime_probe.py` | `3bd3a8fc252a6db46ace2da9c84e03c7c6b81ec5c9c694c532a95923c3e16aa0` |
| Independently compiled native binary | `1f2e56fb6987e3c553a72c2e24b43d7ce77cb5d3d03ba9d289f4e3912a934f3a` |
| Complete native JSONL | `b355a4956c9ac20ff503748685fff716f30627c61d32c0a0b6831d03fa246116` |

Local full command/build/test records are in
`build/runtime-review-independent/`; durable matching execution evidence is
[`runtime-native.jsonl`](runtime-native.jsonl) and
[`runtime-native-report.json`](runtime-native-report.json).

The validator enforces the complete ordered nine-check matrix, independent
expected values, exact record schemas, integer types, duplicate-field
rejection, architecture/flush-path consistency and summary consistency.
The runner additionally binds the architecture to ELF64 little-endian
machine identity, records binary/raw digests and retains failures/timeouts.
These checks establish evidence consistency; they do not authenticate an
externally supplied JSONL stream as actual guest execution.

## Evidence limits and next acceptance

- RV64 cross compilation, QEMU execution, gem5 full-system boot and RTL
  execution were **not performed by this reviewer**. The RV64 instruction
  and syscall paths received source review only. Repeat the probe in each
  declared target runtime with toolchain/sysroot and guest image provenance.
- On RV64, the direct flush calls check Linux syscall success with flags
  zero. The sequence verifies permission transitions followed by explicit
  flush and overwrite/re-execution together. A writable-to-executable
  transition may itself synchronize instructions; success does not isolate
  the syscall's instruction-cache effect. QEMU's automatic self-modification
  handling further limits any cache-coherence conclusion.
- One thread does not exercise hart migration, concurrent patching or remote
  hart coherence. The [Linux RISC-V CMODX documentation](https://docs.kernel.org/arch/riscv/cmodx.html)
  explains why local synchronization alone cannot establish those contracts.
- Signal checks observe signal numbers, without checking `si_code`, fault
  address or faulting PC. The deliberate instructions and adjacent successful
  code executions are useful controls, but this is not a signal-origin or
  signal-frame conformance suite. External signal injection is outside the
  tested conditions.
- This standalone program does not link RandomX. Its direct RV64 syscall
  does not establish the cache-flush implementation actually linked into the
  workload's compiler builtin. The unchanged arithmetic/hash probe,
  upstream tests and full-dataset v2/v1 controls remain separate gates.
- No throughput, cycle accuracy, power, architectural advantage or hashes/J
  result follows from this native smoke test. Keep #16 and M3 open pending
  retained selected-runtime execution and their full acceptance criteria.
