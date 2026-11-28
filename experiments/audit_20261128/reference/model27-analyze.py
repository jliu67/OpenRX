"""Split-load, finite-receiver scheduling of two carried native iterations."""
import collections,copy,dataclasses,difflib,hashlib,inspect,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;B=R.parent;T=B.parent;REPO=T/'openrx-shared-context-source-pr-20261127'
sys.path.insert(0,str(REPO))
from tools.architecture import scheduler as S,native_trace as N
START=time.monotonic()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def patch(original,diff):
 old=original.splitlines(True);lines=diff.splitlines(True);out=[];i=0;k=2
 while k<len(lines):
  m=re.match(r'@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@',lines[k]);need(m is not None,'closed source delta');start=int(m[1])-1;out+=old[i:start];i=start;k+=1
  while k<len(lines)and not lines[k].startswith('@@'):
   v=lines[k];k+=1
   if v[0]in' -':need(old[i]==v[1:],'exact pinned patch context');i+=1
   if v[0]in' +':out.append(v[1:])
 out+=old[i:];return ''.join(out)

class Receivers:
 def __init__(self,metadata,p):
  self.metadata=metadata;self.p=p;self.owned={s:{}for s in ['sp','ds']};self.tokens={};self.reads=collections.Counter();self.writes=collections.Counter();self.port_busy=collections.Counter();self.peaks=collections.Counter();self.stats=collections.Counter();self.events=[]
 def spec(self,space):return self.p['receiver'][space]
 def room(self,s,bank,t,read=0,write=0):
  spec=self.spec(s);return self.reads[s,bank,t]+self.writes[s,bank,t]+read+write<=spec['ports_1RW']
 def candidate(self,ctx,index,cycle,finish):
  m=self.metadata[ctx][index];role=m.get('role');s=m.get('pool','sp')
  if role not in ['load','convert','consume','peek']:return None,None
  token=m['token'];spec=self.spec(s)
  if role=='load':
   if len(self.owned[s])>=spec['entries']or sum(owner[0]==ctx for owner in self.owned[s].values())>=spec['per_context']:return 'load_queue_capacity',None
   free=[q for q in range(spec['entries'])if q not in self.owned[s]]
   for q in free:
    if self.room(s,q%spec['banks'],finish,write=1):return None,q
   return 'receiver_write_port',None
  q=self.tokens[ctx,s,token];bank=q%spec['banks']
  if not self.room(s,bank,cycle,read=1):return 'receiver_read_port',None
  if role=='convert'and not self.room(s,bank,finish,write=1):return 'receiver_write_port',None
  return None,q
 def issue(self,ctx,index,cycle,finish,q):
  m=self.metadata[ctx][index];role=m.get('role');s=m.get('pool','sp')
  if role not in ['load','convert','consume','peek']:return
  token=m['token'];bank=q%self.spec(s)['banks'];self.events.append(dict(context=ctx,index=index,role=role,pool=s,token=token,slot=q,issue=cycle,complete=finish))
  if role=='load':
   self.owned[s][q]=(ctx,token);self.tokens[ctx,s,token]=q;self.writes[s,bank,finish]+=1;self.port_busy[finish]+=1
   self.peaks[s]=max(self.peaks[s],len(self.owned[s]));self.stats[s+'_loads']+=1
  else:
   self.reads[s,bank,cycle]+=1;self.port_busy[cycle]+=1
   if role=='convert':self.writes[s,bank,finish]+=1;self.port_busy[finish]+=1
   if role=='consume':del self.owned[s][q];del self.tokens[ctx,s,token]
 def busy(self,t):return bool(self.port_busy[t])

def adapter():
 original=inspect.getsource(S.simulate);base=patch(original,(B/'model25/scheduler-adapter.diff').read_text());text=base
 a='        return None, (slot, finish, mem_plan)';b='        reason, receiver_slot = RX.candidate(ctx, index, cycle, finish)\n        if reason:\n            return reason, None\n        return None, (slot, finish, mem_plan, receiver_slot)'
 need(text.count(a)==1,'candidate extension anchor');text=text.replace(a,b)
 text=text.replace('ctx, index, (slot, finish, mem_plan) = choice','ctx, index, (slot, finish, mem_plan, receiver_slot) = choice',1)
 text=text.replace('            active_units[op.unit] += 1','            RX.issue(ctx, index, cycle, finish, receiver_slot)\n            active_units[op.unit] += 1',1)
 text=text.replace('        if op.barrier and (older_pending or any(i < index for i in inflight[ctx])):','        if op.barrier and (any(p.unit != "dataset" for p in older_pending) or any(i < index and programs[ctx][i].unit != "dataset" for i in inflight[ctx])):',1)
 text=text.replace('            if not future:\n','            if RX.busy(cycle):\n                future.append(cycle + 1)\n            if not future:\n',1)
 ns=dict(vars(S));ns['RF']=lambda regs:sum(len(r)>1 and r[0]in'rfea'and r[1:].isdigit()for r in regs)
 exec(compile(text,'<pinned-scheduler-finite-load-receivers>','exec'),ns)
 with(R/'scheduler-refinement.diff').open('x')as f:f.write(''.join(difflib.unified_diff(base.splitlines(True),text.splitlines(True),fromfile='model25/simulate',tofile='model27/simulate')))
 return ns

def traces():
 path=B/'trace26/actual01/native-prefix.stdout';groups={};ks={};ds={};headers={};ends={}
 receipt=json.loads((B/'trace26/actual01/result.json').read_text());need(receipt['status']=='PREFIX_NATIVE_TRACE_PASS_PENDING_INDEPENDENT_REVIEW','actual reference trace pass')
 for line in path.read_text().splitlines():
  v=line.split();tag=v[0]
  if tag=='F':continue
  n=int(v[1],16)
  if tag=='H':headers[n]=v;continue
  key=n,int(v[2],16)
  if tag=='I':groups.setdefault(key,[]).append(v)
  elif tag=='K':ks[key]=v
  elif tag=='D':ds[key]=v
  elif tag=='B':ends[key]=v
 refs={v['nonce']:v for v in map(json.loads,(B/'nonces24/actual01/native-four-inputs.stdout').read_text().splitlines())}
 for n in [0,2]:
  p=refs[n]['first_program'];need(int(ds[n,0][3],16)==p['dataset_offset']+(p['initial_ma']&0x7fffffc0),'entry-known current dataset address')
  need(int(ds[n,1][3],16)==p['dataset_offset']+(p['initial_mx']&0x7fffffc0),'entry-known following dataset address')
 return groups,ks,ds,ends,refs

def make_program(n,groups,ks,ds,early,read_regs,following_at_entry):
 ops=[];meta=[];useful=0;port=0;arch=0
 def add(reads=(),writes=(),unit='integer',latency=1,memory=None,barrier=False,name='',role=None,token=None,pool='sp'):
  ops.append(S.MicroOp(tuple(reads),tuple(writes),unit,latency,memory,barrier,name,False));meta.append(dict(role=role,token=token,pool=pool))
 def load(token,address,reads=(),pool='sp'):
  add(reads,(token,), 'lsu'if pool=='sp'else'dataset',1,S.MemoryAccess('scratchpad'if pool=='sp'else'dataset',address,16 if pool=='sp'else 64),name='LOAD:'+token,role='load',token=token,pool=pool)
 def dsload(it,reads=()):load('ds%d'%it,int(ds[n,it][3],16),reads,'ds')
 if early:
  dsload(0)
  if following_at_entry:dsload(1)
 for it in [0,1]:
  previous=[]if it==0 else['iteration_done0'];entry='entry%d'%it;fence='entry_ready%d'%it
  add(previous+['r%d'%i for i in read_regs],(entry,),name='ENTRY_ADDRESS')
  line0,line1=int(ks[n,it][3],16),int(ks[n,it][4],16)
  for k in range(8):
   token='entry%d_%d'%(it,k);addr=(line0 if k<4 else line1)+(k%4)*16
   load(token,addr,[entry,'sp_order']);ops[-1]=dataclasses.replace(ops[-1],writes=(token,'sp_order'));useful+=16;port+=16
   regs=['r%d'%(2*k),'r%d'%(2*k+1)]if k<4 else[(('f'if k<6 else'e')+str(2*(k%2)+a))for a in range(2)]
   add([token]+(regs if k<4 else[]),regs,'integer'if k<4 else'convert',name='ENTRY_XOR_OR_CONVERT',role='consume',token=token)
  add((),(fence,),'control',barrier=True,name='ENTRY_FENCE')
  for step,v in enumerate(groups[n,it]):
   pc,word=int(v[4],16),int(v[6],16);d=N.decode(word);flag=int(v[9],16);lat=58 if d['kind']=='FDIV_M'else 57 if d['kind']=='FSQRT_R'else 3 if d['unit']in['multiply','float']else 1
   reads=d['reads']+[fence];writes=d['writes'];token='v%d_%d'%(it,step)
   if flag==1:
    fp_memory=d['kind']in['FADD_M','FSUB_M','FDIV_M'];address_reads=['r%d'%d['src']]if fp_memory or d['src']!=d['dst']else[]
    load(token,int(v[10],16)&~15,address_reads+[fence,'sp_order']);ops[-1]=dataclasses.replace(ops[-1],writes=(token,'sp_order'));port+=16;useful+=8
    reads=[r for r in reads if not(len(r)>1 and r[0]=='r'and r[1:].isdigit())or(not fp_memory and r=='r%d'%d['dst'])]
    data=token
    if d['kind']in['FADD_M','FSUB_M','FDIV_M']:
     data=token+'c';add([token],(data,),'convert',name='FP_MEMORY_CONVERT',role='convert',token=token)
    add(reads+[data],writes,d['unit'],lat,name=d['kind'],role='consume',token=token)
   elif flag==2:
    add(reads+['sp_order'],('sp_order',),'lsu',1,S.MemoryAccess('scratchpad',int(v[10],16)&~15,16,True),name=d['kind']);port+=16;useful+=8
   else:add(reads,writes,d['unit'],1 if d['nop']else lat,barrier=d['barrier'],name=d['kind'])
   arch+=1
  done='kernel%d'%it;add((),(done,),'control',barrier=True,name='KERNEL_FENCE')
  if not early:dsload(it,[done])
  elif it==0 and not following_at_entry:dsload(1,[done])
  for k in range(4):
   prior=[]if k==0 else['xor%d_%d'%(it,k-1)];regs=['r%d'%(2*k),'r%d'%(2*k+1)];token='ds%d'%it
   add(regs+[done,token]+prior,regs+['xor%d_%d'%(it,k)],name='DATASET_XOR128',role='consume'if k==3 else'peek',token=token,pool='ds')
  for k in range(4):
   add(['r%d'%(2*k),'r%d'%(2*k+1),'xor%d_3'%it,'sp_order'],('sp_order',),'lsu',1,S.MemoryAccess('scratchpad',line1+16*k,16,True),name='TAIL_R_STORE');useful+=16;port+=16
  rdone='R_stores%d'%it;add(['sp_order'],(rdone,),'control',name='R_STORE_FENCE')
  for key in range(4):
   for lane in range(4):add(['f%d'%lane,'e%d'%key,rdone],('f%d'%lane,),'aes',name='AES128_ROUND')
  aesdone='AES_done%d'%it;add((),(aesdone,),'control',barrier=True,name='AES_FENCE')
  for k in range(4):
   add(['f%d'%k,aesdone,'sp_order'],('sp_order',),'lsu',1,S.MemoryAccess('scratchpad',line0+16*k,16,True),name='TAIL_F_STORE');useful+=16;port+=16
  add((),('iteration_done%d'%it,),'control',barrier=True,name='ITERATION_END')
 return ops,meta,dict(nonce=n,architectural_instructions=arch,iterations=2,useful_SP_bytes=useful,port_SP_bytes=port,dataset_payload_bytes=128)

def config(p,n,width=2):
 units={k:S.UnitSpec(v,p['II'].get(k,1),p['nonpipelined'].get(k,True))for k,v in p['counts'].items()}
 return S.Config(n,width,False,16,units,{'scratchpad':S.MemorySpec(8,1,16,p['SP_response']-1,8,16,True),'dataset':S.MemorySpec(4,1,64,p['DS_response']-1,4,64,True,True)},'address')
def run(ns,programs,metadata,p,width=2):
 rx=Receivers(metadata,p);ns.update(RX=rx,LIMITS=p);out=ns['simulate'](programs,config(p,len(programs),width),capture_schedule=True)
 need(not any(rx.owned.values())and not rx.tokens,'all load receiver ownership drained')
 out['receiver_peaks']=dict(rx.peaks);out['receiver_events']=rx.events;return out

def regressions(ns,base):
 p=copy.deepcopy(base);p.update(context_queue=64,rf_reads=100,rf_writes=100);p['unit_credits']={k:100 for k in p['counts']}
 tiny=[S.MicroOp((),('r%d'%i,),'integer',2,name='independent')for i in range(4)];m=[[dict(role=None)for _ in tiny]]
 a=run(ns,[tiny],m,p);b=S.simulate(tiny,config(p,1),capture_schedule=True)
 for row in a['schedule']:row.pop('unit');row.pop('slot')
 a.pop('receiver_peaks');a.pop('receiver_events');need(a==b,'unchanged scheduler parity with inactive extra limits')
 starts=[]
 for ii,credit,expected in [(4,8,20),(1,8,11),(1,1,32)]:
  q=copy.deepcopy(base);q['nonpipelined']['divsqrt']=False;q['II']['divsqrt']=ii;q['unit_credits']['divsqrt']=credit
  ops=[S.MicroOp(('e%d'%i,),('e%d'%i,),'divsqrt',8,name='PIPE')for i in range(4)]
  o=run(ns,[ops],[[dict(role=None)for _ in ops]],q);need(o['cycles']==expected,'II and return-credit timing');starts.append([r['issue']for r in o['schedule']])
 # Independent DIV executes during a memory miss; loaded operand waits for return.
 q=copy.deepcopy(base);q['SP_response']=20
 ops=[S.MicroOp((),('lv',),'lsu',1,S.MemoryAccess('scratchpad',0,16),name='LOAD'),S.MicroOp(('lv','e0'),('e0',),'divsqrt',8,name='CONSUME'),S.MicroOp(('e1',),('e1',),'divsqrt',8,name='INDEPENDENT')]
 md=[[dict(role='load',pool='sp',token='lv'),dict(role='consume',pool='sp',token='lv'),dict(role=None)]]
 o=run(ns,[ops],md,q);by={r['name']:r for r in o['schedule']};need(by['INDEPENDENT']['complete']<by['LOAD']['complete']<=by['CONSUME']['issue'],'arithmetic reservation decoupled from load')
 # Returned data owns its only queue slot until consumed behind a busy DIV.
 q=copy.deepcopy(base);q['receiver']['sp'].update(entries=1,per_context=1)
 ops=[S.MicroOp(('e1',),('e1',),'divsqrt',20,name='BUSY'),S.MicroOp((),('a0v',),'lsu',1,S.MemoryAccess('scratchpad',0,16),name='L0'),S.MicroOp(('a0v','e0'),('e0',),'divsqrt',8,name='C0'),S.MicroOp((),('a1v',),'lsu',1,S.MemoryAccess('scratchpad',16,16),name='L1'),S.MicroOp(('a1v',),('r0',),'integer',1,name='C1')]
 md=[[dict(role=None),dict(role='load',pool='sp',token='a0v'),dict(role='consume',pool='sp',token='a0v'),dict(role='load',pool='sp',token='a1v'),dict(role='consume',pool='sp',token='a1v')]]
 o=run(ns,[ops],md,q);by={r['name']:r for r in o['schedule']};need(by['L0']['complete']<by['C0']['issue']<=by['L1']['issue'],'queue slot retained after response until consume');need(o['blocked_candidate_checks'].get('load_queue_capacity',0)>0,'queue pressure observed')
 # Same register and overlapping store/load survive an iteration boundary.
 q=copy.deepcopy(base);q['SP_response']=10
 ops=[S.MicroOp((),('e0',),'float',8,name='ITER0_WRITE'),S.MicroOp(('e0',),('e0',),'float',3,name='ITER1_READ'),S.MicroOp((),(),'lsu',1,S.MemoryAccess('scratchpad',0,16,True),name='ITER0_STORE'),S.MicroOp((),('z',),'lsu',1,S.MemoryAccess('scratchpad',0,16),name='ITER1_LOAD'),S.MicroOp(('z',),('r0',),'integer',1,name='USE')]
 md=[[dict(role=None),dict(role=None),dict(role=None),dict(role='load',pool='sp',token='z'),dict(role='consume',pool='sp',token='z')]]
 o=run(ns,[ops],md,q);by={r['name']:r for r in o['schedule']};need(by['ITER1_READ']['issue']>=by['ITER0_WRITE']['complete']and by['ITER1_LOAD']['issue']>=by['ITER0_STORE']['complete'],'carried RF and memory dependence')
 bank_issues=[]
 for banks in [1,2]:
  q=copy.deepcopy(base);q['counts']['integer']=2;q['receiver']['sp']['banks']=banks
  ops=[S.MicroOp((),(),'integer',20,name='BUSY0'),S.MicroOp((),(),'integer',20,name='BUSY1'),S.MicroOp((),('q0',),'lsu',1,S.MemoryAccess('scratchpad',0,16),name='L0'),S.MicroOp((),('q1',),'lsu',1,S.MemoryAccess('scratchpad',16,16),name='L1'),S.MicroOp(('q0',),('r0',),'integer',1,name='C0'),S.MicroOp(('q1',),('r1',),'integer',1,name='C1')]
  md=[[dict(role=None),dict(role=None),dict(role='load',pool='sp',token='q0'),dict(role='load',pool='sp',token='q1'),dict(role='consume',pool='sp',token='q0'),dict(role='consume',pool='sp',token='q1')]]
  o=run(ns,[ops],md,q,4);by={r['name']:r for r in o['schedule']};bank_issues.append([by['C0']['issue'],by['C1']['issue']])
 need(bank_issues[0][0]<bank_issues[0][1]and bank_issues[1][0]==bank_issues[1][1],'receiver1RW bank conflict and explicit second bank')
 return dict(tests_passed=8,pipeline_issue_sequences=starts,receiver_bank_consume_cycles=bank_issues,includes=['scheduler parity','II4','II1','one return credit','load/compute overlap','response-held load queue','carried RF/store-load ordering','receiver1RW bank arbitration'])

def union(intervals):
 end=-1;total=0
 for a,b in sorted(intervals):total+=max(0,b-max(a,end));end=max(end,b)
 return total
def main():
 manifest=json.loads((R/'inputs.json').read_text())
 for row in manifest['pins']:need(pin(Path(row['path']))==row,'source/input binding')
 need(pin(Path(S.__file__))['sha256']=='90a0943844addcdb3e3e00a9ceeeb6b42abcce7986f7be0a538c54a68d803beb','pinned scheduler')
 ns=adapter();base=manifest['resources'];tests=regressions(ns,base);groups,ks,ds,ends,refs=traces();rows=[]
 variants=[('DIV1-blocking',1,True,1,8),('DIV2-blocking',2,True,1,8),('DIV1-II8-credit8',1,False,8,8),('DIV1-II4-credit16',1,False,4,16),('DIV1-II1-credit16',1,False,1,16)]
 cases=[]
 for contexts,nonces in [(1,[0]),(1,[2]),(2,[0,2]),(4,[0,2,0,2])]:
  for label,count,blocking,ii,credit in variants:
   p=copy.deepcopy(base);p['counts']['divsqrt']=count;p['nonpipelined']['divsqrt']=blocking;p['II']['divsqrt']=ii;p['unit_credits']['divsqrt']=credit;cases.append((label+'-c%d-'%contexts+''.join(map(str,nonces)),nonces,p,True))
 for label,changes in [('SP10-DIV1',{}),('SP10-DIV1-II4',dict(pipe=True)),('SP10-II4-LQ1',dict(pipe=True,LQ1=True)),('SP10-II4-receiver2banks',dict(pipe=True,banks2=True)),('SP10-II4-credit8',dict(pipe=True,credit8=True)),('late-dataset-II4',dict(pipe=True,late=True))]:
  p=copy.deepcopy(base);p['SP_response']=10
  if changes.get('pipe'):p['nonpipelined']['divsqrt']=False;p['II']['divsqrt']=4;p['unit_credits']['divsqrt']=8 if changes.get('credit8')else 16
  if changes.get('LQ1'):p['receiver']['sp'].update(entries=1,per_context=1)
  if changes.get('banks2'):p['receiver']['sp']['banks']=2
  cases.append((label,[0,2],p,not changes.get('late',False)))
 for label,nonces,p,early in cases:
  selectors={}
  for n in nonces:
   entropy=bytes.fromhex(refs[n]['first_program']['entropy_bytes_hex']);v=int.from_bytes(entropy[96:104],'little');selectors[n]=[v&1,2|((v>>1)&1)]
  following_at_entry=early and len(nonces)*2<=p['receiver']['ds']['entries']
  built=[make_program(n,groups,ks,ds,early,selectors[n],following_at_entry)for n in nonces];programs=[x[0]for x in built];md=[x[1]for x in built];info=[x[2]for x in built]
  o=run(ns,programs,md,p);schedule=o.pop('schedule');rxevents=o.pop('receiver_events');n=len(nonces);arch=sum(v['architectural_instructions']for v in info)
  need(sum(r['name']=='ITERATION_END'for r in schedule)==n*2,'all carried iterations retired')
  metrics={}
  for unit,count in p['counts'].items():
   relevant=[v for v in schedule if v['unit']==unit];slots=collections.defaultdict(list)
   for v in relevant:slots[v['slot']].append((v['issue'],v['complete']))
   metrics[unit]=dict(operations=len(relevant),instances=count,II=p['II'].get(unit,1),nonpipelined=p['nonpipelined'].get(unit,True),active_fraction=sum(union(v)for v in slots.values())/(count*o['cycles']),mean_inflight_per_instance=sum(v['complete']-v['issue']for v in relevant)/(count*o['cycles']))
  fetchfloor=arch;cycles=max(o['cycles'],fetchfloor);hz=manifest['assumed_frequency_hz'];rate=n*2*hz/(cycles*16384);tiles=math.ceil(1000000/rate)
  load_starts={(v['context'],v['pool'],v['token']):v['issue']for v in rxevents if v['role']=='load'}
  data=dict(case=label,nonces=nonces,iterations_per_context=2,resources=p,early_dataset=early,following_dataset_at_entry=following_at_entry,issue_width_microops=2,**o,FU_metrics=metrics,architectural_instructions=arch,microops=sum(len(v)for v in programs),useful_SP_bytes=sum(v['useful_SP_bytes']for v in info),port_SP_bytes=sum(v['port_SP_bytes']for v in info),dataset_payload_bytes=128*n,receiver_payload_bits=p['receiver']['sp']['entries']*128+p['receiver']['ds']['entries']*512,receiver_owner_tag_bits_not_mapped=True,load_residence_clocks=[v['issue']-load_starts[v['context'],v['pool'],v['token']]for v in rxevents if v['role']=='consume'],nominal_at_assumed_frequency=dict(frequency_hz=hz,fetch_capacity_floor_cycles=fetchfloor,hash_equivalent_per_second_short_window=rate,ideal_linear_tiles_at_1MHs=tiles,private_SP_bytes_per_tile=n*2097152,private_SP_bytes_machine_at_1MHs=tiles*n*2097152),estimated_area=None)
  rows.append(data)
  with(R/'completed-rows.json').open('w')as f:json.dump(rows,f,separators=(',',':'));f.write('\n')
 for row in manifest['pins']:need(pin(Path(row['path']))==row,'post source/input integrity')
 result=dict(schema='openrx.model27.decoupled-loads.actual.v1',status='PENDING_INDEPENDENT_MODEL_RESULT_REVIEW',tests=tests,cases=rows,trace=dict(source=str(B/'trace26/actual01/native-prefix.stdout'),instructions=1538,nonces=[0,2],iterations_per_input=2,RF_round_SP_boundary_checks=4,branch_backedge=dict(nonce=2,iteration=1,pc=179,next_pc=178),full_hash_replays=0),assumptions=['Pinned scheduler/decoder reused with finite-resource adapter. Split memory loads reserve LSU/receiver credit, not arithmetic FU. FP conversions use explicit four-scalar converter group; converted128b remains in the same receiver slot until arithmetic issue.','Load receiver ownership persists after response and conversion until operand consumption. One1RW port/bank gates response writes, conversion reads/writes and arithmetic operand reads; DS512b line buffer has four128b slice reads before release. Payload, queues, RF ports and FU return credits are explicit; tag/control area remains uncharacterized.','Native RF names, rounding token and SP-order token carry across both iterations. Real retired PC sequence, branch repeats, memory addresses and operands come from the new prefix trace; RF/SP reference checks are external native checks, not a functional proof of this timing scheduler.','No arithmetic unit is held during load wait. All same-context SP events stay ordered through sp_order; different contexts share8 modeled banks/one16B/cycle fabric. Dataset has separate64B/cycle fabric and4 owned receiver credits; only current/following addresses proven entry-known are prefetched. Branch/iteration fences drain architectural operations while ignoring asynchronous readonly dataset packets.','Uniform SP response parameter applies to READS AND WRITES. DIV/SQRT latencies58/57 andFP/mul3 are modeling parameters based on earlier service spans, not characterized pipelines or measured latencies for these operands. II1 is an aggressive sensitivity, not proven feasible.','Default global RF2R2W, integer1/mul1/FP1281/DIV1281/LSU1/converter4lanes1/AES1281/dataset-request1;2MiB privateSP/context. All variants retain these resources except explicitly listed DIV count/II/credits and receiver changes; equal counts do not imply equal area.','Frontend fetch remains a one-word/cycle capacity floor only, not an integrated finite fetch/branch simulator. Native image initialization, program generation, reciprocal preparation and final hashing are outside warm two-iteration timing.','Nominal hash-equivalent and machine-SP values assume repeated short windows, illustrative1GHz and ideal linear replication. These are not full-hash or steady-state timings, physical frequency/capacity/bandwidth or whole-machine feasibility.'],missing=['Characterized mapped DIV and receiver-bank area/timing/energy/PVT/RC/load; pipeline depth and RF/credit/control costs.','Exact timing/occupancy from integrated fetch, cancellation/ownership wrap, complete hash progression and heterogeneous nonce population.','Full-system memory/controller/PHY, setup amortization, clock/leakage/VRM/PSU/cooling energy.2.5mJ/hash unvalidated.'],physical_acceptance=False,scientific_acceptance=False,physical_unknowns=117,wall_seconds=time.monotonic()-START,pins=manifest['pins'])
 with(R/'profile-and-scheduler.json').open('x')as f:json.dump(result,f,separators=(',',':'));f.write('\n')
 print(json.dumps(dict(status=result['status'],tests=tests['tests_passed'],cases=len(rows),wall_seconds=result['wall_seconds'])))
if __name__=='__main__':
    raise SystemExit('Reference source only: no workload route is published. Use normal independent review/admission.')
