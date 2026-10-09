# Static simulated tick budget review

The current `10000000000000` per-call tick allowance cannot complete the unchanged light matrix. Two mandatory cache initializations require at least **10,519,287,680 guest instructions**, spanning at least **10,519,287,679,000 ticks**, in their Argon round loops alone. This conservative bound allows the first counted instruction to execute at the simulate call's entry tick and excludes all other work. It is an execution-budget proof, not a performance estimate or a completed hash result.

`matrix_review` derived this bound read-only from the exact executing hash ELF and actual generated simulator configuration. `state_review` independently confirmed the full ELF count, counter and bound register invariants, cache driver/backend selection and exit sequence. `runner_review` independently confirmed the ordinary scalar instruction classes and Atomic scheduling, including the conservative entry-boundary correction. Root also replayed the count and inspected the CPU configuration and scheduler. The bound is independently accepted. The matching machine-readable evidence is [budget-review.json](budget-review.json).

## Input identities

The guest ELF is `/tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe`, 376,824 bytes, SHA256 `61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657`. Execution source commit is `9d108c4041e0fa440a676f8a3ee1a2db1d736192`.

The actual attempt-2 `m5out/config.ini` has SHA256 `7d5e9caf43ede0a65bf48be3b718ccac2e2fe7c7ed9df1990724b40b4ea0ddd9`. Its `board.clk_domain` clock period is 1,000 ticks and its `board.processor.cores.core` is `BaseAtomicSimpleCPU`, width 1. Both instruction and data stall simulation are false. `simulator/gem5/fs.py` uses this single Atomic CPU throughout; it does not restore a checkpoint, switch cores or fast-forward guest instructions.

Pinned gem5 source is `c8222cc67a399bfc01e8658dd14b30d5bfd634f9`. `src/cpu/simple/atomic.cc` SHA256 is `dd224e8f3edbfba2b99019abb7286fa58dbcd3b08c30f86bfa6381e1f0a06a0b`. Its `tick()` executes at most `width` ordinary instructions per tick, then schedules the next tick at least one clock period later. The special `locked` extension of this loop applies to locked RMW operations; the two Argon loops contain no atomic or locked RMW instructions. Successive ordinary instructions therefore require at least 1,000 ticks of spacing. To avoid an entry-boundary assumption, this review subtracts one instruction interval from the total lower bound.

## Mandatory instruction count

`readelf -sW` identifies local function `fill_block` at virtual address `0x32972`, size 3,084 bytes. Decoding instruction boundaries from that function's start produces 952 static instructions. Its two round loops each have 418 instructions, including the terminal backward branch. Neither loop contains an internal branch, jump, call or atomic instruction.

| Round loop | First instruction | Backward BNE | Instructions per iteration | Iterations per block |
|---|---|---|---:|---:|
| Columns | `0x32a2e` | `0x32f9e` | 418 | 8 |
| Rows | `0x32fa8` | `0x33514` | 418 | 8 |

The exact compiled pointer bounds establish eight iterations independently of the source's `for (i = 0; i < 8; ++i)` loops. Within each loop, only its terminal increment writes the counter register, and no instruction writes its bound register:

- `0x3299a`: `ADDI x16, sp, 24` supplies the destination to `memcpy`; `0x329be` restores its returned destination to `x16`. `0x329c0`: `ADDI x9, sp, 1048`. `0x32a28` copies `x16` to `x6`. Each column iteration ends with `ADDI x6, x6, 128` at `0x32f9a`, then `BNE x9, x6` at `0x32f9e`. The 1,024-byte range divided by the 128-byte step is eight.
- `0x32fa2`: `ADDI x23, x16, 128`; `0x32fa6` copies `x16` to `x28`. Each row iteration ends with `C.ADDI x28, 16` at `0x33512`, then `BNE x23, x28` at `0x33514`. The 128-byte range divided by the 16-byte step is eight.

Pinned `configuration.h` specifies 262,144 blocks, three Argon passes and one lane. `argon2_core.c` visits every pass and all four slices. `argon2_ref.c` skips only the first two blocks of the first pass because initialization already supplied them; every remaining block unconditionally calls `fill_block`. Thus each cache requires `(262144 × 3) − 2 = 786430` fills.

The probe's `hashChecks` constructs two fresh cache objects sequentially, for interpreter and JIT. Their cache flags are 0 and 8. `dataset.hpp::selectArgonImpl` selects `randomx_argon2_fill_segment_ref` for both, since neither flag enables an optimized Argon implementation. `randomx.cpp::randomx_init_cache` initializes each new cache; the second object cannot reuse the first object's initialization. JIT cache initialization calls `initCache` before compiling superscalar code.

Consequently, the round loops alone require:

```text
418 instructions × 8 iterations × 2 loops × 786430 blocks × 2 caches
= 10,519,287,680 instructions
(10,519,287,680 − 1) × 1000 ticks between successive ordinary instructions
= 10,519,287,679,000 ticks
> 10,000,000,000,000 configured ticks per simulate call
```

Both cache initializations run within the guest script after hypercall 2. Neither the probe nor the RandomX cache code issues an intervening simulator exit or hypercall. The script's completion hypercall 3 follows all controls. No cache work can be skipped while retaining this complete matrix. The allowance therefore cannot be rescued by the reset that occurred at hypercall 2. The bound excludes boot, the nine runtime controls, cache copies/allocation, superscalar generation, all eight hashes, kernel scheduling and all other probe instructions.

## Reproduce the ELF count

These commands inspect the existing ELF; they do not build or execute a workload:

```bash
sha256sum /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe
readelf -sW /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe
readelf -SW /tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe
```

The dependency-free Python decoder below maps virtual addresses through the ELF's load segment, counts 16/32-bit RISC-V instruction boundaries and checks both loops for any internal control transfer or atomic opcode. It decodes from the function start to avoid entering the middle of an instruction.

```python
from pathlib import Path
import hashlib
import struct

data = Path('/tmp/openrx-runtime-ci/probe-riscv/openrx-riscv-probe').read_bytes()
assert hashlib.sha256(data).hexdigest() == '61cf489ab2277477a1b5464035c21fa43c6b5e59153fe37313dbbd4ae6b4e657'
phoff = struct.unpack_from('<Q', data, 32)[0]
phsize, phnum = struct.unpack_from('<HH', data, 54)
start, end = 0x32972, 0x32972 + 3084
for index in range(phnum):
    segment = struct.unpack_from('<IIQQQQQQ', data, phoff + index * phsize)
    if segment[0] == 1 and segment[3] <= start < segment[3] + segment[5]:
        file_offset = segment[2] + start - segment[3]
        break
else:
    raise AssertionError('Missing load segment')

instructions = []
pc = start
while pc < end:
    offset = file_offset + pc - start
    halfword = int.from_bytes(data[offset:offset + 2], 'little')
    size = 4 if halfword & 3 == 3 else 2
    word = int.from_bytes(data[offset:offset + size], 'little')
    instructions.append((pc, word, size))
    pc += size
assert pc == end and len(instructions) == 952

expected = {
    0x3299a: (0x01810813, 4),  # ADDI x16, sp, 24
    0x329be: (0x882a, 2),      # C.MV x16, x10 (memcpy return)
    0x329c0: (0x41810493, 4),  # ADDI x9, sp, 1048
    0x32a28: (0x8342, 2),      # C.MV x6, x16
    0x32f9a: (0x08030313, 4),  # ADDI x6, x6, 128
    0x32fa2: (0x08080b93, 4),  # ADDI x23, x16, 128
    0x32fa6: (0x8e42, 2),      # C.MV x28, x16
    0x33512: (0x0e41, 2),      # C.ADDI x28, 16
}
by_address = {pc: (word, size) for pc, word, size in instructions}
assert all(by_address[pc] == value for pc, value in expected.items())

def transfer(word, size):
    if size == 4:
        return word & 127 in (0x63, 0x6f, 0x67)
    quadrant, funct3 = word & 3, word >> 13
    return (quadrant == 1 and funct3 in (5, 6, 7)) or (
        quadrant == 2 and funct3 == 4 and (word >> 2 & 31) == 0)

def destination(word, size):
    if size == 4:
        return word >> 7 & 31 if word & 127 in (0x03, 0x13, 0x33) else None
    quadrant, funct3 = word & 3, word >> 13
    if quadrant == 0 and funct3 in (0, 2, 3):
        return 8 + (word >> 2 & 7)
    if quadrant == 1:
        if funct3 in (0, 1, 2, 3):
            return word >> 7 & 31
        if funct3 == 4:
            return 8 + (word >> 7 & 7)
    if quadrant == 2 and funct3 in (0, 2, 3, 4):
        return word >> 7 & 31
    return None

for begin, branch in ((0x32a2e, 0x32f9e), (0x32fa8, 0x33514)):
    body = [row for row in instructions if begin <= row[0] <= branch]
    assert len(body) == 418 and body[-1][0] == branch
    assert not any(transfer(word, size) for _, word, size in body[:-1])
    assert not any(size == 4 and word & 127 == 0x2f for _, word, size in body)
    word = body[-1][1]
    assert word & 127 == 0x63 and word >> 12 & 7 == 1  # BNE
    immediate = ((word >> 31 & 1) << 12) | ((word >> 7 & 1) << 11)
    immediate |= ((word >> 25 & 63) << 5) | ((word >> 8 & 15) << 1)
    if immediate & 4096:
        immediate -= 8192
    assert branch + immediate == begin
    counter, bound, increment = (6, 9, 0x32f9a) if begin == 0x32a2e else (28, 23, 0x33512)
    assert [pc for pc, word, size in body if destination(word, size) == counter] == [increment]
    assert not any(destination(word, size) == bound for _, word, size in body)
    print(hex(begin), hex(branch), len(body), 'instructions; 8 iterations')
print(418 * 8 * 2 * (262144 * 3 - 2) * 2)
```

## Consequence for the next attempt

The current attempt was stopped and preserved as incomplete evidence after independent confirmation; see [REVIEW.md](REVIEW.md). The proposed next command should declare `--max-ticks 100000000000000`, retaining a finite guard with ten times the previous allowance. This larger allowance has not been executed, and this lower-bound proof does not guarantee that it is sufficient. The next attempt must still produce all 39 required light controls, all nine runtime controls, complete guest frames, hypercalls `[1, 2, 3]` and simulator exit 0. No wall timeout is proposed, and the default in source need not change.

No signal, process mutation, simulator build, workload change, timing calibration or power measurement was performed by this reviewer.
