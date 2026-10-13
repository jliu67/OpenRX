import hashlib,json,re,subprocess,time
from collections import Counter
from pathlib import Path
O=Path(__file__).resolve().parent;R=Path(json.loads((O/'workspace.json').read_text())['root']);N=Path('/tmp/openrx-floating-driver-rtl-01');D=Path('/tmp/openrx-floating-unit-mapping-01');assert not D.exists();D.mkdir();commands=[]
V='rtl/execute/vendor/hardfloat/';HF=[V+n for n in ['HardFloat_primitives.v','HardFloat_rawFN.v','isSigNaNRecFN.v','fNToRecFN.v','recFNToFN.v','addRecFN.v','mulRecFN.v','8086-SSE/HardFloat_specialize.v']];FP=[*HF,'rtl/execute/randomx_fp64.v','rtl/execute/randomx_fp128.v'];INC=['-Irtl/execute','-I'+V,'-I'+V+'8086-SSE'];ENGINE=['rtl/aes/vendor/secworks/aes_sbox.v','rtl/aes/vendor/secworks/aes_inv_sbox.v','rtl/aes/randomx_aes_round.v','rtl/aes/randomx_v2_aes_mix.v','rtl/aes/randomx_exec_aes_commit.v','rtl/iteration/randomx_iteration_store.v','rtl/engine/randomx_i32_to_f64.v','rtl/engine/randomx_iteration_engine.v','rtl/execute/randomx_mul64.v','rtl/execute/randomx_reciprocal32.v','rtl/execute/randomx_integer_execute.v','rtl/execute/randomx_integer_iteration.v']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((N/'inputs.json').read_text())
for name,digest in inputs.items():assert sha(R/name)==digest,name
(D/'inputs.json').write_text(json.dumps({'code_inputs':inputs,'prior_artifact_manifest_sha256':sha(N/'artifacts.sha256.json'),'mapped_vectors_sha256':sha(N/'fp128-mapped.hex'),'mapping_driver_sha256':sha(Path(__file__))},indent=2)+'\n')
def run(label,argv):
 row={'label':label,'argv':argv,'cwd':'frozen-source','timeout_seconds':2400};commands.append(row);start=time.monotonic();print('START '+label,flush=True)
 try:
  with (D/(label+'.log')).open('w') as f:subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=2400)
  row['returncode']=0
 finally:row['elapsed_seconds']=time.monotonic()-start;(D/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 print('PASS '+label,flush=True)
def same(label,ref):assert (D/(label+'.log')).read_text().splitlines()[0]==(N/(ref+'.log')).read_text().splitlines()[0],label
summary={'mapping':{},'mapped':{}}
try:
 for lanes in (1,2):
  label=f'fp128-{lanes}';net=D/('netlist-'+label+'.v');cmd=f'read_verilog -I{V} -I{V}8086-SSE {" ".join(FP)}; chparam -set LANES {lanes} randomx_fp128; synth -top randomx_fp128 -flatten; check -assert; tee -o {D}/stat-{label}.txt stat; write_verilog -noattr {net}; write_json {D}/netlist-{label}.json';run('synth-'+label,['yosys','-p',cmd]);types=Counter()
  with (D/('netlist-'+label+'.json')).open() as f:
   for line in f:
    m=re.fullmatch(r'\s*"type": "([^\"]+)",\s*\n?',line)
    if m:types[m[1]]+=1
  assert sum(types.values())==int(re.search(r'Number of cells:\s*(\d+)',(D/('stat-'+label+'.txt')).read_text()).group(1))
  summary['mapping'][str(lanes)]={'num_cells':sum(types.values()),'flop_cells':sum(n for t,n in types.items() if 'DFF' in t),'num_cells_by_type':dict(types)}
  label=f'unit-mapped-{lanes}';run('compile-'+label,['iverilog','-g2012','-Wall',*INC,'-DFP128_NETLIST','-s','tb_fp128',f'-Ptb_fp128.LANES={lanes}','-o',str(D/(label+'.vvp')),str(net),'rtl/execute/tests/tb_fp128.v']);run(label,['vvp',str(D/(label+'.vvp')),'+vectors='+str(N/'fp128-mapped.hex')]);same(label,f'unit-corpus-{lanes}')
  for suffix in ('0','1','errors'):
   label=f'mapped-unit-{lanes}-{suffix}';tb='tb_floating_errors' if suffix=='errors' else 'tb_floating_iteration';argv=['iverilog','-g2012','-Wall',*INC,'-I'+str(N),'-DFP128_NETLIST','-s',tb,f'-P{tb}.FP_LANES={lanes}']
   if suffix!='errors':argv += [f'-P{tb}.STALL={suffix}']
   argv += ['-o',str(D/(label+'.vvp')),*ENGINE,str(net),'rtl/execute/tests/'+tb+'.v'];run('compile-'+label,argv)
   argv=['vvp',str(D/(label+'.vvp'))]
   if suffix=='errors':argv+=['+unsupported='+str(N/'unsupported.mem')]
   else:argv += [f'+{arg}={N/file}' for arg,file in [('initial','initial.hex'),('final','final.hex'),('programs','programs.mem'),('steps','steps.mem'),('events','events.mem'),('targets','targets.mem')]]
   run(label,argv);same(label,f'rtl-{lanes}-{suffix}')
  summary['mapped'][str(lanes)]='native primitive+connected ideal/stalled/error firstPASS+cycle records identical'
 (D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
except Exception as e:(D/'failure.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)},indent=2)+'\n');raise
finally:
 (D/'artifacts.sha256.json').write_text(json.dumps({p.name:sha(p) for p in D.iterdir() if p.is_file() and p.name!='artifacts.sha256.json'},indent=2)+'\n')
