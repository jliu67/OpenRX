#!/usr/bin/env python3
"""Build a pinned simulator in-place under an admitted execution; never install.

All archives are explicit, SHA-256-checked inputs. Ubuntu packages are unpacked
only into this fresh output directory. No package database, host PATH, services,
permissions, repositories, system libraries or persistent environment is changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

PINS = {
    'verilator': '6c0e50774abe23c8a40b30745195ba16d91f3963894cf4944f2c7c19396606b7',
    'flex': '980674f410fa6cb5e41d1bdf434a9391dcec0ac8fae5194cd90f9598ae074d8d',
    'bison': '40ba998a24ce53a420fc3f8188b833fde276564df1a7e90acaf875f4f9b76c4e',
    'libfl2': 'b36df0dcc7b3c8769b51790fb37f780a7ca6148448af30ce572ab584ddf8a84a',
    'libfl-dev': '8c65612bacfb9a9e03759f80f64ccba1ca977d3511e22c10fd881b55a762efe0',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists():
        parser.error('fresh external output required')
    out.mkdir()
    pins = json.loads(args.pins.read_text())
    assert set(pins) == set(PINS)
    for name, expected in PINS.items():
        assert pins[name]['sha256'] == expected and sha(Path(pins[name]['file'])) == expected
    assert pins['verilator']['revision'] == '5c5314b39cd888f427807d626e1502cbf222c292'
    commands = []

    def run(label, argv, cwd=out, env=None):
        row = {'label': label, 'argv': argv, 'cwd': str(cwd)}
        if env is not None:
            row['environment_overrides'] = {k: v for k, v in env.items() if os.environ.get(k) != v}
        commands.append(row)
        print('START ' + label, flush=True)
        started = time.monotonic()
        try:
            with (out / (label + '.log')).open('w') as stream:
                proc = subprocess.run(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
            row['returncode'] = proc.returncode
            proc.check_returncode()
        finally:
            row['elapsed_seconds'] = time.monotonic() - started
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        print('PASS ' + label, flush=True)

    deps = out / 'dependencies'
    deps.mkdir()
    aliases = []
    for name in ('flex', 'bison', 'libfl2', 'libfl-dev'):
        # The runner intentionally rejects output symlinks. Preserve package
        # archives, and stage declared aliases as regular, byte-identical copies.
        process = subprocess.Popen(['/usr/bin/dpkg-deb', '--fsys-tarfile', pins[name]['file']], stdout=subprocess.PIPE)
        with tarfile.open(fileobj=process.stdout, mode='r|') as archive:
            for member in archive:
                relative = Path(member.name)
                assert not relative.is_absolute() and '..' not in relative.parts
                target = deps / relative
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as reader, target.open('wb') as stream:
                        shutil.copyfileobj(reader, stream)
                    target.chmod(0o755 if member.mode & 0o111 else 0o644)
                elif member.issym() or member.islnk():
                    aliases.append({'package': name, 'path': str(relative), 'original_target': member.linkname,
                                    'hardlink': member.islnk()})
                else:
                    raise ValueError('unsupported package member ' + member.name)
        assert process.wait() == 0
    for alias in aliases:
        target = deps / alias['path']
        link = Path(alias['original_target'])
        source = deps / str(link).lstrip('/') if link.is_absolute() else (
            deps / link if alias['hardlink'] else target.parent / link)
        source = source.resolve(strict=True)
        assert deps in source.parents and source != target
        if source.is_dir():
            shutil.copytree(source, target)
            alias['derivation'] = 'directory alias copied with regular descendants'
        else:
            shutil.copyfile(source, target)
            target.chmod(0o755 if source.stat().st_mode & 0o111 else 0o644)
            alias.update(derivation='regular byte-identical alias', sha256=sha(target))
    (out / 'package-aliases.json').write_text(json.dumps(aliases, indent=2) + '\n')
    with tarfile.open(pins['verilator']['file']) as archive:
        members = archive.getmembers()
        for member in members:
            assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            if member.issym() or member.islnk():
                target = (out / member.name).parent / member.linkname if member.issym() else out / member.linkname
                assert not Path(member.linkname).is_absolute() and out in target.resolve().parents
        archive.extractall(out)
    toolroot = out / 'verilator-5c5314b39cd888f427807d626e1502cbf222c292'
    env = dict(os.environ,
        PATH=str(deps / 'usr/bin') + ':' + os.environ['PATH'],
        VERILATOR_ROOT=str(toolroot),
        BISON_PKGDATADIR=str(deps / 'usr/share/bison'),
        LD_LIBRARY_PATH=str(deps / 'usr/lib/x86_64-linux-gnu'),
        CPPFLAGS='-I' + str(deps / 'usr/include'),
        LDFLAGS='-L' + str(deps / 'usr/lib/x86_64-linux-gnu'))
    run('autoconf', ['autoconf'], cwd=toolroot, env=env)
    run('configure', [str(toolroot / 'configure')], cwd=toolroot, env=env)
    run('build', ['make', '-C', 'src', '-j6', 'opt'], cwd=toolroot, env=env)
    run('version', [str(toolroot / 'bin/verilator'), '--version'], cwd=toolroot, env=env)
    result = {'status': 'built_run_in_place', 'toolroot': str(toolroot),
        'revision': pins['verilator']['revision'], 'pins': pins,
        'binary_sha256': sha(toolroot / 'bin/verilator_bin'),
        'system_installation_performed': False, 'host_environment_changed': False}
    (out / 'tool-root.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
