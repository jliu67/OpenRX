#!/usr/bin/env python3
"""Native scratchpad finalization fixtures, generated inside an admitted payload.

No AES implementation or constants are duplicated: an independently compiled
pinned RandomX hashAes1Rx4<true>/blake2b oracle produces the expected results.
The default full case reuses published immutable final-program memory/registers,
not a new program-chain run. This helper does not acquire the global compute slot.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import sys

sys.dont_write_bytecode = True
PINNED_RANDOMX = 'aaafe71322df6602c21a5c72937ac284724ae561'
VENDOR_LOCK_SHA = '2c210a233afaedd668463647d25da27f9ffdb7235e53248f91c6f78c7943e3cd'
VENDOR_MANIFEST_SHA = '2763c092b465bb99d71d544915b9fd847064ec195cc438c6370c34ecdf9b746d'
FULL_DIRECTORY = 'docs/validation/program-sequence-20261013/full-v2-8x2048'
FULL_MANIFEST_SHA = 'd002d55d751718f79df5aee0e08d56e8c5cb91e6e76f18fdc8b20caf766c078f'
FULL_MEMORY_GZIP_SHA = '3a0b6b353ce195d885b0cd189c740ea4cafddac39d570b4585b220fb3072ee8e'
FULL_MEMORY_HEX_SHA = 'e5061265e2cf3635e9cdf6c5b2093bb5ebf9373fce868a753a757b1a3775023c'
FULL_REGISTERS_SHA = 'b7ec8f825f289807c8d70a809dcb9b5b1dce598fe219efa20d72f35f34898798'
FULL_BYTES = 2097152
SEED = 0x7363726174636832
ORACLE_SOURCE = 'rtl/hash/tests/scratchpad_finalization_oracle.cpp'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def compile_command(root, executable):
    """Return the proposal; the owning driver records/runs it in its compute slot."""
    root = Path(root).resolve()
    return ['g++', '-std=c++11', '-O2', '-Wall', '-Wextra',
            '-I' + str(root / 'vendor/randomx/src'), str(root / ORACLE_SOURCE),
            str(root / 'vendor/randomx/src/aes_hash.cpp'),
            str(root / 'vendor/randomx/src/soft_aes.cpp'),
            str(root / 'vendor/randomx/src/blake2/blake2b.c'),
            '-o', str(Path(executable).resolve())]


def _sources(root):
    lock = root / 'vendor/randomx.lock.json'
    manifest = root / 'vendor/randomx.sha256.json'
    if sha(lock) != VENDOR_LOCK_SHA or sha(manifest) != VENDOR_MANIFEST_SHA:
        raise ValueError('pinned RandomX manifest identity changed')
    if json.loads(lock.read_text())['commit'] != PINNED_RANDOMX:
        raise ValueError('pinned RandomX revision changed')
    bindings = {'vendor/randomx.lock.json': sha(lock),
                'vendor/randomx.sha256.json': sha(manifest)}
    for relative, expected in json.loads(manifest.read_text()).items():
        path = 'vendor/randomx/' + relative
        if sha(root / path) != expected:
            raise ValueError('native vendor bytes changed: ' + path)
        bindings[path] = expected
    for relative in [ORACLE_SOURCE, 'scripts/scratchpad_finalization_fixture.py']:
        bindings[relative] = sha(root / relative)
    return bindings


def _accepted(root, memory_path, registers_path):
    source = root / FULL_DIRECTORY
    manifest_path = source / 'artifacts.sha256.json'
    if sha(manifest_path) != FULL_MANIFEST_SHA:
        raise ValueError('accepted full artifact manifest changed')
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get('final-7.hex') != FULL_MEMORY_HEX_SHA or
            manifest.get('program-registers.hex') != FULL_REGISTERS_SHA):
        raise ValueError('accepted full artifact identities changed')
    memory_path = Path(memory_path).resolve() if memory_path else source / 'final-7.hex.gz'
    registers_path = Path(registers_path).resolve() if registers_path else source / 'program-registers.hex'
    memory_file = memory_path.read_bytes()
    if memory_path.suffix == '.gz':
        if digest(memory_file) != FULL_MEMORY_GZIP_SHA:
            raise ValueError('accepted compressed final-7 identity changed')
        memory_hex = gzip.decompress(memory_file)
    else:
        memory_hex = memory_file
    if digest(memory_hex) != FULL_MEMORY_HEX_SHA:
        raise ValueError('accepted raw final-7 identity changed')
    lines = memory_hex.decode('ascii').splitlines()
    if len(lines) != FULL_BYTES // 16 or any(not re.fullmatch(r'[0-9a-fA-F]{32}', line) for line in lines):
        raise ValueError('accepted final-7 must contain exactly131072 native128-bit rows')
    memory = b''.join(bytes.fromhex(line)[::-1] for line in lines)
    registers_text = registers_path.read_bytes()
    if digest(registers_text) != FULL_REGISTERS_SHA:
        raise ValueError('accepted register-file artifact identity changed')
    rows = [line.split() for line in registers_text.decode('ascii').splitlines()]
    if len(rows) != 8 or any(len(row) != 3 or int(row[0]) != index or
                              not re.fullmatch(r'[0-9a-fA-F]{512}', row[1]) or
                              not 0 <= int(row[2]) <= 3
                              for index, row in enumerate(rows)):
        raise ValueError('accepted register-file frames malformed')
    registers = bytes.fromhex(rows[7][1])[::-1]
    provenance = {'source': 'accepted native-v2 eight-program x2048 final program7 artifacts',
                  'directory_in_source': FULL_DIRECTORY, 'program_index': 7,
                  'round_mode': int(rows[7][2]), 'artifact_manifest_sha256': FULL_MANIFEST_SHA,
                  'memory_artifact': str(memory_path), 'memory_artifact_sha256': digest(memory_file),
                  'memory_hex_sha256': digest(memory_hex), 'memory_binary_sha256': digest(memory),
                  'registers_artifact': str(registers_path),
                  'registers_artifact_sha256': digest(registers_text),
                  'selected_register_binary_sha256': digest(registers),
                  'no_program_chain_rerun': True}
    return memory, registers, provenance, {memory_path: digest(memory_file),
                                         registers_path: digest(registers_text),
                                         manifest_path: FULL_MANIFEST_SHA}


def _pattern(size, kind, seed):
    if kind == 'zero':
        return bytes(size)
    if kind == 'walking':
        # One bit per128-bit word, walking through all128 bit positions.
        return bytes((1 << ((i // 16 // 16) % 8)) if i % 16 == (i // 16) % 16 else 0
                     for i in range(size))
    rng = random.Random(seed)
    return bytes(rng.getrandbits(8) for _ in range(size))


def _row(path, size):
    lines = Path(path).read_text().splitlines()
    if len(lines) != 1 or not re.fullmatch(r'[0-9a-fA-F]{' + str(size * 2) + '}', lines[0]):
        raise ValueError('malformed native expected row: ' + str(path))
    return bytes.fromhex(lines[0])[::-1]


def prepare(root, output, native_executable, accepted_memory=None, accepted_registers=None):
    """Prepare12 bounded cases and two full cases; caller owns admitted execution.

    output must be a fresh directory outside root. Optional accepted paths are
    the original final-7.hex(.gz) and complete program-registers.hex artifacts,
    whose bytes must match the same pinned public receipts. Return corpus.json.
    """
    root, output, executable = (Path(path).resolve() for path in
                                (root, output, native_executable))
    if output.exists() or output == root or root in output.parents:
        raise ValueError('fixture output must be fresh and outside source')
    if not executable.is_file() or executable == root or root in executable.parents:
        raise ValueError('native oracle executable must be outside source')
    sources = _sources(root)
    memory, registers, provenance, accepted_bindings = _accepted(root, accepted_memory, accepted_registers)
    executable_sha = sha(executable)
    output.mkdir(parents=True)
    save(output / 'source-bindings.json', sources)
    save(output / 'accepted-full-provenance.json', provenance)
    commands, cases = [], []

    def case(name, scratchpad, register_file, kind, seed=None):
        directory = output / name
        directory.mkdir()
        sp_input, rf_input = directory / 'scratchpad.bin', directory / 'register-file.bin'
        sp_input.write_bytes(scratchpad)
        rf_input.write_bytes(register_file)
        command = [str(executable), str(sp_input), str(rf_input), str(directory)]
        record = {'case': name, 'argv': command, 'cwd': str(root), 'timeout_seconds': 120}
        commands.append(record)
        save(output / 'native-commands.json', commands)
        with (directory / 'native-oracle.log').open('w') as log:
            completed = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                       timeout=120, check=False)
        record['returncode'] = completed.returncode
        save(output / 'native-commands.json', commands)
        if completed.returncode:
            raise RuntimeError('native finalization oracle failed; preserve case ' + name)
        native = json.loads((directory / 'native-inputs.json').read_text())
        if native['scratchpad_bytes'] != len(scratchpad) or native['register_file_bytes'] != 256:
            raise ValueError('native input metadata mismatch')
        rows = (directory / 'scratchpad.hex').read_text().splitlines()
        if len(rows) != len(scratchpad) // 16 or any(not re.fullmatch(r'[0-9a-fA-F]{32}', row) for row in rows):
            raise ValueError('native scratchpad output rows malformed')
        if b''.join(bytes.fromhex(row)[::-1] for row in rows) != scratchpad:
            raise ValueError('native scratchpad packing changed')
        if _row(directory / 'rf-in.hex', 256) != register_file:
            raise ValueError('native register-file packing changed')
        reduced = _row(directory / 'aes-hash.hex', 64)
        final = _row(directory / 'rf-final.hex', 256)
        if final[:192] != register_file[:192] or final[192:] != reduced:
            raise ValueError('native finalization must replace exactly A and preserve R/F/E')
        d32, d64 = _row(directory / 'digest32.hex', 32), _row(directory / 'digest64.hex', 64)
        if (hashlib.blake2b(final, digest_size=32).digest() != d32 or
                hashlib.blake2b(final, digest_size=64).digest() != d64 or d32 == d64[:32]):
            raise ValueError('independent native digest parameter/byte-order check failed')
        if sp_input.read_bytes() != scratchpad or rf_input.read_bytes() != register_file:
            raise ValueError('oracle modified raw input files')
        row = {'name': name, 'directory': str(directory), 'scratchpad_bytes': len(scratchpad),
               'aes_64byte_groups': len(scratchpad) // 64, 'memory_reads128': len(scratchpad) // 16,
               'kind': kind, 'seed': hex(seed) if seed is not None else None,
               'input_scratchpad_sha256': digest(scratchpad), 'input_register_sha256': digest(register_file),
               'a_replacement_only': True, 'digest32_not_truncated64': True,
               'scope': 'native expected assertions; hardware receives only scratchpad and original raw register file'}
        save(directory / 'case.json', row)
        save(directory / 'artifacts.sha256.json', {path.name: sha(path) for path in
                                                   sorted(directory.iterdir()) if path.is_file()})
        cases.append(row)

    for size in [64, 128, 256, 4096]:
        for index, kind in enumerate(['zero', 'walking', 'prng']):
            seed = SEED ^ size ^ (index << 48)
            case('bounded-' + str(size) + '-' + kind, _pattern(size, kind, seed),
                 _pattern(256, kind, seed ^ 0x7265676973746572), kind, seed)
    case('full-actual-final7', memory, registers, 'accepted-full-native-v2-program7')
    full_seed = SEED ^ FULL_BYTES ^ 0x66756c6c
    case('full-pattern', _pattern(FULL_BYTES, 'prng', full_seed),
         _pattern(256, 'prng', full_seed ^ 0x7265676973746572), 'generated-full-prng', full_seed)
    if sha(executable) != executable_sha or any(sha(root / path) != value for path, value in sources.items()):
        raise ValueError('native executable/source changed during fixture generation')
    if any(sha(path) != value for path, value in accepted_bindings.items()):
        raise ValueError('accepted full artifacts changed during fixture generation')
    result = {'pinned_randomx': PINNED_RANDOMX, 'native_executable': str(executable),
              'native_executable_sha256': executable_sha, 'cases': cases,
              'bounded_cases': 12, 'full_cases': 2, 'accepted_full_provenance': provenance,
              'source_and_accepted_inputs_unchanged_after_generation': True,
              'oracle': 'unchanged hashAes1Rx4<true> followed by independently parameterized native blake2b32/64',
              'secondary_digest_oracle': 'Python hashlib.blake2b, digest_size32/64',
              'abba_full_profiles': [{'case': 'full-actual-final7', 'stall': 0},
                                     {'case': 'full-pattern', 'stall': 1},
                                     {'case': 'full-pattern', 'stall': 0},
                                     {'case': 'full-actual-final7', 'stall': 1}],
              'boundary': 'new scratchpad AES finalization fixtures; no full chain/dataset rerun or physical timing/power claim'}
    save(output / 'corpus.json', result)
    save(output / 'artifacts.sha256.json', {str(path.relative_to(output)): sha(path)
                                          for path in sorted(output.rglob('*')) if path.is_file()})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-executable', type=Path, required=True)
    parser.add_argument('--accepted-memory', type=Path)
    parser.add_argument('--accepted-registers', type=Path)
    args = parser.parse_args()
    result = prepare(args.root, args.output, args.native_executable,
                     args.accepted_memory, args.accepted_registers)
    print(json.dumps({'cases': len(result['cases']), 'bounded_cases': result['bounded_cases'],
                      'full_cases': result['full_cases'], 'abba_full_profiles': result['abba_full_profiles']}, indent=2))


if __name__ == '__main__':
    main()
