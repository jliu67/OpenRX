#!/usr/bin/env python3
"""Independent mathematical/CLI review; every input here is SYNTHETIC.

The integration oracle uses a global hinge-spline antiderivative rather than
the importer's clipped segment/trapezoid implementation. No meter is accessed.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
import power_import as power
from test_power_import import fixture, encode, rebind, EPOCH

SEED = 2026100813
BASELINE = '3f06f87b970cd1f8fc06f06dff9e9aa06cb5aad4'


def oracle(times, powers, start, end):
    """Exact global spline primitive: slope changes form positive-part hinges."""
    assert times[0] <= start < end <= times[-1]
    slopes = [(b-a)/(y-x) for x,y,a,b in zip(times,times[1:],powers,powers[1:])]
    def primitive(t):
        x=t-times[0]
        return powers[0]*x + slopes[0]*x*x/2 + sum(
            (after-before)*max(F(0),t-knot)**2/2
            for knot,before,after in zip(times[1:-1],slopes,slopes[1:]))
    return (primitive(end)-primitive(start))/power.NS


def numerical_audit():
    rng=random.Random(SEED)
    integration_cases=bound_cases=serialization_cases=0
    for _ in range(500):
        # Large epochs, irregular nanosecond gaps and rational affine rate.
        origin=F(rng.choice([0,2**60,2**62]))
        rate=F(1)+F(rng.randrange(-10000,10001),1_000_000)
        times=[origin]
        for _ in range(rng.randrange(4,13)):
            times.append(times[-1]+rng.randrange(100_000_000,2_000_000_000)*rate)
        powers=[F(rng.randrange(20,1000),10) for _ in times]
        start=times[1]+(times[2]-times[1])*F(rng.randrange(1,99),100)
        end=times[-3]+(times[-2]-times[-3])*F(rng.randrange(1,99),100)
        energy=oracle(times,powers,start,end)
        assert power.integrate(times,powers,start,end)==energy
        integration_cases+=1
        u=F(rng.randrange(1,1_000_000));boundary=F(rng.randrange(1,100_000))
        absolute=F(1,2);relative=F(1,100);interpolation=F(1,4)
        pmax=max(powers)
        duration=(end-start)/power.NS
        slope=max(abs(b-a)/(y-x) for x,y,a,b in zip(times,times[1:],powers,powers[1:]))
        error=(relative*energy+absolute*duration+interpolation*duration
               +(1+relative)*slope*u*duration
               +2*boundary/power.NS*((1+relative)*pmax+absolute+interpolation))
        # Alternating extremal acquisition shifts, correlated/opposed meter
        # errors, residual waveform and both interval edge directions.
        for time_sign in (-1,1):
            actual_times=[t+time_sign*(-1)**i*u for i,t in enumerate(times)]
            for meter_sign in (-1,1):
                actual_powers=[p+meter_sign*(absolute+relative*p) for p in powers]
                for edge_sign in (-1,1):
                    actual_start=start+edge_sign*boundary
                    actual_end=end-edge_sign*boundary
                    for residual_sign in (-1,1):
                        actual=oracle(actual_times,actual_powers,actual_start,actual_end)
                        actual+=residual_sign*interpolation*(actual_end-actual_start)/power.NS
                        assert abs(actual-energy)<=error
                        bound_cases+=1
        report=power.metrics(1000,duration,energy,error)
        assert F(report['energy_lower_joules'])<=energy-error
        assert F(report['energy_upper_joules'])>=energy+error
        assert F(report['hashes_per_joule_lower'])<=F(1000)/(energy+error)
        assert F(report['hashes_per_joule_upper'])>=F(1000)/(energy-error)
        assert F(report['absolute_error_bound_joules'])>=error+abs(F(report['energy_joules'])-energy)
        serialization_cases+=1
    # Unlike constant traces, linear traces expose the affine rate sign and
    # units. Compare complete joined reports with a closed-form physical-time
    # polynomial integral, independently of the segment implementation.
    affine_cases=0
    for ppm in (-10000,-1000,-10,10,1000,10000):
        raw=fixture();doc=json.loads(raw['power.json'])
        doc['synchronization']['rate_correction_ppm']=ppm
        for sample in doc['samples']:
            sample['watts']=50+(sample['time_ns']-EPOCH)//power.NS
        raw['power.json']=encode(doc)
        report=power.analyze(raw,True)
        records=[json.loads(line) for line in raw['adapter.jsonl'].splitlines()]
        rate=F(1)+F(ppm,1_000_000)
        for interval in report['intervals']:
            record=records[interval['sequence']]
            a=F(record['start']['mono_after_ns']);b=F(record['end']['mono_before_ns'])
            expected=50*(b-a)/power.NS+(b*b-a*a)/(2*rate*power.NS**2)
            assert interval['synthetic_metrics']['energy_joules']==float(expected)
            assert interval['energy_joules'] is None and interval['hashes_per_joule'] is None
            affine_cases+=1
    return dict(seed=SEED,integration_oracle_cases=integration_cases,
                bounded_true_waveform_cases=bound_cases,outward_serialization_cases=serialization_cases,
                affine_linear_join_intervals=affine_cases)


def cli_audit(importer,label,expect_fixed):
    cases={}
    for case in ('versions-array','versions-null','rate-overflow','decimal-overflow'):
        raw=fixture()
        if case.startswith('versions-'):
            run=json.loads(raw['run.json'])
            run['configuration']['versions']=[] if case=='versions-array' else None
            raw['run.json']=encode(run);rebind(raw)
        elif case=='rate-overflow':
            raw['power.json']=raw['power.json'].replace(b'"rate_correction_ppm": 0',b'"rate_correction_ppm": 1e1000000')
        else:
            raw['power.json']=raw['power.json'].replace(b'"watts": 100',b'"watts": 1e999999999999999999999')
        with tempfile.TemporaryDirectory(prefix='openrx-independent-power-') as t:
            root=Path(t);source=root/'input';source.mkdir();output=root/'output'
            for name,data in raw.items():(source/name).write_bytes(data)
            command=[sys.executable,str(importer),'--run-dir',str(source),'--power',str(source/'power.json'),
                     '--output-dir',str(output),'--allow-synthetic']
            # A wrapper adds the existing module path for the historic copy.
            wrapper='import runpy,sys;sys.path.insert(0,sys.argv.pop(1));sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")'
            result=subprocess.run([sys.executable,'-c',wrapper,str(ROOT/'scripts')]+command[1:],
                                  text=True,capture_output=True,timeout=5)
            report_path=output/'energy-report.json'
            entry=dict(returncode=result.returncode,report_exists=report_path.exists(),stdout=result.stdout,
                       stderr=result.stderr,inputs_preserved=all((output/name).read_bytes()==data for name,data in raw.items()),
                       inputs_sha256={name:hashlib.sha256(data).hexdigest() for name,data in raw.items()})
            if report_path.exists():entry['report']=json.loads(report_path.read_text())
            assert result.returncode==1 and entry['inputs_preserved']
            assert report_path.exists()==expect_fixed
            if expect_fixed:
                assert 'Traceback' not in result.stderr
                assert entry['report']['status']=='failed' and entry['report']['hashes_per_joule'] is None
            else:assert 'Traceback' in result.stderr
            cases[case]=entry
    return dict(label=label,importer_sha256=hashlib.sha256(importer.read_bytes()).hexdigest(),cases=cases)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',default=BASELINE,help='Historical unpatched git revision')
    args=parser.parse_args()
    report=dict(evidence_class='synthetic',python=sys.version,baseline_revision=args.baseline,
                current_importer_sha256=hashlib.sha256(Path(power.__file__).read_bytes()).hexdigest(),
                mathematics=numerical_audit())
    baseline=subprocess.run(['git','show',args.baseline+':scripts/power_import.py'],cwd=ROOT,
                            check=True,capture_output=True).stdout
    with tempfile.TemporaryDirectory(prefix='openrx-power-baseline-') as t:
        path=Path(t)/'power_import_baseline.py';path.write_bytes(baseline)
        report['original_cli']=cli_audit(path,'original, changes required',False)
    report['fixed_cli']=cli_audit(Path(power.__file__),'patched, separate review required',True)
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':main()
