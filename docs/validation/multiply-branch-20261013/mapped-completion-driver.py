"""Complete three mapped tests from the exact retained successful synthesis."""
import argparse,hashlib,json,re,shutil,subprocess,time
from collections import Counter
from pathlib import Path

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def stats(path):return {k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',path.read_text().splitlines()[0])}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--previous',type=Path,required=True);p.add_argument('--rtl',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=a.source.resolve();prev=a.previous.resolve();out=a.output.resolve();assert not out.exists() and root not in out.parents;out.mkdir();commands=[]
 def run(label,argv):
  row={'label':label,'argv':argv,'cwd':str(root)};commands.append(row);start=time.monotonic()
  try:
   with (out/(label+'.log')).open('w') as f:subprocess.run(argv,cwd=root,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=1500)
   row['returncode']=0
  finally:row['elapsed_seconds']=time.monotonic()-start;(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  print('PASS '+label,flush=True)
 try:
  inputs=json.loads((prev/'inputs.json').read_text())
  for name,digest in inputs.items():assert sha(root/name)==digest,name
  for name,digest in json.loads((prev/'artifacts.sha256.json').read_text()).items():assert sha(prev/name)==digest,name
  assert json.loads((prev/'failure.json').read_text())['type']=='BrokenPipeError'
  last=json.loads((prev/'commands.json').read_text())[-1];assert last['label']=='synth-integrated-0' and last['returncode']==0
  fixtures=['initial.hex','final.hex','programs.mem','steps.mem','events.mem','targets.mem','multiply_vectors.vh',
   'programs.hex','instruction-steps.hex','compiled-targets.hex','iterations.hex','accesses.hex','oracle-summary.json','extraction.json','unsupported.mem']
  for name in fixtures:
   assert (prev/name).read_bytes()==(a.rtl/name).read_bytes(),name;shutil.copyfile(prev/name,out/name)
  net=prev/'netlist-integrated-0.v';net_json=prev/'netlist-integrated-0.json'
  proof={'code_inputs':inputs,'retained_netlist_verilog_sha256':sha(net),'retained_netlist_json_sha256':sha(net_json),
   'prior_artifact_manifest_sha256':sha(prev/'artifacts.sha256.json'),'completion_driver_sha256':sha(Path(__file__)),
   'fixture_identity_verified':fixtures,'original_returncode':120,'original_failure':'terminal BrokenPipe after successful synthesis','no_synthesis_rerun':True}
  (out/'inputs.json').write_text(json.dumps(proof,indent=2)+'\n')
  results={}
  for suffix,tb,param in [('0','tb_multiply_iteration','-Ptb_multiply_iteration.STALL=0'),('1','tb_multiply_iteration','-Ptb_multiply_iteration.STALL=1'),('errors','tb_multiply_errors',None)]:
   name='mapped-integrated-0-'+suffix;exe=out/(name+'.vvp')
   argv=['iverilog','-g2012','-Wall','-DINTEGER_ITERATION_NETLIST','-Irtl/execute','-I'+str(out),'-s',tb]
   if param:argv.append(param)
   argv+=['-o',str(exe),str(net),'rtl/execute/tests/'+tb+'.v'];run('compile-'+name,argv)
   argv=['vvp',str(exe)]
   if suffix=='errors':argv+=['+unsupported='+str(out/'unsupported.mem')]
   else:argv += [f'+{arg}={out/file}' for arg,file in [('initial','initial.hex'),('final','final.hex'),('programs','programs.mem'),('steps','steps.mem'),('events','events.mem'),('targets','targets.mem')]]
   run(name,argv)
   line=(out/(name+'.log')).read_text().splitlines()[0];expected=(prev/('rtl-0-'+suffix+'.log')).read_text().splitlines()[0]
   assert line.startswith('PASS ') and line==expected,(name,line,expected);results[suffix]=stats(out/(name+'.log'))
  summary=json.loads((a.rtl/'summary.json').read_text());summary['synthesis_requested']=True;summary['mapping']={};summary['mapped']={}
  for label,top in [('reciprocal','randomx_reciprocal32'),('mul-0','randomx_mul64'),('mul-1','randomx_mul64'),('integrated-0','randomx_integer_iteration')]:
   types=Counter()
   with (prev/('netlist-'+label+'.json')).open() as f:
    for line in f:
     match=re.fullmatch(r'\s*"type": "([^\"]+)",\s*\n?',line)
     if match:types[match[1]]+=1
   expected=int(re.search(r'Number of cells:\s*(\d+)',(prev/('stat-'+label+'.txt')).read_text()).group(1));assert sum(types.values())==expected
   summary['mapping']['integrated-default' if label=='integrated-0' else label]={'num_cells':sum(types.values()),'flop_cells':sum(n for t,n in types.items() if 'DFF' in t),'num_cells_by_type':dict(sorted(types.items())),'scope':'actual generic mapping; no physical timing/power or external memory area'}
  for radix in (0,1):
   summary['mapped']['unit-'+str(radix)]=stats(prev/f'unit-mapped-{radix}.log')
   summary['mapped']['connected-'+str(radix)]={suffix:stats(prev/f'mapped-units-{radix}-{suffix}.log') for suffix in ('0','1','errors')}
  summary['mapped']['integrated-default']=results
  summary['completion_provenance']={'original_driver_returncode':120,'reason':'exec transport closed progress stdout after successful complete synthesis; no DUT or synthesis failure','focused_completion_returncode':0,'same_frozen_code_inputs':True,'native_fixtures_identical':True,'all_first_PASS_and_cycle_records_match':True,'actual_retained_netlists_reused':True,'no_synthesis_rerun':True}
  (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
  print('PASS all nine RTL / eleven mapped modes across exact retained source and successful mapped-only completion',flush=True)
 except Exception as error:(out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'error':str(error)},indent=2)+'\n');raise
 finally:
  (out/'artifacts.sha256.json').write_text(json.dumps({p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='artifacts.sha256.json'},indent=2)+'\n')
if __name__=='__main__':main()
