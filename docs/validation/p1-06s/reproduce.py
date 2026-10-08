"""Session evidence audit: saved CI native data plus SYNTHETIC power only."""
import zipfile, json, re, sys, argparse
from pathlib import Path
from fractions import Fraction as F
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive', type=Path)
parser.add_argument('--output-dir', required=True, type=Path)
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=False)
import power_import as p
from test_power_import import fixture, encode, EPOCH
archive = args.archive
assert p.sha(archive.read_bytes()) == '1eacda6564e038bc5933b04bc5030b20b5373b629551e801a64e6bed946a6358'
ledger = {'commit': '2b28d6fb4604a2b861241d38678e24c8541aed02', 'run_id': 37726645625, 'job_id': 113146214930,
          'artifact_id': 11528236706, 'artifact_bytes': archive.stat().st_size, 'artifact_sha256': p.sha(archive.read_bytes()),
          'artifact_expires_utc': '2027-01-06T04:15:51Z', 'native_joins': []}
with zipfile.ZipFile(archive) as z:
    for n in ('build/validation/phase1-tests.log', 'build/validation/randomx-tests.log', 'build/validation/steady-native-tests.log'):
        text = z.read(n).decode()
        print(n, '\n', text[-450:])
        (args.output_dir / Path(n).name).write_bytes(z.read(n))
        ok = 'All tests PASSED' in text if 'randomx-tests' in n else bool(re.search(r'\nOK\s*$', text))
        # Match test outcomes, not test names such as test_pull_requests_skipped ... ok.
        assert ok and not re.search(r'\.\.\.\s+(skipped|ERROR|FAIL)\b|^FAILED\b', text, re.M), n
        ledger[n] = {'sha256': p.sha(z.read(n)), 'passed': len(re.findall(r'\.\.\. PASSED', text)) if 'randomx-tests' in n else int(re.search(r'Ran (\d+) tests', text).group(1)), 'skipped': 0}
    for n in z.namelist():
        if not n.endswith('run.json'):
            continue
        folder = n.rsplit('/', 1)[0]
        raw = {x: z.read(folder + '/' + x) for x in p.NAMES if x != 'power.json'}
        run = json.loads(raw['run.json'])
        records = [json.loads(x) for x in raw['adapter.jsonl'].splitlines()]
        assert run['git_revision']['stdout'].strip() == ledger['commit']
        doc = json.loads(fixture()['power.json'])
        doc['benchmark_evidence'] = 'measured'  # Native CI execution; not a controlled baseline.
        doc['binding'] = {'adapter_sha256': p.sha(raw['adapter.jsonl']), 'run_sha256': p.sha(raw['run.json'])}
        start = records[1]['start']['mono_before_ns'] // p.NS - 2
        end = records[-2]['end']['mono_after_ns'] // p.NS + 3
        doc['synchronization']['valid_to_ns'] = EPOCH + max(10000, end + 1) * p.NS
        doc['samples'] = [dict(time_ns=EPOCH + i * p.NS // 4, watts=123, status='ok') for i in range(start * 4, end * 4 + 1)]
        raw['power.json'] = encode(doc)
        root = args.output_dir / 'synthetic-native-joins' / Path(folder).name
        root.mkdir(parents=True, exist_ok=True)
        for name, by in raw.items():
            (root / name).write_bytes(by)
        entry = {'source_folder': folder, 'source_status': run['status'], 'power_class': 'synthetic', 'raw_sha256': {k: p.sha(v) for k, v in raw.items()}}
        try:
            result = p.analyze(raw, True)
            assert run['status'] == 'ok'
            (root / 'energy-report.json').write_text(json.dumps(result, indent=2) + '\n')
            expected = sum(F(r['elapsed_ns'], p.NS) * 123 for r in records[1:-1] if r['phase'] == 'measurement')
            observed = sum(r['synthetic_metrics']['energy_joules'] for r in result['intervals'])
            assert abs(observed - float(expected)) < 1e-9
            assert all(r['hashes_per_joule'] is None for r in result['intervals'])
            entry.update(result='validated-synthetic', measurements=len(result['intervals']), constant_integral_matches=True)
        except ValueError as ex:
            assert run['status'] != 'ok', str(ex)
            entry.update(result='rejected-as-expected', error=str(ex))
        ledger['native_joins'].append(entry)
(args.output_dir / 'ci-checks.json').write_text(json.dumps(ledger, indent=2) + '\n')
print('Verified ledger:', json.dumps(ledger, indent=2))
