#!/usr/bin/python3
"""Export bounded accepted-runtime evidence without changing original bytes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import socket

R=Path('$OPENRX_LOCAL_ROOT')
E=R/'migrations/20261009'
W=R/'checkouts/migration'
ID='20261009T193937Z-576aa858c033'
D=R/'executions'/ID
REVIEW_DIR=E/'independent-runtime-review-v1'
REVIEW_SHA='12db13426bddda29b7857f423e52fca0b87842c3225d81b2ec2cb3f793170bae'
OUT=W/'docs/validation/local-migration-20261009/actual-runtime-v1'
POST=E/'actual-runtime-postreview-integrity-20261009T200936398234Z.json'
POST_SHA='6fd8cdce385b1e2eee0c697eb750974c2c01e24eac65f39bd38d33b46327fcb2'
ALLOWED={
    'events.jsonl','manifest.json','payload/guest.sh','payload/m5out/board.platform.terminal',
    'payload/m5out/citations.bib','payload/m5out/config.ini','payload/m5out/config.json',
    'payload/m5out/device.dts','payload/m5out/simulation.json','payload/m5out/stats.txt',
    'payload/report.json','payload/runtime-stderr.log','payload/runtime.jsonl',
    'payload/stderr.log','payload/stdout.log','process-result.json','stderr.log','stdout.log',
    'submission-command.json','submission-result.json',
}

def sha(data):return hashlib.sha256(data).hexdigest()

def require(value,message):
    if not value:raise ValueError(message)

def fsyncdir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def write_new(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
    with os.fdopen(fd,'wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())

def main():
    review_path=REVIEW_DIR/'independent-runtime-review.json'
    require(sha(review_path.read_bytes())==REVIEW_SHA,'Independent accepted review changed')
    review=json.loads(review_path.read_bytes())
    require(review['execution_id']==ID and review['independent_review_accepted'] is True and
            review['activation_authorized'] is False and len(review['checks_completed'])==9 and
            all(record['passed'] is True for record in review['checks_completed']), 'Review scope not accepted')
    require(sha(POST.read_bytes())==POST_SHA,'Postreview cgroup/integrity receipt changed')
    receipt=json.loads((D/'receipt.json').read_bytes())
    require(receipt['execution_id']==ID and receipt['status']=='PROCESS_EXITED' and
            receipt['process']['returncode']==0 and not receipt['process']['signals'], 'Execution not successful')
    files=[];omitted=[]
    for item in receipt['artifacts']:
        source=Path(item['path']);relative=str(source.relative_to(D))
        require(not source.is_symlink() and source.is_file(),'Retained artifact not regular')
        raw=source.read_bytes()
        require(len(raw)==item['bytes'] and sha(raw)==item['sha256'],'Retained artifact changed')
        if relative=='payload/m5out/device.dtb':
            omitted.append({**item,'reason':'Small binary device-tree retained locally and digest-bound; text device.dts/config and full receipt exported'})
        elif relative=='runner.py':
            omitted.append({**item,'reason':'Duplicate exact988 immutable runner bytes already versioned in repository; execution-specific identity retained in manifest/receipt'})
        else:
            require(relative in ALLOWED,'Unexpected artifact requires privacy review: '+relative)
            files.append((source,'execution/'+relative))
    files.append((D/'receipt.json','execution/receipt.json'))
    files.extend([(E/'runtime-capture-summary.json','runtime-capture-summary.json'),
        (POST,'postreview-integrity.json'),(E/'actual_runtime_postreview_v1.py','actual_runtime_postreview_v1.py'),
        (Path(__file__).resolve(),'export_actual_runtime_v1.py'),
        (review_path,'independent-review/independent-runtime-review.json'),
        (REVIEW_DIR/'review-intent.json','independent-review/review-intent.json'),
        (REVIEW_DIR/'actual-pinned-ldd.log','independent-review/actual-pinned-ldd.log'),
        (REVIEW_DIR/'actual-pinned-build-info.log','independent-review/actual-pinned-build-info.log'),
        (E/'independent-runtime-review-v1-service.log','independent-review/service.log')])
    for index in range(1,10):
        files.append((REVIEW_DIR/('check-%02d.json'%index),'independent-review/check-%02d.json'%index))
    selected=[];hostname=socket.gethostname().encode();header_count=0
    hostname_token=re.compile(rb'(?<![A-Za-z0-9_.-])'+re.escape(hostname)+rb'(?![A-Za-z0-9_.-])')
    header=re.compile(rb'(?m)^(gem5 executing on )([^,\r\n]+)(, pid [0-9]+)')
    for source,target in files:
        require(not source.is_symlink() and source.is_file(),'Export source not regular')
        raw=source.read_bytes();raw.decode('utf-8')
        require(len(raw)<1024*1024,'Export source exceeds1MiB bound')
        transformed=raw;counts=[]
        for old,new in [(str(R).encode(),b'$OPENRX_LOCAL_ROOT'),
                        (b'$OPENRX_ORIGINAL_CHECKOUT',b'$OPENRX_ORIGINAL_CHECKOUT')]:
            count=transformed.count(old);counts.append(count);transformed=transformed.replace(old,new)
        matches=list(header.finditer(transformed));redactions=0
        if matches:
            require(target=='execution/payload/stdout.log','Unexpected hostname header location')
            require(len(matches)==1 and matches[0].group(2)==hostname,'Unexpected hostname header identity')
            transformed=header.sub(lambda match:match.group(1)+b'$OWNER_HOSTNAME_REDACTED'+match.group(3),transformed)
            redactions=len(matches);header_count+=redactions
        require(not hostname_token.search(transformed),'Physical hostname token remains: '+target)
        if target in ['execution/payload/runtime.jsonl','execution/payload/runtime-stderr.log',
                      'execution/payload/m5out/board.platform.terminal']:
            require(transformed==raw,'Scientific rows or raw serial require unexpected transformation')
        selected.append((source,target,raw,transformed,counts,redactions))
    require(header_count==1,'Exact one actual gem5 physical-hostname field expected')
    require(sum(len(item[2]) for item in selected)<2*1024*1024,'Export total exceeds2MiB bound')
    require(not OUT.exists(),'Refuse existing evidence namespace')
    OUT.mkdir(mode=0o755)
    directories={OUT,OUT.parent};rows=[]
    for source,target,raw,transformed,counts,redactions in selected:
        destination=OUT/target
        destination.parent.mkdir(mode=0o755,parents=True,exist_ok=True)
        directories.add(destination.parent)
        write_new(destination,transformed)
        require(source.read_bytes()==raw,'Original source changed during export')
        rows.append({'source':str(source.relative_to(R)),'public_path':target,
            'original_bytes':len(raw),'original_sha256':sha(raw),
            'public_bytes':len(transformed),'public_sha256':sha(transformed),
            'ordered_prefix_substitution_counts':counts,'gem5_physical_hostname_field_redactions':redactions,
            'raw_cr_count':raw.count(b'\r'),'public_cr_count':transformed.count(b'\r'),
            'raw_nul_count':raw.count(b'\0'),'public_nul_count':transformed.count(b'\0')})
    index={'schema':'openrx.actual-runtime.export.v1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'execution_id':ID,'state':'LOCAL_VALIDATING','migration_complete':False,'activation_authorized':False,
        'accepted_scope':'Expected pinned guest boot and original strict nine-case functional runtime smoke, source/input/output integrity, and actual model. Complete RandomX matrix, full dataset, calibrated timing, power, resume and cutover remain outside scope.',
        'method':'Exact ordered byte-prefix substitutions (local root first, original checkout second), followed only in the actual gem5 stdout by replacement of the one physical-hostname field in its exact gem5 executing on HEADER. No JSON reserialization, CR/NUL/newline change, scientific row change, trimming or other normalization.',
        'ordered_substitutions':[{'from':'designated local root absolute prefix','to':'$OPENRX_LOCAL_ROOT'},
                                {'from':'original checkout absolute prefix','to':'$OPENRX_ORIGINAL_CHECKOUT'}],
        'hostname_method':'Exact anchored byte pattern: ^(gem5 executing on )([^,\\r\\n]+)(, pid [0-9]+). Only captured group2 replaced by $OWNER_HOSTNAME_REDACTED; original SHA binds the retained host field without disclosing it.',
        'total_physical_hostname_fields_redacted':header_count,
        'original_guest_serial_and_runtime_rows_exported_byte_identically':True,
        'small_utf8_with_nul_note':'Raw serial UTF-8 contains retained NUL/CR bytes if present; no normalization was applied.',
        'omitted_retained_artifacts':[{**item,'path':str(Path(item['path']).relative_to(R))} for item in omitted],
        'independent_checker_source_reference':'../runtime-checker-v1/index.json (original final source97430d48... bound by accepted review)',
        'earlier_build_preflight_and_live_production_observations_reference':'../local-validating-live-v1/index.json',
        'limitations':review['limitations'],'remaining_gates':review['remaining_gates'],'files':rows}
    data=(json.dumps(index,indent=2,sort_keys=True)+'\n').encode();write_new(OUT/'index.json',data)
    for directory in sorted(directories,key=lambda path:len(path.parts),reverse=True):fsyncdir(directory)
    print(json.dumps({'directory':str(OUT),'files':len(rows),'total_original_bytes':sum(row['original_bytes'] for row in rows),
        'index_sha256':sha(data),'hostname_fields_redacted':header_count,
        'key_files':{row['public_path']:{'raw':row['original_sha256'],'public':row['public_sha256']}
                     for row in rows if row['public_path'] in {'independent-review/independent-runtime-review.json',
                         'execution/receipt.json','execution/payload/report.json','execution/payload/runtime.jsonl',
                         'execution/payload/m5out/board.platform.terminal','execution/payload/stdout.log','postreview-integrity.json'}}},indent=2))

if __name__=='__main__':main()
