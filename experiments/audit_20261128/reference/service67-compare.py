"""One bounded static-prefix sensitivity using unchanged service39/model27 engine."""
import ast,collections,copy,dataclasses,fcntl,hashlib,importlib.util,json,os,re,resource,signal,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;B=R.parent
ADAPTER_SHA='d0d13b59819d8d3e7546c70a2b0cfffe7aee85a5ed9fcff7347f2e073148ffd8'
HORIZON=30000
CASES=[];ACTIVE={}

def need(x,message):
    if not x:raise ValueError(message)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def function(path,name,scope):
    text=path.read_text();node=next(x for x in ast.parse(text).body if isinstance(x,ast.FunctionDef)and x.name==name)
    exec(compile(ast.get_source_segment(text,node),str(path)+'::'+name,'exec'),scope);return scope[name]

class StaticService:
    # Reuse the exact service39 finite parent-chain/port/backend algorithms.
    def __init__(self,profile,md,cap,shared):
        self.backend=shared.Backend(profile);self.md=md;self.cap=cap;self.port=shared.Port()
        self.memory=[];self.stats=collections.Counter();self.shared=shared;self.peaks=collections.Counter()
    def preview(self,ctx,index,cycle,basefinish):
        source=self.md[ctx][index]['source'];a=source['address'];space=source['space'];write=source['write'];size=source['size']
        need(size in ((64,)if space=='ds'else(8,16))and a%size==0 and a//64==(a+size-1)//64,'exact source width/alignment')
        pool='ds'if space=='ds'else'sp'
        active=[x for x in self.memory if x['ctx']==ctx and x['pool']==pool and not x['kind'].startswith('local')and x['release']>cycle]
        local=space=='sp'and a<self.cap
        if not local and len(active)>=2:return 'external_'+pool+'_credit',None
        port=self.port.clone();group=None
        if space=='sp':
            if port.busy(cycle):return 'shared_SP_transport_port',None
            port.book(cycle,1,ctx,'local_macro16'if local else'external_request_front16')
        if local:finish=basefinish;kind='local_write16'if write else'local_read16'
        else:
            # Unmerged64B traffic: external partial store performs owned RMW.
            # No assumption that timing-reordered requests can be coalesced.
            transactions=[(False,space,a//64*64)]
            if write:transactions.append((True,space,a//64*64))
            kind='dataset64'if space=='ds'else'backing_RMW64'if write else'backing_read64'
            arrival=cycle+1 if space=='ds'else basefinish+1
            reason,group=self.shared.Service.chain(self,cycle,arrival,transactions,ctx,port,False)
            if reason:return reason,None
            finish=max(group['finish'],basefinish)
            # Parent credit remains owned until the edge after usable return.
            group['state']['pending'][-1]=finish+1
            for row in group['rows']:row.update(owner_index=index,owner_pool=pool)
        return None,dict(finish=finish,release=finish+1,group=group,ctx=ctx,index=index,issue=cycle,
                         kind=kind,pool=pool,source=source,port=port)
    def commit(self,p):
        self.backend.commit(p['group']);self.port=p['port'];self.stats[p['kind']]+=1
        self.memory.append({k:p[k]for k in ('ctx','index','issue','finish','release','kind','pool','source')})
        for pool in ('ds','sp'):
            active=[x for x in self.memory if x['pool']==pool and x['kind']not in ('local_read16','local_write16')and x['release']>p['issue']]
            self.peaks[pool]=max(self.peaks[pool],len(active))
            need(all(sum(x['ctx']==c for x in active)<=2 for c in (0,1)),'two transport parents/context/class')

def profile(latency):
    # Abstract service response/ack ends L ns after backend acceptance absent
    # contention. Burst4ns is included in L; internal staging/feedback is extra.
    return dict(tick_ns=1,banks=8,queue=2,row_bytes=2048,RP_ns=0,RCD_ns=0,CL_ns=latency-4,
        CWL_ns=latency-4,RAS_ns=0,RTP_ns=0,WR_ns=0,CCD_ns=1,burst_ns=4,RTW_ns=1,WTR_ns=1,link_ns=0)

def attach_values(programs,md,groups,ks,ds,ends):
    for ctx,nonce in enumerate((0,2)):
        store=[x for it in (0,1)for x in groups[nonce,it]if int(x[9],16)==2];si=tr=tf=0
        for op,meta in zip(programs[ctx],md[ctx]):
            if op.memory is None:continue
            source=meta['source'];name=op.name;payload=None
            if source['space']=='ds':
                it=int(meta['token'][-1]);payload=ds[nonce,it][4]
            elif name.startswith('LOAD:entry'):
                it,k=map(int,re.fullmatch(r'LOAD:entry([01])_(\d+)',name).groups())
                data=bytes.fromhex(ks[nonce,it][7 if k<4 else 8]);payload=data[16*(k%4):16*(k%4+1)].hex()
            elif name.startswith('LOAD:v'):
                it,k=map(int,re.fullmatch(r'LOAD:v([01])_(\d+)',name).groups());v=groups[nonce,it][k]
                need(int(v[12],16)==int(v[13],16),'native read unchanged');payload=int(v[12],16).to_bytes(8,'little').hex()
            elif name=='ISTORE':
                v=store[si];si+=1;payload=int(v[13],16).to_bytes(8,'little').hex();source['before_hex']=int(v[12],16).to_bytes(8,'little').hex()
            elif name in ('TAIL_R_STORE','TAIL_F_STORE'):
                k=tr if name=='TAIL_R_STORE'else tf
                data=bytes.fromhex(ends[nonce,k//4][8]);offset=(0 if name=='TAIL_R_STORE'else 64)+16*(k%4)
                payload=data[offset:offset+16].hex()
                if name=='TAIL_R_STORE':tr+=1
                else:tf+=1
            need(payload is not None and len(bytes.fromhex(payload))==source['size'],'exact retained bytes for each request')
            source['value_hex']=payload

def schedule_check(programs,out,service,m):
    schedule=out['schedule'];by={(x['context'],x['index']):x for x in schedule}
    need(len(by)==sum(map(len,programs))==len(schedule),'all operations exactly once')
    edges=0;overlap_reads=0
    for ctx,ops in enumerate(programs):
        writers={};readers=collections.defaultdict(set);last_sp=None;known={}
        for i,op in enumerate(ops):
            x=by[ctx,i];need(x['complete']>x['issue']>=0 and x['complete']<HORIZON,'bounded positive operation')
            for reg in set(op.reads):
                if reg in writers:need(by[ctx,writers[reg]]['complete']<=x['issue'],'RAW');edges+=1
            for reg in set(op.writes):
                for older in readers[reg]|({writers[reg]}if reg in writers else set()):
                    need(by[ctx,older]['complete']<=x['issue'],'WAR/WAW');edges+=1
            for reg in set(op.writes):writers[reg]=i;readers[reg].clear()
            for reg in set(op.reads)-set(op.writes):readers[reg].add(i)
            if op.barrier:
                for j in range(i):
                    if ops[j].unit!='dataset':need(by[ctx,j]['complete']<=x['issue'],'precise older barrier')
                for j in range(i+1,len(ops)):need(by[ctx,j]['issue']>=x['complete'],'precise younger barrier')
        requests=[x for x in service.memory if x['ctx']==ctx and x['source']['space']=='sp']
        need([x['index']for x in requests]==sorted(x['index']for x in requests),'source SP order')
        for request in requests:
            if last_sp:need(last_sp['finish']<=request['issue'],'no overlapping same-context SP effects')
            last_sp=request;s=request['source'];a=s['address'];data=bytes.fromhex(s['value_hex'])
            before=bytes.fromhex(s['before_hex'])if 'before_hex'in s else b''if s['write']else data
            for j,value in enumerate(before):
                if a+j in known:need(known[a+j]==value,f'carried native SP bytes ctx={ctx} address={a+j:x} retained={value} prior={known[a+j]}');overlap_reads+=1
                else:known[a+j]=value
            if s['write']:
                # Full64B RMW must preserve every other known byte, including
                # overlap from earlier stores and the previous iteration.
                prior=dict(known);known.update({a+j:value for j,value in enumerate(data)})
                need(all(known[k]==v for k,v in prior.items()if not a<=k<a+len(data)),'RMW strobe preservation')
    for request in service.memory:
        need(by[request['ctx'],request['index']]['issue']==request['issue']and by[request['ctx'],request['index']]['complete']==request['finish'],'memory schedule/owner correspondence')
        rows=[v for v in service.backend.ledger if v['context']==request['ctx']and v['owner_index']==request['index']]
        expected=0 if request['kind'].startswith('local')else 2 if request['kind']=='backing_RMW64'else 1
        need(len(rows)==expected,'owned child transaction closure')
        if expected==2:need(not rows[0]['write']and rows[1]['write']and rows[1]['arrival']>rows[0]['response'],'ordered RMW children')
    need(all(x['end']<=y['start']for x,y in zip(service.backend.bus,service.backend.bus[1:])),'finite external data bus')
    need(len(service.port.used)==len(service.port.ledger),'unique shared16B beats')
    return dict(dependency_edges_checked=edges,previously_known_SP_bytes_checked=overlap_reads,all_operations_exactly_once=True,
        native_byte_effect_checks=True,arithmetic_recomputed=False,initial_unknown_bytes_lazily_bound=True)

def directed(shared):
    md=[[dict(source=dict(space='sp',address=1048584,size=8,write=False))]]
    small=StaticService(profile(50),md,1048576,shared);large=StaticService(profile(50),md,1572864,shared)
    old=repr(small.__dict__);why,a=small.preview(0,0,0,1);need(why is None and repr(small.__dict__)==old,'preview no side effects')
    _,b=large.preview(0,0,0,1);need(a['kind']=='backing_read64'and b['kind']=='local_read16','prefix changes only route')
    need(sum(x['stage']=='backing_read_merge_or_fill'for x in a['port'].ledger)==4,'four receive beats')
    small.commit(a);occupied=next(x['cycle']for x in small.port.ledger if x['stage']=='backing_read_merge_or_fill')
    need(small.preview(0,0,occupied,occupied+1)[0]=='shared_SP_transport_port','future capture beats block frontend')
    md[0][0]['source']['write']=True;s=StaticService(profile(100),md,1048576,shared);_,a=s.preview(0,0,0,1)
    need([x['write']for x in a['group']['rows']]==[False,True]and a['group']['rows'][1]['arrival']>a['group']['rows'][0]['response'],'RMW chain')
    md=[[dict(source=dict(space='ds',address=64*i,size=64,write=False))for i in range(3)]]
    s=StaticService(profile(50),md,1048576,shared)
    for i in range(2):why,a=s.preview(0,i,0,1);need(why is None,'two dataset parents');s.commit(a)
    need(s.preview(0,2,0,1)[0]=='external_ds_credit','third parent rejected')
    return dict(groups=5,preview_pure=True,prefix_route=True,future_port_conflict=True,RMW_ordered=True,third_credit_rejected=True)

def main():
    pins=json.loads((B/'service39/model-inputs.json').read_text())['pins']
    pins[str(B/'service39/service-adapter.py.txt')]=ADAPTER_SHA
    pins[str(B/'service39/scheduler-refinement.diff')]=sha(B/'service39/scheduler-refinement.diff')
    pins[str(B/'model27/inputs.json')]='1bd756b250474ec7e2558a31e3d1f384a88b6f77a3f862b030770815dc9ae762'
    for p,h in pins.items():need(sha(p)==h,'bound source '+p)
    m=load('service67_model27',B/'model27/analyze.py');shared=load('service67_shared',B/'service39/shared.py')
    ns=dict(vars(m.S));ns['RF']=lambda regs:sum(len(r)>1 and r[0]in'rfea'and r[1:].isdigit()for r in regs)
    exec(compile((B/'service39/service-adapter.py.txt').read_bytes(),'<unchanged-service39-scheduler>','exec'),ns)
    resources=json.loads((B/'model27/inputs.json').read_text())['resources'];resources=copy.deepcopy(resources)
    resources['DS_response']=resources['SP_response']=1
    resources['receiver']['ds'].update(entries=4,per_context=2);resources['receiver']['sp'].update(entries=4,per_context=2)
    resources['unit_credits']['dataset']=4
    tests=directed(shared);cases=CASES
    for window in ('early','later'):
        bundle=m.traces()if window=='early'else function(B/'service39/analyze.py','later_window',dict(R=B/'service39',json=json))()
        groups,ks,ds,ends,refs=bundle;built=[]
        for n in (0,2):
            entropy=bytes.fromhex(refs[n]['first_program']['entropy_bytes_hex']);v=int.from_bytes(entropy[96:104],'little');built.append((n,[v&1,2|((v>>1)&1)]))
        program=function(B/'service38/analyze.py','program',dict(m=m,groups=groups,ks=ks,ds=ds,built=built,dataclasses=dataclasses,re=re))
        programs,md=program(2);attach_values(programs,md,groups,ks,ds,ends)
        for L in (50,100,200):
            for cap in (1048576,1572864):
                ACTIVE.update(window=window,latency_ns=L,capacity_B=cap)
                svc=StaticService(profile(L),md,cap,shared);ns['MEM']=svc;out=m.run(ns,programs,md,resources)
                checks=schedule_check(programs,out,svc,m);end=max(out['cycles'],max(x['release']for x in svc.memory))
                if not cases:
                    bad=copy.deepcopy(out);target=svc.memory[0];next(x for x in bad['schedule']if x['context']==target['ctx']and x['index']==target['index'])['issue']+=1
                    try:schedule_check(programs,bad,svc,m)
                    except ValueError:tests['tampered_schedule_rejected']=True
                    else:raise ValueError('schedule negative control not rejected')
                need(end<HORIZON,'whole bounded window');metrics=svc.backend.metrics(end)
                need(metrics['all_responses_done']and metrics['bank_group_queue_peak']<=2,'finite drain/queue')
                beats=collections.Counter(x['stage']for x in svc.port.ledger)
                traffic={kind:sum(x['kind']==kind for x in svc.memory)for kind in svc.stats}
                perclass={s:dict(read64=sum(not x['write']and x['space']==s for x in svc.backend.ledger),write64=sum(x['write']and x['space']==s for x in svc.backend.ledger))for s in ('ds','sp')}
                events=out['receiver_events'];fu={u:sum(x['complete']-x['issue']for x in out['schedule']if x['unit']==u)/(end*resources['counts'][u])for u in ('divsqrt','float','integer')}
                ledger=dict(memory=svc.memory,backing=svc.backend.ledger,ports=svc.port.ledger)
                cases.append(dict(window=window,capacity_B=cap,assumed_service_ack_ns=L,cycles_including_drain=end,
                    context_completion_cycles=out['per_context_completion_cycles'],idle_cycles=out['idle_cycles'],blocked_candidate_checks=out['blocked_candidate_checks'],
                    FU_occupancy=fu,transport_parent_peaks=dict(svc.peaks),receiver_peaks=out['receiver_peaks'],traffic=traffic,external_classes=perclass,
                    shared16B_port_beats=dict(beats),shared16B_port_utilization=len(svc.port.used)/end,backend=metrics,schedule_checks=checks,
                    ledger_SHA256=hashlib.sha256(json.dumps(ledger,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                    local_physical16B_reads=traffic.get('local_read16',0),local_physical16B_writes=traffic.get('local_write16',0),
                    no_full_hash_extrapolation=True))
                need(sum(p.stat().st_size for p in R.rglob('*')if p.is_file())+589824<4194304,'retained envelope')
    for p,h in pins.items():need(sha(p)==h,'post source '+p)
    result=dict(schema='openrx.service67.static-window.v1',status='PASS_PENDING_INDEPENDENT_REVIEW',cases=cases,pins=pins,resources=resources,script_sha256=sha(Path(__file__)),directed_tests=tests,
        scope='Two actual nonce0/2 native source windows,program0/1 first2carried iterations. Unchanged service39 scheduler,bank/bus/port/parent-chain algorithms and native builder. Static route only; abstract timing parameters,not DRAM legality or calibration.',
        assumptions=['1ns scheduler tick; unchanged model27 FP/DIV58/57,multiply/FP3,2issue,2R2W RF,16entry issue span. No new physical clock,19cycle C910 claim or full-hash residence.',
          '8banks,2parent queue entries/bank,one external64B/4ns bus,1ns turnaround,zero row penalties; each50/100/200ns sensitivity is accept-to-full-burst/ack absent contention. Request launch,internal4x16B capture/launch,register feedback and queue delays add clocks. Dataset and backing own separate two-parent/context limits,share finite bus/bank queues.',
          'One shared16B frontend/transport port; local macro uses one beat,external request one frontend beat,each64B response/write staging four beats. Dataset also pays capture beats; original16B/64B receiver1RW banks and operand reads remain paid separately.',
          'Static local stores assume masked16B writes. Each unmerged external8/16B store performs read64-modify-write64,ordered source SP effects and strobe preservation. No cache,refill/writeback/tag RAM or future coalescing. Whole-hash capacity66 adjacency counts are not reused as window transactions.',
          'Transport credits free only after usable finish+1; load receivers separately retain ownership to consumption. Declared transport data+owner storage8x96B=768B,bank descriptors16x32B=512B,plus original receiver payload384B and uncharacterized RF/control/owner state.',
          'Trace builder combines shell8B source accesses into16B requests as in accepted model27; window macro counts use this existing interface and differ from capacity66 uncombined full-hash interface. Both candidates identical. End state/cancel/physical power not newly simulated.'],
        evidence_limits='Full schedules and memory ledgers checked in memory and hashed; bounded aggregate results retained,not full ledger bytes. Sparse read/write oracle binds initially unknown bytes from retained native values,checks known overlaps and RMW strobes; no arithmetic recomputation or entire scratchpad reconstruction. Candidate-check stalls overlap. No achieved fullhash rate,qualifiedHBM service,energy or production-equivalence assertion.',
        tests='No unrelated old qualification replay; source,dependency,barrier,SP byte/order,owner,queue,bus/port/drain checks execute on each exact case.',physical_acceptance=False)
    with(R/'RESULT.json').open('x')as f:json.dump(result,f,separators=(',',':'));f.write('\n')
    return result

if __name__=='__main__':
    raise SystemExit('Reference source only: no workload route is published. Use normal independent review/admission.')
