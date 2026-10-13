#!/usr/bin/env python3
"""Prepare assertion-only native FP/branch traces; preserve strict acceptance coverage."""
import json,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def prepare(out):
 kinds=[]
 for name,count in re.findall(r'^#define RANDOMX_FREQ_(\w+)\s+(\d+)\s*$',(ROOT/'vendor/randomx/src/configuration.h').read_text(),re.M):kinds += [name]*int(count)
 accepted={op for op,k in enumerate(kinds) if k not in ('FDIV_M','FSQRT_R')};assert len(accepted)==246
 names=('versions chains ev_start ev_count read0 read1 read2 read3 round_in round_out sp0 sp1 mx ma em0 em1 offset '
        'rin ain loadr loadf loade expr expf expe dsaddr pfaddr dsdata outr outf oute outmx outma fline rline fmem rmem').split()
 rows=[l.split() for l in (out/'iterations.hex').read_text().splitlines()];events=[l.split() for l in (out/'accesses.hex').read_text().splitlines()];steps=[l.split() for l in (out/'instruction-steps.hex').read_text().splitlines()];oracle=json.loads((out/'oracle-summary.json').read_text())
 assert len(rows)==8 and len(events)<=2048 and len(steps)<=8192
 lines=[f'localparam integer TOTAL_EVENTS={len(events)},BYTECODE_READS={oracle["bytecode_read64"]},BYTECODE_STORES={oracle["bytecode_store64"]},TOTAL_STEPS={len(steps)},MULTIPLY_STEPS={oracle["multiply_steps"]},BRANCH_STEPS={oracle["branch_steps"]},BRANCH_TAKEN={oracle["branch_taken"]},RCP_NOPS={oracle["rcp_nops"]},FP_STEPS={oracle["fp_steps"]},CF_STEPS={oracle["cf_steps"]};']
 for case,row in enumerate(rows):
  assert len(row)==38 and int(row[0])==case
  for column,(name,value) in enumerate(zip(names,row[1:])):lines.append(f'{name}[{case}]='+(value if column<10 else "'h"+value)+';')
  lines += [f'step_start[{case}]={next(i for i,s in enumerate(steps) if int(s[0])==case)};',f'step_count[{case}]={sum(int(s[0])==case for s in steps)};']
 (out/'floating_vectors.vh').write_text('\n'.join(lines)+'\n')
 instructions={(int(c),int(pc)):int(w,16) for c,pc,w in (l.split() for l in (out/'programs.hex').read_text().splitlines())};assert len(instructions)==2560 and {w&255 for w in instructions.values()}==accepted
 programs=[0]*4096;targets=[511]*4096
 for (c,pc),word in instructions.items():programs[c*512+pc]=word
 for c,pc,op,target in (l.split() for l in (out/'compiled-targets.hex').read_text().splitlines()):
  c,pc,op,target=int(c),int(pc),int(op),int(target);assert instructions[c,pc]&255==op
  if kinds[op]=='CBRANCH':assert 0<=target<=pc;targets[c*512+pc]=target
  else:assert target==-1
 previous={c:int(row[names.index('loadr')+1],16) for c,row in enumerate(rows)};rounds={c:int(row[names.index('round_in')+1]) for c,row in enumerate(rows)};next_pc={c:0 for c in range(8)}
 counts=Counter();rotates=set();shifts=set();masks=set();cfrots=set();conditions=set();used_rm=Counter();guards=Counter();encoded=[]
 for c,pc,op,r,f,e,rm,nxt in steps:
  c,pc,op,rm,nxt=int(c),int(pc),int(op),int(rm),int(nxt);r,f,e=int(r,16),int(f,16),int(e,16);assert pc==next_pc[c] and instructions[c,pc]&255==op
  ins=instructions[c,pc];kind=kinds[op];dst=(ins>>8)&7;src=(ins>>16)&7;mod=(ins>>24)&255;imm=ins>>32;rs=(previous[c]>>(64*src))&((1<<64)-1);counts[kind]+=1
  if kind in ('IROR_R','IROL_R'):rotates.add((imm if dst==src else rs)&63)
  if kind=='IADD_RS':shifts.add((mod>>2)&3)
  if kind.endswith('_M') or kind=='ISTORE':masks.add('L3' if (kind=='ISTORE' and mod>>4>=14 or kind not in ('ISTORE','FADD_M','FSUB_M') and dst==src) else 'L1' if mod&3 else 'L2')
  if kind in ('FADD_R','FADD_M','FSUB_R','FSUB_M','FMUL_R'):used_rm[rounds[c]]+=1
  if kind=='CFROUND':
   shift=imm&63;cfrots.add(shift);rot=((rs>>shift)|(rs<<(64-shift)))&((1<<64)-1);apply=c>=4 or rot&60==0;guards[f'{"v2" if c<4 else "v1"}-{"apply" if apply else "skip"}']+=1
   assert rm==(rot&3 if apply else rounds[c]),'native CFROUND semantics'
  else:assert rm==rounds[c]
  if kind=='CBRANCH':conditions.add(mod>>4);assert nxt in (pc+1,targets[c*512+pc]);counts['taken']+=nxt<=pc;counts['jump_zero']+=nxt==0;counts['self_jump']+=nxt==pc
  else:assert nxt==pc+1
  rounds[c]=rm;previous[c]=r;next_pc[c]=nxt;encoded.append(f'{(pc<<1555)|(nxt<<1546)|(op<<1538)|(rm<<1536)|(e<<1024)|(f<<512)|r:0391x}')
 assert rotates==set(range(64)) and shifts==set(range(4)) and masks=={'L1','L2','L3'} and conditions==set(range(16))
 assert cfrots==set(range(64)) and set(used_rm)==set(range(4)) and all(guards[x] for x in ['v2-apply','v2-skip','v1-apply'])
 assert all(counts[x] for x in ['taken','jump_zero','self_jump'])
 encoded_events=[]
 for c,pc,w,addr,data in events:
  w,addr,data=int(w),int(addr,16),int(data,16);assert w in (0,1) and addr%8==0 and addr<=2097152-8;encoded_events.append(f'{(w<<85)|(addr<<64)|data:022x}')
 for file,values,fmt in [('programs.mem',programs,'016x'),('targets.mem',targets,'03x')]: (out/file).write_text('\n'.join(format(v,fmt) for v in values)+'\n')
 (out/'steps.mem').write_text('\n'.join(encoded)+'\n');(out/'events.mem').write_text('\n'.join(encoded_events)+'\n');(out/'unsupported.mem').write_text('\n'.join('0' if i in accepted else '1' for i in range(256))+'\n')
 coverage={'counts':dict(counts),'supported_raw':sorted(accepted),'rotate_counts':sorted(rotates),'shifts':sorted(shifts),'masks':sorted(masks),'branch_conditions':sorted(conditions),'cfround_rotations':sorted(cfrots),'arithmetic_rounding_counts':dict(used_rm),'cfround_guard_counts':dict(guards)}
 (out/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n');return coverage
if __name__=='__main__':print(json.dumps(prepare(Path(sys.argv[1])),indent=2))
