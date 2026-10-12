#!/usr/bin/env python3
"""Differential pinned iteration-to-SRAM integration and cycle measurements.

The RTL covers only the post-dataset tail. The reference executes unchanged
iteration/bytecode code with a controlled program and dataset-line fixture.
"""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'rtl/aes'
TAIL=ROOT/'rtl/iteration'
RTL=['rtl/aes/vendor/secworks/aes_sbox.v','rtl/aes/vendor/secworks/aes_inv_sbox.v',
     'rtl/aes/randomx_aes_round.v','rtl/aes/randomx_v2_aes_mix.v',
     'rtl/aes/randomx_exec_aes_commit.v','rtl/iteration/randomx_iteration_store.v']
ORACLE=['rtl/iteration/tests/oracle.cpp','vendor/randomx/src/soft_aes.cpp',
        'vendor/randomx/src/bytecode_machine.cpp','vendor/randomx/src/instructions_portable.cpp',
        'vendor/randomx/src/reciprocal.c']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--synthesize',action='store_true')
    a=parser.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:parser.error('output must be outside source')
    if out.exists():parser.error('output must be fresh; preserve prior attempts')
    if any(c.isspace() or c in ';"\\' for c in str(out)):parser.error('output requires a quote-free path')
    for name in ['g++','iverilog','vvp']+(['yosys'] if a.synthesize else []):
        if not shutil.which(name):parser.error('tool unavailable: '+name)
    out.mkdir(parents=True);commands=[]
    def run(label,argv,timeout=300):
        commands.append({'label':label,'argv':argv,'cwd':'repository-root','timeout_seconds':timeout})
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        with (out/(label+'.log')).open('w') as f:
            subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=timeout)
    run('vendor',['python3','scripts/verify_vendor.py'])
    # Preserve PR49's immutable reviewed core; do not replace or rebuild its suite.
    core_inputs=json.loads((ROOT/'docs/validation/aes-rtl-corrected-20261012/inputs.json').read_text())
    for path,digest in core_inputs.items():
        if sha(ROOT/path)!=digest:raise RuntimeError('reviewed core changed: '+path)
    source=ROOT/'vendor/randomx/src/vm_interpreted.cpp';s=source.read_text()
    begin=s.index('\t\t\tuint64_t spMix =');end=s.index('\n\t\t}\n\n\t\tfor',begin)
    iteration=s[begin:end]
    begin=s.index('\t\tuint64_t* datasetLine =');end=s.index('\n\t}\n',begin)
    dataset=s[begin:end]
    virtual=(ROOT/'vendor/randomx/src/virtual_machine.cpp').read_text()
    begin=virtual.index('randomx_vm::~randomx_vm() {');end=virtual.index('\n}',begin)+2
    generated={'pinned_iteration.inc':iteration,'pinned_dataset_read.inc':dataset,
               'pinned_destructor.inc':virtual[begin:end]}
    notices={'pinned_iteration.inc':s[:s.index('*/')+2],
             'pinned_dataset_read.inc':s[:s.index('*/')+2],
             'pinned_destructor.inc':virtual[:virtual.index('*/')+2]}
    for name,data in generated.items():(out/name).write_text(notices[name]+'\n'+data)
    (out/'extraction.json').write_text(json.dumps({
        'RandomX_commit':'aaafe71322df6602c21a5c72937ac284724ae561',
        'source_sha256':sha(source),'policy':'verbatim iteration, dataset-read body and destructor; controlled bytecode program/dataset fixture only',
        'generated_sha256':{name:sha(out/name) for name in generated},
        'verbatim_body_sha256':{name:hashlib.sha256(data.encode()).hexdigest() for name,data in generated.items()}},indent=2)+'\n')
    inputs={str(p.relative_to(ROOT)):sha(p) for p in sorted((TAIL/'tests').glob('*'))}
    for path in RTL+ORACLE+['scripts/test_iteration_tail.py','vendor/randomx.sha256.json',
                         'vendor/randomx.lock.json','vendor/randomx/src/vm_interpreted.cpp',
                         'vendor/randomx/src/virtual_machine.cpp']:
        inputs[path]=sha(ROOT/path)
    (out/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    versions={}
    for tool,flag in [('g++','--version'),('iverilog','-V'),('vvp','-V')]+([('yosys','-V')] if a.synthesize else []):
        versions[tool]=subprocess.check_output([tool,flag],stderr=subprocess.STDOUT,text=True)
    (out/'tools.json').write_text(json.dumps(versions,indent=2)+'\n')
    for src,dst in [(TAIL/'LICENSE','LICENSE-OpenRX'),(CORE/'vendor/secworks/LICENSE','LICENSE-secworks'),
                    (ROOT/'vendor/randomx/LICENSE','LICENSE-RandomX')]:shutil.copyfile(src,out/dst)
    run('compile-oracle',['g++','-std=c++11','-O2','-I'+str(out),'-Ivendor/randomx/src',
                         *ORACLE,'-o',str(out/'oracle')])
    run('oracle',[str(out/'oracle'),str(out)])
    if not (out/'oracle.log').read_text().startswith('PASS software iterations=128'):
        raise RuntimeError('missing software iteration acceptance')
    summary={'source_base':'9a3271d515b8bf4c3f25ec43571b495fe3cb8f5c',
             'scope':'hardware post-dataset iteration tail and ordered SRAM stores; reference uses actual pinned bytecode/iteration body with dataset fixture; no full core/hash/timing proof',
             'seed':'0x697465722d746169','configurations':{}}
    for lanes,overlap in [(1,0),(1,1),(4,0),(4,1)]:
        tag=f'{lanes}-{overlap}'
        run('compile-'+tag,['iverilog','-g2012','-Wall','-s','tb_iteration',
            f'-Ptb_iteration.LANES={lanes}',f'-Ptb_iteration.OVERLAP_R={overlap}',
            '-o',str(out/(tag+'.vvp')),*RTL,'rtl/iteration/tests/tb_iteration.v'])
        args=['+initial='+str(out/'initial.hex'),'+final='+str(out/'final.hex'),
              '+trace='+str(out/'iterations.hex')]
        run('rtl-'+tag,['vvp',str(out/(tag+'.vvp')),*args])
        log=(out/('rtl-'+tag+'.log')).read_text()
        m=re.search(r'PASS tail lanes=(\d+) overlap=(\d+) iterations=128 v2=64 v1=64 writes=1024 aliases=32 full_memory_bytes=2097152 reset_aborts=2 interval_cycles=(\d+) v2_elapsed_cycles=(\d+)',log)
        if not m:raise RuntimeError('missing differential tail acceptance')
        cfg={'lanes':lanes,'overlap_R_writes':overlap,'interval_cycles':int(m.group(3)),
             'v2_64_elapsed_cycles':int(m.group(4)),'trace_iterations':128,'SRAM_writes':1024,
             'full_memory_bytes_compared':2097152,'alias_cases':32,'partial_reset_cases':2}
        summary['configurations'][tag]=cfg
        # Synthesize delivered overlap configurations; reference scheduling remains RTL comparison.
        if a.synthesize and overlap:
            cmd=(f'read_verilog {" ".join(RTL)}; chparam -set LANES {lanes} -set OVERLAP_R 1 randomx_iteration_store; '
                 'synth -top randomx_iteration_store -flatten; check -assert; '
                 f'tee -o {out}/stat-{lanes}.txt stat; write_verilog -noattr {out}/netlist-{lanes}.v; '
                 f'write_json {out}/netlist-{lanes}.json')
            run('synth-'+str(lanes),['yosys','-p',cmd])
            module=json.loads((out/f'netlist-{lanes}.json').read_text())['modules']['randomx_iteration_store']
            types=Counter(c['type'] for c in module['cells'].values());cfg['generic_synthesis']={
                'num_cells':len(module['cells']),'num_cells_by_type':dict(sorted(types.items())),
                'flop_cells':sum(n for t,n in types.items() if 'DFF' in t)}
            run('compile-netlist-'+str(lanes),['iverilog','-g2012','-DITERATION_NETLIST','-s','tb_iteration',
                f'-Ptb_iteration.LANES={lanes}','-Ptb_iteration.OVERLAP_R=1','-o',str(out/f'netlist-{lanes}.vvp'),
                str(out/f'netlist-{lanes}.v'),'rtl/iteration/tests/tb_iteration.v'])
            run('netlist-'+str(lanes),['vvp',str(out/f'netlist-{lanes}.vvp'),*args])
            if (out/f'netlist-{lanes}.log').read_text()!=log:raise RuntimeError('mapped tail differs')
    summary['comparison']={'shared_overlap_interval':21,'shared_serial_interval':25,
        'four_overlap_interval':9,'four_serial_interval':13,'shared_overlap_speedup_per_clock':25/21,
        'four_overlap_speedup_per_clock':13/9,'four_vs_shared_overlap_per_clock':21/9}
    bad=subprocess.run(['iverilog','-g2012','-s','randomx_iteration_store',
        '-Prandomx_iteration_store.OVERLAP_R=2','-o',str(out/'invalid.vvp'),*RTL],
        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (out/'invalid-overlap.log').write_text(bad.stdout)
    if bad.returncode==0 or 'requires_OVERLAP_R_0_or_1' not in bad.stdout:
        raise RuntimeError('invalid scheduling parameter not rejected')
    summary['invalid_overlap_rejected']=True
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'artifacts.sha256.json').write_text(json.dumps({p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
