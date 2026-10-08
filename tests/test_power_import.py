"""Deterministic SYNTHETIC fixtures. No meters, native hashing, or real energy evidence."""
import copy
from fractions import Fraction as F
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import power_import as power
import steady_benchmark as steady

NS = power.NS
EPOCH = 1_791_430_000_000_000_000


def encode(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()


def fixture():
    config = dict(type='config', schema_version=1, pid=1, threads=1, init_threads=1,
                  nonces=1000, warmup_nonces=1000, repeats=2, min_seconds=1,
                  aes='hardware', flags=14, monotonic_resolution_ns=1, realtime_resolution_ns=1,
                  seed=0, versions=['v1', 'v2'], scheduler='static-stride-batch-first-next-last', power_watts=None)
    records = [config]
    plan = [('control', v, 0) for v in config['versions']]
    for repeat in (1, 2):
        for version in config['versions'] if repeat == 1 else list(reversed(config['versions'])):
            plan += [('warmup', version, repeat), ('measurement', version, repeat)]
    tick = 100 * NS + NS // 4
    def point(t):
        return dict(mono_before_ns=t, unix_ns=EPOCH + t + 5, mono_after_ns=t + 10)
    for seq, (phase, version, repeat) in enumerate(plan, 1):
        elapsed = 2 * NS if version == 'v1' else 4 * NS
        records.append(dict(type='interval', sequence=seq, phase=phase, version=version, repeat=repeat,
                            hashes=1000, digest=steady.REFERENCES[version], reference_matches=True, status='ok',
                            start=point(tick), end=point(tick + 10 + elapsed), elapsed_ns=elapsed))
        tick += elapsed + NS
    records.append(dict(type='complete', intervals=len(plan), invalid_intervals=0))
    stream = b''.join(encode(r) for r in records)
    expected = {k: config[k] for k in ('threads', 'init_threads', 'nonces', 'warmup_nonces', 'repeats', 'min_seconds', 'aes')}
    expected['versions'] = 'v1,v2'
    run = dict(schema_version=1, evidence_class='synthetic', purpose='SYNTHETIC TEST FIXTURE; NOT MEASURED',
               status='ok', returncode=0, configuration=expected, binary_sha256='0' * 64,
               vendor_integrity={'returncode': 0}, source_sha256={'scripts/steady_benchmark.py': power.sha(Path(steady.__file__).read_bytes())},
               raw_sha256={'adapter.jsonl': power.sha(stream), 'adapter.stderr': power.sha(b'')},
               summary=steady.validate(stream.decode()))
    raw = {'adapter.jsonl': stream, 'adapter.stderr': b'', 'run.json': encode(run)}
    doc = dict(schema_version=1, evidence_class='synthetic', benchmark_evidence='synthetic',
               binding={'adapter_sha256': power.sha(stream), 'run_sha256': power.sha(raw['run.json'])},
               device=dict(id='SYNTHETIC-ONLY', model='mathematical fixture, no device',
                           calibration_reference='Synthetic assumptions only, not calibration', max_watts=1000),
               boundary=dict(kind='whole_system_ac', description='Synthetic boundary; no physical system',
                             includes=['fictional host and PSU'], excludes=['fictional display']),
               units=dict(time='ns', power='W'), sample_semantics='instantaneous_active_power',
               synchronization=dict(method='affine_to_monotonic', source_clock='synthetic-meter-clock', target_clock='CLOCK_MONOTONIC',
                                    evidence_reference='Analytical fixture mapping; NOT a real synchronization',
                                    source_anchor_ns=EPOCH, target_anchor_ns=0, rate_correction_ppm=0,
                                    offset_bound_ns=1000, drift_bound_ppm=0.1, timestamp_bound_ns=1000,
                                    response_bound_ns=1000, valid_from_ns=EPOCH, valid_to_ns=EPOCH + 1000 * NS),
               uncertainty=dict(absolute_watts=0.5, relative_fraction=0.01, interpolation_bound_watts=0.5,
                                benchmark_boundary_bound_ns=100, rationale='Synthetic bounded-error model, no physical confidence claim'),
               policy=dict(max_gap_ns=2 * NS, max_clock_uncertainty_ns=1_000_000,
                           max_wall_offset_change_ns=1_000_000, max_relative_energy_error=0.2),
               samples=[dict(time_ns=EPOCH + i * NS, watts=100, status='ok') for i in range(99, 150)])
    raw['power.json'] = encode(doc)
    return raw


def amend(raw, path, value):
    doc = json.loads(raw['power.json'])
    target = doc
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    raw['power.json'] = encode(doc)
    return raw


def rebind(raw):
    doc = json.loads(raw['power.json'])
    doc['binding'] = {'adapter_sha256': power.sha(raw['adapter.jsonl']), 'run_sha256': power.sha(raw['run.json'])}
    raw['power.json'] = encode(doc)


def restream(raw, records):
    raw['adapter.jsonl'] = b''.join(encode(r) for r in records)
    run = json.loads(raw['run.json'])
    run['raw_sha256']['adapter.jsonl'] = power.sha(raw['adapter.jsonl'])
    run['summary'] = steady.validate(raw['adapter.jsonl'].decode())
    raw['run.json'] = encode(run)
    rebind(raw)


class ArithmeticTests(unittest.TestCase):
    def test_constant_clipped_boundaries(self):
        self.assertEqual(power.integrate([F(0), F(NS), F(3*NS)], [F(10)]*3, F(NS,4), F(9*NS,4)), 20)

    def test_linear_irregular_sampling(self):
        self.assertEqual(power.integrate([F(0), F(NS), F(3*NS)], [F(10),F(12),F(16)], F(NS,4), F(9*NS,4)), 25)

    def test_nanosecond_precision_at_large_epoch(self):
        a = 2**60
        self.assertEqual(power.integrate([F(a), F(a+2)], [F(10),F(30)], a, a+1), F(15,NS))

    def test_no_extrapolation(self):
        for start,end in [(-1,NS), (0,NS+1), (NS,0), (0,0)]:
            with self.subTest(start=start,end=end), self.assertRaises(ValueError):
                power.integrate([F(0),F(NS)], [F(10),F(10)], start,end)

    def test_additivity(self):
        rng = random.Random(106)
        for _ in range(20):
            t = [F(0), F(NS), F(3*NS), F(4*NS)]
            p = [F(rng.randrange(1,200)) for _ in t]
            self.assertEqual(power.integrate(t,p,0,4*NS),power.integrate(t,p,0,2*NS)+power.integrate(t,p,2*NS,4*NS))

    def test_error_interval(self):
        m=power.metrics(1000,F(2),F(200),F(10))
        self.assertEqual(m['hashes_per_joule'],5)
        self.assertAlmostEqual(m['hashes_per_joule_lower'],1000/210)
        self.assertAlmostEqual(m['hashes_per_joule_upper'],1000/190)
        with self.assertRaises(ValueError): power.metrics(1,F(1),F(1),F(1))


class ImportTests(unittest.TestCase):
    def test_synthetic_requires_opt_in(self):
        with self.assertRaisesRegex(ValueError,'allow-synthetic'): power.analyze(fixture())

    def test_synthetic_cannot_fill_measured_fields(self):
        result=power.analyze(fixture(),True)
        self.assertEqual(result['status'],'validated-synthetic')
        self.assertIsNone(result['hashes_per_joule'])
        self.assertNotIn('measurement_totals',result)
        self.assertFalse(result['baseline_accepted'])
        for item in result['intervals']:
            self.assertIsNone(item['energy_joules']); self.assertIsNone(item['hashes_per_joule'])
        self.assertEqual(len(result['intervals']),4)
        self.assertEqual(result['synthetic_totals']['v1']['energy_joules'],400)
        self.assertEqual(result['synthetic_totals']['v2']['energy_joules'],800)
        self.assertEqual(result['synthetic_totals']['v1']['hashes_per_joule'],5)

    def test_weighted_totals_not_mean_ratios(self):
        raw=fixture(); doc=json.loads(raw['power.json'])
        for s in doc['samples']: s['watts']=50+(s['time_ns']-EPOCH)/NS
        raw['power.json']=encode(doc)
        result=power.analyze(raw,True)
        v1=[r for r in result['intervals'] if r['version']=='v1']
        energies=[r['synthetic_metrics']['energy_joules'] for r in v1]
        self.assertAlmostEqual(result['synthetic_totals']['v1']['hashes_per_joule'],2000/sum(energies))
        errors=[r['synthetic_metrics']['absolute_error_bound_joules'] for r in v1]
        self.assertAlmostEqual(result['synthetic_totals']['v1']['absolute_error_bound_joules'],sum(errors))
        self.assertTrue(all(r['error_components_joules']['sample_clock']>0 for r in v1))

    def test_affine_origin_invariance(self):
        raw=fixture(); original=power.analyze(raw,True)
        doc=json.loads(raw['power.json']); shift=1234567890123
        for k in ('source_anchor_ns','valid_from_ns','valid_to_ns'): doc['synchronization'][k]+=shift
        for s in doc['samples']: s['time_ns']+=shift
        raw['power.json']=encode(doc)
        self.assertEqual(power.analyze(raw,True)['synthetic_totals'],original['synthetic_totals'])

    def test_rate_correction_sign(self):
        for rate in (-10,10):
            result=power.analyze(amend(fixture(),['synchronization','rate_correction_ppm'],rate),True)
            self.assertEqual(result['synthetic_totals']['v1']['energy_joules'],400)

    def test_declared_measured_branch_is_not_certification(self):
        # Entirely synthetic exercise of the measured-output branch; no result is evidence.
        raw=fixture(); run=json.loads(raw['run.json']); run.pop('evidence_class')
        raw['run.json']=encode(run); rebind(raw)
        amend(raw,['evidence_class'],'measured'); amend(raw,['benchmark_evidence'],'measured')
        result=power.analyze(raw)
        self.assertEqual(result['status'],'validated-declared-measurement')
        self.assertEqual(result['measurement_totals']['v1']['hashes_per_joule'],5)
        self.assertFalse(result['meter_evidence_independently_verified']); self.assertFalse(result['baseline_accepted'])

    def test_synthetic_benchmark_cannot_be_relabelled(self):
        with self.assertRaisesRegex(ValueError,'relabeled'):
            power.analyze(amend(fixture(),['benchmark_evidence'],'measured'),True)

    def test_missing_power_key(self):
        raw=fixture();doc=json.loads(raw['power.json']);del doc['samples'][0]['watts'];raw['power.json']=encode(doc)
        with self.assertRaises(ValueError):power.analyze(raw,True)

    def test_missing_coverage(self):
        raw=fixture();doc=json.loads(raw['power.json']);doc['samples']=doc['samples'][:10];raw['power.json']=encode(doc)
        with self.assertRaisesRegex(ValueError,'coverage'):power.analyze(raw,True)

    def test_zero_energy_rejected(self):
        raw=fixture();doc=json.loads(raw['power.json'])
        for s in doc['samples']:s['watts']=0
        raw['power.json']=encode(doc)
        with self.assertRaises(ValueError):power.analyze(raw,True)

    def test_power_gap(self):
        raw=fixture();doc=json.loads(raw['power.json']);del doc['samples'][5:8];raw['power.json']=encode(doc)
        with self.assertRaisesRegex(ValueError,'gap'):power.analyze(raw,True)

    def test_wall_step_between_trials(self):
        raw=fixture();records=[json.loads(x) for x in raw['adapter.jsonl'].splitlines()]
        for record in records[4:-1]:
            for key in ('start','end'):record[key]['unix_ns']+=10*NS
        restream(raw,records)
        with self.assertRaisesRegex(ValueError,'wall clock'):power.analyze(raw,True)

    def test_tampered_run_summary(self):
        raw=fixture();r=json.loads(raw['run.json']);r['summary']['controls_passed']=999;raw['run.json']=encode(r);rebind(raw)
        with self.assertRaisesRegex(ValueError,'summary'):power.analyze(raw,True)

    def test_corrupt_digest_before_power_join(self):
        raw=fixture();raw['adapter.jsonl']=raw['adapter.jsonl'].replace(steady.REFERENCES['v1'].encode(),b'0'*64)
        with self.assertRaisesRegex(ValueError,'digest mismatch'):power.analyze(raw,True)

    def test_incomplete_stream_even_after_rehash(self):
        raw=fixture();raw['adapter.jsonl']=raw['adapter.jsonl'].rsplit(b'\n',2)[0]+b'\n'
        run=json.loads(raw['run.json']);run['raw_sha256']['adapter.jsonl']=power.sha(raw['adapter.jsonl']);raw['run.json']=encode(run);rebind(raw)
        with self.assertRaises(ValueError):power.analyze(raw,True)

    def test_strict_json_duplicate_nonfinite_and_underflow(self):
        for data in (b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}'):
            with self.subTest(data=data),self.assertRaises(ValueError):power.decode(data,True)
        raw=fixture();raw['power.json']=raw['power.json'].replace(b'"watts": 100',b'"watts": 1e-1000')
        with self.assertRaises(ValueError):power.analyze(raw,True)

    def test_failed_benchmark(self):
        raw=fixture();run=json.loads(raw['run.json']);run['status']='rejected-duration';raw['run.json']=encode(run);rebind(raw)
        with self.assertRaisesRegex(ValueError,'did not succeed'):power.analyze(raw,True)

    def test_validator_revision_mismatch(self):
        raw=fixture();run=json.loads(raw['run.json']);run['source_sha256']['scripts/steady_benchmark.py']='0'*64;raw['run.json']=encode(run);rebind(raw)
        with self.assertRaisesRegex(ValueError,'revision mismatch'):power.analyze(raw,True)

    def test_bad_shape_is_cli_failure(self):
        self.run_cli(b'[]',1)

    def run_cli(self, power_bytes, expected):
        raw=fixture();raw['power.json']=power_bytes
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); source=root/'input';source.mkdir(); dest=root/'output'
            for name,data in raw.items():(source/name).write_bytes(data)
            cmd=[sys.executable,str(Path(power.__file__)),'--run-dir',str(source),'--power',str(source/'power.json'),
                 '--output-dir',str(dest),'--allow-synthetic']
            completed=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
            self.assertEqual(completed.returncode,expected,completed.stderr)
            report=json.loads((dest/'energy-report.json').read_text())
            for name,data in raw.items():self.assertEqual((dest/name).read_bytes(),data)
            repeated=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(repeated.returncode,0)
            self.assertEqual(json.loads((dest/'energy-report.json').read_text()),report)
            return report

    def test_cli_round_trip_and_no_overwrite(self):
        report=self.run_cli(fixture()['power.json'],0)
        self.assertEqual(report['status'],'validated-synthetic')

    def test_cli_preserves_failure(self):
        report=self.run_cli(b'{"samples":NaN}',1)
        self.assertEqual(report['status'],'failed');self.assertIsNone(report['hashes_per_joule'])


# One independently reported test per schema/quality rejection.
BAD = {
    'schema':(['schema_version'],True), 'evidence':(['evidence_class'],'estimated'),
    'units':(['units'],{'time':'ms','power':'W'}), 'sample_semantics':(['sample_semantics'],'interval_average'),
    'boundary':(['boundary','kind'],'cpu_package'), 'empty_boundary':(['boundary','includes'],[]),
    'model':(['device','model'],''), 'device_range':(['device','max_watts'],0),
    'negative_power':(['samples',0,'watts'],-1), 'over_range_power':(['samples',0,'watts'],1001),
    'missing_power':(['samples',0,'watts'],None), 'string_power':(['samples',0,'watts'],'100'),
    'boolean_power':(['samples',0,'watts'],True), 'quality':(['samples',0,'status'],'clipped'),
    'duplicate_time':(['samples',1,'time_ns'],EPOCH+99*NS),
    'reverse_time':(['samples',1,'time_ns'],EPOCH+98*NS),
    'float_time':(['samples',0,'time_ns'],float(EPOCH+99*NS)), 'negative_time':(['samples',0,'time_ns'],-1),
    'clock_method':(['synchronization','method'],'unknown'), 'clock_target':(['synchronization','target_clock'],'CLOCK_REALTIME'),
    'clock_evidence':(['synchronization','evidence_reference'],''), 'clock_range':(['synchronization','valid_to_ns'],EPOCH+NS),
    'clock_error':(['synchronization','offset_bound_ns'],100_000_000),
    'clock_drift':(['synchronization','drift_bound_ppm'],10001),
    'clock_rate':(['synchronization','rate_correction_ppm'],10001),
    'response_time':(['synchronization','response_bound_ns'],100_000_000),
    'zero_gap':(['policy','max_gap_ns'],0), 'fraction_limit':(['policy','max_relative_energy_error'],0.9),
    'excess_error':(['uncertainty','absolute_watts'],1000),
    'negative_interpolation':(['uncertainty','interpolation_bound_watts'],-1),
    'zero_boundary_error':(['uncertainty','benchmark_boundary_bound_ns'],0),
    'uncertainty_rationale':(['uncertainty','rationale'],''),
    'wrong_binding':(['binding','adapter_sha256'],'0'*64),
    'wrong_run_binding':(['binding','run_sha256'],'0'*64),
}

def reject_case(path,value):
    def test(self):
        with self.assertRaises(ValueError):power.analyze(amend(fixture(),path,value),True)
    return test

for name,(path,value) in BAD.items():
    setattr(ImportTests,'test_reject_'+name,reject_case(path,value))


if __name__=='__main__':
    unittest.main()
