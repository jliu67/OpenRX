#!/usr/bin/python3
"""Finite host-only lifecycle controls; no simulator or RandomX is imported."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
mode = sys.argv[1]
payload = Path(sys.argv[2])
payload.mkdir(mode=0o700)
fd = os.open(payload.parent, os.O_RDONLY | os.O_DIRECTORY)
os.fsync(fd)
os.close(fd)


def new(name, value):
    with (payload / name).open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(payload, os.O_RDONLY | os.O_DIRECTORY)
    os.fsync(fd)
    os.close(fd)


if mode == 'instant':
    new('nested-result.json', {'host_only': True, 'scientific_acceptance': 'unverified'})
    print('instant host-only exit', flush=True)
elif mode == 'exit-seven':
    new('retained-failure.json', {'intentional_returncode': 7})
    print('preserved intentional failure output', flush=True)
    sys.exit(7)
elif mode in {'hold', 'detached', 'detached-child', 'independent'}:
    if mode == 'detached-child':
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if mode == 'detached':
        child = subprocess.Popen([
            sys.executable, str(Path(__file__).resolve()), 'detached-child',
            str(payload / 'detached-child-output')], start_new_session=True)
        new('detached-child.json', {'pid': child.pid, 'start_new_session': True})
    new('ready.json', {'pid': os.getpid(), 'mode': mode})
    # Finite toy work defines the fixture, rather than a service wall timeout.
    for number in range(400):
        print(f'{mode} heartbeat {number}', flush=True)
        time.sleep(0.25)
elif mode == 'oom':
    new('ready.json', {'pid': os.getpid(), 'mode': mode})
    for number in range(1000):
        if (payload / 'allocate.request').is_file():
            print('intentional 96MiB allocation under fixture-only 48MiB limit', flush=True)
            memory = bytearray(96 * 1024 * 1024)
            print(len(memory), flush=True)
            break
        time.sleep(0.05)
    else:
        raise RuntimeError('OOM control was never released; retain this failure')
else:
    raise ValueError('Unknown host-only fixture mode')
