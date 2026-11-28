"""Source-bound diagnostic/activity collector. No physical power/clock inference."""
import collections
import hashlib
import json
import re
from pathlib import Path

R = Path(__file__).resolve().parent
BENCH_SHA256 = '5e0fcb966dfcbf6cb1edc2e7dd7cf412f381c91272dac883968b3ad1e48cd60f'
IDENTITIES_SHA256 = 'e7650e5397025db796a623f2afc3a9058c6ed8651aaceb6dc067e9d13d8921c0'
PASS = 'PASS isolation68 native=12 corners=192 op3=1 unknown_controls=3 unknown_valid=2 idle=64 held=32 reset_cancel=1 accepted=209 cycles=321'
DEC = r'(0|[1-9][0-9]{0,9})'


def need(value, message):
    if not value:
        raise ValueError(message)


def identities():
    raw = (R / 'activity-identities.json').read_bytes()
    need(hashlib.sha256(raw).hexdigest() == IDENTITIES_SHA256, 'bound activity identities')
    return json.loads(raw)


def vector(value, width, known=False):
    need(len(value) == (width + 3) // 4 and re.fullmatch(r'[0-9a-fxXzZ]+', value), 'exact vector width/encoding')
    if known:
        need(not re.search('[xXzZ]', value), 'known vector required')
    if not re.search('[xXzZ]', value):
        need(int(value, 16) < 2 ** width, 'unused high bits must be zero')
    return value


def activity(raw, *, emitted_bench_path=None):
    """Default terminal binds this local bench. Explicit path is DATA audit use only.

    The audit path comes from its pinned compiler argv/source manifest, never
    from the output being tested. The bench bytes and line remain exact here.
    The production payload supplies no override.
    """
    need(type(raw) is bytes and len(raw) <= 16384, 'bounded simulation capture')
    need(raw.endswith(b'\n') and b'\r' not in raw and b'\x00' not in raw, 'exact LF record framing')
    lines = raw.decode('ascii').splitlines()
    need(len(lines) == 108, 'exact 40FIRST+16SNAP+2GATE+48ACT+PASS+finish')
    bench = R / 'tb_compare.v'
    need(hashlib.sha256(bench.read_bytes()).hexdigest() == BENCH_SHA256, 'bound diagnostic bench')
    number = next(i for i, s in enumerate(bench.read_text().splitlines(), 1) if '$finish;' in s)
    source = str(bench) if emitted_bench_path is None else emitted_bench_path
    need(type(source) is str and source.startswith('/') and '\n' not in source and '\r' not in source, 'exact emitted source path')
    need(lines[-2] == PASS, 'exact functional/control counts')
    need(lines[-1] == f'{source}:{number}: $finish called at 3206000 (1ps)', 'exact source-bound completion')
    ids = identities()
    widths = {x['id']: x['width'] for x in ids}
    values = {}
    for offset, ident in enumerate(range(16)):
        for phase in (1, 2, 3):
            line = lines[58 + offset * 3 + phase - 1]
            m = re.fullmatch(r'ACT id=' + str(ident) + r' phase=' + str(phase) + r' binary=' + DEC + r' fourstate=' + DEC, line)
            need(m, 'exact ordered unique activity identity')
            binary, four = map(int, m.groups())
            need(binary <= 2147483647 and four <= 2147483647, 'bounded integer activity count')
            if ident >= 8 and phase in (1, 3):
                need(binary == four == 0, 'isolated all-state-zero idle/held activity')
            values[ident, phase] = dict(binary=binary, fourstate=four)

    first = []
    counts = collections.Counter()
    last_time = -1
    # Fixed GATE/SNAP groups are indivisible in the source task. FIRST records
    # outside these groups may interleave across monitors in simulator order.
    index = 0
    for label, stamp in ((1, 27000), (2, 28000)):
        if label == 1:
            while index < 58 and lines[index].startswith('FIRST '):
                first.append(lines[index]); index += 1
        need(index < 58 and lines[index] == f'GATE label={label} time={stamp} accepted=0/0 add=0/0 mul=0/0', 'exact known disabled gate snapshot')
        index += 1
        for ident in range(8, 16):
            m = re.fullmatch(r'SNAP label=' + str(label) + r' id=' + str(ident) + r' time=' + str(stamp) + r' unknown=0 prior=([0-9a-f]+) value=([0-9a-f]+)', lines[index])
            need(m, 'exact ordered known snapshot identity')
            prior, value = m.groups()
            vector(prior, widths[ident], known=True)
            vector(value, widths[ident], known=True)
            need(prior == value, 'snapshot history equals current vector')
            index += 1
    while index < 58:
        need(lines[index].startswith('FIRST '), 'no extra diagnostic records')
        first.append(lines[index]); index += 1
    need(len(first) == 40, 'exact bounded FIRST count')
    need(len(set(first)) == len(first), 'no duplicated FIRST record')
    histories = {}
    startup_histories = {}
    for line in first:
        m = re.fullmatch(r'FIRST id=(8|9|1[0-5]) phase=(0|2) time=' + DEC + r' prior=([0-9a-fxXzZ]+) value=([0-9a-fxXzZ]+)', line)
        need(m, 'closed FIRST identity; no idle/held event')
        ident, phase, stamp = map(int, m.groups()[:3])
        prior, value = m.groups()[3:]
        need(last_time <= stamp <= 3206000, 'chronological bounded FIRST time')
        last_time = stamp
        vector(prior, widths[ident], known=phase == 2)
        vector(value, widths[ident], known=phase == 2)
        need(prior != value, 'FIRST must describe a real four-state vector change')
        if phase == 0:
            need(stamp == 0 or 2720000 <= stamp < 3206000, 'unmeasured FIRST phase timing')
            if ident in startup_histories and startup_histories[ident][0] == stamp:
                need(prior == startup_histories[ident][1], 'same-time unmeasured FIRST history')
            startup_histories[ident] = stamp, value
        else:
            need(676000 <= stamp < 2720000, 'accepted-stream FIRST phase timing')
            if ident in histories:
                need(prior == histories[ident], 'consecutive FIRST history')
            histories[ident] = value
        counts[ident, phase] += 1
    need(counts == collections.Counter({(i, p): n for i in range(8, 16) for p, n in ((0, 3), (2, 2))}), 'exact FIRST monitor/phase multiplicities')
    # Require every pre-snapshot FIRST at time zero and every later FIRST after
    # both snapshots; no settling time or monitor history is reset by parsing.
    split = next(i for i, line in enumerate(lines) if line.startswith('GATE '))
    need(all(' time=0 ' in line for line in lines[:split]), 'only startup FIRST before snapshots')
    need(all(int(re.search(r' time=([0-9]+) ', line)[1]) >= 28000 for line in lines[split + 18:58]), 'no retroactive FIRST after snapshots')

    summary = []
    for phase in (1, 2, 3):
        for unit in ('add', 'mul'):
            for kind in ('inputs', 'outputs'):
                totals = {}
                for variant in ('base', 'isolated'):
                    selected = [values[x['id'], phase] for x in ids if x['variant'] == variant and x['unit'] == unit and x['kind'] == kind]
                    totals[variant] = {key: sum(x[key] for x in selected) for key in ('binary', 'fourstate')}
                if phase in (1, 3):
                    need(totals['base']['binary'] > 0, 'stimulus exercises inactive original block')
                summary.append(dict(phase=phase, unit=unit, kind=kind, **totals,
                    binary_reduction_fraction=None if totals['base']['binary'] == 0 else 1 - totals['isolated']['binary'] / totals['base']['binary']))
    return dict(native_result_vectors=12, native_flag_oracle=False, baseline_flags_equivalent=True,
        control_and_special_vectors=192, accepted_pairs=209, cycles=321,
        diagnostics=dict(first=40, snapshots=16, gates=2, known_and_history_equal=True), rows=summary,
        scope='Source-bound zero-delay RTL boundary event activity, not switched capacitance, representative duty, watts, silicon area, timing or Fmax.')


def structural(directory):
    rows = {}
    for name in ('baseline', 'isolated'):
        p = Path(directory) / (name + '-stat.json')
        need(p.stat().st_size <= 65536, 'bounded stat file')
        d = json.loads(p.read_text()); design = d['design']; types = design['num_cells_by_type']
        need(design['num_processes'] == 0 and design['num_memories'] == 0, 'lowered no-process/no-memory structure')
        need(not any('latch' in t.lower() for t in types), 'no inferred latches')
        rows[name] = dict(cells=design['num_cells'], wire_bits=design['num_wire_bits'], generic_cells_by_type=types,
            sequential_cells={t: n for t, n in types.items() if 'dff' in t.lower()})
    need(rows['baseline']['sequential_cells'] == rows['isolated']['sequential_cells'], 'no new sequential cell state')
    return dict(variants=rows, cell_difference=rows['isolated']['cells'] - rows['baseline']['cells'],
        scope='Hierarchical proc/opt/wreduce/check/stat-width generic operators. No TECHMAP, ABC, technology mapping, area, timing or power.')
