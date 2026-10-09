#!/usr/bin/env python3
"""Read-only progress capture for this attempt; partial counts are not acceptance."""
from pathlib import Path
import json,datetime
p=Path('/tmp/openrx-gem5-light-20261008-attempt2')
row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{str(f.relative_to(p)):f.stat().st_size for f in p.rglob('*') if f.is_file()}}
for f in p.glob('m5out/*terminal*'):
    raw=f.read_text();row['serial_tail']=raw[-1800:];row['openrx_markers']=[x for x in raw.splitlines() if 'OPENRX_' in x][-14:]
    records=[]
    for line in raw.replace('\r','').splitlines():
        if line.startswith('{'):
            try: records.append(json.loads(line))
            except ValueError: pass
    row['probe_rows_seen']=len(records)
    row['probe_checks']={}
    for name in ('runtime','hash'):
        marker='OPENRX_'+name.upper()+'_BEGIN\n'
        section=raw.replace('\r','').split(marker,1)[1] if marker in raw.replace('\r','') else ''
        section=section.split('OPENRX_'+name.upper()+'_END',1)[0]
        rows=[]
        for line in section.splitlines():
            if line.startswith('{'):
                try: rows.append(json.loads(line))
                except ValueError: pass
        row['probe_checks'][name]={s:sum(r.get('type')=='check' and r.get('status')==s for r in rows) for s in ('pass','fail','skip')}
    row['stage_records']=[r for r in records if r.get('type')=='stage'];row['check_counts']={s:sum(r.get('type')=='check' and r.get('status')==s for r in records) for s in ['pass','fail','skip']}
if (p/'m5out/simulation.json').exists():row['simulation']=json.loads((p/'m5out/simulation.json').read_text())
row['host_processes']=[]
for process_path in Path('/proc').glob('[0-9]*'):
    try:
        if ((process_path/'comm').read_text().strip()=='gem5.opt'
                and str(p/'m5out').encode() in (process_path/'cmdline').read_bytes()):
            row['host_processes'].append({
                'observed_host_proc_pid':int(process_path.name),
                'status':[line for line in (process_path/'status').read_text().splitlines()
                          if line.startswith(('State:','VmRSS:','NSpid:'))]})
    except OSError:
        pass
out=Path('docs/validation/m3-fs/light-resume-20261008/monitor.jsonl')
with out.open('a') as h:h.write(json.dumps(row)+'\n')
print(json.dumps({k:v for k,v in row.items() if k not in ('serial_tail','files')},indent=2))
