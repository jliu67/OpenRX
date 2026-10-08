#!/usr/bin/env python3
"""Separate reviewer: synthetic input type/Decimal probes and compatibility."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests')]
import power_import as current
from test_power_import import fixture, encode, rebind

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def modify(raw, filename, path, value):
    doc=json.loads(raw[filename]);target=doc
    for key in path[:-1]: target=target[key]
    target[path[-1]]=value
    raw[filename]=encode(doc)
    if filename=='run.json': rebind(raw)
    return raw

def check_cli(raw, expected):
    with tempfile.TemporaryDirectory(prefix='openrx-separate-review-') as temp:
        root=Path(temp);src=root/'input';src.mkdir();out=root/'output'
        for name,data in raw.items(): (src/name).write_bytes(data)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code=current.main(['--run-dir',str(src),'--power',str(src/'power.json'),
                               '--output-dir',str(out),'--allow-synthetic'])
        result=json.loads((out/'energy-report.json').read_text())
        assert code==expected,(code,result)
        assert all((out/name).read_bytes()==data for name,data in raw.items())
        if expected:
            assert result['status']=='failed' and result['hashes_per_joule'] is None
        return result

def compare_accepted(raw, original):
    before=original.analyze(raw,True);after=current.analyze(raw,True)
    for result in (before,after): result.pop('importer_sha256')
    assert before==after
    check_cli(raw,0)
    return after['synthetic_totals']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',default='bac3a069',
                        help='Unpatched historical source revision; override for a local snapshot')
    args=parser.parse_args()
    baseline=subprocess.run(['git','show',args.baseline+':scripts/power_import.py'],cwd=ROOT,
                            check=True,capture_output=True).stdout
    cases=[];comparison=[]
    run_paths=[['schema_version'],['status'],['returncode'],['vendor_integrity'],
               ['vendor_integrity','returncode'],['binary_sha256'],['source_sha256'],
               ['source_sha256','scripts/steady_benchmark.py'],['raw_sha256'],
               ['raw_sha256','adapter.jsonl'],['configuration'],['summary']]
    run_paths += [['configuration',key] for key in
                  ('threads','init_threads','nonces','warmup_nonces','repeats','min_seconds','aes','versions')]
    power_paths=[['schema_version'],['evidence_class'],['benchmark_evidence'],['binding'],
                 ['binding','adapter_sha256'],['device'],['boundary'],['units'],['sample_semantics'],
                 ['synchronization'],['uncertainty'],['policy'],['samples'],['samples',0]]
    for parent in ('device','boundary','synchronization','uncertainty','policy'):
        for key in json.loads(fixture()['power.json'])[parent]: power_paths.append([parent,key])
    power_paths += [['samples',0,key] for key in ('time_ns','watts','status')]
    for filename,paths in [('run.json',run_paths),('power.json',power_paths)]:
        for path in paths:
            for value in (None,[],{},False,'invalid'):
                # Strings legitimate only for syntactic fields; 'invalid' is
                # still valid nonempty free text and is intentionally omitted.
                text_fields=('id','model','calibration_reference','description','source_clock',
                             'evidence_reference','rationale')
                if filename=='power.json' and path[-1] in text_fields and value=='invalid': continue
                if filename=='power.json' and path==['boundary','excludes'] and value==[]: continue
                result=check_cli(modify(fixture(),filename,path,value),1)
                cases.append({'file':filename,'path':path,'value':value,'error':result['error']})
    decimal_failures=[]
    replacements=[('rate_correction_ppm',token) for token in
                  ('1e1000000','-1e1000000','10000.000000000000000001',
                   '-10000.000000000000000001','0.0000000000000000001',
                   '-0.0000000000000000001','1e999999999999999999999','1e-999999999999999999999')]
    replacements += [('watts',token) for token in
                     ('1e1000000','-1e1000000','1e999999999999999999999',
                      '1e-999999999999999999999','0.0000000000000000001')]
    for field,token in replacements:
        raw=fixture();old=b'"rate_correction_ppm": 0' if field=='rate_correction_ppm' else b'"watts": 100'
        raw['power.json']=raw['power.json'].replace(old,('"'+field+'": '+token).encode())
        result=check_cli(raw,1)
        decimal_failures.append({'field':field,'token':token,'error':result['error']})
    with tempfile.TemporaryDirectory(prefix='openrx-baseline-review-') as temp:
        path=Path(temp)/'baseline.py';path.write_bytes(baseline)
        spec=importlib.util.spec_from_file_location('power_import_original',path)
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        comparison.append({'kind':'unmodified fixture','totals':compare_accepted(fixture(),original)})
        for token in ('-10000','10000','-9999.123456789012345678',
                      '9999.123456789012345678','0.000000000000000001',
                      '-0.000000000000000001','-0.0','0e1000000'):
            raw=fixture();raw['power.json']=raw['power.json'].replace(b'"rate_correction_ppm": 0',
                    ('"rate_correction_ppm": '+token).encode())
            comparison.append({'kind':'rate','token':token,'totals':compare_accepted(raw,original)})
        raw=fixture();raw['power.json']=raw['power.json'].replace(b'"watts": 100',b'"watts": 100.000000000000000000')
        comparison.append({'kind':'18-place power','totals':compare_accepted(raw,original)})
    report={'evidence_class':'synthetic','python':sys.version,'reviewer':'power_patch_review',
            'baseline_revision':args.baseline,'baseline_importer_sha256':hashlib.sha256(baseline).hexdigest(),
            'git_HEAD':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip(),
            'importer_sha256':digest(ROOT/'scripts/power_import.py'),
            'tests_sha256':digest(ROOT/'tests/test_power_import.py'),
            'probe_script_sha256':digest(Path(__file__)),
            'type_failures':cases,'decimal_failures':decimal_failures,
            'accepted_compatibility':comparison,'unhandled_errors':0}
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=='__main__':main()
