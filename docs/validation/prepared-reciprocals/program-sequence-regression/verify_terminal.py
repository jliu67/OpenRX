"""Require actual complete default regression gates before exporting evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

E=Path(__file__).resolve().parent
W=json.loads((E/'workspace.json').read_text())
R=Path(W.get('executed_source',W['root']))
Q=Path('/tmp/openrx-prepared-program-sequence-regression-01')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

resource=json.loads((E/'resource01.json').read_text())
assert resource['returncode']==0 and resource['owned_descendants_after_payload']==[]
assert not (Q/'failure.json').exists()
s=json.loads((Q/'summary.json').read_text())
assert s['profile_iterations']==4 and s['full_v2_requested'] is False and s['synthesis_requested'] is True
rtl={f'rtl-{v}-{t}' for v in (1,0) for t in (0,1)}|{'rtl-program-reset-1','rtl-program-reset-0','control','cancel','first'}
mapped={f'mapped-control-{v}-{t}' for v in (1,0) for t in (0,1)}|{'mapped-program-reset-1','mapped-program-reset-0','control-default','cancel','first'}
targets={'control-default','control-short','sequence-default'}
assert set(s['rtl'])==rtl and set(s['mapped'])==mapped and set(s['mapping'])==targets
assert s['invalid_parameters_rejected']==4
for key,row in s['mapped'].items():
    ref='control' if key=='control-default' else key.replace('mapped-control-','rtl-').replace('mapped-program-reset-','rtl-program-reset-')
    assert row['record']==s['rtl'][ref]['record'],key
for group in ('rtl','mapped'):
    for key,row in s[group].items():
        label=('rtl-'+key if group=='rtl' and key in {'control','cancel','first'} else
               'mapped-'+key if group=='mapped' and key in {'control-default','cancel','first'} else key)
        assert (Q/(label+'.log')).read_text().splitlines()[0]==row['record'],label
commands=json.loads((Q/'commands.json').read_text())
assert len({r['label'] for r in commands})==len(commands)
assert all(r.get('returncode')==0 and 'error' not in r for r in commands)
assert {r['label'] for r in commands if r['label'].startswith('synth-')}=={'synth-'+t for t in targets}
for programs,iterations in [(0,2048),(9,2048),(8,0),(8,2049)]:
    assert 'program_control_requires_PROGRAMS_1_to_8_and_ITERATIONS_1_to_2048' in (Q/f'invalid-{programs}-{iterations}.log').read_text()
generic={}
for target in targets:
    types=Counter()
    with (Q/f'netlist-{target}.json').open() as f:
        for line in f:
            m=re.fullmatch(r'\s*"type": "([^\"]+)",\s*\n?',line)
            if m:types[m.group(1)]+=1
    assert types and all(t.startswith('$_') for t in types),target
    stat=int(re.search(r'Number of cells:\s*(\d+)',(Q/f'stat-{target}.txt').read_text()).group(1))
    assert stat==sum(types.values())==s['mapping'][target]['num_cells'],target
    assert dict(sorted(types.items()))==s['mapping'][target]['num_cells_by_type'],target
    generic[target]={'cells':stat,'flops':s['mapping'][target]['flop_cells'],'generic_only':True}
retained=json.loads((E/'regression-source01.json').read_text())
assert all(sha(R/n)==v['sha256'] for n,v in retained['files'].items())
inputs=json.loads((Q/'inputs.json').read_text());assert all(sha(R/n)==h for n,h in inputs.items())
original=json.loads((R/'docs/validation/prepared-reciprocals/server/inputs.json').read_text())
assert len(original)==219 and all(sha(R/n)==h for n,h in original.items())
compat=json.loads((Q/'HardFloat-compile-view.json').read_text())
assert sha(R/compat['upstream_file'])==compat['upstream_sha256']
assert sha(Q/compat['view_file'])==compat['view_sha256'] and compat['all_other_bytes_unchanged']
extraction=json.loads((Q/'program-extraction.json').read_text())
assert sha(R/'vendor/randomx/src/virtual_machine.cpp')==extraction['source_sha256']
assert all(sha(Q/n)==h for n,h in extraction['generated_sha256'].items())
artifacts=json.loads((Q/'artifacts.sha256.json').read_text())
actual={p.relative_to(Q).as_posix() for p in Q.rglob('*') if p.is_file() and p.name!='artifacts.sha256.json'}
assert actual==set(artifacts) and all(sha(Q/n)==h for n,h in artifacts.items())
assert all(int(line.split()[1])==0 for line in resource['kernel_final']['memory.events'].splitlines() if line.split()[0] in {'oom','oom_kill','oom_group_kill'})
prior=json.loads((E/'rtl-prior-comparison01.json').read_text())
assert len(prior['records'])==9 and all(r['exact_match'] for r in prior['records'])
out={'status':'pass','rtl_checks':9,'mapped_checks':9,'actual_synthesis_targets':3,'invalid_parameter_guards':4,
     'positive_commands':len(commands),'unexpected_failures':0,'profile_iterations_per_program':4,'programs':8,
     'native_versions':[1,2],'full_v2_rerun':False,'all_mapped_pass_records_equal_rtl':True,'all9_rtl_records_equal_preserved_accepted_component':True,
     'generic_mappings':generic,'executed_source_files_unchanged':len(retained['files']),
     'driver_input_bindings':len(inputs),'all219_original_scientific_bindings_unchanged':True,
     'generated_compile_view_and_extracted_native_bodies_unchanged':True,'final_complete_output_manifest_files':len(artifacts),
     'full_pipeline_performance_accepted':False,'boundary':s['boundary'],'mapped_scope':s['mapped_scope'],
     'fixture_provenance':'Native fixtures and generated packed files retained in complete final manifest; no retrospective pre-use immutability claim.',
     'resource':{'wall_seconds':resource['wall_seconds'],'peak_bytes':int(resource['kernel_final']['memory.peak']),
                 'swap_peak_bytes':int(resource['kernel_final']['memory.swap.peak']),
                 'memory_events':resource['kernel_final']['memory.events'],'cpu_stat':resource['kernel_final']['cpu.stat']}}
(E/'terminal-pass01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2),flush=True)
