"""Derive one native-kernel component fixture from accepted finite inputs."""
from pathlib import Path
import json,hashlib,struct
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

def first(p):
 with p.open()as f:return int(next(f).strip(),16)
meta=first(G/'metadata.mem');gold=first(G/'iterations.mem');entropy=meta&((1<<1024)-1)
line0=((entropy>>640)&0xffffffff)&0x1fffc0
line1=((entropy>>512)&0x7fffffc0)&0x1fffc0
lines={}
with(G/'initial.hex').open()as f:
 for i,s in enumerate(f):
  if min(line0,line1)//16<=i<max(line0,line1)//16+4:lines[i]=int(s,16)
  if i>=max(line0,line1)//16+4:break
l0=sum(lines[line0//16+i]<<(128*i)for i in range(4))
l1=sum(lines[line1//16+i]<<(128*i)for i in range(4))
def fbits(x):return int.from_bytes(struct.pack('<d',float(x)),'little')
def fm(x):return (0x300<<52)|((x>>60)<<56)|(x&((1<<22)-1))
em0=fm((entropy>>896)&((1<<64)-1));em1=fm(entropy>>960)
fr=er=ar=0
for i in range(8):
 x=(l1>>(32*i))&0xffffffff;x=x-(1<<32)if x>>31 else x;fr|=fbits(x)<<(64*i)
 x=(l1>>(32*(i+8)))&0xffffffff;x=x-(1<<32)if x>>31 else x
 er|=((fbits(x)&0x00ffffffffffffff)|(em0 if i%2==0 else em1))<<(64*i)
 x=(entropy>>(64*i))&((1<<64)-1)
 ar|=((1023+(x>>59))<<52|(x&((1<<52)-1)))<<(64*i)
assert ar==(gold>>1536)&((1<<512)-1)
dsaddr,dsdata=[int(s,16)for s in(G/'dataset-items.hex').read_text().splitlines()[0].split()]
assert dsaddr==(gold>>2242)&((1<<64)-1)
program=[int(s,16)for s in(G/'program-0.mem').read_text().split()];assert len(program)==384
rcps=[]
for w in program:
 d=w>>32;isrcp=76<=w&255<84;nop=d==0 or d&(d-1)==0
 v=0 if not isrcp or nop else (1<<(63+d.bit_length()))//d
 if isrcp and not nop:
  rem=1<<(d.bit_length()-1);q=0
  for _ in range(64):
   rem*=2;q<<=1
   if rem>=d:rem-=d;q|=1
  assert q==v
 rcps.append(v)
data=''.join(f'{v:016x}\n'for v in rcps)
if(R/'reciprocals.mem').exists():assert(R/'reciprocals.mem').read_text()==data
else:(R/'reciprocals.mem').write_text(data)
offset=(gold>>2466)&0xffffffff;count=(gold>>2498)&0xffffffff
assert(offset,count)==(0,80)
with(G/'events.mem').open()as f:events=[next(f)for _ in range(count)]
(R/'events.mem').write_text(''.join(events))
fields={'start_r':l0,'start_f':fr,'start_e':er,'start_a':ar,'emask0':em0,'emask1':em1,
 'expected_r':(gold&((1<<512)-1))^dsdata,'expected_e':(gold>>1024)&((1<<512)-1),
 'expected_post_AES_f':(gold>>512)&((1<<512)-1),'expected_round':(gold>>2048)&3,
 'expected_steps':(gold>>2434)&0xffffffff,'expected_route':(gold>>2370)&((1<<64)-1),
 'dataset_address':dsaddr,'dataset_line':dsdata,'native_events':count,'line0':line0,'line1':line1}
widths={k:512 for k in fields};widths.update(emask0=64,emask1=64,expected_round=2,expected_steps=32,
 expected_route=64,dataset_address=64,native_events=32,line0=32,line1=32)
(R/'fixture.vh').write_text('\n'.join(f"localparam [{widths[k]-1}:0] {k.upper()}={widths[k]}'h{v:x};"for k,v in fields.items())+'\n')
(R/'fixture.json').write_text(json.dumps({'scope':'Kernel start derived from initialSP+entropy using accepted entry equations, exact signedint32tof64. End assertions from first nativeiterationgold+datasetline; native finalF checked by unchangedAES after measuredkernel. No hash generation/replay.',
 'values_hex':{k:hex(v)for k,v in fields.items()},'pins':pins},sort_keys=True))
print('FIXTURE_PASS native_kernel_steps',fields['expected_steps'],'events',count,'emask',hex(em0),hex(em1))
