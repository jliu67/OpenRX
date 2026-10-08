#!/usr/bin/env python3
"""Extract static RandomX configuration facts. This is NOT a timing/traffic model."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    'ARGON_MEMORY', 'DATASET_BASE_SIZE', 'DATASET_EXTRA_SIZE',
    'PROGRAM_SIZE_V1', 'PROGRAM_SIZE_V2', 'PROGRAM_ITERATIONS', 'PROGRAM_COUNT',
    'SCRATCHPAD_L1', 'SCRATCHPAD_L2', 'SCRATCHPAD_L3',
)


def analyze(content):
    """Parse only decimal-literal macros; reject missing, duplicate or invalid data."""
    macros = {}
    for line in content.splitlines():
        match = re.match(r'^\s*#define\s+RANDOMX_([A-Z0-9_]+)\s+(.+?)\s*$', line)
        if not match:
            continue
        name, value = match.groups()
        if name not in REQUIRED and not name.startswith('FREQ_'):
            continue
        if name in macros:
            raise ValueError(f'duplicate macro: {name}')
        value = value.split('//', 1)[0].strip()
        if not re.fullmatch(r'\d+', value):
            raise ValueError(f'expected decimal literal for {name}')
        macros[name] = int(value)
    missing = set(REQUIRED) - macros.keys()
    if missing:
        raise ValueError(f'missing macros: {sorted(missing)}')
    if any(macros[name] <= 0 for name in REQUIRED):
        raise ValueError('configuration sizes/counts must be positive')
    frequencies = {name[5:]: value for name, value in macros.items() if name.startswith('FREQ_')}
    if not frequencies or sum(frequencies.values()) != 256:
        raise ValueError('instruction opcode weights must sum to 256')
    groups = {'integer': 0, 'floating_point': 0, 'control': 0, 'store': 0, 'nop': 0}
    for name, weight in frequencies.items():
        if name == 'ISTORE':
            group = 'store'
        elif name == 'NOP':
            group = 'nop'
        elif name in ('CBRANCH', 'CFROUND'):
            group = 'control'
        elif name.startswith('I'):
            group = 'integer'
        elif name.startswith('F'):
            group = 'floating_point'
        else:
            raise ValueError(f'unclassified opcode: {name}')
        groups[group] += weight
    scratch = [macros['SCRATCHPAD_' + level] for level in ('L1', 'L2', 'L3')]
    if scratch != sorted(scratch) or any(size & (size - 1) for size in scratch):
        raise ValueError('scratchpad regions must be ordered powers of two')
    if any(macros['PROGRAM_SIZE_' + version] % 8 for version in ('V1', 'V2')):
        raise ValueError('program sizes must be divisible by eight')
    if macros['DATASET_EXTRA_SIZE'] % 64:
        raise ValueError('dataset extra size must be divisible by 64')
    iterations = macros['PROGRAM_COUNT'] * macros['PROGRAM_ITERATIONS']
    return {
        'schema_version': 1,
        'evidence_class': 'source-derived static configuration; not measured or simulated',
        'configuration_macros': {name: macros[name] for name in REQUIRED},
        'dataset_bytes': macros['DATASET_BASE_SIZE'] + macros['DATASET_EXTRA_SIZE'],
        'cache_bytes': macros['ARGON_MEMORY'] * 1024,
        'scratchpad_regions_bytes': dict(zip(('L1', 'L2', 'L3'), scratch)),
        'main_loop_iterations_per_hash': iterations,
        'nominal_vm_slots_per_hash': {
            version.lower(): macros['PROGRAM_SIZE_' + version] * iterations
            for version in ('V1', 'V2')
        },
        'opcode_weights_per_256': dict(sorted(frequencies.items())),
        'opcode_groups_per_256': groups,
        'limitations': [
            'Opcode weights describe random program generation, not measured dynamic execution.',
            'Nominal VM slots exclude branch re-execution and JIT transformations; not host instructions.',
            'L1/L2/L3 are nested scratchpad address regions, not physical CPU cache specifications.',
            'The dataset may be shared across VMs; each VM needs its own scratchpad.',
            'No cache-miss rate, DRAM traffic, latency, throughput, power or efficiency is inferred.',
        ],
    }


def profile(path):
    raw = path.read_bytes()
    result = analyze(raw.decode('utf-8'))
    result['configuration_sha256'] = hashlib.sha256(raw).hexdigest()
    result['configuration_git_blob_sha1'] = hashlib.sha1(
        f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path,
                        default=ROOT / 'vendor/randomx/src/configuration.h')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        result = profile(args.configuration)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
