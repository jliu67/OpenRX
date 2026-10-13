#!/usr/bin/env python3
"""Pack assertion-only native program/iteration/event records; no DUT inputs from gold."""
import json
from pathlib import Path
def prepare(out):
 out=Path(out);summary=json.loads((out/'oracle-summary.json').read_text())
 rows=[r.split() for r in (out/'iterations.hex').read_text().splitlines()]
 metas=[r.split() for r in (out/'metadata.hex').read_text().splitlines()]
 assert len(rows)==summary['total_iterations'] and len(metas)==summary['programs']
 packed=[]
 positions=[(5,0,512),(6,512,512),(7,1024,512),(8,1536,512),(9,2048,2),
  (10,2050,32),(11,2082,32),(12,2114,32),(13,2146,32),(14,2178,32),(15,2210,32),
  (16,2242,64),(17,2306,64),(18,2370,64),(4,2434,32),(2,2466,32),(3,2498,32)]
 for index,row in enumerate(rows):
  assert len(row)==19 and int(row[0])==index//summary['iterations_per_program'] and int(row[1])==index%summary['iterations_per_program']
  value=0
  for column,shift,bits in positions:
   x=int(row[column],10 if column in [2,3,4] else 16);assert 0<=x<1<<bits;value|=x<<shift
  assert int(row[12],16)==int(row[13],16)==0
  packed.append(f'{value:0633x}')
 (out/'iterations.mem').write_text('\n'.join(packed)+'\n')
 packed=[]
 for p,row in enumerate(metas):
  assert len(row)==12 and int(row[0])==p
  shifts=[0,1024,1536,1568,1600,1664,1728,1792,1795,1798,1801]
  value=sum(int(x,16)<<shift for x,shift in zip(row[1:],shifts));packed.append(f'{value:0451x}')
 (out/'metadata.mem').write_text('\n'.join(packed)+'\n')
 event_rows=(out/'accesses.hex').read_text().splitlines();assert len(event_rows)==summary['bytecode_events']
 with (out/'events.mem').open('w') as f:
  for row in event_rows:
   kind_addr,data=map(lambda x:int(x,16),row.split());assert kind_addr<(1<<22) and kind_addr&7==0
   f.write(f'{(kind_addr<<64)|data:022x}\n')
 (out/'sequence_sizes.vh').write_text(f'localparam integer TOTAL_ITERATIONS={len(rows)},TOTAL_EVENTS={len(event_rows)},TOTAL_INSTRUCTIONS={summary["instruction_steps"]};\n')
 return summary
