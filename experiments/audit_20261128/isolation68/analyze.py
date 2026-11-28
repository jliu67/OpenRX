"""Closed activity/stat outputs only. No physical power/clock inference."""
import collections,json,re
from pathlib import Path
R=Path(__file__).resolve().parent

def need(v,message):
    if not v:raise ValueError(message)

def activity(raw):
    lines=raw.decode('ascii').splitlines();need(len(lines)==50,'48activity records+PASS+exact finish')
    values={}
    for line in lines[:48]:
        m=re.fullmatch(r'ACT id=(\d+) phase=(\d+) binary=(\d+) fourstate=(\d+)',line);need(m,'closed activity record')
        ident,phase,binary,four=map(int,m.groups());key=ident,phase
        need(0<=ident<16 and 1<=phase<=3 and key not in values,'unique activity identity')
        values[key]=dict(binary=binary,fourstate=four)
    need(lines[48]=='PASS isolation68 native=12 corners=192 op3=1 unknown_controls=3 unknown_valid=2 idle=64 held=32 reset_cancel=1 accepted=209 cycles=321','exact functional/control count')
    bench=R/'tb_compare.v';number=next(i for i,s in enumerate(bench.read_text().splitlines(),1)if '$finish;'in s)
    need(lines[49]==f'{bench}:{number}: $finish called at 3206000 (1ps)','exact source-bound completion')
    identities=json.loads((R/'activity-identities.json').read_bytes());summary=[]
    for phase in (1,2,3):
        for unit in ('add','mul'):
            for kind in ('inputs','outputs'):
                totals={}
                for variant in ('base','isolated'):
                    selected=[values[x['id'],phase]for x in identities if x['variant']==variant and x['unit']==unit and x['kind']==kind]
                    totals[variant]={key:sum(x[key]for x in selected)for key in ('binary','fourstate')}
                if phase in (1,3):
                    need(totals['base']['binary']>0,'stimulus really exercises inactive original block')
                    need(totals['isolated']==dict(binary=0,fourstate=0),'isolated known-idle/held block stable')
                summary.append(dict(phase=phase,unit=unit,kind=kind,**totals,
                    binary_reduction_fraction=None if totals['base']['binary']==0 else 1-totals['isolated']['binary']/totals['base']['binary']))
    return dict(native_result_vectors=12,native_flag_oracle=False,baseline_flags_equivalent=True,control_and_special_vectors=192,
        rows=summary,phases={'1':'idle/changing request bus','2':'accepted native+corner stream','3':'held reply/backpressured changing bus'},
        scope='Zero-delay RTL event transitions at recoded block inputs and result/flag outputs,both scalar lanes. X/Z transitions counted separately. No internal-cell capacitance,glitch timing,representative workload weighting or watts inference.')

def structural(directory):
    rows={}
    for name in ('baseline','isolated'):
        p=Path(directory)/(name+'-stat.json');need(p.stat().st_size<=65536,'bounded stat file')
        raw=p.read_text();d=json.loads(raw);design=d['design'];types=design['num_cells_by_type']
        need(design['num_processes']==0 and design['num_memories']==0,'lowered no-process/no-memory structure')
        need(not any('latch'in t.lower()for t in types),'no inferred latches')
        rows[name]=dict(cells=design['num_cells'],wire_bits=design['num_wire_bits'],generic_cells_by_type=types,
            sequential_cells={t:n for t,n in types.items()if 'dff'in t.lower()})
    need(rows['baseline']['sequential_cells']==rows['isolated']['sequential_cells'],'no new sequential cell state')
    return dict(variants=rows,cell_difference=rows['isolated']['cells']-rows['baseline']['cells'],
        scope='Hierarchical proc/opt/wreduce/check/stat-width generic operators. No TECHMAP,ABC,technology mapping,area,timing or power. Wide mux/operator counts are structural proxies only.')
