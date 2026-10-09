#!/usr/bin/python3
"""Read-only live observation of the already-submitted first runtime validation.

Never submits, signals, recovers, changes state, or invokes the simulator.
Writes one exclusive fsynced evidence record under the migration evidence root.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import select
import stat
import subprocess
import time

R = Path('$OPENRX_LOCAL_ROOT')
E = R / 'migrations/20261009'
S = R / 'checkouts/execution-b4b5ffc'
SPEC = R / 'requests/spec-issue-27-local-runtime-b4b5ffc-attempt-01.json'
SPEC_SHA = 'd11d6f4e5043e3d51a73a0ecf52fc8aa95eb459c6546e46d4136f78013da7972'
COMMIT = 'b4b5ffc5c5ee3f59e0e862a6979d265fd410d726'
RUNNER_SHA = '988cf13f4c9c954388fb7e9d44fda632910fde41ab78392294280f176c674882'
RUNNER = R / 'releases/runner-v1-988cf13f/local_execution.py'
G = R / 'builds/gem5-rebuild-03/gem5-c8222cc67a399bfc01e8658dd14b30d5bfd634f9/build/RISCV/gem5.opt'
BUILD_RESULT = E / 'build-attempt-03/build-result.json'
ID_FILE = E / 'runtime-execution-id.json'
PROPERTIES = ['LoadState','ActiveState','SubState','Result','MainPID','ControlGroup',
              'MemoryMax','MemorySwapMax','CPUQuotaPerSecUSec','TasksMax','Nice',
              'NoNewPrivileges','KillMode','KillSignal','NotifyAccess',
              'TimeoutStopUSec','Restart','UMask','ExecMainCode','ExecMainStatus']

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def binding(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Binding is not a regular unlinked file: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return {'path':str(path), 'bytes':path.stat().st_size, 'sha256':h.hexdigest()}

def require(value, message):
    if not value:
        raise ValueError(message)

def manager(unit):
    p = subprocess.run(['systemctl','--user','show',unit,
                        '--property='+','.join(PROPERTIES)],capture_output=True,text=True)
    result = {'query_returncode':p.returncode,'unit':unit}
    result.update(dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line))
    return result

def healthy(value):
    require(value['query_returncode']==0, 'Manager query failed')
    require(value.get('LoadState') in {'loaded','not-found'}, 'Unknown manager LoadState')
    require(value.get('ActiveState') in {'active','activating','deactivating','inactive','failed'},
            'Unknown manager ActiveState')
    return value.get('ActiveState') in {'active','activating','deactivating'}

def exclusive_record(result):
    result['finished_at'] = now()
    result['observer'] = binding(Path(__file__).resolve())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = E / ('runtime-live-production-observation-'+stamp+'.json')
    data = (json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    fd = os.open(E,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)
    print(json.dumps({'record':str(path),'sha256':hashlib.sha256(data).hexdigest(),
                      'accepted_architecture_observation':result['accepted_architecture_observation']}),flush=True)

def source_identity():
    p = subprocess.run(['git','--no-optional-locks','--no-replace-objects','-C',str(S),
                        'rev-parse','HEAD'],capture_output=True,text=True)
    require(p.returncode==0 and p.stdout.strip()==COMMIT,'Frozen source HEAD mismatch')
    items=[]
    for candidate in sorted(S.rglob('*')):
        relative=candidate.relative_to(S)
        if '.git' in relative.parts:
            continue
        require(not candidate.is_symlink(),'Frozen source symlink')
        require(candidate.stat().st_mode & 0o222 == 0,'Frozen source writable path')
        if candidate.is_file():
            item=binding(candidate); item.pop('path')
            items.append({'relative':str(relative),**item})
        else:
            require(candidate.is_dir(),'Frozen source special file')
    encoded=(json.dumps(items,sort_keys=True,separators=(',',':'))+'\n').encode()
    return {'path':str(S),'kind':'directory','files':items,
            'sha256':hashlib.sha256(encoded).hexdigest()}

def ppid_and_start(pid):
    text=(Path('/proc')/str(pid)/'stat').read_text()
    fields=text[text.rfind(')')+2:].split()
    return int(fields[1]),int(fields[19])

def socket_inodes(process):
    found=set()
    for fd in (process/'fd').iterdir():
        link=os.readlink(fd)
        match=re.fullmatch(r'socket:\[(\d+)\]',link)
        if match:
            found.add(match.group(1))
    return found

def own_socket_snapshot(process, owned):
    result=[]; mapped=set()
    # These proc tables cover a shared network namespace. Only matching
    # pinned-process FD-owned inodes are retained; no other host addresses,
    # ports, paths, socket rows, or environment are recorded.
    for protocol in ['tcp','tcp6','udp','udp6']:
        for line in (process/'net'/protocol).read_text().splitlines()[1:]:
            fields=line.split()
            if len(fields)>9 and fields[9] in owned:
                inode=fields[9]; mapped.add(inode)
                result.append({'inode':inode,'protocol':protocol,'state_hex':fields[3],
                               'is_tcp_listener':protocol.startswith('tcp') and fields[3]=='0A',
                               'endpoint_details_intentionally_omitted':True})
    for line in (process/'net/unix').read_text().splitlines()[1:]:
        fields=line.split()
        if len(fields)>6 and fields[6] in owned:
            inode=fields[6]; mapped.add(inode)
            result.append({'inode':inode,'protocol':'unix','flags_hex':fields[3],
                           'type_hex':fields[4],'state_hex':fields[5],
                           'is_unix_listener':bool(int(fields[3],16)&0x10000),
                           'socket_path_intentionally_omitted':True})
    return {'owned_socket_inodes':sorted(owned), 'matching_owned_rows':result,
            'unmapped_owned_socket_inodes':sorted(owned-mapped),
            'scope':'One live pinned-process FD snapshot, not a perpetual network guarantee; no other host socket rows retained'}

def observe(relative):
    directory=Path('/sys/fs/cgroup')/relative.lstrip('/')
    pids=sorted({int(pid) for f in directory.rglob('cgroup.procs') for pid in f.read_text().split()})
    expected=G.stat()
    for pid in pids:
        fd=None
        try:
            fd=os.pidfd_open(pid)
            poller=select.poll(); poller.register(fd,select.POLLIN)
            if poller.poll(0): continue
            process=Path('/proc')/str(pid)
            actual=(process/'exe').stat()
            if (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino): continue
            require((process/'exe').resolve()==G.resolve(),'Pinned process executable path mismatch')
            membership=(process/'cgroup').read_text().splitlines()
            require(any(line=='0::'+relative or line.startswith('0::'+relative+'/') for line in membership),
                    'Pinned process outside retained manager cgroup')
            parent,start=ppid_and_start(pid)
            stdin=os.readlink(process/'fd/0')
            before=socket_inodes(process)
            sockets=own_socket_snapshot(process,before)
            after=socket_inodes(process)
            require(not poller.poll(0),'Pinned process exited during observation')
            require((process/'exe').stat().st_ino==expected.st_ino,'Executable inode changed')
            require(ppid_and_start(pid)[1]==start,'Pinned process start identity changed')
            sockets['fd_snapshot_stable_during_read']=before==after
            return {'pid':pid,'parent_pid':parent,'start_ticks':start,'exe':str(G),
                    'exe_device':actual.st_dev,'exe_inode':actual.st_ino,
                    'cgroup_membership':membership,'pidfd_opened_while_live':True,
                    'pidfd_not_exited_before_or_after_reads':True,
                    'stdin_fd0':stdin,'sockets':sockets,'observed_at':now()}
        except (FileNotFoundError,ProcessLookupError):
            continue
        finally:
            if fd is not None: os.close(fd)
    return None

def main():
    evidence={'schema':'openrx.runtime.live-production-observation.v1','started_at':now(),
              'accepted_architecture_observation':False,'guest_correctness_accepted':False,
              'scientific_scope':'Manager/process/security architecture only; not boot, smoke, timing, or migration acceptance',
              'actions':'Read-only observation of existing pipeline; no submit, signal, recover, state, service, or GitHub mutation',
              'missing_evidence':[]}
    try:
        require(binding(SPEC)['sha256']==SPEC_SHA,'Owner request SHA mismatch')
        require(binding(RUNNER)['sha256']==RUNNER_SHA,'Immutable runner SHA mismatch')
        while not ID_FILE.exists():
            build=manager('openrx-migration-build03-20261009.service')
            pipeline=manager('openrx-migration-validation-pipeline-v3-20261009.service')
            build_live=healthy(build); pipeline_live=healthy(pipeline)
            if not pipeline_live:
                # Recheck the file after manager observation to avoid classifying
                # a concurrent ID publication as a terminal missing-ID event.
                if ID_FILE.exists(): break
                evidence.update(pipeline_terminal_without_id=True,build_unit=build,pipeline_unit=pipeline)
                evidence['missing_evidence'].append('Pipeline terminal before runtime execution ID was observable')
                exclusive_record(evidence); return
            print(json.dumps({'at':now(),'waiting_existing_pipeline':True,'build_active':build_live}),flush=True)
            time.sleep(30)
        identifier=json.loads(ID_FILE.read_text())['execution_id']
        require(re.fullmatch(r'\d{8}T\d{6}Z-[0-9a-f]{12}',identifier),'Execution ID schema mismatch')
        directory=R/'executions'/identifier
        manifest=json.loads((directory/'manifest.json').read_text())
        spec=json.loads(SPEC.read_text()); build=json.loads(BUILD_RESULT.read_text())
        require(manifest['execution_id']==identifier and manifest['unit']=='openrx-'+identifier+'.service',
                'Manifest namespace mismatch')
        require(manifest['request_key']==spec['request_key'] and manifest['validation_scope']=='guest-runtime-smoke',
                'Manifest fixed request mismatch')
        require(manifest['runner']['sha256']==RUNNER_SHA and binding(directory/'runner.py')['sha256']==RUNNER_SHA,
                'Actual execution runner differs')
        actual_source=source_identity()
        require(manifest['sources']==[actual_source], 'Actual immutable source manifest mismatch')
        binary=binding(G)
        require(binary['sha256']==build['binary_sha256'] and binary['bytes']==build['binary_bytes'],
                'Built simulator binding mismatch')
        require([i for i in manifest['inputs'] if i['path']==str(G)]==[binary],
                'Manifest simulator pin mismatch')
        require([i for i in manifest['inputs'] if i['path']==str(SPEC)]==[binding(SPEC)],
                'Manifest exact owner request pin mismatch')
        evidence.update(execution_id=identifier,manifest=binding(directory/'manifest.json'),
                        request_spec=binding(SPEC),source_commit=COMMIT,
                        source_directory_sha256=actual_source['sha256'],source_files=len(actual_source['files']),
                        runner=binding(directory/'runner.py'),built_simulator=binary,
                        build_result=binding(BUILD_RESULT),input_id_record=binding(ID_FILE))
        while True:
            unit=manager(manifest['unit']); live=healthy(unit)
            relative=unit.get('ControlGroup','')
            if relative:
                require(relative.startswith('/') and '..' not in Path(relative).parts and
                        relative.endswith('/'+manifest['unit']),'Manager retained cgroup namespace mismatch')
                observed=observe(relative)
                if observed:
                    evidence.update(actual_manager=unit,retained_cgroup=relative,pinned_live_simulator=observed)
                    mainpid=int(unit['MainPID']); parent,start=ppid_and_start(mainpid)
                    parentfd=os.pidfd_open(parent)
                    try:
                        parentpoll=select.poll();parentpoll.register(parentfd,select.POLLIN)
                        proc=Path('/proc')/str(parent)
                        parent_exe=str((proc/'exe').resolve())
                        parent_argv=(proc/'cmdline').read_bytes().split(b'\0')
                        is_user=(Path(parent_exe).name=='systemd' and b'--user' in parent_argv)
                        require(not parentpoll.poll(0),'Worker parent exited during observation')
                        evidence['worker_parent']={'worker_pid':mainpid,'worker_start_ticks':start,
                            'parent_pid':parent,'exe':parent_exe,'is_user_systemd':is_user,
                            'pidfd_opened_while_live':True,'environment_not_read':True,
                            'raw_commandline_intentionally_not_retained':True}
                    finally: os.close(parentfd)
                    console=directory/'payload/stdout.log'
                    message=b'Standard input is not a terminal, disabling listeners'
                    found=console.is_file() and message in console.read_bytes()
                    evidence['noninteractive_listener_notice']={'path':str(console),'present':found,
                        'exact_message':message.decode() if found else None,
                        'whole_console_intentionally_not_retained':'May contain physical hostname; raw remains in execution outputs'}
                    expected={'MemoryMax':str(6*1024**3),'MemorySwapMax':str(1024**3),
                        'CPUQuotaPerSecUSec':'2s','TasksMax':'256','Nice':'10',
                        'NoNewPrivileges':'yes','KillMode':'mixed','NotifyAccess':'exec',
                        'TimeoutStopUSec':'45s','Restart':'no','UMask':'0077'}
                    evidence['expected_actual_properties']=expected
                    for key,value in expected.items():
                        if unit.get(key)!=value: evidence['missing_evidence'].append('Actual property mismatch: '+key)
                    if not is_user: evidence['missing_evidence'].append('Worker parent not positively observed as user systemd')
                    if observed['stdin_fd0']!='/dev/null': evidence['missing_evidence'].append('Pinned simulator stdin not /dev/null')
                    sockets=observed['sockets']
                    if not sockets['fd_snapshot_stable_during_read']: evidence['missing_evidence'].append('Socket FD snapshot changed during read')
                    if sockets['unmapped_owned_socket_inodes']: evidence['missing_evidence'].append('Owned socket inodes not completely mapped')
                    if any(row.get('is_tcp_listener') or row.get('is_unix_listener') for row in sockets['matching_owned_rows']):
                        evidence['missing_evidence'].append('Pinned simulator listener actually observed')
                    evidence['accepted_architecture_observation']=not evidence['missing_evidence']
                    exclusive_record(evidence); return
            if not live:
                # This remains a missing live witness even if runtime correctness
                # subsequently passes; no re-launch is performed by this observer.
                evidence['terminal_unit']=unit
                evidence['missing_evidence'].append('Runtime terminal before a live pinned simulator was observed')
                exclusive_record(evidence); return
            time.sleep(0.2)
    except Exception as exc:
        evidence['missing_evidence'].append(type(exc).__name__+': '+str(exc))
        exclusive_record(evidence)

if __name__=='__main__':
    main()
