#!/usr/bin/env python3
"""Native HardFloat-backed RandomX FP subset, actual mapped units/integration."""
import argparse,hashlib,json,re,shutil,subprocess,sys,time
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode=True
from test_iteration_engine import extract,RTL as ENGINE_RTL
from floating_fixture import prepare
ROOT=Path(__file__).resolve().parents[1]
V='rtl/execute/vendor/hardfloat/'
HF=[V+n for n in ['HardFloat_primitives.v','HardFloat_rawFN.v','isSigNaNRecFN.v','fNToRecFN.v','recFNToFN.v','addRecFN.v','mulRecFN.v','8086-SSE/HardFloat_specialize.v']]
FP=[*HF,'rtl/execute/randomx_fp64.v','rtl/execute/randomx_fp128.v']
CORE='rtl/execute/randomx_integer_execute.v';WRAP='rtl/execute/randomx_integer_iteration.v'
INTEGER=['rtl/execute/randomx_mul64.v','rtl/execute/randomx_reciprocal32.v']
RTL=[*ENGINE_RTL,*INTEGER,CORE,WRAP,*FP]
BASE='d62c449574e1f5434aa6809040a02fabfb74dc09'
LIBS=['vendor/randomx/src/soft_aes.cpp','vendor/randomx/src/bytecode_machine.cpp','vendor/randomx/src/instructions_portable.cpp','vendor/randomx/src/reciprocal.c']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(path):return {k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',path.read_text().splitlines()[0])}
def mapped_fixture(out):
 rows=[l.split() for l in (out/'fp128-full.hex').read_text().splitlines()]
 pairs=[(int(rows[i][0],16),int(rows[i][2],16)) for i in range(0,len(rows),24)]
 edges=sorted({a for a,b in pairs[:576]});assert len(edges)==24
 one=0x3ff0000000000000;minus=0xbff0000000000000
 selected={(a,b) for a in edges for b in (one,minus,a)}|{(a,b) for b in edges for a in (one,minus)}
 special=[(0,0x7ff0000000000000),(0x7ff0000000000000,0),(0x0010000000000000,0x3fefffffffffffff),
  (0x000fffffffffffff,0x3ff0000000000001),(0x0010000000000000,0x3fe0000000000000),
  (0x7fefffffffffffff,0x4000000000000000),(one,0x3ca0000000000000),
  (0x7ff8000000001234,0xfff8000000005678),(0x7ff0000000001234,0xfff8000000005678),
  (0x7ff0000000001234,0xfff0000000005678)]
 selected.update(special);selected.update((b,a) for a,b in special);selected.update(pairs[576:608])
 chosen=[' '.join(row) for row in rows if (int(row[0],16),int(row[2],16)) in selected]
 assert len(chosen)%24==0
 flags={int(r.split()[9],16) for r in chosen};assert all(any(f&bit for f in flags) for bit in (16,4,2,1))
 (out/'fp128-mapped.hex').write_text('\n'.join(chosen)+'\n')
 (out/'mapped-primitive-selection.json').write_text(json.dumps({'full_native_vectors':len(rows),'mapped_native_vectors':len(chosen),'selected_operand_pairs':len(chosen)//24,'each_pair_balanced':'3 operations ×4 rounding modes ×IEEE/RandomX DAZ+FTZ','selection':'all24 edge patterns in both operand positions against ±1 and self; directed NaN/zero/underflow-round-to-normal/overflow/tie pairs and reversals; first32 seeded arbitrary-bit pairs','native_invalid_overflow_underflow_inexact_observed':True,'full_raw_sha256':sha(out/'fp128-full.hex'),'selected_raw_sha256':sha(out/'fp128-mapped.hex')},indent=2)+'\n')
 return len(chosen)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--synthesize',action='store_true');a=p.parse_args();out=a.output.resolve()
 if out.exists() or out==ROOT or ROOT in out.parents:p.error('fresh output outside source required')
 if not re.fullmatch(r'[-A-Za-z0-9_./]+',str(out)):p.error('unambiguous HDL output path required')
 tools=[('g++','--version'),('iverilog','-V'),('vvp','-V')]+([('yosys','-V')] if a.synthesize else [])
 for t,_ in tools:
  if not shutil.which(t):p.error('tool missing: '+t)
 out.mkdir();commands=[];includes=['-Irtl/execute','-I'+V,'-I'+V+'8086-SSE']
 def run(label,argv,timeout=2400):
  row={'label':label,'argv':argv,'cwd':'repository-root','timeout_seconds':timeout};commands.append(row);start=time.monotonic();print('START '+label,flush=True)
  try:
   with (out/(label+'.log')).open('w') as f:subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
   row['returncode']=0
  except Exception as e:row['error']=str(e);raise
  finally:row['elapsed_seconds']=time.monotonic()-start;(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  print('PASS '+label,flush=True)
 def check(label,prefix,reference=None):
  line=(out/(label+'.log')).read_text().splitlines()[0];assert line.startswith(prefix),(label,line)
  if reference:assert line==(out/(reference+'.log')).read_text().splitlines()[0],label
 def units(lanes,label,fixture,net=None,reference=None):
  flags=['-DFP128_NETLIST'] if net else [];sources=[str(net)] if net else FP
  run('compile-'+label,['iverilog','-g2012','-Wall',*includes,*flags,'-s','tb_fp128',f'-Ptb_fp128.LANES={lanes}','-o',str(out/(label+'.vvp')),*sources,'rtl/execute/tests/tb_fp128.v'])
  run(label,['vvp',str(out/(label+'.vvp')),'+vectors='+str(out/fixture)]);check(label,f'PASS fp128 lanes={lanes} ',reference);return stats(out/(label+'.log'))
 def connected(lanes,label,net=None,top=None):
  flags=['-DINTEGER_ITERATION_NETLIST'] if top else ['-DFP128_NETLIST'] if net else []
  sources=[str(top)] if top else [*ENGINE_RTL,*INTEGER,CORE,WRAP,*([str(net)] if net else FP)]
  result={}
  for stall in (0,1):
   name=f'{label}-{stall}';run('compile-'+name,['iverilog','-g2012','-Wall',*includes,*flags,'-I'+str(out),'-s','tb_floating_iteration',f'-Ptb_floating_iteration.FP_LANES={lanes}',f'-Ptb_floating_iteration.STALL={stall}','-o',str(out/(name+'.vvp')),*sources,'rtl/execute/tests/tb_floating_iteration.v'])
   run(name,['vvp',str(out/(name+'.vvp')),*[f'+{arg}={out/file}' for arg,file in [('initial','initial.hex'),('final','final.hex'),('programs','programs.mem'),('steps','steps.mem'),('events','events.mem'),('targets','targets.mem')]]]);check(name,f'PASS floating_hardware lanes={lanes} stall={stall} ',f'rtl-{lanes}-{stall}' if net or top else None);result[str(stall)]=stats(out/(name+'.log'))
  name=label+'-errors';run('compile-'+name,['iverilog','-g2012','-Wall',*includes,*flags,'-s','tb_floating_errors',f'-Ptb_floating_errors.FP_LANES={lanes}','-o',str(out/(name+'.vvp')),*sources,'rtl/execute/tests/tb_floating_errors.v'])
  run(name,['vvp',str(out/(name+'.vvp')),'+unsupported='+str(out/'unsupported.mem')]);check(name,f'PASS floating_errors lanes={lanes} unsupported_raw_opcodes=10 held_errors=12 ',f'rtl-{lanes}-errors' if net or top else None);result['errors']=stats(out/(name+'.log'));return result
 def synth(label,top,sources,parameter=None):
  net=out/('netlist-'+label+'.v');cmd=f'read_verilog -Irtl/execute -I{V} -I{V}8086-SSE {" ".join(sources)}; '
  if parameter:cmd+=f'chparam -set {parameter[0]} {parameter[1]} {top}; '
  cmd+=f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; write_verilog -noattr {net}; write_json {out}/netlist-{label}.json'
  run('synth-'+label,['yosys','-p',cmd]);types=Counter()
  with (out/('netlist-'+label+'.json')).open() as f:
   for line in f:
    m=re.fullmatch(r'\s*"type": "([^\"]+)",\s*\n?',line)
    if m:types[m[1]]+=1
  assert sum(types.values())==int(re.search(r'Number of cells:\s*(\d+)',(out/('stat-'+label+'.txt')).read_text()).group(1))
  return net,{'num_cells':sum(types.values()),'flop_cells':sum(n for t,n in types.items() if 'DFF' in t),'num_cells_by_type':dict(sorted(types.items())),'scope':'actual generic mapping; no physical timing/power/external memory area'}
 try:
  run('vendor',['python3','scripts/verify_vendor.py']);preserved={}
  for name in ['aes-rtl-corrected-20261012/inputs.json','iteration-tail-v2-stalls-20261012/inputs.json','iteration-engine-read-grant-20261013/rtl-inputs.json']:
   path=ROOT/'docs/validation'/name;bindings=json.loads(path.read_text())
   for src,digest in bindings.items():assert sha(ROOT/src)==digest,src
   preserved[name]={'checked':len(bindings),'sha256':sha(path)}
  hf=json.loads((ROOT/V/'manifest.json').read_text())
  for name,digest in hf['files'].items():assert sha(ROOT/V/name)==digest,name
  preserved['HardFloat1-8086-SSE']={'checked':len(hf['files']),'manifest_sha256':sha(ROOT/V/'manifest.json')}
  (out/'preserved-inputs.json').write_text(json.dumps(preserved,indent=2)+'\n')
  paths=set(RTL+LIBS+[V+n for n in hf['files']]+[V+'manifest.json','scripts/test_floating_execute.py','scripts/floating_fixture.py','scripts/test_iteration_engine.py','rtl/execute/randomx_opcode_ceils.vh','vendor/randomx.lock.json','vendor/randomx.sha256.json','vendor/randomx/src/configuration.h','vendor/randomx/src/vm_interpreted.cpp','vendor/randomx/src/virtual_machine.cpp','vendor/randomx/src/bytecode_machine.hpp'])
  paths.update('rtl/execute/tests/'+n for n in ['fp_oracle.cpp','floating_oracle.cpp','tb_fp64.v','tb_fp128.v','tb_floating_iteration.v','tb_floating_errors.v','tb_integer_transport.v'])
  (out/'inputs.json').write_text(json.dumps({n:sha(ROOT/n) for n in sorted(paths)},indent=2)+'\n');(out/'tools.json').write_text(json.dumps({t:subprocess.check_output([t,f],stderr=subprocess.STDOUT,text=True) for t,f in tools},indent=2)+'\n')
  for src,dst in [('rtl/execute/LICENSE','LICENSE-OpenRX'),('vendor/randomx/LICENSE','LICENSE-RandomX'),('rtl/aes/vendor/secworks/LICENSE','LICENSE-secworks'),(V+'LICENSE','LICENSE-HardFloat')]:shutil.copyfile(ROOT/src,out/dst)
  extract(out)
  run('compile-fp-oracle',['g++','-std=c++11','-O2','-Ivendor/randomx/src','rtl/execute/tests/fp_oracle.cpp','-o',str(out/'fp-oracle')]);run('fp-oracle',[str(out/'fp-oracle'),str(out/'fp64-full.hex'),str(out/'fp128-full.hex')]);mapped_count=mapped_fixture(out)
  run('compile-oracle',['g++','-std=c++11','-O2','-I'+str(out),'-Ivendor/randomx/src','rtl/execute/tests/floating_oracle.cpp',*LIBS,'-o',str(out/'oracle')]);run('oracle',[str(out/'oracle'),str(out)]);check('oracle','PASS native floating-branch iterations=8');coverage=prepare(out);oracle=json.loads((out/'oracle-summary.json').read_text())
  summary={'base':BASE,'scope':'native integer/branch + exact FSWAP/FADD/FSUB register/memory/FSCAL/FMUL/CFROUND; division/sqrt explicit errors','oracle':oracle,'coverage':coverage,'mapped_primitive_vectors':mapped_count,'rtl':{},'unit_full_rtl':{},'unit_mapped_corpus_rtl':{},'mapping':{},'mapped':{},'synthesis_requested':a.synthesize}
  run('compile-scalar',['iverilog','-g2012','-Wall',*includes,'-s','tb_fp64','-o',str(out/'scalar.vvp'),*FP,'rtl/execute/tests/tb_fp64.v']);run('scalar',['vvp',str(out/'scalar.vvp'),'+vectors='+str(out/'fp64-full.hex')]);check('scalar','PASS fp64 native_vectors=19968 ');summary['scalar']=stats(out/'scalar.log')
  for lanes in (1,2):
   summary['unit_full_rtl'][str(lanes)]=units(lanes,f'unit-full-{lanes}','fp128-full.hex')
   summary['unit_mapped_corpus_rtl'][str(lanes)]=units(lanes,f'unit-corpus-{lanes}','fp128-mapped.hex')
   summary['rtl'][str(lanes)]=connected(lanes,f'rtl-{lanes}')
  run('compile-transport',['iverilog','-g2012','-Wall',*includes,'-s','tb_integer_transport','-o',str(out/'transport.vvp'),'rtl/engine/randomx_i32_to_f64.v',*INTEGER,CORE,*FP,'rtl/execute/tests/tb_integer_transport.v']);run('transport',['vvp',str(out/'transport.vvp')]);check('transport','PASS integer_transport serial_iadd=0 contexts=8');summary['transport']=stats(out/'transport.log')
  cmd=['iverilog','-g2012',*includes,'-s','randomx_fp128','-Prandomx_fp128.LANES=3','-o',str(out/'invalid.vvp'),*FP];q=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(out/'invalid-LANES.log').write_text(q.stdout);assert q.returncode and 'floating_vector_requires_LANES_1_or_2' in q.stdout;summary['invalid_parameters_rejected']=True
  if a.synthesize:
   for lanes in (1,2):
    net,counts=synth(f'fp128-{lanes}','randomx_fp128',FP,('LANES',lanes));summary['mapping'][f'fp128-{lanes}']=counts
    summary['mapped'][f'unit-{lanes}']=units(lanes,f'unit-mapped-{lanes}','fp128-mapped.hex',net,f'unit-corpus-{lanes}')
    summary['mapped'][f'connected-{lanes}']=connected(lanes,f'mapped-unit-{lanes}',net=net)
   net,counts=synth('integrated-2','randomx_integer_iteration',RTL,('FP_LANES',2));summary['mapping']['integrated-default']=counts;summary['mapped']['integrated-default']=connected(2,'mapped-integrated-2',top=net)
  comparison={}
  for stall in ('0','1'):
   slow=summary['rtl']['1'][stall];fast=summary['rtl']['2'][stall];delta=slow['elapsed_cycles']-fast['elapsed_cycles'];assert delta==4*oracle['fp_steps'];assert slow['fetch_to_last_commit_cycles']-fast['fetch_to_last_commit_cycles']==delta;comparison[stall]={'shared_extra_cycles':delta,'extra_per_vector_FP_operation':4,'actual_vector_FP_operations':oracle['fp_steps']}
  summary['comparison']=comparison;(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
 except Exception as e:(out/'failure.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)},indent=2)+'\n');raise
 finally:
  (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');(out/'artifacts.sha256.json').write_text(json.dumps({p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='artifacts.sha256.json'},indent=2)+'\n')
if __name__=='__main__':main()
