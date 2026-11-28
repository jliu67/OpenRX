"""Finite per-bank parent-request queues and 64B burst reservations; not HBM protocol simulator."""
import math,copy,collections
class Backend:
 def __init__(self,p):
  self.p=p;self.banks=[dict(row=None,cmd=0,pre=0,act=0,pending=[])for _ in range(p['banks'])];self.bus=[];self.ledger=[];self.groups=[];self.serial=0
 def ticks(self,x):return math.ceil(x/self.p['tick_ns'])
 def address(self,ctx,space,a):return (a+(1<<34))if space=='ds'else(a+ctx*2097152)
 def bankrow(self,a):return(a//64%self.p['banks'],a//64//self.p['banks']//(self.p['row_bytes']//64))
 def slot(self,bus,ready,write):
  dur=self.ticks(self.p['burst_ns']);t=ready;prior=None
  for x in bus:
   gap=self.ticks(self.p['WTR_ns']if prior and prior['write']else self.p['RTW_ns'])if prior and prior['write']!=write else 0
   if prior:t=max(t,prior['end']+gap)
   after=self.ticks(self.p['WTR_ns']if write else self.p['RTW_ns'])if write!=x['write']else 0
   if t+dur+after<=x['start']:return t,t+dur
   t=max(t,x['end']);prior=x
  if prior and prior['write']!=write:t=max(t,prior['end']+self.ticks(self.p['WTR_ns']if prior['write']else self.p['RTW_ns']))
  return t,t+dur
 def preview(self,cycle,transactions,ctx,kind,front_after=1,arrival=None):
  if not transactions:return None,None
  mapped=[(w,self.address(ctx,s,a),s,a)for w,s,a in transactions];bank=self.bankrow(mapped[0][1])[0]
  assert all(self.bankrow(a)[0]==bank for w,a,s,o in mapped),'one FIFO parent descriptor requires same-bank child sequence'
  state=dict(self.banks[bank]);pending=[t for t in state['pending']if t>cycle]
  if len(pending)>=self.p['queue']:return 'backing_bank_queue',None
  bus=list(self.bus);rows=[];arrival=cycle if arrival is None else arrival
  for write,physical,space,original in mapped:
   _,row=self.bankrow(physical);hit=state['row']==row;conflict=state['row']is not None and not hit
   if hit:col=max(arrival,state['cmd']);activate=None
   else:
    activate=max(arrival,state['cmd'],state['pre'],state['act'])+(self.ticks(self.p['RP_ns'])if conflict else 0)
    col=activate+self.ticks(self.p['RCD_ns']);state['act']=activate+self.ticks(self.p['RAS_ns']);state['row']=row
   latency=self.ticks(self.p['CWL_ns']if write else self.p['CL_ns']);start,end=self.slot(bus,col+latency,write);col=start-latency
   state['cmd']=col+self.ticks(self.p['CCD_ns']);state['pre']=end+self.ticks(self.p['WR_ns'])if write else col+self.ticks(self.p['RTP_ns'])
   response=end+self.ticks(self.p['link_ns']);entry=dict(start=start,end=end,write=write);bus.append(entry);bus.sort(key=lambda x:x['start'])
   rows.append(dict(context=ctx,kind=kind,space=space,address=original,physical_address=physical,bank=bank,row=row,write=write,arrival=arrival,column=col,burst_start=start,burst_end=end,response=response,row_hit=hit,row_conflict=conflict))
   # Child RMW/WB/fill dependencies use one owned FIFO parent descriptor.
   arrival=response+1
  finish=rows[-1]['response']+front_after;state['pending']=pending+[finish]
  return None,dict(bank=bank,state=state,bus=bus,rows=rows,finish=finish,queue_peak=len(state['pending']))
 def commit(self,plan):
  if plan is None:return
  self.banks[plan['bank']]=plan['state'];self.bus=plan['bus'];self.ledger+=plan['rows'];self.groups.append(dict(bank=plan['bank'],finish=plan['finish'],queue_peak=plan['queue_peak']))
 def metrics(self,end):
  busy=sum(x['end']-x['start']for x in self.bus);return dict(transactions64=len(self.ledger),reads64=sum(not x['write']for x in self.ledger),writes64=sum(x['write']for x in self.ledger),bytes=64*len(self.ledger),row_hits=sum(x['row_hit']for x in self.ledger),row_conflicts=sum(x['row_conflict']for x in self.ledger),bus_utilization=busy/end if end else 0,bank_group_queue_peak=max([x['queue_peak']for x in self.groups]or[0]),bank_parent_descriptors=len(self.groups),queue_and_row_wait_ticks=sum(x['column']-x['arrival']for x in self.ledger),all_responses_done=max([x['response']for x in self.ledger]or[0])<=end)
class Spill:
 def __init__(self):
  self.lines=[None]*256;self.seq=0;self.busy=0
  # Untimed completed source initialization: sector-allocated sequential full-line overwrites.
  for line in range(262144//64,2097152//64):
   self.seq+=1;start=(line%64)*4;candidates=range(start,start+4);slot=min(candidates,key=lambda q:-1 if self.lines[q]is None else self.lines[q]['stamp']);self.lines[slot]=dict(tag=line,valid=255,dirty=255,stamp=self.seq)
 def preview(self,a,size,write):
  line=a//64;mask=((1<<(size//8))-1)<<((a%64)//8);assert size in [8,16]and a+size<=((line+1)*64)
  candidates=range((line%64)*4,(line%64)*4+4);hit=next((q for q in candidates if self.lines[q]is not None and self.lines[q]['tag']==line),None)
  slot=hit if hit is not None else min(candidates,key=lambda q:-1 if self.lines[q]is None else self.lines[q]['stamp']);old=self.lines[slot];tx=[]
  if hit is None:
   if old and old['dirty']:
    if old['valid']!=255:tx.append((False,'sp',old['tag']*64))
    tx.append((True,'sp',old['tag']*64))
   v=dict(tag=line,valid=0,dirty=0,stamp=self.seq+1)
  else:v=dict(old);v['stamp']=self.seq+1
  if write:v['valid']|=mask;v['dirty']|=mask
  elif v['valid']&mask!=mask:tx.append((False,'sp',line*64));v['valid']=255
  return dict(slot=slot,value=v,transactions=tx,eviction=bool(hit is None and old and old['dirty']),read_fill=bool(not write and (hit is None or old['valid']&mask!=mask)),tag_hit=hit is not None,read_hit=not write and hit is not None and old['valid']&mask==mask)
 def commit(self,plan,finish):self.seq+=1;self.lines[plan['slot']]=plan['value'];self.busy=finish
class Service:
 def __init__(self,p,metadata,placement):self.backend=Backend(p);self.md=metadata;self.placement=placement;self.cache=[Spill()for _ in metadata];self.memory=[];self.stats=collections.Counter()
 def preview(self,ctx,index,cycle,basefinish):
  m=self.md[ctx][index];source=m['source'];a=source['address'];size=source['size'];space=source['space'];write=source['write'];cp=None;group=None;kind='dataset'if space=='ds'else'local'
  if space=='ds':reason,group=self.backend.preview(cycle,[(False,'ds',a)],ctx,'dataset',arrival=cycle+1);finish=group['finish']if group else 0
  elif self.placement=='local'or a<262144:reason=None;finish=basefinish
  else:
   if self.cache[ctx].busy>cycle:return 'spill_cache_busy',None
   cp=self.cache[ctx].preview(a,size,write);kind=('spill_hit'if cp['tag_hit']else'spill_write_allocate_no_read')if not cp['transactions']else'spill_external'
   if cp['transactions']:reason,group=self.backend.preview(cycle,cp['transactions'],ctx,kind,front_after=(5 if cp['read_fill']else 1),arrival=basefinish+1+(4 if cp['eviction']else 0));finish=group['finish']if group else 0
   else:reason=None;finish=basefinish+1
  if reason:return reason,None
  finish=max(finish,basefinish)
  return None,dict(finish=finish,group=group,cache=cp,ctx=ctx,index=index,issue=cycle,kind=kind,source=source)
 def commit(self,plan):
  self.backend.commit(plan['group'])
  if plan['cache']is not None:self.cache[plan['ctx']].commit(plan['cache'],plan['finish'])
  self.stats[plan['kind']]+=1;self.memory.append({k:plan[k]for k in ['ctx','index','issue','finish','kind','source']})
