#!/usr/bin/env python3
"""Reproduce the v2 AES execution-stage oracle, RTL tests and generic synthesis.

Requires C++11 g++, Icarus Verilog, and (with --synthesize) Yosys/ABC.
All generated data stays in a fresh output directory outside the source tree.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / 'rtl/aes'
IP = RTL / 'vendor/secworks'
SOURCES = [IP / 'aes_sbox.v', IP / 'aes_inv_sbox.v',
           RTL / 'randomx_aes_round.v', RTL / 'randomx_v2_aes_mix.v',
           RTL / 'randomx_exec_aes_commit.v']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--synthesize', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('output must be outside the source tree')
    if out.exists():
        parser.error('output must be a fresh directory; preserve earlier attempts')
    if args.synthesize and any(c.isspace() or c in ';"\\' for c in str(out)):
        parser.error('synthesis output path must not contain whitespace, quotes, ; or backslash')
    tools = ['g++', 'iverilog', 'vvp'] + (['yosys'] if args.synthesize else [])
    for tool in tools:
        if not shutil.which(tool):
            parser.error('required tool unavailable: ' + tool)
    out.mkdir(parents=True)
    commands = []

    def run(label, cmd, timeout=120):
        # Use a stable cwd and relative source paths in recorded commands/logs.
        commands.append({'label': label, 'argv': cmd, 'cwd': 'repository-root',
                         'timeout_seconds': timeout})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        with (out / (label+'.log')).open('w') as log:
            subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=timeout)

    run('vendor-randomx', ['python3', 'scripts/verify_vendor.py'])
    ip_manifest = json.loads((IP / 'UPSTREAM.json').read_text())
    for name, info in ip_manifest['files'].items():
        if digest(IP / name) != info['sha256']:
            raise RuntimeError('secworks IP integrity mismatch: '+name)
    versions = {}
    for tool, option in [('g++','--version'),('iverilog','-V'),('vvp','-V')]+(
            [('yosys','-V')] if args.synthesize else []):
        result = subprocess.run([tool, option], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, check=True)
        versions[tool] = result.stdout
    (out / 'tools.json').write_text(json.dumps(versions, indent=2)+'\n')
    source_inputs = SOURCES + list((RTL / 'tests').glob('*')) + [
        IP / 'LICENSE', IP / 'UPSTREAM.json', Path(__file__).resolve(),
        ROOT / 'vendor/randomx.lock.json', ROOT / 'vendor/randomx.sha256.json']
    for relative in ['soft_aes.cpp','soft_aes.h','intrin_portable.h','blake2/endian.h','common.hpp']:
        source_inputs.append(ROOT / 'vendor/randomx/src' / relative)
    (out / 'inputs.json').write_text(json.dumps({
        str(p.relative_to(ROOT)): digest(p) for p in sorted(set(source_inputs))
    }, indent=2)+'\n')
    run('compile-oracle', ['g++','-std=c++11','-O2','-Wall','-Wextra',
                          '-Ivendor/randomx/src','rtl/aes/tests/oracle.cpp',
                          'vendor/randomx/src/soft_aes.cpp','-o',str(out / 'oracle')])
    run('oracle', [str(out / 'oracle'), str(out)])
    source_args = [str(p.relative_to(ROOT)) for p in SOURCES]
    run('compile-round', ['iverilog','-g2012','-Wall','-s','tb_round','-o',
                         str(out / 'round.vvp'),*source_args,'rtl/aes/tests/tb_round.v'])
    run('round', ['vvp',str(out / 'round.vvp'),'+vectors='+str(out / 'rounds.hex')])
    summary = {'oracle_seed': '0x4f70656e52587632', 'round_vectors': 1024,
               'mix_vectors_per_configuration': 256, 'configurations': {}}
    for lanes in [1,4]:
        run(f'compile-mix-{lanes}', ['iverilog','-g2012','-Wall','-s','tb_mix',
            f'-Ptb_mix.LANES={lanes}','-o',str(out / f'mix-{lanes}.vvp'),
            *source_args,'rtl/aes/tests/tb_mix.v'])
        run(f'mix-{lanes}', ['vvp',str(out / f'mix-{lanes}.vvp'),
                           '+vectors='+str(out / 'mixes.hex')])
        log = (out / f'mix-{lanes}.log').read_text()
        match = re.search(r'PASS lanes=(\d+) mixes=(\d+) directed=(\d+) '
                          r'reset_aborts=(\d+) stalls=(\d+) availability_cycles=(\d+) '
                          r'interval_cycles=(\d+) stream_cycles=(\d+)', log)
        if not match:
            raise RuntimeError('missing RTL acceptance marker')
        names = ['lanes','mixes','directed','reset_aborts','stalls',
                 'availability_cycles','interval_cycles','stream_cycles']
        config = dict(zip(names, map(int,match.groups())))
        summary['configurations'][str(lanes)] = config
        run(f'compile-commit-{lanes}', ['iverilog','-g2012','-Wall','-s','tb_commit',
            f'-Ptb_commit.LANES={lanes}','-o',str(out / f'commit-{lanes}.vvp'),
            *source_args,'rtl/aes/tests/tb_commit.v'])
        run(f'commit-{lanes}', ['vvp',str(out / f'commit-{lanes}.vvp'),
                              '+vectors='+str(out / 'mixes.hex')])
        commit_log = (out / f'commit-{lanes}.log').read_text()
        config['integration_tests'] = commit_log.strip().splitlines()
        if f'phase=0 v2=256 v1=0 cycles={256*(16//lanes+1)}' not in commit_log or 'phase=1 v2=128 v1=128' not in commit_log:
            raise RuntimeError('missing execution integration acceptance markers')
        if args.synthesize:
            synth = (f'read_verilog {" ".join(source_args)}; '
                     f'chparam -set LANES {lanes} randomx_exec_aes_commit; '
                     'synth -top randomx_exec_aes_commit -flatten; check -assert; '
                     f'tee -o {out / ("stat-"+str(lanes)+".json")} stat -json; '
                     f'write_verilog -noattr {out / ("netlist-"+str(lanes)+".v")}; '
                     f'write_json {out / ("netlist-"+str(lanes)+".json")}')
            run(f'synth-{lanes}', ['yosys','-p',synth], timeout=300)
            stats = json.loads((out / f'stat-{lanes}.json').read_text())
            module = stats['modules']['\\randomx_exec_aes_commit']
            config['generic_synthesis'] = module
            # Check the actual ABC-mapped netlist with the same interface testbench.
            run(f'compile-netlist-{lanes}', ['iverilog','-g2012','-s','tb_commit',
                f'-Ptb_commit.LANES={lanes}','-o',str(out / f'netlist-{lanes}.vvp'),
                str(out / f'netlist-{lanes}.v'),'rtl/aes/tests/tb_commit.v'])
            run(f'netlist-{lanes}', ['vvp',str(out / f'netlist-{lanes}.vvp'),
                                   '+vectors='+str(out / 'mixes.hex')])
            if (out / f'netlist-{lanes}.log').read_text() != commit_log:
                raise RuntimeError('synthesized netlist differs from RTL results/cycles')
    # Reject unsupported configuration during elaboration.
    bad = subprocess.run(['iverilog','-g2012','-s','randomx_v2_aes_mix',
        '-Prandomx_v2_aes_mix.LANES=2','-o',str(out / 'invalid.vvp'),*source_args],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (out / 'invalid-parameter.log').write_text(bad.stdout)
    if bad.returncode == 0 or 'requires_LANES_1_or_4' not in bad.stdout:
        raise RuntimeError('invalid LANES was not rejected')
    summary['invalid_parameter_rejected'] = True
    summary['scope'] = 'component RTL/netlist cycles and generic cells; no physical timing/area/power or whole-hash speedup'
    (out / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (out / 'artifacts.sha256.json').write_text(json.dumps({
        p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()
    }, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
