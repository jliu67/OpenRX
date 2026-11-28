"""Service38 backend reused; all SP frontend/readout/RMW/refill/WB beats share one16B port."""
import importlib.util,copy,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('bound_service38_backend',Path(__file__).parent.parent/'service38/backend.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
Backend=old.Backend
class Port:
 def __init__(self):self.used={};self.ledger=[]
 def clone(self):
  q=Port();q.used=dict(self.used);q.ledger=list(self.ledger);return q
 def busy(self,t):return t in self.used
 def book(self,t,beats,ctx,stage):
  for beat in range(beats):
   while self.busy(t):t+=1
   row=dict(cycle=t,context=ctx,stage=stage,beat=beat,bytes=16);self.used[t]=row;self.ledger.append(row);t+=1
  return t
class Service:
 def __init__(self,p,metadata,placement):
  self.backend=Backend(p);self.md=metadata;self.placement=placement;self.cache=[old.Spill()for _ in metadata];self.port=Port();self.memory=[];self.stats=collections.Counter();self.peaks=collections.Counter()
  if p.get('cold_spill',False):
   for c in self.cache:c.lines=[None]*256;c.seq=0
 def chain(self,cycle,arrival,tx,ctx,port,readout):
  mapped=[self.backend.address(ctx,s,a)for w,s,a in tx];bank=self.backend.bankrow(mapped[0])[0];assert all(self.backend.bankrow(a)[0]==bank for a in mapped)
  pending=[t for t in self.backend.banks[bank]['pending']if t>cycle]
  if len(pending)>=self.backend.p['queue']:return 'backing_bank_queue',None
  if readout:arrival=port.book(arrival,4,ctx,'dirty_cache_readout')
  temp=copy.copy(self.backend);temp.banks=list(self.backend.banks);temp.bus=list(self.backend.bus);temp.ledger=[];temp.groups=[]
  for write,space,a in tx:
   if write:arrival=port.book(arrival,4,ctx,'dirty_writeback_to_backing')
   state=dict(temp.banks[bank]);state['pending']=[];temp.banks[bank]=state
   reason,plan=temp.preview(cycle,[(write,space,a)],ctx,'spill_external',front_after=0,arrival=arrival);assert reason is None;temp.commit(plan);arrival=plan['finish']
   if not write:arrival=port.book(arrival,4,ctx,'backing_read_merge_or_fill')
   arrival+=1
  finish=arrival;state=dict(temp.banks[bank]);state['pending']=pending+[finish]
  return None,dict(bank=bank,state=state,bus=temp.bus,rows=temp.ledger,finish=finish,queue_peak=len(pending)+1)
 def preview(self,ctx,index,cycle,basefinish):
  source=self.md[ctx][index]['source'];a=source['address'];size=source['size'];space=source['space'];write=source['write'];cp=None;group=None;port=self.port.clone();kind='dataset'if space=='ds'else'local'
  if space=='ds':
   reason,group=self.backend.preview(cycle,[(False,'ds',a)],ctx,'dataset',arrival=cycle+1);finish=group['finish']if group else 0
  else:
   if port.busy(cycle):return 'shared_SP_port',None
   port.book(cycle,1,ctx,'frontend')
   if self.placement=='local'or a<262144:reason=None;finish=basefinish
   else:
    if self.cache[ctx].busy>cycle:return 'spill_cache_busy',None
    cp=self.cache[ctx].preview(a,size,write);kind=('spill_hit'if cp['tag_hit']else'spill_write_allocate_no_read')if not cp['transactions']else'spill_external'
    if cp['transactions']:reason,group=self.chain(cycle,basefinish+1,cp['transactions'],ctx,port,cp['eviction']);finish=group['finish']if group else 0
    else:reason=None;finish=basefinish+1
  if reason:return reason,None
  finish=max(finish,basefinish)
  return None,dict(finish=finish,group=group,cache=cp,ctx=ctx,index=index,issue=cycle,kind=kind,source=source,port=port)
 def commit(self,plan):
  self.backend.commit(plan['group']);self.port=plan['port']
  if plan['cache']is not None:self.cache[plan['ctx']].commit(plan['cache'],plan['finish'])
  self.stats[plan['kind']]+=1;self.memory.append({k:plan[k]for k in ['ctx','index','issue','finish','kind','source']})
 def port_metrics(self,end):
  assert len(self.port.used)==len(self.port.ledger) and all(r['cycle']<end for r in self.port.ledger)
  return dict(bytes_per_beat=16,ports=1,beat_counts=dict(collections.Counter(x['stage']for x in self.port.ledger)),occupied_cycles=len(self.port.used),utilization=len(self.port.used)/end,max_reserved_cycle=max(self.port.used,default=-1),exact_unique_cycle_reservations=True)
class ByteCache:
 """Directed data oracle companion: sector-lazy cache vs independent byte array; no RTL proof."""
 def __init__(self,initial):
  self.backing=bytearray(initial);self.reference=bytearray(initial);self.meta=old.Spill();self.meta.lines=[None]*256;self.meta.seq=0;self.data=[bytearray(64)for _ in range(256)];self.counts=collections.Counter();self.operations=0
 def evict(self,slot):
  v=self.meta.lines[slot]
  if v is None or not v['dirty']:return
  a=v['tag']*64
  if v['valid']!=255:
   merged=bytearray(self.backing[a:a+64]);self.counts['RMW_read64']+=1
   for k in range(8):
    if v['dirty']>>k&1:merged[k*8:k*8+8]=self.data[slot][k*8:k*8+8]
  else:merged=bytearray(self.data[slot])
  self.backing[a:a+64]=merged;self.counts['writeback64']+=1
 def access(self,a,size,payload=None):
  assert size in[8,16]and a%8==0 and a+size<=(a//64+1)*64 and 262144<=a and a+size<=len(self.backing)
  if payload is not None:assert len(payload)==size
  before_counts=self.counts.copy();p=self.meta.preview(a,size,payload is not None);slot=p['slot'];v=self.meta.lines[slot];hit=v is not None and v['tag']==a//64
  if not hit:self.evict(slot);self.data[slot]=bytearray(64)
  if payload is None:
   mask=((1<<(size//8))-1)<<((a%64)//8)
   if not hit or v['valid']&mask!=mask:
    fresh=bytearray(self.backing[a//64*64:a//64*64+64]);self.counts['fill_read64']+=1
    if hit:
     for k in range(8):
      if v['dirty']>>k&1:fresh[k*8:k*8+8]=self.data[slot][k*8:k*8+8]
    self.data[slot]=fresh
   out=bytes(self.data[slot][a%64:a%64+size]);assert out==bytes(self.reference[a:a+size]),'byte-valued read mismatch'
  else:self.data[slot][a%64:a%64+size]=payload;self.reference[a:a+size]=payload;out=None
  assert self.counts['RMW_read64']+self.counts['fill_read64']-before_counts['RMW_read64']-before_counts['fill_read64']==sum(not w for w,space,address in p['transactions'])
  assert self.counts['writeback64']-before_counts['writeback64']==sum(w for w,space,address in p['transactions'])
  self.meta.commit(p,0);self.operations+=1;return out
 def flush(self):
  for q in range(256):self.evict(q)
  assert self.backing==self.reference,'all backing bytes after dirty flush'
def directed_tests(BASE):
 # The future beats must block another frontend request, including a different context.
 md=[[{'source':dict(space='sp',address=300000,size=8,write=False)}],[{'source':dict(space='sp',address=0,size=8,write=False)}]]
 s=Service(dict(BASE,cold_spill=True),md,'tiered');before=repr(s.__dict__);why,p=s.preview(0,0,0,1);assert not why and not s.port.used and not s.backend.ledger;why,p2=s.preview(0,0,0,1);assert p['finish']==p2['finish'];s.commit(p)
 transfer=[x['cycle']for x in s.port.ledger if x['stage']!='frontend'];assert len(transfer)==4 and s.preview(1,0,transfer[0],transfer[0]+1)[0]=='shared_SP_port'
 why,p=s.preview(1,0,transfer[-1]+1,transfer[-1]+2);assert not why;s.commit(p);s.port_metrics(p['finish'])
 # Dirty eviction uses 4 readout beats + RMW receive4 + WB4 + refill4, all uniquely owned.
 c=s.cache[0];c.lines=[None]*256;c.seq=0
 for a in [327680+i*4096 for i in range(4)]:v=c.preview(a,8,True);c.commit(v,0)
 s.md[0][0]['source']['address']=327680+4*4096
 why,p=s.preview(0,0,1000,1001);assert not why;stages=collections.Counter(x['stage']for x in p['port'].ledger if x['cycle']>=1000)
 assert stages=={'frontend':1,'dirty_cache_readout':4,'backing_read_merge_or_fill':8,'dirty_writeback_to_backing':4};s.commit(p);assert len({x['cycle']for x in s.port.ledger})==len(s.port.ledger)
 # Per-bank group credit includes complete frontend drain, not just backing return.
 q=Service(dict(BASE,cold_spill=True,queue=1),md,'tiered');why,p=q.preview(0,0,0,1);assert not why;q.commit(p)
 assert q.backend.bankrow(q.backend.address(0,'sp',md[0][0]['source']['address']))[0]==q.backend.bankrow(q.backend.address(1,'ds',0))[0]
 assert q.backend.preview(0,[(False,'ds',0)],1,'credit')[0]=='backing_bank_queue'
 initial=bytes((i*17+(i>>8))&255 for i in range(2097152));d=ByteCache(initial);base=327680
 d.access(base,8,b'\x00\x01\x02\x03\x04\x05\x06\xff');d.access(base+8,8);d.access(base,8);d.access(base+16,16,bytes(range(16)));d.access(base+16,16)
 for i in range(1,6):d.access(base+i*4096+56,8,bytes([0xa0+i])*8)
 d.access(base,8);d.access(base+8,16)
 for i in range(1,6):d.access(base+i*4096+56,8)
 # Force a partial-dirty RMW whose untouched bytes remain distinct nonzero reference data.
 for i in range(6,12):d.access(base+i*4096+8,8,bytes([i])*8)
 for i in range(6,12):d.access(base+i*4096,16)
 rejects=0
 for a,z,payload in [(base,4,None),(base+1,8,None),(base+56,16,None),(base,8,b'bad')]:
  try:d.access(a,z,payload)
  except AssertionError:rejects+=1
  else:raise AssertionError('invalid boundary accepted')
 d.flush();assert d.counts['RMW_read64']>=5 and d.counts['writeback64']>=5 and rejects==4
 return dict(groups=5,future_shared_port_conflict=True,preview_side_effect_free=True,all17_dirty_miss_beats_owned=True,finite_credit_guard=True,byte_operations=d.operations,backing_bytes_compared=len(initial),data_transactions=dict(d.counts),bad_boundary_rejections=rejects,dirty_merge_RMW_exact_reference_array=True)
