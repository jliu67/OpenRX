"""Extract four retained native first-iteration checkpoints; no workload replay."""
from pathlib import Path
import hashlib,json,struct
import argparse,resource
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--native-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();G=args.native_dir.resolve(strict=True);R=args.output.resolve()
assert not R.exists(),'fresh output required';R.mkdir(parents=True)
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CPU,(55,55));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
expected=json.loads((Path(__file__).resolve().parents[1]/'fixtures/native-pins.json').read_text())
def pin(p):
 b=p.read_bytes();return dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
pins=[]
for name,row in expected.items():
 v=pin(G/name);assert (v['bytes'],v['sha256'])==(row['bytes'],row['sha256']),name;pins.append(v)

metas=[int(x,16)&((1<<1024)-1)for x in(G/'metadata.mem').read_text().splitlines()[:4]]
gold={};textgold={};datasets={};initial_rounds={0:0}
for name,target in [('iterations.mem',gold),('iterations.hex',textgold),('dataset-items.hex',datasets)]:
 with(G/name).open()as f:
  for i,line in enumerate(f):
   if name=='iterations.mem'and i in(2047,4095,6143):initial_rounds[i//2048+1]=int(line,16)>>2048&3
   if i%2048==0 and i//2048<4:target[i//2048]=int(line,16)if name.endswith('.mem')else line.split()
   if i==6144:break
starts={i:(gold[i]>>2466)&0xffffffff for i in range(4)}
counts={i:(gold[i]>>2498)&0xffffffff for i in range(4)}
assert list(counts.values())==[80,90,82,91]
evs={i:[]for i in range(4)}
with(G/'events.mem').open()as f:
 for off,line in enumerate(f):
  for i in range(4):
   if starts[i]<=off<starts[i]+counts[i]:evs[i].append(int(line,16))
  if off>=starts[3]+counts[3]-1:break
def fm(x):return (0x300<<52)|((x>>60)<<56)|(x&((1<<22)-1))
def fb(x):return int.from_bytes(struct.pack('<d',float(x)),'little')
fields={};rows=[];rom=[];rcps=[];allevents=[];eventbase=0
for i in range(4):
 m=metas[i];g=gold[i];t=textgold[i];a=sum((((1023+((m>>(64*j+59))&31))<<52)|((m>>(64*j))&((1<<52)-1)))<<(64*j)for j in range(8))
 assert a==(g>>1536)&((1<<512)-1)
 l0=(m>>640)&0x1fffc0;l1=(m>>512)&0x1fffc0;mx=(m>>640)&0xffffffff;ma=(m>>512)&0x7fffffc0;offset=((m>>832)&0x7ffff)<<6
 img=G/('initial.hex'if i==0 else f'final-{i-1}.hex');ram=[int(x,16)for x in img.read_text().split()];assert len(ram)==131072
 line0=sum(ram[l0//16+j]<<(128*j)for j in range(4));line1=sum(ram[l1//16+j]<<(128*j)for j in range(4));fr=er=0
 em0=fm((m>>896)&((1<<64)-1));em1=fm(m>>960)
 for j in range(8):
  x=line1>>(32*j)&0xffffffff;x-=1<<32 if x>>31 else 0;fr|=fb(x)<<(64*j)
  x=line1>>(32*(j+8))&0xffffffff;x-=1<<32 if x>>31 else 0;er|=((fb(x)&0x00ffffffffffffff)|(em1 if j%2 else em0))<<(64*j)
 dsaddr,dsdata=map(lambda x:int(x,16),datasets[i]);assert dsaddr==(g>>2242)&((1<<64)-1)==offset+ma
 steps=(g>>2434)&0xffffffff;assert steps==int(t[4])and starts[i]==int(t[2])and counts[i]==int(t[3])
 r=g&((1<<512)-1);f=g>>512&((1<<512)-1);e=g>>1024&((1<<512)-1);rm=g>>2048&3;route=g>>2370&((1<<64)-1)
 assert(r,f,e,rm,route)==(int(t[5],16),int(t[6],16),int(t[7],16),int(t[9]),int(t[18],16))
 writes=0
 for ev in evs[i]:
  addr=((ev>>68)&0x1ffff)<<4;lane=ev>>67&1;val=ev&((1<<64)-1)
  if ev>>85:
   mask=((1<<64)-1)<<(64*lane);ram[addr//16]=(ram[addr//16]&~mask)|(val<<(64*lane));writes+=1
  else:assert ram[addr//16]>>(64*lane)&((1<<64)-1)==val
 for j in range(4):ram[l1//16+j]=r>>(128*j)&((1<<128)-1)
 for j in range(4):ram[l0//16+j]=f>>(128*j)&((1<<128)-1)
 # Compact full-image check, supplementary to exact checked ordered writes.
 fnv=0xcbf29ce484222325
 for x in ram:
  for j in range(16):fnv=((fnv^(x>>(8*j)&255))*0x100000001b3)&((1<<64)-1)
 p=[int(x,16)for x in(G/f'program-{i}.mem').read_text().split()];assert len(p)==384
 for w in p:
  d=w>>32;active=76<=(w&255)<84 and d!=0 and d&(d-1)!=0;v=(1<<(63+d.bit_length()))//d if active else 0
  if active:
   rem=1<<(d.bit_length()-1);q=0
   for _ in range(64):
    rem*=2;q<<=1
    if rem>=d:rem-=d;q|=1
   assert q==v
  rcps.append(v)
 rom.extend(p);allevents.extend(evs[i])
 vals=dict(A=a,INIT_ROUND=initial_rounds[i],EM0=em0,EM1=em1,L0=l0,L1=l1,MX=mx,MA=ma,READ2=4|((m>>770)&1),READ3=6|((m>>771)&1),OFFSET=offset,
  ENTRY_R=line0,ENTRY_F=fr,ENTRY_E=er,GR=r,GF=f,GE=e,ROUND=rm,STEPS=steps,ROUTE=route,COUNT=counts[i],WRITES=writes,EVENT_BASE=eventbase,DSADDR=dsaddr,DSDATA=dsdata,PREFETCH=int(t[17],16),NEXT_MX=int(t[10],16),NEXT_MA=int(t[11],16),SP_FNV=fnv)
 for k,v in vals.items():fields.setdefault(k,[]).append(v)
 rows.append(dict(program=i,image=pin(img),native_iteration_index=i*2048,native_event_offset=starts[i],count=counts[i],steps=steps,writes=writes,values_hex={k:hex(v)for k,v in vals.items()}));eventbase+=counts[i]
widths={k:512 for k in fields}
widths.update(INIT_ROUND=2,EM0=64,EM1=64,L0=21,L1=21,MX=32,MA=32,READ2=3,READ3=3,OFFSET=64,ROUND=2,STEPS=32,ROUTE=64,COUNT=32,WRITES=32,EVENT_BASE=32,DSADDR=64,PREFETCH=64,NEXT_MX=32,NEXT_MA=32,SP_FNV=64)
with(R/'fixture.vh').open('x')as f:
 for k,vs in fields.items():
  w=widths[k];f.write(f"localparam [3:0][{w-1}:0] {k}="+'{'+','.join(f"{w}'h{x:x}"for x in reversed(vs))+'};\n')
for name,vs,w in [('programs.mem',rom,16),('reciprocals.mem',rcps,16),('events.mem',allevents,22)]:
 with(R/name).open('x')as f:f.write(''.join(f'{x:0{w}x}\n'for x in vs))
with(R/'fixture.json').open('x')as f:json.dump(dict(pins=pins,contexts=rows,scope='Four retained firstiteration checkpoints from one canonical v2fullhash, distinctprograms0..3, not independentnonces. Initialimages are initialSP or priorprogramfinalSP; actualentry/dataset/tail are executed. Programgeneration/imagepreparation/SPinitialization untimed. FinalSPFNV reconstructed from nativebytecodeevents+nativepostRF tail, not a separately archived nativefirstiterationfullSP.'),f,sort_keys=True);f.write('\n')
print(json.dumps([dict(program=x['program'],steps=x['steps'],events=x['count'],writes=x['writes'])for x in rows]))
