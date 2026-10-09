#!/usr/bin/python3
import datetime, hashlib, importlib.util, json, os, pathlib, subprocess, sys, time
sys.dont_write_bytecode=True
folder=pathlib.Path(__file__).resolve().parent
source=folder/'local_execution.py';root=folder/'fixture-root'
loader=importlib.util.spec_from_file_location('independent_runner_integration',source);runner=importlib.util.module_from_spec(loader);loader.loader.exec_module(runner)
def binding(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def newjson(path,value):
    with path.open('x') as out:json.dump(value,out,sort_keys=True,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
expected='988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882'
if binding(source)['sha256']!=expected:raise ValueError('Snapshot does not match independently reviewed source')
runner.init(root)
original_command=runner.systemd_command
commands={}
def fixture_command(root_arg,directory,manifest):
    default=original_command(root_arg,directory,manifest)
    replacement={'--property=MemoryMax=6G':'--property=MemoryMax=64M','--property=MemorySwapMax=1G':'--property=MemorySwapMax=0','--property=CPUQuota=200%':'--property=CPUQuota=10%','--property=TasksMax=256':'--property=TasksMax=16'}
    actual=[('--property=ExecStopPost=/usr/bin/python3 '+str(folder/'delayed-finalizer.py')+' '+str(root)+' '+manifest['execution_id']) if word.startswith('--property=ExecStopPost=') else replacement.get(word,word) for word in default]
    commands.update(default=default,fixture=actual)
    newjson(folder/'service-commands.json',{'default':default,'fixture':actual,'purpose':'Reduced-resource tiny test, finalizer wrapper adds controlled55s delay and observes real snapshot notifications. Worker45sstop property unchanged.'})
    return actual
runner.systemd_command=fixture_command
started=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic()
execution_id=runner.submit(root,'independent-finalizer-delay-988cf13f','validation',folder,['/usr/bin/python3',str(folder/'payload.py'),'{execution_dir}/payload'],[folder/'payload.py'],validation_scope='lifecycle')
directory=runner.execution_dir(root,execution_id);manifest=json.loads((directory/'manifest.json').read_text());observations=[]
properties_to_query=['ActiveState','SubState','Result','ExecStopPost','NotifyAccess','TimeoutStopUSec','MainPID','ControlPID','ControlGroup','MemoryMax','MemorySwapMax','CPUQuotaPerSecUSec','TasksMax']
while True:
    command=['systemctl','--user','show',manifest['unit']]+['-p'+name for name in properties_to_query]
    status=subprocess.run(command,capture_output=True,text=True)
    props=dict(line.split('=',1) for line in status.stdout.splitlines() if '=' in line)
    observations.append({'elapsed':time.monotonic()-tick,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'properties':props,'query_returncode':status.returncode,'stderr':status.stderr})
    if props.get('ActiveState') in ['inactive','failed']:break
    time.sleep(1)
verified=runner.verify(root,execution_id)
witness=[json.loads(line) for line in (folder/'finalizer-witness.jsonl').read_text().splitlines()]
start_delay=next(item for item in witness if item['event']=='controlled-output-flush-delay-start')
end_delay=next(item for item in witness if item['event']=='controlled-output-flush-delay-finished')
notifications=[item for item in witness if item['event']=='timeout-notification-returned' and item['sent']]
beyond=[item for item in observations if item['elapsed']>45 and item['properties'].get('SubState')=='stop-post' and int(item['properties'].get('ControlPID','0'))>0]
receipt=json.loads((directory/'receipt.json').read_text());snapshot=binding(directory/'runner.py')
accepted=props.get('Result')=='success' and verified['integrity_verified'] and end_delay['monotonic']-start_delay['monotonic']>=55 and len(notifications)>=6 and bool(beyond) and props.get('TimeoutStopUSec')=='45s' and props.get('NotifyAccess')=='exec' and snapshot['sha256']==expected and receipt['scientific_acceptance']=='unverified'
journal=subprocess.run(['journalctl','--user','-u',manifest['unit'],'--no-pager','-o','short-iso'],capture_output=True,text=True)
with (folder/'unit-journal.log').open('x') as out:out.write(journal.stdout);out.flush();os.fsync(out.fileno())
newjson(folder/'receipt.json',{'schema':'openrx.independent.finalizer-extension-integration.v1','accepted':accepted,'started_at':started,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_seconds':time.monotonic()-tick,'execution_id':execution_id,'unit':manifest['unit'],'commands':commands,'sources':[binding(source),binding(folder/'delayed-finalizer.py'),binding(folder/'payload.py'),binding(pathlib.Path(__file__))],'snapshot':snapshot,'final_properties':props,'observations':observations,'witness':witness,'notifications':len(notifications),'actual_stop_post_observed_beyond_default_deadline':bool(beyond),'controlled_delay_seconds':end_delay['monotonic']-start_delay['monotonic'],'output_integrity':verified,'execution_receipt':binding(directory/'receipt.json'),'scope':'Actual final runner private CLI finalization; controlled delay represents slow I/O/hash work on tiny retained data. No guest simulation, production root, physical host reboot, full Codex shutdown, or real large dataset.'})
print(json.dumps({'accepted':accepted,'execution_id':execution_id,'unit':manifest['unit'],'elapsed_seconds':time.monotonic()-tick,'notifications':len(notifications),'delay_seconds':end_delay['monotonic']-start_delay['monotonic'],'beyond45s':bool(beyond),'final_properties':props,'output_integrity':verified},indent=2))
