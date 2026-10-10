#!/usr/bin/python3
import datetime, importlib.util, json, os, pathlib, sys, time
sys.dont_write_bytecode=True
folder=pathlib.Path(__file__).resolve().parent
root=pathlib.Path(sys.argv[1]); execution_id=sys.argv[2]
source=root/'executions'/execution_id/'runner.py'
loader=importlib.util.spec_from_file_location('verified_openrx_finalizer',source);runner=importlib.util.module_from_spec(loader);loader.loader.exec_module(runner)
def witness(event, **extra):
    with (folder/'finalizer-witness.jsonl').open('a') as out:
        out.write(json.dumps({'event':event,'monotonic':time.monotonic(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid(),**extra})+'\n');out.flush();os.fsync(out.fileno())
original_notify=runner.notify_finalizer_timeout
def witnessed_notify():
    result=original_notify();witness('timeout-notification-returned',sent=result);return result
runner.notify_finalizer_timeout=witnessed_notify
original_flush=runner.flush_retained
calls=0
def delayed_flush(directory, retained):
    global calls
    calls+=1
    if calls==1:
        witness('controlled-output-flush-delay-start',seconds=55)
        time.sleep(55)
        witness('controlled-output-flush-delay-finished')
    return original_flush(directory, retained)
runner.flush_retained=delayed_flush
witness('private-finalizer-started',runner_path=str(source))
result=runner.main(['--root',str(root),'_finalize',execution_id])
witness('private-finalizer-returned',returncode=result)
sys.exit(result)
