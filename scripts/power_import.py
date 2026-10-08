#!/usr/bin/env python3
"""Validate offline power traces against saved steady trials. Never acquire power."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from decimal import Decimal, DecimalException
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import steady_benchmark as steady

NS = 1_000_000_000
LIMIT = 32 * 1024 * 1024
NAMES = ('run.json', 'adapter.jsonl', 'adapter.stderr', 'power.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, names, where):
    require(type(value) is dict and set(value) == set(names.split()), 'invalid fields: ' + where)


def text(value, name):
    require(type(value) is str and 0 < len(value.strip()) <= 2000, 'missing text: ' + name)
    return value


def integer(value, name, minimum=0):
    require(type(value) is int and minimum <= value <= 2**63 - 1, 'invalid integer: ' + name)
    return value


def number(value, name, maximum=1_000_000_000):
    require(type(value) in (int, float, Decimal), 'invalid number: ' + name)
    d = Decimal(str(value))
    require(d.is_finite() and d.as_tuple().exponent >= -18 and 0 <= d <= maximum,
            'out-of-range/nonfinite/overprecise number: ' + name)
    return F(d)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(data, decimal=False):
    require(len(data) <= LIMIT, 'input exceeds 32 MiB limit')
    try:
        return json.loads(data, object_pairs_hook=steady.strict_object,
                          parse_constant=steady.reject_constant, parse_float=Decimal if decimal else float)
    except DecimalException as exc:
        # Decimal rejects exponents outside its representation; preserve the
        # same fail-with-report contract as every other malformed JSON number.
        raise ValueError('invalid JSON decimal number') from exc


def finite(value):
    result = float(value)
    require(math.isfinite(result), 'nonfinite result')
    return result


def check_run(raw):
    """Do not trust a green saved summary; revalidate the complete raw stream."""
    run = decode(raw['run.json'])
    require(type(run) is dict and type(run.get('schema_version')) is int
            and run['schema_version'] == 1, 'unsupported run schema')
    require(run.get('status') == 'ok' and type(run.get('returncode')) is int
            and run['returncode'] == 0, 'benchmark did not succeed')
    require(type(run['vendor_integrity']['returncode']) is int
            and run['vendor_integrity']['returncode'] == 0, 'missing successful integrity check')
    require(re.fullmatch('[0-9a-f]{64}', run['binary_sha256']) is not None, 'missing binary digest')
    require(run['source_sha256']['scripts/steady_benchmark.py'] ==
            sha(Path(steady.__file__).read_bytes()), 'steady validator revision mismatch')
    for name in ('adapter.jsonl', 'adapter.stderr'):
        require(run['raw_sha256'][name] == sha(raw[name]), 'raw digest mismatch: ' + name)
    require(not raw['adapter.stderr'].strip(), 'nonempty adapter stderr')
    keys(run['configuration'], 'threads init_threads nonces warmup_nonces repeats min_seconds aes versions', 'run configuration')
    expected = dict(run['configuration'])
    require(type(expected['versions']) is str, 'invalid run version selection')
    expected['versions'] = expected['versions'].split(',')
    stream = raw['adapter.jsonl'].decode('utf-8')
    summary = steady.validate(stream, expected)
    require(summary['accepted'] and run['summary'] == summary, 'rejected or inconsistent run summary')
    records = [decode(line) for line in stream.splitlines() if line.strip()]
    return records, summary


def trace(doc, raw, config):
    keys(doc, 'schema_version evidence_class benchmark_evidence binding device boundary '
         'units sample_semantics synchronization uncertainty policy samples', 'power trace')
    require(type(doc['schema_version']) is int and doc['schema_version'] == 1, 'unsupported power schema')
    for name in ('evidence_class', 'benchmark_evidence'):
        require(doc[name] in ('synthetic', 'measured'), 'invalid evidence class')
    keys(doc['binding'], 'adapter_sha256 run_sha256', 'binding')
    for field, name in (('adapter_sha256', 'adapter.jsonl'), ('run_sha256', 'run.json')):
        require(doc['binding'][field] == sha(raw[name]), 'power/benchmark binding mismatch')
    require(doc['units'] == {'time': 'ns', 'power': 'W'}, 'units must be ns and W')
    require(doc['sample_semantics'] == 'instantaneous_active_power', 'unsupported sample semantics')
    device = doc['device']
    keys(device, 'id model calibration_reference max_watts', 'device')
    for name in ('id', 'model', 'calibration_reference'):
        text(device[name], name)
    pmax = number(device['max_watts'], 'max_watts')
    require(pmax > 0, 'nonpositive device range')
    boundary = doc['boundary']
    keys(boundary, 'kind description includes excludes', 'boundary')
    require(boundary['kind'] == 'whole_system_ac', 'v1 requires whole-system AC boundary')
    text(boundary['description'], 'boundary description')
    for name in ('includes', 'excludes'):
        require(type(boundary[name]) is list, 'invalid boundary component list')
        for item in boundary[name]:
            text(item, 'boundary component')
    require(boundary['includes'], 'empty physical boundary')
    sync = doc['synchronization']
    keys(sync, 'method source_clock target_clock evidence_reference source_anchor_ns '
         'target_anchor_ns rate_correction_ppm offset_bound_ns drift_bound_ppm '
         'timestamp_bound_ns response_bound_ns valid_from_ns valid_to_ns', 'synchronization')
    require(sync['method'] == 'affine_to_monotonic' and sync['target_clock'] == 'CLOCK_MONOTONIC',
            'unsynchronized or unsupported clock mapping')
    text(sync['source_clock'], 'source clock identity')
    text(sync['evidence_reference'], 'synchronization evidence')
    for name in ('source_anchor_ns', 'target_anchor_ns', 'offset_bound_ns', 'timestamp_bound_ns',
                 'response_bound_ns', 'valid_from_ns', 'valid_to_ns'):
        integer(sync[name], name)
    require(sync['valid_from_ns'] <= sync['source_anchor_ns'] <= sync['valid_to_ns'], 'anchor outside calibration')
    rate_value = sync['rate_correction_ppm']
    require(type(rate_value) in (int, float, Decimal), 'invalid rate correction')
    # Decimal.__abs__ applies the ambient context and can overflow before the
    # explicit cap check. copy_abs is exact and context independent.
    rate_abs = number(Decimal(str(rate_value)).copy_abs(), 'rate correction', 10000)
    rate = 1 + (-rate_abs if rate_value < 0 else rate_abs) / 1_000_000
    drift = number(sync['drift_bound_ppm'], 'drift bound', 10000)
    uncertainty = doc['uncertainty']
    keys(uncertainty, 'absolute_watts relative_fraction interpolation_bound_watts '
         'benchmark_boundary_bound_ns rationale', 'uncertainty')
    absolute = number(uncertainty['absolute_watts'], 'absolute error')
    relative = number(uncertainty['relative_fraction'], 'relative error', 1)
    interpolation = number(uncertainty['interpolation_bound_watts'], 'interpolation error')
    boundary_error = integer(uncertainty['benchmark_boundary_bound_ns'], 'benchmark boundary error', 1)
    require(boundary_error >= config['monotonic_resolution_ns'], 'boundary bound below clock resolution')
    text(uncertainty['rationale'], 'uncertainty rationale')
    if doc['evidence_class'] == 'measured':
        require(absolute + relative > 0 and interpolation > 0, 'measured uncertainty cannot be exact zero')
    policy = doc['policy']
    keys(policy, 'max_gap_ns max_clock_uncertainty_ns max_wall_offset_change_ns '
         'max_relative_energy_error', 'policy')
    for name in ('max_gap_ns', 'max_clock_uncertainty_ns', 'max_wall_offset_change_ns'):
        integer(policy[name], name, 1)
    max_relative = number(policy['max_relative_energy_error'], 'relative energy limit', F(1, 2))
    require(max_relative > 0, 'nonpositive quality limit')
    samples = doc['samples']
    require(type(samples) is list and 2 <= len(samples) <= 200000, 'need 2..200000 samples')
    times, powers, previous = [], [], -1
    for sample in samples:
        keys(sample, 'time_ns watts status', 'sample')
        tick = integer(sample['time_ns'], 'sample time')
        require(tick > previous, 'duplicate or reversed sample timestamp')
        require(sync['valid_from_ns'] <= tick <= sync['valid_to_ns'], 'sample outside calibration')
        require(sample['status'] == 'ok', 'bad/missing/clipped sample')
        watts = number(sample['watts'], 'sample watts', pmax)
        times.append(F(sync['target_anchor_ns']) + (tick - sync['source_anchor_ns']) * rate)
        powers.append(watts)
        previous = tick
    require(times[0] >= 0 and times[-1] <= 2**63 - 1, 'mapped time out of range')
    age = max(abs(s['time_ns'] - sync['source_anchor_ns']) for s in samples)
    clock_error = (sync['offset_bound_ns'] + sync['timestamp_bound_ns'] + sync['response_bound_ns']
                   + age * drift / 1_000_000)
    require(clock_error <= policy['max_clock_uncertainty_ns'], 'clock uncertainty exceeds policy')
    gaps = [b - a for a, b in zip(times, times[1:])]
    require(min(gaps) > 2 * clock_error, 'uncertain sample ordering')
    require(max(gaps) + 2 * clock_error <= policy['max_gap_ns'], 'sample gap exceeds policy')
    slope = max(abs(q - p) / gap for p, q, gap in zip(powers, powers[1:], gaps))
    return times, powers, clock_error, boundary_error, (absolute, relative, interpolation, pmax, slope, max_relative)


def integrate(times, powers, start, end):
    """Exact rational trapezoids; clip boundary segments, never extrapolate."""
    require(times[0] <= start < end <= times[-1], 'insufficient interval coverage')
    index = max(0, bisect_right(times, start) - 1)
    energy = F(0)
    while index < len(times) - 1 and times[index] < end:
        left, right = max(start, times[index]), min(end, times[index + 1])
        width = times[index + 1] - times[index]
        change = powers[index + 1] - powers[index]
        a = powers[index] + change * (left - times[index]) / width
        b = powers[index] + change * (right - times[index]) / width
        energy += (a + b) * (right - left) / (2 * NS)
        index += 1
    return energy


def metrics(hashes, duration, energy, error):
    require(energy > error >= 0, 'energy lower bound is not positive')
    estimate = finite(energy)
    def outward(value, direction):
        return math.nextafter(finite(value), direction)
    return {'energy_joules': estimate,
            'absolute_error_bound_joules': outward(error + abs(energy - F(estimate)), math.inf),
            'energy_lower_joules': outward(energy - error, -math.inf),
            'energy_upper_joules': outward(energy + error, math.inf),
            'average_watts': finite(energy / duration), 'hashes_per_joule': finite(hashes / energy),
            'hashes_per_joule_lower': outward(hashes / (energy + error), -math.inf),
            'hashes_per_joule_upper': outward(hashes / (energy - error), math.inf)}


def analyze(raw, allow_synthetic=False):
    for name in NAMES:
        require(type(raw[name]) is bytes and len(raw[name]) <= LIMIT, 'missing or oversized input: ' + name)
    records, checked = check_run(raw)
    run_evidence = decode(raw['run.json']).get('evidence_class')
    doc = decode(raw['power.json'], decimal=True)
    require(type(doc) is dict, 'power root must be object')
    require(run_evidence != 'synthetic' or doc.get('benchmark_evidence') == 'synthetic',
            'synthetic benchmark cannot be relabeled as measured')
    synthetic = any(doc.get(k) == 'synthetic' for k in ('evidence_class', 'benchmark_evidence'))
    require(not synthetic or allow_synthetic, 'synthetic inputs require --allow-synthetic')
    times, powers, u, boundary_error, terms = trace(doc, raw, records[0])
    absolute, relative, interpolation, pmax, slope, max_relative = terms
    # Check all endpoint offsets, including between trials: do not just check duration deltas.
    offsets = [F(point['unix_ns']) - F(point['mono_before_ns'] + point['mono_after_ns'], 2)
               for r in records[1:-1] for point in (r['start'], r['end'])]
    widths = [point['mono_after_ns'] - point['mono_before_ns']
              for r in records[1:-1] for point in (r['start'], r['end'])]
    require(max(offsets) - min(offsets) + max(widths) <= doc['policy']['max_wall_offset_change_ns'],
            'wall clock step/slew or bracket width exceeds policy')
    output, totals = [], {}
    for r in records[1:-1]:
        if r['phase'] != 'measurement':
            continue
        start, end = r['start']['mono_after_ns'], r['end']['mono_before_ns']
        margin = u + boundary_error
        require(times[0] <= start - margin and end + margin <= times[-1], 'insufficient uncertainty-expanded coverage')
        energy = integrate(times, powers, start, end)
        duration = F(end - start, NS)
        components = {'meter': relative * energy + absolute * duration,
                      'interpolation': interpolation * duration,
                      'sample_clock': (1 + relative) * slope * u * duration,
                      'benchmark_boundary': F(2 * boundary_error, NS) * ((1 + relative) * pmax + absolute + interpolation)}
        error = sum(components.values())
        require(energy > 0 and error / energy <= max_relative, 'energy uncertainty exceeds policy')
        values = metrics(r['hashes'], duration, energy, error)
        item = {key: r[key] for key in ('sequence', 'version', 'repeat', 'hashes', 'digest')}
        item.update({'elapsed_ns': end - start, 'error_components_joules': {k: finite(v) for k, v in components.items()},
                     'energy_joules': None if synthetic else values['energy_joules'],
                     'hashes_per_joule': None if synthetic else values['hashes_per_joule'],
                     'synthetic_metrics' if synthetic else 'measurement_metrics': values})
        output.append(item)
        total = totals.setdefault(r['version'], [0, F(0), F(0), F(0)])
        for i, value in enumerate((r['hashes'], duration, energy, error)):
            total[i] += value
    grouped = {version: metrics(*values) for version, values in totals.items()}
    return {'schema_version': 1, 'status': 'validated-synthetic' if synthetic else 'validated-declared-measurement',
            'evidence_class': 'synthetic' if synthetic else 'operator-declared-measurement',
            'baseline_accepted': False, 'meter_evidence_independently_verified': False,
            'power_watts': None, 'hashes_per_joule': None,
            'physical_boundary': doc['boundary'], 'device_id': doc['device']['id'],
            'clock_uncertainty_bound_ns': finite(u), 'uncertainty_model': 'conditional worst-case bounds, not a confidence interval',
            'inputs_sha256': {name: sha(raw[name]) for name in NAMES},
            'steady_validator_sha256': sha(Path(steady.__file__).read_bytes()),
            'importer_sha256': sha(Path(__file__).read_bytes()),
            'benchmark_validation': checked, 'intervals': output,
            'synthetic_totals' if synthetic else 'measurement_totals': grouped,
            'limitations': ['Calibration, clock identity and uncertainty bounds are operator declarations, not certification.',
                            'No inference of host isolation, thermal equilibrium, meter bandwidth or unobserved spikes.',
                            'Only accepted measurement intervals; excludes initialization, controls and warmups.',
                            'Systematic error bounds are summed; version totals use total hashes / total energy.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--power', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory; existing evidence is never overwritten')
    parser.add_argument('--allow-synthetic', action='store_true')
    args = parser.parse_args(argv)
    try:
        args.output_dir.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        parser.error(str(exc))
    raw = {}
    report = {'schema_version': 1, 'status': 'failed', 'baseline_accepted': False,
              'power_watts': None, 'hashes_per_joule': None}
    try:
        for name in NAMES:
            source = args.power if name == 'power.json' else args.run_dir / name
            with source.open('rb') as handle:
                raw[name] = handle.read(LIMIT + 1)
            require(len(raw[name]) <= LIMIT, 'input exceeds 32 MiB; original left untouched: ' + name)
            (args.output_dir / name).write_bytes(raw[name])
        report = analyze(raw, args.allow_synthetic)
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        report['inputs_sha256'] = {name: sha(value) for name, value in raw.items() if len(value) <= LIMIT}
    report['invocation'] = {'run_dir': str(args.run_dir), 'power': str(args.power), 'allow_synthetic': args.allow_synthetic}
    report['python'] = sys.version
    (args.output_dir / 'energy-report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(args.output_dir / 'energy-report.json')
    return 0 if report['status'].startswith('validated-') else 1


if __name__ == '__main__':
    raise SystemExit(main())
