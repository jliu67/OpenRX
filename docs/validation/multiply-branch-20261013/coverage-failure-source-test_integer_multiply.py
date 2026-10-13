#!/usr/bin/env python3
"""Native multiply/reciprocal/branch RTL, actual mapped units and integrated top."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode=True
from test_iteration_engine import extract, RTL as ENGINE_RTL

ROOT=Path(__file__).resolve().parents[1]
BASE='2b14e4f9a726c1f7e066576bbe8fc351c87d158c'
MUL='rtl/execute/randomx_mul64.v'
RCP='rtl/execute/randomx_reciprocal32.v'
CORE='rtl/execute/randomx_integer_execute.v'
WRAPPER='rtl/execute/randomx_integer_iteration.v'
RTL=[*ENGINE_RTL,MUL,RCP,CORE,WRAPPER]
SUPPORTED={'IADD_RS','IADD_M','ISUB_R','ISUB_M','INEG_R','IXOR_R','IXOR_M','IROR_R','IROL_R','ISWAP_R','ISTORE',
           'IMUL_R','IMUL_M','IMULH_R','IMULH_M','ISMULH_R','ISMULH_M','IMUL_RCP','CBRANCH'}
LIBS=['vendor/randomx/src/soft_aes.cpp','vendor/randomx/src/bytecode_machine.cpp',
      'vendor/randomx/src/instructions_portable.cpp','vendor/randomx/src/reciprocal.c']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def opcode_map(out):
    source=(ROOT/'vendor/randomx/src/configuration.h').read_text()
    kinds=[];ceils={}
    for name,count in re.findall(r'^#define RANDOMX_FREQ_(\w+)\s+(\d+)\s*$',source,re.M):
        kinds.extend([name]*int(count));ceils[name]=len(kinds)
    header=(ROOT/'rtl/execute/randomx_opcode_ceils.vh').read_text()
    declared={name:int(value) for name,value in re.findall(r'localparam integer CEIL_(\w+)=(\d+);',header)}
    if len(kinds)!=256 or ceils!=declared:raise RuntimeError('opcode ceilings differ from unchanged native configuration')
    if not re.search(r'RANDOMX_JUMP_BITS\s+8\b',source) or not re.search(r'RANDOMX_JUMP_OFFSET\s+8\b',source):
        raise RuntimeError('branch constants differ from pinned configuration')
    accepted={op for op,kind in enumerate(kinds) if kind in SUPPORTED}
    if len(accepted)!=161:raise RuntimeError('integer/branch opcode set differs')
    (out/'unsupported.mem').write_text('\n'.join('0' if op in accepted else '1' for op in range(256))+'\n')
    (out/'opcode-map.json').write_text(json.dumps({'ceils':ceils,'supported_raw':sorted(accepted),
        'unsupported_raw':sorted(set(range(256))-accepted),'pin':'aaafe71322df6602c21a5c72937ac284724ae561'},indent=2)+'\n')
    return kinds,accepted

def vectors(out,kinds,accepted):
    names=('versions chains ev_start ev_count read0 read1 read2 read3 round_in round_out sp0 sp1 mx ma em0 em1 offset '
           'rin ain loadr loadf loade expr expf expe dsaddr pfaddr dsdata outr outf oute outmx outma fline rline fmem rmem').split()
    rows=[x.split() for x in (out/'iterations.hex').read_text().splitlines()]
    events=[x.split() for x in (out/'accesses.hex').read_text().splitlines()]
    steps=[x.split() for x in (out/'instruction-steps.hex').read_text().splitlines()]
    oracle=json.loads((out/'oracle-summary.json').read_text())
    if len(rows)!=8 or len(events)>2048 or len(steps)>8192:raise RuntimeError('native fixture bounds')
    lines=[f'localparam integer TOTAL_EVENTS={len(events)},BYTECODE_READS={oracle["bytecode_read64"]},'
        f'BYTECODE_STORES={oracle["bytecode_store64"]},TOTAL_STEPS={len(steps)},MULTIPLY_STEPS={oracle["multiply_steps"]},'
        f'BRANCH_STEPS={oracle["branch_steps"]},BRANCH_TAKEN={oracle["branch_taken"]},RCP_NOPS={oracle["rcp_nops"]};']
    for case,row in enumerate(rows):
        if len(row)!=38 or int(row[0])!=case:raise RuntimeError('iteration vector format')
        for column,(name,value) in enumerate(zip(names,row[1:])):
            lines.append(f'{name}[{case}]='+(value if column<10 else "'h"+value)+';')
        start=next(i for i,s in enumerate(steps) if int(s[0])==case)
        count=sum(int(s[0])==case for s in steps)
        lines += [f'step_start[{case}]={start};',f'step_count[{case}]={count};']
    (out/'multiply_vectors.vh').write_text('\n'.join(lines)+'\n')
    programs=[0]*4096;targets=[511]*4096;raw=set();instructions={}
    for case,pc,word in [x.split() for x in (out/'programs.hex').read_text().splitlines()]:
        case,pc,word=int(case),int(pc),int(word,16)
        if not 0<=pc<(384 if case<4 else 256) or (case,pc) in instructions:raise RuntimeError('program word bounds')
        instructions[case,pc]=word;programs[case*512+pc]=word;raw.add(word&255)
    if raw!=accepted or len(instructions)!=2560:raise RuntimeError('raw supported opcode coverage')
    for case,pc,op,target in [x.split() for x in (out/'compiled-targets.hex').read_text().splitlines()]:
        case,pc,op,target=int(case),int(pc),int(op),int(target)
        if instructions[case,pc]&255!=op:raise RuntimeError('native compiled opcode differs')
        if kinds[op]=='CBRANCH' and not 0<=target<=pc:raise RuntimeError('native branch target bound')
        if kinds[op]!='CBRANCH' and target!=-1:raise RuntimeError('nonbranch native target')
        targets[case*512+pc]=target if target>=0 else 511
    encoded_events=[]
    for case,pc,write,address,data in events:
        case,pc,write,address,data=int(case),int(pc),int(write),int(address,16),int(data,16)
        if not 0<=address<=2097152-8 or address%8 or write not in (0,1):raise RuntimeError('memory event bounds')
        encoded_events.append(f'{(write<<85)|(address<<64)|data:022x}')
    encoded_steps=[];counts=Counter();rotates=set();shifts=set();masks=set();branch_conditions=set();branch_targets=set()
    previous={case:int(row[names.index('loadr')+1],16) for case,row in enumerate(rows)}
    next_pc={case:0 for case in range(8)};case_order=[]
    for case,pc,op,word,nxt in steps:
        case,pc,op,word,nxt=int(case),int(pc),int(op),int(word,16),int(nxt)
        if pc!=next_pc[case] or instructions[case,pc]&255!=op:raise RuntimeError('native dynamic instruction order')
        ins=instructions[case,pc];kind=kinds[op];dst=(ins>>8)&7;src=(ins>>16)&7;mod=(ins>>24)&255;imm=ins>>32
        r=[(previous[case]>>(64*i))&((1<<64)-1) for i in range(8)];counts[kind]+=1
        if kind in ('IROR_R','IROL_R'):rotates.add((imm if dst==src else r[src])&63)
        if kind=='IADD_RS':shifts.add((mod>>2)&3)
        if kind.endswith('_M') or kind=='ISTORE':
            masks.add('L3' if (kind=='ISTORE' and mod>>4>=14 or kind!='ISTORE' and dst==src) else ('L1' if mod&3 else 'L2'))
        if kind=='CBRANCH':
            condition=mod>>4;branch_conditions.add(condition);target=targets[case*512+pc];branch_targets.add(target)
            if nxt not in (pc+1,target):raise RuntimeError('native branch next-PC/compiled target differ')
            counts['taken']+=nxt<=pc;counts['jump_zero']+=nxt==0;counts['self_jump']+=nxt==pc
            counts['target_after_branch']+=target>0 and kinds[instructions[case,target-1]&255]=='CBRANCH'
        elif nxt!=pc+1:raise RuntimeError('nonbranch changed native PC')
        if kind=='IMUL_RCP':counts['reciprocal_nops']+=imm==0 or imm&(imm-1)==0
        previous[case]=word;next_pc[case]=nxt;case_order.append(case)
        encoded_steps.append(f'{(pc<<529)|(nxt<<520)|(op<<512)|word:0135x}')
    if case_order!=sorted(case_order) or any(next_pc[c]!=(384 if c<4 else 256) for c in range(8)):
        raise RuntimeError('native control flow completion')
    if branch_conditions!=set(range(16)) or not all(counts[k] for k in ['taken','jump_zero','self_jump','target_after_branch','reciprocal_nops']):
        raise RuntimeError('native branch/NOP control coverage')
    if rotates!=set(range(64)) or shifts!=set(range(4)) or masks!={'L1','L2','L3'}:raise RuntimeError('integer rotate/shift/address coverage')
    (out/'programs.mem').write_text('\n'.join(f'{x:016x}' for x in programs)+'\n')
    (out/'targets.mem').write_text('\n'.join(f'{x:03x}' for x in targets)+'\n')
    (out/'steps.mem').write_text('\n'.join(encoded_steps)+'\n')
    (out/'events.mem').write_text('\n'.join(encoded_events)+'\n')
    coverage={'counts':dict(counts),'supported_raw_values':sorted(raw),'rotate_counts':sorted(rotates),
        'shifts':sorted(shifts),'masks':sorted(masks),'branch_conditions':sorted(branch_conditions),
        'native_target_values':sorted(branch_targets),'policy':'native compile targets and dynamic outcomes are assertions only'}
    (out/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    return oracle,coverage

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--synthesize',action='store_true');args=parser.parse_args();out=args.output.resolve()
    if out.exists() or out==ROOT or ROOT in out.parents:parser.error('fresh output outside source required')
    if not re.fullmatch(r'[-A-Za-z0-9_./]+',str(out)):parser.error('unambiguous HDL output path required')
    tools=[('g++','--version'),('iverilog','-V'),('vvp','-V')]+([('yosys','-V')] if args.synthesize else [])
    for tool,_ in tools:
        if not shutil.which(tool):parser.error('tool unavailable: '+tool)
    out.mkdir(parents=True);commands=[]
    def run(label,argv,timeout=1500):
        record={'label':label,'argv':argv,'cwd':'repository-root','timeout_seconds':timeout};commands.append(record)
        print('START '+label,flush=True);start=time.monotonic()
        try:
            with (out/(label+'.log')).open('w') as log:subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=timeout)
            record['returncode']=0
        except Exception as error:record['error']=str(error);raise
        finally:record['elapsed_seconds']=time.monotonic()-start;(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        print('PASS '+label,flush=True)
    def stats(label):
        text=(out/(label+'.log')).read_text();return {k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',text.splitlines()[0])}
    def check_log(label,prefix,reference=None):
        line=(out/(label+'.log')).read_text().splitlines()[0]
        if not line.startswith(prefix):raise RuntimeError('acceptance missing: '+label)
        if reference and line!=(out/(reference+'.log')).read_text().splitlines()[0]:raise RuntimeError('mapped result/cycles differ: '+label)
    def test_units(radix,label,mul_net=None,rcp_net=None):
        flags=['-DMUL64_NETLIST'] if mul_net else [];sources=[str(mul_net) if mul_net else MUL,str(rcp_net) if rcp_net else RCP]
        run('compile-'+label,['iverilog','-g2012','-Wall',*flags,'-s','tb_arithmetic',f'-Ptb_arithmetic.RADIX4={radix}',
            '-o',str(out/(label+'.vvp')),*sources,'rtl/execute/tests/tb_arithmetic.v'])
        run(label,['vvp',str(out/(label+'.vvp')),'+multiply='+str(out/'multiply.hex'),'+reciprocal='+str(out/'reciprocal.hex')])
        check_log(label,f'PASS arithmetic radix4={radix} products=2304 reciprocal=',f'unit-rtl-{radix}' if mul_net else None)
        return stats(label)
    def test_connected(radix,label,mul_net=None,rcp_net=None,top_net=None):
        flags=['-DINTEGER_ITERATION_NETLIST'] if top_net else (['-DMUL64_NETLIST'] if mul_net else [])
        sources=[str(top_net)] if top_net else [*ENGINE_RTL,str(mul_net) if mul_net else MUL,str(rcp_net) if rcp_net else RCP,CORE,WRAPPER]
        results={}
        for stall in [0,1]:
            name=f'{label}-{stall}';run('compile-'+name,['iverilog','-g2012','-Wall',*flags,'-Irtl/execute','-I'+str(out),
                '-s','tb_multiply_iteration',f'-Ptb_multiply_iteration.MUL_RADIX4={radix}',f'-Ptb_multiply_iteration.STALL={stall}',
                '-o',str(out/(name+'.vvp')),*sources,'rtl/execute/tests/tb_multiply_iteration.v'])
            run(name,['vvp',str(out/(name+'.vvp')),*[f'+{arg}={out/file}' for arg,file in
                [('initial','initial.hex'),('final','final.hex'),('programs','programs.mem'),('steps','steps.mem'),('events','events.mem'),('targets','targets.mem')]]])
            check_log(name,f'PASS multiply_hardware radix4={radix} stall={stall} ',f'rtl-{radix}-{stall}' if mul_net or top_net else None)
            results[str(stall)]=stats(name)
        name=label+'-errors';run('compile-'+name,['iverilog','-g2012','-Wall',*flags,'-Irtl/execute','-s','tb_multiply_errors',
            f'-Ptb_multiply_errors.MUL_RADIX4={radix}','-o',str(out/(name+'.vvp')),*sources,'rtl/execute/tests/tb_multiply_errors.v'])
        run(name,['vvp',str(out/(name+'.vvp')),'+unsupported='+str(out/'unsupported.mem')])
        check_log(name,f'PASS multiply_errors radix4={radix} unsupported_raw_opcodes=95 held_errors=97 ',f'rtl-{radix}-errors' if mul_net or top_net else None)
        if 'reset_multiply=1 reset_reciprocal=1' not in (out/(name+'.log')).read_text():raise RuntimeError('arithmetic reset coverage missing')
        results['errors']=stats(name);return results
    def synth(label,top,sources,parameter=None):
        net=out/('netlist-'+label+'.v');command=f'read_verilog -Irtl/execute {" ".join(sources)}; '
        if parameter:command+=f'chparam -set {parameter[0]} {parameter[1]} {top}; '
        command+=f'synth -top {top} -flatten; check -assert; tee -o {out}/stat-{label}.txt stat; write_verilog -noattr {net}; write_json {out}/netlist-{label}.json'
        run('synth-'+label,['yosys','-p',command]);module=json.loads((out/('netlist-'+label+'.json')).read_text())['modules'][top]
        types=Counter(cell['type'] for cell in module['cells'].values());counts={'num_cells':len(module['cells']),
            'flop_cells':sum(n for t,n in types.items() if 'DFF' in t),'num_cells_by_type':dict(sorted(types.items())),
            'scope':'actual generic mapping; no physical timing/power or external memory area'}
        return net,counts
    try:
        run('vendor',['python3','scripts/verify_vendor.py']);preserved={}
        for name in ['aes-rtl-corrected-20261012/inputs.json','iteration-tail-v2-stalls-20261012/inputs.json','iteration-engine-read-grant-20261013/rtl-inputs.json']:
            path=ROOT/'docs/validation'/name;bindings=json.loads(path.read_text())
            for source,digest in bindings.items():
                if sha(ROOT/source)!=digest:raise RuntimeError('accepted component input changed: '+source)
            preserved[name]={'checked':len(bindings),'sha256':sha(path)}
        (out/'preserved-inputs.json').write_text(json.dumps(preserved,indent=2)+'\n')
        paths=set(RTL+LIBS+['scripts/test_integer_multiply.py','scripts/test_iteration_engine.py','rtl/execute/randomx_opcode_ceils.vh',
            'vendor/randomx.lock.json','vendor/randomx.sha256.json','vendor/randomx/src/configuration.h',
            'vendor/randomx/src/vm_interpreted.cpp','vendor/randomx/src/virtual_machine.cpp','vendor/randomx/src/bytecode_machine.hpp'])
        paths.update('rtl/execute/tests/'+name for name in ['arithmetic_oracle.cpp','multiply_oracle.cpp','tb_arithmetic.v','tb_multiply_iteration.v','tb_multiply_errors.v','tb_integer_transport.v'])
        (out/'inputs.json').write_text(json.dumps({p:sha(ROOT/p) for p in sorted(paths)},indent=2)+'\n')
        (out/'tools.json').write_text(json.dumps({t:subprocess.check_output([t,flag],stderr=subprocess.STDOUT,text=True) for t,flag in tools},indent=2)+'\n')
        for src,dst in [('rtl/execute/LICENSE','LICENSE-OpenRX'),('vendor/randomx/LICENSE','LICENSE-RandomX'),('rtl/aes/vendor/secworks/LICENSE','LICENSE-secworks')]:shutil.copyfile(ROOT/src,out/dst)
        kinds,accepted=opcode_map(out);extract(out)
        run('compile-arithmetic-oracle',['g++','-std=c++11','-O2','-Ivendor/randomx/src','rtl/execute/tests/arithmetic_oracle.cpp',LIBS[2],LIBS[3],'-o',str(out/'arithmetic-oracle')])
        run('arithmetic-oracle',[str(out/'arithmetic-oracle'),str(out)])
        run('compile-oracle',['g++','-std=c++11','-O2','-I'+str(out),'-Ivendor/randomx/src','rtl/execute/tests/multiply_oracle.cpp',*LIBS,'-o',str(out/'oracle')])
        run('oracle',[str(out/'oracle'),str(out)]);check_log('oracle','PASS native multiply-branch iterations=8')
        oracle,coverage=vectors(out,kinds,accepted)
        summary={'base':BASE,'scope':'all native integer and conditional branch operations; FP/CFROUND unsupported',
            'oracle':oracle,'coverage':coverage,'rtl':{},'unit_rtl':{},'synthesis_requested':args.synthesize,'mapping':{},'mapped':{}}
        for radix in [0,1]:
            summary['unit_rtl'][str(radix)]=test_units(radix,f'unit-rtl-{radix}')
            summary['rtl'][str(radix)]=test_connected(radix,f'rtl-{radix}')
        # Reuse the unchanged parent transport test against the extended core.
        run('compile-transport',['iverilog','-g2012','-Wall','-Irtl/execute','-s','tb_integer_transport','-o',str(out/'transport.vvp'),MUL,RCP,CORE,'rtl/execute/tests/tb_integer_transport.v'])
        run('transport',['vvp',str(out/'transport.vvp')]);check_log('transport','PASS integer_transport serial_iadd=0 contexts=8')
        summary['transport']=stats('transport')
        for top,parameter,sources,marker in [('randomx_mul64','RADIX4',[MUL],'multiplier_requires_RADIX4_0_or_1'),
                                            ('randomx_integer_execute','SERIAL_IADD',[MUL,RCP,CORE],'integer_execute_requires_SERIAL_IADD_0_or_1')]:
            cmd=['iverilog','-g2012','-Irtl/execute','-s',top,f'-P{top}.{parameter}=2','-o',str(out/('invalid-'+parameter+'.vvp')),*sources]
            proc=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            (out/('invalid-'+parameter+'.log')).write_text(proc.stdout);commands.append({'label':'invalid-'+parameter,'argv':cmd,'returncode':proc.returncode,'expected_failure':True})
            if proc.returncode==0 or marker not in proc.stdout:raise RuntimeError('invalid parameter accepted')
        summary['invalid_parameters_rejected']=True
        if args.synthesize:
            rcp_net,rcp_stats=synth('reciprocal','randomx_reciprocal32',[RCP]);summary['mapping']['reciprocal']=rcp_stats
            for radix in [0,1]:
                mul_net,mul_stats=synth(f'mul-{radix}','randomx_mul64',[MUL],('RADIX4',radix));summary['mapping'][f'mul-{radix}']=mul_stats
                summary['mapped'][f'unit-{radix}']=test_units(radix,f'unit-mapped-{radix}',mul_net,rcp_net)
                summary['mapped'][f'connected-{radix}']=test_connected(radix,f'mapped-units-{radix}',mul_net,rcp_net)
            net,top_stats=synth('integrated-0','randomx_integer_iteration',RTL,('MUL_RADIX4',0));summary['mapping']['integrated-default']=top_stats
            summary['mapped']['integrated-default']=test_connected(0,'mapped-integrated-0',top_net=net)
        comparison={}
        for stall in ['0','1']:
            fast=summary['rtl']['0'][stall];slow=summary['rtl']['1'][stall];delta=slow['elapsed_cycles']-fast['elapsed_cycles']
            if delta!=32*oracle['multiply_steps'] or slow['fetch_to_last_commit_cycles']-fast['fetch_to_last_commit_cycles']!=delta:
                raise RuntimeError('multiplier schedule cycle accounting differs')
            comparison[stall]={'iterative_extra_cycles':delta,'extra_per_multiply':32,'actual_multiply_operations':oracle['multiply_steps']}
        summary['comparison']={'cycles':comparison,'scope':'actual controlled program/port cycles; no natural mix, frequency or full-hash inference'}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
    except Exception as error:
        (out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'error':str(error)},indent=2)+'\n');raise
    finally:
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        (out/'artifacts.sha256.json').write_text(json.dumps({p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='artifacts.sha256.json'},indent=2)+'\n')

if __name__=='__main__':main()
