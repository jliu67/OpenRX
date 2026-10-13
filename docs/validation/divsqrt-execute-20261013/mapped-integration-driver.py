import hashlib,json,re,subprocess,time
from collections import Counter
from pathlib import Path
O=Path(__file__).resolve().parent;R=Path(json.loads((O/'workspace.json').read_text())['root']);N=Path('/tmp/openrx-divsqrt-connected-rtl-05');U=Path('/tmp/openrx-divsqrt-unit-mapping-01');D=Path('/tmp/openrx-divsqrt-integration-mapping-01');assert not D.exists();D.mkdir();commands=[]
V='rtl/execute/vendor/hardfloat/';HF=[V+n for n in ['HardFloat_primitives.v','HardFloat_rawFN.v','isSigNaNRecFN.v','fNToRecFN.v','recFNToFN.v','addRecFN.v','mulRecFN.v','divSqrtRecFN_small.v','8086-SSE/HardFloat_specialize.v']];FP=[*HF,'rtl/execute/randomx_fp64.v','rtl/execute/randomx_fp128.v','rtl/execute/randomx_divsqrt64.v','rtl/execute/randomx_divsqrt128.v'];INC=['-Irtl/execute','-I'+V,'-I'+V+'8086-SSE'];ENGINE=['rtl/aes/vendor/secworks/aes_sbox.v','rtl/aes/vendor/secworks/aes_inv_sbox.v','rtl/aes/randomx_aes_round.v','rtl/aes/randomx_v2_aes_mix.v','rtl/aes/randomx_exec_aes_commit.v','rtl/iteration/randomx_iteration_store.v','rtl/engine/randomx_i32_to_f64.v','rtl/engine/randomx_iteration_engine.v','rtl/execute/randomx_mul64.v','rtl/execute/randomx_reciprocal32.v','rtl/execute/randomx_integer_execute.v','rtl/execute/randomx_integer_iteration.v']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((N/'inputs.json').read_text())
for name,e in inputs.items():assert sha(R/name)==e,name
for source in (N,U):
 for name,e in json.loads((source/'artifacts.sha256.json').read_text()).items():assert sha(source/name)==e,name
(D/'inputs.json').write_text(json.dumps({'code_inputs':inputs,'RTL_artifact_manifest_sha256':sha(N/'artifacts.sha256.json'),'unit_artifact_manifest_sha256':sha(U/'artifacts.sha256.json'),'integration_driver_sha256':sha(Path(__file__))},indent=2)+'\n')
def run(label,argv):
 row={'label':label,'argv':argv,'cwd':'frozen-source','timeout_seconds':2400};commands.append(row);start=time.monotonic();print('START '+label,flush=True)
 try:
  with (D/(label+'.log')).open('w') as f:subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=2400)
  row['returncode']=0
 finally:row['elapsed_seconds']=time.monotonic()-start;(D/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 print('PASS '+label,flush=True)
try:
 net=D/'netlist-integrated-2.v';cmd=f'read_verilog -Irtl/execute -I{V} -I{V}8086-SSE {" ".join(ENGINE+FP)}; chparam -set DIVSQRT_LANES 2 randomx_integer_iteration; synth -top randomx_integer_iteration -flatten; check -assert; tee -o {D}/stat-integrated-2.txt stat; write_verilog -noattr {net}; write_json {D}/netlist-integrated-2.json';run('synth-integrated-2',['yosys','-p',cmd]);types=Counter()
 with (D/'netlist-integrated-2.json').open() as f:
  for line in f:
   m=re.fullmatch(r'\s*"type": "([^\"]+)",\s*\n?',line)
   if m:types[m[1]]+=1
 assert sum(types.values())==int(re.search(r'Number of cells:\s*(\d+)',(D/'stat-integrated-2.txt').read_text()).group(1))
 for suffix in ('0','1','errors'):
  label='mapped-integrated-2-'+suffix;tb='tb_divsqrt_cancel' if suffix=='errors' else 'tb_divsqrt_iteration';argv=['iverilog','-g2012','-Wall',*INC,'-I'+str(N),'-DINTEGER_ITERATION_NETLIST','-s',tb]
  if suffix!='errors':argv += [f'-P{tb}.STALL={suffix}']
  argv += ['-o',str(D/(label+'.vvp')),str(net),'rtl/execute/tests/'+tb+'.v'];run('compile-'+label,argv)
  argv=['vvp',str(D/(label+'.vvp'))]
  if suffix!='errors':argv += [f'+{arg}={N/file}' for arg,file in [('initial','initial.hex'),('final','final.hex'),('programs','programs.mem'),('steps','steps.mem'),('events','events.mem'),('targets','targets.mem')]]
  run(label,argv);assert (D/(label+'.log')).read_text().splitlines()[0]==(N/('rtl-2-'+suffix+'.log')).read_text().splitlines()[0]
 summary=json.loads((N/'summary.json').read_text());units=json.loads((U/'summary.json').read_text());summary['synthesis_requested']=True;summary['mapping']={f'divsqrt128-{k}':v for k,v in units['mapping'].items()};summary['mapping']['integrated-default']={'num_cells':sum(types.values()),'flop_cells':sum(n for t,n in types.items() if 'DFF' in t),'num_cells_by_type':dict(types),'scope':'actual generic mapping; no physical timing/power/external memory area'};summary['mapped']={'unit_variants':units['mapped'],'integrated-default':'all three native full-top mapped records equal RTL'};(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
except Exception as e:(D/'failure.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)},indent=2)+'\n');raise
finally:(D/'artifacts.sha256.json').write_text(json.dumps({p.name:sha(p) for p in D.iterdir() if p.is_file() and p.name!='artifacts.sha256.json'},indent=2)+'\n')
