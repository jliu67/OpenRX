#!/usr/bin/python3
import datetime, hashlib, json, os, pathlib, subprocess, sys, time, uuid
folder=pathlib.Path(__file__).resolve().parent
results=[]
def write_new(path, value):
    with path.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
for access in ['all','exec','none']:
    unit='openrx-notify-component-'+access+'-'+uuid.uuid4().hex[:10]+'.service'
    command=['systemd-run','--user','--quiet','--no-block','--unit',unit,'--property=Type=simple','--property=NotifyAccess='+access,'--property=TimeoutStopSec=3s','--property=KillMode=mixed','--property=MemoryMax=64M','--property=CPUQuota=10%','--property=TasksMax=16','--property=Restart=no','--property=NoNewPrivileges=yes','--property=UMask=0077','--property=ExecStopPost=/usr/bin/python3 '+str(folder/'notify-finalizer.py')+' '+str(folder)+' '+access,'/usr/bin/true']
    write_new(folder/(access+'-command.json'),{'command':command,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    launch=subprocess.run(command,capture_output=True,text=True)
    observations=[]
    while True:
        query=subprocess.run(['systemctl','--user','show',unit,'-p','ActiveState','-p','SubState','-p','Result','-p','ExecStopPost','-p','NotifyAccess','-p','TimeoutStopUSec','-p','MainPID','-p','ControlPID','-p','ControlGroup','-p','MemoryMax','-p','CPUQuotaPerSecUSec','-p','TasksMax'],capture_output=True,text=True)
        properties=dict(line.split('=',1) for line in query.stdout.splitlines() if '=' in line)
        observations.append({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'properties':properties,'returncode':query.returncode,'stderr':query.stderr})
        if properties.get('ActiveState') in ['inactive','failed']:
            break
        time.sleep(0.25)
    journal=subprocess.run(['journalctl','--user','-u',unit,'--no-pager','-o','short-iso'],capture_output=True,text=True)
    with (folder/(access+'-journal.log')).open('x') as stream:stream.write(journal.stdout);stream.flush();os.fsync(stream.fileno())
    events=[json.loads(line) for line in (folder/(access+'-finalizer.jsonl')).read_text().splitlines()]
    finished=[event for event in events if event['event']=='finished']
    expected=(properties['Result']=='success' and bool(finished) and finished[0]['elapsed']>=8) if access!='none' else (properties['Result']=='timeout' and not finished)
    record={'access':access,'unit':unit,'launch':{'returncode':launch.returncode,'stdout':launch.stdout,'stderr':launch.stderr},'observations':observations,'final_properties':properties,'finalizer_events':events,'expected_behavior_verified':expected,'commands':{'status':['systemctl','--user','show',unit],'journal':['journalctl','--user','-u',unit,'--no-pager','-o','short-iso']}}
    write_new(folder/(access+'-result.json'),record);results.append(record)
write_new(folder/'receipt.json',{'schema':'openrx.independent.systemd-notify-component.v1','completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'all_expected_behaviors_verified':all(item['expected_behavior_verified'] for item in results),'results':results,'scope':'Tiny isolated component fixtures only; no guest simulations. No worker service timeouts were changed.','upstream_primary_sources':['https://raw.githubusercontent.com/systemd/systemd/v249/src/core/service.c','https://raw.githubusercontent.com/systemd/systemd/v249/man/systemd.service.xml']})
print(json.dumps({'folder':str(folder),'passed':all(item['expected_behavior_verified'] for item in results),'summaries':[{'access':item['access'],'unit':item['unit'],'Result':item['final_properties'].get('Result'),'events':item['finalizer_events']} for item in results]},indent=2))
